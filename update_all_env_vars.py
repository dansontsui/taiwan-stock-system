#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一更新所有檔案使用環境變數
"""

import os
import re
from pathlib import Path

def find_hardcoded_tokens():
    """尋找所有硬編碼的API Token"""
    print("🔍 掃描硬編碼的API Token")
    print("=" * 60)
    
    # 硬編碼的Token模式
    token_pattern = r'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9\.[^"\']*'
    
    # 要掃描的檔案模式
    file_patterns = [
        "*.py",
        "scripts/*.py",
        "app/**/*.py",
        "potential_stock_predictor/*.py"
    ]
    
    files_with_tokens = []
    
    for pattern in file_patterns:
        for file_path in Path('.').glob(pattern):
            if file_path.name.startswith('.') or 'test_env.py' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if re.search(token_pattern, content):
                    files_with_tokens.append(file_path)
                    print(f"❌ 發現硬編碼Token: {file_path}")
                    
            except Exception as e:
                print(f"⚠️ 無法讀取: {file_path} - {e}")
    
    if not files_with_tokens:
        print("✅ 沒有發現硬編碼的API Token")
    
    return files_with_tokens

def check_env_usage():
    """檢查所有檔案的環境變數使用情況"""
    print("\n🔍 檢查環境變數使用情況")
    print("=" * 60)
    
    # 要檢查的檔案
    important_files = [
        "config.py",
        "simple_collect.py", 
        "scripts/collect_with_resume.py",
        "scripts/collect_comprehensive_batch.py",
        "fix_8299_cash_flow.py",
        "scripts/collect_dividend_data.py",
        "scripts/collect_financial_statements.py",
        "scripts/collect_balance_sheets.py",
        "scripts/analyze_potential_stocks.py"
    ]
    
    results = {}
    
    for file_path in important_files:
        if not os.path.exists(file_path):
            results[file_path] = "檔案不存在"
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查是否使用環境變數
            has_dotenv = 'from dotenv import load_dotenv' in content or 'import dotenv' in content
            has_load_dotenv = 'load_dotenv()' in content
            has_getenv = 'os.getenv(' in content and 'FINMIND_API_TOKEN' in content
            has_hardcoded = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9' in content
            
            if has_dotenv and has_load_dotenv and has_getenv and not has_hardcoded:
                results[file_path] = "✅ 正確使用環境變數"
            elif has_hardcoded:
                results[file_path] = "❌ 仍有硬編碼Token"
            elif not has_dotenv:
                results[file_path] = "⚠️ 未導入dotenv"
            elif not has_getenv:
                results[file_path] = "⚠️ 未使用os.getenv"
            else:
                results[file_path] = "⚠️ 部分配置"
                
        except Exception as e:
            results[file_path] = f"❌ 讀取錯誤: {e}"
    
    # 顯示結果
    for file_path, status in results.items():
        print(f"{status}: {file_path}")
    
    return results

def test_env_loading():
    """測試環境變數載入"""
    print("\n🧪 測試環境變數載入")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # 檢查關鍵環境變數
        env_vars = {
            'FINMIND_API_TOKEN': os.getenv('FINMIND_API_TOKEN'),
            'DATABASE_PATH': os.getenv('DATABASE_PATH'),
            'FINMIND_API_URL': os.getenv('FINMIND_API_URL')
        }
        
        for var_name, value in env_vars.items():
            if value:
                if var_name == 'FINMIND_API_TOKEN':
                    display_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***"
                else:
                    display_value = value
                print(f"✅ {var_name}: {display_value}")
            else:
                print(f"❌ {var_name}: 未設定")
        
        # 測試config.py載入
        try:
            from config import Config
            token_status = "已設定" if Config.FINMIND_API_TOKEN else "未設定"
            print(f"✅ Config.FINMIND_API_TOKEN: {token_status}")
        except Exception as e:
            print(f"❌ Config載入失敗: {e}")
            
    except ImportError:
        print("❌ python-dotenv 未安裝")
        print("請執行: pip install python-dotenv")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def generate_summary():
    """生成總結報告"""
    print("\n📊 環境變數使用總結")
    print("=" * 60)
    
    # 檢查.env檔案
    env_exists = os.path.exists('.env')
    env_example_exists = os.path.exists('.env.example')
    gitignore_has_env = False
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
            gitignore_has_env = '.env' in gitignore_content
    
    print(f"📁 .env 檔案: {'✅ 存在' if env_exists else '❌ 不存在'}")
    print(f"📁 .env.example 檔案: {'✅ 存在' if env_example_exists else '❌ 不存在'}")
    print(f"🔒 .gitignore 包含 .env: {'✅ 是' if gitignore_has_env else '❌ 否'}")
    
    # 檢查python-dotenv
    try:
        import dotenv
        print("📦 python-dotenv: ✅ 已安裝")
    except ImportError:
        print("📦 python-dotenv: ❌ 未安裝")
    
    print("\n🎯 建議:")
    if not env_exists:
        print("- 創建 .env 檔案並設定 FINMIND_API_TOKEN")
    if not gitignore_has_env:
        print("- 將 .env 加入 .gitignore")
    
    try:
        import dotenv
    except ImportError:
        print("- 安裝 python-dotenv: pip install python-dotenv")

def main():
    """主函數"""
    print("🔐 環境變數統一檢查工具")
    print("=" * 60)
    
    # 1. 尋找硬編碼Token
    hardcoded_files = find_hardcoded_tokens()
    
    # 2. 檢查環境變數使用
    env_usage = check_env_usage()
    
    # 3. 測試環境變數載入
    test_env_loading()
    
    # 4. 生成總結
    generate_summary()
    
    print("\n" + "=" * 60)
    print("🎉 檢查完成！")
    
    if hardcoded_files:
        print(f"⚠️ 發現 {len(hardcoded_files)} 個檔案仍有硬編碼Token")
    else:
        print("✅ 所有檔案都已使用環境變數")

if __name__ == "__main__":
    main()
