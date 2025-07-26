#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版資料庫工具模組 (使用原生 sqlite3)
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

class SimpleDatabaseManager:
    """簡化版資料庫管理器"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._ensure_database_dir()
        print(f"資料庫路徑: {self.database_path}")
    
    def _ensure_database_dir(self):
        """確保資料庫目錄存在"""
        db_dir = os.path.dirname(self.database_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"建立資料庫目錄: {db_dir}")
    
    def get_connection(self):
        """取得資料庫連接"""
        return sqlite3.connect(self.database_path)
    
    def create_tables(self):
        """建立所有資料表"""
        
        # 股票基本資料表
        stocks_table = """
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market TEXT NOT NULL,
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
            indicator_type TEXT NOT NULL,
            indicator_value REAL,
            indicator_params TEXT,
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
            update_type TEXT NOT NULL,
            last_update_date DATE NOT NULL,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # 現金流量表
        cash_flow_statements_table = """
        CREATE TABLE IF NOT EXISTS cash_flow_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            operating_cash_flow REAL,
            investing_cash_flow REAL,
            financing_cash_flow REAL,
            free_cash_flow REAL,
            net_cash_flow REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        );
        """

        # 市值資料表
        market_values_table = """
        CREATE TABLE IF NOT EXISTS market_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            market_cap REAL,
            shares_outstanding INTEGER,
            pe_ratio REAL,
            pb_ratio REAL,
            dividend_yield REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        );
        """

        # 股票分割表
        stock_splits_table = """
        CREATE TABLE IF NOT EXISTS stock_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            ex_date DATE NOT NULL,
            split_ratio REAL NOT NULL,
            before_split_price REAL,
            after_split_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        );
        """

        # 股利發放結果表
        dividend_results_table = """
        CREATE TABLE IF NOT EXISTS dividend_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            dividend_type TEXT NOT NULL,
            amount REAL NOT NULL,
            ex_dividend_date DATE,
            payment_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        );
        """

        # 月營收資料表
        monthly_revenues_table = """
        CREATE TABLE IF NOT EXISTS monthly_revenues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            revenue_year INTEGER NOT NULL,
            revenue_month INTEGER NOT NULL,
            revenue REAL NOT NULL,
            revenue_growth_mom REAL,
            revenue_growth_yoy REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, revenue_year, revenue_month)
        );
        """

        # 財務報表資料表
        financial_statements_table = """
        CREATE TABLE IF NOT EXISTS financial_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            revenue REAL,
            gross_profit REAL,
            operating_income REAL,
            net_income REAL,
            eps REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        );
        """

        # 資產負債表
        balance_sheets_table = """
        CREATE TABLE IF NOT EXISTS balance_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            total_assets REAL,
            total_liabilities REAL,
            shareholders_equity REAL,
            current_assets REAL,
            current_liabilities REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        );
        """

        # 股利政策表
        dividend_policies_table = """
        CREATE TABLE IF NOT EXISTS dividend_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            year TEXT NOT NULL,
            stock_earnings_distribution REAL,
            stock_statutory_surplus REAL,
            stock_ex_dividend_trading_date DATE,
            cash_earnings_distribution REAL,
            cash_statutory_surplus REAL,
            cash_ex_dividend_trading_date DATE,
            cash_dividend_payment_date DATE,
            total_employee_stock_dividend REAL,
            total_employee_cash_dividend REAL,
            participate_distribution_total_shares REAL,
            announcement_date DATE,
            announcement_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date, year)
        );
        """

        # 財務比率表
        financial_ratios_table = """
        CREATE TABLE IF NOT EXISTS financial_ratios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            date DATE NOT NULL,
            gross_margin REAL,
            operating_margin REAL,
            net_margin REAL,
            roe REAL,
            roa REAL,
            debt_ratio REAL,
            current_ratio REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, date)
        );
        """

        # 潛力股評分表
        stock_scores_table = """
        CREATE TABLE IF NOT EXISTS stock_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT NOT NULL,
            total_score REAL NOT NULL,
            financial_health_score REAL,
            growth_potential_score REAL,
            dividend_stability_score REAL,
            rating TEXT,
            analysis_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
            UNIQUE(stock_id, analysis_date)
        );
        """

        tables = [
            ("stocks", stocks_table),
            ("stock_prices", stock_prices_table),
            ("technical_indicators", technical_indicators_table),
            ("etf_dividends", etf_dividends_table),
            ("data_updates", data_updates_table),
            ("cash_flow_statements", cash_flow_statements_table),
            ("market_values", market_values_table),
            ("stock_splits", stock_splits_table),
            ("dividend_results", dividend_results_table),
            ("monthly_revenues", monthly_revenues_table),
            ("financial_statements", financial_statements_table),
            ("balance_sheets", balance_sheets_table),
            ("dividend_policies", dividend_policies_table),
            ("financial_ratios", financial_ratios_table),
            ("stock_scores", stock_scores_table)
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_name, table_sql in tables:
                try:
                    cursor.execute(table_sql)
                    print(f"✅ 資料表 {table_name} 建立成功")
                except Exception as e:
                    print(f"❌ 建立資料表 {table_name} 失敗: {e}")
                    raise
            
            conn.commit()
        
        # 建立索引
        self._create_indexes()
        print("✅ 所有資料表建立完成")
    
    def _create_indexes(self):
        """建立資料庫索引以提升查詢效能"""
        indexes = [
            # 基本表索引
            "CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_date ON stock_prices(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicators_stock_date ON technical_indicators(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_etf_dividends_stock_date ON etf_dividends(stock_id, announce_date);",
            "CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);",
            "CREATE INDEX IF NOT EXISTS idx_stocks_is_etf ON stocks(is_etf);",

            # 新增表索引
            "CREATE INDEX IF NOT EXISTS idx_cash_flow_stock_date ON cash_flow_statements(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_market_values_stock_date ON market_values(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_stock_splits_stock_date ON stock_splits(stock_id, ex_date);",
            "CREATE INDEX IF NOT EXISTS idx_dividend_results_stock_year ON dividend_results(stock_id, year);",
            "CREATE INDEX IF NOT EXISTS idx_monthly_revenues_stock_year_month ON monthly_revenues(stock_id, revenue_year, revenue_month);",
            "CREATE INDEX IF NOT EXISTS idx_financial_statements_stock_date ON financial_statements(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_balance_sheets_stock_date ON balance_sheets(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_dividend_policies_stock_year ON dividend_policies(stock_id, year);",
            "CREATE INDEX IF NOT EXISTS idx_financial_ratios_stock_date ON financial_ratios(stock_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_stock_scores_stock_date ON stock_scores(stock_id, analysis_date);",
            "CREATE INDEX IF NOT EXISTS idx_data_updates_type_date ON data_updates(update_type, last_update_date);",
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    print(f"⚠️  建立索引失敗: {e}")
            conn.commit()
        
        print("✅ 資料庫索引建立完成")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """執行查詢並返回結果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 取得欄位名稱
            columns = [description[0] for description in cursor.description]
            
            # 轉換為字典列表
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> None:
        """執行 SQL 語句"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
    
    def bulk_insert(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """批量插入資料"""
        if not data:
            return
        
        # 取得欄位名稱
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        sql = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        # 準備資料
        values = []
        for record in data:
            row = []
            for col in columns:
                value = record.get(col)
                # 處理日期和時間
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'date'):  # date 物件
                    value = value.isoformat()
                row.append(value)
            values.append(tuple(row))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, values)
            conn.commit()
        
        print(f"✅ 批量插入 {len(data)} 筆資料到 {table_name}")
    
    def get_table_count(self, table_name: str) -> int:
        """取得資料表記錄數"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count']
    
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
            print(f"取得資料庫大小失敗: {e}")
            return "Unknown"
    
    def vacuum_database(self):
        """清理資料庫，回收空間"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.commit()
        print("✅ 資料庫清理完成")
    
    def backup_database(self, backup_path: str):
        """備份資料庫"""
        import shutil
        shutil.copy2(self.database_path, backup_path)
        print(f"✅ 資料庫備份完成: {backup_path}")
    
    def close(self):
        """關閉資料庫連接 (sqlite3 自動管理連接)"""
        pass
