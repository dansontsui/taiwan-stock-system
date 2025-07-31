#!/usr/bin/env python3
"""
目標變數生成器

負責生成機器學習的目標變數：
- 預測在財務資料公布後20個交易日內，股價上漲超過5%的股票
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

from ..utils.database import DatabaseManager
from ..utils.helpers import calculate_trading_days, get_next_trading_day
try:
    from ...config.config import FEATURE_CONFIG
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    sys.path.insert(0, project_root)
    from config.config import FEATURE_CONFIG

logger = logging.getLogger(__name__)

class TargetGenerator:
    """目標變數生成器"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化目標變數生成器
        
        Args:
            db_manager: 資料庫管理器
        """
        self.db_manager = db_manager or DatabaseManager()
        self.config = FEATURE_CONFIG['target_definition']
        
    def generate_targets(self, stock_id: str, feature_dates: List[str]) -> pd.DataFrame:
        """
        為單一股票生成目標變數
        
        Args:
            stock_id: 股票代碼
            feature_dates: 特徵計算日期列表
            
        Returns:
            包含目標變數的DataFrame
        """
        logger.debug(f"為股票 {stock_id} 生成目標變數")
        
        results = []
        
        for feature_date in feature_dates:
            try:
                target = self._calculate_target(stock_id, feature_date)
                results.append({
                    'stock_id': stock_id,
                    'feature_date': feature_date,
                    'target': target['target'],
                    'max_return': target['max_return'],
                    'max_return_date': target['max_return_date'],
                    'trading_days_count': target['trading_days_count']
                })
            except Exception as e:
                logger.warning(f"計算股票 {stock_id} 在 {feature_date} 的目標變數失敗: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def _calculate_target(self, stock_id: str, feature_date: str) -> Dict:
        """
        計算單一日期的目標變數
        
        Args:
            stock_id: 股票代碼
            feature_date: 特徵計算日期
            
        Returns:
            目標變數資訊字典
        """
        # 計算預測期間的開始和結束日期
        prediction_start = get_next_trading_day(feature_date, 1)  # 下一個交易日
        prediction_end = get_next_trading_day(feature_date, self.config['prediction_days'])
        
        # 獲取預測期間的股價資料
        price_df = self.db_manager.get_stock_prices(stock_id, prediction_start, prediction_end)
        
        if price_df.empty:
            return {
                'target': 0,
                'max_return': 0,
                'max_return_date': None,
                'trading_days_count': 0
            }
        
        # 確保有足夠的交易日資料
        if len(price_df) < self.config['min_trading_days']:
            return {
                'target': 0,
                'max_return': 0,
                'max_return_date': None,
                'trading_days_count': len(price_df)
            }
        
        # 獲取基準價格（特徵日期的收盤價）
        base_price = self._get_base_price(stock_id, feature_date)
        if base_price is None or base_price <= 0:
            return {
                'target': 0,
                'max_return': 0,
                'max_return_date': None,
                'trading_days_count': len(price_df)
            }
        
        # 計算預測期間內的最大報酬率
        max_price = price_df['high_price'].max()
        max_return = (max_price - base_price) / base_price
        
        # 找到最大報酬率發生的日期
        max_return_idx = price_df['high_price'].idxmax()
        max_return_date = price_df.loc[max_return_idx, 'date']
        
        # 判斷是否達到目標報酬率
        target = 1 if max_return >= self.config['target_return'] else 0
        
        return {
            'target': target,
            'max_return': max_return,
            'max_return_date': max_return_date,
            'trading_days_count': len(price_df)
        }
    
    def _get_base_price(self, stock_id: str, feature_date: str) -> Optional[float]:
        """
        獲取基準價格（特徵日期的收盤價）
        
        Args:
            stock_id: 股票代碼
            feature_date: 特徵日期
            
        Returns:
            基準價格
        """
        # 獲取特徵日期前後幾天的股價資料，以防特徵日期不是交易日
        start_date = (pd.to_datetime(feature_date) - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (pd.to_datetime(feature_date) + timedelta(days=5)).strftime('%Y-%m-%d')
        
        price_df = self.db_manager.get_stock_prices(stock_id, start_date, end_date)
        
        if price_df.empty:
            return None
        
        # 找到最接近特徵日期的交易日
        price_df['date'] = pd.to_datetime(price_df['date'])
        feature_dt = pd.to_datetime(feature_date)
        
        # 找到特徵日期當天或之前最近的交易日
        valid_dates = price_df[price_df['date'] <= feature_dt]
        
        if valid_dates.empty:
            # 如果沒有當天或之前的資料，使用之後最近的交易日
            valid_dates = price_df[price_df['date'] > feature_dt]
            if valid_dates.empty:
                return None
        
        # 選擇最接近的日期
        closest_date_idx = (valid_dates['date'] - feature_dt).abs().idxmin()
        return price_df.loc[closest_date_idx, 'close_price']
    
    def generate_batch_targets(self, stock_ids: List[str], feature_dates: List[str]) -> pd.DataFrame:
        """
        批次生成多個股票的目標變數
        
        Args:
            stock_ids: 股票代碼列表
            feature_dates: 特徵計算日期列表
            
        Returns:
            所有股票的目標變數DataFrame
        """
        logger.info(f"批次生成 {len(stock_ids)} 個股票的目標變數")
        
        all_targets = []
        
        for i, stock_id in enumerate(stock_ids):
            try:
                # 排除00開頭的股票
                if stock_id.startswith('00'):
                    logger.debug(f"跳過ETF股票: {stock_id}")
                    continue

                # 顯示當前處理的股票
                logger.info(f"處理股票 {i+1}/{len(stock_ids)}: {stock_id}")

                targets_df = self.generate_targets(stock_id, feature_dates)
                if not targets_df.empty:
                    all_targets.append(targets_df)
                    logger.info(f"股票 {stock_id} 生成 {len(targets_df)} 筆目標變數")
                else:
                    logger.warning(f"股票 {stock_id} 沒有生成目標變數")

                # 階段性進度顯示
                if (i + 1) % 50 == 0:
                    logger.info(f"階段進度: 已完成 {i + 1}/{len(stock_ids)} 個股票 ({(i+1)/len(stock_ids)*100:.1f}%)")

            except Exception as e:
                logger.error(f"生成股票 {stock_id} 目標變數失敗: {e}")
                continue
        
        if all_targets:
            result_df = pd.concat(all_targets, ignore_index=True)
            logger.info(f"成功生成 {len(result_df)} 筆目標變數")
            return result_df
        else:
            logger.warning("沒有成功生成任何目標變數")
            return pd.DataFrame()
    
    def analyze_target_distribution(self, targets_df: pd.DataFrame) -> Dict:
        """
        分析目標變數的分布
        
        Args:
            targets_df: 目標變數DataFrame
            
        Returns:
            分析結果字典
        """
        if targets_df.empty:
            return {}
        
        total_samples = len(targets_df)
        positive_samples = (targets_df['target'] == 1).sum()
        negative_samples = (targets_df['target'] == 0).sum()
        
        # 計算統計資訊
        max_returns = targets_df['max_return'].dropna()
        
        analysis = {
            'total_samples': total_samples,
            'positive_samples': positive_samples,
            'negative_samples': negative_samples,
            'positive_ratio': positive_samples / total_samples if total_samples > 0 else 0,
            'max_return_stats': {
                'mean': max_returns.mean() if not max_returns.empty else 0,
                'std': max_returns.std() if not max_returns.empty else 0,
                'min': max_returns.min() if not max_returns.empty else 0,
                'max': max_returns.max() if not max_returns.empty else 0,
                'median': max_returns.median() if not max_returns.empty else 0
            },
            'trading_days_stats': {
                'mean': targets_df['trading_days_count'].mean(),
                'min': targets_df['trading_days_count'].min(),
                'max': targets_df['trading_days_count'].max()
            }
        }
        
        logger.info(f"目標變數分析: 總樣本 {total_samples}, 正樣本 {positive_samples} ({analysis['positive_ratio']:.2%})")
        
        return analysis
    
    def create_time_series_targets(self, stock_ids: List[str], 
                                 start_date: str, end_date: str, 
                                 frequency: str = 'monthly') -> pd.DataFrame:
        """
        創建時序目標變數
        
        Args:
            stock_ids: 股票代碼列表
            start_date: 開始日期
            end_date: 結束日期
            frequency: 頻率 ('monthly', 'quarterly')
            
        Returns:
            時序目標變數DataFrame
        """
        logger.info(f"創建時序目標變數: {start_date} ~ {end_date}, 頻率: {frequency}")

        # 生成特徵日期序列
        if frequency == 'monthly':
            feature_dates = pd.date_range(start=start_date, end=end_date, freq='ME')  # 月末
        elif frequency == 'quarterly':
            feature_dates = pd.date_range(start=start_date, end=end_date, freq='QE')  # 季末
        else:
            raise ValueError(f"不支援的頻率: {frequency}")

        feature_dates = [date.strftime('%Y-%m-%d') for date in feature_dates]

        logger.info(f"生成 {len(feature_dates)} 個時間點的目標變數: {feature_dates}")
        logger.info(f"將處理 {len(stock_ids)} 檔股票 × {len(feature_dates)} 個時間點 = {len(stock_ids) * len(feature_dates)} 個目標變數")

        # 批次生成目標變數
        return self.generate_batch_targets(stock_ids, feature_dates)
