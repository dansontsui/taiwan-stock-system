# -*- coding: utf-8 -*-
"""
檢查EPS資料
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_eps_data():
    """檢查EPS資料"""
    
    print("🔍 檢查EPS資料")
    print("=" * 50)
    
    try:
        # 連接資料庫
        db_path = Path('..') / 'data' / 'taiwan_stock.db'
        conn = sqlite3.connect(db_path)
        
        # 檢查所有表
        print("1. 檢查資料庫中的所有表...")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("   資料庫中的表:")
        for table in tables:
            print(f"     {table[0]}")
        
        # 檢查financial_statements表
        if ('financial_statements',) in tables:
            print(f"\n2. 檢查financial_statements表結構...")
            cursor.execute("PRAGMA table_info(financial_statements)")
            columns = cursor.fetchall()
            print("   表結構:")
            for col in columns:
                print(f"     {col[1]} ({col[2]})")
            
            # 檢查EPS資料類型
            print(f"\n3. 檢查EPS資料類型...")
            cursor.execute("SELECT DISTINCT type FROM financial_statements WHERE type LIKE '%EPS%'")
            eps_types = cursor.fetchall()
            print("   EPS相關類型:")
            for eps_type in eps_types:
                print(f"     {eps_type[0]}")
            
            # 檢查8299的EPS資料
            print(f"\n4. 檢查8299的EPS資料...")
            query = """
            SELECT date, value as eps, type
            FROM financial_statements
            WHERE stock_id = '8299' AND type = 'EPS'
            ORDER BY date DESC
            LIMIT 10
            """
            
            cursor.execute(query)
            eps_results = cursor.fetchall()
            
            if eps_results:
                print(f"   8299最新10筆EPS資料:")
                for date, eps, type_name in eps_results:
                    print(f"     {date}: {eps} ({type_name})")
                
                print(f"   📊 EPS資料統計:")
                print(f"     總筆數: {len(eps_results)}")
                
                if len(eps_results) >= 8:
                    print(f"     ✅ EPS資料充足，可以進行預測")
                else:
                    print(f"     ⚠️ EPS資料較少，可能影響預測品質")
            else:
                print(f"   ❌ 沒有找到8299的EPS資料")
                
                # 檢查8299是否有其他財務資料
                print(f"\n5. 檢查8299的其他財務資料...")
                cursor.execute("SELECT DISTINCT type FROM financial_statements WHERE stock_id = '8299'")
                other_types = cursor.fetchall()
                
                if other_types:
                    print(f"   8299有以下財務資料類型:")
                    for type_name in other_types:
                        print(f"     {type_name[0]}")
                else:
                    print(f"   ❌ 8299沒有任何財務資料")
        else:
            print(f"\n❌ 沒有找到financial_statements表")
        
        # 檢查2385的EPS資料作為對比
        print(f"\n6. 檢查2385的EPS資料作為對比...")
        if ('financial_statements',) in tables:
            query = """
            SELECT date, value as eps
            FROM financial_statements
            WHERE stock_id = '2385' AND type = 'EPS'
            ORDER BY date DESC
            LIMIT 5
            """
            
            cursor.execute(query)
            eps_2385 = cursor.fetchall()
            
            if eps_2385:
                print(f"   2385最新5筆EPS資料:")
                for date, eps in eps_2385:
                    print(f"     {date}: {eps}")
            else:
                print(f"   ❌ 2385也沒有EPS資料")
        
        conn.close()
        
        print(f"\n" + "="*50)
        print(f"🎯 EPS資料檢查總結:")
        
        if ('financial_statements',) in tables:
            print(f"✅ financial_statements表: 存在")
            
            if eps_results:
                print(f"✅ 8299 EPS資料: 有{len(eps_results)}筆")
            else:
                print(f"❌ 8299 EPS資料: 不存在")
                print(f"   這就是為什麼EPS預測為0的原因")
        else:
            print(f"❌ financial_statements表: 不存在")
            print(f"   這就是為什麼EPS預測失敗的原因")
        
        print(f"=" * 50)
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_eps_data()
