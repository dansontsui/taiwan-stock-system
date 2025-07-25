#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股分析系統簡易啟動腳本
避免複雜的模組導入問題，使用subprocess執行各個腳本
"""

import sys
import os
import time
import subprocess
import webbrowser
from datetime import datetime
import argparse

def print_banner():
    """顯示啟動橫幅"""
    print("=" * 80)
    print("🚀 台股分析系統簡易啟動")
    print("=" * 80)
    print("📊 功能包括：")
    print("   • 資料收集 (股價、財務報表、現金流量等)")
    print("   • Web監控介面 (Streamlit)")
    print("   • 每日增量更新")
    print("   • 潛力股分析")
    print("=" * 80)

def check_python():
    """檢查Python版本"""
    print("🔧 檢查Python版本...")
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python版本過低，需要3.8或更高版本")
        return False
    else:
        print("   ✅ Python版本符合要求")
        return True

def check_packages():
    """檢查必要套件"""
    print("\n🔧 檢查必要套件...")
    
    packages = ['streamlit', 'pandas', 'numpy']
    missing = []
    
    for package in packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ 缺少套件: {', '.join(missing)}")
        print("請執行: pip install " + " ".join(missing))
        return False
    
    print("✅ 所有套件檢查通過")
    return True

def check_files():
    """檢查必要檔案"""
    print("\n📁 檢查必要檔案...")
    
    files = [
        'run.py',
        'config.py',
        'scripts/collect_daily_update.py',
        'scripts/collect_cash_flows.py',
        'scripts/collect_dividend_results.py'
    ]
    
    missing = []
    for file in files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing.append(file)
    
    if missing:
        print(f"\n⚠️ 缺少檔案: {', '.join(missing)}")
        return False
    
    print("✅ 所有檔案檢查通過")
    return True

def run_script(script_path, args=None, timeout=3600):
    """執行Python腳本"""
    try:
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        print(f"🔄 執行: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            print("✅ 執行成功")
            return True
        else:
            print(f"❌ 執行失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 執行超時")
        return False
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        return False

def start_streamlit():
    """啟動Streamlit"""
    print("\n🌐 啟動Web監控介面...")
    
    try:
        # 檢查端口是否已被占用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8501))
        sock.close()
        
        if result == 0:
            print("✅ Web介面已在運行: http://localhost:8501")
            return True
        
        # 啟動Streamlit
        print("🚀 啟動Streamlit服務...")
        
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'run.py',
            '--server.port', '8501',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ])
        
        # 等待服務啟動
        print("⏳ 等待服務啟動...")
        time.sleep(15)
        
        # 檢查服務是否啟動成功
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8501))
        sock.close()
        
        if result == 0:
            print("✅ Web介面啟動成功: http://localhost:8501")
            
            # 自動開啟瀏覽器
            try:
                webbrowser.open('http://localhost:8501')
                print("🌐 已自動開啟瀏覽器")
            except:
                print("💡 請手動開啟瀏覽器訪問: http://localhost:8501")
            
            return True
        else:
            print("❌ Web介面啟動失敗")
            return False
            
    except Exception as e:
        print(f"❌ Web介面啟動錯誤: {e}")
        return False

def show_menu():
    """顯示選單"""
    print("\n📋 請選擇操作:")
    print("1. 🔄 每日增量更新")
    print("2. 💰 現金流量表收集")
    print("3. 🎯 除權除息結果收集")
    print("4. 🌐 啟動Web監控介面")
    print("5. 🔍 檢查系統狀態")
    print("0. ❌ 退出")
    print("-" * 40)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='台股分析系統簡易啟動')
    parser.add_argument('--mode', choices=['daily', 'cash_flow', 'dividend', 'web', 'check'], 
                       help='啟動模式')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 基本檢查
    if not check_python():
        return
    
    if not check_packages():
        return
    
    if not check_files():
        return
    
    if args.mode:
        # 命令列模式
        if args.mode == 'daily':
            print("\n🔄 執行每日增量更新...")
            success = run_script('scripts/collect_daily_update.py', ['--batch-size', '3'])
            if success:
                start_streamlit()
        elif args.mode == 'cash_flow':
            print("\n💰 執行現金流量表收集...")
            success = run_script('scripts/collect_cash_flows.py', ['--batch-size', '3', '--test'])
            if success:
                start_streamlit()
        elif args.mode == 'dividend':
            print("\n🎯 執行除權除息結果收集...")
            success = run_script('scripts/collect_dividend_results.py', ['--batch-size', '3', '--test'])
            if success:
                start_streamlit()
        elif args.mode == 'web':
            start_streamlit()
        elif args.mode == 'check':
            print("\n✅ 系統檢查完成")
    else:
        # 互動模式
        while True:
            show_menu()
            try:
                choice = input("請輸入選項 (0-5): ").strip()
                
                if choice == '0':
                    print("👋 再見！")
                    break
                elif choice == '1':
                    print("\n🔄 執行每日增量更新...")
                    success = run_script('scripts/collect_daily_update.py', ['--batch-size', '3'])
                    if success:
                        start_streamlit()
                elif choice == '2':
                    print("\n💰 執行現金流量表收集...")
                    success = run_script('scripts/collect_cash_flows.py', ['--batch-size', '3', '--test'])
                    if success:
                        start_streamlit()
                elif choice == '3':
                    print("\n🎯 執行除權除息結果收集...")
                    success = run_script('scripts/collect_dividend_results.py', ['--batch-size', '3', '--test'])
                    if success:
                        start_streamlit()
                elif choice == '4':
                    start_streamlit()
                elif choice == '5':
                    print("\n🔍 重新檢查系統狀態...")
                    check_python()
                    check_packages()
                    check_files()
                else:
                    print("❌ 無效選項，請重新選擇")
                
                if choice in ['1', '2', '3', '4']:
                    print("\n✅ 系統已啟動！")
                    print("💡 Web介面: http://localhost:8501")
                    print("💡 按 Ctrl+C 可停止服務")
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n⚠️ 用戶中斷服務")
                        break
                        
            except KeyboardInterrupt:
                print("\n👋 再見！")
                break
            except Exception as e:
                print(f"❌ 執行錯誤: {e}")

if __name__ == "__main__":
    main()
