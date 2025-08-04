#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進度管理工具 - 查看、重置、清理收集任務進度
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.progress_manager import ProgressManager, TaskStatus, TaskType

def format_datetime(dt_str: str) -> str:
    """格式化日期時間顯示"""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str

def format_duration(start_time: str, end_time: str = None) -> str:
    """計算並格式化持續時間"""
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time) if end_time else datetime.now()
        duration = end - start
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        if duration.days > 0:
            return f"{duration.days}天 {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except:
        return "未知"

def list_tasks(progress_manager: ProgressManager):
    """列出所有任務"""
    print("\n" + "=" * 80)
    print("📋 資料收集任務清單")
    print("=" * 80)
    
    tasks = progress_manager.list_tasks()
    
    if not tasks:
        print("📝 目前沒有任何任務記錄")
        return
    
    for i, task in enumerate(tasks, 1):
        status_emoji = {
            'not_started': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(task['status'], '❓')
        
        progress_pct = (task['completed_stocks'] / task['total_stocks'] * 100) if task['total_stocks'] > 0 else 0
        
        print(f"\n{i}. {status_emoji} {task['task_name']}")
        print(f"   任務ID: {task['task_id']}")
        print(f"   類型: {task['task_type']}")
        print(f"   狀態: {task['status']}")
        print(f"   進度: {task['completed_stocks']}/{task['total_stocks']} ({progress_pct:.1f}%)")
        if task['failed_stocks'] > 0:
            print(f"   失敗: {task['failed_stocks']} 檔")
        print(f"   開始時間: {format_datetime(task['start_time'])}")
        print(f"   最後更新: {format_datetime(task['last_updated'])}")
        
        # 計算持續時間
        duration = format_duration(task['start_time'])
        print(f"   持續時間: {duration}")

def show_task_detail(progress_manager: ProgressManager, task_id: str):
    """顯示任務詳細資訊"""
    task_progress = progress_manager.load_task_progress(task_id)
    
    if not task_progress:
        print(f"❌ 找不到任務: {task_id}")
        return
    
    print("\n" + "=" * 80)
    print(f"📊 任務詳細資訊: {task_progress.task_name}")
    print("=" * 80)
    
    # 基本資訊
    print(f"任務ID: {task_progress.task_id}")
    print(f"任務類型: {task_progress.task_type.value}")
    print(f"任務狀態: {task_progress.status.value}")
    print(f"開始時間: {format_datetime(task_progress.start_time)}")
    print(f"最後更新: {format_datetime(task_progress.last_updated)}")
    if task_progress.end_time:
        print(f"結束時間: {format_datetime(task_progress.end_time)}")
    
    # 進度統計
    print(f"\n📈 進度統計:")
    print(f"   總股票數: {task_progress.total_stocks}")
    print(f"   已完成: {task_progress.completed_stocks}")
    print(f"   失敗: {task_progress.failed_stocks}")
    print(f"   跳過: {task_progress.skipped_stocks}")
    
    progress_pct = (task_progress.completed_stocks / task_progress.total_stocks * 100) if task_progress.total_stocks > 0 else 0
    print(f"   完成率: {progress_pct:.1f}%")
    
    # 任務參數
    if task_progress.parameters:
        print(f"\n⚙️ 任務參數:")
        for key, value in task_progress.parameters.items():
            print(f"   {key}: {value}")
    
    # 股票進度摘要
    print(f"\n📋 股票進度摘要:")
    status_counts = {}
    for stock_progress in task_progress.stock_progress.values():
        status = stock_progress.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        emoji = {
            'not_started': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'failed': '❌',
            'skipped': '⏭️'
        }.get(status, '❓')
        print(f"   {emoji} {status}: {count} 檔")
    
    # 失敗股票詳情
    failed_stocks = [sp for sp in task_progress.stock_progress.values() if sp.status == TaskStatus.FAILED]
    if failed_stocks:
        print(f"\n❌ 失敗股票詳情:")
        for stock in failed_stocks[:10]:  # 只顯示前10個
            print(f"   {stock.stock_id} ({stock.stock_name})")
            if stock.error_message:
                print(f"      錯誤: {stock.error_message}")
            print(f"      重試次數: {stock.retry_count}")
        
        if len(failed_stocks) > 10:
            print(f"   ... 還有 {len(failed_stocks) - 10} 檔失敗股票")

def reset_task(progress_manager: ProgressManager, task_id: str):
    """重置任務"""
    task_progress = progress_manager.load_task_progress(task_id)
    
    if not task_progress:
        print(f"❌ 找不到任務: {task_id}")
        return
    
    print(f"\n⚠️ 即將重置任務: {task_progress.task_name}")
    print(f"   任務ID: {task_id}")
    print(f"   這將清除所有進度記錄，重新開始收集")
    
    confirm = input("\n確定要重置嗎？(y/N): ").strip().lower()
    if confirm == 'y':
        progress_manager.reset_task(task_id)
        print("✅ 任務已重置")
    else:
        print("❌ 取消重置")

def delete_task(progress_manager: ProgressManager, task_id: str):
    """刪除任務"""
    task_progress = progress_manager.load_task_progress(task_id)
    
    if not task_progress:
        print(f"❌ 找不到任務: {task_id}")
        return
    
    print(f"\n⚠️ 即將刪除任務: {task_progress.task_name}")
    print(f"   任務ID: {task_id}")
    print(f"   這將永久刪除任務記錄，無法恢復")
    
    confirm = input("\n確定要刪除嗎？(y/N): ").strip().lower()
    if confirm == 'y':
        progress_manager.delete_task(task_id)
        print("✅ 任務已刪除")
    else:
        print("❌ 取消刪除")

def clean_completed_tasks(progress_manager: ProgressManager):
    """清理已完成的任務"""
    tasks = progress_manager.list_tasks()
    completed_tasks = [task for task in tasks if task['status'] == 'completed']
    
    if not completed_tasks:
        print("📝 沒有已完成的任務需要清理")
        return
    
    print(f"\n📋 找到 {len(completed_tasks)} 個已完成的任務:")
    for task in completed_tasks:
        print(f"   - {task['task_name']} ({task['task_id']})")
    
    confirm = input(f"\n確定要刪除這 {len(completed_tasks)} 個已完成的任務嗎？(y/N): ").strip().lower()
    if confirm == 'y':
        for task in completed_tasks:
            progress_manager.delete_task(task['task_id'])
        print(f"✅ 已清理 {len(completed_tasks)} 個已完成的任務")
    else:
        print("❌ 取消清理")

def show_pending_stocks(progress_manager: ProgressManager, task_id: str):
    """顯示待處理的股票"""
    pending_stocks = progress_manager.get_pending_stocks(task_id)
    
    if not pending_stocks:
        print(f"✅ 任務 {task_id} 沒有待處理的股票")
        return
    
    print(f"\n📋 任務 {task_id} 待處理股票 ({len(pending_stocks)} 檔):")
    print("-" * 40)
    
    for i, stock in enumerate(pending_stocks, 1):
        print(f"{i:3d}. {stock['stock_id']} - {stock['stock_name']}")
        
        if i >= 20:  # 只顯示前20個
            print(f"... 還有 {len(pending_stocks) - 20} 檔股票")
            break

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='進度管理工具')
    parser.add_argument('action', choices=['list', 'show', 'reset', 'delete', 'clean', 'pending'], 
                       help='操作類型')
    parser.add_argument('--task-id', help='任務ID')
    parser.add_argument('--progress-dir', default='data/progress', help='進度檔案目錄')
    
    args = parser.parse_args()
    
    # 初始化進度管理器
    progress_manager = ProgressManager(args.progress_dir)
    
    try:
        if args.action == 'list':
            list_tasks(progress_manager)
            
        elif args.action == 'show':
            if not args.task_id:
                print("❌ 請指定任務ID: --task-id <task_id>")
                return
            show_task_detail(progress_manager, args.task_id)
            
        elif args.action == 'reset':
            if not args.task_id:
                print("❌ 請指定任務ID: --task-id <task_id>")
                return
            reset_task(progress_manager, args.task_id)
            
        elif args.action == 'delete':
            if not args.task_id:
                print("❌ 請指定任務ID: --task-id <task_id>")
                return
            delete_task(progress_manager, args.task_id)
            
        elif args.action == 'clean':
            clean_completed_tasks(progress_manager)
            
        elif args.action == 'pending':
            if not args.task_id:
                print("❌ 請指定任務ID: --task-id <task_id>")
                return
            show_pending_stocks(progress_manager, args.task_id)
            
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷操作")
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")

if __name__ == "__main__":
    main()
