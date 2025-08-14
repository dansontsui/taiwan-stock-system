#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import sys

# 設定輸出編碼
sys.stdout.reconfigure(encoding='utf-8')

try:
    conn = sqlite3.connect('data/taiwan_stock.db')
    cursor = conn.cursor()

    # 檢查 stocks 表結構
    cursor.execute("PRAGMA table_info(stocks)")
    columns = cursor.fetchall()
    print("stocks 表結構:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # 檢查 1101-1104 是否在 stocks 表中
    test_ids = ['1101', '1102', '1103', '1104']
    print("\n檢查特定股票:")
    for stock_id in test_ids:
        cursor.execute('SELECT stock_id, stock_name, industry FROM stocks WHERE stock_id = ?', (stock_id,))
        result = cursor.fetchone()
        if result:
            print(f'{stock_id}: {result[1]} ({result[2]})')
        else:
            print(f'{stock_id}: 找不到')

    # 檢查總筆數
    cursor.execute('SELECT COUNT(*) FROM stocks')
    count = cursor.fetchone()[0]
    print(f"\nstocks 表總筆數: {count}")

    conn.close()

except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
