#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版資料收集腳本 - 避免編碼問題
"""

import sys
import os
import time
import requests
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 導入智能等待模組
try:
    from scripts.smart_wait import reset_execution_timer, smart_wait_for_api_reset, is_api_limit_error
except ImportError:
    # 如果無法導入，使用本地版本
    print("[WARNING] 無法導入智能等待模組，使用本地版本")

    # 全局變數追蹤執行時間
    execution_start_time = None

    def reset_execution_timer():
        global execution_start_time
        execution_start_time = datetime.now()
        print(f"[TIMER] 重置執行時間計時器: {execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def smart_wait_for_api_reset():
        global execution_start_time
        total_wait_minutes = 70
        executed_minutes = 0

        if execution_start_time:
            elapsed = datetime.now() - execution_start_time
            executed_minutes = elapsed.total_seconds() / 60

        remaining_wait_minutes = max(0, total_wait_minutes - executed_minutes)

        print(f"\n🚫 API請求限制已達上限")
        print("=" * 60)
        print(f"📊 執行統計:")
        print(f"   總執行時間: {executed_minutes:.1f} 分鐘")
        print(f"   API重置週期: {total_wait_minutes} 分鐘")
        print(f"   需要等待: {remaining_wait_minutes:.1f} 分鐘")
        print("=" * 60)

        if remaining_wait_minutes <= 0:
            print("✅ 已超過API重置週期，立即重置計時器並繼續")
            reset_execution_timer()
            return

        print(f"⏳ 智能等待 {remaining_wait_minutes:.1f} 分鐘...")
        total_wait_seconds = int(remaining_wait_minutes * 60)

        if total_wait_seconds > 0:
            for remaining in range(total_wait_seconds, 0, -60):
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                current_time = datetime.now().strftime("%H:%M:%S")
                progress = ((total_wait_seconds - remaining) / total_wait_seconds) * 100

                print(f"\r⏰ [{current_time}] 剩餘: {hours:02d}:{minutes:02d}:00 | 進度: {progress:.1f}%", end="", flush=True)
                time.sleep(60)

        print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] 智能等待完成，重置計時器並繼續收集...")
        print("=" * 60)
        reset_execution_timer()

    def is_api_limit_error(error_msg):
        api_limit_keywords = ["402", "Payment Required", "API請求限制", "rate limit", "quota exceeded"]
        return any(keyword.lower() in error_msg.lower() for keyword in api_limit_keywords)

# 配置
DATABASE_PATH = "data/taiwan_stock.db"
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wNy0yMyAyMDo1MzowNyIsInVzZXJfaWQiOiJkYW5zb24udHN1aSIsImlwIjoiMTIyLjExNi4xNzQuNyJ9.YkvySt5dqxDg_4NHsJzcmmH1trIQUBOy_wHJkR9Ibmk"

def get_stock_list(limit=None, stock_id=None):
    """獲取股票清單"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        if stock_id:
            # 指定個股
            query = """
            SELECT stock_id, stock_name
            FROM stocks
            WHERE stock_id = ?
            """
            cursor.execute(query, (stock_id,))
        else:
            # 所有股票
            query = """
            SELECT stock_id, stock_name
            FROM stocks
            WHERE LENGTH(stock_id) = 4
            AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
            AND stock_id NOT LIKE '00%'
            ORDER BY stock_id
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)

        stocks = cursor.fetchall()
        conn.close()

        return [{'stock_id': row[0], 'stock_name': row[1]} for row in stocks]

    except Exception as e:
        print(f"獲取股票清單失敗: {e}")
        return []

def collect_stock_data(stock_id, dataset, start_date, end_date, retry_count=0):
    """收集單一股票的資料 - 支援智能等待"""
    max_retries = 3

    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": dataset,
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": API_TOKEN
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return pd.DataFrame(data['data'])
            return None

        elif response.status_code == 402:
            # API請求限制，使用智能等待
            error_msg = f"402 Payment Required for {dataset} {stock_id}"
            print(f"收集 {stock_id} {dataset} 遇到API限制: {error_msg}")

            if is_api_limit_error(error_msg):
                smart_wait_for_api_reset()

                # 重試
                if retry_count < max_retries:
                    print(f"重試收集 {stock_id} {dataset} (第 {retry_count + 1} 次)")
                    return collect_stock_data(stock_id, dataset, start_date, end_date, retry_count + 1)
                else:
                    print(f"收集 {stock_id} {dataset} 達到最大重試次數")
                    return None
            else:
                print(f"收集 {stock_id} {dataset} 失敗: HTTP {response.status_code}")
                return None

        else:
            print(f"收集 {stock_id} {dataset} 失敗: HTTP {response.status_code}")
            return None

    except Exception as e:
        error_msg = str(e)
        print(f"收集 {stock_id} {dataset} 失敗: {e}")

        # 檢查是否為API限制相關錯誤
        if is_api_limit_error(error_msg) and retry_count < max_retries:
            smart_wait_for_api_reset()
            print(f"重試收集 {stock_id} {dataset} (第 {retry_count + 1} 次)")
            return collect_stock_data(stock_id, dataset, start_date, end_date, retry_count + 1)

        return None

def save_stock_prices(df, stock_id):
    """儲存股價資料"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO stock_prices 
                    (stock_id, date, open_price, high_price, low_price, close_price, 
                     volume, trading_money, trading_turnover, spread, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row['open'],
                    row['max'],
                    row['min'],
                    row['close'],
                    row['Trading_Volume'],
                    row['Trading_money'],
                    row['Trading_turnover'],
                    row['spread'],
                    datetime.now().isoformat()
                ))
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存股價失敗: {e}")
        return 0

