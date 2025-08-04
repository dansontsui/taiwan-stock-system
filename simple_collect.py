#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版資料收集腳本 - 避免編碼問題，支援斷點續傳
"""

import sys
import os
import time
import requests
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 導入進度管理器
try:
    from scripts.progress_manager import ProgressManager, TaskType, TaskStatus
    PROGRESS_ENABLED = True
except ImportError:
    print("[WARNING] 無法導入進度管理器，斷點續傳功能將被停用")
    PROGRESS_ENABLED = False

# 導入智能等待模組
try:
    from scripts.smart_wait import reset_execution_timer, smart_wait_for_api_reset, is_api_limit_error
except ImportError:
    # 如果無法導入，使用本地版本
    print("[WARNING] 無法導入智能等待模組，使用本地版本")

    # 全局變數追蹤執行時間
    execution_start_time = None

    def reset_execution_timer():
        global execution_start_time
        execution_start_time = datetime.now()
        print(f"[TIMER] 重置執行時間計時器: {execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def smart_wait_for_api_reset():
        global execution_start_time
        total_wait_minutes = 70
        executed_minutes = 0

        if execution_start_time:
            elapsed = datetime.now() - execution_start_time
            executed_minutes = elapsed.total_seconds() / 60

        remaining_wait_minutes = max(0, total_wait_minutes - executed_minutes)

        print(f"\n🚫 API請求限制已達上限")
        print("=" * 60)
        print(f"📊 執行統計:")
        print(f"   總執行時間: {executed_minutes:.1f} 分鐘")
        print(f"   API重置週期: {total_wait_minutes} 分鐘")
        print(f"   需要等待: {remaining_wait_minutes:.1f} 分鐘")
        print("=" * 60)

        if remaining_wait_minutes <= 0:
            print("✅ 已超過API重置週期，立即重置計時器並繼續")
            reset_execution_timer()
            return

        print(f"⏳ 智能等待 {remaining_wait_minutes:.1f} 分鐘...")
        total_wait_seconds = int(remaining_wait_minutes * 60)

        if total_wait_seconds > 0:
            for remaining in range(total_wait_seconds, 0, -60):
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                current_time = datetime.now().strftime("%H:%M:%S")
                progress = ((total_wait_seconds - remaining) / total_wait_seconds) * 100

                print(f"\r⏰ [{current_time}] 剩餘: {hours:02d}:{minutes:02d}:00 | 進度: {progress:.1f}%", end="", flush=True)
                time.sleep(60)

        print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] 智能等待完成，重置計時器並繼續收集...")
        print("=" * 60)
        reset_execution_timer()

    def is_api_limit_error(error_msg):
        api_limit_keywords = ["402", "Payment Required", "API請求限制", "rate limit", "quota exceeded"]
        return any(keyword.lower() in error_msg.lower() for keyword in api_limit_keywords)

# 配置
DATABASE_PATH = "data/taiwan_stock.db"
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wNy0yMyAyMDo1MzowNyIsInVzZXJfaWQiOiJkYW5zb24udHN1aSIsImlwIjoiMTIyLjExNi4xNzQuNyJ9.YkvySt5dqxDg_4NHsJzcmmH1trIQUBOy_wHJkR9Ibmk"

def get_stock_list(limit=None, stock_id=None):
    """獲取股票清單"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        if stock_id:
            # 指定個股
            query = """
            SELECT stock_id, stock_name
            FROM stocks
            WHERE stock_id = ?
            """
            cursor.execute(query, (stock_id,))
        else:
            # 所有股票
            query = """
            SELECT stock_id, stock_name
            FROM stocks
            WHERE LENGTH(stock_id) = 4
            AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
            AND stock_id NOT LIKE '00%'
            ORDER BY stock_id
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)

        stocks = cursor.fetchall()
        conn.close()

        return [{'stock_id': row[0], 'stock_name': row[1]} for row in stocks]

    except Exception as e:
        print(f"獲取股票清單失敗: {e}")
        return []

def collect_stock_data(stock_id, dataset, start_date, end_date, retry_count=0):
    """收集單一股票的資料 - 支援智能等待"""
    max_retries = 3

    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": dataset,
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": API_TOKEN
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return pd.DataFrame(data['data'])
            return None

        elif response.status_code == 402:
            # API請求限制，使用智能等待
            error_msg = f"402 Payment Required for {dataset} {stock_id}"
            print(f"收集 {stock_id} {dataset} 遇到API限制: {error_msg}")

            if is_api_limit_error(error_msg):
                smart_wait_for_api_reset()

                # 重試
                if retry_count < max_retries:
                    print(f"重試收集 {stock_id} {dataset} (第 {retry_count + 1} 次)")
                    return collect_stock_data(stock_id, dataset, start_date, end_date, retry_count + 1)
                else:
                    print(f"收集 {stock_id} {dataset} 達到最大重試次數")
                    return None
            else:
                print(f"收集 {stock_id} {dataset} 失敗: HTTP {response.status_code}")
                return None

        else:
            print(f"收集 {stock_id} {dataset} 失敗: HTTP {response.status_code}")
            return None

    except Exception as e:
        error_msg = str(e)
        print(f"收集 {stock_id} {dataset} 失敗: {e}")

        # 檢查是否為API限制相關錯誤
        if is_api_limit_error(error_msg) and retry_count < max_retries:
            smart_wait_for_api_reset()
            print(f"重試收集 {stock_id} {dataset} (第 {retry_count + 1} 次)")
            return collect_stock_data(stock_id, dataset, start_date, end_date, retry_count + 1)

        return None

def save_stock_prices(df, stock_id):
    """儲存股價資料"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO stock_prices 
                    (stock_id, date, open_price, high_price, low_price, close_price, 
                     volume, trading_money, trading_turnover, spread, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row['open'],
                    row['max'],
                    row['min'],
                    row['close'],
                    row['Trading_Volume'],
                    row['Trading_money'],
                    row['Trading_turnover'],
                    row['spread'],
                    datetime.now().isoformat()
                ))
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存股價失敗: {e}")
        return 0

