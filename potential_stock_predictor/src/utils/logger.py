#!/usr/bin/env python3
"""
日誌配置工具
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

try:
    from ...config.config import LOGGING_CONFIG
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    sys.path.insert(0, project_root)
    from config.config import LOGGING_CONFIG

def setup_logger(name: str = 'potential_stock_predictor', 
                log_file: Optional[str] = None,
                level: str = None) -> logging.Logger:
    """
    設置日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        log_file: 日誌檔案路徑
        level: 日誌級別
        
    Returns:
        配置好的日誌記錄器
    """
    # 使用配置檔案中的設定
    log_level = level or LOGGING_CONFIG['level']
    log_format = LOGGING_CONFIG['format']
    log_file_path = Path(log_file) if log_file else LOGGING_CONFIG['file_path']
    
    # 確保日誌目錄存在
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 創建日誌記錄器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重複添加處理器
    if logger.handlers:
        return logger
    
    # 創建格式化器
    formatter = logging.Formatter(log_format)
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 檔案處理器（支援輪轉）- 使用 UTF-8 編碼支援中文
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=LOGGING_CONFIG['max_file_size'],
        backupCount=LOGGING_CONFIG['backup_count'],
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 預設日誌記錄器
default_logger = setup_logger()

def log_function_call(func):
    """
    裝飾器：記錄函數調用
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('potential_stock_predictor')
        logger.info(f"調用函數: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"函數 {func.__name__} 執行成功")
            return result
        except Exception as e:
            logger.error(f"函數 {func.__name__} 執行失敗: {e}")
            raise
    return wrapper
