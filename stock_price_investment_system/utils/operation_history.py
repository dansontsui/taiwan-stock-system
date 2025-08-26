# -*- coding: utf-8 -*-
"""
操作歷史記錄管理器 - 記錄用戶在選單中的輸入參數
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OperationHistory:
    def __init__(self, history_file: Optional[str] = None):
        """
        初始化操作歷史記錄器
        
        Args:
            history_file: 歷史記錄檔案路徑，若為None則使用預設路徑
        """
        if history_file is None:
            # 使用系統日誌目錄
            log_dir = Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = log_dir / 'operation_history.json'
        else:
            self.history_file = Path(history_file)
        
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
    def save_operation(self, menu_id: str, operation_name: str, parameters: Dict[str, Any]) -> None:
        """
        保存操作記錄
        
        Args:
            menu_id: 選單ID (如 '5', '9')
            operation_name: 操作名稱 (如 '外層回測', '超參數調優')
            parameters: 輸入的參數字典
        """
        try:
            # 讀取現有歷史
            history = self._load_history()
            
            # 建立新記錄
            record = {
                'timestamp': datetime.now().isoformat(),
                'menu_id': str(menu_id),
                'operation_name': str(operation_name),
                'parameters': parameters
            }
            
            # 添加到歷史記錄
            history.append(record)
            
            # 保留最近50筆記錄
            if len(history) > 50:
                history = history[-50:]
            
            # 保存到檔案
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"操作記錄已保存: {menu_id} - {operation_name}")
            
        except Exception as e:
            logger.warning(f"保存操作記錄失敗: {e}")
    
    def get_last_operation(self, menu_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取指定選單的最後一次操作記錄
        
        Args:
            menu_id: 選單ID
            
        Returns:
            最後一次操作的記錄，若無則返回None
        """
        try:
            history = self._load_history()
            
            # 倒序查找指定選單的記錄
            for record in reversed(history):
                if record.get('menu_id') == str(menu_id):
                    return record
                    
            return None
            
        except Exception as e:
            logger.warning(f"讀取操作記錄失敗: {e}")
            return None
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        獲取最近的操作記錄
        
        Args:
            limit: 返回記錄數量限制
            
        Returns:
            最近的操作記錄列表
        """
        try:
            history = self._load_history()
            return history[-limit:] if history else []
            
        except Exception as e:
            logger.warning(f"讀取操作記錄失敗: {e}")
            return []
    
    def get_operations_by_menu(self, menu_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        獲取指定選單的操作記錄
        
        Args:
            menu_id: 選單ID
            limit: 返回記錄數量限制
            
        Returns:
            指定選單的操作記錄列表
        """
        try:
            history = self._load_history()
            
            # 篩選指定選單的記錄
            menu_records = [r for r in history if r.get('menu_id') == str(menu_id)]
            
            return menu_records[-limit:] if menu_records else []
            
        except Exception as e:
            logger.warning(f"讀取操作記錄失敗: {e}")
            return []
    
    def clear_history(self) -> bool:
        """
        清空操作歷史
        
        Returns:
            是否成功清空
        """
        try:
            if self.history_file.exists():
                self.history_file.unlink()
            return True
        except Exception as e:
            logger.warning(f"清空操作記錄失敗: {e}")
            return False
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """載入歷史記錄"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"歷史記錄檔案損壞，將重新建立: {e}")
            return []
    
    def format_parameters(self, parameters: Dict[str, Any]) -> str:
        """
        格式化參數顯示
        
        Args:
            parameters: 參數字典
            
        Returns:
            格式化後的參數字串
        """
        if not parameters:
            return "無參數"
        
        formatted = []
        for key, value in parameters.items():
            if isinstance(value, bool):
                value_str = "是" if value else "否"
            elif isinstance(value, float):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)
            formatted.append(f"{key}={value_str}")
        
        return ", ".join(formatted)

# 全域實例
_operation_history = None

def get_operation_history() -> OperationHistory:
    """獲取全域操作歷史記錄器實例"""
    global _operation_history
    if _operation_history is None:
        _operation_history = OperationHistory()
    return _operation_history
