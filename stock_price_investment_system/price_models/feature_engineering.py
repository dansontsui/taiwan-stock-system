# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 特徵工程模組
Stock Price Investment System - Feature Engineering Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

from ..data.data_manager import DataManager
from ..data.price_data import PriceDataManager
from ..data.revenue_integration import RevenueIntegration
from ..config.settings import get_config

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """特徵工程師 - 生成用於股價預測的特徵"""
    
    def __init__(self, 
                 data_manager: DataManager = None,
                 price_manager: PriceDataManager = None,
                 revenue_integration: RevenueIntegration = None):
        """初始化特徵工程師"""
        self.data_manager = data_manager or DataManager()
        self.price_manager = price_manager or PriceDataManager(self.data_manager)
        self.revenue_integration = revenue_integration or RevenueIntegration(self.data_manager)
        
        self.config = get_config()
        self.feature_config = self.config['feature']
        
        logger.info("FeatureEngineer initialized")
    
    def generate_features(self, 
                         stock_id: str,
                         as_of_date: str,
                         lookback_months: int = 24) -> Dict[str, float]:
        """
        生成完整的預測特徵集
        
        Args:
            stock_id: 股票代碼
            as_of_date: 預測時點 (YYYY-MM-DD)
            lookback_months: 回看月數
            
        Returns:
            特徵字典
        """
        logger.info(f"Generating features for {stock_id} as of {as_of_date}")
        
        features = {}
        
        # 1. 營收特徵
        try:
            revenue_features = self.revenue_integration.get_combined_fundamental_features(
                stock_id, as_of_date
            )
            features.update(revenue_features)
            logger.debug(f"Added {len(revenue_features)} revenue features")
        except Exception as e:
            logger.warning(f"Failed to generate revenue features: {e}")
        
        # 2. 技術特徵
        try:
            technical_features = self.price_manager.get_price_features_for_prediction(
                stock_id, as_of_date, lookback_months
            )
            features.update(technical_features)
            logger.debug(f"Added {len(technical_features)} technical features")
        except Exception as e:
            logger.warning(f"Failed to generate technical features: {e}")
        
        # 3. 產業特徵
        try:
            industry_features = self._generate_industry_features(stock_id, as_of_date)
            features.update(industry_features)
            logger.debug(f"Added {len(industry_features)} industry features")
        except Exception as e:
            logger.warning(f"Failed to generate industry features: {e}")
        
        # 4. 時間特徵
        try:
            time_features = self._generate_time_features(as_of_date)
            features.update(time_features)
            logger.debug(f"Added {len(time_features)} time features")
        except Exception as e:
            logger.warning(f"Failed to generate time features: {e}")
        
        # 5. 交互特徵
        try:
            interaction_features = self._generate_interaction_features(features)
            features.update(interaction_features)
            logger.debug(f"Added {len(interaction_features)} interaction features")
        except Exception as e:
            logger.warning(f"Failed to generate interaction features: {e}")
        
        # 清理特徵
        features = self._clean_features(features)
        
        logger.info(f"Generated {len(features)} total features for {stock_id}")
        return features
    
    def generate_batch_features(self, 
                              stock_ids: List[str],
                              as_of_date: str,
                              lookback_months: int = 24) -> pd.DataFrame:
        """
        批量生成特徵
        
        Args:
            stock_ids: 股票代碼清單
            as_of_date: 預測時點
            lookback_months: 回看月數
            
        Returns:
            特徵DataFrame
        """
        logger.info(f"Generating batch features for {len(stock_ids)} stocks as of {as_of_date}")
        
        feature_list = []
        
        for stock_id in stock_ids:
            try:
                features = self.generate_features(stock_id, as_of_date, lookback_months)
                features['stock_id'] = stock_id
                features['as_of_date'] = as_of_date
                feature_list.append(features)
            except Exception as e:
                logger.error(f"Failed to generate features for {stock_id}: {e}")
                continue
        
        if feature_list:
            df = pd.DataFrame(feature_list)
            logger.info(f"Generated batch features: {df.shape}")
            return df
        else:
            logger.warning("No features generated for any stock")
            return pd.DataFrame()
    
    def generate_training_dataset(self, 
                                stock_ids: List[str],
                                start_date: str,
                                end_date: str,
                                target_periods: List[int] = [20],
                                frequency: str = 'monthly') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        生成訓練資料集
        
        Args:
            stock_ids: 股票代碼清單
            start_date: 開始日期
            end_date: 結束日期
            target_periods: 目標期間（天數）
            frequency: 頻率 ('monthly' 或 'daily')
            
        Returns:
            (特徵DataFrame, 標籤DataFrame)
        """
        logger.info(f"Generating training dataset for {len(stock_ids)} stocks from {start_date} to {end_date}")
        
        feature_list = []
        target_list = []
        
        # 生成時間序列
        if frequency == 'monthly':
            dates = pd.date_range(start=start_date, end=end_date, freq='M')
        else:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        for stock_id in stock_ids:
            logger.debug(f"Processing {stock_id}")
            
            for date in dates:
                as_of_date = date.strftime('%Y-%m-%d')
                
                try:
                    # 生成特徵
                    features = self.generate_features(stock_id, as_of_date)
                    if not features:
                        continue
                    
                    features['stock_id'] = stock_id
                    features['as_of_date'] = as_of_date
                    
                    # 生成標籤
                    targets = self._generate_targets(stock_id, as_of_date, target_periods)
                    if not targets:
                        continue
                    
                    targets['stock_id'] = stock_id
                    targets['as_of_date'] = as_of_date
                    
                    feature_list.append(features)
                    target_list.append(targets)
                    
                except Exception as e:
                    logger.debug(f"Failed to process {stock_id} on {as_of_date}: {e}")
                    continue
        
        if feature_list and target_list:
            feature_df = pd.DataFrame(feature_list)
            target_df = pd.DataFrame(target_list)

            # 清理 DataFrame 中的 NaN 值
            original_shape = feature_df.shape

            # 1. 填充數值欄位的 NaN
            numeric_columns = feature_df.select_dtypes(include=[np.number]).columns
            feature_df[numeric_columns] = feature_df[numeric_columns].fillna(0)

            # 2. 填充字串欄位的 NaN
            string_columns = feature_df.select_dtypes(include=['object']).columns
            feature_df[string_columns] = feature_df[string_columns].fillna('')

            # 3. 處理無限值
            feature_df = feature_df.replace([np.inf, -np.inf], 0)

            # 4. 清理目標變數的 NaN
            target_numeric_cols = target_df.select_dtypes(include=[np.number]).columns
            before_target_rows = len(target_df)
            target_df = target_df.dropna(subset=target_numeric_cols)
            after_target_rows = len(target_df)

            if before_target_rows != after_target_rows:
                logger.info(f"移除了 {before_target_rows - after_target_rows} 筆目標變數為 NaN 的樣本")
                # 對應調整特徵資料
                feature_df = feature_df.loc[target_df.index]

            # 最終檢查
            nan_counts = feature_df.isnull().sum()
            if nan_counts.sum() > 0:
                logger.warning(f"特徵資料仍有 NaN 值: {nan_counts[nan_counts > 0].to_dict()}")
                # 強制填充剩餘的 NaN
                feature_df = feature_df.fillna(0)

            inf_counts = np.isinf(feature_df.select_dtypes(include=[np.number])).sum()
            if inf_counts.sum() > 0:
                logger.warning(f"特徵資料仍有無限值: {inf_counts[inf_counts > 0].to_dict()}")
                # 強制處理剩餘的無限值
                feature_df = feature_df.replace([np.inf, -np.inf], 0)

            logger.info(f"Generated training dataset: {feature_df.shape} features, {target_df.shape} targets")
            logger.info(f"NaN 清理: {original_shape} -> {feature_df.shape}")
            return feature_df, target_df
        else:
            logger.warning("No training data generated")
            return pd.DataFrame(), pd.DataFrame()
    
    def _generate_industry_features(self, stock_id: str, as_of_date: str) -> Dict[str, float]:
        """生成產業特徵"""
        features = {}
        
        if not self.feature_config['industry_features']['enable_industry_encoding']:
            return features
        
        try:
            # 獲取股票基本資訊
            basic_info = self.data_manager.get_stock_basic_info(stock_id)
            
            # 產業編碼（這裡需要根據實際資料庫結構調整）
            # 暫時使用股票代碼的前兩位作為產業代碼
            industry_code = stock_id[:2] if len(stock_id) >= 2 else '00'
            
            # One-hot編碼主要產業
            major_industries = ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
                              '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']
            
            for industry in major_industries:
                features[f'industry_{industry}'] = 1.0 if industry_code == industry else 0.0
            
            # 上市年限特徵
            if self.feature_config['industry_features']['enable_listing_age_features']:
                first_year = basic_info.get('first_year')
                if first_year:
                    current_year = datetime.strptime(as_of_date, '%Y-%m-%d').year
                    listing_age = current_year - int(first_year)
                    features['listing_age_years'] = max(0, listing_age)
                    features['is_new_listing'] = 1.0 if listing_age <= 3 else 0.0
                else:
                    features['listing_age_years'] = 0
                    features['is_new_listing'] = 0.0
            
        except Exception as e:
            logger.debug(f"Error generating industry features for {stock_id}: {e}")
        
        return features
    
    def _generate_time_features(self, as_of_date: str) -> Dict[str, float]:
        """生成時間特徵"""
        features = {}
        
        try:
            dt = datetime.strptime(as_of_date, '%Y-%m-%d')
            
            # 月份特徵
            features['month'] = dt.month
            features['quarter'] = (dt.month - 1) // 3 + 1
            
            # 季節性特徵
            features['is_q1'] = 1.0 if dt.month in [1, 2, 3] else 0.0
            features['is_q2'] = 1.0 if dt.month in [4, 5, 6] else 0.0
            features['is_q3'] = 1.0 if dt.month in [7, 8, 9] else 0.0
            features['is_q4'] = 1.0 if dt.month in [10, 11, 12] else 0.0
            
            # 年度特徵
            features['year'] = dt.year
            features['year_progress'] = (dt.month - 1) / 11  # 0-1之間
            
        except Exception as e:
            logger.debug(f"Error generating time features: {e}")
        
        return features
    
    def _generate_interaction_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """生成交互特徵"""
        interaction_features = {}
        
        try:
            # 營收與技術指標交互
            if 'predicted_revenue_growth' in features and 'rsi' in features:
                interaction_features['revenue_growth_rsi'] = features['predicted_revenue_growth'] * features['rsi'] / 100
            
            if 'revenue_yoy_12m' in features and 'price_to_ma_20' in features:
                interaction_features['revenue_yoy_price_momentum'] = features['revenue_yoy_12m'] * features['price_to_ma_20']
            
            # 成交量與價格動量交互
            if 'volume_ratio' in features and 'price_change_20d' in features:
                interaction_features['volume_price_momentum'] = features['volume_ratio'] * features['price_change_20d']
            
            # 預測信心與技術確認交互
            if 'revenue_prediction_confidence' in features and 'macd_histogram' in features:
                interaction_features['confidence_technical_confirm'] = features['revenue_prediction_confidence'] * np.sign(features['macd_histogram'])
            
        except Exception as e:
            logger.debug(f"Error generating interaction features: {e}")
        
        return interaction_features
    
    def _generate_targets(self, stock_id: str, as_of_date: str, target_periods: List[int]) -> Dict[str, float]:
        """生成目標變數（未來報酬率）"""
        targets = {}
        
        try:
            # 計算未來報酬率
            future_returns_df = self.price_manager.calculate_future_returns(
                stock_id, as_of_date, as_of_date, target_periods
            )
            
            if not future_returns_df.empty:
                # 找到對應日期的記錄
                target_row = future_returns_df[future_returns_df['date'] == as_of_date]
                
                if target_row.empty:
                    # 嘗試用最近的日期（<= as_of_date 的最後一筆）
                    try:
                        as_of_dt = pd.to_datetime(as_of_date)
                        future_returns_df['date'] = pd.to_datetime(future_returns_df['date'])
                        before_df = future_returns_df[future_returns_df['date'] <= as_of_dt]
                        if not before_df.empty:
                            target_row = before_df.iloc[[-1]]
                    except Exception:
                        pass

                if not target_row.empty:
                    for period in target_periods:
                        col_name = f'future_return_{period}d'
                        if col_name in target_row.columns:
                            raw_value = target_row.iloc[0][col_name]
                            if pd.isna(raw_value) or np.isinf(raw_value):
                                targets[f'target_{period}d'] = 0.0  # 用0代替NaN/Inf
                            else:
                                # 限制極值範圍，避免過大的報酬率
                                clean_value = float(raw_value)
                                clean_value = max(-1.0, min(1.0, clean_value))  # 限制在-100%到100%之間
                                targets[f'target_{period}d'] = clean_value
                        else:
                            targets[f'target_{period}d'] = 0.0  # 缺少欄位時用0
                else:
                    for period in target_periods:
                        targets[f'target_{period}d'] = 0.0  # 無資料時用0
            else:
                for period in target_periods:
                    targets[f'target_{period}d'] = 0.0  # 無資料時用0

        except Exception as e:
            logger.debug(f"Error generating targets for {stock_id} on {as_of_date}: {e}")
            for period in target_periods:
                targets[f'target_{period}d'] = 0.0  # 異常時用0
        
        return targets
    
    def _clean_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """清理特徵"""
        cleaned_features = {}
        
        for key, value in features.items():
            # 處理NaN值
            if pd.isna(value):
                cleaned_features[key] = 0.0
            # 處理無限值
            elif np.isinf(value):
                cleaned_features[key] = 0.0
            # 處理過大的值
            elif abs(value) > 1e6:
                cleaned_features[key] = np.sign(value) * 1e6
            else:
                cleaned_features[key] = float(value)
        
        return cleaned_features
    
    def get_feature_names(self) -> List[str]:
        """獲取特徵名稱清單"""
        # 這裡返回所有可能的特徵名稱
        feature_names = []
        
        # 營收特徵
        for period in self.feature_config['revenue_features']['yoy_periods']:
            feature_names.append(f'revenue_yoy_{period}m')
        
        for period in self.feature_config['revenue_features']['mom_periods']:
            feature_names.append(f'revenue_mom_{period}m')
        
        for period in self.feature_config['revenue_features']['ma_periods']:
            feature_names.extend([f'revenue_ma_{period}m', f'revenue_to_ma_{period}m'])
        
        feature_names.extend([
            'latest_revenue', 'revenue_volatility', 'revenue_trend', 'seasonal_factor',
            'predicted_revenue_growth', 'revenue_prediction_confidence', 'revenue_prediction_range',
            'predicted_eps_growth', 'eps_prediction_confidence', 'eps_prediction_range'
        ])
        
        # 技術特徵
        feature_names.extend([
            'current_price', 'price_change_1d', 'price_change_5d', 'price_change_20d',
            'price_to_ma_5', 'price_to_ma_20', 'price_to_ma_60',
            'rsi', 'macd', 'macd_signal', 'macd_histogram',
            'volume_ratio', 'price_volume_trend', 'price_volatility', 'high_low_ratio'
        ])
        
        # 產業特徵
        major_industries = ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
                          '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']
        for industry in major_industries:
            feature_names.append(f'industry_{industry}')
        
        feature_names.extend(['listing_age_years', 'is_new_listing'])
        
        # 時間特徵
        feature_names.extend([
            'month', 'quarter', 'is_q1', 'is_q2', 'is_q3', 'is_q4',
            'year', 'year_progress'
        ])
        
        # 交互特徵
        feature_names.extend([
            'revenue_growth_rsi', 'revenue_yoy_price_momentum',
            'volume_price_momentum', 'confidence_technical_confirm'
        ])
        
        return feature_names
