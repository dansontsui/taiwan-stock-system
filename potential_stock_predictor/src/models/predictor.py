#!/usr/bin/env python3
"""
預測服務模組

提供潛力股預測功能：
- 載入訓練好的模型
- 對最新資料進行預測
- 生成潛力股排行榜
- 預測結果儲存與歷史追蹤
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
from datetime import datetime, timedelta

from ..features.feature_engineering import FeatureEngineer
from ..utils.database import DatabaseManager
from ..utils.helpers import load_model, load_json, save_json
try:
    from ...config.config import MODEL_CONFIG, PREDICTION_CONFIG
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    sys.path.insert(0, project_root)
    from config.config import MODEL_CONFIG, PREDICTION_CONFIG

logger = logging.getLogger(__name__)

class Predictor:
    """預測器"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化預測器
        
        Args:
            db_manager: 資料庫管理器
        """
        self.db_manager = db_manager or DatabaseManager()
        self.feature_engineer = FeatureEngineer(self.db_manager)
        self.model_config = MODEL_CONFIG
        self.prediction_config = PREDICTION_CONFIG
        
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        
        # 載入模型
        self.load_models()
    
    def load_models(self):
        """載入所有訓練好的模型"""
        logger.info("載入預測模型...")
        
        models_dir = self.model_config['models_dir']
        model_version = self.model_config['model_version']
        
        # 載入特徵名稱
        try:
            features_path = models_dir / f"feature_names_{model_version}.json"
            if features_path.exists():
                feature_data = load_json(str(features_path))
                self.feature_names = feature_data['feature_names']
                logger.info(f"載入 {len(self.feature_names)} 個特徵名稱")
        except Exception as e:
            logger.warning(f"載入特徵名稱失敗: {e}")
        
        # 載入各種模型
        for model_type in self.model_config['model_types']:
            try:
                model_path = models_dir / f"{model_type}_{model_version}.pkl"
                if model_path.exists():
                    self.models[model_type] = load_model(str(model_path))
                    logger.info(f"成功載入 {model_type} 模型")
                    
                    # 載入對應的scaler（如果有的話）
                    scaler_path = models_dir / f"{model_type}_scaler_{model_version}.pkl"
                    if scaler_path.exists():
                        self.scalers[model_type] = load_model(str(scaler_path))
                        logger.info(f"成功載入 {model_type} scaler")
                else:
                    logger.warning(f"找不到 {model_type} 模型檔案: {model_path}")
                    
            except Exception as e:
                logger.error(f"載入 {model_type} 模型失敗: {e}")
        
        if not self.models:
            logger.warning("沒有成功載入任何模型")
        else:
            logger.info(f"成功載入 {len(self.models)} 個模型")
    
    def predict_single_stock(self, stock_id: str, prediction_date: str = None,
                           model_type: str = None) -> Dict:
        """
        預測單一股票
        
        Args:
            stock_id: 股票代碼
            prediction_date: 預測日期，None表示使用當前日期
            model_type: 模型類型，None表示使用預設模型
            
        Returns:
            預測結果字典
        """
        if prediction_date is None:
            prediction_date = datetime.now().strftime('%Y-%m-%d')
        
        if model_type is None:
            model_type = self.model_config['default_model']
        
        if model_type not in self.models:
            raise ValueError(f"模型 {model_type} 未載入")
        
        # 排除00開頭的股票
        if stock_id.startswith('00'):
            return {
                'stock_id': stock_id,
                'prediction_date': prediction_date,
                'probability': 0.0,
                'prediction': 0,
                'model_type': model_type,
                'status': 'excluded_etf'
            }
        
        try:
            # 生成特徵
            features_df = self.feature_engineer.generate_features(stock_id, prediction_date)
            
            if features_df.empty:
                return {
                    'stock_id': stock_id,
                    'prediction_date': prediction_date,
                    'probability': 0.0,
                    'prediction': 0,
                    'model_type': model_type,
                    'status': 'no_features'
                }
            
            # 準備特徵矩陣
            X = self._prepare_features_for_prediction(features_df, model_type)
            
            # 進行預測
            model = self.models[model_type]
            probability = model.predict_proba(X)[0, 1]
            prediction = 1 if probability >= self.prediction_config['confidence_threshold'] else 0
            
            return {
                'stock_id': stock_id,
                'prediction_date': prediction_date,
                'probability': float(probability),
                'prediction': int(prediction),
                'model_type': model_type,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"預測股票 {stock_id} 失敗: {e}")
            return {
                'stock_id': stock_id,
                'prediction_date': prediction_date,
                'probability': 0.0,
                'prediction': 0,
                'model_type': model_type,
                'status': 'error',
                'error': str(e)
            }
    
    def _prepare_features_for_prediction(self, features_df: pd.DataFrame, model_type: str) -> np.ndarray:
        """
        為預測準備特徵矩陣
        
        Args:
            features_df: 特徵DataFrame
            model_type: 模型類型
            
        Returns:
            特徵矩陣
        """
        # 移除非特徵欄位
        feature_columns = [col for col in features_df.columns 
                          if col not in ['stock_id', 'feature_date']]
        
        X = features_df[feature_columns].copy()
        
        # 確保特徵順序與訓練時一致
        if self.feature_names:
            # 添加缺失的特徵（填充為0）
            for feature in self.feature_names:
                if feature not in X.columns:
                    X[feature] = 0
            
            # 重新排序特徵
            X = X[self.feature_names]
        
        # 處理缺失值
        X = X.fillna(0)
        
        # 應用scaler（如果有的話）
        if model_type in self.scalers:
            X = self.scalers[model_type].transform(X)
        
        return X
    
    def predict_batch(self, stock_ids: List[str] = None, prediction_date: str = None,
                     model_type: str = None) -> pd.DataFrame:
        """
        批次預測多個股票
        
        Args:
            stock_ids: 股票代碼列表，None表示預測所有股票
            prediction_date: 預測日期
            model_type: 模型類型
            
        Returns:
            預測結果DataFrame
        """
        if prediction_date is None:
            prediction_date = datetime.now().strftime('%Y-%m-%d')
        
        if model_type is None:
            model_type = self.model_config['default_model']
        
        # 獲取股票清單
        if stock_ids is None:
            stock_list_df = self.db_manager.get_stock_list(
                exclude_patterns=self.prediction_config['exclude_patterns']
            )
            stock_ids = stock_list_df['stock_id'].tolist()
        
        logger.info(f"開始批次預測 {len(stock_ids)} 個股票")
        
        results = []
        
        for i, stock_id in enumerate(stock_ids):
            result = self.predict_single_stock(stock_id, prediction_date, model_type)
            results.append(result)
            
            # 進度顯示
            if (i + 1) % 100 == 0:
                logger.info(f"已預測 {i + 1}/{len(stock_ids)} 個股票")
        
        results_df = pd.DataFrame(results)
        
        # 儲存預測結果
        self.save_predictions(results_df)
        
        logger.info(f"批次預測完成，成功預測 {len(results_df)} 個股票")
        
        return results_df
    
    def generate_potential_stock_ranking(self, prediction_date: str = None,
                                       model_type: str = None,
                                       top_k: int = None) -> pd.DataFrame:
        """
        生成潛力股排行榜
        
        Args:
            prediction_date: 預測日期
            model_type: 模型類型
            top_k: 返回前K個股票
            
        Returns:
            潛力股排行榜DataFrame
        """
        if top_k is None:
            top_k = self.prediction_config['top_k_stocks']
        
        # 批次預測
        predictions_df = self.predict_batch(prediction_date=prediction_date, model_type=model_type)
        
        # 過濾成功預測的股票
        valid_predictions = predictions_df[predictions_df['status'] == 'success'].copy()
        
        if valid_predictions.empty:
            logger.warning("沒有有效的預測結果")
            return pd.DataFrame()
        
        # 按機率排序
        ranking = valid_predictions.sort_values('probability', ascending=False).head(top_k)
        
        # 添加排名
        ranking['rank'] = range(1, len(ranking) + 1)
        
        # 獲取股票基本資訊
        ranking = self._enrich_ranking_with_stock_info(ranking)
        
        logger.info(f"生成潛力股排行榜，共 {len(ranking)} 個股票")
        
        return ranking
    
    def _enrich_ranking_with_stock_info(self, ranking_df: pd.DataFrame) -> pd.DataFrame:
        """為排行榜添加股票基本資訊"""
        try:
            stock_list_df = self.db_manager.get_stock_list()
            ranking_enriched = ranking_df.merge(
                stock_list_df[['stock_id', 'stock_name', 'market', 'industry']], 
                on='stock_id', 
                how='left'
            )
            return ranking_enriched
        except Exception as e:
            logger.warning(f"添加股票基本資訊失敗: {e}")
            return ranking_df
    
    def save_predictions(self, predictions_df: pd.DataFrame):
        """儲存預測結果"""
        try:
            # 添加時間戳
            predictions_df['created_at'] = datetime.now()
            
            # 儲存到資料庫
            self.db_manager.save_predictions(predictions_df, 'stock_predictions')
            
            logger.info(f"已儲存 {len(predictions_df)} 筆預測結果")
            
        except Exception as e:
            logger.error(f"儲存預測結果失敗: {e}")
    
    def get_model_info(self) -> Dict:
        """獲取模型資訊"""
        return {
            'loaded_models': list(self.models.keys()),
            'default_model': self.model_config['default_model'],
            'model_version': self.model_config['model_version'],
            'feature_count': len(self.feature_names),
            'confidence_threshold': self.prediction_config['confidence_threshold']
        }
