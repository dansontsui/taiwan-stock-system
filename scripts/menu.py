#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股資料收集系統 - 互動式選單
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta

def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """顯示標題"""
    print("=" * 60)
    print(" 台股歷史股價系統 - 互動式選單")
    print("=" * 60)
    print()

def print_menu():
    """顯示主選單"""
    print(" 請選擇收集模式:")
    print()
    print("1️⃣  預設清單 (24檔) - 測試模式")
    print("2️⃣  主要股票 (3,782檔) - 測試模式 ⭐ 推薦")
    print("3️⃣  主要股票 (3,782檔) - 完整收集")
    print("4️⃣  分批收集 - 測試模式  最推薦")
    print("5️⃣  分批收集 - 完整收集")
    print("6️⃣  指定股票收集")
    print("7️⃣  指定時間範圍收集")
    print("8️⃣  系統管理")
    print("9️⃣  查看說明文檔")
    print("0️⃣  退出")
    print()

def get_user_input(prompt, valid_options=None):
    """獲取用戶輸入"""
    while True:
        try:
            user_input = input(prompt).strip()
            if valid_options and user_input not in valid_options:
                print(f" 請輸入有效選項: {', '.join(valid_options)}")
                continue
            return user_input
        except KeyboardInterrupt:
            print("\n👋 再見！")
            sys.exit(0)

