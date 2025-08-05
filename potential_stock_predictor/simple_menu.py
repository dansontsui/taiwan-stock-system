#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版選單系統 - 完全沒有編碼問題
"""

import os
import sys
import subprocess
from pathlib import Path

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
    print("0. 退出系統")
    print("-" * 40)

def run_command_simple(command, description="執行中..."):
    """執行命令並顯示結果 - 簡化版"""
    print(f"\n{description}")
    print("=" * 50)
    
    try:
        # 直接執行，不捕獲輸出，讓結果直接顯示
        result = subprocess.run(command, shell=True, text=True, encoding="utf-8", errors="replace")
        
        if result.returncode == 0:
            print("\n執行成功！")
        else:
            print(f"\n執行失敗！(退出碼: {result.returncode})")
    
    except Exception as e:
        print(f"執行錯誤: {e}")
    
    input("\n按 Enter 繼續...")

def predict_single_stock():
    """預測單一股票"""
    print("\n預測單一股票")
    print("-" * 30)
    
    stock_id = input("請輸入股票代碼 (例如: 8299): ").strip()
    
    if not stock_id:
        print("錯誤: 請輸入股票代碼")
        input("按 Enter 繼續...")
        return
    
    cmd = f"python fixed_predict.py {stock_id}"
    run_command_simple(cmd, f"預測股票 {stock_id}")

def generate_ranking():
    """生成潛力股排行榜"""
    print("\n生成潛力股排行榜")
    print("-" * 30)
    
    top_k = input("請輸入排行榜數量 (預設: 20): ").strip()
    
    if not top_k:
        top_k = "20"
    
    try:
        top_k = int(top_k)
        if top_k <= 0 or top_k > 50:
            print("錯誤: 排行榜數量必須在 1-50 之間")
            input("按 Enter 繼續...")
            return
    except ValueError:
        print("錯誤: 請輸入有效的數字")
        input("按 Enter 繼續...")
        return
    
    cmd = f"python fixed_predict.py ranking {top_k}"
    run_command_simple(cmd, f"生成 TOP {top_k} 潛力股排行榜")

def predict_multiple_stocks():
    """預測多個股票"""
    print("\n預測多個股票")
    print("-" * 30)
    
    stock_ids = input("請輸入股票代碼 (逗號分隔，例如: 8299,2330,1301): ").strip()
    
    if not stock_ids:
        print("錯誤: 請輸入股票代碼")
        input("按 Enter 繼續...")
        return
    
    print(f"\n開始預測多個股票: {stock_ids}")
    print("=" * 50)
    
    for stock_id in stock_ids.split(','):
        stock_id = stock_id.strip()
        if stock_id:
            print(f"\n--- 預測股票 {stock_id} ---")
            cmd = f"python fixed_predict.py {stock_id}"
            subprocess.run(cmd, shell=True)
            print("-" * 30)
    
    print("\n所有股票預測完成！")
    input("按 Enter 繼續...")

def system_test():
    """系統測試"""
    print("\n系統測試")
    print("-" * 30)
    print("1. 測試預測功能 (股票 8299)")
    print("2. 測試排行榜功能 (TOP 5)")
    print("3. 檢查模型檔案")
    print("4. 檢查特徵檔案")
    print("0. 返回主選單")
    
    choice = input("\n請選擇測試項目 (0-4): ").strip()
    
    if choice == "1":
        cmd = "python fixed_predict.py 8299"
        run_command_simple(cmd, "測試預測功能")
    elif choice == "2":
        cmd = "python fixed_predict.py ranking 5"
        run_command_simple(cmd, "測試排行榜功能")
    elif choice == "3":
        print("\n檢查模型檔案:")
        models_dir = Path("models")
        if models_dir.exists():
            for file in models_dir.glob("*.pkl"):
                print(f"  {file.name}")
        else:
            print("  模型目錄不存在")
        input("按 Enter 繼續...")
    elif choice == "4":
        print("\n檢查特徵檔案:")
        features_file = Path("data/features/features_basic_2024-06-30.csv")
        if features_file.exists():
            print(f"  特徵檔案存在: {features_file}")
            # 讀取並顯示基本資訊
            try:
                import pandas as pd
                df = pd.read_csv(features_file)
                print(f"  股票數量: {len(df)}")
                print(f"  特徵數量: {len(df.columns)}")
                print(f"  股票代碼範例: {list(df['stock_id'].head())}")
            except Exception as e:
                print(f"  讀取錯誤: {e}")
        else:
            print("  特徵檔案不存在")
        input("按 Enter 繼續...")
    elif choice == "0":
        return
    else:
        print("無效選擇")
        input("按 Enter 繼續...")

def main():
    """主程式"""
    while True:
        clear_screen()
        print_header()
        print_main_menu()
        
        choice = input("請選擇功能 (0-4): ").strip()
        
        if choice == "1":
            predict_single_stock()
        elif choice == "2":
            generate_ranking()
        elif choice == "3":
            predict_multiple_stocks()
        elif choice == "4":
            system_test()
        elif choice == "0":
            print("\n感謝使用潛力股預測系統！")
            print("預測成功，投資順利！")
            break
        else:
            print("無效選擇，請輸入 0-4")
            input("按 Enter 繼續...")

if __name__ == "__main__":
    main()
