#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for EPS Revenue Predictor
"""

import sys
import sqlite3
from pathlib import Path

print("🔍 Simple Test Starting...")

# 測試資料庫直接連接
db_path = Path(__file__).parent.parent / "data" / "taiwan_stock.db"
print(f"Database path: {db_path}")
print(f"Database exists: {db_path.exists()}")

if db_path.exists():
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 檢查表格
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found tables: {tables[:5]}...")
        
        # 檢查2385是否存在
        cursor.execute("SELECT stock_id, stock_name FROM stocks WHERE stock_id = '2385'")
        result = cursor.fetchone()
        if result:
            print(f"✅ Stock 2385 found: {result[0]} - {result[1]}")
        else:
            print("❌ Stock 2385 not found")
        
        # 檢查月營收資料
        cursor.execute("SELECT COUNT(*) FROM monthly_revenues WHERE stock_id = '2385'")
        revenue_count = cursor.fetchone()[0]
        print(f"✅ Monthly revenue records for 2385: {revenue_count}")
        
        # 檢查財務比率資料
        cursor.execute("SELECT COUNT(*) FROM financial_ratios WHERE stock_id = '2385'")
        ratio_count = cursor.fetchone()[0]
        print(f"✅ Financial ratio records for 2385: {ratio_count}")
        
        # 檢查EPS資料
        cursor.execute("SELECT COUNT(*) FROM financial_statements WHERE stock_id = '2385' AND type = 'EPS'")
        eps_count = cursor.fetchone()[0]
        print(f"✅ EPS records for 2385: {eps_count}")
        
        conn.close()
        print("✅ Database test completed successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Database file not found")

print("\n🎉 Simple test completed!")
