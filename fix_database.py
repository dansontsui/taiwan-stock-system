#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復資料庫 - 創建缺失的財務資料表
"""

import sys
import os
import sqlite3
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def create_missing_tables():
    """創建缺失的財務資料表"""
    
    print("=" * 60)
    print("修復資料庫 - 創建缺失的財務資料表")
    print("=" * 60)
    
    # 連接資料庫
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. 月營收表
    monthly_revenues_table = """
    CREATE TABLE IF NOT EXISTS monthly_revenues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        country TEXT,
        revenue BIGINT,
        revenue_month INTEGER,
        revenue_year INTEGER,
        revenue_growth_mom REAL,
        revenue_growth_yoy REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, revenue_year, revenue_month)
    );
    """
    
    # 2. 綜合損益表
    financial_statements_table = """
    CREATE TABLE IF NOT EXISTS financial_statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        type TEXT NOT NULL,
        value REAL,
        origin_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date, type)
    );
    """
    
    # 3. 資產負債表
    balance_sheets_table = """
    CREATE TABLE IF NOT EXISTS balance_sheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        type TEXT NOT NULL,
        value REAL,
        origin_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date, type)
    );
    """

    # 4. 現金流量表
    cash_flow_statements_table = """
    CREATE TABLE IF NOT EXISTS cash_flow_statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        type TEXT NOT NULL,
        value REAL,
        origin_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date, type)
    );
    """

    # 5. 除權除息結果表
    dividend_results_table = """
    CREATE TABLE IF NOT EXISTS dividend_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        before_price REAL,
        after_price REAL,
        stock_and_cache_dividend REAL,
        stock_or_cache_dividend TEXT,
        max_price REAL,
        min_price REAL,
        open_price REAL,
        reference_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date)
    );
    """

    # 6. 除權除息分析表
    dividend_analysis_table = """
    CREATE TABLE IF NOT EXISTS dividend_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        ex_dividend_date DATE NOT NULL,
        fill_right_ratio REAL,
        price_performance REAL,
        dividend_yield REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, ex_dividend_date)
    );
    """
    
    # 4. 股利政策表
    dividend_policies_table = """
    CREATE TABLE IF NOT EXISTS dividend_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        cash_dividend REAL,
        stock_dividend REAL,
        cash_ex_dividend_date DATE,
        stock_ex_dividend_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date)
    );
    """
    
    # 5. 財務比率表 (更新版本，新增現金流量欄位)
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
        revenue_growth_mom REAL,
        revenue_growth_yoy REAL,
        -- 新增現金流量相關欄位
        operating_cash_flow REAL,
        investing_cash_flow REAL,
        financing_cash_flow REAL,
        cash_flow_quality REAL,
        pe_ratio REAL,
        pb_ratio REAL,
        dividend_yield REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date)
    );
    """
    
    # 6. 潛力股評分表
    stock_scores_table = """
    CREATE TABLE IF NOT EXISTS stock_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        stock_name TEXT,
        total_score REAL NOT NULL,
        growth_score REAL,
        profitability_score REAL,
        stability_score REAL,
        valuation_score REAL,
        dividend_score REAL,
        analysis_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, analysis_date)
    );
    """
    
    # 要創建的表
    tables = [
        ("monthly_revenues", monthly_revenues_table),
        ("financial_statements", financial_statements_table),
        ("balance_sheets", balance_sheets_table),
        ("cash_flow_statements", cash_flow_statements_table),
        ("dividend_results", dividend_results_table),
        ("dividend_analysis", dividend_analysis_table),
        ("dividend_policies", dividend_policies_table),
        ("financial_ratios", financial_ratios_table),
        ("stock_scores", stock_scores_table)
    ]
    
    # 創建表
    for table_name, table_sql in tables:
        try:
            cursor.execute(table_sql)
            print(f"✅ 資料表 {table_name} 創建成功")
        except Exception as e:
            print(f"❌ 資料表 {table_name} 創建失敗: {e}")

    # 特別處理 financial_ratios 表的欄位更新
    print("\n🔧 檢查並更新 financial_ratios 表結構...")
    try:
        # 檢查是否缺少現金流量欄位
        cursor.execute("PRAGMA table_info(financial_ratios)")
        columns = [col[1] for col in cursor.fetchall()]

        missing_columns = []
        required_columns = [
            ('operating_cash_flow', 'REAL'),
            ('investing_cash_flow', 'REAL'),
            ('financing_cash_flow', 'REAL'),
            ('cash_flow_quality', 'REAL'),
            ('quick_ratio', 'REAL')
        ]

        for col_name, col_type in required_columns:
            if col_name not in columns:
                missing_columns.append((col_name, col_type))

        # 添加缺少的欄位
        for col_name, col_type in missing_columns:
            try:
                cursor.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col_name} {col_type}")
                print(f"✅ 添加欄位: {col_name}")
            except Exception as e:
                print(f"⚠️ 添加欄位 {col_name} 失敗 (可能已存在): {e}")

        if not missing_columns:
            print("✅ financial_ratios 表結構已是最新")

    except Exception as e:
        print(f"❌ 更新 financial_ratios 表結構失敗: {e}")

    # 創建索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_monthly_revenues_stock_date ON monthly_revenues(stock_id, revenue_year, revenue_month);",
        "CREATE INDEX IF NOT EXISTS idx_financial_statements_stock_date ON financial_statements(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_balance_sheets_stock_date ON balance_sheets(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_cash_flow_statements_stock_date ON cash_flow_statements(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_dividend_results_stock_date ON dividend_results(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_dividend_analysis_stock_date ON dividend_analysis(stock_id, ex_dividend_date);",
        "CREATE INDEX IF NOT EXISTS idx_dividend_policies_stock_date ON dividend_policies(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_financial_ratios_stock_date ON financial_ratios(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_scores_stock_date ON stock_scores(stock_id, analysis_date);",
    ]
    
    print("\n創建索引...")
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"索引創建失敗: {e}")
    
    conn.commit()
    conn.close()
    
    print("✅ 索引創建完成")
    print("\n" + "=" * 60)
    print("✅ 資料庫修復完成！")
    print("=" * 60)
    
    # 檢查結果
    print("\n檢查資料表狀態...")
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    for table_name, _ in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name:<25}: {count:>8} 筆")
        except Exception as e:
            print(f"{table_name:<25}: 錯誤 - {e}")
    
    conn.close()

if __name__ == "__main__":
    create_missing_tables()
