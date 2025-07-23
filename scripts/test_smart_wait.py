#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試智能等待功能
"""

from datetime import datetime, timedelta
import time

def calculate_wait_time(start_time, current_time=None):
    """計算智能等待時間"""
    if current_time is None:
        current_time = datetime.now()

    elapsed_minutes = (current_time - start_time).total_seconds() / 60

    # API限制是每小時重置，所以計算到下一個小時的時間
    minutes_in_hour = current_time.minute
    seconds_in_minute = current_time.second

    # 計算到下一個小時還需要多少時間
    minutes_to_next_hour = 60 - minutes_in_hour
    seconds_to_next_hour = (minutes_to_next_hour * 60) - seconds_in_minute

    # 加上5分鐘緩衝時間
    total_wait_seconds = seconds_to_next_hour + (5 * 60)

    return total_wait_seconds, elapsed_minutes

def test_scenarios():
    """測試不同時間點的等待計算"""
    print("🧪 智能等待時間計算測試")
    print("="*60)
    
    # 測試場景
    test_cases = [
        # (開始時間偏移分鐘, 當前時間偏移分鐘, 描述)
        (0, 10, "開始後10分鐘遇到限制"),
        (0, 30, "開始後30分鐘遇到限制"),
        (0, 50, "開始後50分鐘遇到限制"),
        (0, 55, "開始後55分鐘遇到限制"),
        (30, 45, "開始30分鐘，運行15分鐘後遇到限制"),
    ]
    
    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    for start_offset, current_offset, description in test_cases:
        # 模擬開始時間和當前時間
        start_time = base_time + timedelta(minutes=start_offset)
        current_time = base_time + timedelta(minutes=current_offset)
        
        # 使用指定的時間進行計算
        wait_seconds, elapsed_minutes = calculate_wait_time(start_time, current_time)

        print(f"\n📋 {description}")
        print(f"   開始時間: {start_time.strftime('%H:%M:%S')}")
        print(f"   當前時間: {current_time.strftime('%H:%M:%S')}")
        print(f"   已運行: {elapsed_minutes:.1f} 分鐘")
        print(f"   需等待: {wait_seconds/60:.1f} 分鐘")
        print(f"   恢復時間: {(current_time + timedelta(seconds=wait_seconds)).strftime('%H:%M:%S')}")

def simulate_api_limit():
    """模擬API限制場景"""
    print("\n🎯 模擬API限制場景")
    print("="*60)
    
    # 模擬開始收集資料
    start_time = datetime.now()
    print(f"📊 開始收集資料: {start_time.strftime('%H:%M:%S')}")
    
    # 模擬運行一段時間後遇到API限制
    print("⏳ 模擬收集資料中...")
    time.sleep(2)  # 模擬2秒的工作時間
    
    # 計算等待時間
    wait_seconds, elapsed_minutes = calculate_wait_time(start_time)
    
    print(f"\n⚠️  遇到API限制!")
    print(f"📊 本輪已運行: {elapsed_minutes:.1f} 分鐘")
    print(f"⏳ 需要等待: {wait_seconds/60:.1f} 分鐘")
    
    current_time = datetime.now()
    resume_time = current_time + timedelta(seconds=wait_seconds)
    print(f"🕐 當前時間: {current_time.strftime('%H:%M:%S')}")
    print(f"🕐 恢復時間: {resume_time.strftime('%H:%M:%S')}")
    
    # 顯示節省的時間
    old_wait = 65 * 60  # 原本固定等待65分鐘
    time_saved = (old_wait - wait_seconds) / 60
    
    print(f"\n💡 智能等待優勢:")
    print(f"   原本等待: 65.0 分鐘")
    print(f"   智能等待: {wait_seconds/60:.1f} 分鐘")
    print(f"   節省時間: {time_saved:.1f} 分鐘")
    
    if time_saved > 0:
        print(f"   ✅ 節省 {time_saved:.1f} 分鐘!")
    else:
        print(f"   ⚠️  需要額外等待 {abs(time_saved):.1f} 分鐘")

def main():
    """主函數"""
    print("🚀 智能等待功能測試")
    print("="*60)
    
    # 測試不同場景的等待時間計算
    test_scenarios()
    
    # 模擬實際使用場景
    simulate_api_limit()
    
    print("\n" + "="*60)
    print("✅ 測試完成!")
    print("="*60)

if __name__ == "__main__":
    main()
