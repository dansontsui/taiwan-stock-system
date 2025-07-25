#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試所有收集腳本
確保每個腳本都能正常運行，避免正式啟動時出現問題
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def print_banner():
    """顯示測試橫幅"""
    print("=" * 80)
    print("🧪 台股分析系統腳本測試")
    print("=" * 80)
    print("📋 測試所有收集腳本，確保沒有問題")
    print("🎯 使用測試模式，只收集少量資料")
    print("=" * 80)

def test_script(script_name, description, args=None, timeout=300):
    """測試單個腳本"""
    print(f"\n🧪 測試: {description}")
    print(f"📜 腳本: {script_name}")
    print("-" * 60)
    
    # 檢查腳本是否存在
    script_path = f"scripts/{script_name}"
    if not os.path.exists(script_path):
        print(f"❌ 腳本不存在: {script_path}")
        return False
    
    # 準備命令
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"🔄 執行命令: {' '.join(cmd)}")
    
    try:
        # 執行腳本
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ 測試通過 (耗時: {duration:.1f}秒)")
            
            # 顯示部分輸出
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 10:
                    print("📄 輸出摘要 (最後10行):")
                    for line in lines[-10:]:
                        print(f"   {line}")
                else:
                    print("📄 完整輸出:")
                    for line in lines:
                        print(f"   {line}")
            
            return True
        else:
            print(f"❌ 測試失敗 (耗時: {duration:.1f}秒)")
            print(f"錯誤代碼: {result.returncode}")
            
            if result.stderr:
                print("錯誤輸出:")
                for line in result.stderr.strip().split('\n'):
                    print(f"   {line}")
            
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ 測試超時 (>{timeout}秒)")
        return False
    except Exception as e:
        print(f"❌ 測試異常: {e}")
        return False

def test_basic_imports():
    """測試基本模組導入"""
    print("\n🔧 測試基本模組導入...")
    
    modules = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('sqlite3', 'sqlite3'),
        ('requests', 'requests'),
        ('loguru', 'loguru')
    ]
    
    failed = []
    for module_name, import_name in modules:
        try:
            __import__(import_name)
            print(f"   ✅ {module_name}")
        except ImportError:
            print(f"   ❌ {module_name}")
            failed.append(module_name)
    
    if failed:
        print(f"\n⚠️ 缺少模組: {', '.join(failed)}")
        print("請執行: pip install " + " ".join(failed))
        return False
    
    print("✅ 所有基本模組導入成功")
    return True

def test_config_and_database():
    """測試配置和資料庫"""
    print("\n📊 測試配置和資料庫...")
    
    try:
        # 測試config導入
        try:
            from config import Config
            print("   ✅ config.py 導入成功")
            print(f"   📂 資料庫路徑: {Config.DATABASE_PATH}")
        except Exception as e:
            print(f"   ❌ config.py 導入失敗: {e}")
            return False
        
        # 測試資料庫連接
        import sqlite3
        if os.path.exists(Config.DATABASE_PATH):
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            # 檢查主要表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['stocks', 'stock_prices', 'monthly_revenues']
            existing_tables = [t for t in expected_tables if t in tables]
            
            print(f"   ✅ 資料庫連接成功")
            print(f"   📋 找到表格: {len(tables)} 個")
            print(f"   📊 核心表格: {len(existing_tables)}/{len(expected_tables)} 個")
            
            conn.close()
        else:
            print(f"   ⚠️ 資料庫檔案不存在: {Config.DATABASE_PATH}")
            print("   💡 首次使用需要先執行資料收集")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False

def main():
    """主函數"""
    print_banner()
    
    # 基本檢查
    if not test_basic_imports():
        print("\n❌ 基本模組測試失敗，請先安裝缺少的套件")
        return
    
    if not test_config_and_database():
        print("\n❌ 配置或資料庫測試失敗")
        return
    
    # 定義要測試的腳本
    test_scripts = [
        {
            'script': 'collect_stock_prices_smart.py',
            'description': '智能股價收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'collect_monthly_revenue.py',
            'description': '月營收收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'collect_financial_statements.py',
            'description': '綜合損益表收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'collect_balance_sheets.py',
            'description': '資產負債表收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'collect_cash_flows.py',
            'description': '現金流量表收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'collect_dividend_results.py',
            'description': '除權除息結果收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'collect_dividend_data.py',
            'description': '股利政策收集',
            'args': ['--test'],
            'timeout': 180
        },
        {
            'script': 'calculate_revenue_growth.py',
            'description': '營收成長率計算',
            'args': [],
            'timeout': 120
        },
        {
            'script': 'analyze_potential_stocks.py',
            'description': '潛力股分析',
            'args': ['--top', '10'],
            'timeout': 120
        }
    ]
    
    # 執行測試
    passed = 0
    failed = 0
    failed_scripts = []
    
    for test_config in test_scripts:
        success = test_script(
            test_config['script'],
            test_config['description'],
            test_config.get('args'),
            test_config.get('timeout', 300)
        )
        
        if success:
            passed += 1
        else:
            failed += 1
            failed_scripts.append(test_config['script'])
        
        # 測試間休息
        time.sleep(2)
    
    # 顯示測試結果
    print("\n" + "=" * 80)
    print("🎯 測試結果總結")
    print("=" * 80)
    print(f"✅ 通過: {passed} 個腳本")
    print(f"❌ 失敗: {failed} 個腳本")
    print(f"📊 成功率: {(passed/(passed+failed)*100):.1f}%")
    
    if failed_scripts:
        print(f"\n❌ 失敗的腳本:")
        for script in failed_scripts:
            print(f"   • {script}")
        
        print(f"\n💡 建議:")
        print(f"   1. 檢查失敗腳本的錯誤訊息")
        print(f"   2. 確認API Token設定正確")
        print(f"   3. 檢查網路連接")
        print(f"   4. 確認資料庫權限")
    else:
        print(f"\n🎉 所有腳本測試通過！")
        print(f"✅ 系統準備就緒，可以安全啟動")
        print(f"\n💡 建議使用:")
        print(f"   python 終端機監控.py --mode monitor")
        print(f"   python 簡易啟動.py --mode daily")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
