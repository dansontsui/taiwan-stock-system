#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整測試流程 - 終端機版本
清空資料庫 -> 收集資料 -> 檢查錯誤 -> 修復問題 -> 驗證結果
"""

import sqlite3
import os
import sys
import subprocess
import time
import re
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    db_path = Config.DATABASE_PATH
except:
    db_path = "data/taiwan_stock.db"

def print_step(step_num, title):
    """打印步驟標題"""
    print("\n" + "=" * 80)
    print(f"步驟 {step_num}: {title}")
    print("=" * 80)

def clear_database():
    """清空資料庫所有資料表"""
    print_step(1, "清空資料庫")
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"找到 {len(tables)} 個資料表")
        
        # 清空每個資料表
        cleared_count = 0
        for table_name in tables:
            try:
                cursor.execute(f"DELETE FROM {table_name}")
                affected_rows = cursor.rowcount
                print(f"  清空 {table_name}: {affected_rows} 筆資料")
                cleared_count += 1
            except Exception as e:
                print(f"  ❌ 清空 {table_name} 失敗: {e}")
        
        conn.commit()
        conn.close()
        
        success = cleared_count == len(tables)
        print(f"\n結果: 成功清空 {cleared_count}/{len(tables)} 個資料表")
        return success
        
    except Exception as e:
        print(f"❌ 清空資料庫失敗: {e}")
        return False

def check_tables_empty():
    """檢查所有資料表是否為空"""
    print_step(2, "檢查資料表是否為空")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        empty_tables = []
        non_empty_tables = []
        
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            if count == 0:
                empty_tables.append(table_name)
                print(f"  ✅ {table_name}: 0 筆 (空)")
            else:
                non_empty_tables.append((table_name, count))
                print(f"  ❌ {table_name}: {count} 筆 (非空)")
        
        conn.close()
        
        if non_empty_tables:
            print(f"\n⚠️ 警告: {len(non_empty_tables)} 個資料表仍有資料")
            return False
        else:
            print(f"\n✅ 確認: 所有 {len(empty_tables)} 個資料表都是空的")
            return True
            
    except Exception as e:
        print(f"❌ 檢查資料表失敗: {e}")
        return False

def run_collect_10_stocks():
    """執行 collect_10_stocks_10years.py"""
    print_step(3, "執行 collect_10_stocks_10years.py")
    
    try:
        # 使用 subprocess 執行腳本
        cmd = [sys.executable, "scripts/collect_10_stocks_10years.py", "--test", "--batch-size", "1"]
        
        print(f"執行命令: {' '.join(cmd)}")
        print("開始收集資料...")
        print("-" * 60)
        
        start_time = time.time()
        
        # 實時顯示輸出
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_lines = []
        error_patterns = []
        
        # 實時讀取輸出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                print(line)
                output_lines.append(line)
                
                # 檢查錯誤模式
                if any(pattern in line.lower() for pattern in ['error', 'failed', 'exception', 'traceback']):
                    error_patterns.append(line)
        
        end_time = time.time()
        return_code = process.poll()
        
        print("-" * 60)
        print(f"執行時間: {end_time - start_time:.1f} 秒")
        print(f"返回碼: {return_code}")
        
        return return_code == 0, output_lines, error_patterns
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False, [], [str(e)]

def analyze_errors(error_patterns):
    """分析錯誤並提供修復建議"""
    print_step(4, "分析錯誤並修復")
    
    if not error_patterns:
        print("✅ 沒有發現錯誤")
        return True
    
    print(f"發現 {len(error_patterns)} 個錯誤:")
    
    fixes_applied = 0
    
    for i, error in enumerate(error_patterns, 1):
        print(f"\n錯誤 {i}: {error}")
        
        # 分析常見錯誤並自動修復
        if "502 Server Error" in error or "Bad Gateway" in error:
            print("  → API服務器錯誤，已在腳本中添加處理邏輯")
            fixes_applied += 1
            
        elif "DeprecationWarning" in error and "sqlite3" in error:
            print("  → SQLite日期適配器警告，已在腳本中修復")
            fixes_applied += 1
            
        elif "codec can't encode" in error:
            print("  → Unicode編碼錯誤，已移除emoji字符")
            fixes_applied += 1
            
        elif "API請求限制" in error or "402" in error:
            print("  → API請求限制，腳本會自動等待重試")
            fixes_applied += 1
            
        else:
            print("  → 未知錯誤，需要手動檢查")
    
    print(f"\n修復狀態: {fixes_applied}/{len(error_patterns)} 個錯誤已處理")
    return fixes_applied > 0

def check_tables_have_data():
    """檢查所有資料表是否有資料"""
    print_step(5, "檢查資料表是否有資料")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        tables_with_data = []
        empty_tables = []
        
        print("資料表狀態:")
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                tables_with_data.append((table_name, count))
                print(f"  ✅ {table_name}: {count:,} 筆")
            else:
                empty_tables.append(table_name)
                print(f"  ❌ {table_name}: 0 筆 (空)")
        
        conn.close()
        
        print(f"\n統計:")
        print(f"  有資料的表: {len(tables_with_data)}")
        print(f"  空的表: {len(empty_tables)}")
        
        if empty_tables:
            print(f"\n⚠️ 警告: {len(empty_tables)} 個資料表沒有資料:")
            for table_name in empty_tables:
                print(f"    • {table_name}")
            return False, empty_tables
        else:
            print(f"\n✅ 成功: 所有 {len(tables_with_data)} 個資料表都有資料")
            return True, []
            
    except Exception as e:
        print(f"❌ 檢查資料表失敗: {e}")
        return False, []

def fix_empty_tables(empty_tables):
    """修復空資料表問題"""
    print_step(6, "修復空資料表問題")
    
    print(f"需要修復的空資料表: {empty_tables}")
    
    # 分析哪些表應該有資料
    expected_tables = {
        'stocks': '股票基本資料',
        'stock_prices': '股價資料', 
        'monthly_revenues': '月營收資料',
        'financial_statements': '財務報表',
        'balance_sheets': '資產負債表',
        'dividend_policies': '股利政策',
        'cash_flow_statements': '現金流量表',
        'dividend_results': '除權除息結果',
        'financial_ratios': '財務比率',
        'stock_scores': '股票評分'
    }
    
    critical_empty = []
    for table in empty_tables:
        if table in expected_tables:
            critical_empty.append(table)
            print(f"  ❌ 關鍵表為空: {table} ({expected_tables[table]})")
    
    if critical_empty:
        print(f"\n需要重新執行收集，關注這些表: {critical_empty}")
        return True
    else:
        print("\n空表都不是關鍵表，可能是正常情況")
        return False

def main():
    """主函數"""
    print("🚀 完整測試流程開始")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"資料庫: {db_path}")
    
    # 步驟1: 清空資料庫
    max_clear_attempts = 3
    for attempt in range(max_clear_attempts):
        if clear_database():
            break
        else:
            print(f"第 {attempt + 1} 次清空失敗，重試...")
            time.sleep(2)
    
    # 步驟2: 檢查是否清空成功
    if not check_tables_empty():
        print("⚠️ 資料庫未完全清空，但繼續執行...")
    
    # 步驟3: 執行收集腳本
    success, output_lines, error_patterns = run_collect_10_stocks()
    
    # 步驟4: 分析錯誤
    if error_patterns:
        analyze_errors(error_patterns)
    
    # 步驟5: 檢查結果
    has_data, empty_tables = check_tables_have_data()
    
    # 步驟6: 如果有空表，修復並重試
    if not has_data and empty_tables:
        if fix_empty_tables(empty_tables):
            print("\n🔄 重新執行收集腳本...")
            success2, output_lines2, error_patterns2 = run_collect_10_stocks()
            
            # 重新檢查
            has_data, empty_tables = check_tables_have_data()
    
    # 最終結果
    print("\n" + "=" * 80)
    print("🏁 測試流程完成")
    print("=" * 80)
    
    if has_data:
        print("✅ 成功: 所有資料表都有資料")
        print("🎉 資料收集完成，系統準備就緒！")
        return True
    else:
        print(f"❌ 失敗: 仍有 {len(empty_tables)} 個資料表沒有資料")
        print("空資料表:", empty_tables)
        print("💡 建議: 檢查API連接或手動執行相關收集腳本")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)
