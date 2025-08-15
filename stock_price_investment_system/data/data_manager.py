# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 資料管理器
Stock Price Investment System - Data Manager
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

from ..config.settings import get_config

logger = logging.getLogger(__name__)

class DataManager:
    """資料管理器 - 統一管理所有資料存取"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """初始化資料管理器"""
        self.config = get_config()
        self.db_path = db_path or self.config['database']['path']
        self.timeout = self.config['database']['timeout']
        
        # 檢查資料庫是否存在
        if not self.db_path.exists():
            raise FileNotFoundError(f"資料庫檔案不存在: {self.db_path}")
        
        logger.info(f"DataManager initialized with database: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=self.config['database']['check_same_thread']
        )
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_available_stocks(self, 
                           start_date: str = None, 
                           end_date: str = None,
                           min_history_months: int = 60) -> List[str]:
        """
        獲取可用股票清單
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            min_history_months: 最小歷史資料月數
            
        Returns:
            股票代碼清單
        """
        query = """
        SELECT DISTINCT mr.stock_id
        FROM monthly_revenues mr
        WHERE mr.stock_id IS NOT NULL
        """
        
        params = []
        
        if start_date:
            query += " AND mr.revenue_year || '-' || printf('%02d', mr.revenue_month) >= ?"
            params.append(start_date[:7])  # YYYY-MM
        
        if end_date:
            query += " AND mr.revenue_year || '-' || printf('%02d', mr.revenue_month) <= ?"
            params.append(end_date[:7])  # YYYY-MM
        
        # 檢查歷史資料長度
        if min_history_months > 0:
            query += """
            GROUP BY mr.stock_id
            HAVING COUNT(*) >= ?
            """
            params.append(min_history_months)
        
        query += " ORDER BY mr.stock_id"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            stocks = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(stocks)} available stocks")
        return stocks
    
    def get_stock_basic_info(self, stock_id: str) -> Dict[str, Any]:
        """
        獲取股票基本資訊
        
        Args:
            stock_id: 股票代碼
            
        Returns:
            股票基本資訊字典
        """
        # 從多個表格獲取基本資訊
        queries = {
            'monthly_revenue': """
                SELECT stock_id, MIN(revenue_year) as first_year, MAX(revenue_year) as last_year,
                       COUNT(*) as revenue_records
                FROM monthly_revenues 
                WHERE stock_id = ?
                GROUP BY stock_id
            """,
            'financial_statements': """
                SELECT stock_id, MIN(date) as first_date, MAX(date) as last_date,
                       COUNT(*) as statement_records
                FROM financial_statements 
                WHERE stock_id = ?
                GROUP BY stock_id
            """,
            'stock_prices': """
                SELECT stock_id, MIN(date) as first_price_date, MAX(date) as last_price_date,
                       COUNT(*) as price_records
                FROM stock_prices 
                WHERE stock_id = ?
                GROUP BY stock_id
            """
        }
        
        info = {'stock_id': stock_id}
        
        with self.get_connection() as conn:
            for table, query in queries.items():
                try:
                    cursor = conn.execute(query, [stock_id])
                    result = cursor.fetchone()
                    if result:
                        info.update(dict(result))
                except sqlite3.Error as e:
                    logger.warning(f"Error querying {table} for {stock_id}: {e}")
        
        return info
    
    def get_monthly_revenue(self, 
                          stock_id: str, 
                          start_date: str = None,
                          end_date: str = None,
                          months: int = None) -> pd.DataFrame:
        """
        獲取月營收資料
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            months: 回看月數（如果指定，則忽略start_date）
            
        Returns:
            月營收DataFrame
        """
        query = """
        SELECT revenue_year, revenue_month, revenue,
               revenue_year || '-' || printf('%02d', revenue_month) as year_month
        FROM monthly_revenues
        WHERE stock_id = ?
        """
        
        params = [stock_id]
        
        if months:
            # 計算開始日期
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=months * 30)
            start_date = start_dt.strftime('%Y-%m')
        
        if start_date:
            query += " AND revenue_year || '-' || printf('%02d', revenue_month) >= ?"
            params.append(start_date[:7])
        
        if end_date:
            query += " AND revenue_year || '-' || printf('%02d', revenue_month) <= ?"
            params.append(end_date[:7])
        
        query += " ORDER BY revenue_year, revenue_month"
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # 建立日期欄位
            df['date'] = pd.to_datetime(df['year_month'] + '-01')
            df = df.sort_values('date').reset_index(drop=True)
            
            # 計算成長率（填充 NaN 為 0）
            df['revenue_yoy'] = df['revenue'].pct_change(12).fillna(0)  # 年增率
            df['revenue_mom'] = df['revenue'].pct_change(1).fillna(0)   # 月增率
            
            logger.info(f"Retrieved {len(df)} monthly revenue records for {stock_id}")
        else:
            logger.warning(f"No monthly revenue data found for {stock_id}")
        
        return df
    
    def _get_table_columns(self, table_name: str) -> set:
        """查詢資料表欄位名稱集合"""
        try:
            with self.get_connection() as conn:
                cur = conn.execute(f"PRAGMA table_info({table_name})")
                cols = {row[1] for row in cur.fetchall()}
                logger.debug(f"資料表 {table_name} 欄位偵測: {sorted(list(cols))}")
                return cols
        except Exception as e:
            logger.warning(f"無法讀取資料表結構 {table_name}: {e}")
            return set()

    def get_stock_prices(self,
                        stock_id: str,
                        start_date: str = None,
                        end_date: str = None,
                        days: int = None) -> pd.DataFrame:
        """
        獲取股價資料（自動相容 open/open_price 等欄位差異）

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            days: 回看天數（如果指定，則忽略start_date）

        Returns:
            股價DataFrame（欄位統一為: date, open, high, low, close, volume）
        """
        # 偵測欄位
        cols = self._get_table_columns('stock_prices')
        if not cols:
            logger.error("無法取得 stock_prices 欄位資訊，查詢中止")
            return pd.DataFrame()

        sel_open = 'open' if 'open' in cols else ('open_price' if 'open_price' in cols else 'NULL')
        sel_high = 'high' if 'high' in cols else ('high_price' if 'high_price' in cols else 'NULL')
        sel_low  = 'low'  if 'low'  in cols else ('low_price'  if 'low_price'  in cols else 'NULL')
        sel_close= 'close'if 'close'in cols else ('close_price' if 'close_price' in cols else 'NULL')
        sel_vol  = 'volume' if 'volume' in cols else ('turnover' if 'turnover' in cols else 'NULL')

        query = f"""
        SELECT date,
               {sel_open}  AS open,
               {sel_high}  AS high,
               {sel_low}   AS low,
               {sel_close} AS close,
               {sel_vol}   AS volume
        FROM stock_prices
        WHERE stock_id = ?
        """

        params = [stock_id]

        if days:
            # 計算開始日期
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days)
            start_date = start_dt.strftime('%Y-%m-%d')

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"

        # 詳細記錄查詢資訊
        logger.info(
            f"查詢股價資料: stock_id={stock_id}, 起迄=({start_date or '-'}, {end_date or '-'})")
        logger.debug(
            f"欄位映射: open->{sel_open}, high->{sel_high}, low->{sel_low}, close->{sel_close}, volume->{sel_vol}")
        logger.debug(f"SQL: {query.strip()} | 參數: {params}")

        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"讀取股價資料失敗: {e}")
            return pd.DataFrame()

        if not df.empty:
            # 正規化欄位型別
            try:
                df['date'] = pd.to_datetime(df['date'])
            except Exception:
                pass
            df = df.sort_values('date').reset_index(drop=True)

            # 統計資訊
            date_min = str(df['date'].min()) if 'date' in df.columns and not df['date'].isna().all() else '-'
            date_max = str(df['date'].max()) if 'date' in df.columns and not df['date'].isna().all() else '-'
            logger.info(f"取得 {len(df)} 筆 {stock_id} 價格資料，日期範圍: {date_min} ~ {date_max}")

            # 若關鍵欄位缺失，記錄警告
            required = ['open','high','low','close','volume']
            missing = [c for c in required if c not in df.columns or df[c].isna().all()]
            if missing:
                logger.warning(f"價格資料缺少必要欄位或全為空值: {missing}")
        else:
            logger.warning(f"查無 {stock_id} 價格資料（期間: {start_date or '-'} ~ {end_date or '-'}）")

        return df
    
    def get_financial_statements(self, 
                               stock_id: str,
                               statement_type: str = None,
                               start_date: str = None,
                               end_date: str = None) -> pd.DataFrame:
        """
        獲取財務報表資料
        
        Args:
            stock_id: 股票代碼
            statement_type: 報表類型 (如 'EPS', 'ROE' 等)
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            財務報表DataFrame
        """
        query = """
        SELECT date, type, value
        FROM financial_statements
        WHERE stock_id = ?
        """
        
        params = [stock_id]
        
        if statement_type:
            query += " AND type = ?"
            params.append(statement_type)
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date, type"
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['date', 'type']).reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} financial statement records for {stock_id}")
        else:
            logger.warning(f"No financial statement data found for {stock_id}")
        
        return df
    
    def check_data_availability(self, 
                              stock_id: str,
                              start_date: str,
                              end_date: str) -> Dict[str, bool]:
        """
        檢查指定期間的資料可用性
        
        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            資料可用性字典
        """
        availability = {}
        
        # 檢查月營收資料
        revenue_df = self.get_monthly_revenue(stock_id, start_date, end_date)
        availability['monthly_revenue'] = not revenue_df.empty
        
        # 檢查股價資料
        price_df = self.get_stock_prices(stock_id, start_date, end_date)
        availability['stock_prices'] = not price_df.empty
        
        # 檢查財務報表資料
        financial_df = self.get_financial_statements(stock_id, None, start_date, end_date)
        availability['financial_statements'] = not financial_df.empty
        
        # 整體可用性
        availability['overall'] = all([
            availability['monthly_revenue'],
            availability['stock_prices']
        ])
        
        return availability
