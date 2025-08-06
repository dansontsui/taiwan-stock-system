#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Test Upgrade Verification
測試功能升級驗證腳本
"""

import sys
import os
from pathlib import Path
import warnings
import subprocess
import time
warnings.filterwarnings('ignore')

# 設定編碼以支援中文輸出
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def run_test_command():
    """執行測試命令並檢查結果"""
    print("🧪 驗證 --test 命令升級...")
    
    try:
        # 執行測試命令
        result = subprocess.run(
            [sys.executable, 'main.py', '--test'],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )
        
        # 檢查返回碼
        if result.returncode == 0:
            print("✅ 測試命令執行成功")
        else:
            print(f"❌ 測試命令執行失敗，返回碼: {result.returncode}")
            if result.stderr:
                print(f"錯誤輸出: {result.stderr}")
        
        # 檢查輸出內容
        output = result.stdout
        if output:
            print(f"\n📄 命令輸出:")
            print(output)
        
        # 驗證是否包含營收和EPS測試
        has_revenue_test = "營收預測" in output or "revenue" in output.lower()
        has_eps_test = "EPS預測" in output or "eps" in output.lower()
        
        print(f"\n📊 測試內容驗證:")
        print(f"包含營收測試: {'✅' if has_revenue_test else '❌'}")
        print(f"包含EPS測試: {'✅' if has_eps_test else '❌'}")
        
        return has_revenue_test and has_eps_test
        
    except subprocess.TimeoutExpired:
        print("❌ 測試命令執行超時")
        return False
    except Exception as e:
        print(f"❌ 測試命令執行錯誤: {e}")
        return False

def check_log_file():
    """檢查日誌檔案中的測試記錄"""
    print("\n📋 檢查日誌檔案...")
    
    try:
        log_file = Path(__file__).parent / 'logs' / 'predictor.log'
        
        if not log_file.exists():
            print("❌ 日誌檔案不存在")
            return False
        
        # 讀取最後100行日誌
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-100:] if len(lines) > 100 else lines
        
        # 檢查是否有營收和EPS預測記錄
        revenue_logs = [line for line in recent_lines if "營收預測完成" in line]
        eps_logs = [line for line in recent_lines if "EPS預測完成" in line]
        
        print(f"最近營收預測記錄: {len(revenue_logs)} 筆")
        print(f"最近EPS預測記錄: {len(eps_logs)} 筆")
        
        if revenue_logs:
            print(f"最新營收預測: {revenue_logs[-1].strip()}")
        
        if eps_logs:
            print(f"最新EPS預測: {eps_logs[-1].strip()}")
        
        return len(revenue_logs) > 0 and len(eps_logs) > 0
        
    except Exception as e:
        print(f"❌ 檢查日誌檔案錯誤: {e}")
        return False

def check_help_message():
    """檢查幫助訊息是否更新"""
    print("\n📖 檢查幫助訊息...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        
        help_text = result.stdout
        
        # 檢查是否包含更新的測試說明
        has_complete_test = "完整測試" in help_text or "營收+EPS" in help_text
        
        print(f"幫助訊息包含完整測試說明: {'✅' if has_complete_test else '❌'}")
        
        if has_complete_test:
            # 找到測試相關的行
            for line in help_text.split('\n'):
                if '--test' in line or '完整測試' in line:
                    print(f"測試說明: {line.strip()}")
        
        return has_complete_test
        
    except Exception as e:
        print(f"❌ 檢查幫助訊息錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 測試功能升級驗證")
    print("=" * 50)
    
    print("驗證項目:")
    print("1. --test 命令是否同時執行營收和EPS預測")
    print("2. 日誌檔案是否記錄兩種預測結果")
    print("3. 幫助訊息是否更新")
    print("=" * 50)
    
    # 執行驗證
    tests = [
        ("測試命令執行", run_test_command),
        ("日誌檔案檢查", check_log_file),
        ("幫助訊息檢查", check_help_message)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 執行: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通過")
        else:
            print(f"❌ {test_name} 失敗")
        print("-" * 30)
    
    # 總結
    print(f"\n📋 驗證結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 測試功能升級成功！")
        print("現在 --test 命令會同時執行營收和EPS預測。")
        return 0
    else:
        print("⚠️  部分驗證失敗，請檢查升級狀態。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
