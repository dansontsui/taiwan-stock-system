#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd

# 連接資料庫
conn = sqlite3.connect('data/taiwan_stock.db')

try:
    # 檢查營收表結構
    print('=== monthly_revenues 表結構 ===')
    structure_query = "PRAGMA table_info(monthly_revenues)"
    structure = pd.read_sql_query(structure_query, conn)
    print(structure)
    
    # 檢查8299的營收資料
    print('\n=== 8299 營收資料統計 ===')
    revenue_query = '''
    SELECT 
        COUNT(*) as total_records
    FROM monthly_revenues 
    WHERE stock_id = '8299'
    '''
    revenue_result = pd.read_sql_query(revenue_query, conn)
    print(revenue_result)
    
    # 如果有資料，檢查詳細內容
    if revenue_result.iloc[0]['total_records'] > 0:
        print('\n=== 8299 營收資料樣本 ===')
        sample_query = '''
        SELECT * 
        FROM monthly_revenues 
        WHERE stock_id = '8299'
        ORDER BY year, month
        LIMIT 10
        '''
        sample_result = pd.read_sql_query(sample_query, conn)
        print(sample_result)

except Exception as e:
    print(f'錯誤: {e}')

finally:
    conn.close()
