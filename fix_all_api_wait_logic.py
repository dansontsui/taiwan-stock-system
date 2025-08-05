#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修改所有檔案的API等待邏輯
移除智能時間等待，改為每5分鐘檢查API狀態
"""

import os
import re
from pathlib import Path

# 需要修改的檔案列表
FILES_TO_FIX = [
    "scripts/collect_balance_sheets.py",
    "scripts/collect_financial_statements.py", 
    "scripts/analyze_potential_stocks.py"
]

# 新的API等待函數
NEW_API_WAIT_FUNCTION = '''# 簡化的API狀態檢查
def is_api_limit_error(error_msg):
    """檢查是否為API限制錯誤"""
    api_limit_keywords = ["402", "Payment Required", "API請求限制", "rate limit", "quota exceeded"]
    return any(keyword.lower() in error_msg.lower() for keyword in api_limit_keywords)

def wait_for_api_recovery(stock_id="2330", dataset="TaiwanStockPrice"):
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
        print()  # 換行'''

def fix_file(file_path):
    """修復單個檔案"""
    print(f"🔧 修復檔案: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. 移除智能等待模組導入
        smart_wait_import_pattern = r'# 導入智能等待模組.*?(?=\n\n|\ndef|\nclass|\n#[^#]|\Z)'
        content = re.sub(smart_wait_import_pattern, NEW_API_WAIT_FUNCTION, content, flags=re.DOTALL)
        
        # 2. 替換 smart_wait_for_api_reset() 調用
        content = re.sub(r'smart_wait_for_api_reset\(\)', 'wait_for_api_recovery(stock_id, dataset)', content)
        
        # 3. 移除計時器初始化代碼
        timer_init_pattern = r'# 初始化執行時間計時器.*?(?=\n    # [^初]|\n    [^#]|\n\n|\Z)'
        content = re.sub(timer_init_pattern, '# 不再預先初始化計時器，只在遇到API限制時才開始檢查', content, flags=re.DOTALL)
        
        # 4. 移除 [TIMER] 初始化訊息
        timer_msg_pattern = r'.*?\[TIMER\] 初始化執行時間計時器.*?\n'
        content = re.sub(timer_msg_pattern, '', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修復: {file_path}")
            return True
        else:
            print(f"⚠️ 無需修改: {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ 修復失敗: {file_path} - {e}")
        return False

def main():
    """主函數"""
    print("🚀 批量修復API等待邏輯")
    print("=" * 60)
    print("修改內容:")
    print("1. 移除智能時間等待邏輯")
    print("2. 改為每5分鐘檢查API狀態")
    print("3. 移除開始時的計時器初始化")
    print("4. 只在遇到402錯誤時才開始檢查")
    print("=" * 60)
    
    success_count = 0
    total_count = len(FILES_TO_FIX)
    
    for file_path in FILES_TO_FIX:
        if fix_file(file_path):
            success_count += 1
    
    print("\n" + "=" * 60)
    print("📊 修復結果總結")
    print("=" * 60)
    print(f"成功修復: {success_count}/{total_count} 個檔案")
    
    if success_count == total_count:
        print("🎉 所有檔案修復完成！")
        
        print("\n📖 修復效果:")
        print("=" * 40)
        print("✅ 移除項目:")
        print("   - 智能時間等待邏輯")
        print("   - 70分鐘等待時間")
        print("   - 複雜的執行時間計算")
        print("   - 開始時的計時器初始化")
        print()
        print("✅ 新增項目:")
        print("   - 每5分鐘檢查API狀態")
        print("   - 直接測試API回應")
        print("   - 只在確認恢復後才繼續")
        print("   - 簡化的錯誤處理")
        print()
        print("✅ 改進效果:")
        print("   - 不會在開始時顯示 [TIMER] 訊息")
        print("   - 遇到402錯誤時才開始檢查")
        print("   - 更快恢復執行（不用等70分鐘）")
        print("   - 更準確的API狀態檢測")
        
    else:
        print("❌ 部分檔案修復失敗，請檢查錯誤訊息")
    
    return success_count == total_count

if __name__ == "__main__":
    main()
