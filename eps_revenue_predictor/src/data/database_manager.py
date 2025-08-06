# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Database Manager
資料庫管理器
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager

from config.settings import DATABASE_CONFIG
from src.utils.logger import get_logger, log_execution

logger = get_logger('database_manager')

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DATABASE_CONFIG['path']
        self.timeout = DATABASE_CONFIG['timeout']
        self._validate_database()
    
    def _validate_database(self):
        """驗證資料庫是否存在且可訪問"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['monthly_revenues', 'financial_statements', 'financial_ratios']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    logger.warning(f"Missing required tables: {missing_tables}")
                else:
                    logger.info(f"Database validation successful. Found {len(tables)} tables.")
                    
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """獲取資料庫連接 (上下文管理器)"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=DATABASE_CONFIG['check_same_thread']
            )
            conn.row_factory = sqlite3.Row  # 使結果可以按列名訪問
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @log_execution
    def get_monthly_revenue(self, stock_id: str, months: int = 12) -> pd.DataFrame:
        """
        獲取月營收資料
        
        Args:
            stock_id: 股票代碼
            months: 回看月數
            
        Returns:
            月營收DataFrame
        """
        query = """
        SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy, revenue_growth_mom
        FROM monthly_revenues
        WHERE stock_id = ?
        ORDER BY revenue_year DESC, revenue_month DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[stock_id, months])
        
        if not df.empty:
            # 創建日期欄位 - 重新命名欄位以符合pandas要求
            df_date = df[['revenue_year', 'revenue_month']].copy()
            df_date.columns = ['year', 'month']
            df_date['day'] = 1
            df['date'] = pd.to_datetime(df_date)
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.log_data_collection(stock_id, 'monthly_revenue', len(df),
                                     f"{df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        else:
            logger.warning(f"No monthly revenue data found for stock {stock_id}")
        
        return df
    
    @log_execution
    def get_financial_ratios(self, stock_id: str, quarters: int = 8) -> pd.DataFrame:
        """
        獲取財務比率資料
        
        Args:
            stock_id: 股票代碼
            quarters: 回看季數
            
        Returns:
            財務比率DataFrame
        """
        query = """
        SELECT date, gross_margin, operating_margin, net_margin, roe, roa
        FROM financial_ratios
        WHERE stock_id = ?
        ORDER BY date DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[stock_id, quarters])
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.log_data_collection(stock_id, 'financial_ratios', len(df),
                                     f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        else:
            logger.warning(f"No financial ratios data found for stock {stock_id}")
        
        return df
    
    @log_execution
    def get_eps_data(self, stock_id: str, quarters: int = 8) -> pd.DataFrame:
        """
        獲取EPS資料
        
        Args:
            stock_id: 股票代碼
            quarters: 回看季數
            
        Returns:
            EPS DataFrame
        """
        query = """
        SELECT date, value as eps
        FROM financial_statements
        WHERE stock_id = ? AND type = 'EPS'
        ORDER BY date DESC
        LIMIT ?
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[stock_id, quarters])
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.log_data_collection(stock_id, 'eps_data', len(df),
                                     f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        else:
            logger.warning(f"No EPS data found for stock {stock_id}")
        
        return df
    
    @log_execution
    def get_stock_basic_info(self, stock_id: str) -> Dict:
        """
        獲取股票基本資訊
        
        Args:
            stock_id: 股票代碼
            
        Returns:
            股票基本資訊字典
        """
        query = """
        SELECT stock_id, stock_name, market, industry
        FROM stocks
        WHERE stock_id = ?
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [stock_id])
            result = cursor.fetchone()
        
        if result:
            return {
                'stock_id': result['stock_id'],
                'stock_name': result['stock_name'],
                'market': result['market'],
                'industry': result['industry'] if 'industry' in result.keys() else 'Unknown'
            }
        else:
            logger.warning(f"No basic info found for stock {stock_id}")
            return {}
    
    @log_execution
    def get_comprehensive_data(self, stock_id: str) -> Dict[str, pd.DataFrame]:
        """
        獲取股票的綜合資料
        
        Args:
            stock_id: 股票代碼
            
        Returns:
            包含各類資料的字典
        """
        logger.info(f"Collecting comprehensive data for stock {stock_id}")
        
        data = {
            'basic_info': self.get_stock_basic_info(stock_id),
            'monthly_revenue': self.get_monthly_revenue(stock_id, 24),  # 2年月營收
            'financial_ratios': self.get_financial_ratios(stock_id, 12),  # 3年季度比率
            'eps_data': self.get_eps_data(stock_id, 12)  # 3年EPS
        }
        
        # 檢查資料完整性
        data_quality = self._assess_data_quality(data)
        data['data_quality'] = data_quality
        
        logger.info(f"Comprehensive data collection completed for {stock_id}",
                   quality_score=data_quality['overall_score'])
        
        return data
    
    def _assess_data_quality(self, data: Dict) -> Dict:
        """評估資料品質"""
        quality = {
            'monthly_revenue_completeness': len(data['monthly_revenue']) / 24,  # 期望24個月
            'financial_ratios_completeness': len(data['financial_ratios']) / 12,  # 期望12季
            'eps_data_completeness': len(data['eps_data']) / 12,  # 期望12季
        }
        
        # 計算整體品質分數
        quality['overall_score'] = sum(min(score, 1.0) for score in quality.values()) / len(quality)
        
        # 品質等級
        if quality['overall_score'] >= 0.8:
            quality['grade'] = 'High'
        elif quality['overall_score'] >= 0.6:
            quality['grade'] = 'Medium'
        else:
            quality['grade'] = 'Low'
        
        return quality
    
    @log_execution
    def check_stock_exists(self, stock_id: str) -> bool:
        """檢查股票是否存在"""
        query = "SELECT 1 FROM stocks WHERE stock_id = ? LIMIT 1"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [stock_id])
            result = cursor.fetchone()
        
        exists = result is not None
        logger.debug(f"Stock {stock_id} exists: {exists}")
        return exists
    
    def get_available_stocks(self, limit: int = None) -> List[str]:
        """獲取可用的股票列表 (只包含有營收資料的股票)"""
        query = """
        SELECT DISTINCT s.stock_id
        FROM stocks s
        INNER JOIN monthly_revenues mr ON s.stock_id = mr.stock_id
        WHERE s.is_active = 1
        AND s.stock_id NOT LIKE '00%'  -- 排除ETF
        ORDER BY s.stock_id
        """

        if limit:
            query += f" LIMIT {limit}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            stocks = [row[0] for row in cursor.fetchall()]

        logger.info(f"Found {len(stocks)} available stocks with revenue data")
        return stocks

if __name__ == "__main__":
    # 測試資料庫管理器
    db_manager = DatabaseManager()
    
    # 測試2385群光電子
    test_stock = "2385"
    
    print(f"Testing DatabaseManager with stock {test_stock}")
    
    # 檢查股票是否存在
    if db_manager.check_stock_exists(test_stock):
        print(f"✅ Stock {test_stock} exists")
        
        # 獲取綜合資料
        data = db_manager.get_comprehensive_data(test_stock)
        
        print(f"📊 Data Quality: {data['data_quality']['grade']} ({data['data_quality']['overall_score']:.2%})")
        print(f"📈 Monthly Revenue Records: {len(data['monthly_revenue'])}")
        print(f"📊 Financial Ratios Records: {len(data['financial_ratios'])}")
        print(f"💰 EPS Records: {len(data['eps_data'])}")
        
    else:
        print(f"❌ Stock {test_stock} not found")
