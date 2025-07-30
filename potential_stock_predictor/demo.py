#!/usr/bin/env python3
"""
潛力股預測系統示範程式

展示系統的基本功能和使用方法
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# 添加專案路徑
sys.path.append(str(Path(__file__).parent))

try:
    # 添加當前目錄到 Python 路徑
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    from src.utils.database import DatabaseManager
    from src.features.feature_engineering import FeatureEngineer
    from src.features.target_generator import TargetGenerator
    from src.utils.logger import setup_logger
    from config.config import ensure_directories
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保已安裝必要的依賴套件:")
    print("pip install pandas numpy scikit-learn matplotlib tqdm python-dateutil joblib")
    print("\n如果依賴套件已安裝，可能是模組路徑問題。")
    print("請確保在 potential_stock_predictor 目錄下執行此程式。")
    sys.exit(1)

def main():
    """主示範程式"""
    print("🚀 潛力股預測系統示範")
    print("=" * 60)
    
    # 設置日誌
    logger = setup_logger('demo')
    
    # 確保目錄存在
    ensure_directories()
    
    try:
        # 1. 測試資料庫連接
        print("\n📊 1. 測試資料庫連接...")
        db_manager = DatabaseManager()
        
        # 獲取股票清單
        stock_list = db_manager.get_stock_list(exclude_patterns=['00'])
        print(f"   ✅ 成功連接資料庫，共 {len(stock_list)} 個股票")
        
        # 顯示前5個股票
        print("   📋 股票清單樣本:")
        for _, stock in stock_list.head(5).iterrows():
            print(f"      {stock['stock_id']} - {stock['stock_name']} ({stock['market']})")
        
        # 2. 測試特徵工程
        print("\n🔬 2. 測試特徵工程...")
        feature_engineer = FeatureEngineer(db_manager)
        
        # 選擇測試股票
        test_stocks = ['2330', '2317', '2454']  # 台積電、鴻海、聯發科
        test_date = '2024-06-30'
        
        print(f"   測試股票: {', '.join(test_stocks)}")
        print(f"   特徵日期: {test_date}")
        
        successful_features = 0
        for stock_id in test_stocks:
            try:
                features = feature_engineer.generate_features(stock_id, test_date)
                if not features.empty:
                    feature_count = len(features.columns) - 2  # 排除stock_id和feature_date
                    print(f"   ✅ {stock_id}: 生成 {feature_count} 個特徵")
                    successful_features += 1
                else:
                    print(f"   ⚠️ {stock_id}: 無法生成特徵（資料不足）")
            except Exception as e:
                print(f"   ❌ {stock_id}: 特徵生成失敗 - {str(e)[:50]}...")
        
        print(f"   📊 成功率: {successful_features}/{len(test_stocks)}")
        
        # 3. 測試目標變數生成
        print("\n🎯 3. 測試目標變數生成...")
        target_generator = TargetGenerator(db_manager)
        
        feature_dates = ['2024-03-31', '2024-06-30']
        print(f"   測試日期: {', '.join(feature_dates)}")
        
        successful_targets = 0
        all_targets = []
        
        for stock_id in test_stocks:
            try:
                targets = target_generator.generate_targets(stock_id, feature_dates)
                if not targets.empty:
                    print(f"   ✅ {stock_id}: 生成 {len(targets)} 個目標變數")
                    all_targets.append(targets)
                    successful_targets += 1
                else:
                    print(f"   ⚠️ {stock_id}: 無法生成目標變數")
            except Exception as e:
                print(f"   ❌ {stock_id}: 目標變數生成失敗 - {str(e)[:50]}...")
        
        if all_targets:
            combined_targets = pd.concat(all_targets, ignore_index=True)
            positive_ratio = combined_targets['target'].mean()
            avg_return = combined_targets['max_return'].mean()
            print(f"   📊 目標變數統計:")
            print(f"      總樣本: {len(combined_targets)}")
            print(f"      正樣本比例: {positive_ratio:.2%}")
            print(f"      平均最大報酬率: {avg_return:.2%}")
        
        # 4. 測試系統整合
        print("\n🔧 4. 測試系統整合...")
        
        # 檢查配置
        from config.config import MODEL_CONFIG, FEATURE_CONFIG, PREDICTION_CONFIG
        print(f"   ✅ 配置載入成功")
        print(f"      支援模型: {', '.join(MODEL_CONFIG['model_types'])}")
        print(f"      預設模型: {MODEL_CONFIG['default_model']}")
        print(f"      預測天數: {FEATURE_CONFIG['target_definition']['prediction_days']}")
        print(f"      目標報酬率: {FEATURE_CONFIG['target_definition']['target_return']:.1%}")
        
        # 5. 系統狀態總結
        print("\n📋 5. 系統狀態總結")
        print("   ✅ 資料庫連接: 正常")
        print(f"   ✅ 特徵工程: {successful_features}/{len(test_stocks)} 成功")
        print(f"   ✅ 目標變數: {successful_targets}/{len(test_stocks)} 成功")
        print("   ✅ 配置載入: 正常")
        print("   ✅ 目錄結構: 完整")
        
        # 6. 下一步建議
        print("\n🚀 6. 下一步建議")
        print("   1. 執行完整的特徵生成:")
        print("      python main.py generate-features --date 2024-06-30")
        print("   2. 生成目標變數:")
        print("      python main.py generate-targets --start-date 2022-01-01 --end-date 2024-06-30")
        print("   3. 訓練模型:")
        print("      python main.py train-models --features-file <features.csv> --targets-file <targets.csv>")
        print("   4. 執行預測:")
        print("      python main.py predict --model lightgbm")
        print("   5. 生成排行榜:")
        print("      python main.py ranking --top-k 50")
        
        print("\n🎉 潛力股預測系統示範完成！")
        
    except Exception as e:
        print(f"\n❌ 示範過程中發生錯誤: {e}")
        logger.error(f"示範失敗: {e}")
        raise

if __name__ == "__main__":
    main()
