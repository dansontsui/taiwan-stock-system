#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股分析系統一鍵啟動腳本
支援Windows和Mac，提供資料收集和監控功能
"""

import sys
import os
import time
import subprocess
import threading
import webbrowser
from datetime import datetime
import argparse
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def print_banner():
    """顯示啟動橫幅"""
    print("=" * 80)
    print("🚀 台股分析系統一鍵啟動")
    print("=" * 80)
    print("📊 功能包括：")
    print("   • 資料收集 (股價、財務報表、現金流量等)")
    print("   • Web監控介面 (Streamlit)")
    print("   • 每日增量更新")
    print("   • 潛力股分析")
    print("=" * 80)

def check_dependencies():
    """檢查必要的依賴"""
    print("🔧 檢查系統依賴...")
    
    required_packages = ['streamlit', 'pandas', 'numpy', 'sqlite3']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n❌ 缺少依賴套件: {', '.join(missing_packages)}")
        print("請執行: pip install streamlit pandas numpy")
        return False
    
    print("✅ 所有依賴檢查通過")
    return True

def check_database():
    """檢查資料庫狀態"""
    print("\n📊 檢查資料庫狀態...")
    
    try:
        from config import Config
        from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager

        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 檢查主要資料表
        tables = [
            ('stocks', '股票基本資料'),
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '綜合損益表'),
            ('balance_sheets', '資產負債表'),
            ('cash_flow_statements', '現金流量表'),
            ('dividend_results', '除權除息結果'),
            ('dividend_policies', '股利政策'),
            ('financial_ratios', '財務比率'),
            ('stock_scores', '潛力股評分')
        ]
        
        total_records = 0
        for table_name, display_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
                print(f"   {display_name}: {count:,} 筆")
            except:
                print(f"   {display_name}: 表不存在")
        
        conn.close()
        
        if total_records > 0:
            print(f"✅ 資料庫正常，總計 {total_records:,} 筆資料")
            return True
        else:
            print("⚠️ 資料庫為空，建議先執行資料收集")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")
        return False

def start_data_collection(mode='daily'):
    """啟動資料收集"""
    print(f"\n📈 啟動資料收集 ({mode} 模式)...")
    
    try:
        if mode == 'daily':
            # 每日增量更新
            print("🔄 執行每日增量更新...")
            result = subprocess.run([
                sys.executable, 'scripts/collect_daily_update.py',
                '--batch-size', '3'
            ], capture_output=True, text=True, timeout=3600)
            
        elif mode == 'comprehensive':
            # 綜合資料收集
            print("🔄 執行綜合資料收集...")
            result = subprocess.run([
                sys.executable, 'scripts/collect_comprehensive_batch.py',
                '--batch-size', '3', '--test'
            ], capture_output=True, text=True, timeout=3600)
            
        elif mode == 'cash_flow':
            # 現金流量表收集
            print("🔄 執行現金流量表收集...")
            result = subprocess.run([
                sys.executable, 'scripts/collect_cash_flows.py',
                '--batch-size', '3', '--test'
            ], capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:
            print("✅ 資料收集完成")
            return True
        else:
            print(f"❌ 資料收集失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 資料收集超時")
        return False
    except Exception as e:
        print(f"❌ 資料收集錯誤: {e}")
        return False

def start_web_interface():
    """啟動Web介面"""
    print("\n🌐 啟動Web監控介面...")
    
    try:
        # 檢查是否已有Streamlit在運行
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8501))
        sock.close()
        
        if result == 0:
            print("✅ Web介面已在運行: http://localhost:8501")
            return True
        
        # 啟動Streamlit
        print("🚀 啟動Streamlit服務...")
        
        # 使用非阻塞方式啟動
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'run.py',
            '--server.port', '8501',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服務啟動
        print("⏳ 等待服務啟動...")
        time.sleep(10)
        
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
    print("1. 🔄 每日增量更新 + 啟動監控")
    print("2. 📊 綜合資料收集 + 啟動監控")
    print("3. 💰 現金流量表收集 + 啟動監控")
    print("4. 🌐 只啟動Web監控介面")
    print("5. 📈 只執行資料收集")
    print("6. 🔍 檢查系統狀態")
    print("0. ❌ 退出")
    print("-" * 40)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='台股分析系統一鍵啟動')
    parser.add_argument('--mode', choices=['auto', 'daily', 'comprehensive', 'cash_flow', 'web', 'check'], 
                       default='auto', help='啟動模式')
    parser.add_argument('--no-browser', action='store_true', help='不自動開啟瀏覽器')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 檢查依賴
    if not check_dependencies():
        return
    
    # 檢查資料庫
    db_status = check_database()
    
    if args.mode == 'auto':
        # 互動模式
        while True:
            show_menu()
            try:
                choice = input("請輸入選項 (0-6): ").strip()
                
                if choice == '0':
                    print("👋 再見！")
                    break
                elif choice == '1':
                    print("\n🚀 執行每日增量更新 + 啟動監控...")
                    start_data_collection('daily')
                    start_web_interface()
                elif choice == '2':
                    print("\n🚀 執行綜合資料收集 + 啟動監控...")
                    start_data_collection('comprehensive')
                    start_web_interface()
                elif choice == '3':
                    print("\n🚀 執行現金流量表收集 + 啟動監控...")
                    start_data_collection('cash_flow')
                    start_web_interface()
                elif choice == '4':
                    print("\n🚀 只啟動Web監控介面...")
                    start_web_interface()
                elif choice == '5':
                    print("\n🚀 只執行資料收集...")
                    collection_mode = input("選擇收集模式 (daily/comprehensive/cash_flow): ").strip()
                    if collection_mode in ['daily', 'comprehensive', 'cash_flow']:
                        start_data_collection(collection_mode)
                    else:
                        print("❌ 無效的收集模式")
                elif choice == '6':
                    print("\n🔍 重新檢查系統狀態...")
                    check_dependencies()
                    check_database()
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
    
    else:
        # 命令列模式
        if args.mode == 'daily':
            start_data_collection('daily')
            start_web_interface()
        elif args.mode == 'comprehensive':
            start_data_collection('comprehensive')
            start_web_interface()
        elif args.mode == 'cash_flow':
            start_data_collection('cash_flow')
            start_web_interface()
        elif args.mode == 'web':
            start_web_interface()
        elif args.mode == 'check':
            check_dependencies()
            check_database()

if __name__ == "__main__":
    main()
