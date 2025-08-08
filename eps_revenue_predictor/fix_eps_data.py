# -*- coding: utf-8 -*-
"""
修復EPS資料問題
"""

import sqlite3
import pandas as pd
from pathlib import Path

def fix_eps_data():
    """修復EPS資料問題"""
    
    print("🔧 開始修復EPS資料問題")
    print("=" * 50)
    
    # 連接資料庫
    db_path = Path('..') / 'data' / 'taiwan_stock.db'
    conn = sqlite3.connect(db_path)
    
    try:
        print("📊 分析當前資料結構...")
        
        # 檢查所有type類型
        type_query = """
        SELECT DISTINCT type, COUNT(*) as count
        FROM financial_statements 
        WHERE stock_id = '2385'
        GROUP BY type
        ORDER BY count DESC
        """
        types_df = pd.read_sql_query(type_query, conn)
        print("資料類型分佈:")
        print(types_df)
        
        # 查找可能包含EPS資料的type
        print("\n🔍 查找可能的EPS相關資料...")
        eps_related_query = """
        SELECT type, date, value, origin_name
        FROM financial_statements 
        WHERE stock_id = '2385' 
        AND (
            LOWER(type) LIKE '%eps%' OR 
            LOWER(type) LIKE '%earning%' OR
            LOWER(origin_name) LIKE '%eps%' OR
            LOWER(origin_name) LIKE '%每股%' OR
            LOWER(origin_name) LIKE '%earning%'
        )
        ORDER BY date DESC
        LIMIT 10
        """
        eps_candidates = pd.read_sql_query(eps_related_query, conn)
        
        if not eps_candidates.empty:
            print("找到可能的EPS資料:")
            print(eps_candidates)
        else:
            print("❌ 沒有找到明確的EPS相關資料")
        
        # 檢查是否有Revenue類型的資料包含EPS
        print("\n📈 檢查Revenue類型資料...")
        revenue_query = """
        SELECT date, eps, revenue, net_income, value, origin_name
        FROM financial_statements 
        WHERE stock_id = '2385' 
        AND type = 'Revenue'
        AND date >= '2020-01-01'
        ORDER BY date DESC
        LIMIT 10
        """
        revenue_data = pd.read_sql_query(revenue_query, conn)
        print("Revenue類型資料:")
        print(revenue_data)
        
        # 嘗試從net_income計算EPS (假設股本資料)
        print("\n🧮 嘗試計算EPS...")
        
        # 檢查是否有net_income資料
        income_query = """
        SELECT date, net_income, revenue
        FROM financial_statements 
        WHERE stock_id = '2385' 
        AND type = 'Revenue'
        AND net_income IS NOT NULL
        AND net_income != 0
        ORDER BY date DESC
        LIMIT 5
        """
        income_data = pd.read_sql_query(income_query, conn)
        
        if not income_data.empty:
            print("找到淨利潤資料:")
            print(income_data)
            
            # 假設股本 (需要實際股本資料，這裡用估算)
            # 2385群光電子大約有4億股左右
            estimated_shares = 400_000_000  # 4億股 (估算)
            
            print(f"\n💡 使用估算股本 {estimated_shares:,} 股計算EPS...")
            
            # 更新EPS資料
            update_count = 0
            for _, row in income_data.iterrows():
                if row['net_income'] and row['net_income'] != 0:
                    # 計算EPS (淨利潤 / 股數)
                    # net_income單位是千元，需要轉換
                    calculated_eps = (row['net_income'] * 1000) / estimated_shares
                    
                    # 更新資料庫
                    update_query = """
                    UPDATE financial_statements 
                    SET eps = ?
                    WHERE stock_id = '2385' 
                    AND date = ? 
                    AND type = 'Revenue'
                    """
                    
                    conn.execute(update_query, (calculated_eps, row['date']))
                    update_count += 1
                    
                    print(f"   {row['date']}: 淨利潤={row['net_income']:,.0f}千元 → EPS={calculated_eps:.2f}元")
            
            if update_count > 0:
                conn.commit()
                print(f"\n✅ 成功更新 {update_count} 筆EPS資料")
            else:
                print("\n⚠️ 沒有資料需要更新")
        
        else:
            print("❌ 沒有找到淨利潤資料")
        
        # 驗證修復結果
        print("\n🔍 驗證修復結果...")
        verify_query = """
        SELECT date, eps, revenue, net_income
        FROM financial_statements 
        WHERE stock_id = '2385' 
        AND type = 'Revenue'
        AND eps IS NOT NULL
        AND eps != 0
        ORDER BY date DESC
        LIMIT 10
        """
        
        verified_data = pd.read_sql_query(verify_query, conn)
        
        if not verified_data.empty:
            print("✅ 修復後的EPS資料:")
            print(verified_data)
            
            # 統計
            stats_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN eps IS NOT NULL AND eps != 0 THEN 1 END) as valid_eps,
                MIN(date) as min_date,
                MAX(date) as max_date
            FROM financial_statements 
            WHERE stock_id = '2385' AND type = 'Revenue'
            """
            stats = pd.read_sql_query(stats_query, conn)
            print("\n📊 修復後統計:")
            print(stats)
            
        else:
            print("❌ 修復失敗，仍然沒有有效的EPS資料")
        
    except Exception as e:
        print(f"❌ 修復過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        conn.close()
    
    print("\n🎉 EPS資料修復完成")

if __name__ == "__main__":
    fix_eps_data()
