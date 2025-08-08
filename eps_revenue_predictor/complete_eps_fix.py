# -*- coding: utf-8 -*-
"""
完整修復EPS資料 - 將所有61筆EPS資料整合到Revenue類型
"""

import sqlite3
import pandas as pd
from pathlib import Path

def complete_eps_fix():
    """完整修復EPS資料"""
    
    print("🔧 開始完整修復EPS資料")
    print("=" * 60)
    
    try:
        # 連接資料庫
        db_path = Path('..') / 'data' / 'taiwan_stock.db'
        conn = sqlite3.connect(db_path)
        
        # 1. 獲取所有EPS資料
        print("1. 獲取所有EPS資料...")
        eps_query = """
        SELECT date, value, origin_name
        FROM financial_statements 
        WHERE stock_id = '2385' AND type = 'EPS'
        ORDER BY date
        """
        eps_df = pd.read_sql_query(eps_query, conn)
        print(f"   找到 {len(eps_df)} 筆EPS資料")
        
        # 2. 檢查Revenue類型資料
        print("\n2. 檢查Revenue類型資料...")
        revenue_query = """
        SELECT date, eps, revenue, net_income
        FROM financial_statements 
        WHERE stock_id = '2385' AND type = 'Revenue'
        ORDER BY date
        """
        revenue_df = pd.read_sql_query(revenue_query, conn)
        print(f"   找到 {len(revenue_df)} 筆Revenue資料")
        
        # 3. 執行完整修復
        print("\n3. 執行完整EPS資料修復...")
        update_count = 0
        cursor = conn.cursor()
        
        for _, eps_row in eps_df.iterrows():
            date = eps_row['date']
            eps_value = eps_row['value']
            
            if eps_value is not None and eps_value != 0:
                # 檢查是否已經有對應的Revenue記錄
                check_query = """
                SELECT COUNT(*) FROM financial_statements 
                WHERE stock_id = '2385' AND date = ? AND type = 'Revenue'
                """
                cursor.execute(check_query, (date,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # 更新現有的Revenue記錄
                    update_query = """
                    UPDATE financial_statements 
                    SET eps = ?
                    WHERE stock_id = '2385' AND date = ? AND type = 'Revenue'
                    """
                    cursor.execute(update_query, (eps_value, date))
                    update_count += 1
                    print(f"   更新 {date}: EPS = {eps_value}")
                else:
                    # 創建新的Revenue記錄 (如果不存在)
                    insert_query = """
                    INSERT INTO financial_statements 
                    (stock_id, date, type, eps, origin_name, created_at)
                    VALUES ('2385', ?, 'Revenue', ?, ?, datetime('now'))
                    """
                    cursor.execute(insert_query, (date, eps_value, f"EPS修復: {eps_row['origin_name']}"))
                    update_count += 1
                    print(f"   創建 {date}: EPS = {eps_value}")
        
        # 提交更改
        conn.commit()
        print(f"\n✅ 成功處理 {update_count} 筆EPS資料")
        
        # 4. 驗證修復結果
        print("\n4. 驗證修復結果...")
        verify_query = """
        SELECT date, eps, revenue, net_income
        FROM financial_statements 
        WHERE stock_id = '2385' AND type = 'Revenue' AND eps IS NOT NULL
        ORDER BY date
        """
        verified_df = pd.read_sql_query(verify_query, conn)
        print(f"   修復後Revenue類型中有EPS的記錄: {len(verified_df)} 筆")
        
        # 顯示各年度分佈
        if len(verified_df) > 0:
            verified_df['year'] = verified_df['date'].str[:4]
            year_counts = verified_df['year'].value_counts().sort_index()
            print("\n   各年度EPS資料分佈:")
            for year, count in year_counts.items():
                print(f"     {year}年: {count}筆")
            
            # 顯示2015年的資料
            eps_2015 = verified_df[verified_df['date'].str.startswith('2015')]
            if len(eps_2015) > 0:
                print(f"\n   2015年EPS資料驗證:")
                for _, row in eps_2015.iterrows():
                    print(f"     {row['date']}: EPS = {row['eps']}")
        
        conn.close()
        
        print(f"\n🎉 完整EPS修復完成！")
        print(f"📊 總結:")
        print(f"   原始EPS資料: {len(eps_df)} 筆 (2010-2025)")
        print(f"   修復後可用: {len(verified_df)} 筆")
        print(f"   涵蓋年份: 2010-2025年")
        
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = complete_eps_fix()
    if success:
        print("\n✅ 完整EPS修復成功！現在可以進行完整的歷史回測了！")
    else:
        print("\n❌ 完整EPS修復失敗")
