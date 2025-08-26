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


def set_cli_only_mode(enabled: bool = True):
    """
    設定CLI專用模式 - 禁用所有模組的檔案日誌輸出

    Args:
        enabled: True=啟用CLI專用模式（不記錄檔案），False=恢復正常模式
    """
    # 獲取所有相關的logger
    loggers_to_modify = [
        'stock_price_investment_system.data.data_manager',
        'stock_price_investment_system.data.revenue_integration',
        'stock_price_investment_system.data.price_data',
        'stock_price_investment_system.price_models.feature_engineering',
        'stock_price_investment_system.price_models.stock_price_predictor',
        'stock_price_investment_system.price_models.holdout_backtester',
        'stock_price_investment_system.price_models.walk_forward_validator',
        'stock_price_investment_system.selector.candidate_pool_generator',
        'stock_price_investment_system',  # 根logger
    ]

    for logger_name in loggers_to_modify:
        logger = logging.getLogger(logger_name)

        if enabled:
            # CLI專用模式：移除所有檔案處理器，只保留控制台處理器
            handlers_to_remove = []
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handlers_to_remove.append(handler)

            for handler in handlers_to_remove:
                logger.removeHandler(handler)
                handler.close()

            # 設定為不傳播到父logger（避免重複輸出）
            logger.propagate = False

            # 如果沒有控制台處理器，添加一個簡單的
            has_console_handler = any(
                isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
                for h in logger.handlers
            )

            if not has_console_handler and logger.level <= logging.WARNING:
                # 只為警告和錯誤添加控制台處理器
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.WARNING)  # 只顯示警告和錯誤
                formatter = logging.Formatter('%(levelname)s: %(message)s')
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
        else:
            # 恢復正常模式：重新啟用傳播
            logger.propagate = True


def suppress_verbose_logging():
    """抑制詳細的INFO級別日誌，只保留WARNING和ERROR"""
    loggers_to_suppress = [
        'stock_price_investment_system.data.data_manager',
        'stock_price_investment_system.data.revenue_integration',
        'stock_price_investment_system.data.price_data',
        'stock_price_investment_system.price_models.feature_engineering',
    ]

    for logger_name in loggers_to_suppress:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)  # 只顯示WARNING和ERROR


def suppress_repetitive_warnings():
    """抑制重複的WARNING訊息，特別是營收/EPS預測器不可用的警告"""
    import warnings

    # 抑制特定的重複警告
    warnings.filterwarnings("ignore", message=".*Revenue predictor not available.*")
    warnings.filterwarnings("ignore", message=".*EPS predictor not available.*")

    # 創建一個通用的重複警告過濾器
    class RepetitiveWarningFilter(logging.Filter):
        def __init__(self):
            super().__init__()
            self.seen_messages = set()
            self.max_repeats = 1  # 每種訊息最多顯示1次

        def filter(self, record):
            try:
                if record.levelno == logging.WARNING:
                    # 安全地獲取訊息
                    try:
                        message = record.getMessage()
                    except (TypeError, AttributeError) as e:
                        # 如果getMessage()失敗，嘗試直接使用msg
                        message = str(getattr(record, 'msg', ''))
                        if not message:
                            # 如果還是沒有訊息，允許通過但記錄問題
                            print(f"⚠️  日誌記錄格式異常: {e}")
                            return True

                    # 檢查是否為需要抑制的重複警告
                    suppress_patterns = [
                        "predictor not available",
                        "查無.*價格資料",
                        "No price data available",
                        "No monthly revenue data found",
                        "No revenue data available",
                        "價格資料缺少必要欄位",
                        "Missing required columns",
                        "資料為空",
                        "Empty data"
                    ]

                    should_suppress = any(pattern in message for pattern in suppress_patterns)

                    if should_suppress:
                        if message in self.seen_messages:
                            return False  # 抑制重複訊息
                        else:
                            self.seen_messages.add(message)
                            # 修改訊息，添加提示
                            try:
                                record.msg = f"{record.msg} (後續相同警告將被抑制)"
                            except (TypeError, AttributeError):
                                # 如果無法修改msg，就不修改
                                pass
                            return True
            except Exception as e:
                # 如果過濾器本身出錯，允許日誌通過並記錄問題
                print(f"⚠️  日誌過濾器錯誤: {e}")
                return True
            return True

    # 為相關模組添加過濾器
    modules_to_filter = [
        'stock_price_investment_system.data.revenue_integration',
        'stock_price_investment_system.data.data_manager',
        'stock_price_investment_system.data.price_data',
        'stock_price_investment_system.price_models.feature_engineering'
    ]

    for module_name in modules_to_filter:
        logger = logging.getLogger(module_name)
        logger.addFilter(RepetitiveWarningFilter())


