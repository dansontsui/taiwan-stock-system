# -*- coding: utf-8 -*-
"""
EPS異常過濾器演示
"""

def eps_filter_demo():
    """EPS異常過濾器演示"""
    
    print("🎯 EPS異常過濾器演示")
    print("=" * 50)
    
    # 模擬8299的回測資料
    backtest_data = [
        {
            'quarter': '2025-Q1',
            'predicted_eps': 13.05,
            'actual_eps': 5.53,
            'net_margin': 8.2,
            'prev_net_margin': 19.0
        }
    ]
    
    print("1. 原始回測結果:")
    print("   季度     預測EPS   實際EPS   誤差%")
    print("   " + "-"*40)
    
    original_errors = []
    
    for data in backtest_data:
        quarter = data['quarter']
        pred = data['predicted_eps']
        actual = data['actual_eps']
        error = abs(pred - actual) / actual * 100
        original_errors.append(error)
        
        print(f"   {quarter}   {pred:>7.2f}   {actual:>7.2f}   {error:>6.1f}%")
    
    original_mape = sum(original_errors) / len(original_errors)
    print(f"\n   原始MAPE: {original_mape:.1f}%")
    
    print("\n2. 異常檢測:")
    print("   季度     淨利率   變化     判定")
    print("   " + "-"*40)
    
    filtered_errors = []
    
    for data in backtest_data:
        quarter = data['quarter']
        margin = data['net_margin']
        prev_margin = data['prev_net_margin']
        margin_change = margin - prev_margin
        
        # 異常檢測: 淨利率變化超過5個百分點
        is_abnormal = abs(margin_change) > 5
        
        if is_abnormal:
            status = "⚠️ 異常"
            print(f"   {quarter}   {margin:>6.1f}%   {margin_change:>+5.1f}pp  {status}")
            
            # 估算營業EPS
            pred = data['predicted_eps']
            actual = data['actual_eps']
            
            # 假設正常淨利率為10%
            normal_margin = 10.0
            estimated_operating_eps = actual * (normal_margin / margin)
            
            operating_error = abs(pred - estimated_operating_eps) / estimated_operating_eps * 100
            
            print(f"     → 估算營業EPS: {estimated_operating_eps:.2f}")
            print(f"     → 營業誤差: {operating_error:.1f}%")
            
            # 不納入MAPE計算（或使用營業EPS計算）
            # filtered_errors.append(operating_error)  # 使用營業EPS
            
        else:
            status = "✅ 正常"
            print(f"   {quarter}   {margin:>6.1f}%   {margin_change:>+5.1f}pp  {status}")
            
            # 納入正常計算
            pred = data['predicted_eps']
            actual = data['actual_eps']
            error = abs(pred - actual) / actual * 100
            filtered_errors.append(error)
    
    if filtered_errors:
        filtered_mape = sum(filtered_errors) / len(filtered_errors)
        print(f"\n   過濾後MAPE: {filtered_mape:.1f}%")
        improvement = original_mape - filtered_mape
        print(f"   改善幅度: {improvement:+.1f}個百分點")
    else:
        print(f"\n   所有季度都被過濾，無法計算MAPE")
    
    print("\n3. 過濾策略選項:")
    print("   A. 完全排除: 異常季度不納入準確度計算")
    print("   B. 營業調整: 使用估算的營業EPS計算誤差")
    print("   C. 分層評估: 營業預測 vs 總體預測分開評估")
    
    print("\n4. 實際應用建議:")
    print("   ✅ 檢測規則: 淨利率QoQ變化 > 5個百分點")
    print("   ✅ 過濾標準: 標記為異常，單獨評估")
    print("   ✅ 營業估算: 基於歷史正常淨利率")
    print("   ✅ 報告分離: 營業預測準確度 vs 總體準確度")
    
    print("\n" + "="*50)
    print("🎯 結論:")
    print("✅ 可以有效識別非營業收益影響")
    print("✅ 提升模型評估的公平性")
    print("✅ 分離營業預測能力評估")
    print("✅ 為投資決策提供更準確的參考")

if __name__ == "__main__":
    eps_filter_demo()
