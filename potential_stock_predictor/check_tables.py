#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫表結構
"""

import sqlite3
from pathlib import Path

def check_tables():
    """檢查資料庫表"""
    db_path = Path('../data/taiwan_stock.db')
    
    if not db_path.exists():
        print("資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("資料庫中的表:")
        for table in tables:
            table_name = table[0]
            print(f"  {table_name}")
            
            # 檢查表結構
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"    欄位: {[col[1] for col in columns]}")
            
            # 檢查資料數量
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    資料筆數: {count}")
            print()
        
        # 特別檢查營收相關的表
        print("檢查營收相關表:")
        revenue_tables = [name[0] for name in tables if 'revenue' in name[0].lower()]
        
        if revenue_tables:
            for table in revenue_tables:
                print(f"  營收表: {table}")
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_data = cursor.fetchall()
                print(f"    範例資料: {sample_data}")
        else:
            print("  沒有找到營收相關的表")
        
        conn.close()
        
    except Exception as e:
        print(f"檢查表時發生錯誤: {e}")

if __name__ == "__main__":
    check_tables()
