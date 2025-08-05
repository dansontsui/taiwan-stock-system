#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支援斷點續傳的批次資料收集腳本
整合進度管理功能，支援從中斷點繼續收集
"""

import sys
import os
import time
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 導入進度管理器
from scripts.progress_manager import ProgressManager, TaskType, TaskStatus

# 導入智能等待模組
try:
    from scripts.smart_wait import reset_execution_timer, smart_wait_for_api_reset, is_api_limit_error
except ImportError:
    print("[WARNING] 無法導入智能等待模組")
    def reset_execution_timer():
        pass
    def smart_wait_for_api_reset():
        time.sleep(60)
    def is_api_limit_error(error_msg):
        return "402" in error_msg

# 配置
DATABASE_PATH = "data/taiwan_stock.db"
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wNy0yMyAyMDo1MzowNyIsInVzZXJfaWQiOiJkYW5zb24udHN1aSIsImlwIjoiMTIyLjExNi4xNzQuNyJ9.YkvySt5dqxDg_4NHsJzcmmH1trIQUBOy_wHJkR9Ibmk"

def get_stock_list(limit=None):
    """獲取股票清單"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

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

def collect_stock_dataset(stock_id, dataset_name, dataset_config, start_date, end_date, progress_manager=None, task_id=None):
    """收集單一股票的特定資料集"""
    import requests
    import pandas as pd
    
    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": dataset_config['api_name'],
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": API_TOKEN
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                
                # 儲存資料
                saved_count = dataset_config['save_func'](df, stock_id)
                
                # 更新進度
                if progress_manager and task_id:
                    progress_manager.update_stock_progress(
                        task_id, stock_id, TaskStatus.IN_PROGRESS,
                        completed_datasets=[dataset_name]
                    )
                
                return {'success': True, 'count': saved_count, 'message': f'儲存 {saved_count} 筆'}
            else:
                # 更新進度：無資料
                if progress_manager and task_id:
                    progress_manager.update_stock_progress(
                        task_id, stock_id, TaskStatus.IN_PROGRESS,
                        failed_datasets=[dataset_name],
                        error_message="無資料"
                    )
                return {'success': False, 'count': 0, 'message': '無資料'}

        elif response.status_code == 402:
            # API請求限制
            error_msg = f"402 Payment Required for {dataset_name} {stock_id}"
            print(f"收集 {stock_id} {dataset_name} 遇到API限制")
            
            if is_api_limit_error(error_msg):
                smart_wait_for_api_reset()
                # 重試一次
                return collect_stock_dataset(stock_id, dataset_name, dataset_config, start_date, end_date, progress_manager, task_id)
            
            # 更新進度：API限制
            if progress_manager and task_id:
                progress_manager.update_stock_progress(
                    task_id, stock_id, TaskStatus.IN_PROGRESS,
                    failed_datasets=[dataset_name],
                    error_message=error_msg
                )
            return {'success': False, 'count': 0, 'message': error_msg}

        else:
            error_msg = f"HTTP {response.status_code}"
            # 更新進度：HTTP錯誤
            if progress_manager and task_id:
                progress_manager.update_stock_progress(
                    task_id, stock_id, TaskStatus.IN_PROGRESS,
                    failed_datasets=[dataset_name],
                    error_message=error_msg
                )
            return {'success': False, 'count': 0, 'message': error_msg}

    except Exception as e:
        error_msg = str(e)
        print(f"收集 {stock_id} {dataset_name} 失敗: {error_msg}")
        
        # 檢查是否為API限制相關錯誤
        if is_api_limit_error(error_msg):
            smart_wait_for_api_reset()
            # 重試一次
            return collect_stock_dataset(stock_id, dataset_name, dataset_config, start_date, end_date, progress_manager, task_id)
        
        # 更新進度：異常錯誤
        if progress_manager and task_id:
            progress_manager.update_stock_progress(
                task_id, stock_id, TaskStatus.IN_PROGRESS,
                failed_datasets=[dataset_name],
                error_message=error_msg
            )
        return {'success': False, 'count': 0, 'message': error_msg}

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
            except Exception:
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
            except Exception:
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
            except Exception:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存現金流失敗: {e}")
        return 0

