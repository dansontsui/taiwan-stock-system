#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 c.py 檔案呼叫的所有 Python 腳本
"""

import re
from pathlib import Path

def analyze_c_py_calls():
    """分析 c.py 呼叫的所有 Python 檔案"""
    print("=" * 60)
    print("🔍 分析 c.py 呼叫的 Python 檔案")
    print("=" * 60)
    
    c_py_path = Path('c.py')
    if not c_py_path.exists():
        print("❌ c.py 檔案不存在")
        return
    
    # 讀取 c.py 內容
    with open(c_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 儲存所有找到的 Python 檔案
    python_files = set()
    
    # 1. 查找 run_script() 呼叫
    print("📋 1. 透過 run_script() 呼叫的腳本:")
    run_script_pattern = r"run_script\(['\"]([^'\"]+\.py)['\"]"
    matches = re.findall(run_script_pattern, content)
    
    for match in matches:
        full_path = f"scripts/{match}"
        python_files.add(full_path)
        print(f"  ✅ {full_path}")
    
    # 2. 查找直接路徑呼叫
    print(f"\n📋 2. 直接路徑呼叫的腳本:")
    direct_path_patterns = [
        r'Path\(__file__\)\.parent / ["\']([^"\']+\.py)["\']',
        r'script_path = .*["\']([^"\']+\.py)["\']'
    ]
    
    for pattern in direct_path_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            python_files.add(match)
            print(f"  ✅ {match}")
    
    # 3. 查找 import 語句
    print(f"\n📋 3. 透過 import 導入的模組:")
    import_patterns = [
        r'from scripts\.([^.\s]+)',
        r'import scripts\.([^.\s]+)'
    ]
    
    for pattern in import_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            module_path = f"scripts/{match}.py"
            python_files.add(module_path)
            print(f"  ✅ {module_path}")
    
    # 4. 檢查檔案是否存在
    print(f"\n📋 4. 檔案存在性檢查:")
    existing_files = []
    missing_files = []
    
    for file_path in sorted(python_files):
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"  ✅ {file_path} (存在)")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} (不存在)")
    
    # 5. 統計結果
    print(f"\n📊 統計結果:")
    print(f"  總共呼叫的 Python 檔案數: {len(python_files)}")
    print(f"  存在的檔案數: {len(existing_files)}")
    print(f"  缺失的檔案數: {len(missing_files)}")
    print(f"  檔案存在率: {len(existing_files)/len(python_files)*100:.1f}%")
    
    # 6. 詳細清單
    print(f"\n📋 完整清單:")
    print("=" * 40)
    
    for i, file_path in enumerate(sorted(python_files), 1):
        status = "✅" if Path(file_path).exists() else "❌"
        print(f"{i:2d}. {status} {file_path}")
    
    # 7. 功能分類
    print(f"\n📂 功能分類:")
    print("=" * 40)
    
    categories = {
        "基礎收集": ["simple_collect.py"],
        "財務資料": ["collect_financial_statements.py", "collect_balance_sheets.py"],
        "股利資料": ["collect_dividend_data.py", "collect_dividend_results.py"],
        "分析功能": ["analyze_potential_stocks.py"],
        "輔助功能": ["scripts/simple_progress.py"]
    }
    
    for category, files in categories.items():
        print(f"\n🔸 {category}:")
        for file in files:
            if file in python_files or f"scripts/{file}" in python_files:
                full_path = file if file.startswith("scripts/") else file
                if file in python_files:
                    full_path = file
                elif f"scripts/{file}" in python_files:
                    full_path = f"scripts/{file}"
                
                status = "✅" if Path(full_path).exists() else "❌"
                print(f"  {status} {full_path}")
    
    return python_files

def analyze_script_dependencies():
    """分析腳本之間的依賴關係"""
    print(f"\n" + "=" * 60)
    print("🔗 腳本依賴關係分析")
    print("=" * 60)
    
    # 分析 c.py 中的函數呼叫關係
    c_py_path = Path('c.py')
    with open(c_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找函數定義和呼叫
    function_calls = {
        "run_collect": ["simple_collect.py"],
        "run_collect_with_stock": ["simple_collect.py"],
        "run_financial_collection": ["scripts/collect_financial_statements.py"],
        "run_balance_collection": ["scripts/collect_balance_sheets.py"],
        "run_dividend_collection": ["scripts/collect_dividend_data.py", "scripts/collect_dividend_results.py"],
        "run_analysis": ["scripts/analyze_potential_stocks.py"]
    }
    
    print("📋 函數與腳本對應關係:")
    for func_name, scripts in function_calls.items():
        print(f"\n🔸 {func_name}():")
        for script in scripts:
            status = "✅" if Path(script).exists() else "❌"
            print(f"  {status} {script}")

def main():
    """主函數"""
    print("🔍 c.py 檔案呼叫分析")
    print(f"⏰ 分析時間: {Path('c.py').stat().st_mtime}")
    
    # 執行分析
    python_files = analyze_c_py_calls()
    analyze_script_dependencies()
    
    print(f"\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)
    
    return python_files

if __name__ == "__main__":
    main()
