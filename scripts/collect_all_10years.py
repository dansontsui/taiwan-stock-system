#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十年完整資料收集腳本 - 包含智能等待功能
"""

import sys
import os
import time
import subprocess
from datetime import datetime, timedelta
import argparse

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from loguru import logger

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'collect_all_10years.log'),
        rotation="100 MB",
        retention="30 days",
        level="INFO"
    )

def calculate_date_range():
    """計算日期範圍 (固定起始日期)"""
    end_date = datetime.now().date()
    start_date = "2010-01-01"  # 固定起始日期，避免資料遺失

    return start_date, end_date.isoformat()

def run_script_with_retry(script_name, args, max_retries=3):
    """執行腳本並處理重試"""
    print(f"\n 執行 {script_name}...")
    print("=" * 60)
    
    for attempt in range(max_retries):
        try:
            cmd = ["python", f"scripts/{script_name}"] + args
            print(f"執行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=".",
                capture_output=True,
                text=True,
                timeout=7200  # 2小時超時
            )
            
            if result.returncode == 0:
                print(f" {script_name} 執行成功")
                logger.info(f"{script_name} 執行成功")
                return True
            else:
                error_output = result.stderr
                print(f" {script_name} 執行失敗 (第 {attempt + 1} 次)")
                print(f"錯誤輸出: {error_output}")
                logger.error(f"{script_name} 執行失敗: {error_output}")
                
                # 檢查是否為API限制錯誤
                if "402" in error_output or "Payment Required" in error_output:
                    if attempt < max_retries - 1:
                        print(" 檢測到API限制，等待70分鐘後重試...")
                        wait_for_api_reset()
                        continue
                
                if attempt < max_retries - 1:
                    print(f" 等待30秒後重試...")
                    time.sleep(30)
                    continue
                else:
                    print(f" {script_name} 達到最大重試次數，跳過")
                    return False
                    
        except subprocess.TimeoutExpired:
            print(f" {script_name} 執行超時 (第 {attempt + 1} 次)")
            if attempt < max_retries - 1:
                print("等待60秒後重試...")
                time.sleep(60)
                continue
            else:
                print(f" {script_name} 超時，跳過")
                return False
                
        except Exception as e:
            print(f" {script_name} 執行異常: {e}")
            logger.error(f"{script_name} 執行異常: {e}")
            if attempt < max_retries - 1:
                print("等待30秒後重試...")
                time.sleep(30)
                continue
            else:
                return False
    
    return False

def wait_for_api_reset():
    """等待API限制重置 - 70分鐘"""
    wait_minutes = 70
    print(f"\n API請求限制已達上限，智能等待 {wait_minutes} 分鐘...")
    print("=" * 60)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=wait_minutes)
    
    print(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"預計結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for remaining in range(wait_minutes * 60, 0, -60):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        current_time = datetime.now().strftime("%H:%M:%S")
        progress = ((wait_minutes * 60 - remaining) / (wait_minutes * 60)) * 100
        
        print(f"\r [{current_time}] 剩餘: {hours:02d}:{minutes:02d}:00 | 進度: {progress:.1f}%", end="", flush=True)
        time.sleep(60)
    
    print(f"\n [{datetime.now().strftime('%H:%M:%S')}] 等待完成，繼續收集資料...")
    print("=" * 60)

def show_progress_summary(completed_tasks, total_tasks):
    """顯示進度摘要"""
    print(f"\n 進度摘要: {completed_tasks}/{total_tasks} 項任務完成")
    progress_percent = (completed_tasks / total_tasks) * 100
    progress_bar = "█" * int(progress_percent // 5) + "░" * (20 - int(progress_percent // 5))
    print(f"進度條: [{progress_bar}] {progress_percent:.1f}%")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集十年完整台股資料')
    parser.add_argument('--skip-stock-prices', action='store_true', help='跳過股價資料收集')
    parser.add_argument('--batch-size', type=int, default=5, help='批次大小')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(" 台股十年完整資料收集系統")
    print("=" * 60)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 計算日期範圍
    start_date, end_date = calculate_date_range()
    print(f" 收集期間: {start_date} ~ {end_date} (十年)")
    print(f" 批次大小: {args.batch_size}")
    print("  注意: 遇到402錯誤將自動等待70分鐘")
    print("=" * 60)
    
    # 初始化日誌
    init_logging()
    logger.info("開始十年完整資料收集")
    
    # 檢查已完成的任務
    def check_completion_rate(table_name, expected_count):
        try:
            db_manager = DatabaseManager(Config.DATABASE_PATH)
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            current_count = cursor.fetchone()[0]
            conn.close()
            completion_rate = (current_count / expected_count) * 100 if expected_count > 0 else 0
            return current_count, completion_rate
        except:
            return 0, 0

    # 定義收集任務
    tasks = []

    # 1. 股價資料 (使用智能收集腳本)
    if not args.skip_stock_prices:
        stock_count, stock_completion = check_completion_rate('stock_prices', 500000)
        if stock_completion < 80:
            tasks.append({
                'name': '股價資料收集',
                'script': 'collect_stock_prices_smart.py',
                'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(args.batch_size), '--skip-threshold', '90']
            })
        else:
            print(f" 股價資料已完成 {stock_completion:.1f}% ({stock_count:,} 筆)，跳過收集")
    
    # 2. 月營收資料
    revenue_count, revenue_completion = check_completion_rate('monthly_revenues', 50000)
    if revenue_completion < 95:
        tasks.append({
            'name': '月營收資料收集',
            'script': 'collect_monthly_revenue.py',
            'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(args.batch_size)]
        })
    else:
        print(f" 月營收資料已完成 {revenue_completion:.1f}% ({revenue_count:,} 筆)，跳過收集")

    # 3. 綜合損益表
    financial_count, financial_completion = check_completion_rate('financial_statements', 20000)
    if financial_completion < 95:
        tasks.append({
            'name': '綜合損益表收集',
            'script': 'collect_financial_statements.py',
            'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(max(args.batch_size-2, 3))]
        })
    else:
        print(f" 綜合損益表已完成 {financial_completion:.1f}% ({financial_count:,} 筆)，跳過收集")

    # 4. 資產負債表
    balance_count, balance_completion = check_completion_rate('balance_sheets', 20000)
    if balance_completion < 95:
        tasks.append({
            'name': '資產負債表收集',
            'script': 'collect_balance_sheets.py',
            'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(max(args.batch_size-2, 3))]
        })
    else:
        print(f" 資產負債表已完成 {balance_completion:.1f}% ({balance_count:,} 筆)，跳過收集")

    # 5. 股利政策
    dividend_count, dividend_completion = check_completion_rate('dividend_policies', 5000)
    if dividend_completion < 95:
        tasks.append({
            'name': '股利政策收集',
            'script': 'collect_dividend_data.py',
            'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(max(args.batch_size-2, 3))]
        })
    else:
        print(f" 股利政策已完成 {dividend_completion:.1f}% ({dividend_count:,} 筆)，跳過收集")

    # 6. 現金流量表 (NEW!)
    cash_flow_count, cash_flow_completion = check_completion_rate('cash_flow_statements', 15000)
    if cash_flow_completion < 95:
        tasks.append({
            'name': '現金流量表收集',
            'script': 'collect_cash_flows.py',
            'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(max(args.batch_size-2, 3))]
        })
    else:
        print(f"✅ 現金流量表已完成 {cash_flow_completion:.1f}% ({cash_flow_count:,} 筆)，跳過收集")

    # 7. 除權除息結果表 (NEW!)
    dividend_result_count, dividend_result_completion = check_completion_rate('dividend_results', 3000)
    if dividend_result_completion < 95:
        tasks.append({
            'name': '除權除息結果收集',
            'script': 'collect_dividend_results.py',
            'args': ['--start-date', start_date, '--end-date', end_date, '--batch-size', str(max(args.batch_size-2, 3))]
        })
    else:
        print(f"✅ 除權除息結果已完成 {dividend_result_completion:.1f}% ({dividend_result_count:,} 筆)，跳過收集")

    # 8. 營收成長率計算
    tasks.append({
        'name': '營收成長率計算',
        'script': 'calculate_revenue_growth.py',
        'args': []
    })

    # 9. 潛力股分析
    tasks.append({
        'name': '潛力股分析',
        'script': 'analyze_potential_stocks.py',
        'args': ['--top', '50']
    })
    
    total_tasks = len(tasks)
    completed_tasks = 0
    failed_tasks = []
    
    print(f" 總共 {total_tasks} 項收集任務")
    print()
    
    # 執行所有任務
    for i, task in enumerate(tasks, 1):
        print(f"\n 任務 {i}/{total_tasks}: {task['name']}")
        
        success = run_script_with_retry(task['script'], task['args'])
        
        if success:
            completed_tasks += 1
            print(f" {task['name']} 完成")
        else:
            failed_tasks.append(task['name'])
            print(f" {task['name']} 失敗")
        
        # 顯示進度
        show_progress_summary(completed_tasks, total_tasks)
        
        # 任務間休息
        if i < total_tasks:
            print(f"\n  任務間休息30秒...")
            time.sleep(30)
    
    # 最終結果
    print("\n" + "=" * 60)
    print(" 十年資料收集完成")
    print("=" * 60)
    print(f" 結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" 成功任務: {completed_tasks}/{total_tasks}")
    print(f" 失敗任務: {len(failed_tasks)}")
    
    if failed_tasks:
        print(f"\n失敗任務清單:")
        for task in failed_tasks:
            print(f"  • {task}")
    
    # 顯示資料庫統計
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        print(f"\n 最終資料統計:")
        
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
        
        for table, name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {name:<15}: {count:>10,} 筆")
            except:
                print(f"  {name:<15}: {'錯誤':>10}")
        
        conn.close()
        
    except Exception as e:
        print(f"無法顯示資料統計: {e}")
    
    if completed_tasks == total_tasks:
        print(f"\n 恭喜！十年完整資料收集成功完成！")
        print(f"🌐 您可以在 http://localhost:8501 查看分析結果")
    else:
        print(f"\n  部分任務失敗，建議檢查失敗的任務並重新執行")
    
    print("=" * 60)
    logger.info(f"十年資料收集完成，成功 {completed_tasks}/{total_tasks} 項任務")

if __name__ == "__main__":
    main()