def collect_batch_with_resume(task_type=TaskType.COMPREHENSIVE, test_mode=False, start_date=None, end_date=None, resume_task_id=None, batch_size=50):
    """批次收集資料 - 支援斷點續傳"""
    
    print("=" * 80)
    if resume_task_id:
        print(f"批次資料收集 - 續傳任務 {resume_task_id}")
    else:
        print("批次資料收集 - 支援斷點續傳")
    print("=" * 80)

    # 初始化進度管理器
    progress_manager = ProgressManager()
    task_id = None
    
    # 資料集配置
    datasets = {
        "stock_prices": {
            "name": "股價",
            "api_name": "TaiwanStockPrice",
            "save_func": save_stock_prices,
            "emoji": "📈"
        },
        "monthly_revenue": {
            "name": "月營收",
            "api_name": "TaiwanStockMonthRevenue", 
            "save_func": save_monthly_revenue,
            "emoji": "📊"
        },
        "cash_flows": {
            "name": "現金流",
            "api_name": "TaiwanStockCashFlowsStatement",
            "save_func": save_cash_flow,
            "emoji": "💰"
        }
    }
    
    # 設定日期範圍
    if start_date is None:
        start_date = "2010-01-01"  # 固定起始日期，避免資料遺失

    if end_date is None:
        end_date = datetime.now().date().isoformat()

    print(f"資料收集日期範圍: {start_date} ~ {end_date}")
    
    # 處理續傳或新任務
    if resume_task_id:
        # 載入現有任務
        task_progress = progress_manager.load_task_progress(resume_task_id)
        if task_progress:
            task_id = resume_task_id
            stocks = progress_manager.get_pending_stocks(task_id)
            print(f"✅ 載入續傳任務: {task_progress.task_name}")
            print(f"   進度: {task_progress.completed_stocks}/{task_progress.total_stocks}")
            print(f"   待處理: {len(stocks)} 檔股票")
        else:
            print(f"❌ 找不到任務: {resume_task_id}")
            return
    else:
        # 創建新任務
        limit = 3 if test_mode else None
        stocks = get_stock_list(limit)
        
        if not stocks:
            print("沒有找到股票")
            return
        
        task_name = f"批次收集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if test_mode:
            task_name = f"測試批次收集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        parameters = {
            'start_date': start_date,
            'end_date': end_date,
            'test_mode': test_mode,
            'batch_size': batch_size
        }
        
        task_id = progress_manager.create_task(
            task_type=task_type,
            task_name=task_name,
            stock_list=stocks,
            parameters=parameters
        )
        print(f"📝 創建任務: {task_id}")
        print(f"   股票數量: {len(stocks)}")

    if not stocks:
        print("沒有待處理的股票")
        return

    # 初始化執行時間計時器（如果尚未初始化）
    try:
        from scripts.smart_wait import get_smart_wait_manager
        manager = get_smart_wait_manager()
        if manager.execution_start_time is None:
            from datetime import datetime
            manager.execution_start_time = datetime.now()
            print(f"[TIMER] 初始化執行時間計時器: {manager.execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except ImportError:
        # 如果無法導入智能等待模組，使用本地初始化
        print("[WARNING] 無法導入智能等待模組，跳過計時器初始化")
    
    # 開始收集
    total_stats = {}
    
    for dataset_key, dataset_config in datasets.items():
        print(f"\n{dataset_config['emoji']} 收集 {dataset_config['name']} 資料...")
        print("-" * 60)
        
        dataset_stats = {"success": 0, "failed": 0, "saved": 0}
        
        for i, stock in enumerate(stocks, 1):
            stock_id = stock['stock_id']
            stock_name = stock['stock_name']
            
            print(f"[{i}/{len(stocks)}] {stock_id} ({stock_name})")
            
            # 收集資料
            result = collect_stock_dataset(
                stock_id, dataset_key, dataset_config, 
                start_date, end_date, progress_manager, task_id
            )
            
            if result['success']:
                dataset_stats["success"] += 1
                dataset_stats["saved"] += result['count']
                print(f"  ✅ {result['message']}")
            else:
                dataset_stats["failed"] += 1
                print(f"  ❌ {result['message']}")
            
            # 控制請求頻率
            time.sleep(0.5)
        
        total_stats[dataset_config['name']] = dataset_stats
        print(f"\n{dataset_config['name']} 完成: 成功 {dataset_stats['success']}, 失敗 {dataset_stats['failed']}, 儲存 {dataset_stats['saved']} 筆")
    
    # 更新股票最終狀態
    print(f"\n📝 更新股票完成狀態...")
    for stock in stocks:
        stock_id = stock['stock_id']
        
        # 檢查這檔股票的所有資料集收集情況
        task_progress = progress_manager.load_task_progress(task_id)
        if task_progress and stock_id in task_progress.stock_progress:
            stock_progress = task_progress.stock_progress[stock_id]
            
            # 判斷股票完成狀態
            total_datasets = len(datasets)
            completed_datasets = len(stock_progress.completed_datasets)
            
            if completed_datasets == total_datasets:
                final_status = TaskStatus.COMPLETED
            elif completed_datasets > 0:
                final_status = TaskStatus.COMPLETED  # 部分完成也視為完成
            else:
                final_status = TaskStatus.FAILED
            
            progress_manager.update_stock_progress(task_id, stock_id, final_status)
    
    # 總結
    print("\n" + "=" * 80)
    print("批次收集完成")
    print("=" * 80)
    
    for name, stats in total_stats.items():
        print(f"{name}: 成功 {stats['success']}, 失敗 {stats['failed']}, 儲存 {stats['saved']} 筆")
    
    # 顯示進度資訊
    task_progress = progress_manager.load_task_progress(task_id)
    if task_progress:
        print(f"\n📊 任務進度統計:")
        print(f"   任務ID: {task_id}")
        print(f"   完成股票: {task_progress.completed_stocks}/{task_progress.total_stocks}")
        print(f"   失敗股票: {task_progress.failed_stocks}")
        
        if task_progress.failed_stocks > 0:
            print(f"\n💡 提示: 可使用以下指令續傳失敗的股票:")
            print(f"   python scripts/collect_with_resume.py --resume-task {task_id}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='支援斷點續傳的批次資料收集')
    parser.add_argument('--test', action='store_true', help='測試模式')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--resume-task', help='續傳任務ID')
    parser.add_argument('--batch-size', type=int, default=50, help='批次大小')
    parser.add_argument('--list-tasks', action='store_true', help='列出所有任務')

    args = parser.parse_args()

    # 列出任務
    if args.list_tasks:
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
        return

    collect_batch_with_resume(
        test_mode=args.test,
        start_date=args.start_date,
        end_date=args.end_date,
        resume_task_id=args.resume_task,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    main()
