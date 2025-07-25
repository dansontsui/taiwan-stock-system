#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速移除腳本中的emoji字符
"""

import re
import os

def remove_emojis_from_file(file_path):
    """移除檔案中的emoji字符"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定義emoji替換規則
        emoji_replacements = {
            '❌ ': '',
            '✅ ': '',
            '💰 ': '',
            '🎯 ': '',
            '📊 ': '',
            '📈 ': '',
            '📅 ': '',
            '🔢 ': '',
            '🎉 ': '',
            '💡 ': '',
            '⏰ ': '',
            '⏳ ': '',
            '🧪 ': '',
            '🔄 ': '',
            '📋 ': '',
            '📂 ': '',
            '📄 ': '',
            '🔧 ': '',
            '🔍 ': '',
            '⚠️ ': '',
            '🚀 ': '',
            '💎 ': '',
            '🎊 ': '',
            '🔥 ': '',
            '⭐ ': '',
            '🌟 ': '',
            '🎈 ': '',
            '🎁 ': '',
            '🏆 ': '',
            '🎖️ ': '',
            '🥇 ': '',
            '🥈 ': '',
            '🥉 ': '',
            '🏅 ': '',
            '🎪 ': '',
            '🎭 ': '',
            '🎨 ': '',
            '🎬 ': '',
            '🎤 ': '',
            '🎧 ': '',
            '🎼 ': '',
            '🎵 ': '',
            '🎶 ': '',
            '🎸 ': '',
            '🎹 ': '',
            '🎺 ': '',
            '🎻 ': '',
            '🥁 ': '',
            '🎲 ': '',
            '🎯 ': '',
            '🎳 ': '',
            '🎮 ': '',
            '🕹️ ': '',
            '🎰 ': '',
            '🃏 ': '',
            '🀄 ': '',
            '🎴 ': '',
        }
        
        # 執行替換
        modified = False
        for emoji, replacement in emoji_replacements.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                modified = True
                print(f"  移除: {emoji}")
        
        # 移除其他Unicode emoji (範圍更廣)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        new_content = emoji_pattern.sub('', content)
        if new_content != content:
            content = new_content
            modified = True
            print(f"  移除其他emoji字符")
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 已更新: {file_path}")
            return True
        else:
            print(f"- 無需更新: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ 處理失敗 {file_path}: {e}")
        return False

def main():
    """主函數"""
    print("移除腳本中的emoji字符")
    print("=" * 50)
    
    # 要處理的檔案
    files_to_process = [
        'scripts/collect_cash_flows.py',
        'scripts/collect_dividend_results.py'
    ]
    
    updated_count = 0
    
    for file_path in files_to_process:
        if os.path.exists(file_path):
            print(f"\n處理: {file_path}")
            if remove_emojis_from_file(file_path):
                updated_count += 1
        else:
            print(f"✗ 檔案不存在: {file_path}")
    
    print(f"\n=" * 50)
    print(f"處理完成，更新了 {updated_count} 個檔案")

if __name__ == "__main__":
    main()
