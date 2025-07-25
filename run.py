#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股歷史股價系統啟動腳本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """檢查必要的依賴套件"""
    required_packages = [
        'pandas',
        'requests'
    ]

    optional_packages = [
        'streamlit',
        'plotly'
    ]

    missing_required = []
    missing_optional = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package} 已安裝")
        except ImportError as e:
            print(f"[ERROR] {package} 未安裝: {e}")
            missing_required.append(package)

    for package in optional_packages:
        try:
            __import__(package)
            print(f"[OK] {package} 已安裝")
        except ImportError:
            print(f"[WARNING] {package} 未安裝")
            missing_optional.append(package)

    if missing_required:
        print("[ERROR] 缺少必要套件:")
        for package in missing_required:
            print(f"   - {package}")
        print("\n請執行以下命令安裝:")
        print(f"pip install {' '.join(missing_required)}")
        return False

    if missing_optional:
        print("[WARNING] 缺少可選套件 (Web介面將不可用):")
        for package in missing_optional:
            print(f"   - {package}")
        print("\n如需Web介面，請執行:")
        print(f"pip install {' '.join(missing_optional)}")
        return 'basic'  # 返回基本模式

    return True

def check_database():
    """檢查資料庫是否存在"""
    db_path = Path("data/taiwan_stock.db")
    
    if not db_path.exists():
        print("[ERROR] 資料庫不存在")
        print("\n請先執行以下命令:")
        print("1. python scripts/init_database.py")
        print("2. python scripts/collect_data.py --test")
        return False
    
    return True

def main():
    """主函數"""
    print("=" * 60)
    print("台股歷史股價系統")
    print("=" * 60)

    # 檢查依賴套件
    print("檢查依賴套件...")
    dep_result = check_dependencies()
    if dep_result == False:
        sys.exit(1)
    elif dep_result == 'basic':
        print("[OK] 基本套件檢查通過 (將啟動命令列版本)")
    else:
        print("[OK] 所有套件檢查通過")

    # 檢查資料庫
    print("檢查資料庫...")
    if not check_database():
        sys.exit(1)
    print("[OK] 資料庫檢查通過")

    # 根據套件情況選擇啟動方式
    if dep_result == 'basic':
        # 啟動命令列版本
        print("\n啟動命令列版本...")
        print("按 Ctrl+C 停止系統")
        print("=" * 60)

        try:
            # 啟動簡單演示
            cmd = [sys.executable, "simple_demo.py"]
            subprocess.run(cmd)

        except KeyboardInterrupt:
            print("\n\n系統已停止")
        except Exception as e:
            print(f"\n[ERROR] 啟動失敗: {e}")
            sys.exit(1)

    else:
        # 啟動 Streamlit 應用
        print("\n啟動Web版本...")
        print("瀏覽器將自動開啟 http://localhost:8501")
        print("按 Ctrl+C 停止系統")
        print("=" * 60)

        try:
            # 啟動 Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "app/web/dashboard.py",
                "--server.port=8501",
                "--server.address=localhost",
                "--browser.gatherUsageStats=false"
            ]

            subprocess.run(cmd)

        except KeyboardInterrupt:
            print("\n\n系統已停止")
        except Exception as e:
            print(f"\n[ERROR] 啟動失敗: {e}")
            print("嘗試啟動命令列版本...")
            try:
                cmd = [sys.executable, "simple_demo.py"]
                subprocess.run(cmd)
            except:
                sys.exit(1)

if __name__ == "__main__":
    main()
