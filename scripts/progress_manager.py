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

        # 備份控制
        self.last_backup_time = None
        self.backup_interval_minutes = 30  # 30分鐘備份一次
        self.max_backups = 10  # 最多保留10個備份檔案
    
    def _generate_task_id(self, task_type: TaskType, parameters: Dict[str, Any] = None) -> str:
        """生成任務ID（簡化版，避免過長的ID）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 簡化參數處理，只包含關鍵參數
        if parameters:
            key_params = []
            if parameters.get('stock_id'):
                key_params.append(f"stock_{parameters['stock_id']}")
            if parameters.get('test_mode'):
                key_params.append("test")

            if key_params:
                param_str = "_".join(key_params)
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
        try:
            self._save_task_progress(task_progress)
            print(f"✅ 創建任務: {task_id}")
            print(f"   任務類型: {task_type.value}")
            print(f"   股票數量: {len(stock_list)}")
        except Exception as e:
            print(f"⚠️ 任務儲存失敗: {e}")
            print("📝 任務將在記憶體中繼續，但不會持久化")

        return task_id
    
    def load_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """載入任務進度"""
        try:
            if not self.progress_file.exists():
                return None

            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except KeyboardInterrupt:
            print("\n⚠️ 使用者中斷載入進度")
            raise  # 重新拋出中斷信號
            
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
                try:
                    with open(self.progress_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ 進度檔案損壞: {e}")
                    print("🔧 嘗試從備份恢復...")

                    # 嘗試從最新的備份恢復
                    backup_restored = self._restore_from_backup()
                    if backup_restored:
                        try:
                            with open(self.progress_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            print("✅ 從備份成功恢復進度檔案")
                        except:
                            print("❌ 備份檔案也損壞，使用空白進度")
                            data = {'tasks': {}, 'last_updated': datetime.now().isoformat()}
                    else:
                        print("❌ 無法從備份恢復，使用空白進度")
                        data = {'tasks': {}, 'last_updated': datetime.now().isoformat()}
            
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
            
            # 智能備份：只在需要時備份
            if self.progress_file.exists() and self._should_backup():
                self._create_backup()

            # 使用原子寫入避免檔案損壞
            temp_file = self.progress_file.with_suffix('.tmp')
            try:
                # 先寫入臨時檔案
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                # 驗證寫入的檔案是否有效
                with open(temp_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # 驗證JSON格式

                # 如果驗證成功，原子性地替換原檔案
                if os.name == 'nt':  # Windows
                    if self.progress_file.exists():
                        self.progress_file.unlink()
                    temp_file.rename(self.progress_file)
                else:  # Unix/Linux/macOS
                    temp_file.rename(self.progress_file)

            except Exception as e:
                # 如果寫入失敗，清理臨時檔案
                if temp_file.exists():
                    temp_file.unlink()
                raise e
                
        except Exception as e:
            print(f"❌ 儲存任務進度失敗: {e}")
            raise

    def _should_backup(self):
        """判斷是否需要備份"""
        if self.last_backup_time is None:
            return True

        # 檢查是否超過備份間隔
        elapsed_minutes = (datetime.now() - self.last_backup_time).total_seconds() / 60
        return elapsed_minutes >= self.backup_interval_minutes

    def _create_backup(self):
        """創建備份檔案"""
        try:
            backup_file = self.backup_dir / f"progress_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # 使用copy而不是rename，避免Windows檔案鎖定問題
            import shutil
            shutil.copy2(self.progress_file, backup_file)

            # 更新最後備份時間
            self.last_backup_time = datetime.now()

            # 清理舊備份檔案
            self._cleanup_old_backups()

            print(f"📁 創建備份: {backup_file.name}")

        except Exception as e:
            print(f"⚠️ 備份失敗: {e}")

    def _cleanup_old_backups(self):
        """清理舊的備份檔案"""
        try:
            # 獲取所有備份檔案，按時間排序
            backup_files = list(self.backup_dir.glob("progress_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 刪除超過限制的舊備份
            if len(backup_files) > self.max_backups:
                for old_backup in backup_files[self.max_backups:]:
                    old_backup.unlink()
                    print(f"🗑️ 清理舊備份: {old_backup.name}")

        except Exception as e:
            print(f"⚠️ 清理備份失敗: {e}")

    def _restore_from_backup(self):
        """從備份恢復進度檔案"""
        try:
            # 獲取所有備份檔案，按時間排序（最新的在前）
            backup_files = list(self.backup_dir.glob("progress_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            if not backup_files:
                print("❌ 沒有找到備份檔案")
                return False

            # 嘗試從最新的備份恢復
            for backup_file in backup_files:
                try:
                    print(f"🔄 嘗試從備份恢復: {backup_file.name}")

                    # 驗證備份檔案是否有效
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        json.load(f)  # 驗證JSON格式

                    # 如果驗證成功，複製到主檔案
                    import shutil
                    shutil.copy2(backup_file, self.progress_file)
                    print(f"✅ 成功從備份恢復: {backup_file.name}")
                    return True

                except json.JSONDecodeError:
                    print(f"⚠️ 備份檔案也損壞: {backup_file.name}")
                    continue
                except Exception as e:
                    print(f"⚠️ 恢復備份失敗: {backup_file.name}, 錯誤: {e}")
                    continue

            print("❌ 所有備份檔案都無法使用")
            return False

        except Exception as e:
            print(f"❌ 備份恢復過程失敗: {e}")
            return False

    def _find_task_by_fuzzy_match(self, target_task_id: str, stock_id: str = None) -> Optional[TaskProgress]:
        """通過模糊匹配查找任務"""
        try:
            if not self.progress_file.exists():
                return None

            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 嘗試不同的匹配策略
            for task_id, task_data in data.get('tasks', {}).items():
                # 策略1：檢查是否包含相同的股票ID
                if stock_id and stock_id in task_data.get('stock_progress', {}):
                    # 檢查任務類型是否匹配
                    if target_task_id.startswith(task_data.get('task_type', '')):
                        print(f"✅ 通過股票ID匹配找到任務: {task_id}")
                        # 直接構造 TaskProgress 對象返回
                        return TaskProgress(
                            task_id=task_id,
                            task_type=TaskType(task_data.get('task_type', 'comprehensive')),
                            task_name=task_data.get('task_name', ''),
                            status=TaskStatus(task_data.get('status', 'not_started')),
                            total_stocks=task_data.get('total_stocks', 0),
                            completed_stocks=task_data.get('completed_stocks', 0),
                            failed_stocks=task_data.get('failed_stocks', 0),
                            skipped_stocks=task_data.get('skipped_stocks', 0),
                            start_time=task_data.get('start_time', ''),
                            last_updated=task_data.get('last_updated', ''),
                            parameters=task_data.get('parameters', {}),
                            stock_progress={
                                sid: StockProgress(
                                    stock_id=sid,
                                    stock_name=sdata.get('stock_name', ''),
                                    status=TaskStatus(sdata.get('status', 'not_started')),
                                    completed_datasets=sdata.get('completed_datasets', []),
                                    failed_datasets=sdata.get('failed_datasets', []),
                                    last_updated=sdata.get('last_updated', '')
                                ) for sid, sdata in task_data.get('stock_progress', {}).items()
                            }
                        )

                # 策略2：檢查任務ID的前綴是否匹配
                target_prefix = target_task_id.split('_')[0]  # 取任務類型部分
                task_prefix = task_id.split('_')[0]
                if target_prefix == task_prefix:
                    # 進一步檢查是否為最近的任務
                    task_time = task_data.get('created_at', '')
                    if task_time:  # 如果是最近創建的任務
                        print(f"✅ 通過類型匹配找到任務: {task_id}")
                        return self.load_task_progress(task_id)

            return None

        except Exception as e:
            print(f"⚠️ 模糊匹配失敗: {e}")
            return None
    
    def update_stock_progress(self,
                            task_id: str,
                            stock_id: str,
                            status: TaskStatus,
                            completed_datasets: List[str] = None,
                            failed_datasets: List[str] = None,
                            error_message: str = None):
        """更新股票進度"""
        try:
            task_progress = self.load_task_progress(task_id)
            if not task_progress:
                # 嘗試模糊匹配任務ID
                task_progress = self._find_task_by_fuzzy_match(task_id, stock_id)
                if not task_progress:
                    print(f"⚠️ 找不到任務: {task_id[:50]}...")
                    return
        except Exception as e:
            print(f"⚠️ 載入任務進度失敗: {e}")
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
