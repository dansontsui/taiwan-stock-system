#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester
import logging

# 設定簡單日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def quick_test():
    """快速測試外層回測"""
    print("🚀 快速測試外層回測...")
    
    try:
        # 創建回測器
        backtester = HoldoutBacktester()
        print("✅ 回測器創建成功")
        
        # 執行回測，只測試一個月
        print("📊 執行回測 (2021-06-01 到 2021-06-30)...")
        result = backtester.run(
            candidate_pool_json='stock_price_investment_system/results/candidate_pools/test_candidate_pool.json',
            holdout_start='2021-06-01',
            holdout_end='2021-06-30'
        )
        
        print("✅ 回測執行完成")
        print(f"📊 結果: {result}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    quick_test()
