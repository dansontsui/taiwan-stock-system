# -*- coding: utf-8 -*-
"""
分析停損停利結果
"""

import json
import sys
from pathlib import Path

def analyze_stop_loss_results(json_path):
    """分析停損停利結果"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        best = data.get('best_combination', {})
        analysis_stats = data.get('analysis_stats', {})
        
        print('🎯 最佳停損停利分析結果')
        print('='*50)
        
        # 最佳組合參數
        stop_loss = best.get('stop_loss')
        take_profit = best.get('take_profit')
        score = best.get('score')
        
        print(f'📊 最佳停損停利組合:')
        if stop_loss is not None:
            print(f'   🔻 停損點: {stop_loss:.1%}')
        else:
            print(f'   🔻 停損點: 未找到')
            
        if take_profit is not None:
            print(f'   🔺 停利點: {take_profit:.1%}')
        else:
            print(f'   🔺 停利點: 未找到')
            
        if score is not None:
            print(f'   ⭐ 綜合評分: {score:.1f}/100')
        else:
            print(f'   ⭐ 綜合評分: 未找到')
        
        print()
        
        # 績效指標
        print(f'📈 績效指標:')
        print(f'   總交易數: {best.get("total_trades", 0)}')
        print(f'   獲利交易數: {best.get("winning_trades", 0)}')
        print(f'   勝率: {best.get("win_rate", 0):.1%}')
        print(f'   平均報酬: {best.get("avg_return", 0):.2%}')
        print(f'   總報酬: {best.get("total_return", 0):.2%}')
        print(f'   最大回撤: {best.get("max_drawdown", 0):.1%}')
        
        print()
        
        # 出場原因統計
        print(f'🚪 出場原因統計:')
        exit_reasons = best.get('exit_reasons', {})
        total = best.get('total_trades', 0)
        
        reason_names = {
            'take_profit': '🔺 停利出場',
            'stop_loss': '🔻 停損出場', 
            'normal': '⏰ 正常到期'
        }
        
        for reason, count in exit_reasons.items():
            pct = count/total*100 if total > 0 else 0
            reason_name = reason_names.get(reason, reason)
            print(f'   {reason_name}: {count} 筆 ({pct:.1f}%)')
        
        print()
        
        # 分析統計
        print(f'📊 分析統計:')
        print(f'   測試組合數: {analysis_stats.get("total_combinations_tested", 0)}')
        print(f'   最佳評分: {analysis_stats.get("best_score", 0):.1f}')
        
        # 原始績效比較
        original_perf = analysis_stats.get('original_performance', {})
        if original_perf:
            print()
            print(f'📈 與原始策略比較:')
            print(f'   項目           原始策略    最佳停損停利    改善幅度')
            print(f'   ─────────────────────────────────────────────')
            
            orig_avg = original_perf.get('avg_return', 0)
            best_avg = best.get('avg_return', 0)
            if orig_avg != 0:
                avg_improve = (best_avg - orig_avg) / abs(orig_avg) * 100
                print(f'   平均報酬       {orig_avg:>7.2%}      {best_avg:>7.2%}      {avg_improve:>+6.1f}%')
            
            orig_win = original_perf.get('win_rate', 0)
            best_win = best.get('win_rate', 0)
            if orig_win != 0:
                win_improve = (best_win - orig_win) / orig_win * 100
                print(f'   勝率           {orig_win:>7.1%}      {best_win:>7.1%}      {win_improve:>+6.1f}%')
            
            orig_dd = original_perf.get('max_drawdown', 0)
            best_dd = best.get('max_drawdown', 0)
            if orig_dd != 0:
                dd_improve = (orig_dd - best_dd) / orig_dd * 100
                print(f'   最大回撤       {orig_dd:>7.1%}      {best_dd:>7.1%}      {dd_improve:>+6.1f}%')
        
        print('='*50)
        
        # 檢查是否有問題
        if stop_loss is None or take_profit is None:
            print('⚠️  注意：停損停利參數未找到，可能分析過程中出現問題')
        
        if total == 0:
            print('⚠️  注意：沒有交易記錄，無法進行停損停利分析')
        
        if exit_reasons.get('normal', 0) == total:
            print('⚠️  注意：所有交易都是正常到期，表示停損停利點可能設定過寬')
            print('💡 建議：可以嘗試更緊的停損停利設定')
        
    except Exception as e:
        print(f'❌ 分析失敗: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    json_path = "stock_price_investment_system/results/holdout/holdout_202501_202507_020_k7_MF_0827144232/stop_loss_analysis_20250827_144232.json"
    analyze_stop_loss_results(json_path)
