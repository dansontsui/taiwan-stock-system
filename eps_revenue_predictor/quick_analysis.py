# -*- coding: utf-8 -*-
"""
快速分析8299 EPS問題
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def quick_analysis():
    """快速分析8299 EPS問題"""
    
    print("🔍 8299 EPS快速分析")
    print("=" * 50)
    
    try:
        from src.data.database_manager import DatabaseManager
        
        stock_id = "8299"
        db_manager = DatabaseManager()
        
        # 1. 直接查詢EPS資料
        print(f"1. EPS資料:")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, value as eps
                FROM financial_statements
                WHERE stock_id = ? AND type = 'EPS'
                ORDER BY date DESC
                LIMIT 8
            """, (stock_id,))
            
            eps_results = cursor.fetchall()
            
            print(f"   季度        EPS")
            print(f"   " + "-"*20)
            
            for date, eps in eps_results:
                year = date[:4]
                month = date[5:7]
                quarter_map = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}
                quarter = quarter_map.get(month, 'Q?')
                quarter_str = f"{year}-{quarter}"
                
                print(f"   {quarter_str}      {eps:>6.2f}")
        
        # 2. 查詢營收資料
        print(f"\n2. 營收資料:")
        
        revenue_data = db_manager.get_monthly_revenue(stock_id)
        
        if not revenue_data.empty:
            print(f"   月份        營收(億)")
            print(f"   " + "-"*20)
            
            # 顯示最新12筆
            recent_revenue = revenue_data.tail(12)
            
            for _, row in recent_revenue.iterrows():
                date = row['date']
                revenue = row['revenue']
                revenue_billion = revenue / 100 if revenue else 0
                
                print(f"   {date}    {revenue_billion:>8.1f}")
        
        # 3. 季度對比
        print(f"\n3. 季度對比:")
        
        # 計算季度營收
        if not revenue_data.empty:
            q4_2024_months = ['2024-10', '2024-11', '2024-12']
            q1_2025_months = ['2025-01', '2025-02', '2025-03']
            
            q4_2024_data = revenue_data[revenue_data['date'].isin(q4_2024_months)]
            q1_2025_data = revenue_data[revenue_data['date'].isin(q1_2025_months)]
            
            q4_2024_revenue = q4_2024_data['revenue'].sum() / 100 if not q4_2024_data.empty else 0
            q1_2025_revenue = q1_2025_data['revenue'].sum() / 100 if not q1_2025_data.empty else 0
            
            print(f"   2024-Q4 營收: {q4_2024_revenue:.1f}億")
            print(f"   2025-Q1 營收: {q1_2025_revenue:.1f}億")
            print(f"   營收差異: {q4_2024_revenue - q1_2025_revenue:+.1f}億")
        
        # 4. EPS對比
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 2024-Q4 EPS
            cursor.execute("""
                SELECT value FROM financial_statements
                WHERE stock_id = ? AND type = 'EPS' AND date = '2024-12-31'
            """, (stock_id,))
            eps_2024_q4_result = cursor.fetchone()
            eps_2024_q4 = eps_2024_q4_result[0] if eps_2024_q4_result else 0
            
            # 2024-Q3 EPS
            cursor.execute("""
                SELECT value FROM financial_statements
                WHERE stock_id = ? AND type = 'EPS' AND date = '2024-09-30'
            """, (stock_id,))
            eps_2024_q3_result = cursor.fetchone()
            eps_2024_q3 = eps_2024_q3_result[0] if eps_2024_q3_result else 0
            
            # 2023-Q4 EPS
            cursor.execute("""
                SELECT value FROM financial_statements
                WHERE stock_id = ? AND type = 'EPS' AND date = '2023-12-31'
            """, (stock_id,))
            eps_2023_q4_result = cursor.fetchone()
            eps_2023_q4 = eps_2023_q4_result[0] if eps_2023_q4_result else 0
            
            print(f"   2024-Q4 EPS: {eps_2024_q4:.2f}")
            print(f"   2024-Q3 EPS: {eps_2024_q3:.2f}")
            print(f"   2023-Q4 EPS: {eps_2023_q4:.2f}")
            
            if eps_2024_q3 > 0:
                qoq_growth = (eps_2024_q4 - eps_2024_q3) / abs(eps_2024_q3) * 100
                print(f"   QoQ成長: {qoq_growth:+.1f}%")
            
            if eps_2023_q4 > 0:
                yoy_growth = (eps_2024_q4 - eps_2023_q4) / abs(eps_2023_q4) * 100
                print(f"   YoY成長: {yoy_growth:+.1f}%")
        
        # 5. 分析結論
        print(f"\n4. 分析結論:")
        print(f"   " + "="*30)
        
        if q4_2024_revenue and q1_2025_revenue and abs(q4_2024_revenue - q1_2025_revenue) < 5:
            print(f"   ✅ 營收確實相近: Q4={q4_2024_revenue:.1f}億 vs Q1={q1_2025_revenue:.1f}億")
        
        if eps_2024_q4 and eps_2024_q3 and eps_2024_q4 > eps_2024_q3 * 2:
            print(f"   ⚠️ EPS異常增長: Q4={eps_2024_q4:.2f} vs Q3={eps_2024_q3:.2f}")
            print(f"   💡 可能原因:")
            print(f"     - 一次性收益 (資產處分、投資收益)")
            print(f"     - 成本結構改善")
            print(f"     - 匯兌收益")
            print(f"     - 稅務影響")
            print(f"     - 會計調整")
        
        # 6. 查看財務比率變化
        print(f"\n5. 財務比率變化:")
        
        ratios_data = db_manager.get_financial_ratios(stock_id)
        
        if not ratios_data.empty:
            # 找2024-Q4和2024-Q3的資料
            q4_2024_ratios = ratios_data[ratios_data['date'] == '2024-12-31']
            q3_2024_ratios = ratios_data[ratios_data['date'] == '2024-09-30']
            
            if not q4_2024_ratios.empty and not q3_2024_ratios.empty:
                q4_net_margin = q4_2024_ratios.iloc[0].get('net_margin', 0) or 0
                q3_net_margin = q3_2024_ratios.iloc[0].get('net_margin', 0) or 0
                
                print(f"   2024-Q4 淨利率: {q4_net_margin:.1f}%")
                print(f"   2024-Q3 淨利率: {q3_net_margin:.1f}%")
                
                if q4_net_margin > q3_net_margin * 1.5:
                    print(f"   ⚠️ 淨利率大幅提升，可能有非營業收益")
        
        print(f"\n" + "="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    quick_analysis()
