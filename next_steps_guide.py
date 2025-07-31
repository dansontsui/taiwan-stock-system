#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
潛力股預測系統使用指南
"""

def print_guide():
    """列印使用指南"""
    print("台股潛力股預測系統使用指南")
    print("=" * 50)
    
    print("\n步驟 1: 進入預測系統目錄")
    print("cd potential_stock_predictor")
    
    print("\n步驟 2: 生成特徵資料")
    print("python simple_features.py 2024-06-30")
    print("# 這會為所有股票生成機器學習特徵")
    
    print("\n步驟 3: 生成目標變數")
    print("python simple_targets.py 2024-01-01 2024-06-30")
    print("# 這會生成訓練用的目標變數 (20天內漲幅>5%)")
    
    print("\n步驟 4: 訓練模型")
    print("python simple_train.py data/features/features_2024-06-30.csv data/targets/targets_quarterly_2024-06-30.csv")
    print("# 這會訓練 Random Forest 和 Logistic Regression 模型")
    
    print("\n步驟 5: 生成潛力股排行榜")
    print("python simple_predict.py ranking random_forest 20")
    print("# 這會生成 TOP 20 潛力股排行榜")
    
    print("\n或者使用選單系統 (推薦):")
    print("python start.py")
    print("# 然後跟著選單操作:")
    print("# 1. 選單 1 → 1 (快速測試)")
    print("# 2. 選單 2 → 4 (批次處理資料)")
    print("# 3. 選單 3 → 1 (訓練模型)")
    print("# 4. 選單 4 → 1 (生成排行榜)")
    
    print("\n系統特色:")
    print("- 24個核心特徵 (技術指標、財務比率、現金流)")
    print("- 預測目標: 20個交易日內漲幅超過5%")
    print("- 支援多種模型: Random Forest, XGBoost, LightGBM")
    print("- 自動排除ETF (00開頭股票)")
    print("- 提供預測機率和信心度")
    
    print("\n預期結果:")
    print("- 處理股票數: ~2,000+ 個")
    print("- 特徵數量: 24 個")
    print("- 模型性能: AUC ~0.65, F1 ~0.73")
    print("- 潛力股排行榜: TOP 20 with 機率")
    
    print("\n注意事項:")
    print("- 首次執行可能需要10-30分鐘")
    print("- 確保有足夠的歷史資料 (建議至少1年)")
    print("- 預測結果僅供參考，投資需謹慎")

if __name__ == "__main__":
    print_guide()
