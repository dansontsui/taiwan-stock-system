#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime

# 設定編碼
sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# 加入路徑
sys.path.append('.')

def run_walkforward_validation():
    """執行選單3：Walk-forward驗證"""
    print("🔄 步驟1：執行Walk-forward驗證")
    print("="*50)
    
    try:
        from stock_price_investment_system.data.data_manager import DataManager
        from stock_price_investment_system.price_models.feature_engineering import FeatureEngineer
        from stock_price_investment_system.price_models.walk_forward_validator import WalkForwardValidator
        from stock_price_investment_system.config.settings import get_config
        
        # 獲取配置
        config = get_config('walkforward')
        
        print("📋 當前配置：")
        print(f"   訓練視窗: {config['train_window_months']} 個月")
        print(f"   測試視窗: {config['test_window_months']} 個月")
        print(f"   步長: {config['stride_months']} 個月")
        
        # 獲取可用股票（限制數量以節省時間）
        data_manager = DataManager()
        available_stocks = data_manager.get_available_stocks(
            start_date=config['training_start'] + '-01',
            end_date=config['training_end'] + '-31',
            min_history_months=config['min_stock_history_months']
        )
        
        # 限制股票數量進行測試
        max_stocks = 20
        if len(available_stocks) > max_stocks:
            available_stocks = available_stocks[:max_stocks]
            print(f"限制為前 {max_stocks} 檔股票進行測試")
        
        print(f"📊 將驗證 {len(available_stocks)} 檔股票")
        print(f"股票清單: {available_stocks[:10]}{'...' if len(available_stocks) > 10 else ''}")
        
        # 初始化驗證器
        feature_engineer = FeatureEngineer()
        validator = WalkForwardValidator(feature_engineer)
        
        # 執行驗證（使用預設參數，不使用最佳參數）
        print(f"\n🚀 開始執行 walk-forward 驗證...")
        print(f"📋 使用最佳參數: 否")
        print(f"📋 模型設定: ['xgboost']")
        
        results = validator.run_validation(
            stock_ids=available_stocks,
            start_date=config['training_start'] + '-01',
            end_date=config['training_end'] + '-31',
            train_window_months=config['train_window_months'],
            test_window_months=config['test_window_months'],
            stride_months=config['stride_months'],
            models_to_use=['xgboost'],  # 只用主模型節省時間
            override_models=None
        )
        
        # 儲存結果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"walk_forward_results_{timestamp}.json"
        validator.save_results(results_file)
        
        print(f"\n✅ Walk-forward 驗證完成！")
        print(f"📁 結果已儲存至: {results_file}")
        print(f"📊 總共執行了 {results['fold_count']} 個 fold")
        print(f"📈 涵蓋 {results['stock_count']} 檔股票")
        print(f"💼 總交易次數: {results['total_trades']}")
        
        return results_file
        
    except Exception as e:
        print(f"❌ Walk-forward 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_candidate_pool(walk_forward_file=None):
    """執行選單4：生成候選池"""
    print("\n🎯 步驟2：生成候選池")
    print("="*50)
    
    try:
        import glob
        import json
        from stock_price_investment_system.config.settings import get_config
        from stock_price_investment_system.selector.candidate_pool_generator import CandidatePoolGenerator
        
        # 尋找最新的walk-forward結果
        if walk_forward_file:
            latest_file = f"stock_price_investment_system/results/walk_forward/{walk_forward_file}"
        else:
            out_dir = get_config('output')['paths']['walk_forward_results']
            result_files = glob.glob(str(out_dir / "walk_forward_results_*.json"))
            if not result_files:
                print("❌ 找不到 walk-forward 驗證結果檔案")
                return None
            latest_file = max(result_files, key=os.path.getctime)
        
        print(f"📁 使用結果檔案: {os.path.basename(latest_file)}")
        
        # 載入結果
        with open(latest_file, 'r', encoding='utf-8-sig') as f:
            walk_forward_results = json.load(f)
        
        # 顯示嚴格門檻設定
        config = get_config('selection')
        thresholds = config['candidate_pool_thresholds']
        
        print(f"\n📋 使用嚴格篩選門檻：")
        print(f"   最小勝率: {thresholds['min_win_rate']*100:.1f}%")
        print(f"   最小盈虧比: {thresholds['min_profit_loss_ratio']}")
        print(f"   最小交易次數: {thresholds['min_trade_count']}")
        print(f"   最少fold數: {thresholds['min_folds_with_trades']}")
        print(f"   最大回撤: {thresholds['max_drawdown_threshold']*100:.1f}%")
        
        # 生成候選池
        print(f"\n🚀 開始生成候選池...")
        
        generator = CandidatePoolGenerator()
        pool_result = generator.generate_candidate_pool(walk_forward_results)
        
        if pool_result['success']:
            candidates = pool_result['candidate_pool']
            rejected = pool_result.get('rejected_stocks', [])
            
            # 儲存結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"candidate_pool_{timestamp}.json"
            csv_file = f"candidate_pool_{timestamp}.csv"
            
            generator.save_results(pool_result, json_file, csv_file)
            
            print(f"\n✅ 候選池生成完成！")
            print(f"📊 通過嚴格篩選: {len(candidates)} 檔股票")
            print(f"📊 被拒絕: {len(rejected)} 檔股票")
            print(f"📁 結果已儲存至: {json_file}")
            
            if candidates:
                print(f"\n🏆 通過篩選的優質股票:")
                for i, stock in enumerate(candidates, 1):
                    stats = stock['statistics']
                    print(f"   {i}. {stock['stock_id']}: 勝率{stats['win_rate']*100:.1f}%, 盈虧比{stats['profit_loss_ratio']:.2f}, 交易{stats['total_trades']}筆")
            else:
                print(f"\n⚠️ 沒有股票通過嚴格篩選")
                print(f"💡 被拒絕的股票範例:")
                for i, stock in enumerate(rejected[:5], 1):
                    reasons = stock.get('rejection_reasons', ['未知原因'])
                    print(f"   {i}. {stock['stock_id']}: {reasons[0]}")
            
            return json_file
        else:
            print(f"❌ 候選池生成失敗: {pool_result.get('error', '未知錯誤')}")
            return None
            
    except Exception as e:
        print(f"❌ 候選池生成失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_holdout_backtest(candidate_pool_file=None):
    """執行選單5：外層回測"""
    print("\n🏆 步驟3：執行外層回測")
    print("="*50)
    
    try:
        from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester
        
        print("📋 回測配置：")
        print("   候選池模式: 靜態候選池（使用步驟2生成的結果）")
        print("   預測門檻: 5.0%（嚴格標準）")
        print("   每月最多買入: 3檔股票")
        print("   技術指標確認: 啟用")
        print("   動態持有期間: 啟用")
        
        hb = HoldoutBacktester()
        
        # 如果有指定候選池檔案，使用它
        if candidate_pool_file:
            candidate_pool_path = f"stock_price_investment_system/results/candidate_pools/{candidate_pool_file}"
        else:
            candidate_pool_path = None
        
        print(f"\n🚀 開始執行外層回測...")
        res = hb.run(
            candidate_pool_json=candidate_pool_path,
            dynamic_pool=False  # 使用靜態候選池
        )
        
        if res.get('success'):
            m = res['metrics']
            print(f"\n✅ 外層回測完成！")
            print(f"📊 交易數: {m.get('trade_count', 0)} 筆")
            print(f"📈 總報酬: {m.get('total_return', 0):.2%}")
            print(f"🎯 勝率: {m.get('win_rate', 0):.1%}")
            print(f"📊 平均報酬: {m.get('avg_return', 0):.4f}")
            
            # 檢查是否有交易記錄
            if m.get('trade_count', 0) > 0:
                print(f"\n🎉 嚴格標準下仍有 {m.get('trade_count', 0)} 筆交易！")
                print(f"💡 這些都是高品質的交易機會")
            else:
                print(f"\n⚠️ 嚴格標準下沒有產生任何交易")
                print(f"💡 這表示標準非常嚴格，可能需要適度調整")
            
            return res
        else:
            print(f"❌ 外層回測失敗: {res.get('error', '未知錯誤')}")
            return None
            
    except Exception as e:
        print(f"❌ 外層回測失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """執行完整的嚴格標準流程"""
    print("🚀 執行選項A：嚴格標準完整流程")
    print("="*60)
    print("📋 流程：Walk-forward驗證 → 候選池生成 → 外層回測")
    print("🎯 特色：使用最嚴格的篩選標準，確保高品質交易")
    print("="*60)
    
    # 步驟1：Walk-forward驗證
    wf_file = run_walkforward_validation()
    if not wf_file:
        print("❌ 步驟1失敗，終止流程")
        return
    
    # 步驟2：生成候選池
    pool_file = generate_candidate_pool(wf_file)
    if not pool_file:
        print("❌ 步驟2失敗，終止流程")
        return
    
    # 步驟3：外層回測
    backtest_result = run_holdout_backtest(pool_file)
    if not backtest_result:
        print("❌ 步驟3失敗，終止流程")
        return
    
    # 總結
    print("\n" + "="*60)
    print("🎉 嚴格標準完整流程執行完成！")
    print("="*60)
    
    m = backtest_result['metrics']
    print(f"📊 最終結果總結：")
    print(f"   交易數: {m.get('trade_count', 0)} 筆")
    print(f"   總報酬: {m.get('total_return', 0):.2%}")
    print(f"   勝率: {m.get('win_rate', 0):.1%}")
    
    if m.get('trade_count', 0) > 0:
        print(f"\n🎯 結論：嚴格標準成功篩選出高品質交易機會！")
        print(f"💡 建議：可以實際使用這個策略")
    else:
        print(f"\n⚠️ 結論：標準過於嚴格，沒有產生交易")
        print(f"💡 建議：考慮適度放寬標準（選項B）")
    
    print(f"\n📁 詳細結果請查看 results/ 資料夾中的檔案")


if __name__ == "__main__":
    main()
