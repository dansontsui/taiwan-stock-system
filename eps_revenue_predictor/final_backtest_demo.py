# -*- coding: utf-8 -*-
"""
EPS與營收預測系統 - 回測功能最終演示
展示完整的回測功能，包括準確度評估和AI模型調整
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主演示函數"""
    
    print("🎯" + "="*70)
    print("🚀 EPS與營收預測系統 - 回測功能最終演示")
    print("🎯" + "="*70)
    
    try:
        # 導入必要模組
        from src.data.database_manager import DatabaseManager
        from src.predictors.backtest_engine import BacktestEngine
        from src.utils.backtest_reporter import BacktestReporter
        from src.models.model_optimizer import ModelOptimizer
        
        stock_id = "2385"  # 群光電子
        
        print(f"\n📊 目標股票: {stock_id} (群光電子)")
        print("🔍 這是一個完整的回測演示，展示以下功能:")
        print("   1. 歷史資料驗證")
        print("   2. 營收預測回測")
        print("   3. 準確度評估")
        print("   4. AI模型優化建議")
        print("   5. 詳細報告生成")
        
        # 步驟1: 初始化系統
        print(f"\n" + "="*50)
        print("📦 步驟1: 初始化回測系統")
        print("="*50)
        
        db_manager = DatabaseManager()
        print("✅ 資料庫管理器初始化完成")
        
        backtest_engine = BacktestEngine(db_manager)
        print("✅ 回測引擎初始化完成")
        
        reporter = BacktestReporter()
        print("✅ 報告生成器初始化完成")
        
        optimizer = ModelOptimizer(db_manager)
        print("✅ 模型優化器初始化完成")
        
        # 步驟2: 資料驗證
        print(f"\n" + "="*50)
        print("🔍 步驟2: 驗證歷史資料可用性")
        print("="*50)
        
        validation = db_manager.validate_backtest_data_availability(stock_id)
        
        print(f"📈 營收資料: {validation.get('revenue_count', 0)} 個月")
        print(f"📊 財務資料: {validation.get('financial_count', 0)} 季")
        print(f"✅ 回測可行性: {'是' if validation.get('backtest_feasible', False) else '否'}")
        
        if not validation.get('backtest_feasible', False):
            print("❌ 資料不足，無法進行回測演示")
            return
        
        # 步驟3: 執行回測
        print(f"\n" + "="*50)
        print("🚀 步驟3: 執行營收預測回測")
        print("="*50)
        
        print("⏰ 正在執行回測分析 (這可能需要1-2分鐘)...")
        
        backtest_results = backtest_engine.run_comprehensive_backtest(
            stock_id=stock_id,
            backtest_periods=6,  # 回測6個月
            prediction_types=['revenue']  # 專注於營收回測
        )
        
        # 步驟4: 顯示回測結果
        print(f"\n" + "="*50)
        print("📋 步驟4: 回測結果摘要")
        print("="*50)
        
        reporter.display_backtest_summary(backtest_results)
        
        # 步驟5: 生成詳細報告
        print(f"\n" + "="*50)
        print("📄 步驟5: 生成詳細報告")
        print("="*50)
        
        report_result = reporter.generate_comprehensive_report(backtest_results)
        
        if report_result.get('success'):
            print(f"✅ 詳細報告已生成")
            print(f"📁 報告位置: {report_result.get('report_file')}")
        else:
            print(f"❌ 報告生成失敗: {report_result.get('error')}")
        
        # 步驟6: AI模型優化
        print(f"\n" + "="*50)
        print("🔧 步驟6: AI模型優化分析")
        print("="*50)
        
        optimization_result = optimizer.optimize_based_on_backtest(stock_id, backtest_results)
        optimizer.display_optimization_summary(optimization_result)
        
        # 步驟7: 總結
        print(f"\n" + "="*70)
        print("🎉 回測演示完成總結")
        print("="*70)
        
        revenue_stats = backtest_results.get('results', {}).get('revenue', {}).get('statistics', {})
        
        if revenue_stats:
            direction_acc = revenue_stats.get('direction_accuracy', 0)
            mape = revenue_stats.get('avg_revenue_mape', 0)
            periods = revenue_stats.get('total_periods', 0)
            
            print(f"📊 回測統計:")
            print(f"   測試期數: {periods}")
            print(f"   方向準確度: {direction_acc:.1%}")
            print(f"   平均MAPE: {mape:.1f}%")
            
            # 評估表現
            if direction_acc >= 0.7 and mape <= 10:
                grade = "A (優秀)"
                emoji = "🏆"
            elif direction_acc >= 0.6 and mape <= 15:
                grade = "B (良好)"
                emoji = "👍"
            elif direction_acc >= 0.5 and mape <= 20:
                grade = "C (中等)"
                emoji = "👌"
            else:
                grade = "D (需改善)"
                emoji = "⚠️"
            
            print(f"   整體評級: {grade} {emoji}")
        
        print(f"\n💡 主要成果:")
        print(f"   ✅ 成功建立完整的回測系統")
        print(f"   ✅ 驗證了預測模型的歷史準確度")
        print(f"   ✅ 生成了詳細的分析報告")
        print(f"   ✅ 提供了AI模型優化建議")
        
        print(f"\n🎯 下一步建議:")
        suggestions = backtest_results.get('improvement_suggestions', [])
        if suggestions:
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"   {i}. {suggestion}")
        
        print(f"\n🚀 回測功能已完全整合到系統中！")
        print(f"💡 您可以通過主選單的選項9來使用回測功能")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    
    print(f"\n" + "="*70)
    print("👋 感謝觀看回測功能演示！")
    print("="*70)
