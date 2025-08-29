#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷候選池檔案中可能導致除零錯誤的問題
"""

import json
import sys
from pathlib import Path

def diagnose_candidate_pool(file_path):
    """診斷候選池檔案中的潛在問題"""
    
    print(f"🔍 診斷候選池檔案: {file_path}")
    print("=" * 60)
    
    try:
        # 處理BOM問題
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
            print("🔧 已移除UTF-8 BOM")
        
        # 解析JSON
        text_content = content.decode('utf-8')
        
        try:
            data = json.loads(text_content)
        except json.JSONDecodeError:
            print("🔧 嘗試解析部分JSON...")
            decoder = json.JSONDecoder()
            data, idx = decoder.raw_decode(text_content)
        
        print(f"✅ 成功讀取JSON檔案")
        
        candidate_pool = data.get('candidate_pool', [])
        print(f"📊 候選股票總數: {len(candidate_pool)}")
        
        # 診斷潛在問題
        issues = []
        problematic_stocks = []
        
        print("\n🔍 檢查潛在的除零錯誤原因...")
        
        for i, stock in enumerate(candidate_pool):
            stock_id = stock.get('stock_id', f'unknown_{i}')
            stock_score = stock.get('stock_score', 0)
            
            # 檢查1: 股票評分是否異常
            if stock_score <= 0:
                issues.append(f"股票 {stock_id}: 評分異常 ({stock_score})")
                problematic_stocks.append(stock_id)
            
            # 檢查2: 統計資料是否完整
            statistics = stock.get('statistics', {})
            if not statistics:
                issues.append(f"股票 {stock_id}: 缺少統計資料")
                problematic_stocks.append(stock_id)
                continue
            
            # 檢查3: 交易記錄是否存在
            all_trades = statistics.get('all_trades', [])
            if not all_trades:
                issues.append(f"股票 {stock_id}: 沒有交易記錄")
                problematic_stocks.append(stock_id)
                continue
            
            # 檢查4: 交易記錄中的異常值
            for j, trade in enumerate(all_trades[:3]):  # 只檢查前3筆交易
                entry_date = trade.get('entry_date', '')
                predicted_return = trade.get('predicted_return', '0')
                actual_return = trade.get('actual_return', 0)
                
                # 檢查預測報酬是否為字串格式的0或空值
                if predicted_return == '0' or predicted_return == '' or predicted_return is None:
                    issues.append(f"股票 {stock_id}: 交易{j+1}預測報酬為0或空值")
                
                # 檢查實際報酬是否異常
                if actual_return == 0:
                    issues.append(f"股票 {stock_id}: 交易{j+1}實際報酬為0")
                
                # 檢查日期格式
                if not entry_date or len(entry_date) != 10:
                    issues.append(f"股票 {stock_id}: 交易{j+1}日期格式異常 ({entry_date})")
            
            # 檢查5: 統計指標是否異常
            avg_return = statistics.get('average_return', 0)
            win_rate = statistics.get('win_rate', 0)
            total_trades = statistics.get('total_trades', 0)
            
            if avg_return == 0:
                issues.append(f"股票 {stock_id}: 平均報酬為0")
            
            if total_trades == 0:
                issues.append(f"股票 {stock_id}: 總交易次數為0")
            
            # 只檢查前10個股票，避免輸出太多
            if i >= 9:
                break
        
        # 輸出診斷結果
        print(f"\n📋 診斷結果:")
        print(f"   發現問題數量: {len(issues)}")
        print(f"   問題股票數量: {len(set(problematic_stocks))}")
        
        if issues:
            print(f"\n⚠️ 發現的問題:")
            for issue in issues[:20]:  # 只顯示前20個問題
                print(f"   - {issue}")
            
            if len(issues) > 20:
                print(f"   ... 還有 {len(issues) - 20} 個問題")
        
        # 檢查特定的2024-12月份相關問題
        print(f"\n🔍 檢查2024-12月份相關問題...")

        dec_2024_issues = []
        dec_2024_stocks = []

        for stock in candidate_pool[:10]:  # 只檢查前10個股票
            stock_id = stock.get('stock_id', 'unknown')
            all_trades = stock.get('statistics', {}).get('all_trades', [])

            has_dec_2024 = False
            for trade in all_trades:
                entry_date = trade.get('entry_date', '')
                if entry_date.startswith('2024-12'):
                    has_dec_2024 = True
                    predicted_return = trade.get('predicted_return', '0')
                    actual_return = trade.get('actual_return', 0)

                    if predicted_return == '0' or float(predicted_return) == 0:
                        dec_2024_issues.append(f"股票 {stock_id}: 2024-12預測報酬為0")

                    if actual_return == 0:
                        dec_2024_issues.append(f"股票 {stock_id}: 2024-12實際報酬為0")

            if has_dec_2024:
                dec_2024_stocks.append(stock_id)

        print(f"   包含2024-12資料的股票: {dec_2024_stocks}")

        if dec_2024_issues:
            print(f"   發現2024-12月份問題: {len(dec_2024_issues)}個")
            for issue in dec_2024_issues[:10]:
                print(f"   - {issue}")
        else:
            print(f"   2024-12月份資料看起來正常")

        # 模擬實際執行情況
        print(f"\n🔍 模擬實際執行情況...")

        # 檢查是否有股票在2024-12月份會被選中
        simulation_issues = []

        for stock in candidate_pool[:5]:  # 檢查前5個股票
            stock_id = stock.get('stock_id', 'unknown')
            stock_score = stock.get('stock_score', 0)

            # 模擬月投資金額分配
            monthly_investment = 1000000  # 假設100萬
            num_stocks = 5  # 假設選中5檔股票
            per_stock_investment = monthly_investment / num_stocks

            print(f"   股票 {stock_id}: 評分 {stock_score}, 分配金額 {per_stock_investment:,.0f}")

            # 模擬股價獲取（這裡我們無法真正獲取，但可以檢查邏輯）
            # 假設股價為0的情況
            entry_price = 0  # 模擬股價獲取失敗的情況

            if entry_price <= 0:
                simulation_issues.append(f"股票 {stock_id}: 無法獲取股價或股價為0")
                continue

        if simulation_issues:
            print(f"   模擬執行發現問題: {len(simulation_issues)}個")
            for issue in simulation_issues:
                print(f"   - {issue}")
        else:
            print(f"   模擬執行正常")
        
        # 總結可能的除零原因
        print(f"\n🎯 可能的除零錯誤原因:")
        print(f"   1. 股票評分為0或負數 → 影響股數計算")
        print(f"   2. 預測報酬為0 → 影響出場價格計算")
        print(f"   3. 實際報酬為0 → 可能表示股價沒有變化")
        print(f"   4. 總交易次數為0 → 影響月報酬率計算")
        print(f"   5. 股價資料缺失 → 導致進場價格為0")
        
        return len(issues) > 0
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    
    file_path = "stock_price_investment_system/results/candidate_pools/candidate_pool_20250827_132845.json"
    
    if not Path(file_path).exists():
        print(f"❌ 檔案不存在: {file_path}")
        return
    
    has_issues = diagnose_candidate_pool(file_path)
    
    if has_issues:
        print(f"\n⚠️ 發現潛在問題，這些可能是導致除零錯誤的原因")
        print(f"\n💡 建議:")
        print(f"   1. 檢查股價資料是否完整")
        print(f"   2. 確認預測模型輸出是否正常")
        print(f"   3. 驗證候選池生成邏輯")
        print(f"   4. 使用測試候選池進行驗證")
    else:
        print(f"\n✅ 候選池檔案看起來正常")

if __name__ == "__main__":
    main()
