#!/usr/bin/env python3
"""
特徵工程模組

負責從原始財務資料中提取和構建機器學習特徵，包括：
1. 月營收特徵：YoY成長率、MoM成長率、連續成長月數
2. 財務比率特徵：ROE、ROA、毛利率、營業利益率
3. 現金流特徵：營運現金流、自由現金流、現金流比率
4. 技術指標特徵：股價波動率、RSI、動量指標
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.database import DatabaseManager
from ..utils.helpers import (
    calculate_returns, calculate_volatility, calculate_rsi,
    calculate_moving_average, calculate_momentum, get_financial_quarter
)
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

class FeatureEngineer:
    """特徵工程器"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化特徵工程器
        
        Args:
            db_manager: 資料庫管理器
        """
        self.db_manager = db_manager or DatabaseManager()
        self.config = FEATURE_CONFIG
        
    def generate_features(self, stock_id: str, end_date: str) -> pd.DataFrame:
        """
        為單一股票生成所有特徵

        Args:
            stock_id: 股票代碼
            end_date: 特徵計算的截止日期

        Returns:
            特徵DataFrame
        """
        logger.info(f"為股票 {stock_id} 生成特徵，截止日期: {end_date}")

        # 智能計算實際可用的資料範圍
        actual_start_date, actual_end_date = self._calculate_smart_date_range(stock_id, end_date)

        if actual_start_date is None:
            logger.warning(f"股票 {stock_id} 沒有足夠的歷史資料，跳過特徵生成")
            return pd.DataFrame()

        # 如果調整了日期範圍，記錄信息
        original_start = self._calculate_start_date(end_date)
        if actual_start_date != original_start:
            logger.info(f"[SMART] 股票 {stock_id} 智能調整資料範圍: {actual_start_date} ~ {actual_end_date} (原始: {original_start} ~ {end_date})")

        # 收集所有原始資料
        raw_data = self._collect_raw_data(stock_id, actual_start_date, actual_end_date)

        # 最終驗證資料是否足夠
        if not self._validate_raw_data(raw_data):
            logger.warning(f"股票 {stock_id} 即使調整日期後資料仍不足，跳過特徵生成")
            return pd.DataFrame()

        # 生成各類特徵
        features = {}
        
        # 記錄資料完整性
        data_completeness = {
            'monthly_revenue': not raw_data['monthly_revenue'].empty,
            'financial_statements': not raw_data['financial_statements'].empty,
            'balance_sheets': not raw_data['balance_sheets'].empty,
            'cash_flow': not raw_data['cash_flow'].empty,
            'stock_prices': not raw_data['stock_prices'].empty
        }

        missing_data = [k for k, v in data_completeness.items() if not v]
        if missing_data:
            logger.warning(f"股票 {stock_id} 缺少資料: {', '.join(missing_data)}")

            # 記錄到專門的缺失資料日誌
            missing_log_file = Path("logs/missing_data.log")
            missing_log_file.parent.mkdir(exist_ok=True)

            with open(missing_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{pd.Timestamp.now()},{stock_id},{','.join(missing_data)}\n")

        # 1. 月營收特徵 (如果有營收資料)
        if data_completeness['monthly_revenue']:
            revenue_features = self._generate_revenue_features(raw_data['monthly_revenue'])
            features.update(revenue_features)
            logger.info(f"股票 {stock_id} 生成 {len(revenue_features)} 個營收特徵")
        else:
            logger.warning(f"股票 {stock_id} 沒有營收資料，跳過營收特徵")

        # 2. 財務比率特徵 (如果有財務資料)
        if data_completeness['financial_statements']:
            financial_features = self._generate_financial_features(
                raw_data['financial_statements'],
                raw_data['balance_sheets']
            )
            features.update(financial_features)
            logger.info(f"股票 {stock_id} 生成 {len(financial_features)} 個財務特徵")
        else:
            logger.warning(f"股票 {stock_id} 沒有財務報表資料，跳過財務特徵")

        # 3. 現金流特徵 (如果有現金流資料)
        if data_completeness['cash_flow']:
            cashflow_features = self._generate_cashflow_features(raw_data['cash_flow'])
            features.update(cashflow_features)
            logger.info(f"股票 {stock_id} 生成 {len(cashflow_features)} 個現金流特徵")
        else:
            logger.warning(f"股票 {stock_id} 沒有現金流資料，跳過現金流特徵")
        
        # 4. 技術指標特徵
        technical_features = self._generate_technical_features(raw_data['stock_prices'])
        features.update(technical_features)
        
        # 5. 基本資訊特徵
        basic_features = self._generate_basic_features(stock_id, end_date)
        features.update(basic_features)
        
        # 組合成DataFrame
        feature_df = pd.DataFrame([features])
        feature_df['stock_id'] = stock_id
        feature_df['feature_date'] = end_date
        
        logger.info(f"股票 {stock_id} 生成 {len(features)} 個特徵")
        return feature_df
    
    def _calculate_start_date(self, end_date: str) -> str:
        """計算需要的歷史資料開始日期"""
        end_dt = pd.to_datetime(end_date)
        # 回看2年的資料以確保有足夠的歷史資料計算特徵
        start_dt = end_dt - timedelta(days=2*365)
        return start_dt.strftime('%Y-%m-%d')

    def _calculate_smart_date_range(self, stock_id: str, end_date: str) -> tuple:
        """
        智能計算股票的實際可用資料範圍

        Args:
            stock_id: 股票代碼
            end_date: 期望的結束日期

        Returns:
            (actual_start_date, actual_end_date) 或 (None, None) 如果資料不足
        """
        # 1. 先檢查股票的實際資料範圍
        actual_range = self._get_stock_data_range(stock_id)
        if not actual_range:
            return None, None

        stock_first_date, stock_last_date = actual_range

        # 2. 計算理想的開始日期（往前推2年）
        ideal_start_date = self._calculate_start_date(end_date)

        # 3. 智能調整開始日期
        # 使用股票實際開始日期和理想開始日期中較晚的那個
        actual_start_date = max(stock_first_date, ideal_start_date)

        # 4. 調整結束日期
        # 使用股票實際結束日期和期望結束日期中較早的那個
        actual_end_date = min(stock_last_date, end_date)

        # 5. 檢查調整後的時間範圍是否足夠
        start_dt = pd.to_datetime(actual_start_date)
        end_dt = pd.to_datetime(actual_end_date)
        days_diff = (end_dt - start_dt).days

        # 至少需要90天的資料來計算技術指標
        if days_diff < 90:
            logger.debug(f"股票 {stock_id} 調整後的時間範圍太短: {days_diff} 天")
            return None, None

        return actual_start_date, actual_end_date

    def _get_stock_data_range(self, stock_id: str) -> tuple:
        """
        獲取股票的實際資料日期範圍

        Returns:
            (first_date, last_date) 或 None 如果沒有資料
        """
        try:
            # 查詢股票的資料範圍
            query = """
            SELECT MIN(date) as first_date, MAX(date) as last_date
            FROM stock_prices
            WHERE stock_id = ?
            """

            with self.db_manager.get_connection() as conn:
                result = pd.read_sql_query(query, conn, params=[stock_id])

            if result.empty or pd.isna(result.iloc[0]['first_date']):
                return None

            first_date = result.iloc[0]['first_date']
            last_date = result.iloc[0]['last_date']

            return first_date, last_date

        except Exception as e:
            logger.error(f"獲取股票 {stock_id} 資料範圍失敗: {e}")
            return None
    
    def _collect_raw_data(self, stock_id: str, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """收集原始資料"""
        logger.debug(f"收集股票 {stock_id} 原始資料: {start_date} ~ {end_date}")
        
        return {
            'stock_prices': self.db_manager.get_stock_prices(stock_id, start_date, end_date),
            'monthly_revenue': self.db_manager.get_monthly_revenue(stock_id, start_date, end_date),
            'financial_statements': self.db_manager.get_financial_statements(stock_id, start_date, end_date),
            'balance_sheets': self.db_manager.get_balance_sheets(stock_id, start_date, end_date),
            'cash_flow': self.db_manager.get_cash_flow_statements(stock_id, start_date, end_date)
        }
    
    def _validate_raw_data(self, raw_data: Dict[str, pd.DataFrame]) -> bool:
        """驗證原始資料是否足夠"""
        # 只檢查股價資料（最基本的要求）
        if 'stock_prices' not in raw_data or raw_data['stock_prices'].empty:
            return False

        # 檢查股價資料數量是否足夠 (降低到30天，因為需要計算技術指標)
        if len(raw_data['stock_prices']) < 30:
            return False

        # 移除過於嚴格的日期限制，讓系統能處理更多歷史資料
        # 只要有足夠數量的資料就可以生成特徵
        return True
    
    def _generate_revenue_features(self, revenue_df: pd.DataFrame) -> Dict[str, float]:
        """生成月營收特徵"""
        if revenue_df.empty:
            return {}
        
        features = {}
        config = self.config['revenue_features']
        
        # 排序資料
        revenue_df = revenue_df.sort_values(['revenue_year', 'revenue_month'])
        
        # 最近的營收成長率
        if len(revenue_df) >= 2:
            latest_revenue = revenue_df.iloc[-1]['revenue']
            prev_revenue = revenue_df.iloc[-2]['revenue']
            features['revenue_mom_latest'] = (latest_revenue - prev_revenue) / prev_revenue if prev_revenue > 0 else 0
        
        # 年增率特徵
        if 'revenue_growth_yoy' in revenue_df.columns:
            yoy_growth = revenue_df['revenue_growth_yoy'].dropna()
            if not yoy_growth.empty:
                features['revenue_yoy_mean'] = yoy_growth.mean()
                features['revenue_yoy_std'] = yoy_growth.std()
                features['revenue_yoy_latest'] = yoy_growth.iloc[-1] if len(yoy_growth) > 0 else 0
        
        # 連續成長月數
        if 'revenue_growth_mom' in revenue_df.columns:
            mom_growth = revenue_df['revenue_growth_mom'].dropna()
            if not mom_growth.empty:
                consecutive_growth = 0
                for growth in reversed(mom_growth.tolist()):
                    if growth > 0:
                        consecutive_growth += 1
                    else:
                        break
                features['revenue_consecutive_growth_months'] = consecutive_growth
        
        # 營收趨勢（線性回歸斜率）
        if len(revenue_df) >= 6:
            recent_revenues = revenue_df['revenue'].tail(6).values
            x = np.arange(len(recent_revenues))
            slope = np.polyfit(x, recent_revenues, 1)[0]
            features['revenue_trend_slope'] = slope
        
        # 營收穩定性（變異係數）
        if len(revenue_df) >= 12:
            recent_revenues = revenue_df['revenue'].tail(12)
            cv = recent_revenues.std() / recent_revenues.mean() if recent_revenues.mean() > 0 else 0
            features['revenue_stability_cv'] = cv
        
        return features
    
    def _generate_financial_features(self, financial_df: pd.DataFrame, 
                                   balance_df: pd.DataFrame) -> Dict[str, float]:
        """生成財務比率特徵"""
        features = {}
        
        if financial_df.empty or balance_df.empty:
            return features
        
        # 將財務資料轉換為透視表格式
        financial_pivot = financial_df.pivot_table(
            index='date', columns='type', values='value', aggfunc='first'
        )
        balance_pivot = balance_df.pivot_table(
            index='date', columns='type', values='value', aggfunc='first'
        )
        
        # 獲取最新的財務資料
        if not financial_pivot.empty:
            latest_financial = financial_pivot.iloc[-1]
            
            # ROE (股東權益報酬率)
            if 'NetIncome' in latest_financial and not balance_pivot.empty:
                latest_balance = balance_pivot.iloc[-1]
                if 'TotalEquity' in latest_balance:
                    net_income = latest_financial.get('NetIncome', 0)
                    total_equity = latest_balance.get('TotalEquity', 0)
                    features['roe'] = net_income / total_equity if total_equity > 0 else 0
            
            # 毛利率
            if 'Revenue' in latest_financial and 'GrossProfit' in latest_financial:
                revenue = latest_financial.get('Revenue', 0)
                gross_profit = latest_financial.get('GrossProfit', 0)
                features['gross_margin'] = gross_profit / revenue if revenue > 0 else 0
            
            # 營業利益率
            if 'Revenue' in latest_financial and 'OperatingIncome' in latest_financial:
                revenue = latest_financial.get('Revenue', 0)
                operating_income = latest_financial.get('OperatingIncome', 0)
                features['operating_margin'] = operating_income / revenue if revenue > 0 else 0
        
        # 資產負債比
        if not balance_pivot.empty:
            latest_balance = balance_pivot.iloc[-1]
            if 'TotalLiabilities' in latest_balance and 'TotalAssets' in latest_balance:
                total_liabilities = latest_balance.get('TotalLiabilities', 0)
                total_assets = latest_balance.get('TotalAssets', 0)
                features['debt_ratio'] = total_liabilities / total_assets if total_assets > 0 else 0
            
            # 流動比率
            if 'CurrentAssets' in latest_balance and 'CurrentLiabilities' in latest_balance:
                current_assets = latest_balance.get('CurrentAssets', 0)
                current_liabilities = latest_balance.get('CurrentLiabilities', 0)
                features['current_ratio'] = current_assets / current_liabilities if current_liabilities > 0 else 0
        
        return features

    def _generate_cashflow_features(self, cashflow_df: pd.DataFrame) -> Dict[str, float]:
        """生成現金流特徵"""
        features = {}

        if cashflow_df.empty:
            return features

        # 將現金流資料轉換為透視表格式
        cashflow_pivot = cashflow_df.pivot_table(
            index='date', columns='type', values='value', aggfunc='first'
        )

        if not cashflow_pivot.empty:
            latest_cashflow = cashflow_pivot.iloc[-1]

            # 營運現金流
            if 'CashFlowsFromOperatingActivities' in latest_cashflow:
                operating_cf = latest_cashflow.get('CashFlowsFromOperatingActivities', 0)
                features['operating_cash_flow'] = operating_cf

            # 投資現金流
            if 'CashFlowsFromInvestingActivities' in latest_cashflow:
                investing_cf = latest_cashflow.get('CashFlowsFromInvestingActivities', 0)
                features['investing_cash_flow'] = investing_cf

            # 融資現金流
            if 'CashFlowsFromFinancingActivities' in latest_cashflow:
                financing_cf = latest_cashflow.get('CashFlowsFromFinancingActivities', 0)
                features['financing_cash_flow'] = financing_cf

            # 自由現金流 (營運現金流 - 資本支出)
            if ('CashFlowsFromOperatingActivities' in latest_cashflow and
                'CashFlowsFromInvestingActivities' in latest_cashflow):
                operating_cf = latest_cashflow.get('CashFlowsFromOperatingActivities', 0)
                investing_cf = latest_cashflow.get('CashFlowsFromInvestingActivities', 0)
                features['free_cash_flow'] = operating_cf + investing_cf  # 投資現金流通常為負

        # 現金流穩定性
        if len(cashflow_pivot) >= 4:
            if 'CashFlowsFromOperatingActivities' in cashflow_pivot.columns:
                operating_cfs = cashflow_pivot['CashFlowsFromOperatingActivities'].dropna()
                if len(operating_cfs) >= 4:
                    features['operating_cf_stability'] = operating_cfs.std() / abs(operating_cfs.mean()) if operating_cfs.mean() != 0 else 0

        return features

    def _generate_technical_features(self, price_df: pd.DataFrame) -> Dict[str, float]:
        """生成技術指標特徵"""
        features = {}

        if price_df.empty or len(price_df) < 20:
            return features

        # 確保資料按日期排序
        price_df = price_df.sort_values('date').reset_index(drop=True)

        # 價格序列
        close_prices = price_df['close_price']
        volumes = price_df['volume']

        # 1. 價格移動平均
        for window in self.config['technical_features']['price_windows']:
            if len(close_prices) >= window:
                ma = calculate_moving_average(close_prices, window)
                features[f'price_ma_{window}'] = ma.iloc[-1] if not ma.empty else 0

                # 價格相對於移動平均的位置
                current_price = close_prices.iloc[-1]
                features[f'price_vs_ma_{window}'] = (current_price - ma.iloc[-1]) / ma.iloc[-1] if ma.iloc[-1] > 0 else 0

        # 2. 成交量移動平均
        for window in self.config['technical_features']['volume_windows']:
            if len(volumes) >= window:
                vol_ma = calculate_moving_average(volumes, window)
                features[f'volume_ma_{window}'] = vol_ma.iloc[-1] if not vol_ma.empty else 0

                # 成交量相對於平均的比率
                current_volume = volumes.iloc[-1]
                features[f'volume_vs_ma_{window}'] = current_volume / vol_ma.iloc[-1] if vol_ma.iloc[-1] > 0 else 0

        # 3. 價格波動率
        returns = calculate_returns(close_prices)
        volatility_window = self.config['technical_features']['volatility_window']
        if len(returns) >= volatility_window:
            volatility = calculate_volatility(returns, volatility_window)
            features['price_volatility'] = volatility.iloc[-1] if not volatility.empty else 0

        # 4. RSI指標
        rsi_window = self.config['technical_features']['rsi_window']
        if len(close_prices) >= rsi_window:
            rsi = calculate_rsi(close_prices, rsi_window)
            features['rsi'] = rsi.iloc[-1] if not rsi.empty else 50

        # 5. 動量指標
        for window in self.config['technical_features']['momentum_windows']:
            if len(close_prices) >= window:
                momentum = calculate_momentum(close_prices, window)
                features[f'momentum_{window}'] = momentum.iloc[-1] if not momentum.empty else 0

        # 6. 價格範圍特徵
        if len(price_df) >= 20:
            recent_high = price_df['high_price'].tail(20).max()
            recent_low = price_df['low_price'].tail(20).min()
            current_price = close_prices.iloc[-1]

            # 當前價格在近期範圍中的位置
            features['price_position_in_range'] = (current_price - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5

        # 7. 成交量價格關係
        if len(price_df) >= 5:
            recent_returns = returns.tail(5)
            recent_volumes = volumes.tail(5)

            # 計算價量相關性
            if len(recent_returns) == len(recent_volumes) and len(recent_returns) > 1:
                correlation = recent_returns.corr(recent_volumes)
                features['price_volume_correlation'] = correlation if not pd.isna(correlation) else 0

        return features

    def _generate_basic_features(self, stock_id: str, end_date: str) -> Dict[str, float]:
        """生成基本特徵"""
        features = {}

        # 股票代碼特徵
        features['stock_id_numeric'] = int(stock_id) if stock_id.isdigit() else 0

        # 市場特徵（從股票代碼推斷）
        if stock_id.startswith('00'):
            features['is_etf'] = 1
            features['market_type'] = 0  # ETF
        elif int(stock_id) < 2000:
            features['market_type'] = 1  # 上市
        else:
            features['market_type'] = 2  # 上櫃

        # 時間特徵
        end_dt = pd.to_datetime(end_date)
        features['month'] = end_dt.month
        features['quarter'] = end_dt.quarter
        features['is_year_end'] = 1 if end_dt.month == 12 else 0
        features['is_quarter_end'] = 1 if end_dt.month in [3, 6, 9, 12] else 0

        return features

    def generate_batch_features(self, stock_ids: List[str], end_date: str) -> pd.DataFrame:
        """
        批次生成多個股票的特徵

        Args:
            stock_ids: 股票代碼列表
            end_date: 特徵計算的截止日期

        Returns:
            所有股票的特徵DataFrame
        """
        logger.info(f"批次生成 {len(stock_ids)} 個股票的特徵")

        all_features = []

        for i, stock_id in enumerate(stock_ids):
            try:
                # 排除00開頭的股票
                if stock_id.startswith('00'):
                    logger.debug(f"跳過ETF股票: {stock_id}")
                    continue

                features_df = self.generate_features(stock_id, end_date)
                if not features_df.empty:
                    all_features.append(features_df)

                # 進度顯示
                if (i + 1) % 100 == 0:
                    logger.info(f"已處理 {i + 1}/{len(stock_ids)} 個股票")

            except Exception as e:
                logger.error(f"生成股票 {stock_id} 特徵失敗: {e}")
                continue

        if all_features:
            result_df = pd.concat(all_features, ignore_index=True)
            logger.info(f"成功生成 {len(result_df)} 個股票的特徵")
            return result_df
        else:
            logger.warning("沒有成功生成任何特徵")
            return pd.DataFrame()
