#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣股票系統 - 跨平台啟動器
Taiwan Stock System - Cross-platform Launcher

這個腳本會自動處理路徑問題，確保系統能在任何位置正常執行
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """設定 Python 路徑"""
    # 獲取腳本所在目錄（應該是專案根目錄）
    script_dir = Path(__file__).parent.absolute()
    
    # 確保專案根目錄在 Python 路徑中
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    print(f"📁 專案根目錄: {script_dir}")
    return script_dir

def check_required_files(project_root):
    """檢查必要檔案是否存在"""
    required_files = [
        'stock_price_investment_system/__init__.py',
        'stock_price_investment_system/config/settings.py',
        'stock_price_investment_system/selector/candidate_pool_generator.py',
        'stock_price_investment_system/start.py',
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必要檔案:")
        for file_path in missing_files:
            print(f"   • {file_path}")
        print("\n💡 請確保完整複製整個專案資料夾")
        return False
    
    print("✅ 必要檔案檢查通過")
    return True

def main():
    """主函數"""
    print("🚀 台灣股票系統啟動器")
    print("=" * 50)
    
    # 設定路徑
    project_root = setup_python_path()
    
    # 檢查檔案
    if not check_required_files(project_root):
        input("按 Enter 鍵退出...")
        return 1
    
    try:
        # 嘗試匯入並執行主程式
        print("🔄 正在載入系統...")
        
        # 先測試關鍵模組匯入
        from stock_price_investment_system.config.settings import get_config
        from stock_price_investment_system.selector.candidate_pool_generator import CandidatePoolGenerator
        
        print("✅ 模組載入成功")
        
        # 執行主程式
        print("🎯 啟動主程式...")
        from stock_price_investment_system.start import main as start_main
        return start_main()
        
    except ImportError as e:
        print(f"❌ 模組匯入失敗: {e}")
        print("\n🔍 可能的原因:")
        print("1. 專案檔案不完整")
        print("2. Python 環境缺少必要套件")
        print("3. 檔案路徑問題")
        
        print(f"\n💡 建議解決方案:")
        print("1. 確保完整複製整個專案資料夾")
        print("2. 安裝必要套件: pip install -r requirements.txt")
        print("3. 在專案根目錄下執行此腳本")
        
        input("按 Enter 鍵退出...")
        return 1
        
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        input("按 Enter 鍵退出...")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n\n👋 使用者中斷執行")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        input("按 Enter 鍵退出...")
        sys.exit(1)
