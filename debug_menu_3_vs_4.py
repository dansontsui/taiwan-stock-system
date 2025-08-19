#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json

# 加入路徑
sys.path.append('.')

def analyze_walkforward_results():
    """分析Walk-forward驗證結果（選單3的輸出）"""
    print("🔍 分析Walk-forward驗證結果（選單3）")
    print("="*50)
    
    try:
        # 載入最新的walk-forward結果
        latest_file = "stock_price_investment_system/results/walk_forward/walk_forward_results_20250818_174045.json"
        
        with open(latest_file, 'r', encoding='utf-8-sig') as f:
            results = json.load(f)
        
        print(f"📁 分析檔案: {os.path.basename(latest_file)}")
        
        # 檢查基本資訊
        print(f"\n📊 基本資訊:")
        print(f"   總fold數: {results.get('fold_count', 0)}")
        print(f"   總股票數: {results.get('stock_count', 0)}")
        print(f"   總交易數: {results.get('total_trades', 0)}")
        
        # 檢查股票統計
        stock_stats = results.get('stock_statistics', {})
        print(f"\n📈 股票統計詳情:")
        print(f"   股票統計數量: {len(stock_stats)}")
        
        if stock_stats:
            print(f"\n🏆 各股票表現:")
            for stock_id, stats in stock_stats.items():
                total_trades = stats.get('total_trades', 0)
                win_rate = stats.get('win_rate', 0)
                profit_loss_ratio = stats.get('profit_loss_ratio', 0)
                avg_return = stats.get('avg_return', 0)
                max_drawdown = stats.get('max_drawdown', 0)
                folds_with_trades = stats.get('folds_with_trades', 0)
                
                print(f"   {stock_id}:")
                print(f"     交易數: {total_trades}")
                print(f"     勝率: {win_rate*100:.1f}%")
                print(f"     盈虧比: {profit_loss_ratio:.2f}")
                print(f"     平均報酬: {avg_return:.4f}")
                print(f"     最大回撤: {max_drawdown*100:.1f}%")
                print(f"     有交易的fold數: {folds_with_trades}")
                print()
        
        return stock_stats
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return {}


def analyze_candidate_pool_filtering():
    """分析候選池篩選過程（選單4的邏輯）"""
    print("🎯 分析候選池篩選過程（選單4）")
    print("="*50)
    
    try:
        from stock_price_investment_system.config.settings import get_config
        
        # 獲取篩選門檻
        config = get_config('selection')
        thresholds = config['candidate_pool_thresholds']
        
        print(f"📋 當前篩選門檻:")
        print(f"   最小勝率: {thresholds['min_win_rate']*100:.1f}%")
        print(f"   最小盈虧比: {thresholds['min_profit_loss_ratio']}")
        print(f"   最小交易數: {thresholds['min_trade_count']}")
        print(f"   最少fold數: {thresholds['min_folds_with_trades']}")
        print(f"   最大回撤: {thresholds['max_drawdown_threshold']*100:.1f}%")
        
        return thresholds
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return {}


def manual_filtering_test(stock_stats, thresholds):
    """手動測試篩選邏輯"""
    print(f"\n🧪 手動測試篩選邏輯")
    print("="*50)
    
    if not stock_stats or not thresholds:
        print("❌ 缺少必要資料")
        return
    
    print(f"📊 逐一檢查每檔股票:")
    
    passed_stocks = []
    failed_stocks = []
    
    for stock_id, stats in stock_stats.items():
        print(f"\n🔍 檢查 {stock_id}:")
        
        # 檢查各項條件
        checks = []
        
        # 1. 勝率檢查
        win_rate = stats.get('win_rate', 0)
        win_rate_ok = win_rate >= thresholds['min_win_rate']
        checks.append(('勝率', f"{win_rate*100:.1f}%", f">= {thresholds['min_win_rate']*100:.1f}%", win_rate_ok))
        
        # 2. 盈虧比檢查
        profit_loss_ratio = stats.get('profit_loss_ratio', 0)
        plr_ok = profit_loss_ratio >= thresholds['min_profit_loss_ratio']
        checks.append(('盈虧比', f"{profit_loss_ratio:.2f}", f">= {thresholds['min_profit_loss_ratio']}", plr_ok))
        
        # 3. 交易數檢查
        total_trades = stats.get('total_trades', 0)
        trades_ok = total_trades >= thresholds['min_trade_count']
        checks.append(('交易數', f"{total_trades}", f">= {thresholds['min_trade_count']}", trades_ok))
        
        # 4. fold數檢查
        folds_with_trades = stats.get('folds_with_trades', 0)
        folds_ok = folds_with_trades >= thresholds['min_folds_with_trades']
        checks.append(('fold數', f"{folds_with_trades}", f">= {thresholds['min_folds_with_trades']}", folds_ok))
        
        # 5. 回撤檢查
        max_drawdown = stats.get('max_drawdown', 1)  # 預設1表示100%回撤
        drawdown_ok = max_drawdown <= thresholds['max_drawdown_threshold']
        checks.append(('最大回撤', f"{max_drawdown*100:.1f}%", f"<= {thresholds['max_drawdown_threshold']*100:.1f}%", drawdown_ok))
        
        # 顯示檢查結果
        for check_name, actual, required, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {actual} ({required})")
        
        # 總體結果
        all_passed = all(check[3] for check in checks)
        if all_passed:
            print(f"   🎉 {stock_id} 通過所有檢查！")
            passed_stocks.append(stock_id)
        else:
            print(f"   ❌ {stock_id} 未通過檢查")
            failed_reasons = [check[0] for check in checks if not check[3]]
            failed_stocks.append((stock_id, failed_reasons))
    
    # 總結
    print(f"\n📊 篩選結果總結:")
    print(f"   通過篩選: {len(passed_stocks)} 檔")
    print(f"   未通過篩選: {len(failed_stocks)} 檔")
    
    if passed_stocks:
        print(f"\n🏆 通過篩選的股票: {passed_stocks}")
    
    if failed_stocks:
        print(f"\n❌ 未通過篩選的股票:")
        for stock_id, reasons in failed_stocks:
            print(f"   {stock_id}: {', '.join(reasons)}")
    
    return len(passed_stocks) > 0


