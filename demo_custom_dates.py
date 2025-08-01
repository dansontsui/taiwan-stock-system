#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示自訂日期功能的使用方式
"""

def demo_custom_dates_usage():
    """演示如何使用自訂日期功能"""
    
    print("=" * 70)
    print("🎯 潛力股預測系統 - 自訂日期功能演示")
    print("=" * 70)
    
    print("\n📋 新增功能說明:")
    print("1. 系統啟動時會詢問是否使用自訂日期")
    print("2. 預設日期已更新為您要求的範圍")
    print("3. 可在選單中重新設定日期參數")
    
    print("\n🎯 預設日期設定:")
    print("   訓練期間: 2018-01-01 ~ 2023-12-31")
    print("   回測期間: 2024-01-31 ~ 2024-12-31")
    
    print("\n🚀 使用方式:")
    print("1. 執行: python backtesting_system.py")
    print("2. 系統會詢問: '是否使用自訂日期? (y/N)'")
    print("3. 選擇 'y' 可自訂日期，選擇 'N' 使用預設日期")
    print("4. 在主選單中選擇 '3. 重新設定日期參數' 可隨時修改")
    
    print("\n📊 自訂日期輸入範例:")
    print("   訓練開始日期 [2018-01-01]: 2019-01-01")
    print("   訓練結束日期 [2023-12-31]: 2023-06-30")
    print("   回測開始日期 [2024-01-31]: 2024-02-01")
    print("   回測結束日期 [2024-12-31]: 2024-11-30")
    
    print("\n⚡ 快速測試步驟:")
    print("1. cd potential_stock_predictor")
    print("2. python backtesting_system.py")
    print("3. 選擇 'y' 使用自訂日期")
    print("4. 輸入您想要的日期範圍")
    print("5. 選擇 '2. 執行單一個股回測'")
    print("6. 輸入股票代號 (如: 2330)")
    print("7. 選擇訓練模式")
    
    print("\n🎯 主要改進:")
    print("✓ 預設訓練期間延長至 2018-2023 (6年資料)")
    print("✓ 回測期間涵蓋整個 2024 年")
    print("✓ 支援完全自訂日期範圍")
    print("✓ 可在執行過程中重新設定日期")
    print("✓ 保持所有原有功能不變")
    
    print("\n📋 選單功能:")
    print("1. 執行完整投資組合回測")
    print("2. 執行單一個股回測")
    print("3. 重新設定日期參數  ← 新增功能")
    print("4. 查看系統狀態")
    print("5. 退出系統")
    
    print("\n🔍 日期驗證:")
    print("✓ 自動驗證日期格式 (YYYY-MM-DD)")
    print("✓ 確保訓練期間在回測期間之前")
    print("✓ 支援不同長度的訓練和回測期間")
    
    print("\n💡 使用建議:")
    print("• 訓練期間建議至少 3-5 年以獲得足夠樣本")
    print("• 回測期間可根據需要調整 (季度/年度)")
    print("• 首次使用建議先用預設日期測試")
    print("• 確認資料庫中有對應期間的股價資料")
    
    print("\n" + "=" * 70)
    print("🎉 自訂日期功能已完成！可以開始使用了！")
    print("=" * 70)

def show_date_examples():
    """顯示日期設定範例"""
    
    print("\n📅 常用日期設定範例:")
    print("-" * 50)
    
    examples = [
        {
            'name': '標準設定 (您的需求)',
            'train_start': '2018-01-01',
            'train_end': '2023-12-31',
            'backtest_start': '2024-01-31',
            'backtest_end': '2024-12-31',
            'description': '6年訓練資料，2024年完整回測'
        },
        {
            'name': '短期測試',
            'train_start': '2020-01-01',
            'train_end': '2023-12-31',
            'backtest_start': '2024-01-31',
            'backtest_end': '2024-06-30',
            'description': '4年訓練資料，2024上半年回測'
        },
        {
            'name': '長期分析',
            'train_start': '2015-01-01',
            'train_end': '2023-12-31',
            'backtest_start': '2024-01-31',
            'backtest_end': '2024-12-31',
            'description': '9年訓練資料，2024年完整回測'
        },
        {
            'name': '季度回測',
            'train_start': '2018-01-01',
            'train_end': '2023-12-31',
            'backtest_start': '2024-01-31',
            'backtest_end': '2024-03-31',
            'description': '6年訓練資料，2024第一季回測'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}:")
        print(f"   訓練期間: {example['train_start']} ~ {example['train_end']}")
        print(f"   回測期間: {example['backtest_start']} ~ {example['backtest_end']}")
        print(f"   說明: {example['description']}")

if __name__ == "__main__":
    demo_custom_dates_usage()
    show_date_examples()
    
    print(f"\n🚀 準備好了嗎？執行以下命令開始使用:")
    print(f"   cd potential_stock_predictor")
    print(f"   python backtesting_system.py")
