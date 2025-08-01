#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 Windows cp950 編碼問題 - 移除 emoji 字符
"""

import re

def fix_emoji_in_file(file_path):
    """修復檔案中的 emoji 編碼問題"""
    
    # emoji 替換對應表
    emoji_replacements = {
        '🎯': '[TARGET]',
        '📊': '[CHART]',
        '⚠️': '[WARNING]',
        '❌': '[ERROR]',
        '✅': '[OK]',
        '📈': '[UP]',
        '📉': '[DOWN]',
        '💾': '[SAVE]',
        '🔄': '[REFRESH]',
        '📋': '[LIST]',
        '🛠️': '[TOOL]',
        '🚀': '[ROCKET]',
        '🎉': '[PARTY]',
        '⚡': '[FAST]',
        '🔍': '[SEARCH]'
    }
    
    try:
        # 讀取檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替換 emoji
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # 寫回檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 修復完成: {file_path}")
        
    except Exception as e:
        print(f"✗ 修復失敗: {file_path}, 錯誤: {e}")

if __name__ == "__main__":
    # 修復主要檔案
    files_to_fix = [
        "potential_stock_predictor/backtesting_system.py"
    ]
    
    for file_path in files_to_fix:
        fix_emoji_in_file(file_path)
    
    print("\n所有檔案修復完成！")
