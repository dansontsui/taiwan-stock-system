#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫結構和內容
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

# 設置輸出編碼
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def check_database():
    """檢查資料庫"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print('找不到資料庫檔案')
        return

    print('台股資料庫分析')
    print('=' * 60)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 查看所有資料表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f'資料庫包含 {len(tables)} 個資料表:')
    for table in tables:
        print(f'  - {table[0]}')

    # 查看關鍵資料表的詳細資訊
    key_tables = ['stocks', 'stock_prices', 'monthly_revenues', 'financial_statements', 'balance_sheets']

    for table_name in key_tables:
        if (table_name,) in tables:
            print(f'\n{table_name} 資料表:')

            # 記錄數
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'  記錄數: {count:,}')

            # 欄位資訊
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            print(f'  欄位數: {len(columns)}')
            print('  主要欄位:')
            for col in columns[:8]:  # 顯示前8個欄位
                print(f'    - {col[1]} ({col[2]})')
            if len(columns) > 8:
                print(f'    ... 還有 {len(columns) - 8} 個欄位')

            # 樣本資料
            if count > 0:
                cursor.execute(f'SELECT * FROM {table_name} LIMIT 2')
                samples = cursor.fetchall()
                print('  樣本資料:')
                for i, sample in enumerate(samples):
                    print(f'    第{i+1}筆: {sample[:5]}...' if len(sample) > 5 else f'    第{i+1}筆: {sample}')

    conn.close()
    print('\n資料庫檢查完成')

if __name__ == "__main__":
    check_database()
