#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復腳本中的emoji字符，避免Windows cp950編碼問題
"""

import os
import re

def fix_emoji_in_file(file_path):
    """修復單個檔案中的emoji"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定義emoji替換規則
        emoji_replacements = {
            '📈': '',
            '📊': '',
            '📅': '',
            '🔄': '',
            '✅': '',
            '❌': '',
            '⚠️': '',
            '⏰': '',
            '⏳': '',
            '🚀': '',
            '💾': '',
            '🧪': '',
            '⏸️': '',
            '🎯': '',
            '💰': '',
            '🏢': '',
            '🔍': '',
            '📋': '',
            '📌': '',
            '🎉': '',
            '💡': '',
            '🔥': '',
            '📝': '',
            '🎨': '',
            '⚙️': '',
            '🌟': '',
            '🎪': '',
            '🎭': '',
            '🎬': '',
            '🎮': '',
            '🎯': '',
            '🎲': '',
            '🎳': '',
            '🎴': '',
            '🎵': '',
            '🎶': '',
            '🎷': '',
            '🎸': '',
            '🎹': '',
            '🎺': '',
            '🎻': '',
            '🎼': '',
            '🎽': '',
            '🎾': '',
            '🎿': '',
            '🏀': '',
            '🏁': '',
            '🏂': '',
            '🏃': '',
            '🏄': '',
            '🏅': '',
            '🏆': '',
            '🏇': '',
            '🏈': '',
            '🏉': '',
            '🏊': '',
            '🏋': '',
            '🏌': '',
            '🏍': '',
            '🏎': '',
            '🏏': '',
            '🏐': '',
            '🏑': '',
            '🏒': '',
            '🏓': '',
            '🏔': '',
            '🏕': '',
            '🏖': '',
            '🏗': '',
            '🏘': '',
            '🏙': '',
            '🏚': '',
            '🏛': '',
            '🏜': '',
            '🏝': '',
            '🏞': '',
            '🏟': '',
            '🏠': '',
            '🏡': '',
            '🏢': '',
            '🏣': '',
            '🏤': '',
            '🏥': '',
            '🏦': '',
            '🏧': '',
            '🏨': '',
            '🏩': '',
            '🏪': '',
            '🏫': '',
            '🏬': '',
            '🏭': '',
            '🏮': '',
            '🏯': '',
            '🏰': '',
        }
        
        # 替換emoji
        modified = False
        for emoji, replacement in emoji_replacements.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                modified = True
        
        # 如果有修改，寫回檔案
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"修復了 {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"修復 {file_path} 時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("開始修復腳本中的emoji字符...")
    
    # 需要修復的腳本檔案
    script_files = [
        'scripts/collect_stock_prices_smart.py',
        'scripts/collect_monthly_revenue.py',
        'scripts/collect_financial_statements.py',
        'scripts/collect_balance_sheets.py',
        'scripts/collect_dividend_data.py',
        'scripts/analyze_potential_stocks.py',
        'scripts/calculate_revenue_growth.py',
        'scripts/collect_all_10years.py',
        'scripts/collect_daily_update.py',
        'scripts/collect_batch.py',
        'scripts/menu.py'
    ]
    
    fixed_count = 0
    
    for script_file in script_files:
        if os.path.exists(script_file):
            if fix_emoji_in_file(script_file):
                fixed_count += 1
        else:
            print(f"檔案不存在: {script_file}")
    
    print(f"修復完成！共修復了 {fixed_count} 個檔案")

if __name__ == "__main__":
    main()