def suggest_relaxed_thresholds(stock_stats):
    """建議放寬的門檻"""
    print(f"\n💡 建議放寬的門檻")
    print("="*50)
    
    if not stock_stats:
        print("❌ 無股票統計資料")
        return
    
    # 計算統計值
    win_rates = [stats.get('win_rate', 0) for stats in stock_stats.values()]
    profit_loss_ratios = [stats.get('profit_loss_ratio', 0) for stats in stock_stats.values()]
    trade_counts = [stats.get('total_trades', 0) for stats in stock_stats.values()]
    fold_counts = [stats.get('folds_with_trades', 0) for stats in stock_stats.values()]
    drawdowns = [stats.get('max_drawdown', 1) for stats in stock_stats.values()]
    
    print(f"📊 當前股票表現分布:")
    print(f"   勝率範圍: {min(win_rates)*100:.1f}% ~ {max(win_rates)*100:.1f}%")
    print(f"   盈虧比範圍: {min(profit_loss_ratios):.2f} ~ {max(profit_loss_ratios):.2f}")
    print(f"   交易數範圍: {min(trade_counts)} ~ {max(trade_counts)}")
    print(f"   fold數範圍: {min(fold_counts)} ~ {max(fold_counts)}")
    print(f"   回撤範圍: {min(drawdowns)*100:.1f}% ~ {max(drawdowns)*100:.1f}%")
    
    # 建議門檻（取中位數或較寬鬆的值）
    import statistics
    
    suggested_thresholds = {
        'min_win_rate': max(0.5, statistics.median(win_rates) * 0.9),  # 中位數的90%，但至少50%
        'min_profit_loss_ratio': max(1.0, statistics.median(profit_loss_ratios) * 0.8),  # 中位數的80%，但至少1.0
        'min_trade_count': max(3, int(statistics.median(trade_counts) * 0.7)),  # 中位數的70%，但至少3
        'min_folds_with_trades': max(2, int(statistics.median(fold_counts) * 0.8)),  # 中位數的80%，但至少2
        'max_drawdown_threshold': min(0.3, statistics.median(drawdowns) * 1.5)  # 中位數的150%，但最多30%
    }
    
    print(f"\n💡 建議的放寬門檻:")
    print(f"   最小勝率: {suggested_thresholds['min_win_rate']*100:.1f}%")
    print(f"   最小盈虧比: {suggested_thresholds['min_profit_loss_ratio']:.2f}")
    print(f"   最小交易數: {suggested_thresholds['min_trade_count']}")
    print(f"   最少fold數: {suggested_thresholds['min_folds_with_trades']}")
    print(f"   最大回撤: {suggested_thresholds['max_drawdown_threshold']*100:.1f}%")
    
    return suggested_thresholds


def main():
    """主函數"""
    print("🔍 調查選單3 vs 選單4的差異")
    print("="*60)
    
    # 步驟1: 分析Walk-forward結果
    stock_stats = analyze_walkforward_results()
    
    # 步驟2: 分析候選池篩選門檻
    thresholds = analyze_candidate_pool_filtering()
    
    # 步驟3: 手動測試篩選邏輯
    has_candidates = manual_filtering_test(stock_stats, thresholds)
    
    # 步驟4: 如果沒有候選股票，建議放寬門檻
    if not has_candidates:
        suggested_thresholds = suggest_relaxed_thresholds(stock_stats)
    
    print(f"\n" + "="*60)
    print("🎯 結論")
    print("="*60)
    
    if has_candidates:
        print("✅ 找到了問題！有股票應該能通過篩選")
        print("💡 可能是候選池生成程式碼有bug")
    else:
        print("⚠️ 確認問題：門檻設定過於嚴格")
        print("💡 選單3能找到股票，但選單4的門檻太高")
        print("🔧 建議使用上面建議的放寬門檻")


if __name__ == "__main__":
    main()
