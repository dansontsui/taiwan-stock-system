#!/usr/bin/env python3
"""
潛力股預測系統互動選單

提供簡單易用的選單介面，無需記住複雜指令
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """顯示標題"""
    print("🚀 潛力股預測系統")
    print("=" * 50)
    print("基於台灣股票系統的機器學習預測模組")
    print("預測目標：20日內股價上漲超過5%的股票")
    print("=" * 50)

def print_main_menu():
    """顯示主選單"""
    print("\n📋 主選單")
    print("-" * 30)
    print("1. 🧪 系統測試")
    print("2. 🔬 資料處理")
    print("3. 🤖 模型訓練")
    print("4. 🔮 執行預測")
    print("5. 📊 查看結果")
    print("6. ⚙️  系統設定")
    print("7. 📚 說明文檔")
    print("0. 🚪 退出系統")
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
    print("\n🤖 模型訓練選單")
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
    print("\n🔮 執行預測選單")
    print("-" * 30)
    print("1. 生成潛力股排行榜 (簡化版)")
    print("2. 預測特定股票 (簡化版)")
    print("3. 預測特定股票")
    print("4. 批次預測所有股票")
    print("5. 生成潛力股排行榜")
    print("6. 預測並儲存結果")
    print("0. 返回主選單")
    print("-" * 30)

def print_result_menu():
    """顯示結果查看選單"""
    print("\n📊 查看結果選單")
    print("-" * 30)
    print("1. 查看最新排行榜")
    print("2. 查看歷史預測")
    print("3. 模型性能報告")
    print("4. 特徵重要性分析")
    print("0. 返回主選單")
    print("-" * 30)

def run_command(command, description="執行中..."):
    """執行命令並顯示結果"""
    print(f"\n⏳ {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 執行成功！")
            if result.stdout:
                print("\n📄 輸出結果:")
                print(result.stdout)
        else:
            print("❌ 執行失敗！")
            if result.stderr:
                print("\n🚨 錯誤訊息:")
                print(result.stderr)
    
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
    
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
            print("❌ 無效選擇，請重新輸入")
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
            cmd = f"python simple_features.py {date}"
            run_command(cmd, "生成特徵資料 (簡化版)")

        elif choice == "2":
            date = get_user_input("請輸入特徵計算日期 (YYYY-MM-DD)", "2024-06-30")
            stock_ids = get_user_input("請輸入股票代碼 (逗號分隔，留空表示所有股票)", "")

            cmd = f"python main.py generate-features --date {date}"
            if stock_ids:
                cmd += f" --stock-ids {stock_ids}"

            run_command(cmd, "生成特徵資料 (完整版)")

        elif choice == "3":
            start_date = get_user_input("請輸入開始日期 (YYYY-MM-DD)", "2022-01-01")
            end_date = get_user_input("請輸入結束日期 (YYYY-MM-DD)", "2024-06-30")
            frequency = get_user_input("請輸入頻率 (monthly/quarterly)", "quarterly")
            
            cmd = f"python main.py generate-targets --start-date {start_date} --end-date {end_date} --frequency {frequency}"
            run_command(cmd, "生成目標變數")
            
        elif choice == "4":
            print("\n⏳ 批次處理所有資料...")
            print("這將依序執行：特徵生成 → 目標變數生成")
            confirm = input("確定要繼續嗎？(y/N): ").strip().lower()

            if confirm == 'y':
                run_command("python simple_features.py 2024-06-30", "生成特徵資料")
                run_command("python main.py generate-targets --start-date 2022-01-01 --end-date 2024-06-30 --frequency quarterly", "生成目標變數")

        elif choice == "5":
            run_command("ls -la data/", "檢查資料目錄")
            
        elif choice == "0":
            break
        else:
            print("❌ 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def handle_model_menu():
    """處理模型訓練選單"""
    while True:
        clear_screen()
        print_header()
        print_model_menu()
        
        choice = input("請選擇功能 (0-5): ").strip()

        if choice == "1":
            features_file = get_user_input("特徵檔案路徑", "data/features/features_2024-06-30.csv")
            targets_file = get_user_input("目標變數檔案路徑", "data/targets/targets_quarterly_2024-06-30.csv")

            cmd = f"python simple_train.py {features_file} {targets_file}"
            run_command(cmd, "訓練基本模型 (簡化版)")

        elif choice == "2":
            features_file = get_user_input("特徵檔案路徑", "data/features/features_2024-06-30.csv")
            targets_file = get_user_input("目標變數檔案路徑", "data/targets/targets_quarterly_2024-06-30.csv")

            cmd = f"python main.py train-models --features-file {features_file} --targets-file {targets_file} --models random_forest"
            run_command(cmd, "訓練基本模型")

        elif choice == "3":
            features_file = get_user_input("特徵檔案路徑", "data/features/features_2024-06-30.csv")
            targets_file = get_user_input("目標變數檔案路徑", "data/targets/targets_quarterly_2024-06-30.csv")
            
            cmd = f"python main.py train-models --features-file {features_file} --targets-file {targets_file}"
            run_command(cmd, "訓練所有模型")
            
        elif choice == "3":
            print("⚠️ 超參數調校功能需要安裝 optuna")
            print("請先執行: pip install optuna")
            input("按 Enter 繼續...")
            
        elif choice == "4":
            run_command("ls -la models/", "查看已訓練的模型")
            
        elif choice == "0":
            break
        else:
            print("❌ 無效選擇，請重新輸入")
            input("按 Enter 繼續...")

def handle_predict_menu():
    """處理預測選單"""
    while True:
        clear_screen()
        print_header()
        print_predict_menu()
        
        choice = input("請選擇功能 (0-6): ").strip()

        if choice == "1":
            model = get_user_input("請選擇模型", "random_forest")
            top_k = get_user_input("排行榜數量", "20")

            cmd = f"python simple_predict.py ranking {model} {top_k}"
            run_command(cmd, "生成潛力股排行榜 (簡化版)")

        elif choice == "2":
            stock_ids = get_user_input("請輸入股票代碼 (逗號分隔)", "2330,2317,2454")
            model = get_user_input("請選擇模型", "random_forest")

            cmd = f"python simple_predict.py specific {model}"
            # 需要手動輸入股票代碼，所以使用互動模式
            print(f"\n⏳ 執行預測特定股票...")
            print("=" * 50)
            print("提示：程式會要求輸入股票代碼，請輸入:", stock_ids)
            input("按 Enter 繼續...")
            run_command("python simple_predict.py", "預測特定股票 (簡化版)")

        elif choice == "3":
            stock_ids = get_user_input("請輸入股票代碼 (逗號分隔)", "2330,2317,2454")
            model = get_user_input("請選擇模型", "random_forest")
            date = get_user_input("預測日期 (YYYY-MM-DD)", datetime.now().strftime('%Y-%m-%d'))

            cmd = f"python main.py predict --stock-ids {stock_ids} --model {model} --date {date}"
            run_command(cmd, "預測特定股票")

        elif choice == "4":
            model = get_user_input("請選擇模型", "random_forest")
            date = get_user_input("預測日期 (YYYY-MM-DD)", datetime.now().strftime('%Y-%m-%d'))
            
            cmd = f"python main.py predict --model {model} --date {date}"
            run_command(cmd, "批次預測所有股票")
            
        elif choice == "3":
            model = get_user_input("請選擇模型", "random_forest")
            top_k = get_user_input("排行榜數量", "20")
            date = get_user_input("預測日期 (YYYY-MM-DD)", datetime.now().strftime('%Y-%m-%d'))
            
            cmd = f"python main.py ranking --model {model} --top-k {top_k} --date {date}"
            run_command(cmd, "生成潛力股排行榜")
            
        elif choice == "4":
            model = get_user_input("請選擇模型", "random_forest")
            output = get_user_input("輸出檔案名稱", f"predictions_{datetime.now().strftime('%Y%m%d')}.csv")
            
            cmd = f"python main.py predict --model {model} --output data/predictions/{output}"
            run_command(cmd, "預測並儲存結果")
            
        elif choice == "0":
            break
        else:
            print("❌ 無效選擇，請重新輸入")
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
            print("📊 特徵重要性分析需要訓練完成的模型")
            print("請先完成模型訓練")
            input("按 Enter 繼續...")
            
        elif choice == "0":
            break
        else:
            print("❌ 無效選擇，請重新輸入")
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
        print("\n🚀 快速上手指南")
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
            print("\n👋 感謝使用潛力股預測系統！")
            print("🎯 預測成功，投資順利！")
            break
        else:
            print("❌ 無效選擇，請輸入 0-7")
            input("按 Enter 繼續...")

if __name__ == "__main__":
    main()
