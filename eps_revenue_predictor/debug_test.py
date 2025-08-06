#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug test for EPS Revenue Predictor
"""

import sys
from pathlib import Path

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("🔍 Debug Test Starting...")
print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path[:3]}")

try:
    print("\n1. Testing config import...")
    from config.settings import DATABASE_CONFIG, PROJECT_ROOT
    print(f"✅ Config imported successfully")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Database path: {DATABASE_CONFIG['path']}")
    print(f"Database exists: {Path(DATABASE_CONFIG['path']).exists()}")
    
except Exception as e:
    print(f"❌ Config import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Testing database manager import...")
    from src.data.database_manager import DatabaseManager
    print(f"✅ DatabaseManager imported successfully")
    
except Exception as e:
    print(f"❌ DatabaseManager import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing database connection...")
    db_manager = DatabaseManager()
    print(f"✅ DatabaseManager created successfully")
    
    # 測試基本查詢
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Database connected, found tables: {tables}")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n4. Testing stock 2385 existence...")
    exists = db_manager.check_stock_exists("2385")
    print(f"✅ Stock 2385 exists: {exists}")
    
    if exists:
        basic_info = db_manager.get_stock_basic_info("2385")
        print(f"✅ Stock info: {basic_info}")
    
except Exception as e:
    print(f"❌ Stock check failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n5. Testing revenue predictor import...")
    from src.predictors.revenue_predictor import RevenuePredictor
    print(f"✅ RevenuePredictor imported successfully")
    
    predictor = RevenuePredictor(db_manager)
    print(f"✅ RevenuePredictor created successfully")
    
except Exception as e:
    print(f"❌ RevenuePredictor failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 Debug test completed!")
