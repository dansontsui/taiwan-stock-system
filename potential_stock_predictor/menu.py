#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
潛力股預測系統互動選單

提供簡單易用的選單介面，無需記住複雜指令
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 設定輸出編碼
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """顯示標題"""
    print(" 潛力股預測系統")
    print("=" * 50)
    print("基於台灣股票系統的機器學習預測模組")
    print("預測目標：20日內股價上漲超過5%的股票")
    print("=" * 50)

def print_main_menu():
    """顯示主選單"""
    print("\n主選單")
    print("-" * 30)
    print("1. 系統測試")
    print("2. 資料處理")
    print("3. 模型訓練")
    print("4. 執行預測")
    print("5. 查看結果")
    print("6. 系統設定")
    print("7. 說明文檔")
    print("0. 退出系統")
    print("-" * 30)

def print_test_menu():
    """顯示測試選單"""
    print("\n🧪 系統測試選單")
    print("-" * 30)
    print("1. 快速測試 (基本功能)")
    print("2. 完整測試 (所有功能)")
    print("3. 基本示範 (機器學習)")
    print("4. 檢查依賴套件")
    print("0. 返回主選單")
    print("-" * 30)

def print_data_menu():
    """顯示資料處理選單"""
    print("\n🔬 資料處理選單")
    print("-" * 30)
    print("1. 生成特徵資料 (簡化版)")
    print("2. 生成特徵資料 (完整版)")
    print("3. 生成目標變數")
    print("4. 批次處理所有資料")
    print("5. 檢查資料品質")
    print("0. 返回主選單")
    print("-" * 30)

def print_model_menu():
    """顯示模型訓練選單"""
    print("\n 模型訓練選單")
    print("-" * 30)
    print("1. 訓練基本模型 (簡化版)")
    print("2. 訓練基本模型 (Random Forest)")
    print("3. 訓練所有模型")
    print("4. 超參數調校")
    print("5. 模型評估")
    print("0. 返回主選單")
    print("-" * 30)

def print_predict_menu():
    """顯示預測選單"""
    print("\n執行預測選單 (修復版)")
    print("-" * 30)
    print("1. 生成潛力股排行榜 (推薦)")
    print("2. 預測單一股票 (推薦)")
    print("3. 預測多個股票")
    print("4. 批次預測所有股票")
    print("5. 生成完整排行榜")
    print("6. 預測並顯示詳細結果")
    print("0. 返回主選單")
    print("-" * 30)

def print_result_menu():
    """顯示結果查看選單"""
    print("\n 查看結果選單")
    print("-" * 30)
    print("1. 查看最新排行榜")
    print("2. 查看歷史預測")
    print("3. 模型性能報告")
    print("4. 特徵重要性分析")
    print("0. 返回主選單")
    print("-" * 30)

def run_command(command, description="執行中..."):
    """執行命令並顯示結果"""
    print(f"\n {description}")
    print("=" * 50)

    try:
        # 使用實時輸出模式
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode == 0:
            print("OK 執行成功！")

            # 顯示標準輸出
            if result.stdout and result.stdout.strip():
                print("\n輸出結果:")
                print(result.stdout)

            # 也顯示標準錯誤（可能包含日誌信息）
            if result.stderr and result.stderr.strip():
                print("\n詳細信息:")
                print(result.stderr)

        else:
            print("X 執行失敗！")

            # 顯示錯誤信息
            if result.stderr and result.stderr.strip():
                print("\n 錯誤訊息:")
                print(result.stderr)

            # 也顯示可能的輸出
            if result.stdout and result.stdout.strip():
                print("\n部分輸出:")
                print(result.stdout)

    except Exception as e:
        print(f"X 執行錯誤: {e}")

    input("\n按 Enter 繼續...")

