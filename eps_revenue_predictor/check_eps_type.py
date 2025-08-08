# -*- coding: utf-8 -*-
"""
檢查EPS類型資料
"""

import sqlite3
from pathlib import Path

print("🔍 檢查EPS類型資料")

try:
    db_path = Path('..') / 'data' / 'taiwan_stock.db'
    conn = sqlite3.connect(db_path)
    
    print("=== 檢查EPS類型資料 ===")
    cursor = conn.cursor()
    
    # 檢查EPS類型的資料
    cursor.execute("""
    SELECT date, value, origin_name, eps, revenue, net_income
    FROM financial_statements 
    WHERE stock_id = '2385' AND type = 'EPS'
    ORDER BY date DESC
    LIMIT 10
    """)
    
    eps_data = cursor.fetchall()
    print("EPS類型資料:")
    for row in eps_data:
        date, value, origin_name, eps, revenue, net_income = row
        print(f"  {date}: value={value}, origin_name={origin_name}, eps={eps}")
    
    # 如果EPS類型有value，我們可以用它來修復eps欄位
    if eps_data and eps_data[0][1] is not None:
        print("\n✅ 找到EPS類型資料，開始修復...")
        
        # 更新eps欄位
        update_count = 0
        for row in eps_data:
            date, value, origin_name, eps, revenue, net_income = row
            if value is not None and value != 0:
                # 更新對應日期的Revenue類型記錄的eps欄位
                cursor.execute("""
                UPDATE financial_statements 
                SET eps = ?
                WHERE stock_id = '2385' AND date = ? AND type = 'Revenue'
                """, (value, date))
                update_count += 1
                print(f"    更新 {date}: EPS = {value}")
        
        if update_count > 0:
            conn.commit()
            print(f"\n✅ 成功更新 {update_count} 筆EPS資料")
            
            # 驗證更新結果
            cursor.execute("""
            SELECT date, eps, revenue, net_income
            FROM financial_statements 
            WHERE stock_id = '2385' AND type = 'Revenue' AND eps IS NOT NULL
            ORDER BY date DESC
            LIMIT 5
            """)
            
            updated_data = cursor.fetchall()
            print("\n驗證更新結果:")
            for row in updated_data:
                print(f"  {row[0]}: EPS={row[1]}, 營收={row[2]}, 淨利={row[3]}")
        
    else:
        print("❌ EPS類型資料的value欄位也是空的")
    
    conn.close()
    
except Exception as e:
    print(f"❌ 檢查失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 檢查完成")
