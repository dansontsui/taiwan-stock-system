# -*- coding: utf-8 -*-
"""
診斷回測預測數字異常問題
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def diagnose_backtest_issue():
    """診斷回測預測數字異常問題"""
    
    print("🔍 診斷回測預測數字異常問題")
    print("=" * 80)
    
    try:
        from src.data.database_manager import DatabaseManager
        from src.predictors.revenue_predictor import RevenuePredictor
        
        stock_id = "2385"
        
        print(f"📊 診斷股票: {stock_id}")
        
        # 初始化組件
        db_manager = DatabaseManager()
        revenue_predictor = RevenuePredictor(db_manager)
        
        # 1. 檢查歷史資料
        print(f"\n1. 檢查歷史營收資料...")
        historical_data = db_manager.get_monthly_revenue_data(stock_id)
        print(f"   歷史資料筆數: {len(historical_data)}")
        
        if len(historical_data) > 0:
            print(f"   資料範圍: {historical_data['date'].min()} ~ {historical_data['date'].max()}")
            print(f"   最新10筆營收資料:")
            for _, row in historical_data.tail(10).iterrows():
                revenue_billion = row['revenue'] / 1e8
                print(f"     {row['date']}: {revenue_billion:.1f}億")
        
        # 2. 測試不同時間點的預測
        print(f"\n2. 測試不同時間點的營收預測...")
        
        # 模擬回測的時間點
        latest_date = historical_data['date'].max()
        print(f"   最新資料日期: {latest_date}")
        
        test_dates = []
        for i in range(6):
            backtest_date = latest_date - timedelta(days=30 * (6 - i))
            target_date = backtest_date + timedelta(days=30)
            test_dates.append((backtest_date, target_date))
        
        print(f"\n   測試不同回測時間點的預測:")
        print(f"   {'回測日期':<12} {'目標月份':<12} {'預測營收(億)':<12} {'成長率':<10} {'信心':<8}")
        print(f"   {'-'*60}")
        
        for i, (backtest_date, target_date) in enumerate(test_dates, 1):
            target_month = target_date.strftime('%Y-%m')
            
            # 執行預測
            prediction = revenue_predictor.predict_monthly_growth(stock_id, target_month)
            
            if prediction.get('success', True):
                pred_revenue = prediction['predicted_revenue'] / 1e8
                growth_rate = prediction['growth_rate'] * 100
                confidence = prediction['confidence']
                
                print(f"   {backtest_date.strftime('%Y-%m-%d'):<12} {target_month:<12} {pred_revenue:<12.1f} {growth_rate:<10.1f}% {confidence:<8}")
            else:
                print(f"   {backtest_date.strftime('%Y-%m-%d'):<12} {target_month:<12} {'失敗':<12} {'-':<10} {'-':<8}")
        
        # 3. 檢查預測方法的內部邏輯
        print(f"\n3. 檢查預測方法的內部邏輯...")
        
        # 測試單一預測的詳細資訊
        test_target = "2025-07"
        print(f"   詳細分析目標月份: {test_target}")
        
        prediction = revenue_predictor.predict_monthly_growth(stock_id, test_target)
        
        if prediction.get('success', True):
            print(f"   預測營收: {prediction['predicted_revenue']/1e8:.1f}億")
            print(f"   成長率: {prediction['growth_rate']*100:.1f}%")
            print(f"   信心水準: {prediction['confidence']}")
            
            # 檢查方法分解
            method_breakdown = prediction.get('method_breakdown', {})
            if method_breakdown:
                print(f"   方法分解:")
                for method, details in method_breakdown.items():
                    growth = details.get('growth', 0) * 100
                    confidence = details.get('confidence', 'Unknown')
                    print(f"     {method}: {growth:.1f}% (信心: {confidence})")
            
            # 檢查權重
            weights = prediction.get('weights_used', {})
            if weights:
                print(f"   權重分配: {weights}")
        
        # 4. 檢查是否每次都使用相同的資料
        print(f"\n4. 檢查資料使用情況...")
        
        # 檢查最近12個月的資料
        recent_data = db_manager.get_monthly_revenue(stock_id)
        if len(recent_data) > 0:
            print(f"   最近12個月資料:")
            for _, row in recent_data.tail(12).iterrows():
                revenue_billion = row['revenue'] / 1e8
                print(f"     {row['date']}: {revenue_billion:.1f}億")
        
        # 5. 問題總結
        print(f"\n" + "="*80)
        print(f"🎯 問題分析總結:")
        print(f"1. 回測執行模式問題:")
        print(f"   - 每次預測都調用 predict_monthly_growth()")
        print(f"   - 但沒有限制資料範圍到回測時間點")
        print(f"   - 預測器可能每次都使用最新的完整資料")
        
        print(f"\n2. 預測方法問題:")
        print(f"   - 如果預測方法過度依賴最新資料")
        print(f"   - 或者權重分配導致結果趨同")
        print(f"   - 可能產生相似的預測值")
        
        print(f"\n3. 資料時間範圍問題:")
        print(f"   - 回測應該只使用回測時間點之前的資料")
        print(f"   - 但目前可能使用了未來資料")
        print(f"=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = diagnose_backtest_issue()
    if success:
        print("\n✅ 診斷完成")
    else:
        print("\n❌ 診斷失敗")
