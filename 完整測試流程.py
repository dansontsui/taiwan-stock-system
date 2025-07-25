#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整測試流程：清空資料庫 -> 收集資料 -> 檢查結果 -> 修復問題
"""

import sqlite3
import os
import sys
import subprocess
import time
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    db_path = Config.DATABASE_PATH
except:
    db_path = "data/taiwan_stock.db"

def clear_database():
    """清空資料庫所有資料表"""
    print("=" * 60)
    print("步驟1: 清空資料庫")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"資料庫檔案不存在: {db_path}")
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
                print(f"  清空 {table_name} 失敗: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"成功清空 {cleared_count}/{len(tables)} 個資料表")
        return cleared_count == len(tables)
        
    except Exception as e:
        print(f"清空資料庫失敗: {e}")
        return False

def check_tables_empty():
    """檢查所有資料表是否為空"""
    print("\n=" * 60)
    print("步驟2: 檢查資料表是否為空")
    print("=" * 60)
    
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
                print(f"  {table_name}: 0 筆 (空)")
            else:
                non_empty_tables.append((table_name, count))
                print(f"  {table_name}: {count} 筆 (非空)")
        
        conn.close()
        
        if non_empty_tables:
            print(f"\n警告: {len(non_empty_tables)} 個資料表仍有資料:")
            for table_name, count in non_empty_tables:
                print(f"  {table_name}: {count} 筆")
            return False
        else:
            print(f"\n確認: 所有 {len(empty_tables)} 個資料表都是空的")
            return True
            
    except Exception as e:
        print(f"檢查資料表失敗: {e}")
        return False

def run_collect_10_stocks():
    """執行 collect_10_stocks_10years.py"""
    print("\n=" * 60)
    print("步驟3: 執行 collect_10_stocks_10years.py")
    print("=" * 60)
    
    try:
        # 使用 subprocess 執行腳本
        cmd = [sys.executable, "scripts/collect_10_stocks_10years.py", "--batch-size", "3"]
        
        print(f"執行命令: {' '.join(cmd)}")
        print("開始收集資料...")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30分鐘超時
        end_time = time.time()
        
        print(f"執行時間: {end_time - start_time:.1f} 秒")
        
        if result.returncode == 0:
            print("collect_10_stocks_10years.py 執行成功")
            if result.stdout:
                print("輸出:")
                print(result.stdout[-1000:])  # 顯示最後1000字符
            return True
        else:
            print(f"collect_10_stocks_10years.py 執行失敗 (返回碼: {result.returncode})")
            if result.stderr:
                print("錯誤:")
                print(result.stderr[-1000:])
            if result.stdout:
                print("輸出:")
                print(result.stdout[-1000:])
            return False
            
    except subprocess.TimeoutExpired:
        print("執行超時 (30分鐘)")
        return False
    except Exception as e:
        print(f"執行失敗: {e}")
        return False

def check_tables_have_data():
    """檢查所有資料表是否有資料"""
    print("\n=" * 60)
    print("步驟4: 檢查資料表是否有資料")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        tables_with_data = []
        empty_tables = []
        
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                tables_with_data.append((table_name, count))
                print(f"  {table_name}: {count:,} 筆")
            else:
                empty_tables.append(table_name)
                print(f"  {table_name}: 0 筆 (空)")
        
        conn.close()
        
        print(f"\n統計:")
        print(f"  有資料的表: {len(tables_with_data)}")
        print(f"  空的表: {len(empty_tables)}")
        
        if empty_tables:
            print(f"\n警告: {len(empty_tables)} 個資料表沒有資料:")
            for table_name in empty_tables:
                print(f"  {table_name}")
            return False, empty_tables
        else:
            print(f"\n確認: 所有 {len(tables_with_data)} 個資料表都有資料")
            return True, []
            
    except Exception as e:
        print(f"檢查資料表失敗: {e}")
        return False, []

def fix_and_retry(empty_tables):
    """修復問題並重新執行"""
    print("\n=" * 60)
    print("步驟5: 修復問題並重新執行")
    print("=" * 60)
    
    print(f"需要修復的空資料表: {empty_tables}")
    
    # 這裡可以添加具體的修復邏輯
    # 例如：檢查對應的收集腳本，修復API問題等
    
    print("重新執行 collect_10_stocks_10years.py...")
    return run_collect_10_stocks()

def main():
    """主函數"""
    print("完整測試流程開始")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"資料庫: {db_path}")
    
    # 步驟1: 清空資料庫
    if not clear_database():
        print("清空資料庫失敗，繼續嘗試...")
        # 可以在這裡添加更強力的清空方法
    
    # 步驟2: 檢查是否清空成功
    max_clear_attempts = 3
    for attempt in range(max_clear_attempts):
        if check_tables_empty():
            break
        else:
            print(f"第 {attempt + 1} 次清空嘗試...")
            if not clear_database():
                print(f"第 {attempt + 1} 次清空失敗")
            if attempt == max_clear_attempts - 1:
                print("多次清空失敗，但繼續執行...")
    
    # 步驟3: 執行收集腳本
    if not run_collect_10_stocks():
        print("首次執行失敗，但繼續檢查結果...")
    
    # 步驟4: 檢查結果
    has_data, empty_tables = check_tables_have_data()
    
    # 步驟5: 如果有空表，修復並重試
    if not has_data and empty_tables:
        print(f"\n發現 {len(empty_tables)} 個空資料表，嘗試修復...")
        if fix_and_retry(empty_tables):
            # 重新檢查
            has_data, empty_tables = check_tables_have_data()
    
    # 最終結果
    print("\n" + "=" * 60)
    print("測試流程完成")
    print("=" * 60)
    
    if has_data:
        print("成功: 所有資料表都有資料")
        return True
    else:
        print(f"失敗: 仍有 {len(empty_tables)} 個資料表沒有資料")
        print("空資料表:", empty_tables)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
