#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
from pathlib import Path

def check_database():
    """檢查資料庫狀態"""
    db_path = Path('data/taiwan_stock.db')
    
    if not db_path.exists():
        print('❌ 資料庫檔案不存在')
        return
    
    print(f'✅ 資料庫檔案存在: {db_path}')
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        # 檢查所有表
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = pd.read_sql_query(tables_query, conn)
        print('\n📋 資料庫中的表:')
        for table in tables['name']:
            print(f"  - {table}")
        
        # 檢查 stock_prices 表
        if 'stock_prices' in tables['name'].values:
            print('\n📊 stock_prices 表結構:')
            schema = pd.read_sql_query('PRAGMA table_info(stock_prices)', conn)
            for _, row in schema.iterrows():
                print(f"  {row['name']}: {row['type']}")
            
            # 檢查資料筆數
            count_query = 'SELECT COUNT(*) as count FROM stock_prices'
            count = pd.read_sql_query(count_query, conn)
            print(f'\n📈 stock_prices 表資料筆數: {count.iloc[0]["count"]:,}')
            
            # 檢查股票 6146 的資料
            sample_query = 'SELECT * FROM stock_prices WHERE stock_id = "6146" ORDER BY date DESC LIMIT 5'
            sample = pd.read_sql_query(sample_query, conn)
            print(f'\n🔍 股票 6146 的最新 5 筆資料:')
            if len(sample) > 0:
                print(sample.to_string(index=False))
            else:
                print("  ❌ 沒有找到股票 6146 的資料")
                
            # 檢查日期範圍
            date_range_query = '''
            SELECT 
                MIN(date) as min_date,
                MAX(date) as max_date,
                COUNT(DISTINCT stock_id) as stock_count
            FROM stock_prices
            '''
            date_range = pd.read_sql_query(date_range_query, conn)
            print(f'\n📅 資料日期範圍:')
            print(f"  最早日期: {date_range.iloc[0]['min_date']}")
            print(f"  最晚日期: {date_range.iloc[0]['max_date']}")
            print(f"  股票數量: {date_range.iloc[0]['stock_count']}")
            
        else:
            print('\n❌ stock_prices 表不存在')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ 檢查資料庫時發生錯誤: {e}')

if __name__ == '__main__':
    check_database()
