#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd

def check_8299_data():
    """檢查8299的資料情況"""
    
    # 連接資料庫
    conn = sqlite3.connect('data/taiwan_stock.db')
    
    try:
        # 先檢查有哪些表
        print('=== 資料庫表格列表 ===')
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = pd.read_sql_query(tables_query, conn)
        print(tables)
        
        # 檢查股價相關的表
        price_tables = [name for name in tables['name'] if 'price' in name.lower() or 'stock' in name.lower()]
        print(f'\n股價相關表格: {price_tables}')
        
        # 檢查營收相關的表
        revenue_tables = [name for name in tables['name'] if 'revenue' in name.lower() or 'monthly' in name.lower()]
        print(f'營收相關表格: {revenue_tables}')
        
        # 如果有股價表，檢查8299的資料
        if price_tables:
            # 優先使用 stock_prices 表
            price_table = 'stock_prices' if 'stock_prices' in price_tables else price_tables[0]
            print(f'\n=== 使用表格: {price_table} ===')
            
            # 檢查表結構
            structure_query = f"PRAGMA table_info({price_table})"
            structure = pd.read_sql_query(structure_query, conn)
            print('表格結構:')
            print(structure)
            
            # 檢查8299的資料
            print(f'\n=== 8299 在 {price_table} 的資料統計 ===')
            count_query = f"SELECT COUNT(*) as total_records FROM {price_table} WHERE stock_id = '8299'"
            count_result = pd.read_sql_query(count_query, conn)
            print(f'總記錄數: {count_result.iloc[0]["total_records"]}')
            
            if count_result.iloc[0]["total_records"] > 0:
                # 檢查日期範圍
                date_query = f"""
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM {price_table} 
                WHERE stock_id = '8299'
                """
                date_result = pd.read_sql_query(date_query, conn)
                print('日期範圍:')
                print(date_result)
                
                # 檢查2015-2022年間的月度資料
                print(f'\n=== 2015-2022年間8299的月度資料分布 ===')
                monthly_query = f"""
                SELECT 
                    strftime('%Y-%m', date) as year_month,
                    COUNT(*) as trading_days
                FROM {price_table} 
                WHERE stock_id = '8299' 
                    AND date >= '2015-01-01' 
                    AND date <= '2022-12-31'
                GROUP BY strftime('%Y-%m', date)
                ORDER BY year_month
                """
                monthly_result = pd.read_sql_query(monthly_query, conn)
                print(f'2015-2022年間總月份數: {len(monthly_result)}')
                
                if len(monthly_result) > 0:
                    print('前10個月:')
                    print(monthly_result.head(10))
                    print('後10個月:')
                    print(monthly_result.tail(10))
                    
                    # 檢查缺失的月份
                    all_months = pd.date_range('2015-01', '2022-12', freq='M')
                    expected_months = [dt.strftime('%Y-%m') for dt in all_months]
                    actual_months = monthly_result['year_month'].tolist()
                    missing_months = [m for m in expected_months if m not in actual_months]
                    
                    print(f'\n缺失的月份數: {len(missing_months)}')
                    if missing_months:
                        print('缺失的月份:')
                        for month in missing_months[:20]:  # 只顯示前20個
                            print(f'  {month}')
                        if len(missing_months) > 20:
                            print(f'  ... 還有 {len(missing_months) - 20} 個月份')
        
        # 檢查營收資料
        if revenue_tables:
            revenue_table = revenue_tables[0]
            print(f'\n=== 使用營收表格: {revenue_table} ===')
            
            # 檢查表結構
            structure_query = f"PRAGMA table_info({revenue_table})"
            structure = pd.read_sql_query(structure_query, conn)
            print('表格結構:')
            print(structure)
            
            # 檢查8299的營收資料
            print(f'\n=== 8299 在 {revenue_table} 的資料統計 ===')
            revenue_count_query = f"SELECT COUNT(*) as total_records FROM {revenue_table} WHERE stock_id = '8299'"
            revenue_count = pd.read_sql_query(revenue_count_query, conn)
            print(f'總記錄數: {revenue_count.iloc[0]["total_records"]}')
            
            if revenue_count.iloc[0]["total_records"] > 0:
                # 檢查營收資料範圍
                revenue_range_query = f"""
                SELECT 
                    MIN(year_month) as earliest_month,
                    MAX(year_month) as latest_month
                FROM {revenue_table} 
                WHERE stock_id = '8299'
                """
                revenue_range = pd.read_sql_query(revenue_range_query, conn)
                print('營收資料範圍:')
                print(revenue_range)
    
    except Exception as e:
        print(f'錯誤: {e}')
    
    finally:
        conn.close()

if __name__ == '__main__':
    check_8299_data()