def suppress_data_missing_warnings():
    """完全抑制資料缺失相關的WARNING訊息（用於精簡模式）"""

    class DataMissingWarningFilter(logging.Filter):
        def filter(self, record):
            try:
                if record.levelno == logging.WARNING:
                    # 安全地獲取訊息
                    try:
                        message = record.getMessage()
                    except (TypeError, AttributeError) as e:
                        # 如果getMessage()失敗，嘗試直接使用msg
                        message = str(getattr(record, 'msg', ''))
                        if not message:
                            # 如果還是沒有訊息，允許通過但記錄問題
                            print(f"⚠️  日誌記錄格式異常: {e}")
                            return True

                    # 使用正則表達式進行更精確的匹配
                    import re
                    suppress_patterns = [
                        r"查無.*價格資料",
                        r"No price data available",
                        r"No monthly revenue data found",
                        r"No revenue data available",
                        r"價格資料缺少必要欄位",
                        r"Missing required columns",
                        r"資料為空",
                        r"Empty data",
                        r".*predictor not available.*",
                        r"Revenue predictor not available.*",
                        r"EPS predictor not available.*"
                    ]

                    # 如果匹配任何模式，完全抑制
                    for pattern in suppress_patterns:
                        if re.search(pattern, message, re.IGNORECASE):
                            return False

            except Exception as e:
                # 如果過濾器本身出錯，允許日誌通過並記錄問題
                print(f"⚠️  日誌過濾器錯誤: {e}")
                return True

            return True

    # 為所有相關模組添加強力過濾器
    modules_to_filter = [
        'stock_price_investment_system.data.revenue_integration',
        'stock_price_investment_system.data.data_manager',
        'stock_price_investment_system.data.price_data',
        'stock_price_investment_system.price_models.feature_engineering',
        'stock_price_investment_system.price_models.stock_price_predictor',
        'stock_price_investment_system.price_models.holdout_backtester',
        'stock_price_investment_system.price_models.walk_forward_validator'
    ]

    for module_name in modules_to_filter:
        logger = logging.getLogger(module_name)
        logger.addFilter(DataMissingWarningFilter())


def log_menu_parameters(menu_id: str, menu_name: str, parameters: dict, force_log: bool = True):
    """
    記錄選單參數到日誌檔案

    Args:
        menu_id: 選單編號
        menu_name: 選單名稱
        parameters: 參數字典
        force_log: 是否強制記錄（即使在CLI專用模式下）
    """
    import json
    from datetime import datetime
    from pathlib import Path

    try:
        # 創建參數記錄
        param_record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'menu_id': menu_id,
            'menu_name': menu_name,
            'parameters': parameters
        }

        # 確保日誌目錄存在
        log_dir = Path("stock_price_investment_system/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "menu_parameters.log"

        # 格式化參數記錄
        param_str = json.dumps(param_record, ensure_ascii=False, indent=2)
        log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 選單參數記錄:\n{param_str}\n\n"

        # 直接寫入檔案（追加模式）
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        # 同時輸出到控制台
        print(f"📝 已記錄選單{menu_id}的參數到日誌檔案")

    except Exception as e:
        print(f"⚠️  參數記錄失敗: {e}")
        import traceback
        traceback.print_exc()


def log_execution_summary(menu_id: str, menu_name: str, success: bool, duration: float = None, result_summary: str = None):
    """
    記錄執行摘要到日誌檔案

    Args:
        menu_id: 選單編號
        menu_name: 選單名稱
        success: 是否執行成功
        duration: 執行時間（秒）
        result_summary: 結果摘要
    """
    from datetime import datetime
    from pathlib import Path

    try:
        # 確保日誌目錄存在
        log_dir = Path("stock_price_investment_system/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "menu_parameters.log"

        status = "成功" if success else "失敗"
        duration_str = f", 耗時: {duration:.1f}秒" if duration else ""

        log_message = f"選單{menu_id}執行{status}{duration_str}"
        if result_summary:
            log_message += f", 結果: {result_summary}"

        # 直接寫入檔案（追加模式）
        log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {log_message}\n"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        # 同時輸出到控制台
        emoji = "✅" if success else "❌"
        print(f"{emoji} {log_message}")

    except Exception as e:
        print(f"⚠️  執行摘要記錄失敗: {e}")


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
