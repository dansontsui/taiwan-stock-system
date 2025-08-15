#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester
from stock_price_investment_system.price_models.stock_price_predictor import StockPricePredictor
from stock_price_investment_system.data.data_manager import DataManager
import logging

# 設定簡單日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_prediction():
    """調試預測功能"""
    print("🔍 調試預測功能...")
    
    try:
        # 創建資料管理器
        dm = DataManager()
        
        # 創建預測器
        predictor = StockPricePredictor(model_type='random_forest')
        
        # 測試預測8299在2021年的某個日期
        test_date = '2021-06-30'
        stock_id = '8299'
        
        print(f"📊 測試預測: {stock_id} 在 {test_date}")
        
        # 檢查資料是否存在
        price_data = dm.get_stock_prices(stock_id, '2020-01-01', test_date)
        print(f"📈 價格資料筆數: {len(price_data)}")
        
        if len(price_data) > 0:
            print(f"📅 資料範圍: {price_data['date'].min()} ~ {price_data['date'].max()}")
            
            # 執行預測
            result = predictor.predict(stock_id, test_date)
            print(f"🎯 預測結果: {result}")
            
            if result['success']:
                print(f"✅ 預測成功: {result['predicted_return']:.4f}")
            else:
                print(f"❌ 預測失敗: {result.get('error', '未知錯誤')}")
        else:
            print("❌ 沒有價格資料")
            
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()

def debug_holdout_simple():
    """簡化的外層回測調試"""
    print("\n🚀 調試外層回測...")
    
    try:
        # 讀取候選池
        with open('stock_price_investment_system/results/candidate_pools/test_candidate_pool.json', 'r', encoding='utf-8') as f:
            pool_data = json.load(f)
        
        candidate_stocks = [stock['stock_id'] for stock in pool_data['candidate_pool']]
        print(f"📋 候選股票: {candidate_stocks}")
        
        # 創建回測器
        backtester = HoldoutBacktester()
        
        # 手動測試一個月的預測
        test_date = '2021-06-30'
        print(f"📅 測試日期: {test_date}")
        
        # 模擬回測器的預測邏輯
        stock_predictors = {}
        for stock_id in candidate_stocks:
            stock_predictors[stock_id] = StockPricePredictor(model_type='random_forest')
        
        predictions = []
        for stock_id in candidate_stocks:
            if stock_id in stock_predictors:
                pred_result = stock_predictors[stock_id].predict(stock_id, test_date)
                print(f"🎯 {stock_id} 預測: success={pred_result['success']}")
                if pred_result['success']:
                    print(f"   報酬率: {pred_result['predicted_return']:.4f}")
                    predictions.append({
                        'stock_id': stock_id,
                        'predicted_return': pred_result['predicted_return'],
                        'model_type': 'random_forest'
                    })
                else:
                    print(f"   錯誤: {pred_result.get('error', '未知')}")
        
        print(f"📊 總預測數: {len(predictions)}")
        
        if predictions:
            # 檢查門檻篩選
            prediction_threshold = -0.05
            positive_preds = [p for p in predictions if p['predicted_return'] > prediction_threshold]
            print(f"🎯 符合門檻 ({prediction_threshold}) 的預測: {len(positive_preds)}")
            
            for pred in positive_preds:
                print(f"   {pred['stock_id']}: {pred['predicted_return']:.4f}")
        
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_prediction()
    debug_holdout_simple()
