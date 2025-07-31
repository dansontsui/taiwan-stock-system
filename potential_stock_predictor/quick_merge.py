#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速合併特徵檔案
"""

import pandas as pd
from pathlib import Path

# 讀取原始的46檔股票特徵 (從備份或重新生成)
print("重新生成原始46檔股票特徵...")

# 先生成原始的46檔股票
import subprocess
import sys

try:
    result = subprocess.run([
        sys.executable, "simple_features_basic.py", "2024-06-30"
    ], capture_output=True, text=True, timeout=120)
    
    if result.returncode == 0:
        print("原始46檔股票特徵生成完成")
        
        # 讀取46檔股票特徵
        df_46 = pd.read_csv("data/features/features_basic_2024-06-30.csv")
        print(f"46檔股票特徵: {len(df_46)} 筆")
        
        # 生成8299特徵
        print("生成8299特徵...")
        result2 = subprocess.run([
            sys.executable, "simple_features_basic.py", "2024-06-30", "8299"
        ], capture_output=True, text=True, timeout=60)
        
        if result2.returncode == 0:
            # 讀取8299特徵
            df_8299 = pd.read_csv("data/features/features_basic_2024-06-30.csv")
            print(f"8299特徵: {len(df_8299)} 筆")
            
            # 合併
            merged_df = pd.concat([df_46, df_8299]).drop_duplicates(subset=['stock_id'], keep='last')
            merged_df = merged_df.sort_values('stock_id')
            
            # 保存
            merged_df.to_csv("data/features/features_basic_2024-06-30.csv", index=False)
            
            print(f"合併完成！總共 {len(merged_df)} 檔股票")
            print("股票清單:", sorted(merged_df['stock_id'].astype(str).tolist()))
            print("包含8299:", '8299' in merged_df['stock_id'].astype(str).values)
        else:
            print("8299特徵生成失敗")
    else:
        print("原始特徵生成失敗")
        
except Exception as e:
    print(f"錯誤: {e}")
