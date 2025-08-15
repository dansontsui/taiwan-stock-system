# -*- coding: utf-8 -*-
"""
Debug 股票匹配問題
"""

import sys
from pathlib import Path

# 添加路徑
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from stock_price_investment_system.data.data_manager import DataManager
from stock_price_investment_system.price_models.hyperparameter_tuner import HyperparameterTuner
from stock_price_investment_system.config.settings import get_config

def debug_stock_matching():
    print("=== Debug 股票匹配問題 ===")
    
    # 1. 檢查已調優股票
    print("\n1. 檢查已調優股票...")
    tuned_df = HyperparameterTuner.get_tuned_stocks_info()
    
    if tuned_df.empty:
        print("❌ 註冊表為空")
        return
    
    successful_tuned = tuned_df[tuned_df['是否成功'] == '成功']
    tuned_stock_ids = successful_tuned['股票代碼'].unique().tolist()
    
    print(f"✅ 找到 {len(tuned_stock_ids)} 檔已調優股票")
    print(f"已調優股票: {tuned_stock_ids}")
    print(f"股票類型: {[type(sid) for sid in tuned_stock_ids]}")
    
    # 2. 檢查可用股票
    print("\n2. 檢查可用股票...")
    data_manager = DataManager()
    config = get_config('walkforward')
    
    available_stocks = data_manager.get_available_stocks(
        start_date=config['training_start'] + '-01',
        end_date=config['training_end'] + '-31',
        min_history_months=config['min_stock_history_months']
    )
    
    print(f"✅ 找到 {len(available_stocks)} 檔可用股票")
    print(f"前20檔可用股票: {available_stocks[:20]}")
    print(f"股票類型: {[type(sid) for sid in available_stocks[:5]]}")
    
    # 3. 檢查 8299 是否在可用股票中
    print("\n3. 檢查 8299 是否在可用股票中...")
    
    # 不同格式的 8299
    formats_to_check = ['8299', 8299, '08299']
    
    for fmt in formats_to_check:
        if fmt in available_stocks:
            print(f"✅ {fmt} ({type(fmt)}) 在可用股票中")
        else:
            print(f"❌ {fmt} ({type(fmt)}) 不在可用股票中")
    
    # 4. 檢查匹配邏輯
    print("\n4. 檢查匹配邏輯...")
    
    tuned_stock_ids_str = [str(sid) for sid in tuned_stock_ids]
    available_stock_ids_str = [str(sid) for sid in available_stocks]
    
    print(f"已調優股票(字串): {tuned_stock_ids_str}")
    print(f"可用股票前10檔(字串): {available_stock_ids_str[:10]}")
    
    # 檢查交集
    intersection = set(tuned_stock_ids_str) & set(available_stock_ids_str)
    print(f"交集: {list(intersection)}")
    
    # 5. 手動檢查 8299
    print("\n5. 手動檢查 8299...")
    
    if '8299' in available_stock_ids_str:
        print("✅ '8299' 在可用股票字串清單中")
    else:
        print("❌ '8299' 不在可用股票字串清單中")
        # 檢查相似的股票代碼
        similar = [s for s in available_stock_ids_str if '8299' in s or s in '8299']
        print(f"相似股票代碼: {similar}")
    
    print("\n=== Debug 完成 ===")

if __name__ == '__main__':
    debug_stock_matching()
