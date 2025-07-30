#!/usr/bin/env python3
"""
潛力股預測系統啟動器

一鍵啟動選單系統
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """檢查運行環境"""
    print("🔍 檢查運行環境...")
    
    # 檢查 Python 版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"⚠️ Python 版本過舊: {python_version.major}.{python_version.minor}")
        print("建議使用 Python 3.8 或以上版本")
    else:
        print(f"✅ Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 檢查基本套件
    required_packages = ['pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安裝")
        except ImportError:
            print(f"❌ {package} 未安裝")
            missing_packages.append(package)
    
    # 檢查可選套件
    optional_packages = ['sklearn', 'matplotlib']
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安裝")
        except ImportError:
            print(f"⚠️ {package} 未安裝 (可選)")
    
    # 檢查資料庫
    db_path = Path("../data/taiwan_stock.db")
    if db_path.exists():
        print("✅ 台灣股票資料庫已找到")
    else:
        print("⚠️ 台灣股票資料庫未找到")
        print("請先執行主系統收集資料: cd ../ && python c.py")
    
    if missing_packages:
        print(f"\n🔧 需要安裝的套件: {', '.join(missing_packages)}")
        print(f"安裝命令: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def show_welcome():
    """顯示歡迎訊息"""
    print("🚀 歡迎使用潛力股預測系統！")
    print("=" * 50)
    print("📈 基於台灣股票系統的機器學習預測模組")
    print("🎯 預測目標：20日內股價上漲超過5%的股票")
    print("🤖 支援多種機器學習模型")
    print("📊 提供完整的特徵工程和預測服務")
    print("=" * 50)

def show_quick_start():
    """顯示快速開始指南"""
    print("\n🚀 快速開始指南")
    print("-" * 30)
    print("1️⃣ 首次使用：選單 1 → 1 (快速測試)")
    print("2️⃣ 準備資料：選單 2 → 3 (批次處理)")
    print("3️⃣ 訓練模型：選單 3 → 1 (訓練基本模型)")
    print("4️⃣ 執行預測：選單 4 → 3 (生成排行榜)")
    print("5️⃣ 查看結果：選單 5 → 1 (查看排行榜)")
    print("-" * 30)

def main():
    """主程式"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    show_welcome()
    
    # 檢查環境
    if not check_environment():
        print("\n❌ 環境檢查失敗，請先安裝必要套件")
        choice = input("\n是否要自動安裝基本套件？(y/N): ").strip().lower()
        if choice == 'y':
            print("⏳ 安裝基本套件...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "numpy", "scikit-learn", "matplotlib"], check=True)
                print("✅ 套件安裝完成！")
            except subprocess.CalledProcessError:
                print("❌ 套件安裝失敗，請手動安裝")
                return
        else:
            return
    
    show_quick_start()
    
    # 啟動選單
    choice = input("\n按 Enter 啟動選單系統，或輸入 'q' 退出: ").strip().lower()
    if choice != 'q':
        print("\n🚀 啟動選單系統...")
        try:
            subprocess.run([sys.executable, "menu.py"])
        except KeyboardInterrupt:
            print("\n\n👋 感謝使用潛力股預測系統！")
        except Exception as e:
            print(f"\n❌ 啟動選單失敗: {e}")
    else:
        print("👋 感謝使用潛力股預測系統！")

if __name__ == "__main__":
    main()
