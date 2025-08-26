#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查專案結構完整性
"""

import os
import sys
from pathlib import Path

def check_project_structure():
    """檢查專案結構是否完整"""
    print("🔍 檢查專案結構完整性")
    print("=" * 50)
    
    # 獲取當前目錄
    current_dir = Path.cwd()
    print(f"📁 當前目錄: {current_dir}")
    
    # 檢查必要的目錄和檔案
    required_structure = {
        'stock_price_investment_system/': 'dir',
        'stock_price_investment_system/__init__.py': 'file',
        'stock_price_investment_system/config/': 'dir',
        'stock_price_investment_system/config/__init__.py': 'file',
        'stock_price_investment_system/config/settings.py': 'file',
        'stock_price_investment_system/selector/': 'dir',
        'stock_price_investment_system/selector/__init__.py': 'file',
        'stock_price_investment_system/selector/candidate_pool_generator.py': 'file',
        'stock_price_investment_system/data/': 'dir',
        'stock_price_investment_system/data/__init__.py': 'file',
        'stock_price_investment_system/data/data_manager.py': 'file',
        'stock_price_investment_system/price_models/': 'dir',
        'stock_price_investment_system/price_models/__init__.py': 'file',
        'stock_price_investment_system/price_models/feature_engineering.py': 'file',
        'stock_price_investment_system/price_models/stock_price_predictor.py': 'file',
        'stock_price_investment_system/price_models/walk_forward_validator.py': 'file',
        'stock_price_investment_system/price_models/holdout_backtester.py': 'file',
        'stock_price_investment_system/utils/': 'dir',
        'stock_price_investment_system/utils/__init__.py': 'file',
        'stock_price_investment_system/start.py': 'file',
    }
    
    missing_items = []
    existing_items = []
    
    print(f"\n📋 檢查必要檔案和目錄:")
    for item_path, item_type in required_structure.items():
        full_path = current_dir / item_path
        
        if item_type == 'dir':
            exists = full_path.is_dir()
            type_str = "目錄"
        else:
            exists = full_path.is_file()
            type_str = "檔案"
        
        if exists:
            print(f"   ✅ {item_path} ({type_str})")
            existing_items.append(item_path)
        else:
            print(f"   ❌ {item_path} ({type_str}) - 缺失")
            missing_items.append(item_path)
    
    print(f"\n📊 統計:")
    print(f"   存在: {len(existing_items)} 項")
    print(f"   缺失: {len(missing_items)} 項")
    
    if missing_items:
        print(f"\n⚠️  缺失的項目:")
        for item in missing_items:
            print(f"   • {item}")
        
        print(f"\n💡 解決方案:")
        print(f"   1. 確保完整複製整個專案資料夾")
        print(f"   2. 檢查是否有檔案被防毒軟體隔離")
        print(f"   3. 確認複製過程中沒有錯誤")
        
        return False
    else:
        print(f"\n🎉 專案結構完整！")
        
        # 測試 Python 路徑
        print(f"\n🐍 測試 Python 路徑:")
        print(f"   當前 Python 路徑:")
        for i, path in enumerate(sys.path):
            print(f"     {i+1}. {path}")
        
        # 測試匯入
        print(f"\n🧪 測試關鍵模組匯入:")
        test_imports = [
            'stock_price_investment_system',
            'stock_price_investment_system.config',
            'stock_price_investment_system.config.settings',
            'stock_price_investment_system.selector',
            'stock_price_investment_system.selector.candidate_pool_generator',
        ]
        
        for module_name in test_imports:
            try:
                __import__(module_name)
                print(f"   ✅ {module_name}")
            except ImportError as e:
                print(f"   ❌ {module_name} - {e}")
                return False
        
        print(f"\n🎯 建議的執行方式:")
        print(f"   在專案根目錄下執行:")
        print(f"   python stock_price_investment_system/start.py")
        print(f"   或")
        print(f"   python -m stock_price_investment_system.start")
        
        return True

if __name__ == '__main__':
    success = check_project_structure()
    if not success:
        print(f"\n❌ 專案結構不完整，請修正後再執行")
        sys.exit(1)
    else:
        print(f"\n✅ 專案結構檢查通過")
        sys.exit(0)