def run_command(command, description):
    """執行命令"""
    print(f"\n {description}")
    print(f" 執行命令: {command}")
    print("-" * 60)
    
    # 詢問是否確認執行
    confirm = get_user_input("確定要執行嗎？(y/n): ", ["y", "n", "Y", "N"])
    if confirm.lower() != 'y':
        print(" 已取消執行")
        return False
    
    try:
        # 執行命令
        result = subprocess.run(command, shell=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("\n 執行完成！")
        else:
            print(f"\n 執行失敗，返回碼: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"\n 執行錯誤: {e}")
        return False

def option_1():
    """預設清單 - 測試模式"""
    command = "python scripts/collect_data.py --test --skip-existing"
    description = "收集預設清單 (24檔精選股票) - 測試模式"
    run_command(command, description)

def option_2():
    """主要股票 - 測試模式"""
    command = "python scripts/collect_data.py --main-stocks --test --skip-existing"
    description = "收集主要股票 (上市+上櫃+00開頭ETF，3,782檔) - 測試模式"
    run_command(command, description)

def option_3():
    """主要股票 - 完整收集"""
    print("\n  注意事項:")
    print("- 需要約38,000次API請求")
    print("- 預估時間: 60-100小時")
    print("- 建議使用分批收集模式")
    print()
    
    confirm = get_user_input("確定要使用完整收集模式嗎？建議選擇分批收集 (4或5)。(y/n): ", ["y", "n", "Y", "N"])
    if confirm.lower() != 'y':
        print(" 建議使用選項 4 或 5 的分批收集模式")
        return
    
    command = "python scripts/collect_data.py --main-stocks --skip-existing"
    description = "收集主要股票 (上市+上櫃+00開頭ETF，3,782檔) - 完整收集"
    run_command(command, description)

def option_4():
    """分批收集 - 測試模式"""
    print("\n 分批收集的優勢:")
    print("-  自動處理API限制")
    print("-  智能等待功能")
    print("-  自動跳過已有資料")
    print("-  斷點續傳")
    print()
    
    command = "python scripts/collect_batch.py --test"
    description = "分批收集主要股票 - 測試模式 (最推薦)"
    run_command(command, description)

def option_5():
    """分批收集 - 完整收集"""
    print("\n 分批收集 - 完整模式:")
    print("-  收集範圍: 上市+上櫃+00開頭ETF (3,782檔)")
    print("-  預估時間: 15-20小時 (自動處理)")
    print("- 🤖 全自動: 無需人工干預")
    print()
    
    batch_size = get_user_input("請輸入批次大小 (預設200，建議100-300): ") or "200"
    
    command = f"python scripts/collect_batch.py --batch-size {batch_size}"
    description = f"分批收集主要股票 - 完整收集 (批次大小: {batch_size})"
    run_command(command, description)

def option_6():
    """指定股票收集"""
    print("\n 指定股票收集:")
    print("請輸入股票代碼，用空格分隔")
    print("範例: 2330 8299 0050 0056")
    print()
    
    stocks = get_user_input("股票代碼: ")
    if not stocks:
        print(" 未輸入股票代碼")
        return
    
    # 詢問是否為測試模式
    test_mode = get_user_input("是否為測試模式？(y/n): ", ["y", "n", "Y", "N"])
    test_flag = "--test" if test_mode.lower() == 'y' else ""
    
    command = f"python scripts/collect_data.py --stocks {stocks} {test_flag} --skip-existing"
    description = f"收集指定股票: {stocks}"
    run_command(command, description)

def option_7():
    """指定時間範圍收集"""
    print("\n 指定時間範圍收集:")
    print()
    
    # 選擇收集範圍
    print("選擇收集範圍:")
    print("1. 預設清單 (24檔)")
    print("2. 主要股票 (3,782檔)")
    print("3. 指定股票")
    
    range_choice = get_user_input("請選擇 (1-3): ", ["1", "2", "3"])
    
    # 設定收集範圍參數
    if range_choice == "1":
        range_param = ""
        range_desc = "預設清單"
    elif range_choice == "2":
        range_param = "--main-stocks"
        range_desc = "主要股票"
    else:
        stocks = get_user_input("請輸入股票代碼 (用空格分隔): ")
        if not stocks:
            print(" 未輸入股票代碼")
            return
        range_param = f"--stocks {stocks}"
        range_desc = f"指定股票: {stocks}"
    
    # 輸入時間範圍
    print("\n時間範圍設定:")
    print("格式: YYYY-MM-DD")
    
    start_date = get_user_input("開始日期 (預設2015-01-01): ") or "2015-01-01"
    end_date = get_user_input("結束日期 (預設今天): ") or datetime.now().strftime("%Y-%m-%d")
    
    command = f"python scripts/collect_data.py {range_param} --start-date {start_date} --end-date {end_date} --skip-existing"
    description = f"收集 {range_desc} 的資料 ({start_date} ~ {end_date})"
    run_command(command, description)

def option_8():
    """系統管理"""
    clear_screen()
    print_header()
    print("🛠️  系統管理:")
    print()
    print("1️⃣  啟動Web系統")
    print("2️⃣  查看資料庫統計")
    print("3️⃣  測試跳過功能")
    print("4️⃣  測試智能等待")
    print("5️⃣  返回主選單")
    print()
    
    choice = get_user_input("請選擇 (1-5): ", ["1", "2", "3", "4", "5"])
    
    if choice == "1":
        command = "python run.py"
        description = "啟動Web系統 (http://localhost:5000)"
        run_command(command, description)
    elif choice == "2":
        command = "python scripts/test_skip_existing.py"
        description = "查看資料庫統計資訊"
        run_command(command, description)
    elif choice == "3":
        command = "python scripts/test_skip_existing.py"
        description = "測試跳過已有資料功能"
        run_command(command, description)
    elif choice == "4":
        command = "python scripts/test_smart_wait.py"
        description = "測試智能等待功能"
        run_command(command, description)
    elif choice == "5":
        return

def option_9():
    """查看說明文檔"""
    clear_screen()
    print_header()
    print("📚 說明文檔:")
    print()
    print("1️⃣  README.md - 系統總覽")
    print("2️⃣  COLLECTION_MODES.md - 收集模式說明")
    print("3️⃣  SMART_WAIT_GUIDE.md - 智能等待功能")
    print("4️⃣  SKIP_EXISTING_GUIDE.md - 跳過已有資料功能")
    print("5️⃣  返回主選單")
    print()
    
    choice = get_user_input("請選擇 (1-5): ", ["1", "2", "3", "4", "5"])
    
    docs = {
        "1": "README.md",
        "2": "COLLECTION_MODES.md", 
        "3": "SMART_WAIT_GUIDE.md",
        "4": "SKIP_EXISTING_GUIDE.md"
    }
    
    if choice in docs:
        doc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), docs[choice])
        if os.path.exists(doc_path):
            print(f"\n📖 開啟文檔: {docs[choice]}")
            if sys.platform.startswith('darwin'):  # macOS
                os.system(f"open '{doc_path}'")
            elif sys.platform.startswith('win'):   # Windows
                os.system(f"start '{doc_path}'")
            else:  # Linux
                os.system(f"xdg-open '{doc_path}'")
        else:
            print(f" 文檔不存在: {docs[choice]}")
    elif choice == "5":
        return

def main():
    """主函數"""
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = get_user_input("請選擇 (0-9): ", [str(i) for i in range(10)])
        
        if choice == "0":
            print("\n👋 感謝使用台股歷史股價系統！")
            break
        elif choice == "1":
            option_1()
        elif choice == "2":
            option_2()
        elif choice == "3":
            option_3()
        elif choice == "4":
            option_4()
        elif choice == "5":
            option_5()
        elif choice == "6":
            option_6()
        elif choice == "7":
            option_7()
        elif choice == "8":
            option_8()
        elif choice == "9":
            option_9()
        
        if choice != "0":
            input("\n按 Enter 鍵繼續...")

if __name__ == "__main__":
    main()
