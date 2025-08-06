# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Logging System
日誌系統
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from config.settings import LOGGING_CONFIG

class PredictorLogger:
    """預測系統專用日誌器"""
    
    def __init__(self, name: str = 'eps_revenue_predictor'):
        self.name = name
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌器"""
        # 創建日誌器
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, LOGGING_CONFIG['level']))
        
        # 避免重複添加handler
        if self.logger.handlers:
            return
        
        # 確保日誌目錄存在
        log_dir = LOGGING_CONFIG['file_path'].parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建格式器
        formatter = logging.Formatter(
            LOGGING_CONFIG['format'],
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件處理器 (輪轉日誌)
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                LOGGING_CONFIG['file_path'],
                maxBytes=LOGGING_CONFIG['max_file_size'],
                backupCount=LOGGING_CONFIG['backup_count'],
                encoding='utf-8'
            )
        except Exception as e:
            # 如果文件處理器失敗，只使用控制台處理器
            print(f"Warning: File handler failed: {e}")
            file_handler = None
        # 控制台處理器
        import sys
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # 添加處理器
        if file_handler:
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """記錄信息日誌"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def debug(self, message: str, **kwargs):
        """記錄調試日誌"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """記錄警告日誌"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """記錄錯誤日誌"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """記錄嚴重錯誤日誌"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """格式化日誌訊息"""
        if kwargs:
            # 添加額外的上下文信息
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {context}"
        return message
    
    def log_prediction_start(self, stock_id: str, prediction_type: str):
        """記錄預測開始"""
        self.info(f"[PREDICTION_START] {prediction_type} prediction started", 
                 stock_id=stock_id, type=prediction_type)
    
    def log_prediction_result(self, stock_id: str, prediction_type: str, 
                            result: dict, confidence: str):
        """記錄預測結果"""
        self.info(f"[PREDICTION_RESULT] {prediction_type} prediction completed",
                 stock_id=stock_id, type=prediction_type, 
                 confidence=confidence, result=str(result))
    
    def log_data_collection(self, stock_id: str, data_type: str, 
                          records_count: int, date_range: str = None):
        """記錄資料收集"""
        self.info(f"[DATA_COLLECTION] {data_type} data collected",
                 stock_id=stock_id, data_type=data_type,
                 records=records_count, date_range=date_range)
    
    def log_model_training(self, model_type: str, training_samples: int, 
                          performance: dict = None):
        """記錄模型訓練"""
        self.info(f"[MODEL_TRAINING] {model_type} model training completed",
                 model_type=model_type, samples=training_samples,
                 performance=str(performance) if performance else None)
    
    def log_backtest_start(self, start_date: str, end_date: str, stocks_count: int):
        """記錄回測開始"""
        self.info(f"[BACKTEST_START] Backtesting started",
                 start_date=start_date, end_date=end_date, stocks=stocks_count)
    
    def log_backtest_result(self, accuracy: float, total_predictions: int):
        """記錄回測結果"""
        self.info(f"[BACKTEST_RESULT] Backtesting completed",
                 accuracy=f"{accuracy:.2%}", predictions=total_predictions)
    
    def log_error_with_context(self, error: Exception, context: dict):
        """記錄帶上下文的錯誤"""
        self.error(f"[ERROR] {str(error)}", **context)

# 全域日誌器實例
logger = PredictorLogger()

# 便捷函數
def get_logger(name: str = None) -> PredictorLogger:
    """獲取日誌器實例"""
    if name:
        return PredictorLogger(name)
    return logger

def log_function_call(func_name: str, **kwargs):
    """記錄函數調用"""
    logger.debug(f"[FUNCTION_CALL] {func_name}", **kwargs)

def log_performance(func_name: str, execution_time: float, **kwargs):
    """記錄性能指標"""
    logger.info(f"[PERFORMANCE] {func_name} executed", 
               execution_time=f"{execution_time:.3f}s", **kwargs)

# 裝飾器：自動記錄函數執行
def log_execution(func):
    """裝飾器：自動記錄函數執行時間"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        
        try:
            log_function_call(func_name, args_count=len(args), kwargs_count=len(kwargs))
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            log_performance(func_name, execution_time, status='success')
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.log_error_with_context(e, {
                'function': func_name,
                'execution_time': f"{execution_time:.3f}s",
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            })
            raise
    
    return wrapper

if __name__ == "__main__":
    # 測試日誌系統
    test_logger = get_logger("test")
    
    test_logger.info("Testing logger system")
    test_logger.log_prediction_start("2385", "revenue_growth")
    test_logger.log_data_collection("2385", "monthly_revenue", 24, "2022-01 to 2023-12")
    test_logger.log_prediction_result("2385", "revenue_growth", 
                                    {"growth": 0.15, "confidence": "High"}, "High")
    
    print("Logger test completed. Check logs directory.")
