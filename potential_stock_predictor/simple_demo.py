#!/usr/bin/env python3
"""
潛力股預測系統簡化示範程式

測試基本功能和依賴套件
"""

import sys
import os
from pathlib import Path

def test_basic_imports():
    """測試基本套件導入"""
    print("🔍 測試基本套件導入...")
    
    try:
        import pandas as pd
        print("   ✅ pandas 導入成功")
    except ImportError as e:
        print(f"   ❌ pandas 導入失敗: {e}")
        return False
    
    try:
        import numpy as np
        print("   ✅ numpy 導入成功")
    except ImportError as e:
        print(f"   ❌ numpy 導入失敗: {e}")
        return False
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # 使用非互動式後端
        import matplotlib.pyplot as plt
        print("   ✅ matplotlib 導入成功")
    except ImportError as e:
        print(f"   ❌ matplotlib 導入失敗: {e}")
        print("   ⚠️ matplotlib 是可選套件，不影響核心功能")
        # 不返回 False，因為 matplotlib 是可選的
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        print("   ✅ scikit-learn 導入成功")
    except ImportError as e:
        print(f"   ❌ scikit-learn 導入失敗: {e}")
        return False
    
    try:
        import tqdm
        print("   ✅ tqdm 導入成功")
    except ImportError as e:
        print(f"   ❌ tqdm 導入失敗: {e}")
        return False
    
    try:
        import joblib
        print("   ✅ joblib 導入成功")
    except ImportError as e:
        print(f"   ❌ joblib 導入失敗: {e}")
        return False
    
    return True

def test_database_connection():
    """測試資料庫連接"""
    print("\n📊 測試資料庫連接...")
    
    try:
        import sqlite3
        
        # 檢查主資料庫是否存在
        db_path = Path("../data/taiwan_stock.db")
        if db_path.exists():
            print(f"   ✅ 找到資料庫檔案: {db_path}")
            
            # 嘗試連接
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 檢查資料表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"   📋 資料庫包含 {len(tables)} 個資料表:")
            for table in tables[:5]:  # 只顯示前5個
                print(f"      - {table[0]}")
            
            if len(tables) > 5:
                print(f"      ... 還有 {len(tables) - 5} 個資料表")
            
            conn.close()
            return True
        else:
            print(f"   ⚠️ 找不到資料庫檔案: {db_path}")
            print("   請確保已執行主系統的資料收集功能")
            return False
            
    except Exception as e:
        print(f"   ❌ 資料庫連接失敗: {e}")
        return False

def test_directory_structure():
    """測試目錄結構"""
    print("\n📁 檢查目錄結構...")
    
    required_dirs = [
        "src",
        "src/features",
        "src/models", 
        "src/utils",
        "config",
        "data",
        "models",
        "notebooks",
        "tests"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ (缺失)")
            all_exist = False
    
    return all_exist

def test_core_files():
    """測試核心檔案"""
    print("\n📄 檢查核心檔案...")
    
    required_files = [
        "config/config.py",
        "src/utils/database.py",
        "src/utils/helpers.py",
        "src/features/feature_engineering.py",
        "src/features/target_generator.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {file_name} ({size} bytes)")
        else:
            print(f"   ❌ {file_name} (缺失)")
            all_exist = False
    
    return all_exist

def test_technical_indicators():
    """測試技術指標計算"""
    print("\n📈 測試技術指標計算...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # 創建測試資料
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
        
        test_data = pd.DataFrame({
            'date': dates,
            'close_price': prices,
            'high_price': prices + np.random.rand(50) * 2,
            'low_price': prices - np.random.rand(50) * 2,
            'volume': np.random.randint(1000, 10000, 50)
        })
        
        print(f"   ✅ 創建測試資料: {len(test_data)} 筆")
        
        # 測試移動平均
        ma_5 = test_data['close_price'].rolling(window=5).mean()
        print(f"   ✅ 5日移動平均計算成功")
        
        # 測試RSI
        delta = test_data['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        print(f"   ✅ RSI指標計算成功")
        
        # 測試波動率
        returns = test_data['close_price'].pct_change()
        volatility = returns.rolling(window=20).std() * np.sqrt(252)
        print(f"   ✅ 波動率計算成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 技術指標計算失敗: {e}")
        return False

def main():
    """主程式"""
    print("🚀 潛力股預測系統簡化示範")
    print("=" * 60)
    
    # 測試結果
    results = []
    
    # 1. 測試基本套件導入
    results.append(("基本套件導入", test_basic_imports()))
    
    # 2. 測試目錄結構
    results.append(("目錄結構", test_directory_structure()))
    
    # 3. 測試核心檔案
    results.append(("核心檔案", test_core_files()))
    
    # 4. 測試資料庫連接
    results.append(("資料庫連接", test_database_connection()))
    
    # 5. 測試技術指標
    results.append(("技術指標計算", test_technical_indicators()))
    
    # 總結
    print("\n📋 測試總結")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 測試結果: {passed}/{total} 通過 ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 所有測試通過！潛力股預測系統基礎環境正常。")
        print("\n📚 下一步建議:")
        print("   1. 安裝高級機器學習套件:")
        print("      pip install lightgbm xgboost optuna")
        print("   2. 執行完整示範:")
        print("      python demo.py")
        print("   3. 開始使用系統:")
        print("      python main.py --help")
    else:
        print(f"\n⚠️ 有 {total - passed} 個測試失敗，請檢查相關問題。")
        
        if not results[0][1]:  # 基本套件導入失敗
            print("\n🔧 安裝基本依賴:")
            print("   pip install pandas numpy scikit-learn matplotlib tqdm python-dateutil joblib")
        
        if not results[3][1]:  # 資料庫連接失敗
            print("\n🗄️ 資料庫問題:")
            print("   請先執行主系統收集股票資料:")
            print("   cd ../")
            print("   python c.py")

if __name__ == "__main__":
    main()
