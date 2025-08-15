# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 營收整合模組
Stock Price Investment System - Revenue Integration Module
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# 添加EPS預測系統路徑
eps_predictor_path = Path(__file__).parent.parent.parent / "eps_revenue_predictor"
if eps_predictor_path.exists():
    sys.path.insert(0, str(eps_predictor_path))

from .data_manager import DataManager
from ..config.settings import get_config

logger = logging.getLogger(__name__)

class RevenueIntegration:
    """營收整合模組 - 整合現有的營收預測結果"""
    
    def __init__(self, data_manager: DataManager = None):
        """初始化營收整合模組"""
        self.data_manager = data_manager or DataManager()
        self.config = get_config('feature')
        
        # 嘗試導入EPS預測系統
        self.eps_predictor = None
        try:
            from src.predictors.revenue_predictor import RevenuePredictor
            from src.predictors.eps_predictor import EPSPredictor
            self.revenue_predictor = RevenuePredictor()
            self.eps_predictor = EPSPredictor()
            logger.info("Successfully integrated with EPS Revenue Predictor system")
        except ImportError as e:
            logger.warning(f"Could not import EPS Revenue Predictor: {e}")
            self.revenue_predictor = None
            self.eps_predictor = None
        
        logger.info("RevenueIntegration initialized")
    
    def get_revenue_features(self, 
                           stock_id: str,
                           as_of_date: str,
                           lookback_months: int = 24) -> Dict[str, float]:
        """
        獲取營收特徵（避免未來函數）
        
        Args:
            stock_id: 股票代碼
            as_of_date: 預測時點 (YYYY-MM-DD)
            lookback_months: 回看月數
            
        Returns:
            營收特徵字典
        """
        # 計算開始日期
        as_of_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
        start_dt = as_of_dt - timedelta(days=lookback_months * 30)
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # 獲取歷史營收資料（截止到as_of_date）
        revenue_df = self.data_manager.get_monthly_revenue(
            stock_id, start_date, as_of_date
        )
        
        if revenue_df.empty:
            logger.warning(f"No revenue data available for {stock_id} up to {as_of_date}")
            return self._get_default_revenue_features()
        
        # 計算營收特徵
        features = {}
        
        # 基本統計
        latest_revenue = revenue_df.iloc[-1]['revenue'] if not revenue_df.empty else 0
        features['latest_revenue'] = latest_revenue
        
        # YoY成長率特徵
        yoy_periods = self.config['revenue_features']['yoy_periods']
        for period in yoy_periods:
            if len(revenue_df) > period:
                current_revenue = revenue_df.iloc[-1]['revenue']
                past_revenue = revenue_df.iloc[-(period+1)]['revenue']
                if past_revenue > 0:
                    features[f'revenue_yoy_{period}m'] = (current_revenue - past_revenue) / past_revenue
                else:
                    features[f'revenue_yoy_{period}m'] = 0
            else:
                features[f'revenue_yoy_{period}m'] = 0
        
        # MoM成長率特徵
        mom_periods = self.config['revenue_features']['mom_periods']
        for period in mom_periods:
            if len(revenue_df) > period:
                current_revenue = revenue_df.iloc[-1]['revenue']
                past_revenue = revenue_df.iloc[-(period+1)]['revenue']
                if past_revenue > 0:
                    features[f'revenue_mom_{period}m'] = (current_revenue - past_revenue) / past_revenue
                else:
                    features[f'revenue_mom_{period}m'] = 0
            else:
                features[f'revenue_mom_{period}m'] = 0
        
        # 移動平均特徵
        ma_periods = self.config['revenue_features']['ma_periods']
        for period in ma_periods:
            if len(revenue_df) >= period:
                ma_value = revenue_df['revenue'].tail(period).mean()
                features[f'revenue_ma_{period}m'] = ma_value
                if ma_value > 0:
                    features[f'revenue_to_ma_{period}m'] = latest_revenue / ma_value - 1
                else:
                    features[f'revenue_to_ma_{period}m'] = 0
            else:
                features[f'revenue_ma_{period}m'] = latest_revenue
                features[f'revenue_to_ma_{period}m'] = 0
        
        # 波動性特徵
        volatility_window = self.config['revenue_features']['volatility_window']
        if len(revenue_df) >= volatility_window:
            revenue_returns = revenue_df['revenue'].pct_change().dropna()
            if len(revenue_returns) > 0:
                features['revenue_volatility'] = revenue_returns.tail(volatility_window).std()
                features['revenue_trend'] = revenue_returns.tail(volatility_window).mean()
            else:
                features['revenue_volatility'] = 0
                features['revenue_trend'] = 0
        else:
            features['revenue_volatility'] = 0
            features['revenue_trend'] = 0
        
        # 季節性特徵
        if len(revenue_df) >= 12:
            current_month = as_of_dt.month
            same_month_revenues = revenue_df[revenue_df['date'].dt.month == current_month]['revenue']
            if len(same_month_revenues) > 1:
                features['seasonal_factor'] = same_month_revenues.mean() / revenue_df['revenue'].mean()
            else:
                features['seasonal_factor'] = 1.0
        else:
            features['seasonal_factor'] = 1.0
        
        # 移除NaN值
        features = {k: v if not pd.isna(v) else 0 for k, v in features.items()}
        
        logger.info(f"Generated {len(features)} revenue features for {stock_id} as of {as_of_date}")
        return features
    
    def get_revenue_prediction(self, 
                             stock_id: str,
                             target_month: str = None) -> Dict[str, Any]:
        """
        獲取營收預測結果
        
        Args:
            stock_id: 股票代碼
            target_month: 目標月份 (YYYY-MM)，None表示下個月
            
        Returns:
            營收預測結果字典
        """
        if self.revenue_predictor is None:
            logger.warning("Revenue predictor not available, returning default prediction")
            return self._get_default_prediction()
        
        try:
            # 使用現有的營收預測系統
            result = self.revenue_predictor.predict_monthly_growth(stock_id, target_month)
            
            if result.get('success', False):
                prediction = result.get('final_prediction', {})
                return {
                    'success': True,
                    'predicted_growth': prediction.get('growth_rate', 0),
                    'confidence': prediction.get('confidence', 'Low'),
                    'prediction_range': {
                        'lower': prediction.get('lower_bound', 0),
                        'upper': prediction.get('upper_bound', 0)
                    },
                    'method': 'eps_revenue_predictor',
                    'details': prediction
                }
            else:
                logger.warning(f"Revenue prediction failed for {stock_id}: {result.get('error', 'Unknown error')}")
                return self._get_default_prediction()
                
        except Exception as e:
            logger.error(f"Error in revenue prediction for {stock_id}: {e}")
            return self._get_default_prediction()
    
    def get_eps_prediction(self, 
                         stock_id: str,
                         target_quarter: str = None) -> Dict[str, Any]:
        """
        獲取EPS預測結果
        
        Args:
            stock_id: 股票代碼
            target_quarter: 目標季度 (YYYY-Q)，None表示下個季度
            
        Returns:
            EPS預測結果字典
        """
        if self.eps_predictor is None:
            logger.warning("EPS predictor not available, returning default prediction")
            return self._get_default_prediction()
        
        try:
            # 使用現有的EPS預測系統
            result = self.eps_predictor.predict_quarterly_growth(stock_id, target_quarter)
            
            if result.get('success', False):
                prediction = result.get('final_prediction', {})
                return {
                    'success': True,
                    'predicted_growth': prediction.get('growth_rate', 0),
                    'confidence': prediction.get('confidence', 'Low'),
                    'prediction_range': {
                        'lower': prediction.get('lower_bound', 0),
                        'upper': prediction.get('upper_bound', 0)
                    },
                    'method': 'eps_revenue_predictor',
                    'details': prediction
                }
            else:
                logger.warning(f"EPS prediction failed for {stock_id}: {result.get('error', 'Unknown error')}")
                return self._get_default_prediction()
                
        except Exception as e:
            logger.error(f"Error in EPS prediction for {stock_id}: {e}")
            return self._get_default_prediction()
    
    def get_combined_fundamental_features(self, 
                                        stock_id: str,
                                        as_of_date: str) -> Dict[str, float]:
        """
        獲取綜合基本面特徵（營收 + EPS預測）
        
        Args:
            stock_id: 股票代碼
            as_of_date: 預測時點 (YYYY-MM-DD)
            
        Returns:
            綜合基本面特徵字典
        """
        features = {}
        
        # 獲取營收特徵
        revenue_features = self.get_revenue_features(stock_id, as_of_date)
        features.update(revenue_features)
        
        # 獲取營收預測
        revenue_prediction = self.get_revenue_prediction(stock_id)
        if revenue_prediction['success']:
            features['predicted_revenue_growth'] = revenue_prediction['predicted_growth']
            features['revenue_prediction_confidence'] = self._confidence_to_numeric(revenue_prediction['confidence'])
            features['revenue_prediction_range'] = revenue_prediction['prediction_range']['upper'] - revenue_prediction['prediction_range']['lower']
        else:
            features['predicted_revenue_growth'] = 0
            features['revenue_prediction_confidence'] = 0.5
            features['revenue_prediction_range'] = 0
        
        # 獲取EPS預測
        eps_prediction = self.get_eps_prediction(stock_id)
        if eps_prediction['success']:
            features['predicted_eps_growth'] = eps_prediction['predicted_growth']
            features['eps_prediction_confidence'] = self._confidence_to_numeric(eps_prediction['confidence'])
            features['eps_prediction_range'] = eps_prediction['prediction_range']['upper'] - eps_prediction['prediction_range']['lower']
        else:
            features['predicted_eps_growth'] = 0
            features['eps_prediction_confidence'] = 0.5
            features['eps_prediction_range'] = 0
        
        logger.info(f"Generated {len(features)} combined fundamental features for {stock_id}")
        return features
    
    def _get_default_revenue_features(self) -> Dict[str, float]:
        """獲取預設營收特徵"""
        features = {}
        
        # 預設YoY特徵
        for period in self.config['revenue_features']['yoy_periods']:
            features[f'revenue_yoy_{period}m'] = 0
        
        # 預設MoM特徵
        for period in self.config['revenue_features']['mom_periods']:
            features[f'revenue_mom_{period}m'] = 0
        
        # 預設移動平均特徵
        for period in self.config['revenue_features']['ma_periods']:
            features[f'revenue_ma_{period}m'] = 0
            features[f'revenue_to_ma_{period}m'] = 0
        
        # 其他預設特徵
        features.update({
            'latest_revenue': 0,
            'revenue_volatility': 0,
            'revenue_trend': 0,
            'seasonal_factor': 1.0
        })
        
        return features
    
    def _get_default_prediction(self) -> Dict[str, Any]:
        """獲取預設預測結果"""
        return {
            'success': False,
            'predicted_growth': 0,
            'confidence': 'Low',
            'prediction_range': {'lower': 0, 'upper': 0},
            'method': 'default',
            'details': {}
        }
    
    def _confidence_to_numeric(self, confidence: str) -> float:
        """將信心水準轉換為數值"""
        confidence_map = {
            'High': 0.8,
            'Medium': 0.6,
            'Low': 0.4
        }
        return confidence_map.get(confidence, 0.5)
