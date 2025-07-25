#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫結構
"""

import sqlite3
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    db_path = Config.DATABASE_PATH
except:
    db_path = "data/taiwan_stock.db"

def check_table_structure():
    """檢查資料表結構"""
    print("🔍 檢查資料庫結構")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查主要資料表
        tables = [
            'stocks',
            'stock_prices', 
            'monthly_revenues',
            'financial_statements',
            'balance_sheets',
            'cash_flow_statements',
            'dividend_results',
            'dividend_policies',
            'financial_ratios',
            'stock_scores'
        ]
        
        for table_name in tables:
            print(f"\n📋 {table_name} 表結構:")
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                if columns:
                    print("   欄位名稱:")
                    for col in columns:
                        print(f"     • {col[1]} ({col[2]})")
                    
                    # 檢查資料數量
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   資料筆數: {count:,}")
                    
                    # 顯示前幾筆資料的欄位名稱
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                        sample = cursor.fetchone()
                        if sample:
                            print("   範例資料:")
                            for i, col in enumerate(columns):
                                value = sample[i] if i < len(sample) else 'NULL'
                                print(f"     {col[1]}: {value}")
                else:
                    print("   ❌ 表不存在或無欄位")
                    
            except Exception as e:
                print(f"   ❌ 檢查失敗: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")

def check_specific_stock():
    """檢查特定股票的資料"""
    stock_id = '2330'
    print(f"\n🔍 檢查股票 {stock_id} 的資料")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查股價資料
        cursor.execute("SELECT * FROM stock_prices WHERE stock_id = ? LIMIT 3", (stock_id,))
        prices = cursor.fetchall()
        
        if prices:
            print("📈 股價資料範例:")
            cursor.execute("PRAGMA table_info(stock_prices)")
            columns = [col[1] for col in cursor.fetchall()]
            
            for i, price in enumerate(prices[:2]):
                print(f"   第{i+1}筆:")
                for j, col_name in enumerate(columns):
                    value = price[j] if j < len(price) else 'NULL'
                    print(f"     {col_name}: {value}")
                print()
        else:
            print("❌ 無股價資料")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    check_table_structure()
    check_specific_stock()
