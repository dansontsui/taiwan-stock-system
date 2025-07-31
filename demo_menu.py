#!/usr/bin/env python3
"""
演示 start.py 選單功能
"""

import subprocess
import sys
import os

def demo_menu():
    """演示選單功能"""
    print("=" * 60)
    print("Taiwan Stock System - start.py 選單功能演示")
    print("=" * 60)
    
    print("\n[功能說明]:")
    print("• 執行 'python start.py' 會顯示互動式選單")
    print("• 選單提供 6 個選項：")
    print("  1. 收集所有股票 (2,822檔)")
    print("  2. 收集主要股票 (50檔)")
    print("  3. 測試收集 (3檔)")
    print("  4. 啟動Web介面")
    print("  5. 顯示說明")
    print("  0. 退出")

    print("\n[使用方式]:")
    print("• 輸入數字選擇功能")
    print("• 執行完成後會返回選單")
    print("• 按 Ctrl+C 或選擇 0 退出")

    print("\n[快速測試]:")
    print("• 建議先選擇選項 3 (測試收集) 確認系統正常")
    print("• 測試成功後再使用其他功能")

    print("\n[命令列模式]:")
    print("• 也可以直接使用參數：python start.py test")
    print("• 支援的參數：all, main, test, web, help")
    print("• 簡化參數：a, m, t, w, h")
    
    print("\n" + "=" * 60)
    print("現在您可以執行 'python start.py' 來體驗選單功能！")
    print("=" * 60)

if __name__ == "__main__":
    demo_menu()
