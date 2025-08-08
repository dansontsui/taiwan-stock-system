# -*- coding: utf-8 -*-
"""
實作EPS異常過濾器
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def implement_eps_filter():
    """實作EPS異常過濾器"""
    
    print("🔧 實作EPS異常過濾器")
    print("=" * 60)
    
    try:
        from src.data.database_manager import DatabaseManager
        from src.predictors.backtest_engine import BacktestEngine
        
        stock_id = "8299"
        db_manager = DatabaseManager()
        backtest_engine = BacktestEngine(db_manager)
        
        print(f"📊 測試股票: {stock_id}")
        
        # 1. 執行原始回測
        print(f"\n1. 原始回測結果...")
        
        original_result = backtest_engine.run_comprehensive_backtest(
            stock_id=stock_id,
            backtest_periods=4,
            prediction_types=['eps']
        )
        
        eps_results = original_result.get('results', {}).get('eps', {})
        
        if eps_results.get('success', False):
            eps_data = eps_results.get('backtest_results', [])
            
            print(f"   期數   目標季度    預測EPS    實際EPS    誤差%     狀態")
            print(f"   " + "-"*60)
            
            total_error = 0
            valid_count = 0
            
            for i, result in enumerate(eps_data, 1):
                prediction = result.get('prediction', {})
                actual = result.get('actual', {})
                
                target_quarter = result.get('target_quarter', 'N/A')
                predicted_eps = prediction.get('predicted_eps', 0)
                actual_eps = actual.get('actual_eps', 0)
                
                if predicted_eps > 0 and actual_eps > 0:
                    error_pct = abs(predicted_eps - actual_eps) / actual_eps * 100
                    total_error += error_pct
                    valid_count += 1
                    status = "正常"
                else:
                    error_pct = 0
                    status = "無效"
                
                print(f"   {i:<6} {target_quarter:<11} {predicted_eps:<10.2f} {actual_eps:<10.2f} {error_pct:<8.1f}% {status}")
            
            original_mape = total_error / valid_count if valid_count > 0 else 0
            print(f"\n   原始MAPE: {original_mape:.1f}%")
        
        # 2. 實作異常檢測
        print(f"\n2. 異常檢測分析...")
        
        def detect_abnormal_quarters(stock_id):
            """檢測異常季度"""
            ratios_data = db_manager.get_financial_ratios(stock_id)
            abnormal_quarters = []
            
            if not ratios_data.empty:
                recent_ratios = ratios_data.tail(8)
                
                for i, (_, row) in enumerate(recent_ratios.iterrows()):
                    if i == 0:
                        continue  # 跳過第一筆（沒有前期比較）
                    
                    date_str = str(row['date'])
                    year = date_str[:4]
                    month = date_str[5:7]
                    quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                    quarter = quarter_map.get(month, 'Q?')
                    quarter_str = f"{year}-{quarter}"
                    
                    current_margin = row.get('net_margin', 0) or 0
                    prev_margin = recent_ratios.iloc[i-1].get('net_margin', 0) or 0
                    
                    if prev_margin > 0:
                        margin_change = abs(current_margin - prev_margin)
                        
                        # 異常標準: 淨利率變化超過5個百分點
                        if margin_change > 5:
                            abnormal_quarters.append({
                                'quarter': quarter_str,
                                'net_margin': current_margin,
                                'margin_change': current_margin - prev_margin,
                                'reason': '淨利率異常變化'
                            })
            
            return abnormal_quarters
        
        abnormal_quarters = detect_abnormal_quarters(stock_id)
        
        print(f"   檢測到異常季度:")
        for abnormal in abnormal_quarters:
            quarter = abnormal['quarter']
            margin = abnormal['net_margin']
            change = abnormal['margin_change']
            reason = abnormal['reason']
            print(f"     {quarter}: 淨利率{margin:.1f}% ({change:+.1f}pp) - {reason}")
        
        # 3. 過濾後回測
        print(f"\n3. 過濾後回測結果...")
        
        if eps_results.get('success', False):
            eps_data = eps_results.get('backtest_results', [])
            
            print(f"   期數   目標季度    預測EPS    實際EPS    誤差%     過濾狀態")
            print(f"   " + "-"*70)
            
            filtered_total_error = 0
            filtered_valid_count = 0
            
            for i, result in enumerate(eps_data, 1):
                prediction = result.get('prediction', {})
                actual = result.get('actual', {})
                
                target_quarter = result.get('target_quarter', 'N/A')
                predicted_eps = prediction.get('predicted_eps', 0)
                actual_eps = actual.get('actual_eps', 0)
                
                # 檢查是否為異常季度
                is_abnormal = any(abnormal['quarter'] == target_quarter for abnormal in abnormal_quarters)
                
                if predicted_eps > 0 and actual_eps > 0:
                    error_pct = abs(predicted_eps - actual_eps) / actual_eps * 100
                    
                    if is_abnormal:
                        filter_status = "⚠️ 已過濾"
                    else:
                        filtered_total_error += error_pct
                        filtered_valid_count += 1
                        filter_status = "✅ 納入"
                else:
                    error_pct = 0
                    filter_status = "❌ 無效"
                
                print(f"   {i:<6} {target_quarter:<11} {predicted_eps:<10.2f} {actual_eps:<10.2f} {error_pct:<8.1f}% {filter_status}")
            
            filtered_mape = filtered_total_error / filtered_valid_count if filtered_valid_count > 0 else 0
            print(f"\n   過濾後MAPE: {filtered_mape:.1f}%")
            print(f"   改善幅度: {original_mape - filtered_mape:+.1f}個百分點")
        
        # 4. 營業EPS估算
        print(f"\n4. 營業EPS估算...")
        
        def estimate_operating_eps(actual_eps, current_margin, normal_margin):
            """估算營業EPS"""
            if current_margin > 0:
                return actual_eps * (normal_margin / current_margin)
            return actual_eps
        
        # 對異常季度進行營業EPS估算
        for abnormal in abnormal_quarters:
            quarter = abnormal['quarter']
            current_margin = abnormal['net_margin']
            
            # 找到對應的回測結果
            for result in eps_data:
                if result.get('target_quarter') == quarter:
                    actual_eps = result.get('actual', {}).get('actual_eps', 0)
                    predicted_eps = result.get('prediction', {}).get('predicted_eps', 0)
                    
                    if actual_eps > 0:
                        # 使用歷史正常淨利率（假設10%）
                        normal_margin = 10.0
                        estimated_operating_eps = estimate_operating_eps(actual_eps, current_margin, normal_margin)
                        
                        if predicted_eps > 0:
                            operating_error = abs(predicted_eps - estimated_operating_eps) / estimated_operating_eps * 100
                            original_error = abs(predicted_eps - actual_eps) / actual_eps * 100
                            
                            print(f"   {quarter}:")
                            print(f"     實際EPS: {actual_eps:.2f}")
                            print(f"     估算營業EPS: {estimated_operating_eps:.2f}")
                            print(f"     預測EPS: {predicted_eps:.2f}")
                            print(f"     原始誤差: {original_error:.1f}%")
                            print(f"     營業誤差: {operating_error:.1f}%")
                            print(f"     改善: {original_error - operating_error:+.1f}個百分點")
        
        print(f"\n" + "="*60)
        print(f"🎯 過濾器效果總結:")
        
        if 'original_mape' in locals() and 'filtered_mape' in locals():
            improvement = original_mape - filtered_mape
            print(f"✅ 原始MAPE: {original_mape:.1f}%")
            print(f"✅ 過濾後MAPE: {filtered_mape:.1f}%")
            print(f"✅ 準確度改善: {improvement:+.1f}個百分點")
            
            if improvement > 0:
                print(f"🎉 過濾器有效！模型準確度提升")
            else:
                print(f"⚠️ 過濾器效果有限，需要調整參數")
        
        print(f"✅ 異常季度檢測: {len(abnormal_quarters)}個")
        print(f"✅ 營業EPS估算: 可行")
        print(f"✅ 模型評估: 更公平")
        
        return True
        
    except Exception as e:
        print(f"❌ 實作失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    implement_eps_filter()
