# -*- coding: utf-8 -*-
"""
緊急診斷EPS預測問題
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_eps_issue():
    """緊急診斷EPS預測問題"""
    
    print("🚨 緊急診斷EPS預測問題")
    print("=" * 60)
    
    try:
        from src.data.database_manager import DatabaseManager
        from src.predictors.eps_predictor import EPSPredictor
        from src.predictors.backtest_engine import BacktestEngine
        
        stock_id = "8299"
        
        print(f"📊 診斷股票: {stock_id}")
        
        # 初始化組件
        db_manager = DatabaseManager()
        eps_predictor = EPSPredictor(db_manager)
        backtest_engine = BacktestEngine(db_manager)
        
        # 步驟1: 檢查EPS資料是否存在
        print(f"\n1. 檢查EPS資料...")
        
        query = """
        SELECT date, value as eps
        FROM financial_statements
        WHERE stock_id = ? AND type = 'EPS'
        ORDER BY date DESC
        LIMIT 5
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (stock_id,))
            eps_results = cursor.fetchall()
            
            if eps_results:
                print(f"   ✅ 找到EPS資料: {len(eps_results)}筆")
                for date, eps in eps_results:
                    print(f"     {date}: {eps}")
            else:
                print(f"   ❌ 沒有找到EPS資料")
                return False
        
        # 步驟2: 測試單次EPS預測
        print(f"\n2. 測試單次EPS預測...")
        
        try:
            prediction = eps_predictor.predict_quarterly_growth(stock_id, "2025-Q2")
            
            print(f"   預測結果:")
            print(f"   成功: {prediction.get('success', True)}")
            print(f"   預測EPS: {prediction.get('predicted_eps', 0)}")
            print(f"   成長率: {prediction.get('growth_rate', 0)*100:.1f}%")
            print(f"   信心水準: {prediction.get('confidence', 'Unknown')}")
            
            if prediction.get('error'):
                print(f"   錯誤: {prediction.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 單次預測失敗: {e}")
            import traceback
            traceback.print_exc()
        
        # 步驟3: 測試EPS回測
        print(f"\n3. 測試EPS回測...")
        
        try:
            eps_backtest = backtest_engine.run_comprehensive_backtest(
                stock_id=stock_id,
                backtest_periods=4,  # 減少期數
                prediction_types=['eps']
            )
            
            eps_results = eps_backtest.get('results', {}).get('eps', {})
            
            print(f"   回測結果:")
            print(f"   成功: {eps_results.get('success', False)}")
            print(f"   錯誤: {eps_results.get('error', 'None')}")
            print(f"   資料點數: {eps_results.get('data_points', 0)}")
            
            if eps_results.get('success', False):
                backtest_data = eps_results.get('backtest_results', [])
                print(f"   回測期數: {len(backtest_data)}")
                
                for i, result in enumerate(backtest_data, 1):
                    prediction = result.get('prediction', {})
                    actual = result.get('actual', {})
                    
                    target_quarter = result.get('target_quarter', 'N/A')
                    predicted_eps = prediction.get('predicted_eps', 0)
                    actual_eps = actual.get('actual_eps', 0)
                    
                    print(f"     期數{i}: {target_quarter} | 預測={predicted_eps:.2f} | 實際={actual_eps:.2f}")
            
        except Exception as e:
            print(f"   ❌ EPS回測失敗: {e}")
            import traceback
            traceback.print_exc()
        
        # 步驟4: 檢查季度財務資料
        print(f"\n4. 檢查季度財務資料...")
        
        try:
            quarterly_data = db_manager.get_quarterly_financial_data(stock_id)
            
            print(f"   季度財務資料:")
            print(f"   資料筆數: {len(quarterly_data)}")
            
            if not quarterly_data.empty:
                print(f"   欄位: {list(quarterly_data.columns)}")
                print(f"   最新5筆:")
                for i, row in quarterly_data.tail(5).iterrows():
                    date = row['date']
                    eps = row.get('eps', 'N/A')
                    print(f"     {date}: EPS={eps}")
            else:
                print(f"   ❌ 沒有季度財務資料")
                
        except Exception as e:
            print(f"   ❌ 季度財務資料查詢失敗: {e}")
            import traceback
            traceback.print_exc()
        
        # 步驟5: 檢查綜合資料
        print(f"\n5. 檢查綜合資料...")
        
        try:
            comprehensive_data = db_manager.get_comprehensive_data(stock_id)
            
            print(f"   綜合資料:")
            for key, value in comprehensive_data.items():
                if hasattr(value, '__len__'):
                    print(f"     {key}: {len(value)} 筆")
                else:
                    print(f"     {key}: {value}")
            
            # 檢查EPS資料
            eps_data = comprehensive_data.get('eps_data', None)
            if eps_data is not None and not eps_data.empty:
                print(f"   EPS資料詳情:")
                print(f"     筆數: {len(eps_data)}")
                print(f"     欄位: {list(eps_data.columns)}")
                print(f"     最新EPS: {eps_data['eps'].iloc[-1] if 'eps' in eps_data.columns else 'N/A'}")
            else:
                print(f"   ❌ 綜合資料中沒有EPS資料")
                
        except Exception as e:
            print(f"   ❌ 綜合資料查詢失敗: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n" + "="*60)
        print(f"🎯 診斷總結:")
        
        # 根據檢查結果給出診斷
        if eps_results:
            print(f"✅ 基礎EPS資料: 正常")
        else:
            print(f"❌ 基礎EPS資料: 缺失")
        
        # 這裡會根據上面的測試結果給出具體的問題診斷
        print(f"📋 建議檢查:")
        print(f"   1. 資料庫連接是否正常")
        print(f"   2. EPS預測器初始化是否成功")
        print(f"   3. 回測引擎邏輯是否正確")
        print(f"   4. 資料格式是否匹配")
        
        print(f"=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_eps_issue()
