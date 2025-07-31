#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫結構
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_database_structure():
    """檢查資料庫結構"""
    db_path = Path("data/taiwan_stock.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 獲取所有資料表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Database Tables:")
    print("=" * 50)
    
    for table in tables:
        print(f"\nTable: {table}")
        print("-" * 30)
        
        # 獲取欄位資訊
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 獲取記錄數
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Records: {count:,}")
        
        # 如果是關鍵資料表，顯示樣本資料
        if table in ['monthly_revenues', 'stock_prices', 'stocks']:
            print("Sample data:")
            cursor.execute(f"SELECT * FROM {table} LIMIT 2")
            samples = cursor.fetchall()
            for i, sample in enumerate(samples):
                print(f"  Row {i+1}: {sample[:5]}..." if len(sample) > 5 else f"  Row {i+1}: {sample}")
    
    conn.close()

if __name__ == "__main__":
    check_database_structure()