def run_command_live(command, description="執行中..."):
    """執行命令並實時顯示結果"""
    print(f"\n {description}")
    print("=" * 50)

    try:
        # 直接執行，不捕獲輸出，讓結果直接顯示到控制台
        result = subprocess.run(command, shell=True, text=True)

        if result.returncode == 0:
            print("\nOK 執行成功！")
        else:
            print(f"\nX 執行失敗！(退出碼: {result.returncode})")

    except Exception as e:
        print(f"X 執行錯誤: {e}")

    input("\n按 Enter 繼續...")

def get_user_input(prompt, default=None):
    """獲取用戶輸入"""
    if default:
        user_input = input(f"{prompt} (預設: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def handle_test_menu():
    """處理測試選單"""
    while True:
        clear_screen()
        print_header()
        print_test_menu()
        
        choice = input("請選擇功能 (0-4): ").strip()
        
        if choice == "1":
            run_command("python quick_test.py", "執行快速測試")
        elif choice == "2":
            run_command("python simple_demo.py", "執行完整測試")
        elif choice == "3":
            run_command("python basic_demo.py", "執行基本示範")
        elif choice == "4":
            run_command("pip list | grep -E '(pandas|numpy|scikit-learn|matplotlib)'", "檢查依賴套件")
        elif choice == "0":
            break
        else:
            print("X 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def handle_data_menu():
    """處理資料處理選單"""
    while True:
        clear_screen()
        print_header()
        print_data_menu()
        
        choice = input("請選擇功能 (0-5): ").strip()

        if choice == "1":
            date = get_user_input("請輸入特徵計算日期 (YYYY-MM-DD)", "2024-06-30")
            cmd = f"python simple_features_basic.py {date}"
            run_command_live(cmd, "生成特徵資料 (簡化版)")

        elif choice == "2":
            date = get_user_input("請輸入特徵計算日期 (YYYY-MM-DD)", "2024-06-30")
            stock_ids = get_user_input("請輸入股票代碼 (逗號分隔，留空表示所有股票)", "")

            if stock_ids:
                # 如果指定了股票，使用簡化版系統（更可靠）
                cmd = f"python simple_features_basic.py {date} {stock_ids}"
                run_command_live(cmd, "生成特徵資料 (指定股票)")
            else:
                # 如果是所有股票，先嘗試原始系統
                print("\n選擇特徵生成方式:")
                print("1. 使用原始系統 (30個特徵，可能有相容性問題)")
                print("2. 使用簡化系統 (16個特徵，更穩定)")

                method = input("請選擇 (1-2，預設2): ").strip()

                if method == "1":
                    cmd = f"python main.py generate-features --date {date}"
                    run_command_live(cmd, "生成特徵資料 (原始系統)")
                else:
                    cmd = f"python simple_features_basic.py {date}"
                    run_command_live(cmd, "生成特徵資料 (簡化系統)")

        elif choice == "3":
            start_date = get_user_input("請輸入開始日期 (YYYY-MM-DD)", "2022-01-01")
            end_date = get_user_input("請輸入結束日期 (YYYY-MM-DD)", "2024-06-30")
            frequency = get_user_input("請輸入頻率 (monthly/quarterly)", "quarterly")

            print("\n選擇目標變數生成方式:")
            print("1. 使用原始系統 (可能沒有進度顯示)")
            print("2. 使用進度顯示版本 (推薦)")

            method = input("請選擇 (1-2，預設2): ").strip()

            if method == "1":
                cmd = f"python main.py generate-targets --start-date {start_date} --end-date {end_date} --frequency {frequency}"
                run_command_live(cmd, "生成目標變數 (原始系統)")
            else:
                cmd = f"python generate_targets_with_progress.py --start-date {start_date} --end-date {end_date} --frequency {frequency}"
                run_command_live(cmd, "生成目標變數 (進度顯示版)")
            
        elif choice == "4":
            print("\n 批次處理所有資料...")
            print("這將依序執行：特徵生成 → 目標變數生成")
            confirm = input("確定要繼續嗎？(y/N): ").strip().lower()

            if confirm == 'y':
                run_command_live("python simple_features_basic.py 2024-06-30", "生成特徵資料")
                run_command_live("python main.py generate-targets --start-date 2022-01-01 --end-date 2024-06-30 --frequency quarterly", "生成目標變數")

        elif choice == "5":
            print("\n檢查資料品質")
            print("=" * 30)

            # 檢查資料目錄
            import pathlib
            data_dir = pathlib.Path("data")
            if data_dir.exists():
                print("資料目錄結構:")
                for subdir in ["features", "targets", "predictions"]:
                    subpath = data_dir / subdir
                    if subpath.exists():
                        files = list(subpath.glob("*.csv"))
                        print(f"  {subdir}/: {len(files)} 個檔案")
                        for file in files[:3]:  # 只顯示前3個
                            print(f"    - {file.name}")
                    else:
                        print(f"  {subdir}/: 不存在")
            else:
                print("資料目錄不存在")

            input("\n按 Enter 繼續...")
            
        elif choice == "0":
            break
        else:
            print("X 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def handle_model_menu():
    """處理模型訓練選單"""
    while True:
        clear_screen()
        print_header()
        print_model_menu()
        
        choice = input("請選擇功能 (0-5): ").strip()

        if choice == "1":
            features_file = get_user_input("特徵檔案路徑", "data/features/features_basic_2024-06-30.csv")

            cmd = f"python simple_train_basic.py {features_file}"
            run_command_live(cmd, "訓練基本模型 (簡化版)")

        elif choice == "2":
            features_file = get_user_input("特徵檔案路徑", "data/features/features_2024-06-30.csv")
            targets_file = get_user_input("目標變數檔案路徑", "data/targets/targets_quarterly_2024-06-30.csv")

            cmd = f"python main.py train-models --features-file {features_file} --targets-file {targets_file} --models random_forest"
            run_command_live(cmd, "訓練基本模型")

        elif choice == "3":
            features_file = get_user_input("特徵檔案路徑", "data/features/features_2024-06-30.csv")
            targets_file = get_user_input("目標變數檔案路徑", "data/targets/targets_quarterly_2024-06-30.csv")
            
            cmd = f"python main.py train-models --features-file {features_file} --targets-file {targets_file}"
            run_command(cmd, "訓練所有模型")
            
        elif choice == "3":
            print("WARNING 超參數調校功能需要安裝 optuna")
            print("請先執行: pip install optuna")
            input("按 Enter 繼續...")
            
        elif choice == "4":
            run_command("ls -la models/", "查看已訓練的模型")
            
        elif choice == "0":
            break
        else:
            print("X 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def handle_predict_menu():
    """處理預測選單"""
    while True:
        clear_screen()
        print_header()
        print_predict_menu()
        
        choice = input("請選擇功能 (0-6): ").strip()

        if choice == "1":
            top_k = get_user_input("排行榜數量", "20")

            cmd = f"python fixed_predict.py ranking {top_k}"
            run_command_live(cmd, f"生成 TOP {top_k} 潛力股排行榜 (修復版)")

        elif choice == "2":
            stock_id = get_user_input("請輸入股票代碼", "8299")

            cmd = f"python fixed_predict.py {stock_id}"
            run_command_live(cmd, f"預測股票 {stock_id} (修復版)")

        elif choice == "3":
            stock_ids = get_user_input("請輸入股票代碼 (逗號分隔)", "8299,2330,1301")

            print(f"\n預測多個股票: {stock_ids}")
            print("=" * 50)

            # 分別預測每個股票
            for stock_id in stock_ids.split(','):
                stock_id = stock_id.strip()
                if stock_id:
                    cmd = f"python fixed_predict.py {stock_id}"
                    print(f"\n--- 預測股票 {stock_id} ---")
                    run_command_live(cmd, f"預測股票 {stock_id}")

            input("\n所有預測完成，按 Enter 繼續...")

        elif choice == "4":
            print("\n批次預測所有股票 (使用修復版)")
            print("=" * 50)
            print("注意: 這會預測所有47檔股票，需要較長時間")
            confirm = input("確定要繼續嗎？(y/N): ").strip().lower()

            if confirm == 'y':
                cmd = f"python fixed_predict.py ranking 47"
                run_command_live(cmd, "批次預測所有股票")
            else:
                print("已取消批次預測")
                input("按 Enter 繼續...")

        elif choice == "5":
            top_k = get_user_input("排行榜數量", "20")

            cmd = f"python fixed_predict.py ranking {top_k}"
            run_command_live(cmd, f"生成 TOP {top_k} 潛力股排行榜")

        elif choice == "6":
            stock_id = get_user_input("請輸入股票代碼", "8299")

            print(f"\n預測股票 {stock_id} 詳細分析")
            print("=" * 50)

            cmd = f"python fixed_predict.py {stock_id}"
            run_command_live(cmd, f"預測股票 {stock_id} 詳細分析")

            print(f"\n詳細分析完成")
            input("按 Enter 繼續...")
            
        elif choice == "0":
            break
        else:
            print("X 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def handle_result_menu():
    """處理結果查看選單"""
    while True:
        clear_screen()
        print_header()
        print_result_menu()
        
        choice = input("請選擇功能 (0-4): ").strip()
        
        if choice == "1":
            run_command("ls -la data/rankings/ | tail -5", "查看最新排行榜檔案")
            
        elif choice == "2":
            run_command("ls -la data/predictions/ | tail -10", "查看歷史預測檔案")
            
        elif choice == "3":
            run_command("ls -la models/ && cat models/training_results_*.json 2>/dev/null | head -20", "查看模型性能")
            
        elif choice == "4":
            print(" 特徵重要性分析需要訓練完成的模型")
            print("請先完成模型訓練")
            input("按 Enter 繼續...")
            
        elif choice == "0":
            break
        else:
            print("X 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def show_help():
    """顯示說明文檔"""
    clear_screen()
    print_header()
    print("\n📚 說明文檔")
    print("-" * 50)
    print("1. README.md - 完整使用說明")
    print("2. INSTALL.md - 安裝指南")
    print("3. 線上文檔 - GitHub 專案頁面")
    print("4. 快速上手指南")
    print("0. 返回主選單")
    print("-" * 50)
    
    choice = input("請選擇查看內容 (0-4): ").strip()
    
    if choice == "1":
        run_command("cat README.md", "顯示 README.md")
    elif choice == "2":
        run_command("cat INSTALL.md", "顯示 INSTALL.md")
    elif choice == "3":
        print("📖 請在瀏覽器中訪問專案頁面獲取最新文檔")
        input("按 Enter 繼續...")
    elif choice == "4":
        print("\n 快速上手指南")
        print("=" * 50)
        print("1. 首次使用：")
        print("   選單 1 → 1 (快速測試)")
        print("2. 準備資料：")
        print("   選單 2 → 3 (批次處理所有資料)")
        print("3. 訓練模型：")
        print("   選單 3 → 1 (訓練基本模型)")
        print("4. 執行預測：")
        print("   選單 4 → 3 (生成潛力股排行榜)")
        print("5. 查看結果：")
        print("   選單 5 → 1 (查看最新排行榜)")
        input("\n按 Enter 繼續...")

def main():
    """主程式"""
    while True:
        clear_screen()
        print_header()
        print_main_menu()
        
        choice = input("請選擇功能 (0-7): ").strip()
        
        if choice == "1":
            handle_test_menu()
        elif choice == "2":
            handle_data_menu()
        elif choice == "3":
            handle_model_menu()
        elif choice == "4":
            handle_predict_menu()
        elif choice == "5":
            handle_result_menu()
        elif choice == "6":
            print("\n⚙️ 系統設定")
            print("配置檔案位置: config/config.py")
            print("可以編輯該檔案來調整系統參數")
            input("按 Enter 繼續...")
        elif choice == "7":
            show_help()
        elif choice == "0":
            print("\n 感謝使用潛力股預測系統！")
            print(" 預測成功，投資順利！")
            break
        else:
            print("X 無效選擇，請輸入 0-7")
            input("按 Enter 繼續...")

if __name__ == "__main__":
    main()
