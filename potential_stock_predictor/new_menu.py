#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新選單系統 - 解決所有編碼和顯示問題
"""

import os
import sys
import subprocess

def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """顯示標題"""
    print("=" * 60)
    print("           潛力股預測系統")
    print("=" * 60)
    print("基於台灣股票系統的機器學習預測模組")
    print("預測目標：20日內股價上漲超過5%的股票")
    print("=" * 60)

def print_main_menu():
    """顯示主選單"""
    print("\n主選單")
    print("-" * 40)
    print("1. 預測單一股票")
    print("2. 生成潛力股排行榜")
    print("3. 預測多個股票")
    print("4. 系統測試")
    print("5. 查看說明")
    print("0. 退出系統")
    print("-" * 40)

def execute_command(command, description):
    """執行命令 - 直接顯示輸出"""
    print(f"\n{description}")
    print("=" * 50)
    
    try:
        # 直接執行命令，輸出會直接顯示在控制台
        result = subprocess.run(command, shell=True)
        
        print("=" * 50)
        if result.returncode == 0:
            print("執行成功！")
        else:
            print(f"執行失敗！(退出碼: {result.returncode})")
            
    except Exception as e:
        print(f"執行錯誤: {e}")

def predict_single_stock():
    """預測單一股票"""
    clear_screen()
    print_header()
    print("\n預測單一股票")
    print("-" * 30)
    
    stock_id = input("請輸入股票代碼 (例如: 8299): ").strip()
    
    if not stock_id:
        print("錯誤: 請輸入股票代碼")
        input("\n按 Enter 繼續...")
        return
    
    command = f"python fixed_predict.py {stock_id}"
    execute_command(command, f"預測股票 {stock_id}")
    input("\n按 Enter 繼續...")

def generate_ranking():
    """生成潛力股排行榜"""
    clear_screen()
    print_header()
    print("\n生成潛力股排行榜")
    print("-" * 30)
    
    top_k = input("請輸入排行榜數量 (預設: 20): ").strip()
    
    if not top_k:
        top_k = "20"
    
    try:
        top_k_int = int(top_k)
        if top_k_int <= 0 or top_k_int > 50:
            print("錯誤: 排行榜數量必須在 1-50 之間")
            input("\n按 Enter 繼續...")
            return
    except ValueError:
        print("錯誤: 請輸入有效的數字")
        input("\n按 Enter 繼續...")
        return
    
    command = f"python fixed_predict.py ranking {top_k}"
    execute_command(command, f"生成 TOP {top_k} 潛力股排行榜")
    input("\n按 Enter 繼續...")

def predict_multiple_stocks():
    """預測多個股票"""
    clear_screen()
    print_header()
    print("\n預測多個股票")
    print("-" * 30)
    
    stock_ids = input("請輸入股票代碼 (逗號分隔，例如: 8299,2330,1301): ").strip()
    
    if not stock_ids:
        print("錯誤: 請輸入股票代碼")
        input("\n按 Enter 繼續...")
        return
    
    print(f"\n開始預測多個股票: {stock_ids}")
    print("=" * 50)
    
    for stock_id in stock_ids.split(','):
        stock_id = stock_id.strip()
        if stock_id:
            print(f"\n--- 預測股票 {stock_id} ---")
            command = f"python fixed_predict.py {stock_id}"
            subprocess.run(command, shell=True)
            print("-" * 30)
    
    print("\n所有股票預測完成！")
    input("\n按 Enter 繼續...")

def system_test():
    """系統測試"""
    clear_screen()
    print_header()
    print("\n系統測試")
    print("-" * 30)
    print("1. 測試預測功能 (股票 8299)")
    print("2. 測試排行榜功能 (TOP 5)")
    print("3. 檢查系統狀態")
    print("0. 返回主選單")
    
    choice = input("\n請選擇測試項目 (0-3): ").strip()
    
    if choice == "1":
        command = "python fixed_predict.py 8299"
        execute_command(command, "測試預測功能")
        input("\n按 Enter 繼續...")
    elif choice == "2":
        command = "python fixed_predict.py ranking 5"
        execute_command(command, "測試排行榜功能")
        input("\n按 Enter 繼續...")
    elif choice == "3":
        print("\n檢查系統狀態:")
        print("=" * 30)
        
        # 檢查模型檔案
        import pathlib
        models_dir = pathlib.Path("models")
        if models_dir.exists():
            model_files = list(models_dir.glob("*.pkl"))
            print(f"模型檔案: {len(model_files)} 個")
            for file in model_files[:5]:  # 只顯示前5個
                print(f"  - {file.name}")
        else:
            print("模型目錄不存在")
        
        # 檢查特徵檔案
        features_file = pathlib.Path("data/features/features_basic_2024-06-30.csv")
        if features_file.exists():
            print(f"特徵檔案: 存在")
            try:
                import pandas as pd
                df = pd.read_csv(features_file)
                print(f"  - 股票數量: {len(df)}")
                print(f"  - 特徵數量: {len(df.columns)}")
            except Exception as e:
                print(f"  - 讀取錯誤: {e}")
        else:
            print("特徵檔案: 不存在")
        
        input("\n按 Enter 繼續...")
    elif choice == "0":
        return
    else:
        print("無效選擇")
        input("\n按 Enter 繼續...")

def show_help():
    """顯示說明"""
    clear_screen()
    print_header()
    print("\n使用說明")
    print("-" * 30)
    print("1. 預測單一股票:")
    print("   - 輸入股票代碼 (如: 8299, 2330, 1301)")
    print("   - 系統會顯示預測結果、機率和關鍵特徵")
    print()
    print("2. 生成潛力股排行榜:")
    print("   - 輸入想要的排行榜數量 (1-50)")
    print("   - 系統會按預測機率排序顯示")
    print()
    print("3. 預測多個股票:")
    print("   - 輸入多個股票代碼，用逗號分隔")
    print("   - 系統會依序預測每個股票")
    print()
    print("4. 系統測試:")
    print("   - 測試系統各項功能是否正常")
    print("   - 檢查模型和資料檔案狀態")
    print()
    print("注意事項:")
    print("- 預測結果僅供參考，投資有風險")
    print("- 系統基於歷史資料訓練，不保證未來表現")
    print("- 建議搭配其他分析工具使用")
    
    input("\n按 Enter 繼續...")

def main():
    """主程式"""
    while True:
        clear_screen()
        print_header()
        print_main_menu()
        
        choice = input("請選擇功能 (0-5): ").strip()
        
        if choice == "1":
            predict_single_stock()
        elif choice == "2":
            generate_ranking()
        elif choice == "3":
            predict_multiple_stocks()
        elif choice == "4":
            system_test()
        elif choice == "5":
            show_help()
        elif choice == "0":
            clear_screen()
            print("=" * 60)
            print("           感謝使用潛力股預測系統！")
            print("           預測成功，投資順利！")
            print("=" * 60)
            break
        else:
            print("無效選擇，請輸入 0-5")
            input("\n按 Enter 繼續...")

if __name__ == "__main__":
    main()
