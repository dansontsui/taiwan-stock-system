#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
綜合批次收集腳本 - 包含所有資料類型
包括：股價、月營收、財務報表、資產負債表、現金流量表、除權除息結果、股利政策
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 先嘗試導入基本模組
try:
    from config import Config
    from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
    from app.services.data_collector import FinMindDataCollector
    from loguru import logger
except ImportError:
    # 如果app模組不存在，使用替代方案
    import sqlite3
    from datetime import datetime

    # 載入環境變數
    import os
    from dotenv import load_dotenv
    load_dotenv()

    class Config:
        DATABASE_PATH = os.getenv('DATABASE_PATH', "data/taiwan_stock.db")
        FINMIND_API_URL = os.getenv('FINMIND_API_URL', "https://api.finmindtrade.com/api/v4/data")
        FINMIND_API_TOKEN = os.getenv('FINMIND_API_TOKEN', '')

    class DatabaseManager:
        def __init__(self, db_path):
            self.db_path = db_path

        def get_connection(self):
            return sqlite3.connect(self.db_path)

    class FinMindDataCollector:
        def __init__(self, api_url, api_token):
            self.api_url = api_url
            self.api_token = api_token

def wait_for_api_reset():
    """等待API重置"""
    print("⏰ API請求限制，等待70分鐘後重試...")
    for i in range(70, 0, -1):
        print(f"\r⏳ 剩餘等待時間: {i} 分鐘", end="", flush=True)
        time.sleep(60)
    print("\n✅ 等待完成，繼續收集...")

def get_stock_list(db_manager):
    """獲取股票清單"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT stock_id, stock_name 
        FROM stocks 
        WHERE is_etf = 0 
        AND LENGTH(stock_id) = 4 
        AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
        AND market IN ('TWSE', 'TPEx')
        ORDER BY stock_id
    """)
    stock_list = [{'stock_id': row[0], 'stock_name': row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return stock_list

def run_script_with_subprocess(script_name, args, timeout=3600):
    """使用subprocess執行腳本"""
    try:
        import subprocess
        cmd = [sys.executable, f"scripts/{script_name}"] + args
        print(f"執行: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            print(f"✅ {script_name} 執行成功")
            return True, result.stdout
        else:
            print(f"❌ {script_name} 執行失敗")
            print(f"錯誤: {result.stderr}")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} 執行超時")
        return False, "執行超時"
    except Exception as e:
        print(f"❌ {script_name} 執行錯誤: {e}")
        return False, str(e)

def collect_comprehensive_data(start_date, end_date, batch_size=3, test_mode=False):
    """綜合收集所有資料類型"""
    print("🚀 開始綜合資料收集")
    print(f"📅 日期範圍: {start_date} ~ {end_date}")
    print(f"🔢 批次大小: {batch_size}")
    if test_mode:
        print("🧪 測試模式：只收集前3檔股票")
    print("=" * 80)

    # 定義收集任務
    collection_tasks = [
        {
            'name': '股價資料',
            'emoji': '📈',
            'script': 'collect_stock_prices_smart.py',
            'priority': 1
        },
        {
            'name': '月營收資料',
            'emoji': '📊',
            'script': 'collect_monthly_revenue.py',
            'priority': 2
        },
        {
            'name': '綜合損益表',
            'emoji': '📋',
            'script': 'collect_financial_statements.py',
            'priority': 3
        },
        {
            'name': '資產負債表',
            'emoji': '🏦',
            'script': 'collect_balance_sheets.py',
            'priority': 4
        },
        {
            'name': '現金流量表',
            'emoji': '💰',
            'script': 'collect_cash_flows.py',
            'priority': 5
        },
        {
            'name': '除權除息結果',
            'emoji': '🎯',
            'script': 'collect_dividend_results.py',
            'priority': 6
        },
        {
            'name': '股利政策',
            'emoji': '💎',
            'script': 'collect_dividend_data.py',
            'priority': 7
        }
    ]
    
    # 執行收集任務
    total_tasks = len(collection_tasks)
    completed_tasks = 0
    failed_tasks = []

    # 準備參數
    args = [
        '--start-date', start_date,
        '--end-date', end_date,
        '--batch-size', str(batch_size)
    ]

    if test_mode:
        args.append('--test')

    for i, task in enumerate(collection_tasks, 1):
        print(f"\n{task['emoji']} 任務 {i}/{total_tasks}: {task['name']}")
        print("=" * 60)

        try:
            # 使用subprocess執行腳本
            success, output = run_script_with_subprocess(task['script'], args)

            if success:
                completed_tasks += 1
                print(f"✅ {task['name']} 完成")
            else:
                failed_tasks.append(task['name'])
                print(f"❌ {task['name']} 失敗")

        except Exception as e:
            failed_tasks.append(task['name'])
            print(f"❌ {task['name']} 執行失敗: {e}")

        # 任務間休息
        if i < total_tasks:
            print(f"\n⏳ 任務間休息30秒...")
            time.sleep(30)
    
    # 最終統計
    print("\n" + "=" * 80)
    print("🎉 綜合資料收集完成")
    print("=" * 80)
    print(f"✅ 完成任務: {completed_tasks}/{total_tasks}")
    print(f"❌ 失敗任務: {len(failed_tasks)}")
    
    if failed_tasks:
        print(f"\n❌ 失敗的任務:")
        for task_name in failed_tasks:
            print(f"   • {task_name}")
    
    # 顯示資料庫統計
    print(f"\n📊 最終資料庫統計:")
    show_database_stats()

def show_database_stats():
    """顯示資料庫統計"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        tables = [
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '綜合損益表'),
            ('balance_sheets', '資產負債表'),
            ('cash_flow_statements', '現金流量表'),
            ('dividend_results', '除權除息結果'),
            ('dividend_policies', '股利政策'),
            ('financial_ratios', '財務比率'),
            ('stock_scores', '潛力股評分')
        ]

        for table_name, display_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   {display_name}: {count:,} 筆")
            except:
                print(f"   {display_name}: 表不存在")

        conn.close()
    except Exception as e:
        print(f"   ❌ 無法獲取資料庫統計: {e}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='綜合批次收集所有資料類型')
    parser.add_argument('--start-date', default='2015-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=50, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式（只收集前3檔股票）')
    
    args = parser.parse_args()
    
    try:
        collect_comprehensive_data(
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size,
            test_mode=args.test
        )
        
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷收集")
    except Exception as e:
        logger.error(f"綜合收集失敗: {e}")
        print(f"❌ 執行失敗: {e}")

if __name__ == "__main__":
    main()
