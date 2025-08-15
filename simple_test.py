#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("開始測試...")

try:
    import sys
    import os
    print("✅ 基本模組導入成功")
    
    # 檢查路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 當前目錄: {current_dir}")
    
    # 檢查候選池檔案
    test_pool_path = 'stock_price_investment_system/results/candidate_pools/test_candidate_pool.json'
    if os.path.exists(test_pool_path):
        print(f"✅ 測試候選池檔案存在: {test_pool_path}")
        
        # 讀取檔案內容
        import json
        with open(test_pool_path, 'r', encoding='utf-8') as f:
            pool_data = json.load(f)
        print(f"📊 候選池包含 {len(pool_data.get('candidate_pool', []))} 檔股票")
    else:
        print(f"❌ 測試候選池檔案不存在: {test_pool_path}")
    
    # 嘗試導入回測器
    print("📝 嘗試導入回測器...")
    from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester
    print("✅ 回測器導入成功")
    
    # 創建回測器實例
    print("🏗️ 創建回測器實例...")
    backtester = HoldoutBacktester()
    print("✅ 回測器實例創建成功")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("測試完成")