def save_monthly_revenue(df, stock_id):
    """儲存月營收資料"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO monthly_revenues 
                    (stock_id, date, country, revenue, revenue_month, revenue_year, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row.get('country', 'Taiwan'),
                    row['revenue'],
                    row['revenue_month'],
                    row['revenue_year'],
                    datetime.now().isoformat()
                ))
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存月營收失敗: {e}")
        return 0

def save_cash_flow(df, stock_id):
    """儲存現金流資料"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO cash_flow_statements 
                    (stock_id, date, type, value, origin_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row['type'],
                    row['value'],
                    row.get('origin_name', ''),
                    datetime.now().isoformat()
                ))
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        return saved
        
    except Exception as e:
        print(f"儲存現金流失敗: {e}")
        return 0

def collect_all_data(test_mode=False, stock_id=None, start_date=None, end_date=None):
    """收集所有資料"""

    print("=" * 60)
    if stock_id:
        print(f"簡化版資料收集 - 個股 {stock_id}")
    else:
        print("簡化版資料收集")
    print("=" * 60)

    # 重置執行時間計時器
    reset_execution_timer()

    # 獲取股票清單
    if stock_id:
        stocks = get_stock_list(stock_id=stock_id)
    else:
        limit = 3 if test_mode else None
        stocks = get_stock_list(limit)

    if not stocks:
        if stock_id:
            print(f"找不到股票代碼: {stock_id}")
        else:
            print("沒有找到股票")
        return

    print(f"找到 {len(stocks)} 檔股票")
    if stock_id:
        print(f"個股模式：收集 {stock_id}")
    elif test_mode:
        print("測試模式：只收集前3檔")
    
    # 資料集定義
    datasets = {
        "TaiwanStockPrice": ("股價", save_stock_prices),
        "TaiwanStockMonthRevenue": ("月營收", save_monthly_revenue),
        "TaiwanStockCashFlowsStatement": ("現金流", save_cash_flow)
    }
    
    # 設定日期範圍
    if start_date is None:
        from datetime import datetime, timedelta
        end_date_obj = datetime.now().date()
        start_date_obj = end_date_obj - timedelta(days=10*365)  # 預設10年
        start_date = start_date_obj.isoformat()

    if end_date is None:
        from datetime import datetime
        end_date = datetime.now().date().isoformat()

    print(f"資料收集日期範圍: {start_date} ~ {end_date}")
    
    total_stats = {}
    
    for dataset, (name, save_func) in datasets.items():
        print(f"\n收集 {name} 資料...")
        print("-" * 40)
        
        dataset_stats = {"success": 0, "failed": 0, "saved": 0}
        
        for i, stock in enumerate(stocks, 1):
            stock_id = stock['stock_id']
            stock_name = stock['stock_name']
            
            print(f"[{i}/{len(stocks)}] {stock_id} ({stock_name})")
            
            try:
                # 收集資料
                df = collect_stock_data(stock_id, dataset, start_date, end_date)
                
                if df is not None and not df.empty:
                    # 儲存資料
                    saved_count = save_func(df, stock_id)
                    dataset_stats["success"] += 1
                    dataset_stats["saved"] += saved_count
                    print(f"  成功: {len(df)} 筆資料，儲存 {saved_count} 筆")
                else:
                    dataset_stats["failed"] += 1
                    print(f"  無資料")
                
                # 控制請求頻率
                time.sleep(0.5)
                
            except Exception as e:
                dataset_stats["failed"] += 1
                print(f"  失敗: {e}")
                time.sleep(1)
        
        total_stats[name] = dataset_stats
        print(f"{name} 完成: 成功 {dataset_stats['success']}, 失敗 {dataset_stats['failed']}, 儲存 {dataset_stats['saved']} 筆")
    
    # 總結
    print("\n" + "=" * 60)
    print("收集完成")
    print("=" * 60)
    
    for name, stats in total_stats.items():
        print(f"{name}: 成功 {stats['success']}, 失敗 {stats['failed']}, 儲存 {stats['saved']} 筆")

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='簡化版資料收集')
    parser.add_argument('--test', action='store_true', help='測試模式')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')

    args = parser.parse_args()

    collect_all_data(
        test_mode=args.test,
        stock_id=args.stock_id,
        start_date=args.start_date,
        end_date=args.end_date
    )

if __name__ == "__main__":
    main()
