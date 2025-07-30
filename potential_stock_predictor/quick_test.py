#!/usr/bin/env python3
"""
快速測試基本功能
"""

def test_imports():
    """測試基本導入"""
    print("🔍 測試基本套件導入...")
    
    success_count = 0
    total_count = 0
    
    # 測試 pandas
    total_count += 1
    try:
        import pandas as pd
        print("   ✅ pandas 導入成功")
        success_count += 1
    except ImportError as e:
        print(f"   ❌ pandas 導入失敗: {e}")
    
    # 測試 numpy
    total_count += 1
    try:
        import numpy as np
        print("   ✅ numpy 導入成功")
        success_count += 1
    except ImportError as e:
        print(f"   ❌ numpy 導入失敗: {e}")
    
    # 測試 scikit-learn
    total_count += 1
    try:
        from sklearn.ensemble import RandomForestClassifier
        print("   ✅ scikit-learn 導入成功")
        success_count += 1
    except ImportError as e:
        print(f"   ❌ scikit-learn 導入失敗: {e}")
    
    # 測試 matplotlib (可選)
    total_count += 1
    try:
        import matplotlib
        matplotlib.use('Agg')  # 非互動式後端
        print("   ✅ matplotlib 導入成功")
        success_count += 1
    except ImportError as e:
        print(f"   ⚠️ matplotlib 導入失敗: {e} (可選套件)")
        success_count += 1  # 視為成功，因為是可選的
    
    print(f"\n📊 導入測試結果: {success_count}/{total_count} 成功")
    return success_count >= 3  # 至少需要前3個核心套件

def test_basic_functionality():
    """測試基本功能"""
    print("\n🧮 測試基本功能...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # 創建測試資料
        data = pd.DataFrame({
            'price': [100, 102, 98, 105, 103],
            'volume': [1000, 1200, 800, 1500, 1100]
        })
        
        # 計算移動平均
        data['ma_3'] = data['price'].rolling(window=3).mean()
        
        # 計算報酬率
        data['return'] = data['price'].pct_change()
        
        print("   ✅ 基本資料處理功能正常")
        
        # 測試機器學習
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # 創建簡單的分類資料
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        
        print("   ✅ 機器學習功能正常")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 基本功能測試失敗: {e}")
        return False

def test_database():
    """測試資料庫連接"""
    print("\n🗄️ 測試資料庫連接...")
    
    try:
        import sqlite3
        from pathlib import Path
        
        # 檢查主資料庫
        db_path = Path("../data/taiwan_stock.db")
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"   ✅ 資料庫連接成功，包含 {len(tables)} 個資料表")
            
            # 檢查關鍵資料表
            table_names = [table[0] for table in tables]
            key_tables = ['stocks', 'stock_prices', 'monthly_revenues']
            
            for table in key_tables:
                if table in table_names:
                    print(f"   ✅ 找到關鍵資料表: {table}")
                else:
                    print(f"   ⚠️ 缺少資料表: {table}")
            
            conn.close()
            return True
        else:
            print(f"   ⚠️ 找不到資料庫檔案: {db_path}")
            print("   請先執行主系統收集資料: cd ../ && python c.py")
            return False
            
    except Exception as e:
        print(f"   ❌ 資料庫測試失敗: {e}")
        return False

def main():
    """主程式"""
    print("🚀 潛力股預測系統快速測試")
    print("=" * 50)
    
    results = []
    
    # 測試導入
    results.append(("套件導入", test_imports()))
    
    # 測試基本功能
    results.append(("基本功能", test_basic_functionality()))
    
    # 測試資料庫
    results.append(("資料庫連接", test_database()))
    
    # 總結
    print("\n📋 測試總結")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 總體結果: {passed}/{total} 通過 ({passed/total:.1%})")
    
    if passed >= 2:  # 至少需要套件導入和基本功能通過
        print("\n🎉 系統基本功能正常！")
        print("\n📚 下一步:")
        print("   1. 如果資料庫測試失敗，請先收集資料:")
        print("      cd ../")
        print("      python c.py")
        print("   2. 安裝高級機器學習套件:")
        print("      pip install lightgbm xgboost optuna")
        print("   3. 執行完整示範:")
        print("      python demo.py")
    else:
        print("\n⚠️ 系統存在問題，請檢查套件安裝")
        print("   pip install pandas numpy scikit-learn")

if __name__ == "__main__":
    main()
