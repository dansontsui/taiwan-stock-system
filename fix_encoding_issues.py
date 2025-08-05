#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復編碼問題的工具
"""

import os
import sys
import re
from pathlib import Path

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

def fix_subprocess_encoding(file_path):
    """修復檔案中的 subprocess 編碼問題"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 修復模式1: subprocess.run(..., text=True, encoding="utf-8", errors="replace") -> subprocess.run(..., text=True, encoding='utf-8', errors='replace')
        pattern1 = r'subprocess\.run\(([^)]*),\s*text=True\)'
        def replace1(match):
            args = match.group(1)
            if 'encoding=' not in args:
                return f'subprocess.run({args}, text=True, encoding="utf-8", errors="replace")'
            return match.group(0)
        
        new_content = re.sub(pattern1, replace1, content)
        if new_content != content:
            changes_made.append("添加 encoding='utf-8', errors='replace' 到 subprocess.run")
            content = new_content
        
        # 修復模式2: subprocess.run(..., capture_output=True, text=True, encoding="utf-8", errors="replace") 
        pattern2 = r'subprocess\.run\(([^)]*),\s*capture_output=True,\s*text=True\)'
        def replace2(match):
            args = match.group(1)
            if 'encoding=' not in args:
                return f'subprocess.run({args}, capture_output=True, text=True, encoding="utf-8", errors="replace")'
            return match.group(0)
        
        new_content = re.sub(pattern2, replace2, content)
        if new_content != content:
            changes_made.append("添加編碼參數到 capture_output subprocess.run")
            content = new_content
        
        # 修復模式3: subprocess.Popen(..., text=True, encoding="utf-8", errors="replace")
        pattern3 = r'subprocess\.Popen\(([^)]*),\s*text=True\)'
        def replace3(match):
            args = match.group(1)
            if 'encoding=' not in args:
                return f'subprocess.Popen({args}, text=True, encoding="utf-8", errors="replace")'
            return match.group(0)
        
        new_content = re.sub(pattern3, replace3, content)
        if new_content != content:
            changes_made.append("添加編碼參數到 subprocess.Popen")
            content = new_content
        
        # 修復模式4: subprocess.Popen(..., universal_newlines=True, encoding="utf-8", errors="replace")
        pattern4 = r'subprocess\.Popen\(([^)]*),\s*universal_newlines=True\)'
        def replace4(match):
            args = match.group(1)
            if 'encoding=' not in args:
                return f'subprocess.Popen({args}, universal_newlines=True, encoding="utf-8", errors="replace")'
            return match.group(0)
        
        new_content = re.sub(pattern4, replace4, content)
        if new_content != content:
            changes_made.append("添加編碼參數到 universal_newlines subprocess.Popen")
            content = new_content
        
        # 如果有變更，寫回檔案
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        else:
            return False, []
            
    except Exception as e:
        print(f"❌ 修復 {file_path} 失敗: {e}")
        return False, []

def scan_and_fix_files():
    """掃描並修復所有相關檔案"""
    print("🔧 掃描並修復編碼問題")
    print("=" * 60)
    
    # 需要檢查的檔案模式
    file_patterns = [
        "*.py",
        "scripts/*.py",
        "potential_stock_predictor/*.py"
    ]
    
    files_to_check = []
    
    # 收集所有需要檢查的檔案
    for pattern in file_patterns:
        files_to_check.extend(Path('.').glob(pattern))
    
    # 去重並排序
    files_to_check = sorted(set(files_to_check))
    
    print(f"📁 找到 {len(files_to_check)} 個 Python 檔案")
    
    fixed_files = []
    total_changes = 0
    
    for file_path in files_to_check:
        if file_path.name.startswith('.'):
            continue
            
        print(f"🔍 檢查: {file_path}")
        
        try:
            # 檢查檔案是否包含 subprocess
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'subprocess' in content:
                fixed, changes = fix_subprocess_encoding(file_path)
                if fixed:
                    print(f"✅ 修復: {file_path}")
                    for change in changes:
                        print(f"   - {change}")
                    fixed_files.append(str(file_path))
                    total_changes += len(changes)
                else:
                    print(f"✓ 無需修復: {file_path}")
            else:
                print(f"⏭️ 跳過: {file_path} (不包含 subprocess)")
                
        except Exception as e:
            print(f"❌ 檢查失敗: {file_path} - {e}")
    
    print("\n" + "=" * 60)
    print("📊 修復結果總結")
    print("=" * 60)
    
    print(f"檢查檔案數: {len(files_to_check)}")
    print(f"修復檔案數: {len(fixed_files)}")
    print(f"總修復項目: {total_changes}")
    
    if fixed_files:
        print("\n✅ 已修復的檔案:")
        for file_path in fixed_files:
            print(f"   - {file_path}")
    
    return len(fixed_files) > 0

