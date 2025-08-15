#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd

def check_data_range():
    conn = sqlite3.connect('data/taiwan_stock.db')
    
    try:
        # 檢查8299的資料範圍
        query = '''
        SELECT 
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as total_records
        FROM stock_prices 
        WHERE stock_id = '8299'
        '''
        result = pd.read_sql_query(query, conn)
        print('8299 資料範圍:')
        print(result)
        
        # 檢查最後幾年的資料
        query2 = '''
        SELECT 
            strftime('%Y', date) as year,
            COUNT(*) as trading_days
        FROM stock_prices 
        WHERE stock_id = '8299' 
            AND date >= '2020-01-01'
        GROUP BY strftime('%Y', date)
        ORDER BY year
        '''
        result2 = pd.read_sql_query(query2, conn)
        print('\n2020年後的年度資料:')
        print(result2)
        
    except Exception as e:
        print(f'錯誤: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    check_data_range()
