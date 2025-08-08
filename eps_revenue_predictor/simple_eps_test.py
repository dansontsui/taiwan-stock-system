# -*- coding: utf-8 -*-
"""
簡單EPS測試
"""

print("🧪 開始簡單EPS測試")

try:
    import sys
    from pathlib import Path
    
    # 添加專案根目錄到路徑
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    print("📦 導入模組...")
    from src.data.database_manager import DatabaseManager
    
    print("🔧 初始化資料庫管理器...")
    db_manager = DatabaseManager()
    
    stock_id = "2385"
    print(f"📊 測試股票: {stock_id}")
    
    print("📈 獲取季度財務資料...")
    financial_data = db_manager.get_quarterly_financial_data(stock_id)
    print(f"✅ 獲取 {len(financial_data)} 筆資料")
    
    if len(financial_data) > 0:
        print(f"   欄位: {list(financial_data.columns)}")
        print(f"   日期範圍: {financial_data['date'].min()} ~ {financial_data['date'].max()}")
        
        # 檢查EPS資料
        if 'eps' in financial_data.columns:
            eps_data = financial_data['eps'].dropna()
            print(f"   有效EPS資料: {len(eps_data)} 筆")
            if len(eps_data) > 0:
                print(f"   EPS範例: {eps_data.head(3).tolist()}")
        
        # 測試日期轉換
        print("\n🔄 測試日期轉換...")
        test_date = "2024-03-31"
        
        # 使用資料庫管理器的方法
        quarter = db_manager._quarter_to_date("2024-Q1")
        print(f"   2024-Q1 -> {quarter}")
        
    print("\n✅ 簡單EPS測試完成")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
