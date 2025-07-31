#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速預測工具 - 直接可用，無選單問題
"""

import sys
import subprocess

def show_usage():
    """顯示使用說明"""
    print("=" * 60)
    print("           潛力股預測系統 - 快速工具")
    print("=" * 60)
    print("\n使用方法:")
    print("  python quick_predict.py <功能> [參數]")
    print("\n功能選項:")
    print("  stock <股票代碼>     - 預測單一股票")
    print("  ranking [數量]       - 生成排行榜 (預設20)")
    print("  test                 - 系統測試")
    print("\n範例:")
    print("  python quick_predict.py stock 8299")
    print("  python quick_predict.py stock 2330")
    print("  python quick_predict.py ranking 10")
    print("  python quick_predict.py ranking")
    print("  python quick_predict.py test")
    print("=" * 60)

def predict_stock(stock_id):
    """預測股票"""
    print(f"預測股票 {stock_id}")
    print("=" * 50)
    
    cmd = f"python fixed_predict.py {stock_id}"
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n股票 {stock_id} 預測完成！")
    else:
        print(f"\n股票 {stock_id} 預測失敗！")

def generate_ranking(top_k=20):
    """生成排行榜"""
    print(f"生成 TOP {top_k} 潛力股排行榜")
    print("=" * 50)
    
    cmd = f"python fixed_predict.py ranking {top_k}"
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\nTOP {top_k} 排行榜生成完成！")
    else:
        print(f"\n排行榜生成失敗！")

def system_test():
    """系統測試"""
    print("系統測試")
    print("=" * 50)
    
    print("\n1. 測試股票 8299 預測:")
    print("-" * 30)
    subprocess.run("python fixed_predict.py 8299", shell=True)
    
    print("\n2. 測試 TOP 5 排行榜:")
    print("-" * 30)
    subprocess.run("python fixed_predict.py ranking 5", shell=True)
    
    print("\n系統測試完成！")

def main():
    """主程式"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "stock":
        if len(sys.argv) < 3:
            print("錯誤: 請提供股票代碼")
            print("範例: python quick_predict.py stock 8299")
            return
        
        stock_id = sys.argv[2]
        predict_stock(stock_id)
        
    elif command == "ranking":
        top_k = 20
        if len(sys.argv) > 2:
            try:
                top_k = int(sys.argv[2])
                if top_k <= 0 or top_k > 50:
                    print("錯誤: 排行榜數量必須在 1-50 之間")
                    return
            except ValueError:
                print("錯誤: 排行榜數量必須是數字")
                return
        
        generate_ranking(top_k)
        
    elif command == "test":
        system_test()
        
    else:
        print(f"錯誤: 未知功能 '{command}'")
        show_usage()

if __name__ == "__main__":
    main()
