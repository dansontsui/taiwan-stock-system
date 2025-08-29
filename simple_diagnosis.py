#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單診斷除零錯誤的原因
"""

import json
import sys
from pathlib import Path

def main():
    """主函數"""
    
    file_path = "stock_price_investment_system/results/candidate_pools/candidate_pool_20250827_132845.json"
    
    print("🔍 簡單診斷除零錯誤原因")
    print("=" * 40)
    
    try:
        # 處理BOM並讀取檔案
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        
        text_content = content.decode('utf-8')
        
        # 解析JSON
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError:
            decoder = json.JSONDecoder()
            data, idx = decoder.raw_decode(text_content)
        
        candidate_pool = data.get('candidate_pool', [])
        print(f"📊 候選股票總數: {len(candidate_pool)}")
        
        # 檢查前幾個股票的詳細資訊
        print(f"\n🔍 檢查前5個股票的詳細資訊:")
        
        for i, stock in enumerate(candidate_pool[:5]):
            stock_id = stock.get('stock_id', f'unknown_{i}')
            stock_score = stock.get('stock_score', 0)
            
            print(f"\n   股票 {i+1}: {stock_id}")
            print(f"   評分: {stock_score}")
            
            # 檢查統計資料
            statistics = stock.get('statistics', {})
            if statistics:
                total_trades = statistics.get('total_trades', 0)
                avg_return = statistics.get('average_return', 0)
                win_rate = statistics.get('win_rate', 0)
                
                print(f"   總交易次數: {total_trades}")
                print(f"   平均報酬: {avg_return:.4f}")
                print(f"   勝率: {win_rate:.4f}")
                
                # 檢查交易記錄
                all_trades = statistics.get('all_trades', [])
                print(f"   交易記錄數: {len(all_trades)}")
                
                if all_trades:
                    # 檢查第一筆交易
                    first_trade = all_trades[0]
                    entry_date = first_trade.get('entry_date', '')
                    predicted_return = first_trade.get('predicted_return', '0')
                    actual_return = first_trade.get('actual_return', 0)
                    
                    print(f"   第一筆交易日期: {entry_date}")
                    print(f"   第一筆預測報酬: {predicted_return}")
                    print(f"   第一筆實際報酬: {actual_return}")
                    
                    # 檢查是否有2024-12的交易
                    dec_2024_trades = [t for t in all_trades if t.get('entry_date', '').startswith('2024-12')]
                    if dec_2024_trades:
                        print(f"   2024-12交易數: {len(dec_2024_trades)}")
                        dec_trade = dec_2024_trades[0]
                        print(f"   2024-12預測報酬: {dec_trade.get('predicted_return', '0')}")
                        print(f"   2024-12實際報酬: {dec_trade.get('actual_return', 0)}")
                    else:
                        print(f"   沒有2024-12的交易記錄")
            else:
                print(f"   ❌ 缺少統計資料")
        
        # 檢查可能的問題
        print(f"\n🎯 可能的除零錯誤原因分析:")
        
        # 1. 檢查是否有評分為0的股票
        zero_score_stocks = [s for s in candidate_pool if s.get('stock_score', 0) <= 0]
        print(f"   1. 評分≤0的股票數: {len(zero_score_stocks)}")
        
        # 2. 檢查是否有沒有交易記錄的股票
        no_trades_stocks = [s for s in candidate_pool if not s.get('statistics', {}).get('all_trades', [])]
        print(f"   2. 沒有交易記錄的股票數: {len(no_trades_stocks)}")
        
        # 3. 檢查是否有平均報酬為0的股票
        zero_return_stocks = [s for s in candidate_pool if s.get('statistics', {}).get('average_return', 0) == 0]
        print(f"   3. 平均報酬為0的股票數: {len(zero_return_stocks)}")
        
        # 4. 檢查預測報酬為0的交易
        zero_predicted_count = 0
        for stock in candidate_pool[:10]:  # 只檢查前10個
            all_trades = stock.get('statistics', {}).get('all_trades', [])
            for trade in all_trades:
                predicted_return = trade.get('predicted_return', '0')
                if predicted_return == '0' or float(predicted_return) == 0:
                    zero_predicted_count += 1
        
        print(f"   4. 預測報酬為0的交易數 (前10股): {zero_predicted_count}")
        
        print(f"\n💡 最可能的除零原因:")
        print(f"   - 在2024-12月份執行時，無法獲取股價資料")
        print(f"   - 導致 entry_price 為 0 或 None")
        print(f"   - 在計算股數或報酬率時發生除零錯誤")
        print(f"   - 建議檢查股價資料庫中2024-12月份的資料完整性")
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
