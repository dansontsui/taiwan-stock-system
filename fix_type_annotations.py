#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正 Python 3.9 類型註解相容性問題
將 Type | None 改為 Optional[Type]
"""

import os
import re
from pathlib import Path

def fix_type_annotations(file_path):
    """修正單個檔案的類型註解"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修正 Type | None 為 Optional[Type]
        # 匹配模式：word | None
        pattern = r'(\w+(?:\[[\w\s,\[\]]+\])?)\s*\|\s*None'
        
        def replace_func(match):
            type_part = match.group(1)
            return f'Optional[{type_part}]'
        
        content = re.sub(pattern, replace_func, content)
        
        # 確保有 Optional import
        if 'Optional[' in content and 'from typing import' in content:
            # 檢查是否已經有 Optional
            if 'Optional' not in content.split('from typing import')[1].split('\n')[0]:
                # 找到 typing import 行並添加 Optional
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('from typing import'):
                        # 添加 Optional 到 import 中
                        if 'Optional' not in line:
                            line = line.rstrip()
                            if line.endswith(','):
                                lines[i] = line + ' Optional'
                            else:
                                lines[i] = line + ', Optional'
                        break
                content = '\n'.join(lines)
        
        # 只有內容改變時才寫入
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修正: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ 錯誤 {file_path}: {e}")
        return False

def main():
    """主函數"""
    print("🔧 修正 Python 3.9 類型註解相容性問題...")
    
    # 掃描 stock_price_investment_system 目錄
    base_dir = Path("stock_price_investment_system")
    
    if not base_dir.exists():
        print(f"❌ 目錄不存在: {base_dir}")
        return
    
    fixed_count = 0
    total_count = 0
    
    # 遞迴掃描所有 .py 檔案
    for py_file in base_dir.rglob("*.py"):
        total_count += 1
        if fix_type_annotations(py_file):
            fixed_count += 1
    
    print(f"\n📊 修正完成:")
    print(f"   總檔案數: {total_count}")
    print(f"   修正檔案數: {fixed_count}")
    print(f"   未修正檔案數: {total_count - fixed_count}")

if __name__ == "__main__":
    main()
