#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查除權除息相關資料
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

def check_dividend_data():
    """檢查除權除息相關資料"""
    print("🔍 檢查除權除息相關資料")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查股利政策資料
        print("💎 股利政策資料 (dividend_policies):")
        cursor.execute("SELECT COUNT(*) FROM dividend_policies")
        total_policies = cursor.fetchone()[0]
        print(f"   總筆數: {total_policies:,}")
        
        # 檢查1301的股利政策
        cursor.execute("SELECT COUNT(*) FROM dividend_policies WHERE stock_id = '1301'")
        count_1301 = cursor.fetchone()[0]
        print(f"   1301筆數: {count_1301}")
        
        if count_1301 > 0:
            cursor.execute("SELECT * FROM dividend_policies WHERE stock_id = '1301' LIMIT 3")
            samples = cursor.fetchall()
            print(f"   1301範例資料:")
            for i, sample in enumerate(samples, 1):
                print(f"      第{i}筆: {sample}")
        
        # 檢查除權除息結果資料
        print(f"\n🎯 除權除息結果 (dividend_results):")
        cursor.execute("SELECT COUNT(*) FROM dividend_results")
        total_results = cursor.fetchone()[0]
        print(f"   總筆數: {total_results:,}")
        
        if total_results > 0:
            cursor.execute("SELECT stock_id, COUNT(*) FROM dividend_results GROUP BY stock_id")
            stock_counts = cursor.fetchall()
            print(f"   有資料的股票:")
            for stock_id, count in stock_counts:
                print(f"      {stock_id}: {count} 筆")
        else:
            print(f"   ❌ 無除權除息結果資料")
        
        # 檢查表結構
        print(f"\n📋 dividend_results 表結構:")
        cursor.execute("PRAGMA table_info(dividend_results)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   • {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

def analyze_dividend_gap():
    """分析股利政策與除權除息結果的差距"""
    print(f"\n🔍 分析股利政策與除權除息結果的差距")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取有股利政策但沒有除權除息結果的股票
        cursor.execute("""
            SELECT DISTINCT dp.stock_id, s.stock_name, COUNT(dp.stock_id) as policy_count
            FROM dividend_policies dp
            LEFT JOIN stocks s ON dp.stock_id = s.stock_id
            LEFT JOIN dividend_results dr ON dp.stock_id = dr.stock_id
            WHERE dr.stock_id IS NULL
            GROUP BY dp.stock_id, s.stock_name
            ORDER BY policy_count DESC
            LIMIT 10
        """)
        
        missing_results = cursor.fetchall()
        
        if missing_results:
            print(f"📊 有股利政策但無除權除息結果的股票:")
            for stock_id, stock_name, policy_count in missing_results:
                name = stock_name or "未知"
                print(f"   • {stock_id} ({name}): {policy_count} 筆股利政策")
        else:
            print(f"✅ 所有有股利政策的股票都有除權除息結果")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")

def suggest_dividend_collection():
    """建議除權除息資料收集方案"""
    print(f"\n💡 除權除息資料收集建議")
    print("=" * 60)
    
    print("基於檢查結果，建議以下方案:")
    print()
    print("1. 🔍 檢查API可用性:")
    print("   python 測試除權除息API.py")
    print()
    print("2. 🎯 收集除權除息結果:")
    print("   python scripts/collect_dividend_results.py --test")
    print("   python scripts/collect_dividend_results.py --batch-size 3")
    print()
    print("3. 📊 從股利政策計算除權除息結果:")
    print("   如果API不可用，可以從dividend_policies計算")
    print()
    print("4. 🔧 修復資料庫結構:")
    print("   python fix_database.py")
    print()
    print("5. 📈 重新生成報告:")
    print("   python generate_stock_report.py 1301")

def check_specific_stock(stock_id):
    """檢查特定股票的除權除息資料"""
    print(f"\n🎯 檢查 {stock_id} 的除權除息資料")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查股利政策
        cursor.execute("SELECT COUNT(*) FROM dividend_policies WHERE stock_id = ?", (stock_id,))
        policy_count = cursor.fetchone()[0]
        print(f"💎 股利政策: {policy_count} 筆")
        
        if policy_count > 0:
            cursor.execute("""
                SELECT date, cash_dividend, stock_dividend 
                FROM dividend_policies 
                WHERE stock_id = ? 
                ORDER BY date DESC 
                LIMIT 3
            """, (stock_id,))
            policies = cursor.fetchall()
            print(f"   最近3筆:")
            for date, cash, stock in policies:
                print(f"      {date}: 現金股利={cash}, 股票股利={stock}")
        
        # 檢查除權除息結果
        cursor.execute("SELECT COUNT(*) FROM dividend_results WHERE stock_id = ?", (stock_id,))
        result_count = cursor.fetchone()[0]
        print(f"🎯 除權除息結果: {result_count} 筆")
        
        if result_count > 0:
            cursor.execute("""
                SELECT date, before_price, after_price 
                FROM dividend_results 
                WHERE stock_id = ? 
                ORDER BY date DESC 
                LIMIT 3
            """, (stock_id,))
            results = cursor.fetchall()
            print(f"   最近3筆:")
            for date, before, after in results:
                print(f"      {date}: 除權前={before}, 除權後={after}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查 {stock_id} 失敗: {e}")

if __name__ == "__main__":
    check_dividend_data()
    analyze_dividend_gap()
    check_specific_stock("1301")
    check_specific_stock("2330")
    suggest_dividend_collection()
