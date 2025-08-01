#!/usr/bin/env python3
"""
資料庫管理工具
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import logging

try:
    from ...config.config import DATABASE_CONFIG
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    sys.path.insert(0, project_root)
    from config.config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化資料庫管理器
        
        Args:
            db_path: 資料庫路徑，None則使用配置檔案中的路徑
        """
        self.db_path = Path(db_path) if db_path else DATABASE_CONFIG['path']
        self.timeout = DATABASE_CONFIG['timeout']
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"資料庫檔案不存在: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """獲取資料庫連接（上下文管理器）"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=self.timeout)
            conn.row_factory = sqlite3.Row  # 使結果可以用欄位名稱存取
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"資料庫操作錯誤: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        """
        執行查詢並返回結果
        
        Args:
            query: SQL查詢語句
            params: 查詢參數
            
        Returns:
            查詢結果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
    
    def execute_query_df(self, query: str, params: Tuple = ()) -> pd.DataFrame:
        """
        執行查詢並返回DataFrame

        Args:
            query: SQL查詢語句
            params: 查詢參數

        Returns:
            查詢結果DataFrame
        """
        with self.get_connection() as conn:
            try:
                # 嘗試使用 params 參數
                if params:
                    return pd.read_sql_query(query, conn, params=list(params))
                else:
                    return pd.read_sql_query(query, conn)
            except Exception as e:
                logger.error(f"查詢執行失敗: {e}")
                logger.error(f"查詢語句: {query}")
                logger.error(f"參數: {params}")
                # 如果 params 方式失敗，嘗試使用 cursor 方式
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return pd.DataFrame(rows, columns=columns)
    
    def get_stock_list(self, exclude_patterns: List[str] = None) -> pd.DataFrame:
        """
        獲取股票清單
        
        Args:
            exclude_patterns: 要排除的股票代碼模式
            
        Returns:
            股票清單DataFrame
        """
        query = """
        SELECT stock_id, stock_name, market, industry, is_etf, is_active
        FROM stocks
        WHERE is_active = 1
        AND stock_id GLOB '[0-9][0-9][0-9][0-9]'  -- 只要4位數字的股票代碼
        AND LENGTH(stock_id) = 4  -- 確保長度為4
        """

        if exclude_patterns:
            for pattern in exclude_patterns:
                query += f" AND stock_id NOT LIKE '{pattern}%'"

        query += " ORDER BY stock_id"
        
        return self.execute_query_df(query)
    
    def get_stock_prices(self, stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取股價資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            股價資料DataFrame
        """
        query = """
        SELECT date, open_price, high_price, low_price, close_price, volume
        FROM stock_prices 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        ORDER BY date
        """
        
        return self.execute_query_df(query, (stock_id, start_date, end_date))
    
    def get_monthly_revenue(self, stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取月營收資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            月營收資料DataFrame
        """
        query = """
        SELECT revenue_year, revenue_month, revenue, 
               revenue_growth_mom, revenue_growth_yoy, date
        FROM monthly_revenues 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        ORDER BY revenue_year, revenue_month
        """
        
        return self.execute_query_df(query, (stock_id, start_date, end_date))
    
    def get_financial_statements(self, stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取財務報表資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            財務報表資料DataFrame
        """
        query = """
        SELECT date, type, value, origin_name
        FROM financial_statements 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        ORDER BY date, type
        """
        
        return self.execute_query_df(query, (stock_id, start_date, end_date))
    
    def get_balance_sheets(self, stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取資產負債表資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            資產負債表資料DataFrame
        """
        query = """
        SELECT date, type, value, origin_name
        FROM balance_sheets 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        ORDER BY date, type
        """
        
        return self.execute_query_df(query, (stock_id, start_date, end_date))
    
    def get_cash_flow_statements(self, stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取現金流量表資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            現金流量表資料DataFrame
        """
        query = """
        SELECT date, type, value, origin_name
        FROM cash_flow_statements 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        ORDER BY date, type
        """
        
        return self.execute_query_df(query, (stock_id, start_date, end_date))
    
    def save_predictions(self, predictions_df: pd.DataFrame, table_name: str = 'stock_predictions'):
        """
        儲存預測結果
        
        Args:
            predictions_df: 預測結果DataFrame
            table_name: 資料表名稱
        """
        with self.get_connection() as conn:
            predictions_df.to_sql(table_name, conn, if_exists='append', index=False)
            conn.commit()
            logger.info(f"已儲存 {len(predictions_df)} 筆預測結果到 {table_name}")
    
    def get_table_info(self, table_name: str) -> Dict:
        """
        獲取資料表資訊
        
        Args:
            table_name: 資料表名稱
            
        Returns:
            資料表資訊字典
        """
        # 獲取資料表結構
        schema_query = f"PRAGMA table_info({table_name})"
        schema_df = self.execute_query_df(schema_query)
        
        # 獲取資料筆數
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count_result = self.execute_query(count_query)
        
        return {
            'table_name': table_name,
            'columns': schema_df.to_dict('records'),
            'row_count': count_result[0]['count'] if count_result else 0
        }
