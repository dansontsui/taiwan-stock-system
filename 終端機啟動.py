#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股分析系統終端機啟動
專為終端機使用者設計，不需要Web瀏覽器
"""

import sys
import os
import subprocess
import time
import threading
from datetime import datetime

def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """顯示啟動橫幅"""
    clear_screen()
    print("=" * 80)
    print("🚀 台股分析系統終端機啟動")
    print("=" * 80)
    print("📊 功能包括：")
    print("   • 資料收集 (股價、財務報表、現金流量等)")
    print("   • 終端機監控介面")
    print("   • 每日增量更新")
    print("   • 潛力股分析")
    print("=" * 80)

def run_script_async(script_path, args=None, description=""):
    """異步執行腳本"""
    def run():
        try:
            cmd = [sys.executable, script_path]
            if args:
                cmd.extend(args)
            
            print(f"🔄 開始執行: {description}")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            
            if result.returncode == 0:
                print(f"✅ 完成: {description}")
            else:
                print(f"❌ 失敗: {description}")
                print(f"錯誤: {result.stderr[:200]}...")
                
        except Exception as e:
            print(f"❌ 異常: {description} - {e}")
    
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    return thread

def run_script_sync(script_path, args=None, description="", timeout=3600):
    """同步執行腳本"""
    try:
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        print(f"🔄 執行: {description}")
        print(f"📜 命令: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ 完成: {description} (耗時: {duration:.1f}秒)")
            return True
        else:
            print(f"❌ 失敗: {description} (耗時: {duration:.1f}秒)")
            if result.stderr:
                print(f"錯誤: {result.stderr[:300]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ 超時: {description}")
        return False
    except Exception as e:
        print(f"❌ 異常: {description} - {e}")
        return False

def start_monitoring():
    """啟動監控"""
    print("\n🖥️ 啟動終端機監控...")
    try:
        subprocess.run([sys.executable, '終端機監控.py', '--mode', 'monitor'])
    except KeyboardInterrupt:
        print("\n⚠️ 監控已停止")
    except Exception as e:
        print(f"❌ 監控啟動失敗: {e}")

def show_menu():
    """顯示選單"""
    print("\n📋 請選擇操作:")
    print("1. 🧪 測試所有腳本 (推薦首次使用)")
    print("2. 🔄 每日增量更新 + 監控")
    print("3. 💰 現金流量表收集 + 監控")
    print("4. 🎯 除權除息結果收集 + 監控")
    print("5. 📊 完整資料收集 + 監控")
    print("6. 🖥️ 只啟動終端機監控")
    print("7. 📈 查看資料庫統計")
    print("0. ❌ 退出")
    print("-" * 40)

def test_all_scripts():
    """測試所有腳本"""
    print("\n🧪 開始測試所有腳本...")
    success = run_script_sync('測試所有腳本.py', description="腳本測試", timeout=1800)
    
    if success:
        print("\n✅ 所有腳本測試完成")
        input("按 Enter 鍵繼續...")
    else:
        print("\n❌ 腳本測試失敗，請檢查錯誤訊息")
        input("按 Enter 鍵繼續...")

def daily_update_and_monitor():
    """每日更新並監控"""
    print("\n🔄 執行每日增量更新...")
    
    success = run_script_sync(
        'scripts/collect_daily_update.py',
        ['--batch-size', '3'],
        "每日增量更新",
        timeout=3600
    )
    
    if success:
        print("\n✅ 每日更新完成，啟動監控...")
        time.sleep(2)
        start_monitoring()
    else:
        print("\n❌ 每日更新失敗")
        input("按 Enter 鍵返回選單...")

def cash_flow_and_monitor():
    """現金流量收集並監控"""
    print("\n💰 執行現金流量表收集...")
    
    success = run_script_sync(
        'scripts/collect_cash_flows.py',
        ['--batch-size', '3', '--test'],
        "現金流量表收集",
        timeout=1800
    )
    
    if success:
        print("\n✅ 現金流量收集完成，啟動監控...")
        time.sleep(2)
        start_monitoring()
    else:
        print("\n❌ 現金流量收集失敗")
        input("按 Enter 鍵返回選單...")

def dividend_and_monitor():
    """除權除息收集並監控"""
    print("\n🎯 執行除權除息結果收集...")
    
    success = run_script_sync(
        'scripts/collect_dividend_results.py',
        ['--batch-size', '3', '--test'],
        "除權除息結果收集",
        timeout=1800
    )
    
    if success:
        print("\n✅ 除權除息收集完成，啟動監控...")
        time.sleep(2)
        start_monitoring()
    else:
        print("\n❌ 除權除息收集失敗")
        input("按 Enter 鍵返回選單...")

def comprehensive_collection():
    """完整資料收集"""
    print("\n📊 執行完整資料收集...")
    print("⚠️ 這可能需要1-3小時，請確保網路穩定")
    
    confirm = input("確定要繼續嗎？(y/N): ").strip().lower()
    if confirm != 'y':
        return
    
    # 執行多個收集腳本
    scripts = [
        ('scripts/collect_stock_prices_smart.py', ['--batch-size', '3'], '股價收集'),
        ('scripts/collect_monthly_revenue.py', ['--batch-size', '3'], '月營收收集'),
        ('scripts/collect_financial_statements.py', ['--batch-size', '3'], '財務報表收集'),
        ('scripts/collect_balance_sheets.py', ['--batch-size', '3'], '資產負債表收集'),
        ('scripts/collect_cash_flows.py', ['--batch-size', '3'], '現金流量表收集'),
        ('scripts/collect_dividend_results.py', ['--batch-size', '3'], '除權除息收集'),
        ('scripts/collect_dividend_data.py', ['--batch-size', '3'], '股利政策收集'),
    ]
    
    completed = 0
    total = len(scripts)
    
    for script_path, args, description in scripts:
        print(f"\n📋 進度: {completed+1}/{total} - {description}")
        success = run_script_sync(script_path, args, description, timeout=3600)
        
        if success:
            completed += 1
        
        # 腳本間休息
        if completed < total:
            print("⏳ 休息30秒...")
            time.sleep(30)
    
    print(f"\n🎯 完整收集完成: {completed}/{total} 個腳本成功")
    
    if completed > 0:
        print("✅ 啟動監控...")
        time.sleep(2)
        start_monitoring()
    else:
        print("❌ 所有收集都失敗了")
        input("按 Enter 鍵返回選單...")

def show_database_stats():
    """顯示資料庫統計"""
    print("\n📊 查看資料庫統計...")
    run_script_sync('終端機監控.py', ['--mode', 'stats'], "資料庫統計")

def main():
    """主函數"""
    print_banner()
    
    try:
        while True:
            show_menu()
            choice = input("請輸入選項 (0-7): ").strip()
            
            if choice == '0':
                print("👋 再見！")
                break
            elif choice == '1':
                test_all_scripts()
            elif choice == '2':
                daily_update_and_monitor()
            elif choice == '3':
                cash_flow_and_monitor()
            elif choice == '4':
                dividend_and_monitor()
            elif choice == '5':
                comprehensive_collection()
            elif choice == '6':
                print("\n🖥️ 啟動終端機監控...")
                start_monitoring()
            elif choice == '7':
                show_database_stats()
            else:
                print("❌ 無效選項，請重新選擇")
            
            # 返回選單前清除螢幕
            if choice != '0':
                time.sleep(1)
                clear_screen()
                print_banner()
                
    except KeyboardInterrupt:
        print("\n👋 程式已退出")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")

if __name__ == "__main__":
    main()