def save_monthly_revenue(df, stock_id):
    """儲存月營收資料"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO monthly_revenues 
                    (stock_id, date, country, revenue, revenue_month, revenue_year, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row.get('country', 'Taiwan'),
                    row['revenue'],
                    row['revenue_month'],
                    row['revenue_year'],
                    datetime.now().isoformat()
                ))
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存月營收失敗: {e}")
        return 0

def save_cash_flow(df, stock_id):
    """儲存現金流資料"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO cash_flow_statements 
                    (stock_id, date, type, value, origin_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row['type'],
                    row['value'],
                    row.get('origin_name', ''),
                    datetime.now().isoformat()
                ))
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存現金流失敗: {e}")
        return 0

def collect_all_data(test_mode=False, stock_id=None, start_date=None, end_date=None, resume_task_id=None):
    """收集所有資料 - 支援斷點續傳"""

    print("=" * 60)
    if stock_id:
        print(f"簡化版資料收集 - 個股 {stock_id}")
    elif resume_task_id:
        print(f"簡化版資料收集 - 續傳任務 {resume_task_id}")
    else:
        print("簡化版資料收集")
    print("=" * 60)

    # 初始化進度管理器
    progress_manager = None
    task_id = None

    if PROGRESS_ENABLED:
        progress_manager = ProgressManager()

        # 如果指定續傳任務ID，載入現有任務
        if resume_task_id:
            task_progress = progress_manager.load_task_progress(resume_task_id)
            if task_progress:
                task_id = resume_task_id
                print(f"✅ 載入續傳任務: {task_progress.task_name}")
                print(f"   進度: {task_progress.completed_stocks}/{task_progress.total_stocks}")
            else:
                print(f"❌ 找不到任務: {resume_task_id}")
                return

    # 重置執行時間計時器
    reset_execution_timer()

    # 獲取股票清單
    if resume_task_id and task_id:
        # 續傳模式：只處理待處理的股票
        stocks = progress_manager.get_pending_stocks(task_id)
        print(f"續傳模式：找到 {len(stocks)} 檔待處理股票")
    elif stock_id:
        stocks = get_stock_list(stock_id=stock_id)
    else:
        limit = 3 if test_mode else None
        stocks = get_stock_list(limit)

    if not stocks:
        if stock_id:
            print(f"找不到股票代碼: {stock_id}")
        elif resume_task_id:
            print("沒有待處理的股票，任務可能已完成")
        else:
            print("沒有找到股票")
        return

    if not resume_task_id:
        print(f"找到 {len(stocks)} 檔股票")
        if stock_id:
            print(f"個股模式：收集 {stock_id}")
        elif test_mode:
            print("測試模式：只收集前3檔")
    
    # 資料集定義
    datasets = {
        "TaiwanStockPrice": ("股價", save_stock_prices),
        "TaiwanStockMonthRevenue": ("月營收", save_monthly_revenue),
        "TaiwanStockCashFlowsStatement": ("現金流", save_cash_flow)
    }

    # 設定日期範圍
    if start_date is None:
        from datetime import datetime
        start_date = "2010-01-01"  # 固定起始日期，避免資料遺失

    if end_date is None:
        from datetime import datetime
        end_date = datetime.now().date().isoformat()

    print(f"資料收集日期範圍: {start_date} ~ {end_date}")

    # 創建新任務（如果不是續傳模式）
    if PROGRESS_ENABLED and not resume_task_id:
        from datetime import datetime
        task_name = f"簡化版資料收集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if stock_id:
            task_name = f"個股收集_{stock_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        elif test_mode:
            task_name = f"測試收集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        parameters = {
            'start_date': start_date,
            'end_date': end_date,
            'test_mode': test_mode,
            'stock_id': stock_id
        }

        task_id = progress_manager.create_task(
            task_type=TaskType.COMPREHENSIVE,
            task_name=task_name,
            stock_list=stocks,
            parameters=parameters
        )
        print(f"📝 創建任務: {task_id}")

    total_stats = {}
    
    for dataset, (name, save_func) in datasets.items():
        print(f"\n收集 {name} 資料...")
        print("-" * 40)

        dataset_stats = {"success": 0, "failed": 0, "saved": 0}

        for i, stock in enumerate(stocks, 1):
            stock_id_val = stock['stock_id']
            stock_name = stock['stock_name']

            print(f"[{i}/{len(stocks)}] {stock_id_val} ({stock_name})")

            try:
                # 收集資料
                df = collect_stock_data(stock_id_val, dataset, start_date, end_date)

                if df is not None and not df.empty:
                    # 儲存資料
                    saved_count = save_func(df, stock_id_val)
                    dataset_stats["success"] += 1
                    dataset_stats["saved"] += saved_count
                    print(f"  成功: {len(df)} 筆資料，儲存 {saved_count} 筆")

                    # 更新進度：成功收集資料集
                    if PROGRESS_ENABLED and task_id:
                        progress_manager.update_stock_progress(
                            task_id, stock_id_val, TaskStatus.IN_PROGRESS,
                            completed_datasets=[dataset]
                        )
                else:
                    dataset_stats["failed"] += 1
                    print(f"  無資料")

                    # 更新進度：資料集失敗
                    if PROGRESS_ENABLED and task_id:
                        progress_manager.update_stock_progress(
                            task_id, stock_id_val, TaskStatus.IN_PROGRESS,
                            failed_datasets=[dataset],
                            error_message="無資料"
                        )

                # 控制請求頻率
                time.sleep(0.5)

            except Exception as e:
                dataset_stats["failed"] += 1
                error_msg = str(e)
                print(f"  失敗: {error_msg}")

                # 更新進度：資料集失敗
                if PROGRESS_ENABLED and task_id:
                    progress_manager.update_stock_progress(
                        task_id, stock_id_val, TaskStatus.IN_PROGRESS,
                        failed_datasets=[dataset],
                        error_message=error_msg
                    )

                time.sleep(1)

        total_stats[name] = dataset_stats
        print(f"{name} 完成: 成功 {dataset_stats['success']}, 失敗 {dataset_stats['failed']}, 儲存 {dataset_stats['saved']} 筆")

    # 更新每檔股票的最終狀態
    if PROGRESS_ENABLED and task_id:
        print(f"\n📝 更新股票完成狀態...")
        for stock in stocks:
            stock_id_val = stock['stock_id']

            # 檢查這檔股票的所有資料集收集情況
            task_progress = progress_manager.load_task_progress(task_id)
            if task_progress and stock_id_val in task_progress.stock_progress:
                stock_progress = task_progress.stock_progress[stock_id_val]

                # 判斷股票完成狀態
                total_datasets = len(datasets)
                completed_datasets = len(stock_progress.completed_datasets)
                failed_datasets = len(stock_progress.failed_datasets)

                if completed_datasets == total_datasets:
                    # 所有資料集都成功
                    final_status = TaskStatus.COMPLETED
                elif completed_datasets > 0:
                    # 部分成功
                    final_status = TaskStatus.COMPLETED  # 視為完成，但有部分失敗
                else:
                    # 全部失敗
                    final_status = TaskStatus.FAILED

                progress_manager.update_stock_progress(
                    task_id, stock_id_val, final_status
                )

        print(f"✅ 任務進度已更新: {task_id}")

    # 總結
    print("\n" + "=" * 60)
    print("收集完成")
    print("=" * 60)

    for name, stats in total_stats.items():
        print(f"{name}: 成功 {stats['success']}, 失敗 {stats['failed']}, 儲存 {stats['saved']} 筆")

    # 顯示進度資訊
    if PROGRESS_ENABLED and task_id:
        task_progress = progress_manager.load_task_progress(task_id)
        if task_progress:
            print(f"\n📊 任務進度統計:")
            print(f"   任務ID: {task_id}")
            print(f"   完成股票: {task_progress.completed_stocks}/{task_progress.total_stocks}")
            print(f"   失敗股票: {task_progress.failed_stocks}")

            if task_progress.failed_stocks > 0:
                print(f"\n💡 提示: 可使用以下指令續傳失敗的股票:")
                print(f"   python simple_collect.py --resume-task {task_id}")

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='簡化版資料收集 - 支援斷點續傳')
    parser.add_argument('--test', action='store_true', help='測試模式')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--resume-task', help='續傳任務ID')
    parser.add_argument('--list-tasks', action='store_true', help='列出所有任務')

    args = parser.parse_args()

    # 列出任務
    if args.list_tasks:
        if PROGRESS_ENABLED:
            progress_manager = ProgressManager()
            tasks = progress_manager.list_tasks()

            if not tasks:
                print("📝 目前沒有任何任務記錄")
                return

            print("\n📋 任務清單:")
            print("-" * 80)
            for i, task in enumerate(tasks, 1):
                status_emoji = {
                    'not_started': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(task['status'], '❓')

                progress_pct = (task['completed_stocks'] / task['total_stocks'] * 100) if task['total_stocks'] > 0 else 0

                print(f"{i}. {status_emoji} {task['task_name']}")
                print(f"   ID: {task['task_id']}")
                print(f"   進度: {task['completed_stocks']}/{task['total_stocks']} ({progress_pct:.1f}%)")
                print(f"   時間: {task['start_time'][:19]}")
                print()
        else:
            print("❌ 進度管理功能未啟用")
        return

    collect_all_data(
        test_mode=args.test,
        stock_id=args.stock_id,
        start_date=args.start_date,
        end_date=args.end_date,
        resume_task_id=args.resume_task
    )

if __name__ == "__main__":
    main()
