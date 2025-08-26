#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試選股池收集功能
"""

import sys
import os
from pathlib import Path

def debug_candidate_pool():
    """調試選股池收集功能"""
    print("=== 調試選股池收集功能 ===")
    
    # 測試參數解析
    test_args = ['candidate-pool-collection', '--file', 'stock_price_investment_system/results/candidate_pools/candidate_pool_test_20250818_181234.csv']
    print(f"測試參數: {test_args}")
    
    # 檢查檔案是否存在
    csv_file = Path('stock_price_investment_system/results/candidate_pools/candidate_pool_test_20250818_181234.csv')
    print(f"檔案存在: {csv_file.exists()}")
    
    if csv_file.exists():
        print(f"檔案路徑: {csv_file.absolute()}")
        
        # 嘗試讀取檔案
        try:
            import pandas as pd
            df = pd.read_csv(csv_file, encoding='utf-8')
            print(f"檔案讀取成功，包含 {len(df)} 行")
            print(f"欄位: {list(df.columns)}")
            
            if '股票代碼' in df.columns:
                stock_codes = df['股票代碼'].astype(str).tolist()
                print(f"股票代碼: {stock_codes}")
            else:
                print("沒有找到'股票代碼'欄位")
                
        except Exception as e:
            print(f"讀取檔案失敗: {e}")
    
    # 測試c.py的參數解析
    print("\n=== 測試c.py參數解析 ===")
    
    # 模擬sys.argv
    original_argv = sys.argv.copy()
    sys.argv = ['c.py'] + test_args
    
    try:
        # 導入c.py的main函數
        import c
        
        # 檢查參數解析邏輯
        args = sys.argv[1:]
        print(f"解析的參數: {args}")
        
        if len(args) >= 2:
            option = args[0].lower()
            print(f"選項: {option}")
            
            if option in ['candidate-pool-collection', 'cpc']:
                print("找到candidate-pool-collection選項")
                
                # 檢查是否有檔案參數
                if '--file' in args:
                    file_index = args.index('--file')
                    if file_index + 1 < len(args):
                        csv_file_path = args[file_index + 1]
                        print(f"檔案參數: {csv_file_path}")
                        
                        # 檢查檔案是否存在
                        if Path(csv_file_path).exists():
                            print("檔案存在，可以執行")
                        else:
                            print("檔案不存在")
                    else:
                        print("--file 參數後沒有檔案路徑")
                else:
                    print("沒有找到--file參數")
            else:
                print(f"不是candidate-pool-collection選項: {option}")
        else:
            print("參數不足")
            
    except Exception as e:
        print(f"測試c.py時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢復原始argv
        sys.argv = original_argv

if __name__ == "__main__":
    debug_candidate_pool()
