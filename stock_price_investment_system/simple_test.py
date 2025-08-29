#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("開始簡單測試...")

try:
    from price_models.holdout_backtester import HoldoutBacktester
    print("✅ HoldoutBacktester 導入成功")
    
    backtester = HoldoutBacktester()
    print("✅ HoldoutBacktester 初始化成功")
    
    # 測試 _calculate_monthly_investment_metrics 函式
    empty_results = []
    metrics = backtester._calculate_monthly_investment_metrics(empty_results, 1000000)
    print(f"✅ 空結果測試: {type(metrics)}")
    print(f"   total_invested: {metrics.get('total_invested', 'N/A')}")
    
    # 測試有結果的情況
    test_results = [{
        'month': '2025-03',
        'investment_amount': 333333,
        'month_end_value': 350000,
        'return_rate': 0.05,
        'trades': [{'stock_id': '2442', 'investment_amount': 333333}]
    }]
    
    metrics2 = backtester._calculate_monthly_investment_metrics(test_results, 1000000)
    print(f"✅ 有結果測試: {type(metrics2)}")
    print(f"   total_invested: {metrics2.get('total_invested', 'N/A')}")
    print(f"   total_trades: {metrics2.get('total_trades', 'N/A')}")
    
    print("🎉 基本功能測試通過！")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
