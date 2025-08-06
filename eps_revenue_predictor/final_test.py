#!/usr/bin/env python3
# -*- coding: ascii -*-

import sys
import pandas as pd
from pathlib import Path

# Add project path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Final Test for EPS Revenue Predictor")
print("=" * 50)

# Test 1: Direct database connection
print("\n1. Testing direct database connection...")
try:
    from config.settings import DATABASE_CONFIG
    import sqlite3
    
    conn = sqlite3.connect(str(DATABASE_CONFIG['path']))
    cursor = conn.cursor()
    
    # Test monthly revenue query
    cursor.execute("""
        SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy, revenue_growth_mom
        FROM monthly_revenues
        WHERE stock_id = '2385'
        ORDER BY revenue_year DESC, revenue_month DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} revenue records for 2385")
    
    if results:
        print("Sample data:")
        for row in results[:3]:
            print(f"  {row[0]}-{row[1]:02d}: {row[2]:,} (YoY: {row[3]}%)")
    
    conn.close()
    print("Direct database test: SUCCESS")
    
except Exception as e:
    print(f"Direct database test: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 2: Database manager
print("\n2. Testing database manager...")
try:
    from src.data.database_manager import DatabaseManager
    
    db_manager = DatabaseManager()
    print("DatabaseManager created")
    
    # Test stock existence
    exists = db_manager.check_stock_exists("2385")
    print(f"Stock 2385 exists: {exists}")
    
    if exists:
        # Test revenue data with manual date creation
        query = """
        SELECT revenue_year, revenue_month, revenue, revenue_growth_yoy, revenue_growth_mom
        FROM monthly_revenues
        WHERE stock_id = ?
        ORDER BY revenue_year DESC, revenue_month DESC
        LIMIT ?
        """
        
        with db_manager.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=["2385", 12])
        
        print(f"Retrieved {len(df)} revenue records")
        
        if not df.empty:
            # Manual date creation
            df_date = df[['revenue_year', 'revenue_month']].copy()
            df_date.columns = ['year', 'month']
            df_date['day'] = 1
            df['date'] = pd.to_datetime(df_date)
            
            print("Date creation successful")
            print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    print("Database manager test: SUCCESS")
    
except Exception as e:
    print(f"Database manager test: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 3: Revenue predictor
print("\n3. Testing revenue predictor...")
try:
    from src.predictors.revenue_predictor import RevenuePredictor
    
    predictor = RevenuePredictor()
    print("RevenuePredictor created")
    
    # Simple prediction
    result = predictor.predict_monthly_growth("2385")
    
    if result.get('success', True):
        print("Revenue prediction: SUCCESS")
        print(f"Growth rate: {result.get('growth_rate', 0):.2%}")
        print(f"Confidence: {result.get('confidence', 'Unknown')}")
    else:
        print(f"Revenue prediction: FAILED - {result.get('error', 'Unknown')}")
    
except Exception as e:
    print(f"Revenue predictor test: FAILED - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Final test completed!")
