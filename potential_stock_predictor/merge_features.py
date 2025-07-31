#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合併特徵檔案
"""

import pandas as pd
from pathlib import Path
import sys

def merge_features():
    """合併特徵檔案"""
    features_file = Path("data/features/features_basic_2024-06-30.csv")
    backup_file = Path("data/features/features_basic_2024-06-30_backup.csv")
    
    if not features_file.exists():
        print("找不到特徵檔案")
        return
    
    # 讀取當前特徵檔案
    current_df = pd.read_csv(features_file)
    print(f"當前特徵檔案包含 {len(current_df)} 檔股票")
    
    # 檢查是否有備份檔案
    if backup_file.exists():
        backup_df = pd.read_csv(backup_file)
        print(f"備份檔案包含 {len(backup_df)} 檔股票")
        
        # 合併資料 (去重)
        merged_df = pd.concat([backup_df, current_df]).drop_duplicates(subset=['stock_id'], keep='last')
        merged_df = merged_df.sort_values('stock_id')
        
        # 保存合併結果
        merged_df.to_csv(features_file, index=False)
        print(f"合併完成，總共 {len(merged_df)} 檔股票")
        
        # 顯示股票清單
        print("包含的股票:")
        stock_list = sorted(merged_df['stock_id'].astype(str).tolist())
        print(stock_list)
        
    else:
        print("沒有找到備份檔案，創建備份")
        # 如果沒有備份，先備份原始檔案
        original_file = Path("data/features/features_basic_original_2024-06-30.csv")
        if original_file.exists():
            original_df = pd.read_csv(original_file)
            merged_df = pd.concat([original_df, current_df]).drop_duplicates(subset=['stock_id'], keep='last')
            merged_df = merged_df.sort_values('stock_id')
            merged_df.to_csv(features_file, index=False)
            print(f"與原始檔案合併完成，總共 {len(merged_df)} 檔股票")

if __name__ == "__main__":
    merge_features()
