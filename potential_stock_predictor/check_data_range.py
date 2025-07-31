#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫中的資料範圍
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_data_range():
    """檢查資料範圍"""
    db_path = Path('../data/taiwan_stock.db')
    
    if not db_path.exists():
        print("資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 檢查股價資料的日期範圍
        print("檢查股價資料範圍...")
        query = """
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(DISTINCT date) as total_days,
            COUNT(DISTINCT stock_id) as total_stocks
        FROM stock_prices
        """
        
        result = pd.read_sql_query(query, conn)
        print("股價資料範圍:")
        print(f"  最早日期: {result['min_date'].iloc[0]}")
        print(f"  最晚日期: {result['max_date'].iloc[0]}")
        print(f"  總交易日: {result['total_days'].iloc[0]}")
        print(f"  總股票數: {result['total_stocks'].iloc[0]}")
        
        # 檢查2024年的資料
        print("\n檢查2024年資料...")
        query2 = """
        SELECT date, COUNT(DISTINCT stock_id) as stock_count
        FROM stock_prices 
        WHERE date >= '2024-01-01' AND date <= '2024-12-31'
        GROUP BY date
        ORDER BY date DESC
        LIMIT 10
        """
        
        result2 = pd.read_sql_query(query2, conn)
        if len(result2) > 0:
            print("2024年最近的股價資料:")
            for _, row in result2.iterrows():
                print(f"  {row['date']}: {row['stock_count']} 檔股票")
        else:
            print("沒有2024年的資料")
        
        # 檢查2025年的資料
        print("\n檢查2025年資料...")
        query3 = """
        SELECT date, COUNT(DISTINCT stock_id) as stock_count
        FROM stock_prices 
        WHERE date >= '2025-01-01'
        GROUP BY date
        ORDER BY date DESC
        LIMIT 5
        """
        
        result3 = pd.read_sql_query(query3, conn)
        if len(result3) > 0:
            print("2025年的股價資料:")
            for _, row in result3.iterrows():
                print(f"  {row['date']}: {row['stock_count']} 檔股票")
        else:
            print("沒有2025年的資料")
        
        # 檢查營收資料
        print("\n檢查營收資料...")
        query4 = """
        SELECT 
            MIN(year || '-' || CASE WHEN month < 10 THEN '0' || month ELSE month END) as min_month,
            MAX(year || '-' || CASE WHEN month < 10 THEN '0' || month ELSE month END) as max_month,
            COUNT(DISTINCT stock_id) as total_stocks
        FROM monthly_revenue
        """
        
        result4 = pd.read_sql_query(query4, conn)
        if len(result4) > 0:
            print("營收資料範圍:")
            print(f"  最早月份: {result4['min_month'].iloc[0]}")
            print(f"  最晚月份: {result4['max_month'].iloc[0]}")
            print(f"  總股票數: {result4['total_stocks'].iloc[0]}")
        
        conn.close()
        
        # 建議可用的日期
        print("\n建議使用的特徵計算日期:")
        if len(result2) > 0:
            latest_2024 = result2['date'].iloc[0]
            print(f"  2024年最新: {latest_2024}")
        
        if len(result) > 0:
            latest_overall = result['max_date'].iloc[0]
            print(f"  整體最新: {latest_overall}")
        
    except Exception as e:
        print(f"檢查資料時發生錯誤: {e}")

if __name__ == "__main__":
    check_data_range()
