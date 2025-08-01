#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查2024資料
"""

import sqlite3
import pandas as pd

def main():
    print("檢查2024年資料...")
    
    try:
        conn = sqlite3.connect('data/taiwan_stock.db', timeout=10)
        
        # 檢查2024資料
        query = """
        SELECT 
            COUNT(DISTINCT stock_id) as stock_count_2024,
            COUNT(*) as records_2024
        FROM stock_prices
        WHERE date >= '2024-01-01'
        AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
        AND stock_id NOT LIKE '00%'
        """
        
        df = pd.read_sql_query(query, conn)
        
        print("2024年資料:")
        print(f"  股票數量: {df.iloc[0]['stock_count_2024']}")
        print(f"  記錄數量: {df.iloc[0]['records_2024']:,}")
        
        # 檢查月度分布
        query_monthly = """
        SELECT 
            strftime('%Y-%m', date) as month,
            COUNT(DISTINCT stock_id) as stocks,
            COUNT(*) as records
        FROM stock_prices
        WHERE date >= '2024-01-01' AND date < '2025-01-01'
        AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
        AND stock_id NOT LIKE '00%'
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
        LIMIT 12
        """
        
        df_monthly = pd.read_sql_query(query_monthly, conn)
        
        print("\n2024年月度資料:")
        for _, row in df_monthly.iterrows():
            print(f"  {row['month']}: {row['stocks']}檔, {row['records']:,}筆")
        
        conn.close()
        print("\n✅ 資料庫查詢成功")
        
        # 判斷資料是否足夠回測
        if df.iloc[0]['records_2024'] > 100000:
            print("✅ 2024資料充足，可以進行回測")
        else:
            print("⚠️ 2024資料不足")
        
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")

if __name__ == "__main__":
    main()
