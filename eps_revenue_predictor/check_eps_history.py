# -*- coding: utf-8 -*-
"""
檢查2385 EPS歷史資料
"""

import sqlite3
import pandas as pd
from pathlib import Path

def check_eps_history():
    """檢查2385的完整EPS歷史資料"""
    
    print("🔍 檢查2385 EPS歷史資料")
    print("=" * 60)
    
    try:
        # 連接資料庫
        db_path = Path('..') / 'data' / 'taiwan_stock.db'
        conn = sqlite3.connect(db_path)
        
        # 1. 檢查EPS類型的完整歷史資料
        print("1. EPS類型資料 (完整歷史):")
        eps_query = """
        SELECT date, value, origin_name
        FROM financial_statements 
        WHERE stock_id = '2385' AND type = 'EPS'
        ORDER BY date
        """
        eps_df = pd.read_sql_query(eps_query, conn)
        
        print(f"   EPS類型資料總數: {len(eps_df)}")
        if len(eps_df) > 0:
            print(f"   最早資料: {eps_df.iloc[0]['date']} (EPS: {eps_df.iloc[0]['value']})")
            print(f"   最新資料: {eps_df.iloc[-1]['date']} (EPS: {eps_df.iloc[-1]['value']})")
            
            print("\n   前5筆資料:")
            for _, row in eps_df.head(5).iterrows():
                print(f"     {row['date']}: {row['value']} ({row['origin_name']})")
            
            print("\n   後5筆資料:")
            for _, row in eps_df.tail(5).iterrows():
                print(f"     {row['date']}: {row['value']} ({row['origin_name']})")
        
        # 2. 檢查2015年的EPS資料
        print(f"\n2. 檢查2015年的EPS資料:")
        eps_2015 = eps_df[eps_df['date'].str.startswith('2015')]
        print(f"   2015年EPS資料: {len(eps_2015)}筆")
        if len(eps_2015) > 0:
            for _, row in eps_2015.iterrows():
                print(f"     {row['date']}: {row['value']}")
        
        # 3. 檢查各年度的EPS資料分佈
        print(f"\n3. 各年度EPS資料分佈:")
        if len(eps_df) > 0:
            eps_df['year'] = eps_df['date'].str[:4]
            year_counts = eps_df['year'].value_counts().sort_index()
            for year, count in year_counts.items():
                print(f"   {year}年: {count}筆")
        
        # 4. 檢查資料庫中的所有表
        print(f"\n4. 檢查資料庫中的所有表:")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"   總共{len(table_names)}個表:")
        for table in table_names:
            print(f"     - {table}")
        
        # 5. 檢查是否有dividend相關的表
        print(f"\n5. 檢查除權息相關表:")
        dividend_tables = [table for table in table_names if 'dividend' in table.lower() or 'ex' in table.lower()]
        if dividend_tables:
            print(f"   找到除權息相關表: {dividend_tables}")
            
            for table in dividend_tables[:2]:  # 只檢查前2個表
                print(f"\n   檢查表 {table} 的2385資料:")
                try:
                    sample_query = f"SELECT * FROM {table} WHERE stock_id = '2385' ORDER BY date LIMIT 5"
                    sample_data = pd.read_sql_query(sample_query, conn)
                    if len(sample_data) > 0:
                        print(f"     找到{len(sample_data)}筆資料:")
                        print(sample_data)
                    else:
                        print("     沒有找到2385的資料")
                except Exception as e:
                    print(f"     無法查詢表 {table}: {e}")
        else:
            print("   沒有找到除權息相關表")
        
        # 6. 檢查financial_statements表中2385的完整時間範圍
        print(f"\n6. 檢查2385在financial_statements表的完整時間範圍:")
        range_query = """
        SELECT 
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(DISTINCT date) as unique_dates,
            COUNT(*) as total_records
        FROM financial_statements 
        WHERE stock_id = '2385'
        """
        range_data = pd.read_sql_query(range_query, conn)
        print(f"   最早日期: {range_data['earliest_date'].iloc[0]}")
        print(f"   最新日期: {range_data['latest_date'].iloc[0]}")
        print(f"   不重複日期數: {range_data['unique_dates'].iloc[0]}")
        print(f"   總記錄數: {range_data['total_records'].iloc[0]}")
        
        # 7. 檢查我們修復後的Revenue類型EPS資料
        print(f"\n7. 檢查修復後的Revenue類型EPS資料:")
        revenue_eps_query = """
        SELECT date, eps, revenue, net_income
        FROM financial_statements 
        WHERE stock_id = '2385' AND type = 'Revenue' AND eps IS NOT NULL
        ORDER BY date
        """
        revenue_eps = pd.read_sql_query(revenue_eps_query, conn)
        print(f"   Revenue類型中有EPS的記錄: {len(revenue_eps)}筆")
        if len(revenue_eps) > 0:
            for _, row in revenue_eps.iterrows():
                print(f"     {row['date']}: EPS={row['eps']}, 營收={row['revenue']}")
        
        conn.close()
        
        # 8. 總結分析
        print(f"\n" + "="*60)
        print("📊 分析總結:")
        
        if len(eps_df) > 0:
            earliest_year = eps_df['date'].min()[:4]
            latest_year = eps_df['date'].max()[:4]
            print(f"✅ EPS資料存在: {earliest_year}年 ~ {latest_year}年")
            print(f"✅ 總共{len(eps_df)}筆EPS資料")
            
            if earliest_year <= '2015':
                print(f"✅ 確實有2015年以前的EPS資料")
            else:
                print(f"⚠️  最早EPS資料從{earliest_year}年開始")
        else:
            print("❌ 沒有找到任何EPS資料")
        
        if len(revenue_eps) > 0:
            print(f"✅ 修復成功: {len(revenue_eps)}筆EPS資料已整合到Revenue類型")
        else:
            print("❌ 修復失敗: Revenue類型中沒有EPS資料")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_eps_history()
