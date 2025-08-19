# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 價格資料管理器
Stock Price Investment System - Price Data Manager
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .data_manager import DataManager
from ..config.settings import get_config

logger = logging.getLogger(__name__)

class PriceDataManager:
    """價格資料管理器 - 專門處理股價相關資料"""
    
    def __init__(self, data_manager: DataManager = None):
        """初始化價格資料管理器"""
        self.data_manager = data_manager or DataManager()
        self.config = get_config('feature')
        
        logger.info("PriceDataManager initialized")
    
    def get_monthly_price_data(self, 
                             stock_id: str,
                             start_date: str = None,
                             end_date: str = None,
                             months: int = None) -> pd.DataFrame:
        """
        獲取月度股價資料（每月最後一個交易日）
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            months: 回看月數
            
        Returns:
            月度股價DataFrame
        """
        # 獲取日度股價資料
        daily_df = self.data_manager.get_stock_prices(
            stock_id, start_date, end_date, 
            days=months*30 if months else None
        )
        
        if daily_df.empty:
            return pd.DataFrame()
        
        # 轉換為月度資料（每月最後一個交易日）
        daily_df['year_month'] = daily_df['date'].dt.to_period('M')
        monthly_df = daily_df.groupby('year_month').last().reset_index()
        
        # 重新設定日期為月末
        monthly_df['date'] = monthly_df['year_month'].dt.end_time
        monthly_df = monthly_df.drop('year_month', axis=1)
        
        # 計算月度報酬率（填充 NaN 為 0）
        monthly_df['monthly_return'] = monthly_df['close'].pct_change().fillna(0)
        
        logger.info(f"Generated {len(monthly_df)} monthly price records for {stock_id}")
        return monthly_df
    
    def calculate_technical_indicators(self, 
                                     price_df: pd.DataFrame,
                                     indicators: List[str] = None) -> pd.DataFrame:
        """
        計算技術指標
        
        Args:
            price_df: 股價DataFrame (需包含 open, high, low, close, volume)
            indicators: 要計算的指標清單
            
        Returns:
            包含技術指標的DataFrame
        """
        if price_df.empty:
            return price_df
        
        df = price_df.copy()
        tech_config = self.config['technical_features']
        
        # 預設指標
        if indicators is None:
            indicators = ['ma', 'rsi', 'macd', 'volume_indicators']
        
        # 移動平均線
        if 'ma' in indicators:
            for period in tech_config['ma_periods']:
                df[f'ma_{period}'] = df['close'].rolling(window=period).mean().bfill().fillna(0)
                df[f'price_to_ma_{period}'] = (df['close'] / df[f'ma_{period}'] - 1).fillna(0)
        
        # RSI
        if 'rsi' in indicators:
            df['rsi'] = self._calculate_rsi(df['close'], tech_config['rsi_period'])
        
        # MACD
        if 'macd' in indicators:
            macd_data = self._calculate_macd(
                df['close'], 
                tech_config['macd_fast'],
                tech_config['macd_slow'],
                tech_config['macd_signal']
            )
            df = pd.concat([df, macd_data], axis=1)
        
        # 成交量指標
        if 'volume_indicators' in indicators:
            df['volume_ma'] = df['volume'].rolling(window=tech_config['volume_ma_period']).mean().bfill().fillna(0)
            df['volume_ratio'] = (df['volume'] / df['volume_ma']).fillna(1.0)
            df['price_volume_trend'] = (((df['close'] - df['close'].shift(1)) / df['close'].shift(1)) * df['volume']).fillna(0)
        
        # 波動性指標
        if 'volatility' in indicators:
            df['price_volatility'] = df['close'].pct_change().rolling(window=20).std().fillna(0)
            df['high_low_ratio'] = ((df['high'] - df['low']) / df['close']).fillna(0)
        
        logger.info(f"Calculated technical indicators: {indicators}")
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean().fillna(0)
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean().fillna(0)

        # 避免除零
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # RSI 預設值 50
    
    def _calculate_macd(self, 
                       prices: pd.Series,
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> pd.DataFrame:
        """計算MACD指標"""
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line.fillna(0),
            'macd_signal': signal_line.fillna(0),
            'macd_histogram': histogram.fillna(0)
        })
    
    def get_price_features_for_prediction(self, 
                                        stock_id: str,
                                        as_of_date: str,
                                        lookback_months: int = 12) -> Dict:
        """
        獲取用於預測的價格特徵（避免未來函數）
        
        Args:
            stock_id: 股票代碼
            as_of_date: 預測時點 (YYYY-MM-DD)
            lookback_months: 回看月數
            
        Returns:
            價格特徵字典
        """
        # 計算開始日期
        as_of_dt = datetime.strptime(as_of_date, '%Y-%m-%d')
        start_dt = as_of_dt - timedelta(days=lookback_months * 30)
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # 獲取歷史價格資料（截止到as_of_date）
        price_df = self.data_manager.get_stock_prices(
            stock_id, start_date, as_of_date
        )
        
        if price_df.empty:
            logger.warning(f"No price data available for {stock_id} up to {as_of_date}")
            return {}
        
        # 計算技術指標
        try:
            price_df = self.calculate_technical_indicators(price_df)
        except Exception as e:
            logger.error(f"計算技術指標失敗: {e}")
            return {}

        if price_df.empty or len(price_df) == 0:
            logger.warning("技術指標計算後資料為空")
            return {}

        # 獲取最新的特徵值（as_of_date當天或之前最近的交易日）
        latest_data = price_df.iloc[-1]
        
        features = {
            # 價格相關
            'current_price': latest_data['close'],
            'price_change_1d': (latest_data['close'] - price_df.iloc[-2]['close']) / price_df.iloc[-2]['close'] if len(price_df) > 1 and price_df.iloc[-2]['close'] != 0 else 0,
            'price_change_5d': (latest_data['close'] - price_df.iloc[-6]['close']) / price_df.iloc[-6]['close'] if len(price_df) > 5 and price_df.iloc[-6]['close'] != 0 else 0,
            'price_change_20d': (latest_data['close'] - price_df.iloc[-21]['close']) / price_df.iloc[-21]['close'] if len(price_df) > 20 and price_df.iloc[-21]['close'] != 0 else 0,
            
            # 移動平均相關
            'price_to_ma_5': latest_data.get('price_to_ma_5', 0),
            'price_to_ma_20': latest_data.get('price_to_ma_20', 0),
            'price_to_ma_60': latest_data.get('price_to_ma_60', 0),
            
            # 技術指標
            'rsi': latest_data.get('rsi', 50),
            'macd': latest_data.get('macd', 0),
            'macd_signal': latest_data.get('macd_signal', 0),
            'macd_histogram': latest_data.get('macd_histogram', 0),
            
            # 成交量相關
            'volume_ratio': latest_data.get('volume_ratio', 1),
            'price_volume_trend': latest_data.get('price_volume_trend', 0),
            
            # 波動性
            'price_volatility': latest_data.get('price_volatility', 0),
            'high_low_ratio': latest_data.get('high_low_ratio', 0),
        }
        
        # 移除NaN值
        features = {k: v if not pd.isna(v) else 0 for k, v in features.items()}
        
        logger.info(f"Generated {len(features)} price features for {stock_id} as of {as_of_date}")
        return features
    
    def calculate_future_returns(self, 
                               stock_id: str,
                               start_date: str,
                               end_date: str,
                               holding_periods: List[int] = [20, 40, 60]) -> pd.DataFrame:
        """
        計算未來報酬率（用於訓練標籤）
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            holding_periods: 持有期間（天數）
            
        Returns:
            包含未來報酬率的DataFrame
        """
        # 獲取更長期間的價格資料（包含未來資料用於計算標籤）
        extended_end = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=max(holding_periods) + 30)).strftime('%Y-%m-%d')
        
        price_df = self.data_manager.get_stock_prices(stock_id, start_date, extended_end)
        
        if price_df.empty:
            return pd.DataFrame()
        
        # 計算各種持有期間的未來報酬率
        for period in holding_periods:
            price_df[f'future_return_{period}d'] = (
                price_df['close'].shift(-period) / price_df['close'] - 1
            )
        
        # 只保留原始時間範圍內的資料
        price_df = price_df[price_df['date'] <= end_date]
        
        logger.info(f"Calculated future returns for {stock_id} with periods {holding_periods}")
        return price_df
    
    def get_monthly_aligned_data(self, 
                               stock_id: str,
                               start_date: str,
                               end_date: str) -> pd.DataFrame:
        """
        獲取與月營收對齊的月度價格資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            月度對齊的價格資料
        """
        # 獲取月營收資料
        revenue_df = self.data_manager.get_monthly_revenue(stock_id, start_date, end_date)
        
        if revenue_df.empty:
            return pd.DataFrame()
        
        # 獲取對應的月度價格資料
        monthly_prices = []
        
        for _, row in revenue_df.iterrows():
            year_month = f"{row['revenue_year']}-{row['revenue_month']:02d}"
            
            # 獲取該月的價格資料（月末價格）
            month_start = f"{year_month}-01"
            month_end = (datetime.strptime(month_start, '%Y-%m-%d') + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            month_end_str = month_end.strftime('%Y-%m-%d')
            
            month_prices = self.data_manager.get_stock_prices(stock_id, month_start, month_end_str)
            
            if not month_prices.empty:
                # 取該月最後一個交易日的價格
                last_price = month_prices.iloc[-1]
                
                monthly_prices.append({
                    'year_month': year_month,
                    'date': last_price['date'],
                    'close': last_price['close'],
                    'volume': last_price['volume'],
                    'revenue': row['revenue'],
                    'revenue_yoy': row.get('revenue_yoy', 0),
                    'revenue_mom': row.get('revenue_mom', 0)
                })
        
        if monthly_prices:
            aligned_df = pd.DataFrame(monthly_prices)
            aligned_df['date'] = pd.to_datetime(aligned_df['date'])
            aligned_df = aligned_df.sort_values('date').reset_index(drop=True)
            
            # 計算價格變化（填充 NaN 為 0）
            aligned_df['price_return'] = aligned_df['close'].pct_change().fillna(0)
            
            logger.info(f"Generated {len(aligned_df)} monthly aligned records for {stock_id}")
            return aligned_df
        
        return pd.DataFrame()
