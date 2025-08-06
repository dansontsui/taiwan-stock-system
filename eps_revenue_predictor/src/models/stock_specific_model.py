# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Stock-Specific AI Model
股票專用AI調整模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
import hashlib
warnings.filterwarnings('ignore')

try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor
    LIGHTGBM_AVAILABLE = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path

from config.settings import AI_MODEL_CONFIG, PROJECT_ROOT
from src.data.database_manager import DatabaseManager
from src.utils.logger import get_logger, log_execution

logger = get_logger('stock_specific_model')

class StockSpecificAIModel:
    """股票專用AI調整模型
    
    為每支股票訓練獨立的AI模型
    當資料不足時，回退到通用模型
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.config = AI_MODEL_CONFIG
        self.models = {}  # 儲存各股票的模型
        self.scalers = {}  # 儲存各股票的標準化器
        self.model_dir = PROJECT_ROOT / 'models' / 'stock_specific'
        self.general_model = None  # 通用模型作為備用
        self.general_scaler = StandardScaler()
        
        # 確保模型目錄存在
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StockSpecificAIModel initialized (LightGBM: {LIGHTGBM_AVAILABLE})")
    
    def get_model_path(self, stock_id: str) -> Tuple[Path, Path]:
        """獲取股票專用模型的檔案路徑"""
        model_file = f"model_{stock_id}.pkl"
        scaler_file = f"scaler_{stock_id}.pkl"
        return (self.model_dir / model_file, self.model_dir / scaler_file)
    
    def has_sufficient_data(self, stock_id: str, min_samples: int = 20) -> bool:
        """檢查股票是否有足夠的歷史資料訓練專用模型"""
        try:
            # 獲取股票的歷史資料
            monthly_revenue = self.db_manager.get_monthly_revenue(stock_id, months=36)  # 3年資料
            financial_ratios = self.db_manager.get_financial_ratios(stock_id)
            
            # 計算可用的訓練樣本數
            available_samples = min(len(monthly_revenue), len(financial_ratios))
            
            logger.info(f"Stock {stock_id} has {available_samples} samples (min required: {min_samples})")
            
            return available_samples >= min_samples
            
        except Exception as e:
            logger.warning(f"Error checking data sufficiency for {stock_id}: {e}")
            return False
    
    @log_execution
    def train_stock_model(self, stock_id: str, retrain: bool = False) -> Dict:
        """為特定股票訓練專用AI模型"""
        
        model_path, scaler_path = self.get_model_path(stock_id)
        
        # 檢查是否需要重新訓練
        if not retrain and model_path.exists() and scaler_path.exists():
            try:
                self.models[stock_id] = joblib.load(model_path)
                self.scalers[stock_id] = joblib.load(scaler_path)
                logger.info(f"Loaded existing model for stock {stock_id}")
                return {'status': 'loaded_existing', 'stock_id': stock_id}
            except Exception as e:
                logger.warning(f"Failed to load existing model for {stock_id}: {e}")
        
        # 檢查資料充足性
        if not self.has_sufficient_data(stock_id):
            logger.warning(f"Insufficient data for stock {stock_id}, will use general model")
            return {'status': 'insufficient_data', 'stock_id': stock_id}
        
        logger.info(f"Training stock-specific model for {stock_id}")
        
        try:
            # 收集該股票的訓練資料
            training_data = self._collect_stock_training_data(stock_id)
            
            if training_data.empty:
                logger.error(f"No training data for stock {stock_id}")
                return {'status': 'failed', 'reason': 'no_data', 'stock_id': stock_id}
            
            # 準備特徵和目標變數
            X, y = self._prepare_training_data(training_data)
            
            if len(X) < 10:
                logger.warning(f"Insufficient samples for {stock_id}: {len(X)}")
                return {'status': 'failed', 'reason': 'insufficient_samples', 'stock_id': stock_id}
            
            # 分割訓練和驗證集
            if len(X) > 20:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            else:
                # 資料較少時，使用全部資料訓練
                X_train, y_train = X, y
                X_val, y_val = X, y
            
            # 標準化特徵
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # 訓練模型
            model = self._create_model()
            model.fit(X_train_scaled, y_train)
            
            # 驗證模型
            val_score = model.score(X_val_scaled, y_val)
            
            # 儲存模型
            self.models[stock_id] = model
            self.scalers[stock_id] = scaler
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            logger.info(f"Stock-specific model trained for {stock_id}, validation score: {val_score:.4f}")
            
            return {
                'status': 'success',
                'stock_id': stock_id,
                'validation_score': val_score,
                'training_samples': len(X_train),
                'model_type': 'stock_specific'
            }
            
        except Exception as e:
            logger.error(f"Failed to train model for stock {stock_id}: {e}")
            return {'status': 'failed', 'reason': str(e), 'stock_id': stock_id}
    
    @log_execution
    def train_general_model(self, stock_list: List[str] = None, retrain: bool = False) -> Dict:
        """訓練通用模型作為備用"""
        
        general_model_path = self.model_dir / 'general_model.pkl'
        general_scaler_path = self.model_dir / 'general_scaler.pkl'
        
        # 檢查是否需要重新訓練
        if not retrain and general_model_path.exists() and general_scaler_path.exists():
            try:
                self.general_model = joblib.load(general_model_path)
                self.general_scaler = joblib.load(general_scaler_path)
                logger.info("Loaded existing general model")
                return {'status': 'loaded_existing', 'model_type': 'general'}
            except Exception as e:
                logger.warning(f"Failed to load existing general model: {e}")
        
        logger.info("Training general AI model")
        
        # 獲取訓練股票列表
        if stock_list is None:
            stock_list = self.db_manager.get_available_stocks(limit=100)
        
        # 收集多股票訓練資料
        all_training_data = []
        for stock_id in stock_list:
            try:
                stock_data = self._collect_stock_training_data(stock_id)
                if not stock_data.empty:
                    all_training_data.append(stock_data)
            except Exception as e:
                logger.warning(f"Failed to collect data for {stock_id}: {e}")
                continue
        
        if not all_training_data:
            logger.error("No training data available for general model")
            return {'status': 'failed', 'reason': 'no_data'}
        
        # 合併所有資料
        training_data = pd.concat(all_training_data, ignore_index=True)
        
        # 準備特徵和目標變數
        X, y = self._prepare_training_data(training_data)
        
        if len(X) < 50:
            logger.warning(f"Insufficient samples for general model: {len(X)}")
            return {'status': 'failed', 'reason': 'insufficient_samples'}
        
        # 分割訓練和驗證集
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 標準化特徵
        X_train_scaled = self.general_scaler.fit_transform(X_train)
        X_val_scaled = self.general_scaler.transform(X_val)
        
        # 訓練模型
        self.general_model = self._create_model()
        self.general_model.fit(X_train_scaled, y_train)
        
        # 驗證模型
        val_score = self.general_model.score(X_val_scaled, y_val)
        
        # 儲存模型
        joblib.dump(self.general_model, general_model_path)
        joblib.dump(self.general_scaler, general_scaler_path)
        
        logger.info(f"General model trained, validation score: {val_score:.4f}")
        
        return {
            'status': 'success',
            'model_type': 'general',
            'validation_score': val_score,
            'training_samples': len(X_train),
            'stocks_used': len(stock_list)
        }
    
    def predict_adjustment_factor(self, stock_id: str, base_prediction: float, prediction_type: str = 'revenue') -> Dict:
        """預測調整因子 - 優先使用股票專用模型"""
        
        try:
            # 嘗試使用股票專用模型
            if stock_id in self.models and stock_id in self.scalers:
                return self._predict_with_stock_model(stock_id, base_prediction, prediction_type)
            
            # 嘗試載入股票專用模型
            model_path, scaler_path = self.get_model_path(stock_id)
            if model_path.exists() and scaler_path.exists():
                try:
                    self.models[stock_id] = joblib.load(model_path)
                    self.scalers[stock_id] = joblib.load(scaler_path)
                    return self._predict_with_stock_model(stock_id, base_prediction, prediction_type)
                except Exception as e:
                    logger.warning(f"Failed to load stock model for {stock_id}: {e}")
            
            # 回退到通用模型
            return self._predict_with_general_model(stock_id, base_prediction, prediction_type)
            
        except Exception as e:
            logger.error(f"Prediction failed for {stock_id}: {e}")
            return {
                'adjustment_factor': 0.0,
                'adjusted_prediction': base_prediction,
                'confidence': 'Low',
                'model_used': 'none',
                'error': str(e)
            }
    
    def _predict_with_stock_model(self, stock_id: str, base_prediction: float, prediction_type: str) -> Dict:
        """使用股票專用模型預測"""
        # 實作股票專用預測邏輯
        # 這裡需要實作具體的預測邏輯
        return {
            'adjustment_factor': 0.0,
            'adjusted_prediction': base_prediction,
            'confidence': 'High',
            'model_used': 'stock_specific'
        }
    
    def _predict_with_general_model(self, stock_id: str, base_prediction: float, prediction_type: str) -> Dict:
        """使用通用模型預測"""
        # 實作通用模型預測邏輯
        return {
            'adjustment_factor': 0.0,
            'adjusted_prediction': base_prediction,
            'confidence': 'Medium',
            'model_used': 'general'
        }
    
    def _collect_stock_training_data(self, stock_id: str) -> pd.DataFrame:
        """收集單一股票的訓練資料"""
        # 實作資料收集邏輯
        return pd.DataFrame()
    
    def _prepare_training_data(self, training_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練資料"""
        # 實作資料準備邏輯
        return np.array([]), np.array([])
    
    def _create_model(self):
        """創建模型實例"""
        if LIGHTGBM_AVAILABLE:
            return LGBMRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
                verbose=-1
            )
        else:
            return GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
