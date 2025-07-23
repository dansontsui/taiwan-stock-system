#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查詢服務模組
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from app.utils.simple_database import SimpleDatabaseManager

class StockQueryService:
    """股票查詢服務"""
    
    def __init__(self, db_manager: SimpleDatabaseManager):
        self.db = db_manager
    
    def get_stock_list(self, market: Optional[str] = None, 
                      is_etf: Optional[bool] = None) -> List[Dict]:
        """取得股票清單"""
        query = "SELECT * FROM stocks WHERE is_active = 1"
        params = []
        
        if market:
            query += " AND market = ?"
            params.append(market)
        
        if is_etf is not None:
            query += " AND is_etf = ?"
            params.append(is_etf)
        
        query += " ORDER BY stock_id"
        
        return self.db.execute_query(query, tuple(params) if params else None)
    
    def get_stock_info(self, stock_id: str) -> Optional[Dict]:
        """取得股票基本資訊"""
        query = "SELECT * FROM stocks WHERE stock_id = ?"
        result = self.db.execute_query(query, (stock_id,))
        return result[0] if result else None
    
    def get_stock_prices(self, stock_id: str, start_date: Optional[str] = None,
                        end_date: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """取得股價資料"""
        query = """
        SELECT * FROM stock_prices 
        WHERE stock_id = ?
        """
        params = [stock_id]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        return self.db.execute_query(query, tuple(params))
    
    def get_latest_price(self, stock_id: str) -> Optional[Dict]:
        """取得最新股價"""
        query = """
        SELECT * FROM stock_prices 
        WHERE stock_id = ? 
        ORDER BY date DESC 
        LIMIT 1
        """
        result = self.db.execute_query(query, (stock_id,))
        return result[0] if result else None
    
    def get_price_range(self, stock_id: str, days: int = 30) -> Dict:
        """取得指定天數內的價格統計"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            MIN(low_price) as min_price,
            MAX(high_price) as max_price,
            AVG(close_price) as avg_price,
            SUM(volume) as total_volume,
            COUNT(*) as trading_days
        FROM stock_prices 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        """
        
        result = self.db.execute_query(query, (stock_id, start_date, end_date))
        return result[0] if result else {}
    
    def get_multiple_latest_prices(self, stock_ids: List[str]) -> List[Dict]:
        """取得多檔股票的最新價格"""
        if not stock_ids:
            return []
        
        placeholders = ','.join(['?' for _ in stock_ids])
        query = f"""
        SELECT sp.*, s.stock_name, s.market, s.is_etf
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.stock_id
        WHERE sp.stock_id IN ({placeholders})
        AND sp.date = (
            SELECT MAX(date) 
            FROM stock_prices sp2 
            WHERE sp2.stock_id = sp.stock_id
        )
        ORDER BY sp.stock_id
        """
        
        return self.db.execute_query(query, tuple(stock_ids))
    
    def search_stocks(self, keyword: str) -> List[Dict]:
        """搜尋股票"""
        query = """
        SELECT * FROM stocks 
        WHERE (stock_id LIKE ? OR stock_name LIKE ?) 
        AND is_active = 1
        ORDER BY stock_id
        LIMIT 20
        """
        search_term = f"%{keyword}%"
        return self.db.execute_query(query, (search_term, search_term))
    
    def get_market_summary(self) -> Dict:
        """取得市場摘要"""
        # 取得最新交易日
        latest_date_query = "SELECT MAX(date) as latest_date FROM stock_prices"
        latest_date_result = self.db.execute_query(latest_date_query)
        latest_date = latest_date_result[0]['latest_date'] if latest_date_result else None
        
        if not latest_date:
            return {}
        
        # 統計資訊
        summary_query = """
        SELECT 
            COUNT(DISTINCT sp.stock_id) as total_stocks,
            SUM(sp.volume) as total_volume,
            SUM(sp.trading_money) as total_trading_money,
            COUNT(CASE WHEN sp.spread > 0 THEN 1 END) as up_stocks,
            COUNT(CASE WHEN sp.spread < 0 THEN 1 END) as down_stocks,
            COUNT(CASE WHEN sp.spread = 0 THEN 1 END) as flat_stocks
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.stock_id
        WHERE sp.date = ? AND s.is_active = 1
        """
        
        summary = self.db.execute_query(summary_query, (latest_date,))
        
        return {
            'latest_date': latest_date,
            'summary': summary[0] if summary else {}
        }
    
    def get_top_performers(self, limit: int = 10, 
                          performance_type: str = 'gain') -> List[Dict]:
        """取得表現最佳/最差的股票"""
        # 取得最新交易日
        latest_date_query = "SELECT MAX(date) as latest_date FROM stock_prices"
        latest_date_result = self.db.execute_query(latest_date_query)
        latest_date = latest_date_result[0]['latest_date'] if latest_date_result else None
        
        if not latest_date:
            return []
        
        order_by = "DESC" if performance_type == 'gain' else "ASC"
        
        query = f"""
        SELECT sp.*, s.stock_name, s.market, s.is_etf,
               ROUND((sp.spread / (sp.close_price - sp.spread)) * 100, 2) as change_percent
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.stock_id
        WHERE sp.date = ? AND s.is_active = 1
        ORDER BY sp.spread {order_by}
        LIMIT ?
        """
        
        return self.db.execute_query(query, (latest_date, limit))
    
    def get_volume_leaders(self, limit: int = 10) -> List[Dict]:
        """取得成交量排行"""
        # 取得最新交易日
        latest_date_query = "SELECT MAX(date) as latest_date FROM stock_prices"
        latest_date_result = self.db.execute_query(latest_date_query)
        latest_date = latest_date_result[0]['latest_date'] if latest_date_result else None
        
        if not latest_date:
            return []
        
        query = """
        SELECT sp.*, s.stock_name, s.market, s.is_etf
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.stock_id
        WHERE sp.date = ? AND s.is_active = 1
        ORDER BY sp.volume DESC
        LIMIT ?
        """
        
        return self.db.execute_query(query, (latest_date, limit))
    
    def get_etf_dividends(self, stock_id: str) -> List[Dict]:
        """取得 ETF 配息記錄"""
        query = """
        SELECT * FROM etf_dividends 
        WHERE stock_id = ? 
        ORDER BY announce_date DESC
        """
        return self.db.execute_query(query, (stock_id,))
    
    def get_data_update_status(self) -> List[Dict]:
        """取得資料更新狀態"""
        query = """
        SELECT 
            stock_id,
            update_type,
            last_update_date,
            status,
            error_message,
            created_at
        FROM data_updates 
        ORDER BY created_at DESC
        LIMIT 100
        """
        return self.db.execute_query(query)
    
    def get_database_stats(self) -> Dict:
        """取得資料庫統計資訊"""
        stats = {}
        
        # 各表記錄數
        tables = ['stocks', 'stock_prices', 'technical_indicators', 'etf_dividends', 'data_updates']
        for table in tables:
            try:
                count = self.db.get_table_count(table)
                stats[f'{table}_count'] = count
            except:
                stats[f'{table}_count'] = 0
        
        # 資料庫大小
        stats['database_size'] = self.db.get_database_size()
        
        # 資料日期範圍
        try:
            date_range_query = """
            SELECT 
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM stock_prices
            """
            date_range = self.db.execute_query(date_range_query)
            if date_range:
                stats.update(date_range[0])
        except:
            pass
        
        return stats
