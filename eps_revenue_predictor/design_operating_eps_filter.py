# -*- coding: utf-8 -*-
"""
設計營業EPS過濾器 - 扣除非營業收益影響
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def design_operating_eps_filter():
    """設計營業EPS過濾器"""
    
    print("🎯 營業EPS過濾器設計")
    print("=" * 60)
    
    try:
        from src.data.database_manager import DatabaseManager
        
        stock_id = "8299"
        db_manager = DatabaseManager()
        
        print(f"📊 分析股票: {stock_id}")
        
        # 1. 分析淨利率異常變化
        print(f"\n1. 淨利率異常檢測...")
        
        ratios_data = db_manager.get_financial_ratios(stock_id)
        
        if not ratios_data.empty:
            print(f"   季度        淨利率    QoQ變化    異常標記")
            print(f"   " + "-"*50)
            
            recent_ratios = ratios_data.tail(8)
            
            for i, (_, row) in enumerate(recent_ratios.iterrows()):
                date = row['date']
                net_margin = row.get('net_margin', 0) or 0
                
                # 轉換為季度
                date_str = str(date)
                year = date_str[:4]
                month = date_str[5:7]
                quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                quarter = quarter_map.get(month, 'Q?')
                quarter_str = f"{year}-{quarter}"
                
                # 計算QoQ變化
                if i > 0:
                    prev_margin = recent_ratios.iloc[i-1].get('net_margin', 0) or 0
                    if prev_margin > 0:
                        qoq_change = net_margin - prev_margin
                        qoq_change_pct = qoq_change / prev_margin * 100
                        
                        # 異常檢測: 淨利率變化超過5個百分點
                        is_abnormal = abs(qoq_change) > 5
                        abnormal_mark = "⚠️ 異常" if is_abnormal else "✅ 正常"
                        
                        print(f"   {quarter_str}      {net_margin:>6.1f}%    {qoq_change:+5.1f}pp   {abnormal_mark}")
                    else:
                        print(f"   {quarter_str}      {net_margin:>6.1f}%    {'N/A':>7}   {'?':>8}")
                else:
                    print(f"   {quarter_str}      {net_margin:>6.1f}%    {'N/A':>7}   {'基準':>8}")
        
        # 2. EPS vs 營收相關性分析
        print(f"\n2. EPS vs 營收相關性分析...")
        
        # 獲取EPS和營收資料
        eps_data = db_manager.get_eps_data(stock_id)
        revenue_data = db_manager.get_monthly_revenue(stock_id)
        
        if not eps_data.empty and not revenue_data.empty:
            print(f"   季度        季營收(億)  EPS     營收/EPS比  異常標記")
            print(f"   " + "-"*60)
            
            recent_eps = eps_data.tail(6)
            
            for _, row in recent_eps.iterrows():
                date = row['date']
                eps = row['eps']
                
                # 轉換為季度
                date_str = str(date)
                year = date_str[:4]
                month = date_str[5:7]
                quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                quarter = quarter_map.get(month, 'Q?')
                quarter_str = f"{year}-{quarter}"
                
                # 計算對應季度營收
                if quarter == 'Q1':
                    months = [f"{year}-01", f"{year}-02", f"{year}-03"]
                elif quarter == 'Q2':
                    months = [f"{year}-04", f"{year}-05", f"{year}-06"]
                elif quarter == 'Q3':
                    months = [f"{year}-07", f"{year}-08", f"{year}-09"]
                else:  # Q4
                    months = [f"{year}-10", f"{year}-11", f"{year}-12"]
                
                quarter_revenue = 0
                for month in months:
                    month_data = revenue_data[revenue_data['date'] == month]
                    if not month_data.empty:
                        quarter_revenue += month_data.iloc[0]['revenue']
                
                quarter_revenue_billion = quarter_revenue / 100 if quarter_revenue > 0 else 0
                
                # 計算營收/EPS比率
                if eps > 0 and quarter_revenue_billion > 0:
                    revenue_eps_ratio = quarter_revenue_billion / eps
                    
                    # 異常檢測: 比率異常偏離
                    # 正常情況下，營收/EPS比率應該相對穩定
                    is_abnormal = revenue_eps_ratio < 5 or revenue_eps_ratio > 50
                    abnormal_mark = "⚠️ 異常" if is_abnormal else "✅ 正常"
                    
                    print(f"   {quarter_str}      {quarter_revenue_billion:>8.1f}   {eps:>6.2f}   {revenue_eps_ratio:>8.1f}   {abnormal_mark}")
                else:
                    print(f"   {quarter_str}      {quarter_revenue_billion:>8.1f}   {eps:>6.2f}   {'N/A':>8}   {'?':>8}")
        
        # 3. 設計過濾規則
        print(f"\n3. 營業EPS過濾規則設計...")
        print(f"   " + "="*50)
        
        print(f"   🔍 異常檢測規則:")
        print(f"   1. 淨利率QoQ變化 > 5個百分點 → 可能有非營業收益")
        print(f"   2. 營收/EPS比率 < 5 或 > 50 → EPS異常")
        print(f"   3. EPS QoQ變化 > 100% 且營收變化 < 20% → 非營業因素")
        
        print(f"\n   💡 過濾策略:")
        print(f"   A. 標記異常季度: 不納入準確度計算")
        print(f"   B. 調整預期EPS: 基於營業利潤估算")
        print(f"   C. 分層評估: 營業EPS vs 總EPS分別評估")
        
        # 4. 實作範例
        print(f"\n4. 8299案例應用...")
        
        # 檢查2024-Q4是否異常
        q4_2024_ratios = ratios_data[ratios_data['date'] == '2024-12-31']
        q3_2024_ratios = ratios_data[ratios_data['date'] == '2024-09-30']
        
        if not q4_2024_ratios.empty and not q3_2024_ratios.empty:
            q4_net_margin = q4_2024_ratios.iloc[0].get('net_margin', 0) or 0
            q3_net_margin = q3_2024_ratios.iloc[0].get('net_margin', 0) or 0
            
            margin_change = q4_net_margin - q3_net_margin
            
            print(f"   2024-Q4 淨利率: {q4_net_margin:.1f}%")
            print(f"   2024-Q3 淨利率: {q3_net_margin:.1f}%")
            print(f"   變化: {margin_change:+.1f}個百分點")
            
            if abs(margin_change) > 5:
                print(f"   ⚠️ 判定: 2024-Q4有異常，可能含非營業收益")
                print(f"   📊 建議: 此季度不納入模型準確度評估")
                
                # 估算營業EPS
                q4_2024_eps = eps_data[eps_data['date'] == '2024-12-31']
                if not q4_2024_eps.empty:
                    actual_eps = q4_2024_eps.iloc[0]['eps']
                    
                    # 假設營業EPS = 實際EPS × (Q3淨利率/Q4淨利率)
                    if q4_net_margin > 0:
                        estimated_operating_eps = actual_eps * (q3_net_margin / q4_net_margin)
                        print(f"   📈 估算營業EPS: {estimated_operating_eps:.2f}")
                        print(f"   📈 我們的預測: 13.05")
                        print(f"   📈 調整後誤差: {abs(estimated_operating_eps - 13.05) / 13.05 * 100:.1f}%")
            else:
                print(f"   ✅ 判定: 2024-Q4正常")
        
        print(f"\n" + "="*60)
        print(f"🎯 結論:")
        print(f"✅ 可以設計過濾器扣除非營業收益影響")
        print(f"✅ 提升模型評估的公平性和準確性")
        print(f"✅ 分離營業預測能力 vs 總體預測能力")
        
        return True
        
    except Exception as e:
        print(f"❌ 設計失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    design_operating_eps_filter()
