#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd

# 連接資料庫
conn = sqlite3.connect('data/taiwan_stock.db')

try:
    # 檢查8299的股價資料
    print('=== 8299 股價資料統計 ===')
    price_query = '''
    SELECT 
        COUNT(*) as total_records,
        MIN(date) as earliest_date,
        MAX(date) as latest_date
    FROM stock_prices 
    WHERE stock_id = '8299'
    '''
    price_result = pd.read_sql_query(price_query, conn)
    print(price_result)
    
    # 檢查2015-2022年間的月度資料
    print('\n=== 2015-2022年間8299的月度資料分布 ===')
    monthly_query = '''
    SELECT 
        strftime('%Y-%m', date) as year_month,
        COUNT(*) as trading_days
    FROM stock_prices 
    WHERE stock_id = '8299' 
        AND date >= '2015-01-01' 
        AND date <= '2022-12-31'
    GROUP BY strftime('%Y-%m', date)
    ORDER BY year_month
    '''
    monthly_result = pd.read_sql_query(monthly_query, conn)
    print(f'2015-2022年間總月份數: {len(monthly_result)}')
    
    if len(monthly_result) > 0:
        print('\n前10個月:')
        print(monthly_result.head(10))
        print('\n後10個月:')
        print(monthly_result.tail(10))
        
        # 檢查缺失的月份
        all_months = pd.date_range('2015-01', '2022-12', freq='M')
        expected_months = [dt.strftime('%Y-%m') for dt in all_months]
        actual_months = monthly_result['year_month'].tolist()
        missing_months = [m for m in expected_months if m not in actual_months]
        
        print(f'\n預期月份數: {len(expected_months)}')
        print(f'實際月份數: {len(actual_months)}')
        print(f'缺失月份數: {len(missing_months)}')
        
        if missing_months:
            print('\n缺失的月份（前20個）:')
            for month in missing_months[:20]:
                print(f'  {month}')
    
    # 檢查8299的營收資料
    print('\n=== 8299 營收資料統計 ===')
    revenue_query = '''
    SELECT 
        COUNT(*) as total_records,
        MIN(year_month) as earliest_month,
        MAX(year_month) as latest_month
    FROM monthly_revenues 
    WHERE stock_id = '8299'
    '''
    revenue_result = pd.read_sql_query(revenue_query, conn)
    print(revenue_result)

except Exception as e:
    print(f'錯誤: {e}')

finally:
    conn.close()
