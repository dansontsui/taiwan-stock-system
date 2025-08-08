# -*- coding: utf-8 -*-
"""
診斷EPS資料問題
"""

print("🔍 診斷EPS資料問題")

try:
    import sqlite3
    import pandas as pd
    from pathlib import Path
    
    # 連接資料庫
    db_path = Path('..') / 'data' / 'taiwan_stock.db'
    print(f"資料庫路徑: {db_path}")
    print(f"資料庫存在: {db_path.exists()}")
    
    if not db_path.exists():
        print("❌ 資料庫文件不存在")
        exit(1)
    
    conn = sqlite3.connect(db_path)
    
    # 1. 檢查表結構
    print("\n=== 1. 檢查表結構 ===")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(financial_statements)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 2. 檢查2385的資料總數
    print("\n=== 2. 檢查2385資料總數 ===")
    count_query = "SELECT COUNT(*) FROM financial_statements WHERE stock_id = '2385'"
    total_count = conn.execute(count_query).fetchone()[0]
    print(f"  總記錄數: {total_count}")
    
    # 3. 檢查type分佈
    print("\n=== 3. 檢查type分佈 ===")
    type_query = """
    SELECT type, COUNT(*) as count
    FROM financial_statements 
    WHERE stock_id = '2385'
    GROUP BY type
    ORDER BY count DESC
    LIMIT 10
    """
    cursor.execute(type_query)
    types = cursor.fetchall()
    for type_name, count in types:
        print(f"  {type_name}: {count}")
    
    # 4. 檢查Revenue類型的資料
    print("\n=== 4. 檢查Revenue類型資料 ===")
    revenue_query = """
    SELECT date, eps, revenue, net_income
    FROM financial_statements 
    WHERE stock_id = '2385' AND type = 'Revenue'
    ORDER BY date DESC
    LIMIT 5
    """
    cursor.execute(revenue_query)
    revenue_data = cursor.fetchall()
    print("  最新5筆Revenue資料:")
    for row in revenue_data:
        print(f"    {row[0]}: EPS={row[1]}, 營收={row[2]}, 淨利={row[3]}")
    
    # 5. 檢查是否有任何非空的EPS
    print("\n=== 5. 檢查非空EPS ===")
    eps_query = """
    SELECT COUNT(*) 
    FROM financial_statements 
    WHERE stock_id = '2385' AND eps IS NOT NULL AND eps != 0
    """
    eps_count = conn.execute(eps_query).fetchone()[0]
    print(f"  非空EPS記錄數: {eps_count}")
    
    if eps_count > 0:
        eps_sample_query = """
        SELECT date, type, eps, revenue, net_income
        FROM financial_statements 
        WHERE stock_id = '2385' AND eps IS NOT NULL AND eps != 0
        ORDER BY date DESC
        LIMIT 5
        """
        cursor.execute(eps_sample_query)
        eps_samples = cursor.fetchall()
        print("  EPS樣本:")
        for row in eps_samples:
            print(f"    {row[0]} ({row[1]}): EPS={row[2]}")
    
    conn.close()
    
    print("\n✅ 診斷完成")
    
    # 總結問題
    print("\n=== 問題總結 ===")
    if eps_count == 0:
        print("❌ 主要問題: 資料庫中沒有任何有效的EPS資料")
        print("💡 可能原因:")
        print("   1. EPS資料沒有正確導入")
        print("   2. EPS資料存儲在其他欄位或表中")
        print("   3. 需要從淨利潤和股本計算EPS")
    else:
        print("✅ 找到EPS資料，可能是查詢邏輯問題")

except Exception as e:
    print(f"❌ 診斷失敗: {e}")
    import traceback
    traceback.print_exc()
