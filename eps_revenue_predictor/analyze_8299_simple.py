# -*- coding: utf-8 -*-
"""
簡化版8299 EPS分析
"""

import sys
from pathlib import Path
import pandas as pd

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_8299_simple():
    """簡化版8299 EPS分析"""
    
    print("🔍 8299 EPS異常增長分析")
    print("=" * 60)
    
    try:
        from src.data.database_manager import DatabaseManager
        
        stock_id = "8299"
        
        print(f"📊 分析股票: {stock_id}")
        
        # 初始化資料庫管理器
        db_manager = DatabaseManager()
        
        # 1. 使用資料庫管理器的方法獲取資料
        print(f"\n1. 營收資料分析...")
        
        # 獲取營收資料
        revenue_data = db_manager.get_monthly_revenue(stock_id)
        
        if not revenue_data.empty:
            print(f"   最新12個月營收:")
            print(f"   月份        營收(億)    YoY成長率")
            print(f"   " + "-"*40)
            
            # 顯示最新12筆
            recent_revenue = revenue_data.tail(12)
            
            for _, row in recent_revenue.iterrows():
                date = row['date']
                revenue = row['revenue']
                revenue_billion = revenue / 100 if revenue else 0
                
                # 計算YoY成長率
                date_str = str(date)
                year_month = date_str.replace('-', '')
                prev_year_month = f"{int(year_month[:4])-1}-{year_month[4:6]}"
                
                prev_revenue = revenue_data[revenue_data['date'] == prev_year_month]
                if not prev_revenue.empty:
                    prev_rev = prev_revenue.iloc[0]['revenue']
                    if prev_rev and prev_rev > 0:
                        yoy_growth = (revenue - prev_rev) / prev_rev * 100
                        print(f"   {date}    {revenue_billion:>8.1f}    {yoy_growth:>8.1f}%")
                    else:
                        print(f"   {date}    {revenue_billion:>8.1f}    {'N/A':>8}")
                else:
                    print(f"   {date}    {revenue_billion:>8.1f}    {'N/A':>8}")
            
            # 季度營收分析
            print(f"\n   季度營收分析:")
            
            # 2024 Q4 vs 2025 Q1
            q4_2024_months = ['2024-10', '2024-11', '2024-12']
            q1_2025_months = ['2025-01', '2025-02', '2025-03']
            
            q4_2024_revenue = revenue_data[revenue_data['date'].isin(q4_2024_months)]['revenue'].sum()
            q1_2025_revenue = revenue_data[revenue_data['date'].isin(q1_2025_months)]['revenue'].sum()
            
            print(f"   2024-Q4 營收: {q4_2024_revenue/100:.1f}億")
            print(f"   2025-Q1 營收: {q1_2025_revenue/100:.1f}億")
            print(f"   季度差異: {(q4_2024_revenue-q1_2025_revenue)/100:+.1f}億 ({(q4_2024_revenue/q1_2025_revenue-1)*100:+.1f}%)")
        
        # 2. EPS資料分析
        print(f"\n2. EPS資料分析...")
        
        eps_data = db_manager.get_eps_data(stock_id)
        
        if not eps_data.empty:
            print(f"   最新8季EPS:")
            print(f"   季度        EPS        QoQ變化    YoY變化")
            print(f"   " + "-"*50)
            
            # 顯示最新8筆
            recent_eps = eps_data.tail(8)
            
            for i, (_, row) in enumerate(recent_eps.iterrows()):
                date = row['date']
                eps = row['eps']
                
                # 轉換日期為季度
                year = date[:4]
                month = date[5:7]
                quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                quarter = quarter_map.get(month, 'Q?')
                quarter_str = f"{year}-{quarter}"
                
                # 計算QoQ變化
                if i > 0:
                    prev_eps = recent_eps.iloc[i-1]['eps']
                    qoq_change = (eps - prev_eps) / abs(prev_eps) * 100 if prev_eps else 0
                    qoq_str = f"{qoq_change:+.1f}%"
                else:
                    qoq_str = "N/A"
                
                # 計算YoY變化
                prev_year = str(int(year) - 1)
                prev_date = date.replace(year, prev_year)
                prev_year_eps = eps_data[eps_data['date'] == prev_date]
                
                if not prev_year_eps.empty:
                    prev_eps_yoy = prev_year_eps.iloc[0]['eps']
                    yoy_change = (eps - prev_eps_yoy) / abs(prev_eps_yoy) * 100 if prev_eps_yoy else 0
                    yoy_str = f"{yoy_change:+.1f}%"
                else:
                    yoy_str = "N/A"
                
                print(f"   {quarter_str}      {eps:>6.2f}      {qoq_str:>8}   {yoy_str:>8}")
        
        # 3. 財務比率分析
        print(f"\n3. 財務比率分析...")
        
        ratios_data = db_manager.get_financial_ratios(stock_id)
        
        if not ratios_data.empty:
            print(f"   最新6季財務比率:")
            print(f"   季度        毛利率   營業利益率  淨利率    ROE      ROA")
            print(f"   " + "-"*65)
            
            # 顯示最新6筆
            recent_ratios = ratios_data.tail(6)
            
            for _, row in recent_ratios.iterrows():
                date = row['date']
                
                # 轉換日期為季度
                year = date[:4]
                month = date[5:7]
                quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                quarter = quarter_map.get(month, 'Q?')
                quarter_str = f"{year}-{quarter}"
                
                gross_margin = row.get('gross_margin', 0) or 0
                operating_margin = row.get('operating_margin', 0) or 0
                net_margin = row.get('net_margin', 0) or 0
                roe = row.get('roe', 0) or 0
                roa = row.get('roa', 0) or 0
                
                print(f"   {quarter_str}      {gross_margin:>6.1f}%   {operating_margin:>8.1f}%   {net_margin:>6.1f}%   {roe:>6.1f}%   {roa:>6.1f}%")
        
        # 4. 關鍵發現
        print(f"\n4. 關鍵發現...")
        print(f"   " + "="*50)
        
        # 檢查2024-Q4的特殊情況
        q4_2024_eps = eps_data[eps_data['date'] == '2024-12-31']
        q3_2024_eps = eps_data[eps_data['date'] == '2024-09-30']
        q4_2023_eps = eps_data[eps_data['date'] == '2023-12-31']
        
        if not q4_2024_eps.empty and not q3_2024_eps.empty and not q4_2023_eps.empty:
            eps_2024_q4 = q4_2024_eps.iloc[0]['eps']
            eps_2024_q3 = q3_2024_eps.iloc[0]['eps']
            eps_2023_q4 = q4_2023_eps.iloc[0]['eps']
            
            qoq_growth = (eps_2024_q4 - eps_2024_q3) / abs(eps_2024_q3) * 100
            yoy_growth = (eps_2024_q4 - eps_2023_q4) / abs(eps_2023_q4) * 100
            
            print(f"   🔍 2024-Q4 EPS分析:")
            print(f"     2024-Q4 EPS: {eps_2024_q4:.2f}")
            print(f"     2024-Q3 EPS: {eps_2024_q3:.2f}")
            print(f"     2023-Q4 EPS: {eps_2023_q4:.2f}")
            print(f"     QoQ成長: {qoq_growth:+.1f}%")
            print(f"     YoY成長: {yoy_growth:+.1f}%")
            
            print(f"\n   💡 可能原因:")
            if qoq_growth > 100:
                print(f"     - QoQ成長{qoq_growth:.1f}%異常高，可能有一次性收益")
            if yoy_growth > 50:
                print(f"     - YoY成長{yoy_growth:.1f}%顯著，可能有結構性改善")
            
            # 檢查營收vs EPS的關係
            if q4_2024_revenue and q1_2025_revenue:
                revenue_change = (q4_2024_revenue - q1_2025_revenue) / q1_2025_revenue * 100
                print(f"     - 營收季度變化: {revenue_change:+.1f}%")
                print(f"     - EPS季度變化: {qoq_growth:+.1f}%")
                
                if abs(qoq_growth) > abs(revenue_change) * 2:
                    print(f"     - ⚠️ EPS變化幅度遠超營收變化，可能有非營業因素")
        
        print(f"\n   🎯 建議查看:")
        print(f"     - 2024-Q4財報的營業外收支明細")
        print(f"     - 是否有資產處分收益")
        print(f"     - 匯兌損益變化")
        print(f"     - 投資收益或一次性項目")
        print(f"     - 稅務影響")
        
        print(f"\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_8299_simple()
