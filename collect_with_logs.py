#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收集十年資料並顯示詳細日誌過程
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def print_with_time(message):
    """帶時間戳的打印"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

def run_script_with_logs(script_path, script_name, args=""):
    """執行腳本並顯示日誌"""
    print("=" * 80)
    print_with_time(f"開始執行: {script_name}")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 執行腳本
        if args:
            cmd = f"python {script_path} {args}"
        else:
            cmd = f"python {script_path}"
        print_with_time(f"執行命令: {cmd}")

        # 使用列表形式避免shell解析問題
        cmd_list = ["python", script_path] + (args.split() if args else [])
        print_with_time(f"命令列表: {cmd_list}")

        process = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 即時顯示輸出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # 等待進程完成
        return_code = process.poll()
        
        end_time = time.time()
        duration = end_time - start_time
        
        if return_code == 0:
            print_with_time(f"✅ {script_name} 執行成功 (耗時: {duration:.1f}秒)")
        else:
            print_with_time(f"❌ {script_name} 執行失敗 (返回碼: {return_code})")
        
        return return_code == 0
        
    except Exception as e:
        print_with_time(f"❌ 執行 {script_name} 時發生錯誤: {e}")
        return False

def check_database_status():
    """檢查資料庫狀態"""
    print("=" * 80)
    print_with_time("檢查資料庫狀態")
    print("=" * 80)
    
    try:
        import sqlite3
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # 檢查各表的資料量
        tables = [
            ('stocks', '股票基本資料'),
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '綜合損益表'),
            ('balance_sheets', '資產負債表'),
            ('dividend_policies', '股利政策'),
            ('financial_ratios', '財務比率'),
            ('stock_scores', '潛力股評分')
        ]
        
        print("資料表統計:")
        print("-" * 50)
        
        for table_name, table_desc in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"{table_desc:15}: {count:>10,} 筆")
            except sqlite3.OperationalError:
                print(f"{table_desc:15}: {'表不存在':>10}")
        
        conn.close()
        print("-" * 50)
        
    except Exception as e:
        print_with_time(f"檢查資料庫狀態時發生錯誤: {e}")

def main():
    """主函數"""
    print("=" * 80)
    print("台股系統 - 十年資料收集 (含詳細日誌)")
    print("=" * 80)
    print_with_time("開始收集程序")
    
    # 檢查初始狀態
    check_database_status()
    
    # 收集腳本列表 (添加必要的日期參數)
    collection_tasks = [
        ("scripts/collect_stock_prices_smart.py", "智能股價收集", "--start-date 2015-01-01 --end-date 2025-12-31 --batch-size 3"),
        ("scripts/collect_monthly_revenue.py", "月營收收集", "--start-date 2015-01-01 --end-date 2025-12-31 --batch-size 3"),
        ("scripts/collect_financial_statements.py", "綜合損益表收集", "--start-date 2015-01-01 --end-date 2025-12-31 --batch-size 3"),
        ("scripts/collect_balance_sheets.py", "資產負債表收集", "--start-date 2015-01-01 --end-date 2025-12-31 --batch-size 3"),
        ("scripts/collect_dividend_data.py", "股利政策收集", "--start-date 2015-01-01 --end-date 2025-12-31 --batch-size 3"),
        ("scripts/calculate_revenue_growth.py", "營收成長率計算", ""),
        ("scripts/analyze_potential_stocks.py", "潛力股分析", "")
    ]
    
    successful_tasks = 0
    total_tasks = len(collection_tasks)
    
    # 執行收集任務
    for i, (script_path, script_name, args) in enumerate(collection_tasks, 1):
        print(f"\n進度: {i}/{total_tasks}")
        
        if run_script_with_logs(script_path, script_name, args):
            successful_tasks += 1
            print_with_time(f"任務 {i} 完成")
        else:
            print_with_time(f"任務 {i} 失敗，繼續下一個任務")
        
        # 每個任務之間休息一下
        if i < total_tasks:
            print_with_time("休息5秒...")
            time.sleep(5)
    
    # 最終檢查
    print("\n" + "=" * 80)
    print_with_time("收集完成，檢查最終狀態")
    print("=" * 80)
    check_database_status()
    
    # 總結
    print("\n" + "=" * 80)
    print("收集總結")
    print("=" * 80)
    print_with_time(f"成功完成: {successful_tasks}/{total_tasks} 個任務")
    
    if successful_tasks == total_tasks:
        print_with_time("🎉 所有任務都成功完成！")
    elif successful_tasks > 0:
        print_with_time(f"⚠️  部分任務完成，{total_tasks - successful_tasks} 個任務失敗")
    else:
        print_with_time("❌ 所有任務都失敗了")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
