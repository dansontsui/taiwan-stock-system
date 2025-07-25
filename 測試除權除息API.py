#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試除權除息API是否可用
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    from app.services.data_collector import FinMindDataCollector
except ImportError as e:
    print(f"❌ 模組導入失敗: {e}")
    sys.exit(1)

def test_dividend_result_api():
    """測試除權除息結果API"""
    print("🔍 測試除權除息結果API")
    print("=" * 60)
    
    try:
        # 創建資料收集器
        collector = FinMindDataCollector(Config.FINMIND_API_URL, Config.FINMIND_API_TOKEN)
        
        # 測試股票清單
        test_stocks = ['1301', '2330', '2454']
        
        for stock_id in test_stocks:
            print(f"\n📊 測試股票: {stock_id}")
            print("-" * 40)
            
            try:
                # 測試除權除息結果
                print("🎯 測試 TaiwanStockDividendResult...")
                data = collector._make_request(
                    dataset="TaiwanStockDividendResult",
                    data_id=stock_id,
                    start_date="2020-01-01",
                    end_date="2024-12-31"
                )
                
                if data and 'data' in data:
                    count = len(data['data'])
                    print(f"   ✅ 成功獲取 {count} 筆除權除息結果")
                    
                    if count > 0:
                        # 顯示範例資料
                        sample = data['data'][0]
                        print(f"   📋 範例資料:")
                        for key, value in list(sample.items())[:5]:
                            print(f"      {key}: {value}")
                    else:
                        print(f"   ⚠️ 該股票無除權除息結果資料")
                else:
                    print(f"   ❌ API回應格式錯誤")
                
            except Exception as e:
                print(f"   ❌ API請求失敗: {e}")
            
            # 等待避免API限制
            import time
            time.sleep(2)
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_dividend_policy_api():
    """測試股利政策API (對比)"""
    print(f"\n🔍 測試股利政策API (對比)")
    print("=" * 60)
    
    try:
        collector = FinMindDataCollector(Config.FINMIND_API_URL, Config.FINMIND_API_TOKEN)
        
        # 測試1301的股利政策
        print(f"📊 測試 1301 股利政策...")
        data = collector._make_request(
            dataset="TaiwanStockDividend",
            data_id="1301",
            start_date="2020-01-01",
            end_date="2024-12-31"
        )
        
        if data and 'data' in data:
            count = len(data['data'])
            print(f"   ✅ 股利政策資料: {count} 筆")
            
            if count > 0:
                sample = data['data'][0]
                print(f"   📋 範例資料:")
                for key, value in list(sample.items())[:5]:
                    print(f"      {key}: {value}")
        else:
            print(f"   ❌ 股利政策API失敗")
            
    except Exception as e:
        print(f"❌ 股利政策測試失敗: {e}")

def check_api_datasets():
    """檢查可用的API資料集"""
    print(f"\n🔍 檢查FinMind API可用資料集")
    print("=" * 60)
    
    try:
        # 直接請求API資料集列表
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": "DataList"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                datasets = data['data']
                print(f"✅ 找到 {len(datasets)} 個資料集")
                
                # 尋找除權除息相關的資料集
                dividend_datasets = []
                for dataset in datasets:
                    if 'dividend' in dataset.get('dataset', '').lower():
                        dividend_datasets.append(dataset)
                
                if dividend_datasets:
                    print(f"\n🎯 除權除息相關資料集:")
                    for dataset in dividend_datasets:
                        print(f"   • {dataset.get('dataset', 'Unknown')}: {dataset.get('description', 'No description')}")
                else:
                    print(f"\n⚠️ 未找到除權除息相關資料集")
            else:
                print(f"❌ API回應格式錯誤")
        else:
            print(f"❌ API請求失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 檢查API資料集失敗: {e}")

def suggest_solutions():
    """建議解決方案"""
    print(f"\n💡 解決方案建議")
    print("=" * 60)
    
    print("如果除權除息API無法使用:")
    print()
    print("1. 🔍 檢查API資料集名稱是否正確")
    print("   • TaiwanStockDividendResult")
    print("   • TaiwanStockDividend")
    print()
    print("2. 🔑 檢查API Token設定")
    print("   • 確認config.py中的FINMIND_API_TOKEN")
    print("   • 檢查Token是否有效")
    print()
    print("3. 📊 檢查資料可用性")
    print("   • 某些股票可能沒有除權除息資料")
    print("   • 調整日期範圍")
    print()
    print("4. 🔄 使用替代方案")
    print("   • 使用TaiwanStockDividend (股利政策)")
    print("   • 手動計算除權除息結果")

if __name__ == "__main__":
    test_dividend_result_api()
    test_dividend_policy_api()
    check_api_datasets()
    suggest_solutions()
