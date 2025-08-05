#!/usr/bin/env python3
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
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager

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
            print(f"\r   剩餘 {remaining} 分鐘...", end="", flush=True)
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
    
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        if args.stock_id:
            # 指定個股
            cursor.execute("""
                SELECT stock_id, stock_name
                FROM stocks
                WHERE stock_id = ?
            """, (args.stock_id,))
            stock_list = [{'stock_id': row[0], 'stock_name': row[1]} for row in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT stock_id, stock_name
                FROM stocks
                WHERE is_etf = 0
                AND LENGTH(stock_id) = 4
                AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
                AND market IN ('TWSE', 'TPEx')
                ORDER BY stock_id
            """)
            stock_list = [{'stock_id': row[0], 'stock_name': row[1]} for row in cursor.fetchall()]

        conn.close()

        if args.test and not args.stock_id:
            stock_list = stock_list[:5]
            print("測試模式：只收集前5檔股票")

        if not stock_list:
            if args.stock_id:
                print(f"找不到股票代碼: {args.stock_id}")
            else:
                print("未找到股票資料")
            return
        
        print(f"找到 {len(stock_list)} 檔股票")
        
        if args.stock_id:
            print(f"個股模式：收集 {args.stock_id}")
        
        print(f"資料收集日期範圍: {args.start_date} ~ {args.end_date}")
        
        # 收集股利政策資料
        success_count = 0
        total_records = 0
        
        for i, stock in enumerate(stock_list, 1):
            stock_id = stock['stock_id']
            stock_name = stock['stock_name']
            print(f"\n[{i}/{len(stock_list)}] {stock_id} ({stock_name})")
            
            try:
                # 收集股利政策資料
                url = "https://api.finmindtrade.com/api/v4/data"
                params = {
                    "dataset": "TaiwanStockDividend",
                    "data_id": stock_id,
                    "start_date": args.start_date,
                    "end_date": args.end_date,
                    "token": Config.FINMIND_API_TOKEN
                }
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        records = len(data['data'])
                        print(f"  成功: {records} 筆資料")
                        success_count += 1
                        total_records += records
                    else:
                        print(f"  無資料")
                elif response.status_code == 402:
                    print(f"  遇到API限制，開始檢查恢復狀態...")
                    if is_api_limit_error(str(response.status_code)):
                        wait_for_api_recovery(stock_id, "TaiwanStockDividend")
                        # 重試
                        response = requests.get(url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('data'):
                                records = len(data['data'])
                                print(f"  成功: {records} 筆資料")
                                success_count += 1
                                total_records += records
                            else:
                                print(f"  無資料")
                        else:
                            print(f"  重試失敗: HTTP {response.status_code}")
                else:
                    print(f"  失敗: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  錯誤: {e}")
        
        print(f"\n收集完成: 成功 {success_count}, 總筆數 {total_records}")
        print("✅ 股利政策資料收集完成")
        
    except Exception as e:
        print(f"執行錯誤: {e}")

if __name__ == "__main__":
    main()
