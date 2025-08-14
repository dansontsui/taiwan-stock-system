#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import sys

# 設定輸出編碼
sys.stdout.reconfigure(encoding='utf-8')

try:
    # 模擬回測結果
    rep = pd.DataFrame({
        'stock_id': ['1101', '1102', '1103', '1104'],
        'year': [2012, 2012, 2012, 2012]
    })

    # 讀取 stocks 資料
    conn = sqlite3.connect('data/taiwan_stock.db')
    stocks_meta = pd.read_sql_query("SELECT stock_id, stock_name, industry FROM stocks", conn)
    conn.close()

    print("=== rep 資料 ===")
    print(rep)
    print(f"rep stock_id 型別: {rep['stock_id'].dtype}")
    print(f"rep stock_id 樣本: {rep['stock_id'].tolist()}")

    print("\n=== stocks_meta 相關資料 ===")
    relevant = stocks_meta[stocks_meta['stock_id'].isin(['1101', '1102', '1103', '1104'])]
    print(relevant)
    print(f"stocks_meta stock_id 型別: {stocks_meta['stock_id'].dtype}")
    print(f"相關 stock_id 樣本: {relevant['stock_id'].tolist()}")

    # 確保型別一致
    print("\n=== 型別轉換 ===")
    rep['stock_id'] = rep['stock_id'].astype(str)
    stocks_meta['stock_id'] = stocks_meta['stock_id'].astype(str)
    print(f"轉換後 rep stock_id 型別: {rep['stock_id'].dtype}")
    print(f"轉換後 stocks_meta stock_id 型別: {stocks_meta['stock_id'].dtype}")

    # 合併測試
    print("\n=== 合併測試 ===")
    merged = rep.merge(stocks_meta, on='stock_id', how='left')
    print(merged[['stock_id', 'stock_name', 'industry']])

    print(f"\n=== 結果統計 ===")
    print(f"合併後有公司名稱的筆數: {merged['stock_name'].notna().sum()}/{len(merged)}")
    print(f"合併後有產業別的筆數: {merged['industry'].notna().sum()}/{len(merged)}")

except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
