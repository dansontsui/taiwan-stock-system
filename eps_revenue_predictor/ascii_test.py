#!/usr/bin/env python3
# -*- coding: ascii -*-

import sys
from pathlib import Path

# Add project path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_database():
    print("Testing database connection...")
    
    try:
        from src.data.database_manager import DatabaseManager
        print("DatabaseManager imported")
        
        db_manager = DatabaseManager()
        print("DatabaseManager created")
        
        # Test stock 2385
        exists = db_manager.check_stock_exists("2385")
        print(f"Stock 2385 exists: {exists}")
        
        if exists:
            revenue_data = db_manager.get_monthly_revenue("2385", 12)
            print(f"Revenue records: {len(revenue_data)}")
            
            ratio_data = db_manager.get_financial_ratios("2385", 8)
            print(f"Ratio records: {len(ratio_data)}")
        
        return True
    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_revenue_predictor():
    print("\nTesting revenue predictor...")
    
    try:
        from src.data.database_manager import DatabaseManager
        from src.predictors.revenue_predictor import RevenuePredictor
        
        print("RevenuePredictor imported")
        
        db_manager = DatabaseManager()
        predictor = RevenuePredictor(db_manager)
        print("RevenuePredictor created")
        
        # Simple prediction test
        result = predictor.predict_monthly_growth("2385")
        print(f"Prediction completed: success={result.get('success', True)}")
        
        if result.get('success', True):
            growth = result.get('growth_rate', 0)
            confidence = result.get('confidence', 'Unknown')
            print(f"Growth rate: {growth:.2%}")
            print(f"Confidence: {confidence}")
        else:
            print(f"Error: {result.get('error', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"Revenue predictor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("ASCII Test for EPS Revenue Predictor")
    print("=" * 50)
    
    # Test database
    db_success = test_database()
    
    if db_success:
        # Test revenue predictor
        predictor_success = test_revenue_predictor()
        
        if predictor_success:
            print("\nAll tests passed! System is working!")
        else:
            print("\nRevenue predictor test failed")
    else:
        print("\nDatabase test failed")

if __name__ == "__main__":
    main()
