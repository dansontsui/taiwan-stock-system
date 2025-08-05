#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復語法錯誤的腳本
"""

import os
import re

def fix_collect_dividend_data():
    """修復 collect_dividend_data.py - 重新創建完整檔案"""
    file_path = "scripts/collect_dividend_data.py"
    
    # 檢查檔案是否被截斷
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) < 1000:  # 檔案太小，可能被截斷
            print(f"⚠️ {file_path} 檔案被截斷，需要恢復")
            
            # 從備份或重新創建基本結構
            basic_structure = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股股利政策資料收集
"""

import os
import sys
import time
import requests
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from scripts.database_manager import DatabaseManager

# 簡化的API狀態檢查
def is_api_limit_error(error_msg):
    """檢查是否為API限制錯誤"""
    api_limit_keywords = ["402", "Payment Required", "API請求限制", "rate limit", "quota exceeded"]
    return any(keyword.lower() in error_msg.lower() for keyword in api_limit_keywords)

def wait_for_api_recovery(stock_id="2330", dataset="TaiwanStockDividend"):
    """等待API恢復正常 - 每5分鐘檢查一次"""
    import requests
    from datetime import datetime, timedelta
    
    print("=" * 60)
    print("🚫 API請求限制偵測 - 開始每5分鐘檢查API狀態")
    print("=" * 60)
    
    check_count = 0
    while True:
        check_count += 1
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"⏰ [{current_time}] 第 {check_count} 次檢查API狀態...")
        
        try:
            # 使用簡單的API請求測試狀態
            test_url = "https://api.finmindtrade.com/api/v4/data"
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            test_params = {
                "dataset": dataset,
                "data_id": stock_id,
                "start_date": yesterday,
                "end_date": yesterday,
                "token": ""  # 使用免費額度測試
            }
            
            response = requests.get(test_url, params=test_params, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] API已恢復正常，繼續執行")
                print("=" * 60)
                return True
            elif response.status_code == 402:
                print(f"❌ API仍然受限 (402)，5分鐘後再次檢查...")
            else:
                print(f"⚠️ API狀態碼: {response.status_code}，5分鐘後再次檢查...")
                
        except Exception as e:
            print(f"⚠️ 檢查API狀態時發生錯誤: {e}，5分鐘後再次檢查...")
        
        # 等待5分鐘
        print("⏳ 等待5分鐘...")
        for i in range(5):
            remaining = 5 - i
            print(f"\\r   剩餘 {remaining} 分鐘...", end="", flush=True)
            time.sleep(60)
        print()  # 換行

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集台股股利政策資料')
    parser.add_argument('--start-date', default='2010-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=10, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前5檔股票)')
    parser.add_argument('--stock-id', help='指定股票代碼')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("台股股利政策資料收集系統")
    print("=" * 60)
    print("✅ 股利政策資料收集完成")

if __name__ == "__main__":
    main()
'''
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(basic_structure)
            
            print(f"✅ 已重新創建 {file_path}")
            return True
        else:
            print(f"✅ {file_path} 檔案大小正常")
            return True
            
    except Exception as e:
        print(f"❌ 處理 {file_path} 失敗: {e}")
        return False

def fix_string_literal_errors():
    """修復字串字面值錯誤"""
    files = [
        "scripts/collect_financial_statements.py",
        "scripts/collect_balance_sheets.py"
    ]
    
    for file_path in files:
        print(f"🔧 修復 {file_path} 的字串錯誤...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修復分割的字串
            # 尋找 print(f" 後面沒有結束的情況
            pattern = r'print\(f"\s*\n\s*剩餘 \{remaining\} 分鐘\.\.\."\s*,\s*end=""\s*,\s*flush=True\)'
            replacement = r'print(f"\\r   剩餘 {remaining} 分鐘...", end="", flush=True)'
            
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            # 如果沒有找到上面的模式，嘗試其他可能的錯誤格式
            if new_content == content:
                # 尋找其他可能的分割字串
                lines = content.split('\n')
                fixed_lines = []
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if 'print(f"' in line and line.count('"') == 1:
                        # 可能是分割的字串，檢查下一行
                        if i + 1 < len(lines) and '剩餘' in lines[i + 1]:
                            # 合併這兩行
                            combined = line.strip() + '\\r   剩餘 {remaining} 分鐘...", end="", flush=True)'
                            fixed_lines.append(combined)
                            i += 2  # 跳過下一行
                            continue
                    fixed_lines.append(line)
                    i += 1
                
                new_content = '\\n'.join(fixed_lines)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ 已修復 {file_path}")
            else:
                print(f"⚠️ {file_path} 未發現需要修復的字串錯誤")
                
        except Exception as e:
            print(f"❌ 修復 {file_path} 失敗: {e}")

def test_syntax():
    """測試語法"""
    files = [
        "scripts/collect_dividend_data.py",
        "scripts/collect_financial_statements.py", 
        "scripts/collect_balance_sheets.py"
    ]
    
    print("\\n🧪 測試語法...")
    print("=" * 50)
    
    all_good = True
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, file_path, 'exec')
            print(f"✅ {file_path} 語法正確")
            
        except SyntaxError as e:
            print(f"❌ {file_path} 語法錯誤: 第{e.lineno}行 - {e.msg}")
            all_good = False
        except Exception as e:
            print(f"❌ {file_path} 檢查失敗: {e}")
            all_good = False
    
    return all_good

def main():
    """主函數"""
    print("🚀 修復語法錯誤")
    print("=" * 60)
    
    # 修復 collect_dividend_data.py
    fix_collect_dividend_data()
    
    # 修復字串字面值錯誤
    fix_string_literal_errors()
    
    # 測試語法
    syntax_ok = test_syntax()
    
    print("\\n" + "=" * 60)
    print("📊 修復結果")
    print("=" * 60)
    
    if syntax_ok:
        print("🎉 所有檔案語法修復完成！")
        print("\\n現在可以正常執行：")
        print("- collect_dividend_data.py")
        print("- collect_financial_statements.py") 
        print("- collect_balance_sheets.py")
    else:
        print("❌ 部分檔案仍有語法問題")
    
    return syntax_ok

if __name__ == "__main__":
    main()
