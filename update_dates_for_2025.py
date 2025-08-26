# -*- coding: utf-8 -*-
"""
更新系統日期配置為2025年回測設定
回測期間：2025年1-7月
推論期間：2025年8月
"""

import sys
sys.path.append('stock_price_investment_system')

def update_dates_for_2025():
    """更新日期配置為2025年設定"""
    print("更新系統日期配置為2025年...")
    print("=" * 60)
    
    # 讀取當前配置檔案
    config_file = 'stock_price_investment_system/config/settings.py'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 當前配置:")
        print("  訓練期間: 2015-01 ~ 2022-12")
        print("  外層回測: 2023-01 ~ 2024-12")
        
        print("\n🎯 新配置:")
        print("  訓練期間: 2015-01 ~ 2024-12 (擴展到2024年)")
        print("  外層回測: 2025-01 ~ 2025-07 (2025年1-7月)")
        print("  推論期間: 2025-08 (8月)")
        
        # 更新配置
        updates = [
            # 更新訓練結束日期到2024年
            ("'training_end': '2022-12'", "'training_end': '2024-12'"),
            
            # 更新外層回測期間到2025年1-7月
            ("'holdout_start': '2023-01'", "'holdout_start': '2025-01'"),
            ("'holdout_end': '2024-12'", "'holdout_end': '2025-07'"),
            
            # 更新選單描述
            ("'執行內層 walk-forward（訓練期：2015–2022）'", "'執行內層 walk-forward（訓練期：2015–2024）'"),
            ("'執行外層回測（2023–2024）'", "'執行外層回測（2025年1-7月）'"),
        ]
        
        updated_content = content
        for old, new in updates:
            if old in updated_content:
                updated_content = updated_content.replace(old, new)
                print(f"✅ 更新: {old} -> {new}")
            else:
                print(f"⚠️  未找到: {old}")
        
        # 寫回檔案
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"\n✅ 配置檔案已更新: {config_file}")
        
        # 顯示建議的執行順序
        print("\n" + "=" * 60)
        print("📋 建議執行順序（2025年設定）:")
        print("=" * 60)
        print("1. 選單9: 超參數調優")
        print("   - 使用2015-2024年資料找最佳參數")
        print("")
        print("2. 選單3: 內層 walk-forward")
        print("   - 訓練期: 2015-2024年")
        print("   - 驗證模型穩健性")
        print("")
        print("3. 選單4: 生成候選池")
        print("   - 基於內層結果篩選優質股票")
        print("")
        print("4. 選單5: 外層回測")
        print("   - 回測期間: 2025年1-7月")
        print("   - 驗證策略在2025年的表現")
        print("")
        print("5. 推論8月:")
        print("   - 使用截至2025年7月的資料")
        print("   - 預測2025年8月的投資標的")
        print("")
        print("⚠️  注意事項:")
        print("- 確保資料庫包含2025年1-7月的完整資料")
        print("- 8月推論需要7月底的最新資料")
        print("- 可能需要調整候選池門檻以適應2025年市況")
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        import traceback
        traceback.print_exc()

def show_current_config():
    """顯示當前配置"""
    try:
        from stock_price_investment_system.config.settings import get_config
        
        wf_config = get_config('walkforward')
        
        print("\n📊 當前系統配置:")
        print("-" * 40)
        print(f"訓練開始: {wf_config['training_start']}")
        print(f"訓練結束: {wf_config['training_end']}")
        print(f"外層回測開始: {wf_config['holdout_start']}")
        print(f"外層回測結束: {wf_config['holdout_end']}")
        print(f"訓練視窗: {wf_config['train_window_months']}個月")
        print(f"測試視窗: {wf_config['test_window_months']}個月")
        print(f"步長: {wf_config['stride_months']}個月")
        
    except Exception as e:
        print(f"❌ 讀取配置失敗: {e}")

if __name__ == "__main__":
    # 顯示當前配置
    show_current_config()
    
    # 詢問是否更新
    response = input("\n是否要更新為2025年配置？ (y/N): ").strip().lower()
    
    if response in ['y', 'yes', '是']:
        update_dates_for_2025()
        print("\n" + "=" * 60)
        print("🔄 重新載入配置...")
        show_current_config()
    else:
        print("❌ 取消更新")
