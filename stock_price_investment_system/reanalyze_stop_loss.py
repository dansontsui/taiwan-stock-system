# -*- coding: utf-8 -*-
"""
重新分析停損停利（修正欄位名稱問題）
"""

import sys
from pathlib import Path
import pandas as pd

# 添加專案路徑
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester

def reanalyze_stop_loss(csv_path, output_dir):
    """重新分析停損停利"""
    try:
        # 讀取交易資料
        trades_df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        print(f"📊 讀取交易資料: {len(trades_df)} 筆交易")
        print(f"📁 輸出目錄: {output_dir}")
        
        # 檢查資料欄位
        print(f"\n🔍 檢查資料欄位:")
        key_columns = ['max_return_20d', 'min_return_20d', 'actual_return']
        for col in key_columns:
            if col in trades_df.columns:
                print(f"   ✅ {col}: 存在")
                # 顯示一些統計資訊
                values = trades_df[col].dropna()
                if len(values) > 0:
                    print(f"      範圍: {values.min():.3f} ~ {values.max():.3f}")
                    print(f"      平均: {values.mean():.3f}")
            else:
                print(f"   ❌ {col}: 不存在")
        
        # 檢查是否有有效的最高最低報酬資料
        max_returns = trades_df['max_return_20d'].dropna()
        min_returns = trades_df['min_return_20d'].dropna()
        
        print(f"\n📈 最高報酬統計:")
        print(f"   有效資料: {len(max_returns)} 筆")
        if len(max_returns) > 0:
            print(f"   最大值: {max_returns.max():.2%}")
            print(f"   平均值: {max_returns.mean():.2%}")
            positive_count = len(max_returns[max_returns > 0])
            print(f"   正值數量: {positive_count} 筆 ({positive_count/len(max_returns)*100:.1f}%)")
        
        print(f"\n📉 最低報酬統計:")
        print(f"   有效資料: {len(min_returns)} 筆")
        if len(min_returns) > 0:
            print(f"   最小值: {min_returns.min():.2%}")
            print(f"   平均值: {min_returns.mean():.2%}")
            negative_count = len(min_returns[min_returns < 0])
            print(f"   負值數量: {negative_count} 筆 ({negative_count/len(min_returns)*100:.1f}%)")
        
        # 重新執行停損停利分析
        print(f"\n🎯 重新執行停損停利分析...")
        hb = HoldoutBacktester()
        
        # 模擬幾個停損停利組合來測試
        test_combinations = [
            {'stop_loss': 0.05, 'take_profit': 0.10},  # 5%停損, 10%停利
            {'stop_loss': 0.03, 'take_profit': 0.08},  # 3%停損, 8%停利
            {'stop_loss': 0.08, 'take_profit': 0.15},  # 8%停損, 15%停利
        ]
        
        print(f"\n📊 測試停損停利組合:")
        print(f"{'組合':>15} {'觸發停利':>8} {'觸發停損':>8} {'正常到期':>8} {'平均報酬':>10}")
        print("-" * 60)
        
        for combo in test_combinations:
            result = hb._simulate_stop_levels(trades_df, combo['stop_loss'], combo['take_profit'])
            
            exit_reasons = result.get('exit_reasons', {})
            take_profit_count = exit_reasons.get('take_profit', 0)
            stop_loss_count = exit_reasons.get('stop_loss', 0)
            normal_count = exit_reasons.get('normal', 0)
            avg_return = result.get('avg_return', 0)
            
            combo_name = f"{combo['stop_loss']:.0%}/{combo['take_profit']:.0%}"
            print(f"{combo_name:>15} {take_profit_count:>8} {stop_loss_count:>8} {normal_count:>8} {avg_return:>9.2%}")
        
        # 如果有觸發停損停利的組合，執行完整分析
        has_triggers = False
        for combo in test_combinations:
            result = hb._simulate_stop_levels(trades_df, combo['stop_loss'], combo['take_profit'])
            exit_reasons = result.get('exit_reasons', {})
            if exit_reasons.get('take_profit', 0) > 0 or exit_reasons.get('stop_loss', 0) > 0:
                has_triggers = True
                break
        
        if has_triggers:
            print(f"\n✅ 發現有效的停損停利觸發，執行完整分析...")
            
            # 計算模擬的portfolio_metrics
            portfolio_metrics = {
                'sharpe_ratio': 1.0,
                'max_drawdown': 0.1,
                'annualized_return': 0.1,
                'annualized_volatility': 0.15,
                'total_return': 0.05
            }
            
            # 執行完整的停損停利分析
            stop_analysis = hb._analyze_optimal_stop_levels(trades_df)
            
            if stop_analysis:
                # 保存新的分析結果
                import json
                from datetime import datetime
                
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_analysis_path = Path(output_dir) / f'stop_loss_analysis_fixed_{ts}.json'
                
                with open(new_analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(stop_analysis, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"💾 修正後的停損停利分析已保存: {new_analysis_path.name}")
                
                # 顯示結果
                best_combination = stop_analysis.get('best_combination', {})
                if best_combination:
                    print(f"\n🎯 修正後的最佳停損停利結果:")
                    print(f"   🔻 停損點: {best_combination.get('stop_loss', 0):.1%}")
                    print(f"   🔺 停利點: {best_combination.get('take_profit', 0):.1%}")
                    print(f"   ⭐ 綜合評分: {best_combination.get('score', 0):.1f}/100")
                    print(f"   📈 平均報酬: {best_combination.get('avg_return', 0):.2%}")
                    print(f"   🎯 勝率: {best_combination.get('win_rate', 0):.1%}")
                    
                    exit_reasons = best_combination.get('exit_reasons', {})
                    total_trades = best_combination.get('total_trades', 0)
                    print(f"\n🚪 出場原因:")
                    for reason, count in exit_reasons.items():
                        pct = count/total_trades*100 if total_trades > 0 else 0
                        reason_name = {'take_profit': '停利', 'stop_loss': '停損', 'normal': '到期'}.get(reason, reason)
                        print(f"   {reason_name}: {count} 筆 ({pct:.1f}%)")
        else:
            print(f"\n⚠️  所有測試組合都沒有觸發停損停利")
            print(f"💡 可能原因:")
            print(f"   1. 停損停利點設定過寬")
            print(f"   2. 市場波動較小")
            print(f"   3. 持有期間較短（20日）")
            
            # 建議更緊的停損停利點
            print(f"\n💡 建議嘗試更緊的停損停利設定:")
            tight_combinations = [
                {'stop_loss': 0.02, 'take_profit': 0.05},  # 2%停損, 5%停利
                {'stop_loss': 0.015, 'take_profit': 0.03}, # 1.5%停損, 3%停利
            ]
            
            for combo in tight_combinations:
                result = hb._simulate_stop_levels(trades_df, combo['stop_loss'], combo['take_profit'])
                exit_reasons = result.get('exit_reasons', {})
                take_profit_count = exit_reasons.get('take_profit', 0)
                stop_loss_count = exit_reasons.get('stop_loss', 0)
                
                combo_name = f"{combo['stop_loss']:.1%}/{combo['take_profit']:.1%}"
                print(f"   {combo_name}: 停利{take_profit_count}筆, 停損{stop_loss_count}筆")
        
    except Exception as e:
        print(f"❌ 重新分析失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    csv_path = "stock_price_investment_system/results/holdout/holdout_202501_202507_020_k7_MF_0827144232/holdout_trades_20250827_144232.csv"
    output_dir = "stock_price_investment_system/results/holdout/holdout_202501_202507_020_k7_MF_0827144232"
    
    reanalyze_stop_loss(csv_path, output_dir)
