# -*- coding: utf-8 -*-
"""
日誌管理工具
用於批量調優時控制日誌大小與輸出
"""

import os
import sys
import logging
import gzip
from datetime import datetime
from pathlib import Path
from typing import Optional


def _safe_setup_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def _p(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.write(msg.encode("utf-8", "ignore").decode("utf-8", "ignore") + "\n")
        except Exception:
            pass


class BatchLogManager:
    """批量調優專用的日誌管理器"""
    
    def __init__(self, log_mode: str = "2", max_log_size_mb: int = 50):
        """
        初始化日誌管理器
        
        Args:
            log_mode: 日誌模式 ("1"=標準, "2"=簡化, "3"=靜默)
            max_log_size_mb: 日誌檔案大小上限（MB）
        """
        self.log_mode = log_mode
        self.max_log_size = max_log_size_mb * 1024 * 1024  # 轉換為 bytes
        self.original_log_level = None
        self.batch_log_file = None
        
        _safe_setup_stdout()
    
    def start_batch_logging(self, operation_name: str = "batch_tuning"):
        """開始批量操作的日誌記錄"""
        # 設定日誌級別
        if self.log_mode == '3':  # 靜默模式
            self.original_log_level = logging.getLogger().level
            logging.getLogger().setLevel(logging.ERROR)
            logging.getLogger('stock_price_investment_system').setLevel(logging.ERROR)
        elif self.log_mode == '2':  # 簡化模式
            self.original_log_level = logging.getLogger().level
            logging.getLogger().setLevel(logging.WARNING)
            logging.getLogger('stock_price_investment_system').setLevel(logging.WARNING)
        
        # 創建專用的批量日誌檔案
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = Path("stock_price_investment_system/logs")
        log_dir.mkdir(exist_ok=True)
        
        self.batch_log_file = log_dir / f"{operation_name}_{timestamp}.log"
        
        # 設定批量日誌處理器
        batch_handler = logging.FileHandler(self.batch_log_file, encoding='utf-8')
        batch_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        batch_handler.setFormatter(batch_formatter)
        
        # 只在簡化/靜默模式下使用專用日誌檔案
        if self.log_mode in ['2', '3']:
            # 移除現有的檔案處理器，只保留批量處理器
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    logger.removeHandler(handler)
            logger.addHandler(batch_handler)
        
        _p(f"📝 批量日誌模式: {['標準', '簡化', '靜默'][int(self.log_mode)-1]}")
        _p(f"📁 批量日誌檔案: {self.batch_log_file}")
    
    def stop_batch_logging(self):
        """結束批量操作的日誌記錄"""
        # 恢復原始日誌級別
        if self.original_log_level is not None:
            logging.getLogger().setLevel(self.original_log_level)
            logging.getLogger('stock_price_investment_system').setLevel(self.original_log_level)
        
        # 檢查日誌檔案大小
        if self.batch_log_file and self.batch_log_file.exists():
            file_size = self.batch_log_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            _p(f"📊 批量日誌檔案大小: {size_mb:.1f} MB")
            
            # 如果檔案太大，提供壓縮選項
            if file_size > self.max_log_size:
                _p(f"⚠️  日誌檔案超過 {self.max_log_size/(1024*1024):.0f} MB 限制")
                
                try:
                    compressed_file = self.batch_log_file.with_suffix('.log.gz')
                    with open(self.batch_log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    # 刪除原始檔案
                    self.batch_log_file.unlink()
                    
                    compressed_size = compressed_file.stat().st_size / (1024 * 1024)
                    _p(f"✅ 已壓縮日誌檔案: {compressed_file} ({compressed_size:.1f} MB)")
                    
                except Exception as e:
                    _p(f"❌ 壓縮日誌檔案失敗: {e}")
    
    def log_progress(self, current: int, total: int, successful: int, failed: int, 
                    stock_id: Optional[str] = None, result: Optional[str] = None):
        """記錄進度訊息"""
        if self.log_mode == '1':  # 標準模式
            if stock_id and result:
                _p(f"📊 [{current}/{total}] {stock_id}: {result}")
        elif self.log_mode == '2':  # 簡化模式
            if current % 10 == 1 or current == total:
                if stock_id:
                    _p(f"📊 處理股票 {current}-{min(current+9, total)}: {stock_id}...")
        elif self.log_mode == '3':  # 靜默模式
            if current % 100 == 0 or current == total:
                _p(f"📈 進度: {current}/{total} (成功: {successful}, 失敗: {failed})")
    
    def log_summary(self, current: int, total: int, successful: int, failed: int):
        """記錄摘要訊息"""
        show_summary = False
        
        if self.log_mode == '1' and (current % 10 == 0 or current == total):
            show_summary = True
        elif self.log_mode == '2' and (current % 50 == 0 or current == total):
            show_summary = True
        elif self.log_mode == '3' and (current % 100 == 0 or current == total):
            show_summary = True
        
        if show_summary:
            _p(f"📈 進度摘要 [{current}/{total}]: 成功 {successful}, 失敗 {failed}")


def clean_old_logs(log_dir: str = "stock_price_investment_system/logs", 
                   keep_days: int = 7, 
                   compress_days: int = 1):
    """
    清理舊日誌檔案
    
    Args:
        log_dir: 日誌目錄
        keep_days: 保留天數
        compress_days: 超過幾天的檔案進行壓縮
    """
    _safe_setup_stdout()
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    now = datetime.now()
    compressed_count = 0
    deleted_count = 0
    
    for log_file in log_path.glob("*.log"):
        # 跳過當前會話的日誌
        if "current_session" in log_file.name:
            continue
            
        file_age = (now - datetime.fromtimestamp(log_file.stat().st_mtime)).days
        
        if file_age > keep_days:
            # 刪除舊檔案
            try:
                log_file.unlink()
                deleted_count += 1
            except Exception as e:
                _p(f"❌ 刪除日誌檔案失敗 {log_file}: {e}")
                
        elif file_age > compress_days and not log_file.name.endswith('.gz'):
            # 壓縮檔案
            try:
                compressed_file = log_file.with_suffix('.log.gz')
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                log_file.unlink()
                compressed_count += 1
            except Exception as e:
                _p(f"❌ 壓縮日誌檔案失敗 {log_file}: {e}")
    
    if compressed_count > 0 or deleted_count > 0:
        _p(f"🧹 日誌清理完成: 壓縮 {compressed_count} 個, 刪除 {deleted_count} 個檔案")


# 使用範例
if __name__ == "__main__":
    # 測試日誌管理器
    manager = BatchLogManager(log_mode="2")
    manager.start_batch_logging("test_operation")
    
    # 模擬批量操作
    total_stocks = 100
    successful = 0
    failed = 0
    
    for i in range(1, total_stocks + 1):
        stock_id = f"TEST{i:04d}"
        
        # 模擬處理結果
        if i % 7 == 0:  # 模擬失敗
            failed += 1
            result = "❌ 失敗"
        else:
            successful += 1
            result = "✅ 成功"
        
        manager.log_progress(i, total_stocks, successful, failed, stock_id, result)
        manager.log_summary(i, total_stocks, successful, failed)
    
    manager.stop_batch_logging()
    
    # 清理舊日誌
    clean_old_logs()
