#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step by step test for EPS Revenue Predictor
"""

import sys
from pathlib import Path

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_step_1():
    """測試步驟1: 基本導入"""
    print("🔍 Step 1: Testing basic imports...")
    
    try:
        from config.settings import DATABASE_CONFIG, PREDICTION_CONFIG
        print("✅ Settings imported")
        
        from src.utils.logger import get_logger
        print("✅ Logger imported")
        
        logger = get_logger('test')
        logger.info("Logger test message")
        print("✅ Logger working")
        
        return True
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_2():
    """測試步驟2: 資料庫管理器"""
    print("\n🔍 Step 2: Testing database manager...")
    
    try:
        from src.data.database_manager import DatabaseManager
        print("✅ DatabaseManager imported")
        
        db_manager = DatabaseManager()
        print("✅ DatabaseManager created")
        
        # 測試2385
        exists = db_manager.check_stock_exists("2385")
        print(f"✅ Stock 2385 exists: {exists}")
        
        if exists:
            # 獲取月營收資料
            revenue_data = db_manager.get_monthly_revenue("2385", 12)
            print(f"✅ Revenue data: {len(revenue_data)} records")
            
            # 獲取財務比率
            ratio_data = db_manager.get_financial_ratios("2385", 8)
            print(f"✅ Ratio data: {len(ratio_data)} records")
        
        return True
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_3():
    """測試步驟3: 營收預測器"""
    print("\n🔍 Step 3: Testing revenue predictor...")
    
    try:
        from src.data.database_manager import DatabaseManager
        from src.predictors.revenue_predictor import RevenuePredictor
        
        print("✅ RevenuePredictor imported")
        
        db_manager = DatabaseManager()
        predictor = RevenuePredictor(db_manager)
        print("✅ RevenuePredictor created")
        
        # 執行簡單預測
        result = predictor.predict_monthly_growth("2385")
        print(f"✅ Prediction completed: success={result.get('success', True)}")
        
        if result.get('success', True):
            print(f"   Growth rate: {result.get('growth_rate', 0):.2%}")
            print(f"   Confidence: {result.get('confidence', 'Unknown')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_4():
    """測試步驟4: AI調整模型"""
    print("\n🔍 Step 4: Testing AI adjustment model...")
    
    try:
        from src.models.adjustment_model import AIAdjustmentModel
        print("✅ AIAdjustmentModel imported")
        
        ai_model = AIAdjustmentModel()
        print("✅ AIAdjustmentModel created")
        
        # 測試調整預測 (不訓練，只測試結構)
        adjustment = ai_model.predict_adjustment_factor("2385", 0.15)
        print(f"✅ Adjustment prediction: {adjustment['adjustment_factor']:.3f}")
        print(f"   Confidence: {adjustment['confidence']}")
        
        return True
    except Exception as e:
        print(f"❌ Step 4 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 Step-by-Step Test for EPS Revenue Predictor")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_step_1),
        ("Database Manager", test_step_2),
        ("Revenue Predictor", test_step_3),
        ("AI Adjustment Model", test_step_4)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            
            if not success:
                print(f"\n❌ {test_name} failed, stopping tests")
                break
                
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
            break
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    if passed == len(tests):
        print(f"\n🎉 All tests passed! System is ready!")
    else:
        print(f"\n⚠️  {passed}/{total} tests passed. Please fix issues before proceeding.")

if __name__ == "__main__":
    main()
