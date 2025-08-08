# -*- coding: utf-8 -*-
"""
分析8299 EPS異常增長原因
"""

import sys
from pathlib import Path
import pandas as pd

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_8299_eps():
    """分析8299 EPS異常增長原因"""
    
    print("🔍 分析8299 EPS異常增長原因")
    print("=" * 80)
    
    try:
        from src.data.database_manager import DatabaseManager
        
        stock_id = "8299"
        
        print(f"📊 分析股票: {stock_id}")
        
        # 初始化資料庫管理器
        db_manager = DatabaseManager()
        
        # 1. 查看營收資料
        print(f"\n1. 營收資料分析...")
        
        revenue_query = """
        SELECT date, revenue
        FROM revenue_data
        WHERE stock_id = ?
        ORDER BY date DESC
        LIMIT 12
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(revenue_query, (stock_id,))
            revenue_results = cursor.fetchall()
            
            if revenue_results:
                print(f"   最新12個月營收:")
                print(f"   月份        營收(億)    YoY成長率")
                print(f"   " + "-"*40)
                
                revenue_data = []
                for date, revenue in revenue_results:
                    revenue_billion = revenue / 100 if revenue else 0
                    revenue_data.append((date, revenue_billion))
                    
                    # 計算YoY成長率
                    year_month = date
                    prev_year_month = f"{int(year_month[:4])-1}{year_month[4:]}"
                    
                    # 查找去年同期
                    cursor.execute("SELECT revenue FROM revenue_data WHERE stock_id = ? AND date = ?",
                                 (stock_id, prev_year_month))
                    prev_result = cursor.fetchone()
                    
                    if prev_result and prev_result[0]:
                        yoy_growth = (revenue - prev_result[0]) / prev_result[0] * 100
                        print(f"   {year_month}    {revenue_billion:>8.1f}    {yoy_growth:>8.1f}%")
                    else:
                        print(f"   {year_month}    {revenue_billion:>8.1f}    {'N/A':>8}")
                
                # 季度營收分析
                print(f"\n   季度營收分析:")
                print(f"   季度        營收(億)    季度總和")
                print(f"   " + "-"*40)
                
                # 2024 Q4 (10,11,12月)
                q4_2024 = [r for r in revenue_data if r[0].startswith('2024') and r[0][4:] in ['10', '11', '12']]
                q4_2024_total = sum([r[1] for r in q4_2024])
                
                # 2025 Q1 (1,2,3月)
                q1_2025 = [r for r in revenue_data if r[0].startswith('2025') and r[0][4:] in ['01', '02', '03']]
                q1_2025_total = sum([r[1] for r in q1_2025])
                
                print(f"   2024-Q4     {q4_2024_total:>8.1f}    (10+11+12月)")
                for date, rev in sorted(q4_2024):
                    print(f"     {date}      {rev:>6.1f}")
                
                print(f"   2025-Q1     {q1_2025_total:>8.1f}    (1+2+3月)")
                for date, rev in sorted(q1_2025):
                    print(f"     {date}      {rev:>6.1f}")
                
                print(f"   季度營收差異: {q4_2024_total - q1_2025_total:+.1f}億 ({(q4_2024_total/q1_2025_total-1)*100:+.1f}%)")
        
        # 2. 查看EPS資料
        print(f"\n2. EPS資料分析...")
        
        eps_query = """
        SELECT date, value as eps
        FROM financial_statements
        WHERE stock_id = ? AND type = 'EPS'
        ORDER BY date DESC
        LIMIT 8
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(eps_query, (stock_id,))
            eps_results = cursor.fetchall()
            
            if eps_results:
                print(f"   最新8季EPS:")
                print(f"   季度        EPS        YoY成長率")
                print(f"   " + "-"*40)
                
                for date, eps in eps_results:
                    # 轉換日期為季度
                    year = date[:4]
                    month = date[5:7]
                    quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                    quarter = quarter_map.get(month, 'Q?')
                    quarter_str = f"{year}-{quarter}"
                    
                    # 計算YoY成長率
                    prev_year = str(int(year) - 1)
                    prev_date = date.replace(year, prev_year)
                    
                    cursor.execute("SELECT value FROM financial_statements WHERE stock_id = ? AND type = 'EPS' AND date = ?", 
                                 (stock_id, prev_date))
                    prev_result = cursor.fetchone()
                    
                    if prev_result and prev_result[0]:
                        yoy_growth = (eps - prev_result[0]) / abs(prev_result[0]) * 100
                        print(f"   {quarter_str}      {eps:>6.2f}      {yoy_growth:>8.1f}%")
                    else:
                        print(f"   {quarter_str}      {eps:>6.2f}      {'N/A':>8}")
        
        # 3. 查看財務比率資料
        print(f"\n3. 財務比率分析...")
        
        ratios_query = """
        SELECT date, gross_margin, operating_margin, net_margin, roe, roa
        FROM financial_ratios
        WHERE stock_id = ?
        ORDER BY date DESC
        LIMIT 6
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(ratios_query, (stock_id,))
            ratios_results = cursor.fetchall()
            
            if ratios_results:
                print(f"   最新6季財務比率:")
                print(f"   季度        毛利率   營業利益率  淨利率    ROE      ROA")
                print(f"   " + "-"*65)
                
                for date, gross_margin, operating_margin, net_margin, roe, roa in ratios_results:
                    # 轉換日期為季度
                    year = date[:4]
                    month = date[5:7]
                    quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                    quarter = quarter_map.get(month, 'Q?')
                    quarter_str = f"{year}-{quarter}"
                    
                    gross_margin = gross_margin or 0
                    operating_margin = operating_margin or 0
                    net_margin = net_margin or 0
                    roe = roe or 0
                    roa = roa or 0
                    
                    print(f"   {quarter_str}      {gross_margin:>6.1f}%   {operating_margin:>8.1f}%   {net_margin:>6.1f}%   {roe:>6.1f}%   {roa:>6.1f}%")
        
        # 4. 查看完整財務報表資料
        print(f"\n4. 完整財務報表分析...")
        
        financial_query = """
        SELECT date, type, value
        FROM financial_statements
        WHERE stock_id = ? AND date IN ('2024-12-31', '2024-09-30', '2023-12-31', '2025-03-31')
        ORDER BY date DESC, type
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(financial_query, (stock_id,))
            financial_results = cursor.fetchall()
            
            if financial_results:
                print(f"   關鍵財務指標:")
                
                # 組織資料
                financial_data = {}
                for date, type_name, value in financial_results:
                    if date not in financial_data:
                        financial_data[date] = {}
                    financial_data[date][type_name] = value
                
                # 顯示關鍵指標
                key_metrics = ['EPS', 'Revenue', 'Operating_Income', 'Net_Income', 'Total_Assets', 'Total_Equity']
                
                print(f"   指標          2024-Q4    2024-Q3    2023-Q4    2025-Q1")
                print(f"   " + "-"*60)
                
                for metric in key_metrics:
                    values = []
                    for date in ['2024-12-31', '2024-09-30', '2023-12-31', '2025-03-31']:
                        value = financial_data.get(date, {}).get(metric, 0)
                        if metric in ['Revenue', 'Operating_Income', 'Net_Income', 'Total_Assets', 'Total_Equity']:
                            values.append(f"{value/100:.1f}億" if value else "N/A")
                        else:
                            values.append(f"{value:.2f}" if value else "N/A")
                    
                    print(f"   {metric:<12}  {values[0]:>8}   {values[1]:>8}   {values[2]:>8}   {values[3]:>8}")
        
        # 5. 分析結論
        print(f"\n5. 分析結論...")
        print(f"   " + "="*60)
        
        print(f"   🔍 EPS異常增長可能原因:")
        print(f"   1. 季節性因素: Q4通常是電子業旺季")
        print(f"   2. 一次性收益: 可能有資產處分、投資收益等")
        print(f"   3. 成本控制: 營業費用降低或成本結構改善")
        print(f"   4. 匯率影響: 匯兌損益變化")
        print(f"   5. 稅務影響: 稅率變化或稅務優惠")
        print(f"   6. 會計調整: 會計政策變更或一次性調整")
        
        print(f"\n   💡 建議進一步查看:")
        print(f"   - 損益表詳細項目 (營業外收支)")
        print(f"   - 現金流量表")
        print(f"   - 財報附註說明")
        print(f"   - 法說會資料")
        
        print(f"\n" + "="*80)
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_8299_eps()
