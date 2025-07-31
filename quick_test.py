#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試
"""

import sqlite3

def main():
    print("快速測試...")
    
    try:
        conn = sqlite3.connect("data/taiwan_stock.db")
        cursor = conn.cursor()
        
        # 查詢前5檔非ETF股票
        cursor.execute("""
            SELECT stock_id, stock_name 
            FROM stocks 
            WHERE LENGTH(stock_id) = 4 
            AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
            AND stock_id NOT LIKE '00%'
            ORDER BY stock_id
            LIMIT 5
        """)
        
        stocks = cursor.fetchall()
        print("前5檔股票:")
        for stock in stocks:
            print(f"  {stock[0]} - {stock[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    main()
