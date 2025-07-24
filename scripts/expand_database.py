#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫擴展腳本 - 新增潛力股分析所需的資料表
"""

import sys
import os
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from loguru import logger

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'expand_database.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def create_financial_tables(db_manager):
    """創建財務相關資料表"""
    
    # 1. 綜合損益表
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
    
    # 2. 資產負債表
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
    
    # 3. 現金流量表
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
    
    # 4. 月營收表
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
    
    # 5. 股利政策表
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
    
    # 6. 除權息結果表
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
    
    tables = [
        ("financial_statements", financial_statements_table),
        ("balance_sheets", balance_sheets_table),
        ("cash_flow_statements", cash_flow_statements_table),
        ("monthly_revenues", monthly_revenues_table),
        ("dividend_policies", dividend_policies_table),
        ("dividend_results", dividend_results_table)
    ]
    
    return tables

def create_analysis_tables(db_manager):
    """創建分析相關資料表"""
    
    # 7. 財務比率表
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
        pe_ratio REAL,
        pb_ratio REAL,
        dividend_yield REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date)
    );
    """
    
    # 8. 潛力股評分表
    stock_scores_table = """
    CREATE TABLE IF NOT EXISTS stock_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        analysis_date DATE NOT NULL,
        financial_health_score REAL,
        profitability_score REAL,
        growth_score REAL,
        valuation_score REAL,
        dividend_score REAL,
        total_score REAL,
        grade TEXT,
        score_details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, analysis_date)
    );
    """
    
    # 9. 市值相關表 (付費功能)
    market_values_table = """
    CREATE TABLE IF NOT EXISTS market_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        market_value BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date)
    );
    """
    
    # 10. 股票分割表
    stock_splits_table = """
    CREATE TABLE IF NOT EXISTS stock_splits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id TEXT NOT NULL,
        date DATE NOT NULL,
        type TEXT,
        before_price REAL,
        after_price REAL,
        max_price REAL,
        min_price REAL,
        open_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
        UNIQUE(stock_id, date)
    );
    """
    
    tables = [
        ("financial_ratios", financial_ratios_table),
        ("stock_scores", stock_scores_table),
        ("market_values", market_values_table),
        ("stock_splits", stock_splits_table)
    ]
    
    return tables

def create_indexes(db_manager):
    """創建索引以提升查詢效能"""
    indexes = [
        # 財務報表索引
        "CREATE INDEX IF NOT EXISTS idx_financial_statements_stock_date ON financial_statements(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_balance_sheets_stock_date ON balance_sheets(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_cash_flow_statements_stock_date ON cash_flow_statements(stock_id, date);",
        
        # 營收和股利索引
        "CREATE INDEX IF NOT EXISTS idx_monthly_revenues_stock_year_month ON monthly_revenues(stock_id, revenue_year, revenue_month);",
        "CREATE INDEX IF NOT EXISTS idx_dividend_policies_stock_year ON dividend_policies(stock_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_dividend_results_stock_date ON dividend_results(stock_id, date);",
        
        # 分析相關索引
        "CREATE INDEX IF NOT EXISTS idx_financial_ratios_stock_date ON financial_ratios(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_scores_analysis_date ON stock_scores(analysis_date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_scores_total_score ON stock_scores(total_score DESC);",
        
        # 市值和分割索引
        "CREATE INDEX IF NOT EXISTS idx_market_values_stock_date ON market_values(stock_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_splits_stock_date ON stock_splits(stock_id, date);",
    ]
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            logger.info(f"索引創建成功: {index_sql[:50]}...")
        except Exception as e:
            logger.warning(f"索引創建失敗: {e}")
    
    conn.commit()
    conn.close()

def main():
    """主函數"""
    print("=" * 60)
    print("台股潛力股分析系統 - 資料庫擴展")
    print("=" * 60)
    
    # 初始化日誌
    init_logging()
    logger.info("開始擴展資料庫")
    
    try:
        # 建立資料庫管理器
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        
        print(f"資料庫路徑: {Config.DATABASE_PATH}")
        
        # 創建財務相關資料表
        print("\n正在創建財務相關資料表...")
        financial_tables = create_financial_tables(db_manager)
        
        # 創建分析相關資料表
        print("正在創建分析相關資料表...")
        analysis_tables = create_analysis_tables(db_manager)
        
        # 合併所有資料表
        all_tables = financial_tables + analysis_tables
        
        # 執行資料表創建
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        for table_name, table_sql in all_tables:
            try:
                cursor.execute(table_sql)
                print(f"✅ 資料表 {table_name} 創建成功")
                logger.info(f"資料表 {table_name} 創建成功")
            except Exception as e:
                print(f"❌ 資料表 {table_name} 創建失敗: {e}")
                logger.error(f"資料表 {table_name} 創建失敗: {e}")
        
        conn.commit()
        conn.close()
        
        # 創建索引
        print("\n正在創建索引...")
        create_indexes(db_manager)
        print("✅ 索引創建完成")
        
        # 顯示資料表資訊
        print("\n新增資料表資訊:")
        print("-" * 40)
        
        new_tables = [name for name, _ in all_tables]
        for table in new_tables:
            try:
                count = db_manager.get_table_count(table)
                print(f"{table:<25}: {count:>10} 筆記錄")
            except Exception as e:
                print(f"{table:<25}: 創建失敗 ({e})")
        
        print("\n" + "=" * 60)
        print("✅ 資料庫擴展完成！")
        print("=" * 60)
        
        print("\n下一步:")
        print("1. 執行 python scripts/collect_financial_data.py 收集財務資料")
        print("2. 執行 python scripts/calculate_ratios.py 計算財務比率")
        print("3. 執行 python scripts/analyze_potential_stocks.py 分析潛力股")
        
        logger.info("資料庫擴展成功完成")
        
    except Exception as e:
        error_msg = f"資料庫擴展失敗: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
