#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
執行回測 - 簡化版
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "potential_stock_predictor"))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def simple_backtest():
    """簡化版回測"""
    print("=" * 60)
    print("潛力股預測系統 - 簡化回測")
    print("=" * 60)
    
    # 回測配置
    config = {
        'train_period': '2015-2023',
        'backtest_period': '2024',
        'rebalance_dates': ['2024-01-31', '2024-04-30', '2024-07-31', '2024-10-31'],
        'prediction_horizon': 20,
        'top_n_stocks': 10
    }
    
    print("回測配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("回測流程說明")
    print("=" * 60)
    
    print("1. 滾動窗口訓練:")
    for i, date in enumerate(config['rebalance_dates']):
        train_end = (pd.to_datetime(date) - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"   {date}: 訓練資料 2015-01-01 ~ {train_end}")
    
    print("\n2. 預測與持有期間:")
    for i, date in enumerate(config['rebalance_dates']):
        if i < len(config['rebalance_dates']) - 1:
            next_date = config['rebalance_dates'][i + 1]
            print(f"   {date} 預測 → 持有至 {next_date}")
        else:
            print(f"   {date} 預測 → 持有至 2024-12-31")
    
    print("\n3. 關鍵特點:")
    print("   ✅ 避免未來函數：每次只用當時已知的資料")
    print("   ✅ 滾動更新：新的財報發布後重新訓練")
    print("   ✅ 真實模擬：模擬實際投資決策過程")
    
    print("\n" + "=" * 60)
    print("資料需求分析")
    print("=" * 60)
    
    print("特徵資料需求:")
    print("├── 2015-2023: 訓練用歷史特徵")
    print("├── 2024-01-31: Q1預測用特徵")
    print("├── 2024-04-30: Q2預測用特徵 (包含Q1財報)")
    print("├── 2024-07-31: Q3預測用特徵 (包含Q2財報)")
    print("└── 2024-10-31: Q4預測用特徵 (包含Q3財報)")
    
    print("\n目標變數需求:")
    print("├── 2015-2023: 訓練用歷史目標")
    print("├── 2024-02-20~2024-03-15: Q1預測驗證")
    print("├── 2024-05-20~2024-06-15: Q2預測驗證")
    print("├── 2024-08-20~2024-09-15: Q3預測驗證")
    print("└── 2024-11-20~2024-12-15: Q4預測驗證")
    
    print("\n" + "=" * 60)
    print("回答您的問題")
    print("=" * 60)
    
    print("❓ 特徵資料只要維持2015-2023即可？")
    print("❌ 不正確！")
    print("✅ 正確做法：")
    print("   - 2015-2023: 訓練用歷史特徵")
    print("   - 2024每季: 新增當季預測用特徵")
    print("   - 原因: 需要模擬每個時點的實際情況")
    
    print("\n❓ 2024每次有月報季報都要重新產生？")
    print("✅ 正確！")
    print("   - 每季重新訓練模型")
    print("   - 使用最新的財報資料")
    print("   - 確保預測基於當時已知資訊")
    
    print("\n" + "=" * 60)
    print("實作建議")
    print("=" * 60)
    
    print("階段1: 資料準備")
    print("├── 收集2015-2024完整資料")
    print("├── 生成2015-2023訓練特徵")
    print("└── 生成2015-2023訓練目標")
    
    print("\n階段2: 回測執行")
    print("├── 2024-01-31: 用2015-2023資料訓練，預測Q1")
    print("├── 2024-04-30: 用2015-Q1資料訓練，預測Q2")
    print("├── 2024-07-31: 用2015-Q2資料訓練，預測Q3")
    print("└── 2024-10-31: 用2015-Q3資料訓練，預測Q4")
    
    print("\n階段3: 結果評估")
    print("├── 計算每季預測準確率")
    print("├── 計算累積報酬率")
    print("└── 分析策略有效性")

def create_backtest_plan():
    """創建回測執行計劃"""
    print("\n" + "=" * 60)
    print("回測執行計劃")
    print("=" * 60)
    
    plan = {
        "步驟1": {
            "名稱": "資料完整性檢查",
            "內容": [
                "檢查2015-2024股價資料完整性",
                "檢查財報資料覆蓋率",
                "識別資料缺失問題"
            ]
        },
        "步驟2": {
            "名稱": "訓練資料準備",
            "內容": [
                "生成2015-2023特徵資料",
                "生成2015-2023目標變數",
                "資料清理和預處理"
            ]
        },
        "步驟3": {
            "名稱": "回測框架建立",
            "內容": [
                "實作滾動窗口訓練",
                "實作預測和評估邏輯",
                "建立結果記錄系統"
            ]
        },
        "步驟4": {
            "名稱": "執行回測",
            "內容": [
                "Q1回測 (2024-01-31預測)",
                "Q2回測 (2024-04-30預測)",
                "Q3回測 (2024-07-31預測)",
                "Q4回測 (2024-10-31預測)"
            ]
        },
        "步驟5": {
            "名稱": "結果分析",
            "內容": [
                "計算整體績效指標",
                "分析各季表現差異",
                "生成詳細報告"
            ]
        }
    }
    
    for step, info in plan.items():
        print(f"\n{step}: {info['名稱']}")
        for item in info['內容']:
            print(f"  • {item}")
    
    return plan

def main():
    """主函數"""
    simple_backtest()
    create_backtest_plan()
    
    print("\n" + "=" * 60)
    print("下一步行動")
    print("=" * 60)
    print("1. 確認您的回測需求是否符合上述說明")
    print("2. 如需執行完整回測，請運行:")
    print("   python potential_stock_predictor/backtesting_system.py")
    print("3. 如需客製化配置，請修改回測參數")

if __name__ == "__main__":
    main()
