#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細檢查資料庫表結構
"""

import sqlite3
import pandas as pd
from pathlib import Path
import os

def check_db_tables():
    """詳細檢查資料庫表"""
    # 嘗試多個可能的路徑
    possible_paths = [
        Path('../data/taiwan_stock.db'),
        Path('data/taiwan_stock.db'),
        Path('taiwan_stock.db')
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("錯誤: 找不到資料庫檔案")
        print(f"當前工作目錄: {os.getcwd()}")
        print(f"嘗試的路徑: {[str(p) for p in possible_paths]}")
        return
    
    print(f"找到資料庫: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n資料庫中共有 {len(tables)} 個表:")
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            print(f"{i}. {table_name}")
        
        # 檢查是否有營收相關的表
        revenue_tables = [name[0] for name in tables if 'revenue' in name[0].lower()]
        if revenue_tables:
            print(f"\n找到 {len(revenue_tables)} 個營收相關表:")
            for table in revenue_tables:
                print(f"  - {table}")
                
                # 檢查表結構
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"    欄位: {[col[1] for col in columns]}")
                
                # 檢查資料數量
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    資料筆數: {count}")
                
                # 檢查資料範例
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"    資料範例: {sample}")
        else:
            print("\n沒有找到營收相關的表")
        
        # 檢查財務報表相關的表
        financial_tables = [name[0] for name in tables if 'financial' in name[0].lower() or 'statement' in name[0].lower()]
        if financial_tables:
            print(f"\n找到 {len(financial_tables)} 個財務報表相關表:")
            for table in financial_tables:
                print(f"  - {table}")
                
                # 檢查資料數量
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    資料筆數: {count}")
        else:
            print("\n沒有找到財務報表相關的表")
        
        # 檢查資產負債表相關的表
        balance_tables = [name[0] for name in tables if 'balance' in name[0].lower()]
        if balance_tables:
            print(f"\n找到 {len(balance_tables)} 個資產負債表相關表:")
            for table in balance_tables:
                print(f"  - {table}")
                
                # 檢查資料數量
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    資料筆數: {count}")
        else:
            print("\n沒有找到資產負債表相關的表")
        
        # 檢查現金流相關的表
        cash_tables = [name[0] for name in tables if 'cash' in name[0].lower() or 'flow' in name[0].lower()]
        if cash_tables:
            print(f"\n找到 {len(cash_tables)} 個現金流相關表:")
            for table in cash_tables:
                print(f"  - {table}")
                
                # 檢查資料數量
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    資料筆數: {count}")
        else:
            print("\n沒有找到現金流相關的表")
        
        # 檢查股價資料
        print("\n檢查股價資料:")
        cursor.execute("SELECT COUNT(*) FROM stock_prices")
        count = cursor.fetchone()[0]
        print(f"  股價資料筆數: {count}")
        
        cursor.execute("SELECT MIN(date), MAX(date) FROM stock_prices")
        date_range = cursor.fetchone()
        print(f"  日期範圍: {date_range[0]} 到 {date_range[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"檢查資料庫時發生錯誤: {e}")

if __name__ == "__main__":
    check_db_tables()