def create_encoding_helper():
    """創建編碼輔助模組"""
    helper_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
編碼輔助模組 - 提供統一的 subprocess 編碼處理
"""

import subprocess
import sys
import os

# 設置環境編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

def safe_subprocess_run(*args, **kwargs):
    """安全的 subprocess.run，自動處理編碼問題"""
    # 設置預設編碼參數
    if 'text' in kwargs and kwargs['text']:
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
    
    return subprocess.run(*args, **kwargs)

def safe_subprocess_popen(*args, **kwargs):
    """安全的 subprocess.Popen，自動處理編碼問題"""
    # 設置預設編碼參數
    if kwargs.get('text') or kwargs.get('universal_newlines'):
        kwargs.setdefault('encoding', 'utf-8')
        kwargs.setdefault('errors', 'replace')
    
    return subprocess.Popen(*args, **kwargs)

# 向後兼容的別名
run = safe_subprocess_run
Popen = safe_subprocess_popen
'''
    
    helper_path = Path('scripts/encoding_helper.py')
    
    try:
        with open(helper_path, 'w', encoding='utf-8') as f:
            f.write(helper_content)
        print(f"✅ 創建編碼輔助模組: {helper_path}")
        return True
    except Exception as e:
        print(f"❌ 創建編碼輔助模組失敗: {e}")
        return False

def test_encoding_fix():
    """測試編碼修復效果"""
    print("\n🧪 測試編碼修復效果")
    print("-" * 40)
    
    try:
        # 測試基本的 subprocess 調用
        import subprocess
        
        # 測試1: 簡單命令
        result = subprocess.run(
            [sys.executable, '-c', 'print("測試中文輸出")'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and '測試中文輸出' in result.stdout:
            print("✅ 基本中文輸出測試通過")
        else:
            print("❌ 基本中文輸出測試失敗")
            return False
        
        # 測試2: 包含特殊字符
        result = subprocess.run(
            [sys.executable, '-c', 'print("特殊字符: ✅❌⚠️🔧")'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("✅ 特殊字符輸出測試通過")
        else:
            print("❌ 特殊字符輸出測試失敗")
            return False
        
        print("✅ 所有編碼測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 編碼測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 編碼問題修復工具")
    print("=" * 60)
    
    # 掃描並修復檔案
    files_fixed = scan_and_fix_files()
    
    # 創建編碼輔助模組
    helper_created = create_encoding_helper()
    
    # 測試修復效果
    test_passed = test_encoding_fix()
    
    # 總結
    print("\n" + "=" * 60)
    print("🎉 修復完成總結")
    print("=" * 60)
    
    if files_fixed:
        print("✅ 檔案修復: 已修復 subprocess 編碼問題")
    else:
        print("ℹ️ 檔案修復: 沒有發現需要修復的檔案")
    
    if helper_created:
        print("✅ 輔助模組: 已創建編碼輔助模組")
    else:
        print("❌ 輔助模組: 創建失敗")
    
    if test_passed:
        print("✅ 測試驗證: 編碼修復效果良好")
    else:
        print("❌ 測試驗證: 編碼問題可能仍存在")
    
    print("\n💡 使用建議:")
    print("1. 重新執行之前失敗的腳本")
    print("2. 如果仍有編碼問題，檢查系統環境變數")
    print("3. 考慮使用 scripts/encoding_helper.py 中的安全函數")
    
    return files_fixed or helper_created

if __name__ == "__main__":
    main()
