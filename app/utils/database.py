#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫工具模組
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.engine = None
        self.Session = None
        self._ensure_database_dir()
        self._init_engine()
    
    def _ensure_database_dir(self):
        """確保資料庫目錄存在"""
        db_dir = os.path.dirname(self.database_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"建立資料庫目錄: {db_dir}")
    
    def _init_engine(self):
        """初始化資料庫引擎"""
        self.engine = create_engine(f'sqlite:///{self.database_path}')
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"資料庫引擎初始化完成: {self.database_path}")
    
    def create_tables(self):
        """建立所有資料表"""
        
        # 股票基本資料表
        stocks_table = """
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market TEXT NOT NULL,  -- TWSE/TPEX
            industry TEXT,
            listing_date DATE,
            is_etf BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 股價資料表
        stock_prices_table = """
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume INTEGER NOT NULL,
            trading_money REAL,
            trading_turnover INTEGER,
            spread REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        );
        """
        
        # 技術指標表
        technical_indicators_table = """
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            indicator_type TEXT NOT NULL,  -- MA, RSI, MACD, etc.
            indicator_value REAL,
            indicator_params TEXT,  -- JSON格式參數
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date, indicator_type, indicator_params)
        );
        """
        
        # ETF配息表
        etf_dividends_table = """
        CREATE TABLE IF NOT EXISTS etf_dividends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            announce_date DATE NOT NULL,
            ex_dividend_date DATE,
            payment_date DATE,
            cash_dividend REAL,
            stock_dividend REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        );
        """
        
        # 資料更新記錄表
        data_updates_table = """
        CREATE TABLE IF NOT EXISTS data_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT,
            update_type TEXT NOT NULL,  -- price, dividend, indicator
            last_update_date DATE NOT NULL,
            status TEXT DEFAULT 'success',  -- success, failed, partial
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        tables = [
            ("stocks", stocks_table),
            ("stock_prices", stock_prices_table),
            ("technical_indicators", technical_indicators_table),
            ("etf_dividends", etf_dividends_table),
            ("data_updates", data_updates_table)
        ]
        
        with self.engine.connect() as conn:
            for table_name, table_sql in tables:
                try:
                    conn.execute(text(table_sql))
                    logger.info(f"資料表 {table_name} 建立成功")
                except Exception as e:
                    logger.error(f"建立資料表 {table_name} 失敗: {e}")
                    raise
            
            conn.commit()
        
        # 建立索引
        self._create_indexes()
        logger.info("所有資料表建立完成")
    
    def _create_indexes(self):
        """建立資料庫索引以提升查詢效能"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_date ON stock_prices(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_stock_date ON technical_indicators(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_etf_dividends_stock_date ON etf_dividends(stock_id, announce_date);",
            "CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);",
            "CREATE INDEX IF NOT EXISTS idx_stocks_is_etf ON stocks(is_etf);",
        ]
        
        with self.engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"建立索引失敗: {e}")
            conn.commit()
        
        logger.info("資料庫索引建立完成")
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """執行查詢並返回 DataFrame"""
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(query, conn, params=params)
                return result
        except Exception as e:
            logger.error(f"查詢執行失敗: {e}")
            raise
    
    def execute_sql(self, sql: str, params: Optional[Dict] = None) -> None:
        """執行 SQL 語句"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql), params or {})
                conn.commit()
        except Exception as e:
            logger.error(f"SQL 執行失敗: {e}")
            raise
    
    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """批量插入資料"""
        if not data:
            return
        
        try:
            df = pd.DataFrame(data)
            df.to_sql(table_name, self.engine, if_exists='append', index=False)
            logger.info(f"批量插入 {len(data)} 筆資料到 {table_name}")
        except Exception as e:
            logger.error(f"批量插入失敗: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """取得資料表資訊"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """取得資料表記錄數"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result.iloc[0]['count']
    
    def vacuum_database(self):
        """清理資料庫，回收空間"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.commit()
            logger.info("資料庫清理完成")
        except Exception as e:
            logger.error(f"資料庫清理失敗: {e}")
    
    def backup_database(self, backup_path: str):
        """備份資料庫"""
        try:
            import shutil
            shutil.copy2(self.database_path, backup_path)
            logger.info(f"資料庫備份完成: {backup_path}")
        except Exception as e:
            logger.error(f"資料庫備份失敗: {e}")
            raise
    
    def get_database_size(self) -> str:
        """取得資料庫大小"""
        try:
            size_bytes = os.path.getsize(self.database_path)
            
            # 轉換為人類可讀格式
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.2f} TB"
        except Exception as e:
            logger.error(f"取得資料庫大小失敗: {e}")
            return "Unknown"
    
    def close(self):
        """關閉資料庫連接"""
        if self.engine:
            self.engine.dispose()
            logger.info("資料庫連接已關閉")
