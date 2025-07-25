#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 financial_ratios 表的實際結構
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

def check_financial_ratios_table():
    """檢查 financial_ratios 表結構"""
    print("🔍 檢查 financial_ratios 表結構")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表結構
        cursor.execute("PRAGMA table_info(financial_ratios)")
        columns = cursor.fetchall()
        
        print("📋 當前表結構:")
        for col in columns:
            print(f"   • {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # 檢查是否有必要的現金流量欄位
        column_names = [col[1] for col in columns]
        
        required_columns = [
            'operating_cash_flow',
            'investing_cash_flow', 
            'financing_cash_flow',
            'cash_flow_quality',
            'quick_ratio'
        ]
        
        print(f"\n🔍 檢查必要欄位:")
        missing_columns = []
        for col_name in required_columns:
            if col_name in column_names:
                print(f"   ✅ {col_name}")
            else:
                print(f"   ❌ {col_name} - 缺少")
                missing_columns.append(col_name)
        
        if missing_columns:
            print(f"\n⚠️ 缺少 {len(missing_columns)} 個欄位: {', '.join(missing_columns)}")
            print("\n💡 建議執行:")
            print("   python fix_database.py")
        else:
            print(f"\n✅ 所有必要欄位都存在")
        
        # 檢查資料數量
        cursor.execute("SELECT COUNT(*) FROM financial_ratios")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 總資料筆數: {total_count:,}")
        
        # 檢查1301的資料
        cursor.execute("SELECT COUNT(*) FROM financial_ratios WHERE stock_id = '1301'")
        count_1301 = cursor.fetchone()[0]
        print(f"📊 1301 資料筆數: {count_1301}")
        
        if count_1301 > 0:
            cursor.execute("SELECT * FROM financial_ratios WHERE stock_id = '1301' LIMIT 1")
            sample = cursor.fetchone()
            print(f"\n📋 1301 範例資料:")
            for i, col in enumerate(columns):
                value = sample[i] if i < len(sample) else 'NULL'
                print(f"   {col[1]}: {value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

def check_cash_flow_calculation_code():
    """檢查現金流量計算程式碼"""
    print(f"\n🔍 檢查現金流量計算相關程式碼")
    print("=" * 60)
    
    # 檢查可能的計算腳本
    scripts_to_check = [
        'scripts/calculate_revenue_growth.py',
        'scripts/collect_cash_flows.py',
        'scripts/analyze_potential_stocks.py'
    ]
    
    for script_path in scripts_to_check:
        if os.path.exists(script_path):
            print(f"✅ {script_path} 存在")
            
            # 檢查是否包含現金流量計算
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if 'operating_cash_flow' in content:
                    print(f"   📊 包含 operating_cash_flow 計算")
                if 'cash_flow_quality' in content:
                    print(f"   📊 包含 cash_flow_quality 計算")
                if 'calculate_cash_flow_ratios' in content:
                    print(f"   📊 包含 calculate_cash_flow_ratios 函數")
                    
            except Exception as e:
                print(f"   ❌ 讀取失敗: {e}")
        else:
            print(f"❌ {script_path} 不存在")

def suggest_fix():
    """建議修復方案"""
    print(f"\n💡 修復建議")
    print("=" * 60)
    
    print("如果 financial_ratios 表缺少欄位:")
    print("1. 執行資料庫修復:")
    print("   python fix_database.py")
    print()
    print("2. 重新計算財務比率:")
    print("   python scripts/calculate_revenue_growth.py")
    print()
    print("3. 重新收集現金流量:")
    print("   python scripts/collect_cash_flows.py --test")
    print()
    print("4. 檢查錯誤日誌:")
    print("   查看 logs/ 目錄下的錯誤日誌")

if __name__ == "__main__":
    check_financial_ratios_table()
    check_cash_flow_calculation_code()
    suggest_fix()
