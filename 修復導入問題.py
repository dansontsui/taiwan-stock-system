#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復所有腳本中的導入問題
將錯誤的 app.database.database_manager 改為 app.utils.simple_database
"""

import os
import re

def fix_import_in_file(file_path):
    """修復單個檔案的導入問題"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修復導入語句
        patterns = [
            # 修復 from app.database.database_manager import DatabaseManager
            (r'from app\.database\.database_manager import DatabaseManager',
             'from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager'),
            
            # 修復 from app.database import database_manager
            (r'from app\.database import database_manager',
             'from app.utils import simple_database as database_manager'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # 如果內容有變化，寫回檔案
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修復: {file_path}")
            return True
        else:
            print(f"⏭️ 跳過: {file_path} (無需修復)")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤: {file_path} - {e}")
        return False

def main():
    """主函數"""
    print("🔧 開始修復導入問題...")
    print("=" * 60)
    
    # 需要檢查的檔案
    files_to_check = [
        # Python腳本
        '一鍵啟動.py',
        '簡易啟動.py',
        '終端機啟動.py',
        '終端機監控.py',
        '測試所有腳本.py',
        
        # scripts目錄下的腳本
        'scripts/collect_stock_prices_smart.py',
        'scripts/collect_monthly_revenue.py',
        'scripts/collect_financial_statements.py',
        'scripts/collect_balance_sheets.py',
        'scripts/collect_cash_flows.py',
        'scripts/collect_dividend_results.py',
        'scripts/collect_dividend_data.py',
        'scripts/collect_comprehensive_batch.py',
        'scripts/collect_all_10years.py',
        'scripts/collect_daily_update.py',
        'scripts/collect_batch.py',
        'scripts/analyze_potential_stocks.py',
        'scripts/calculate_revenue_growth.py',
        'scripts/expand_database.py',
        'scripts/init_database.py',
        'scripts/collect_10_stocks_10years.py',
    ]
    
    fixed_count = 0
    total_count = 0
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            total_count += 1
            if fix_import_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️ 檔案不存在: {file_path}")
    
    print("=" * 60)
    print(f"🎯 修復完成！")
    print(f"📊 檢查檔案: {total_count} 個")
    print(f"✅ 修復檔案: {fixed_count} 個")
    print(f"⏭️ 跳過檔案: {total_count - fixed_count} 個")
    
    if fixed_count > 0:
        print("\n💡 建議重新測試腳本:")
        print("python 測試所有腳本.py")
    else:
        print("\n✅ 所有檔案都已正確，無需修復")

if __name__ == "__main__":
    main()
