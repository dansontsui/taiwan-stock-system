# -*- coding: utf-8 -*-
"""
檢查資料庫中的營收資料
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_revenue_data():
    """檢查營收資料"""
    
    print("🔍 檢查營收資料")
    print("=" * 50)
    
    try:
        # 連接資料庫
        db_path = Path('..') / 'data' / 'taiwan_stock.db'
        conn = sqlite3.connect(db_path)
        
        # 檢查8299的最新營收資料
        print("1. 檢查8299股票的最新營收資料...")
        query = """
        SELECT revenue_year, revenue_month, revenue
        FROM monthly_revenues 
        WHERE stock_id = '8299'
        ORDER BY revenue_year DESC, revenue_month DESC
        LIMIT 15
        """
        
        df = pd.read_sql_query(query, conn, params=[])
        
        if not df.empty:
            print("8299最新15筆營收資料:")
            for _, row in df.iterrows():
                revenue_billion = row['revenue'] / 1e8
                year = int(row['revenue_year'])
                month = int(row['revenue_month'])
                print(f"  {year}-{month:02d}: {revenue_billion:.1f}億")
            
            # 檢查是否有2025年7月資料
            july_2025 = df[(df['revenue_year'] == 2025) & (df['revenue_month'] == 7)]
            if not july_2025.empty:
                revenue_val = july_2025.iloc[0]['revenue'] / 1e8
                print(f"\n✅ 找到2025年7月資料: {revenue_val:.1f}億")
            else:
                print(f"\n❌ 沒有找到2025年7月資料")
            
            # 檢查最新資料日期
            latest = df.iloc[0]
            latest_year = int(latest['revenue_year'])
            latest_month = int(latest['revenue_month'])
            print(f"\n📅 最新資料: {latest_year}-{latest_month:02d}")
            
        else:
            print("❌ 沒有找到8299的營收資料")
        
        # 檢查2385的資料作為對比
        print(f"\n2. 檢查2385股票的最新營收資料...")
        query2 = """
        SELECT revenue_year, revenue_month, revenue
        FROM monthly_revenues 
        WHERE stock_id = '2385'
        ORDER BY revenue_year DESC, revenue_month DESC
        LIMIT 10
        """
        
        df2 = pd.read_sql_query(query2, conn, params=[])
        
        if not df2.empty:
            print("2385最新10筆營收資料:")
            for _, row in df2.iterrows():
                revenue_billion = row['revenue'] / 1e8
                year = int(row['revenue_year'])
                month = int(row['revenue_month'])
                print(f"  {year}-{month:02d}: {revenue_billion:.1f}億")
            
            # 檢查最新資料日期
            latest2 = df2.iloc[0]
            latest_year2 = int(latest2['revenue_year'])
            latest_month2 = int(latest2['revenue_month'])
            print(f"\n📅 2385最新資料: {latest_year2}-{latest_month2:02d}")
        
        conn.close()
        
        # 分析結果
        print(f"\n" + "="*50)
        print(f"🎯 分析結果:")
        
        if not df.empty:
            latest_year = int(df.iloc[0]['revenue_year'])
            latest_month = int(df.iloc[0]['revenue_month'])
            
            if latest_year == 2025 and latest_month >= 7:
                print(f"✅ 8299有2025年7月或更新的資料")
                print(f"   回測顯示2025-07的實際營收是合理的")
            elif latest_year == 2025 and latest_month == 6:
                print(f"⚠️ 8299最新資料只到2025年6月")
                print(f"   回測顯示2025-07的實際營收可能是錯誤的")
                print(f"   應該是2025年6月的資料")
            else:
                print(f"❌ 8299資料不足，無法支援2025年7月回測")
        
        print(f"=" * 50)
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_revenue_data()
