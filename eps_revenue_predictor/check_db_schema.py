#!/usr/bin/env python3
# -*- coding: ascii -*-

import sqlite3
from pathlib import Path

# Database path
db_path = Path(__file__).parent.parent / "data" / "taiwan_stock.db"

print("Checking database schema...")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check monthly_revenues table schema
    cursor.execute("PRAGMA table_info(monthly_revenues)")
    columns = cursor.fetchall()
    
    print("monthly_revenues table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check sample data
    cursor.execute("SELECT * FROM monthly_revenues WHERE stock_id = '2385' LIMIT 3")
    sample_data = cursor.fetchall()
    
    print("\nSample data:")
    for row in sample_data:
        print(f"  {row}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
