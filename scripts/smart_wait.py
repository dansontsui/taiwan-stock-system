#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能等待模組 - 用於API限制處理
"""

import time
from datetime import datetime, timedelta

class SmartWaitManager:
    """智能等待管理器"""
    
    def __init__(self, api_reset_minutes=70):
        """
        初始化智能等待管理器
        
        Args:
            api_reset_minutes: API重置週期（分鐘）
        """
        self.api_reset_minutes = api_reset_minutes
        self.execution_start_time = None
        self.reset_execution_timer()
    
    def reset_execution_timer(self):
        """重置執行時間計時器"""
        self.execution_start_time = datetime.now()
        print(f"[TIMER] 重置執行時間計時器: {self.execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_execution_time_minutes(self):
        """獲取總執行時間（分鐘）"""
        if self.execution_start_time is None:
            return 0
        
        elapsed = datetime.now() - self.execution_start_time
        return elapsed.total_seconds() / 60
    
    def smart_wait_for_api_reset(self):
        """智能等待API限制重置 - 等待時間 = API重置週期 - 總執行時間"""
        executed_minutes = self.get_execution_time_minutes()
        
        # 計算實際需要等待的時間
        remaining_wait_minutes = max(0, self.api_reset_minutes - executed_minutes)
        
        print(f"\n🚫 API請求限制已達上限")
        print("=" * 60)
        print(f"📊 執行統計:")
        print(f"   總執行時間: {executed_minutes:.1f} 分鐘")
        print(f"   API重置週期: {self.api_reset_minutes} 分鐘")
        print(f"   需要等待: {remaining_wait_minutes:.1f} 分鐘")
        print("=" * 60)
        
        if remaining_wait_minutes <= 0:
            print("✅ 已超過API重置週期，立即重置計時器並繼續")
            self.reset_execution_timer()
            return
        
        # 執行智能等待
        print(f"⏳ 智能等待 {remaining_wait_minutes:.1f} 分鐘...")
        
        wait_start_time = datetime.now()
        end_time = wait_start_time + timedelta(minutes=remaining_wait_minutes)
        
        print(f"開始等待: {wait_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"預計結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 等待邏輯
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
        
        # 重置執行時間計時器
        self.reset_execution_timer()
    
    def is_api_limit_error(self, error_msg):
        """判斷是否為API限制錯誤"""
        api_limit_keywords = [
            "402", "Payment Required", "API請求限制", 
            "rate limit", "quota exceeded", "too many requests"
        ]
        
        error_msg_lower = error_msg.lower()
        return any(keyword.lower() in error_msg_lower for keyword in api_limit_keywords)

# 全局智能等待管理器實例
_global_wait_manager = None

def get_smart_wait_manager():
    """獲取全局智能等待管理器"""
    global _global_wait_manager
    if _global_wait_manager is None:
        _global_wait_manager = SmartWaitManager()
    return _global_wait_manager

def reset_execution_timer():
    """重置執行時間計時器（全局函數）"""
    manager = get_smart_wait_manager()
    manager.reset_execution_timer()

def smart_wait_for_api_reset():
    """智能等待API限制重置（全局函數）"""
    manager = get_smart_wait_manager()
    manager.smart_wait_for_api_reset()

def is_api_limit_error(error_msg):
    """判斷是否為API限制錯誤（全局函數）"""
    manager = get_smart_wait_manager()
    return manager.is_api_limit_error(error_msg)

def get_execution_time_minutes():
    """獲取總執行時間（全局函數）"""
    manager = get_smart_wait_manager()
    return manager.get_execution_time_minutes()

# 向後兼容的函數
def wait_for_api_reset():
    """向後兼容的等待函數"""
    smart_wait_for_api_reset()

if __name__ == "__main__":
    # 測試智能等待功能
    print("測試智能等待功能")
    
    manager = SmartWaitManager(api_reset_minutes=2)  # 2分鐘測試
    
    print("模擬執行1分鐘...")
    time.sleep(60)
    
    print("觸發API限制...")
    manager.smart_wait_for_api_reset()
    
    print("測試完成")
