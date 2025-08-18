# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 股價預測器
Stock Price Investment System - Stock Price Predictor
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import logging
import pickle
from pathlib import Path

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM not available")

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score

from .feature_engineering import FeatureEngineer
from ..config.settings import get_config

logger = logging.getLogger(__name__)

class StockPricePredictor:
    """股價預測器 - 使用機器學習預測股價報酬率"""
    
    def __init__(self,
                 feature_engineer: FeatureEngineer = None,
                 model_type: str = None,
                 override_params: Optional[Dict[str, Any]] = None):
        """
        初始化股價預測器
        
        Args:
            feature_engineer: 特徵工程師
            model_type: 模型類型 ('xgboost', 'lightgbm', 'random_forest', 'linear')
        """
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.config = get_config()
        self.model_config = self.config['model']

        # 設定模型類型
        self.model_type = model_type or self.model_config['primary_model']

        # 外部覆蓋參數（例如最佳參數）
        self.override_params = override_params or {}

        # 初始化模型
        self.model = None
        self.feature_names = None
        self.is_trained = False
        
        # 模型儲存路徑
        self.model_dir = Path(self.config['output']['paths']['models'])
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StockPricePredictor initialized with model type: {self.model_type}")
    
    def create_model(self) -> Any:
        """建立模型實例"""
        if self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
            params = self.model_config['xgboost_params'].copy()
            params.update(self.override_params or {})
            return xgb.XGBRegressor(**params)

        elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            params = self.model_config['lightgbm_params'].copy()
            params.update(self.override_params or {})
            return lgb.LGBMRegressor(**params)

        elif self.model_type == 'random_forest':
            base = {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42,
                'n_jobs': -1
            }
            base.update(self.override_params or {})
            return RandomForestRegressor(**base)
        
        elif self.model_type == 'linear':
            return LinearRegression()
        
        else:
            logger.warning(f"Model type {self.model_type} not available, using RandomForest")
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
    
    def train(self, 
              feature_df: pd.DataFrame,
              target_df: pd.DataFrame,
              target_column: str = 'target_20d',
              validation_split: float = 0.2) -> Dict[str, Any]:
        """
        訓練模型
        
        Args:
            feature_df: 特徵DataFrame
            target_df: 目標DataFrame
            target_column: 目標欄位名稱
            validation_split: 驗證集比例
            
        Returns:
            訓練結果字典
        """
        logger.info(f"Training model with {len(feature_df)} samples")
        
        # 合併特徵和目標
        merged_df = feature_df.merge(
            target_df[['stock_id', 'as_of_date', target_column]],
            on=['stock_id', 'as_of_date'],
            how='inner'
        )

        logger.info(f"合併後樣本數: {len(merged_df)}")

        # 檢查 NaN 情況
        nan_counts = merged_df.isnull().sum()
        if nan_counts.sum() > 0:
            logger.warning(f"發現 NaN 值: {nan_counts[nan_counts > 0].to_dict()}")

        # 移除包含NaN的樣本
        before_dropna = len(merged_df)
        merged_df = merged_df.dropna()
        after_dropna = len(merged_df)

        if before_dropna != after_dropna:
            logger.info(f"移除 NaN 樣本: {before_dropna} -> {after_dropna}")

        if len(merged_df) == 0:
            raise ValueError("No valid training samples after removing NaN values")

        # 準備特徵和目標
        feature_columns = [col for col in merged_df.columns
                          if col not in ['stock_id', 'as_of_date', target_column]]

        X = merged_df[feature_columns].values
        y = merged_df[target_column].values

        # 最終 NaN 檢查
        if np.isnan(X).any():
            nan_features = [feature_columns[i] for i in range(len(feature_columns)) if np.isnan(X[:, i]).any()]
            logger.error(f"特徵矩陣仍有 NaN: {nan_features}")
            # 強制填充
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            logger.info("已強制將 NaN 和無限值替換為 0")

        if np.isnan(y).any():
            logger.error(f"目標變數仍有 NaN: {np.sum(np.isnan(y))} 個")
            raise ValueError("Target variable contains NaN values")
        
        # 儲存特徵名稱
        self.feature_names = feature_columns
        
        # 分割訓練和驗證集
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # 建立和訓練模型（如果還沒有模型的話）
        if self.model is None:
            self.model = self.create_model()
            logger.debug("創建新模型")
        else:
            logger.debug("使用現有模型（可能來自超參數調優）")
        
        try:
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # 驗證模型
            train_pred = self.model.predict(X_train)
            val_pred = self.model.predict(X_val)
            
            # 計算評估指標
            train_metrics = self._calculate_metrics(y_train, train_pred)
            val_metrics = self._calculate_metrics(y_val, val_pred)
            
            # 交叉驗證
            cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='r2')
            
            result = {
                'success': True,
                'model_type': self.model_type,
                'training_samples': len(X_train),
                'validation_samples': len(X_val),
                'feature_count': len(feature_columns),
                'train_metrics': train_metrics,
                'validation_metrics': val_metrics,
                'cv_r2_mean': cv_scores.mean(),
                'cv_r2_std': cv_scores.std(),
                'feature_names': feature_columns
            }
            
            logger.info(f"Model training completed successfully")
            logger.info(f"Validation R²: {val_metrics['r2']:.4f}, RMSE: {val_metrics['rmse']:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_type': self.model_type
            }
    
    def predict(self, 
                stock_id: str,
                as_of_date: str,
                return_confidence: bool = True) -> Dict[str, Any]:
        """
        預測股價報酬率
        
        Args:
            stock_id: 股票代碼
            as_of_date: 預測時點
            return_confidence: 是否返回信心區間
            
        Returns:
            預測結果字典
        """
        if not self.is_trained:
            return {
                'success': False,
                'error': 'Model not trained',
                'stock_id': stock_id,
                'as_of_date': as_of_date
            }
        
        try:
            # 生成特徵
            features = self.feature_engineer.generate_features(stock_id, as_of_date)
            
            if not features:
                return {
                    'success': False,
                    'error': 'No features generated',
                    'stock_id': stock_id,
                    'as_of_date': as_of_date
                }
            
            # 準備特徵向量
            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(features.get(feature_name, 0))
            
            X = np.array(feature_vector).reshape(1, -1)
            
            # 預測
            prediction = self.model.predict(X)[0]
            
            result = {
                'success': True,
                'stock_id': stock_id,
                'as_of_date': as_of_date,
                'predicted_return': prediction,
                'model_type': self.model_type
            }
            
            # 計算信心區間（如果支援）
            if return_confidence:
                confidence_info = self._calculate_confidence(X, prediction)
                result.update(confidence_info)
            
            # 特徵重要性（如果支援）
            if hasattr(self.model, 'feature_importances_'):
                feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
                result['feature_importance'] = feature_importance
            
            logger.debug(f"Prediction for {stock_id}: {prediction:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for {stock_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'stock_id': stock_id,
                'as_of_date': as_of_date
            }
    
    def predict_batch(self, 
                     stock_ids: List[str],
                     as_of_date: str) -> pd.DataFrame:
        """
        批量預測
        
        Args:
            stock_ids: 股票代碼清單
            as_of_date: 預測時點
            
        Returns:
            預測結果DataFrame
        """
        logger.info(f"Batch prediction for {len(stock_ids)} stocks as of {as_of_date}")
        
        results = []
        
        for stock_id in stock_ids:
            result = self.predict(stock_id, as_of_date)
            results.append(result)
        
        # 轉換為DataFrame
        df = pd.DataFrame(results)
        
        logger.info(f"Batch prediction completed: {len(df)} results")
        return df
    
    def save_model(self, filename: str = None) -> str:
        """
        儲存模型
        
        Args:
            filename: 檔案名稱
            
        Returns:
            儲存路徑
        """
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.model_type}_stock_predictor_{timestamp}.pkl"
        
        filepath = self.model_dir / filename
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'config': self.model_config,
            'created_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
        return str(filepath)
    
    def load_model(self, filepath: str) -> bool:
        """
        載入模型
        
        Args:
            filepath: 模型檔案路徑
            
        Returns:
            是否載入成功
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.model_type = model_data['model_type']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model from {filepath}: {e}")
            return False
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """計算評估指標"""
        return {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mean_pred': np.mean(y_pred),
            'std_pred': np.std(y_pred)
        }
    
    def _calculate_confidence(self, X: np.ndarray, prediction: float) -> Dict[str, Any]:
        """計算信心區間（簡化版本）"""
        # 這裡實作簡化的信心區間計算
        # 實際應用中可以使用更複雜的方法如quantile regression
        
        confidence_info = {
            'confidence_level': 0.8,  # 預設信心水準
            'lower_bound': prediction * 0.9,  # 簡化的下界
            'upper_bound': prediction * 1.1,  # 簡化的上界
            'prediction_std': abs(prediction) * 0.1  # 簡化的標準差
        }
        
        return confidence_info
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型資訊"""
        return {
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names) if self.feature_names else 0,
            'feature_names': self.feature_names,
            'config': self.model_config
        }
