#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版資料收集腳本 - 使用簡單進度系統
"""

import os
import sys
import time
import argparse
from datetime import datetime
import pandas as pd

# 設置編碼
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 導入簡單進度記錄系統
try:
    from scripts.simple_progress import SimpleProgress
    PROGRESS_ENABLED = True
except ImportError:
    print("[WARNING] 無法導入簡單進度記錄系統，進度記錄功能將被停用")
    PROGRESS_ENABLED = False

# 導入智能等待模組
try:
    from scripts.smart_wait import reset_execution_timer, smart_wait_for_api_reset, is_api_limit_error
except ImportError:
    print("[WARNING] 無法導入智能等待模組，使用本地版本")
    
    def reset_execution_timer():
        print(f"[TIMER] 重置執行時間計時器: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def smart_wait_for_api_reset():
        print("[WAIT] 等待API重置...")
        time.sleep(60)
    
    def is_api_limit_error(error_msg):
        return "429" in str(error_msg) or "rate limit" in str(error_msg).lower()

# 導入股票清單函數
def get_stock_list(limit=None, stock_id=None):
    """獲取股票清單"""
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path('data/taiwan_stock.db')
        if not db_path.exists():
            print("資料庫檔案不存在")
            return []

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        if stock_id:
            # 查詢特定股票
            cursor.execute("SELECT stock_id, stock_name FROM stocks WHERE stock_id = ?", (stock_id,))
        else:
            # 查詢所有股票
            if limit:
                cursor.execute("SELECT stock_id, stock_name FROM stocks ORDER BY stock_id LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT stock_id, stock_name FROM stocks ORDER BY stock_id")

        results = cursor.fetchall()
        conn.close()

        # 轉換為字典格式
        stocks = [{'stock_id': row[0], 'stock_name': row[1]} for row in results]
        return stocks

    except Exception as e:
        print(f"獲取股票清單失敗: {e}")
        return []

def collect_stock_data(stock_id, dataset, start_date, end_date, retry_count=0):
    """收集單一股票的資料 - 支援智能等待"""
    max_retries = 3

    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        parameter = {
            "dataset": dataset,
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": ""  # 使用免費額度
        }

        import requests
        resp = requests.get(url, params=parameter, timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                df = pd.DataFrame(data['data'])
                return df
            else:
                return None
        else:
            print(f"API請求失敗: {resp.status_code}")
            return None

    except Exception as e:
        error_msg = str(e)
        print(f"收集資料失敗: {error_msg}")

        # 檢查是否為API限制錯誤
        if is_api_limit_error(error_msg) and retry_count < max_retries:
            print(f"[RETRY] API限制，等待後重試 ({retry_count + 1}/{max_retries})")
            smart_wait_for_api_reset()
            return collect_stock_data(stock_id, dataset, start_date, end_date, retry_count + 1)

        return None

# 導入資料儲存函數
def save_stock_prices(df, stock_id):
    """儲存股價資料"""
    try:
        from scripts.data_saver import save_stock_prices as save_func
        return save_func(df, stock_id)
    except Exception as e:
        print(f"儲存股價失敗: {e}")
        return 0

def save_monthly_revenue(df, stock_id):
    """儲存月營收資料"""
    try:
        from scripts.data_saver import save_monthly_revenue as save_func
        return save_func(df, stock_id)
    except Exception as e:
        print(f"儲存月營收失敗: {e}")
        return 0

def save_cash_flow(df, stock_id):
    """儲存現金流資料"""
    try:
        from scripts.data_saver import save_cash_flow as save_func
        return save_func(df, stock_id)
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

    # 初始化執行時間計時器
    reset_execution_timer()

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

    # 設定日期範圍
    if start_date is None:
        start_date = "2010-01-01"  # 固定起始日期，避免資料遺失

    if end_date is None:
        end_date = datetime.now().date().isoformat()

    print(f"資料收集日期範圍: {start_date} ~ {end_date}")

    # 資料集定義
    datasets = {
        "TaiwanStockPrice": ("股價", save_stock_prices),
        "TaiwanStockMonthRevenue": ("月營收", save_monthly_revenue),
        "TaiwanStockCashFlowsStatement": ("現金流", save_cash_flow)
    }

    total_stats = {}
    
    for dataset, (name, save_func) in datasets.items():
        print(f"\n收集 {name} 資料...")
        print("-" * 40)
        
        dataset_stats = {"success": 0, "failed": 0, "saved": 0}
        
        for i, stock in enumerate(stocks, 1):
            stock_id_val = stock['stock_id']
            stock_name = stock.get('stock_name', '')
            current_index = start_index + i
            
            try:
                print(f"[{current_index}/{len(stocks_with_names)}] {stock_id_val} ({stock_name})")
                
                # 記錄當前處理的股票
                if progress:
                    progress.save_current_stock(stock_id_val, stock_name, len(stocks_with_names), current_index)
                
                df = collect_stock_data(stock_id_val, dataset, start_date, end_date)

                if df is not None and not df.empty:
                    # 儲存資料
                    saved_count = save_func(df, stock_id_val)
                    dataset_stats["success"] += 1
                    dataset_stats["saved"] += saved_count
                    print(f"  成功: {len(df)} 筆資料，儲存 {saved_count} 筆")
                else:
                    dataset_stats["failed"] += 1
                    print(f"  無資料")

                # 控制請求頻率
                time.sleep(0.5)

            except KeyboardInterrupt:
                print(f"\n⚠️ 使用者中斷執行，{name} 資料收集已處理 {i}/{len(stocks)} 檔股票")
                
                # 記錄為失敗
                if progress:
                    progress.add_failed_stock(stock_id_val, stock_name, "使用者中斷執行")

                raise  # 重新拋出中斷信號
            except Exception as e:
                dataset_stats["failed"] += 1
                error_msg = str(e)
                print(f"  失敗: {error_msg}")

                # 記錄為失敗
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
    parser = argparse.ArgumentParser(description='簡化版台股資料收集')
    parser.add_argument('--start-date', default='2010-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前3檔股票)')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--resume', action='store_true', help='續傳模式')
    parser.add_argument('--show-progress', action='store_true', help='顯示進度摘要')

    args = parser.parse_args()

    # 顯示進度摘要
    if args.show_progress:
        if PROGRESS_ENABLED:
            progress = SimpleProgress()
            progress.show_progress_summary()
        else:
            print("❌ 進度記錄功能未啟用")
        return

    # 執行資料收集
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
