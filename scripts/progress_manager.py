#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料收集進度管理器 - 支援斷點續傳功能
提供進度記錄、載入、更新、重置等功能
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum

class TaskType(Enum):
    """任務類型枚舉"""
    STOCK_PRICES = "stock_prices"
    MONTHLY_REVENUE = "monthly_revenue"
    FINANCIAL_STATEMENTS = "financial_statements"
    BALANCE_SHEETS = "balance_sheets"
    CASH_FLOWS = "cash_flows"
    DIVIDEND_RESULTS = "dividend_results"
    DIVIDEND_POLICIES = "dividend_policies"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"

class TaskStatus(Enum):
    """任務狀態枚舉"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StockProgress:
    """單一股票的進度記錄"""
    stock_id: str
    stock_name: str
    status: TaskStatus
    completed_datasets: List[str]  # 已完成的資料集
    failed_datasets: List[str]     # 失敗的資料集
    last_updated: str
    retry_count: int = 0
    error_message: Optional[str] = None

@dataclass
class TaskProgress:
    """任務進度記錄"""
    task_id: str
    task_type: TaskType
    task_name: str
    status: TaskStatus
    total_stocks: int
    completed_stocks: int
    failed_stocks: int
    skipped_stocks: int
    start_time: str
    last_updated: str
    end_time: Optional[str] = None
    parameters: Dict[str, Any] = None  # 任務參數（日期範圍、批次大小等）
    stock_progress: Dict[str, StockProgress] = None  # 股票進度詳情

    def __post_init__(self):
        if self.stock_progress is None:
            self.stock_progress = {}
        if self.parameters is None:
            self.parameters = {}

class ProgressManager:
    """進度管理器"""
    
    def __init__(self, progress_dir: str = "data/progress"):
        """
        初始化進度管理器
        
        Args:
            progress_dir: 進度檔案儲存目錄
        """
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        
        # 進度檔案路徑
        self.progress_file = self.progress_dir / "collection_progress.json"
        self.backup_dir = self.progress_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def _generate_task_id(self, task_type: TaskType, parameters: Dict[str, Any] = None) -> str:
        """生成任務ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if parameters:
            param_str = "_".join([f"{k}_{v}" for k, v in sorted(parameters.items()) if v])
            return f"{task_type.value}_{param_str}_{timestamp}"
        return f"{task_type.value}_{timestamp}"
    
    def create_task(self, 
                   task_type: TaskType, 
                   task_name: str,
                   stock_list: List[Dict[str, str]],
                   parameters: Dict[str, Any] = None) -> str:
        """
        創建新任務
        
        Args:
            task_type: 任務類型
            task_name: 任務名稱
            stock_list: 股票清單 [{'stock_id': '2330', 'stock_name': '台積電'}, ...]
            parameters: 任務參數
            
        Returns:
            任務ID
        """
        task_id = self._generate_task_id(task_type, parameters)
        
        # 創建任務進度記錄
        task_progress = TaskProgress(
            task_id=task_id,
            task_type=task_type,
            task_name=task_name,
            status=TaskStatus.NOT_STARTED,
            total_stocks=len(stock_list),
            completed_stocks=0,
            failed_stocks=0,
            skipped_stocks=0,
            start_time=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            parameters=parameters or {}
        )
        
        # 初始化股票進度
        for stock in stock_list:
            stock_progress = StockProgress(
                stock_id=stock['stock_id'],
                stock_name=stock['stock_name'],
                status=TaskStatus.NOT_STARTED,
                completed_datasets=[],
                failed_datasets=[],
                last_updated=datetime.now().isoformat()
            )
            task_progress.stock_progress[stock['stock_id']] = stock_progress
        
        # 儲存進度
        self._save_task_progress(task_progress)
        
        print(f"✅ 創建任務: {task_id}")
        print(f"   任務類型: {task_type.value}")
        print(f"   股票數量: {len(stock_list)}")
        
        return task_id
    
    def load_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """載入任務進度"""
        try:
            if not self.progress_file.exists():
                return None
            
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if task_id not in data.get('tasks', {}):
                return None
            
            task_data = data['tasks'][task_id]
            
            # 重建TaskProgress物件
            task_progress = TaskProgress(
                task_id=task_data['task_id'],
                task_type=TaskType(task_data['task_type']),
                task_name=task_data['task_name'],
                status=TaskStatus(task_data['status']),
                total_stocks=task_data['total_stocks'],
                completed_stocks=task_data['completed_stocks'],
                failed_stocks=task_data['failed_stocks'],
                skipped_stocks=task_data['skipped_stocks'],
                start_time=task_data['start_time'],
                last_updated=task_data['last_updated'],
                end_time=task_data.get('end_time'),
                parameters=task_data.get('parameters', {})
            )
            
            # 重建股票進度
            for stock_id, stock_data in task_data.get('stock_progress', {}).items():
                stock_progress = StockProgress(
                    stock_id=stock_data['stock_id'],
                    stock_name=stock_data['stock_name'],
                    status=TaskStatus(stock_data['status']),
                    completed_datasets=stock_data['completed_datasets'],
                    failed_datasets=stock_data['failed_datasets'],
                    last_updated=stock_data['last_updated'],
                    retry_count=stock_data.get('retry_count', 0),
                    error_message=stock_data.get('error_message')
                )
                task_progress.stock_progress[stock_id] = stock_progress
            
            return task_progress
            
        except Exception as e:
            print(f"❌ 載入任務進度失敗: {e}")
            return None
    
    def _save_task_progress(self, task_progress: TaskProgress):
        """儲存任務進度"""
        try:
            # 載入現有進度資料
            data = {'tasks': {}, 'last_updated': datetime.now().isoformat()}
            if self.progress_file.exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # 轉換為可序列化的格式
            task_data = asdict(task_progress)
            task_data['task_type'] = task_progress.task_type.value
            task_data['status'] = task_progress.status.value
            
            # 轉換股票進度
            for stock_id, stock_progress in task_data['stock_progress'].items():
                stock_progress['status'] = stock_progress['status'].value
            
            # 更新任務資料
            data['tasks'][task_progress.task_id] = task_data
            data['last_updated'] = datetime.now().isoformat()
            
            # 備份現有檔案
            if self.progress_file.exists():
                backup_file = self.backup_dir / f"progress_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                # 確保備份檔案不存在，避免Windows重命名錯誤
                counter = 1
                while backup_file.exists():
                    backup_file = self.backup_dir / f"progress_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{counter}.json"
                    counter += 1

                # 使用copy而不是rename，避免Windows檔案鎖定問題
                import shutil
                shutil.copy2(self.progress_file, backup_file)
            
            # 儲存新檔案
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 儲存任務進度失敗: {e}")
            raise
    
    def update_stock_progress(self, 
                            task_id: str, 
                            stock_id: str, 
                            status: TaskStatus,
                            completed_datasets: List[str] = None,
                            failed_datasets: List[str] = None,
                            error_message: str = None):
        """更新股票進度"""
        task_progress = self.load_task_progress(task_id)
        if not task_progress:
            print(f"❌ 找不到任務: {task_id}")
            return
        
        if stock_id not in task_progress.stock_progress:
            print(f"❌ 找不到股票: {stock_id}")
            return
        
        # 更新股票進度
        stock_progress = task_progress.stock_progress[stock_id]
        old_status = stock_progress.status
        stock_progress.status = status
        stock_progress.last_updated = datetime.now().isoformat()
        
        if completed_datasets:
            stock_progress.completed_datasets.extend(completed_datasets)
            stock_progress.completed_datasets = list(set(stock_progress.completed_datasets))
        
        if failed_datasets:
            stock_progress.failed_datasets.extend(failed_datasets)
            stock_progress.failed_datasets = list(set(stock_progress.failed_datasets))
        
        if error_message:
            stock_progress.error_message = error_message
            stock_progress.retry_count += 1
        
        # 更新任務統計
        if old_status != status:
            if old_status == TaskStatus.COMPLETED:
                task_progress.completed_stocks -= 1
            elif old_status == TaskStatus.FAILED:
                task_progress.failed_stocks -= 1
            elif old_status == TaskStatus.SKIPPED:
                task_progress.skipped_stocks -= 1
            
            if status == TaskStatus.COMPLETED:
                task_progress.completed_stocks += 1
            elif status == TaskStatus.FAILED:
                task_progress.failed_stocks += 1
            elif status == TaskStatus.SKIPPED:
                task_progress.skipped_stocks += 1
        
        # 更新任務狀態
        task_progress.last_updated = datetime.now().isoformat()
        if task_progress.completed_stocks + task_progress.failed_stocks + task_progress.skipped_stocks >= task_progress.total_stocks:
            task_progress.status = TaskStatus.COMPLETED
            task_progress.end_time = datetime.now().isoformat()
        elif task_progress.completed_stocks > 0 or task_progress.failed_stocks > 0:
            task_progress.status = TaskStatus.IN_PROGRESS
        
        # 儲存進度
        self._save_task_progress(task_progress)
    
    def get_pending_stocks(self, task_id: str) -> List[Dict[str, str]]:
        """獲取待處理的股票清單"""
        task_progress = self.load_task_progress(task_id)
        if not task_progress:
            return []

        pending_stocks = []
        for stock_id, stock_progress in task_progress.stock_progress.items():
            # 包含未開始、失敗、和進行中但未完成的股票
            if stock_progress.status in [TaskStatus.NOT_STARTED, TaskStatus.FAILED, TaskStatus.IN_PROGRESS]:
                pending_stocks.append({
                    'stock_id': stock_progress.stock_id,
                    'stock_name': stock_progress.stock_name
                })

        return pending_stocks
    
    def reset_task(self, task_id: str):
        """重置任務進度"""
        task_progress = self.load_task_progress(task_id)
        if not task_progress:
            print(f"❌ 找不到任務: {task_id}")
            return
        
        # 重置任務狀態
        task_progress.status = TaskStatus.NOT_STARTED
        task_progress.completed_stocks = 0
        task_progress.failed_stocks = 0
        task_progress.skipped_stocks = 0
        task_progress.start_time = datetime.now().isoformat()
        task_progress.last_updated = datetime.now().isoformat()
        task_progress.end_time = None
        
        # 重置所有股票進度
        for stock_progress in task_progress.stock_progress.values():
            stock_progress.status = TaskStatus.NOT_STARTED
            stock_progress.completed_datasets = []
            stock_progress.failed_datasets = []
            stock_progress.last_updated = datetime.now().isoformat()
            stock_progress.retry_count = 0
            stock_progress.error_message = None
        
        # 儲存進度
        self._save_task_progress(task_progress)
        print(f"✅ 任務 {task_id} 已重置")
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有任務"""
        try:
            if not self.progress_file.exists():
                return []
            
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tasks = []
            for task_id, task_data in data.get('tasks', {}).items():
                tasks.append({
                    'task_id': task_id,
                    'task_type': task_data['task_type'],
                    'task_name': task_data['task_name'],
                    'status': task_data['status'],
                    'total_stocks': task_data['total_stocks'],
                    'completed_stocks': task_data['completed_stocks'],
                    'failed_stocks': task_data['failed_stocks'],
                    'start_time': task_data['start_time'],
                    'last_updated': task_data['last_updated']
                })
            
            return sorted(tasks, key=lambda x: x['last_updated'], reverse=True)
            
        except Exception as e:
            print(f"❌ 列出任務失敗: {e}")
            return []
    
    def delete_task(self, task_id: str):
        """刪除任務"""
        try:
            if not self.progress_file.exists():
                print(f"❌ 找不到進度檔案")
                return
            
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if task_id in data.get('tasks', {}):
                del data['tasks'][task_id]
                data['last_updated'] = datetime.now().isoformat()
                
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 任務 {task_id} 已刪除")
            else:
                print(f"❌ 找不到任務: {task_id}")
                
        except Exception as e:
            print(f"❌ 刪除任務失敗: {e}")
