#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動修復剩餘檔案的重複函數定義問題
"""

import os
import re

def fix_collect_balance_sheets():
    """修復 collect_balance_sheets.py"""
    file_path = "scripts/collect_balance_sheets.py"
    print(f"🔧 修復 {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到重複的舊函數定義並移除
        # 從 "# 全局變數追蹤執行時間" 到 "def init_logging():" 之間的內容
        pattern = r'    # 全局變數追蹤執行時間.*?(?=def init_logging\(\):)'
        
        replacement = '''
def init_logging():'''
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ 已修復 {file_path}")
            return True
        else:
            print(f"⚠️ 無需修改 {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ 修復失敗: {file_path} - {e}")
        return False

def fix_collect_financial_statements():
    """修復 collect_financial_statements.py"""
    file_path = "scripts/collect_financial_statements.py"
    print(f"🔧 修復 {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有重複的函數定義
        if content.count('def wait_for_api_recovery') > 1:
            # 移除舊的函數定義
            lines = content.split('\n')
            new_lines = []
            skip_old_function = False
            
            for line in lines:
                if '# 全局變數追蹤執行時間' in line:
                    skip_old_function = True
                    continue
                elif skip_old_function and line.startswith('def ') and 'wait_for_api_recovery' not in line:
                    skip_old_function = False
                    new_lines.append(line)
                elif not skip_old_function:
                    new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ 已修復 {file_path}")
            return True
        else:
            print(f"⚠️ 無需修改 {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ 修復失敗: {file_path} - {e}")
        return False

def remove_timer_initialization():
    """移除所有檔案中的計時器初始化"""
    files = [
        "scripts/collect_balance_sheets.py",
        "scripts/collect_financial_statements.py",
        "scripts/collect_dividend_data.py"
    ]
    
    for file_path in files:
        print(f"🔧 移除 {file_path} 中的計時器初始化")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除計時器初始化代碼
            patterns = [
                r'# 初始化執行時間計時器.*?(?=\n    [^#\s]|\n\n|\Z)',
                r'.*?\[TIMER\] 初始化執行時間計時器.*?\n',
                r'    try:\s*from scripts\.smart_wait import get_smart_wait_manager.*?(?=\n    [^#\s]|\n\n|\Z)'
            ]
            
            for pattern in patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL)
            
            # 清理多餘的空行
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已移除 {file_path} 中的計時器初始化")
            
        except Exception as e:
            print(f"❌ 處理失敗: {file_path} - {e}")

def test_syntax():
    """測試所有修復後檔案的語法"""
    files = [
        "simple_collect.py",
        "scripts/collect_balance_sheets.py", 
        "scripts/collect_financial_statements.py",
        "scripts/collect_dividend_data.py",
        "scripts/analyze_potential_stocks.py"
    ]
    
    print("\n🧪 測試修復後檔案語法...")
    print("=" * 50)
    
    all_good = True
    for file_path in files:
        if os.path.exists(file_path):
            try:
                import subprocess
                result = subprocess.run([
                    'python', '-m', 'py_compile', file_path
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ {file_path} 語法正確")
                else:
                    print(f"❌ {file_path} 語法錯誤: {result.stderr}")
                    all_good = False
            except Exception as e:
                print(f"❌ 無法測試 {file_path}: {e}")
                all_good = False
        else:
            print(f"⚠️ 檔案不存在: {file_path}")
    
    return all_good

def main():
    """主函數"""
    print("🚀 手動修復剩餘檔案問題")
    print("=" * 60)
    
    success_count = 0
    
    # 修復重複函數定義
    if fix_collect_balance_sheets():
        success_count += 1
    
    if fix_collect_financial_statements():
        success_count += 1
    
    # 移除計時器初始化
    remove_timer_initialization()
    
    # 測試語法
    syntax_ok = test_syntax()
    
    print("\n" + "=" * 60)
    print("📊 修復結果總結")
    print("=" * 60)
    
    if syntax_ok:
        print("🎉 所有檔案修復完成且語法正確！")
        
        print("\n📖 最終修復效果:")
        print("=" * 40)
        print("✅ 完全移除:")
        print("   - [TIMER] 初始化執行時間計時器 訊息")
        print("   - 智能時間等待邏輯（70分鐘等待）")
        print("   - 複雜的執行時間計算")
        print("   - 重複的函數定義")
        print()
        print("✅ 新的API等待邏輯:")
        print("   - 遇到402錯誤時才開始檢查")
        print("   - 每5分鐘測試一次API狀態")
        print("   - 直接向FinMind發送測試請求")
        print("   - 確認API恢復正常才繼續執行")
        print()
        print("✅ 改進效果:")
        print("   - 啟動時不會顯示計時器訊息")
        print("   - 更快的API恢復檢測")
        print("   - 更準確的狀態判斷")
        print("   - 簡化的錯誤處理邏輯")
        
    else:
        print("❌ 部分檔案仍有語法問題，請檢查錯誤訊息")
    
    return syntax_ok

if __name__ == "__main__":
    main()
