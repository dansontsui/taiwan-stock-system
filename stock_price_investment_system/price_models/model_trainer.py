# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 簡易模型訓練器
提供最小功能封裝 StockPricePredictor 的訓練流程。
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd

from .feature_engineering import FeatureEngineer
from .stock_price_predictor import StockPricePredictor
from ..config.settings import get_config
from ..data.data_manager import DataManager


class ModelTrainer:
    """簡易模型訓練器"""

    def __init__(self,
                 feature_engineer: Optional[FeatureEngineer] = None,
                 model_type: Optional[str] = None):
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.model_type = model_type
        self.predictor = StockPricePredictor(self.feature_engineer, model_type=self.model_type)
        self.cfg = get_config()

    def prepare_training_data(self, stock_ids: List[str], start_date: str, end_date: str,
                              target_periods: Optional[List[int]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        target_periods = target_periods or [20]
        features, targets = self.feature_engineer.generate_training_dataset(
            stock_ids=stock_ids,
            start_date=start_date,
            end_date=end_date,
            target_periods=target_periods,
            frequency='monthly'
        )
        return features, targets

    def train(self, feature_df: pd.DataFrame, target_df: pd.DataFrame, target_col: str = 'target_20d') -> Dict[str, Any]:
        return self.predictor.train(feature_df, target_df, target_column=target_col)

    def train_from_config(self) -> Dict[str, Any]:
        wf = self.cfg['walkforward']
        dm = DataManager()
        stocks = dm.get_available_stocks(
            start_date=wf['training_start'] + '-01',
            end_date=wf['training_end'] + '-31',
            min_history_months=wf['min_stock_history_months']
        )
        if not stocks:
            return {'success': False, 'error': 'no_stocks'}
        stocks = stocks[:20]
        feats, targs = self.prepare_training_data(stocks, wf['training_start'] + '-01', wf['training_end'] + '-31')
        if feats.empty or targs.empty:
            return {'success': False, 'error': 'no_training_data'}
        return self.train(feats, targs)

