# -*- coding: utf-8 -*-
"""
檢查資料庫表格結構
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_tables():
    """檢查資料庫表格結構"""
    
    try:
        from src.data.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查看所有表格
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print("📊 資料庫表格:")
            for table in tables:
                table_name = table[0]
                print(f"  {table_name}")
                
                # 查看表格結構
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                print(f"    欄位:")
                for col in columns:
                    print(f"      {col[1]} ({col[2]})")
                
                # 查看資料筆數
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"    資料筆數: {count}")
                
                # 如果是8299相關的資料，顯示範例
                if count > 0:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} WHERE stock_id = '8299' LIMIT 3")
                        sample_data = cursor.fetchall()
                        if sample_data:
                            print(f"    8299範例資料:")
                            for row in sample_data:
                                print(f"      {row}")
                    except:
                        pass
                
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_tables()
