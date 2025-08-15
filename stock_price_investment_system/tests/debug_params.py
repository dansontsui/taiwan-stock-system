# -*- coding: utf-8 -*-
"""
Debug 參數解析
"""

import sys
from pathlib import Path
import pandas as pd
import ast

# 添加路徑
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

def debug_params():
    print("=== Debug 參數解析 ===")
    
    # 直接讀取 CSV
    csv_file = Path("stock_price_investment_system/models/hyperparameter_tuning/tuned_stocks_registry.csv")
    
    if not csv_file.exists():
        print("❌ CSV 檔案不存在")
        return
    
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"✅ 讀取 CSV，共 {len(df)} 筆記錄")
    
    # 顯示欄位
    print(f"欄位: {list(df.columns)}")

    # 顯示實際資料
    print("\n實際資料:")
    for i, row in df.iterrows():
        print(f"  {i}: 股票={repr(row['股票代碼'])}, 模型={repr(row['模型類型'])}")

    # 檢查資料類型
    print(f"\n股票代碼類型: {df['股票代碼'].dtype}")
    print(f"模型類型類型: {df['模型類型'].dtype}")

    # 嘗試不同的查找方式
    print(f"\n股票代碼唯一值: {df['股票代碼'].unique()}")
    print(f"模型類型唯一值: {df['模型類型'].unique()}")

    # 查找 2330 xgboost
    mask1 = df['股票代碼'] == '2330'
    mask2 = df['模型類型'] == 'xgboost'

    print(f"\n股票代碼匹配: {mask1.sum()} 筆")
    print(f"模型類型匹配: {mask2.sum()} 筆")

    mask = mask1 & mask2
    matching = df[mask]

    print(f"組合匹配: 找到 {len(matching)} 筆")
    
    if not matching.empty:
        params_str = matching.iloc[0]['最佳參數']
        print(f"參數字串: {params_str}")
        print(f"參數類型: {type(params_str)}")
        
        try:
            params = ast.literal_eval(params_str)
            print(f"✅ 解析成功: {params}")
            print(f"解析類型: {type(params)}")
        except Exception as e:
            print(f"❌ 解析失敗: {e}")
    
    print("\n=== Debug 完成 ===")

if __name__ == '__main__':
    debug_params()
