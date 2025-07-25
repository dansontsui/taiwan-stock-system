#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查現金流量資料是否存在
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

def check_cash_flow_table():
    """檢查現金流量表"""
    print("🔍 檢查現金流量表")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cash_flow_statements'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ cash_flow_statements 表存在")
            
            # 檢查表結構
            cursor.execute("PRAGMA table_info(cash_flow_statements)")
            columns = cursor.fetchall()
            print("\n📋 表結構:")
            for col in columns:
                print(f"   • {col[1]} ({col[2]})")
            
            # 檢查總資料數量
            cursor.execute("SELECT COUNT(*) FROM cash_flow_statements")
            total_count = cursor.fetchone()[0]
            print(f"\n📊 總資料筆數: {total_count:,}")
            
            # 檢查有哪些股票有資料
            cursor.execute("SELECT stock_id, COUNT(*) FROM cash_flow_statements GROUP BY stock_id ORDER BY COUNT(*) DESC")
            stock_counts = cursor.fetchall()
            
            if stock_counts:
                print(f"\n📈 有現金流量資料的股票:")
                for stock_id, count in stock_counts[:10]:  # 顯示前10個
                    print(f"   • {stock_id}: {count} 筆")
            
            # 特別檢查2330
            cursor.execute("SELECT COUNT(*) FROM cash_flow_statements WHERE stock_id = '2330'")
            count_2330 = cursor.fetchone()[0]
            print(f"\n🎯 2330 (台積電) 現金流量資料: {count_2330} 筆")
            
            if count_2330 > 0:
                cursor.execute("SELECT * FROM cash_flow_statements WHERE stock_id = '2330' LIMIT 3")
                samples = cursor.fetchall()
                print("\n📋 2330 資料範例:")
                for i, sample in enumerate(samples, 1):
                    print(f"   第{i}筆: {sample}")
            else:
                print("❌ 2330 沒有現金流量資料")
                
        else:
            print("❌ cash_flow_statements 表不存在")
            
            # 檢查是否有其他相關表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%cash%'")
            related_tables = cursor.fetchall()
            
            if related_tables:
                print("\n🔍 找到相關表:")
                for table in related_tables:
                    print(f"   • {table[0]}")
            else:
                print("❌ 沒有找到任何現金流量相關的表")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

def check_dividend_results_table():
    """檢查除權除息結果表"""
    print("\n🔍 檢查除權除息結果表")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dividend_results'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ dividend_results 表存在")
            
            # 檢查總資料數量
            cursor.execute("SELECT COUNT(*) FROM dividend_results")
            total_count = cursor.fetchone()[0]
            print(f"📊 總資料筆數: {total_count:,}")
            
            # 特別檢查2330
            cursor.execute("SELECT COUNT(*) FROM dividend_results WHERE stock_id = '2330'")
            count_2330 = cursor.fetchone()[0]
            print(f"🎯 2330 (台積電) 除權除息資料: {count_2330} 筆")
            
        else:
            print("❌ dividend_results 表不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

def suggest_solutions():
    """建議解決方案"""
    print("\n💡 解決方案建議")
    print("=" * 60)
    
    print("如果現金流量表不存在或無資料，請執行以下步驟:")
    print()
    print("1. 🔧 修復資料庫結構:")
    print("   python fix_database.py")
    print()
    print("2. 📊 收集現金流量資料:")
    print("   python scripts/collect_cash_flows.py --test")
    print("   python scripts/collect_cash_flows.py --batch-size 3")
    print()
    print("3. 🎯 收集除權除息結果:")
    print("   python scripts/collect_dividend_results.py --test")
    print("   python scripts/collect_dividend_results.py --batch-size 3")
    print()
    print("4. 📈 執行10檔股票收集:")
    print("   python scripts/collect_10_stocks_10years.py --test")
    print("   python scripts/collect_10_stocks_10years.py --batch-size 3")
    print()
    print("5. 🔍 重新檢查資料:")
    print("   python 檢查現金流量資料.py")
    print()
    print("6. 📊 重新生成報告:")
    print("   python generate_stock_report.py 2330")

if __name__ == "__main__":
    check_cash_flow_table()
    check_dividend_results_table()
    suggest_solutions()
