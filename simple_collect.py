#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版資料收集腳本 - 避免編碼問題，支援斷點續傳
"""

import sys
import os
import time
import requests
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 導入簡單進度記錄系統
try:
    from scripts.simple_progress import SimpleProgress
    PROGRESS_ENABLED = True
except ImportError:
    print("[WARNING] 無法導入簡單進度記錄系統，進度記錄功能將被停用")
    PROGRESS_ENABLED = False

# 簡化的API狀態檢查
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
            print(f"\r   剩餘 {remaining} 分鐘...", end="", flush=True)
            time.sleep(60)
        print()  # 換行

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

        # 如果是股價資料，暫時改為昨天開始以減少資料量
        actual_start_date = start_date
        if dataset in ["TaiwanStockPrice", "price"]:
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            actual_start_date = yesterday
            print(f"  📊 股價資料：調整起始日期為 {actual_start_date} (減少資料量)")

        params = {
            "dataset": dataset,
            "data_id": stock_id,
            "start_date": actual_start_date,
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
                wait_for_api_recovery(stock_id, dataset)

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
            wait_for_api_recovery(stock_id, dataset)
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

def collect_all_data(test_mode=False, stock_id=None, start_date=None, end_date=None, resume_mode=False):
    """收集所有資料 - 支援簡單續傳"""

    print("=" * 60)
    if stock_id:
        print(f"簡化版資料收集 - 個股 {stock_id}")
    elif resume_mode:
        print(f"簡化版資料收集 - 續傳模式")
    else:
        print("簡化版資料收集")
    print("=" * 60)

    # 初始化簡單進度記錄系統
    progress = None

    if PROGRESS_ENABLED:
        try:
            progress = SimpleProgress()
            print("✅ 簡單進度記錄系統初始化成功")

            # 顯示當前進度摘要
            if resume_mode:
                progress.show_progress_summary()

        except Exception as e:
            print(f"⚠️ 進度記錄系統初始化失敗: {e}")
            print("📝 將跳過進度記錄，但繼續執行主要功能")
            progress = None

    # 不再預先初始化計時器，只在遇到API限制時才開始計時

    # 獲取股票清單
    if stock_id:
        all_stocks = get_stock_list(stock_id=stock_id)
    else:
        limit = 3 if test_mode else None
        all_stocks = get_stock_list(limit)

    if not all_stocks:
        if stock_id:
            print(f"找不到股票代碼: {stock_id}")
        else:
            print("沒有找到股票")
        return

    # 準備股票清單格式（包含股票名稱）
    stocks_with_names = []
    for stock in all_stocks:
        if isinstance(stock, dict):
            stocks_with_names.append(stock)
        else:
            # 如果是字串，轉換為字典格式
            stocks_with_names.append({'stock_id': stock, 'stock_name': stock})

    # 找到續傳位置
    start_index = 0
    if progress and resume_mode:
        start_index = progress.find_resume_position(stocks_with_names)
        if start_index >= len(stocks_with_names):
            print("所有股票都已完成")
            return

    # 要處理的股票清單
    stocks = stocks_with_names[start_index:]

    print(f"找到 {len(stocks_with_names)} 檔股票")
    if resume_mode and start_index > 0:
        print(f"續傳模式：從第 {start_index + 1} 檔開始，處理 {len(stocks)} 檔股票")
    elif stock_id:
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
        from datetime import datetime
        start_date = "2010-01-01"  # 固定起始日期，避免資料遺失

    if end_date is None:
        from datetime import datetime
        end_date = datetime.now().date().isoformat()

    print(f"資料收集日期範圍: {start_date} ~ {end_date}")

    # 不再需要創建複雜的任務ID，簡單進度系統會自動記錄

    total_stats = {}
    
    for dataset, (name, save_func) in datasets.items():
        print(f"\n收集 {name} 資料...")
        print("-" * 40)

        dataset_stats = {"success": 0, "failed": 0, "saved": 0}

        for i, stock in enumerate(stocks, 1):
            stock_id_val = stock['stock_id']
            stock_name = stock['stock_name']

            print(f"[{i}/{len(stocks)}] {stock_id_val} ({stock_name})")

            try:
                # 收集資料
                df = collect_stock_data(stock_id_val, dataset, start_date, end_date)

                if df is not None and not df.empty:
                    # 儲存資料
                    saved_count = save_func(df, stock_id_val)
                    dataset_stats["success"] += 1
                    dataset_stats["saved"] += saved_count
                    print(f"  成功: {len(df)} 筆資料，儲存 {saved_count} 筆")

                    # 簡單進度記錄：記錄當前股票
                    if progress:
                        progress.save_current_stock(stock_id_val, stock_name, len(stocks_with_names), start_index + i)
                else:
                    dataset_stats["failed"] += 1
                    print(f"  無資料")

                    # 簡單進度記錄：記錄當前股票
                    if progress:
                        progress.save_current_stock(stock_id_val, stock_name, len(stocks_with_names), start_index + i)

                # 控制請求頻率
                time.sleep(0.5)

            except KeyboardInterrupt:
                print(f"\n⚠️ 使用者中斷執行，{name} 資料收集已處理 {i}/{len(stocks)} 檔股票")

                # 記錄中斷的股票為失敗
                if progress:
                    progress.add_failed_stock(stock_id_val, stock_name, "使用者中斷執行")

                raise  # 重新拋出中斷信號
            except Exception as e:
                dataset_stats["failed"] += 1
                error_msg = str(e)
                print(f"  失敗: {error_msg}")

                # 記錄失敗的股票
                if progress:
                    progress.add_failed_stock(stock_id_val, stock_name, error_msg)

                time.sleep(1)

        total_stats[name] = dataset_stats
        print(f"{name} 完成: 成功 {dataset_stats['success']}, 失敗 {dataset_stats['failed']}, 儲存 {dataset_stats['saved']} 筆")

    # 記錄成功完成的股票
    if progress:
        print(f"\n📝 更新股票完成狀態...")
        for stock in stocks:
            stock_id_val = stock['stock_id']
            stock_name = stock.get('stock_name', '')

            # 檢查是否有成功收集的資料
            has_success = any(stats['success'] > 0 for stats in total_stats.values())

            if has_success:
                # 記錄為已完成
                completed_datasets = [name for name, stats in total_stats.items() if stats['success'] > 0]
                progress.add_completed_stock(stock_id_val, stock_name, completed_datasets)

        print(f"✅ 進度記錄已更新")

    # 總結
    print("\n" + "=" * 60)
    print("收集完成")
    print("=" * 60)

    for name, stats in total_stats.items():
        print(f"{name}: 成功 {stats['success']}, 失敗 {stats['failed']}, 儲存 {stats['saved']} 筆")

    # 顯示進度資訊
    if progress:
        print(f"\n📊 進度統計:")
        progress.show_progress_summary()

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='簡化版資料收集 - 支援斷點續傳')
    parser.add_argument('--test', action='store_true', help='測試模式')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--resume', action='store_true', help='續傳模式')
    parser.add_argument('--list-tasks', action='store_true', help='列出所有任務')

    args = parser.parse_args()

    # 顯示進度摘要
    if args.list_tasks:
        if PROGRESS_ENABLED:
            progress = SimpleProgress()
            progress.show_progress_summary()
        else:
            print("❌ 進度記錄功能未啟用")
        return

    try:
        collect_all_data(
            test_mode=args.test,
            stock_id=args.stock_id,
            start_date=args.start_date,
            end_date=args.end_date,
            resume_mode=args.resume
        )
    except KeyboardInterrupt:
        print(f"\n⚠️ 簡化版資料收集已被使用者中斷")
        sys.exit(0)  # 正常退出，不是錯誤

if __name__ == "__main__":
    main()
