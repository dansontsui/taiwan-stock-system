#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收集10檔精選股票的10年資料 - 包含智能等待功能
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from app.services.data_collector import FinMindDataCollector
from loguru import logger

# 精選10檔股票
SELECTED_STOCKS = [
    {'stock_id': '2330', 'stock_name': '台積電', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2317', 'stock_name': '鴻海', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2454', 'stock_name': '聯發科', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2412', 'stock_name': '中華電', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2882', 'stock_name': '國泰金', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2891', 'stock_name': '中信金', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2303', 'stock_name': '聯電', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '2002', 'stock_name': '中鋼', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '1301', 'stock_name': '台塑', 'market': 'TWSE', 'is_etf': False},
    {'stock_id': '0050', 'stock_name': '元大台灣50', 'market': 'TWSE', 'is_etf': True},
]

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'collect_10_stocks_10years.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def wait_for_api_reset():
    """智能等待API限制重置 - 70分鐘"""
    wait_minutes = 70
    print(f"\nAPI請求限制已達上限，智能等待 {wait_minutes} 分鐘...")
    print("=" * 60)

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=wait_minutes)

    print(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"預計結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    logger.info(f"開始智能等待 {wait_minutes} 分鐘，預計 {end_time.strftime('%Y-%m-%d %H:%M:%S')} 完成")

    for remaining in range(wait_minutes * 60, 0, -60):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        current_time = datetime.now().strftime("%H:%M:%S")
        progress = ((wait_minutes * 60 - remaining) / (wait_minutes * 60)) * 100

        print(f"\r[{current_time}] 剩餘: {hours:02d}:{minutes:02d}:00 | 進度: {progress:.1f}%", end="", flush=True)
        time.sleep(60)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待完成，繼續收集資料...")
    print("=" * 60)
    logger.info("智能等待完成，繼續收集資料")

def check_existing_data(db_manager, stock_id, start_date, end_date):
    """檢查已存在的資料"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM stock_prices 
            WHERE stock_id = ? AND date BETWEEN ? AND ?
        """, (stock_id, start_date, end_date))
        
        existing_count = cursor.fetchone()[0]
        
        # 計算預期的交易日數量（大約每年250個交易日）
        years = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days / 365
        expected_count = int(years * 250)
        
        completion_rate = (existing_count / expected_count) * 100 if expected_count > 0 else 0
        
        return existing_count, expected_count, completion_rate
        
    except Exception as e:
        logger.error(f"檢查 {stock_id} 現有資料失敗: {e}")
        return 0, 0, 0
    finally:
        conn.close()

def save_stock_prices(db_manager, stock_id, data):
    """儲存股價資料"""
    if not data:
        return 0

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        saved_count = 0
        for record in data:
            # 適應清理後的資料格式
            cursor.execute("""
                INSERT OR REPLACE INTO stock_prices
                (stock_id, date, open_price, high_price, low_price, close_price, volume, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stock_id,
                record.get('date'),
                record.get('open_price', record.get('open')),
                record.get('high_price', record.get('max')),
                record.get('low_price', record.get('min')),
                record.get('close_price', record.get('close')),
                record.get('volume', record.get('Trading_Volume')),
                datetime.now()
            ))
            saved_count += 1

        conn.commit()
        return saved_count

    except Exception as e:
        logger.error(f"儲存 {stock_id} 股價資料失敗: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def save_cash_flow_data(db_manager, data, stock_id):
    """儲存現金流量表資料"""
    if not data:
        return 0

    conn = db_manager.get_connection()
    cursor = conn.cursor()
    saved_count = 0

    try:
        for record in data:
            cursor.execute("""
                INSERT OR REPLACE INTO cash_flow_statements
                (stock_id, date, type, value, origin_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record['stock_id'],
                record['date'],
                record['type'],
                record['value'],
                record.get('origin_name', ''),
                datetime.now()
            ))
            saved_count += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"儲存現金流量資料失敗: {e}")
        saved_count = 0
    finally:
        conn.close()

    return saved_count

def save_dividend_result_data(db_manager, data, stock_id):
    """儲存除權除息結果資料"""
    if not data:
        return 0

    conn = db_manager.get_connection()
    cursor = conn.cursor()
    saved_count = 0

    try:
        for record in data:
            cursor.execute("""
                INSERT OR REPLACE INTO dividend_results
                (stock_id, date, before_price, after_price,
                 stock_and_cache_dividend, stock_or_cache_dividend,
                 max_price, min_price, open_price, reference_price, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['stock_id'],
                record['date'],
                record.get('before_price', None),
                record.get('after_price', None),
                record.get('stock_and_cache_dividend', None),
                record.get('stock_or_cache_dividend', ''),
                record.get('max_price', None),
                record.get('min_price', None),
                record.get('open_price', None),
                record.get('reference_price', None),
                datetime.now()
            ))
            saved_count += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"儲存除權除息結果資料失敗: {e}")
        saved_count = 0
    finally:
        conn.close()

    return saved_count

def collect_stock_data_with_retry(db_manager, finmind_collector, stock_info, start_date, end_date, max_retries=3):
    """收集單一股票資料，支援重試和智能等待"""
    stock_id = stock_info['stock_id']
    stock_name = stock_info['stock_name']

    # 檢查現有資料
    existing_count, expected_count, completion_rate = check_existing_data(db_manager, stock_id, start_date, end_date)

    print(f"\n{stock_id} ({stock_name}) 資料狀況:")
    print(f"  現有資料: {existing_count:,} 筆")
    print(f"  預期資料: {expected_count:,} 筆")
    print(f"  完成度: {completion_rate:.1f}%")

    # 如果完成度超過95%，跳過
    if completion_rate >= 95:
        print(f"{stock_id} 完成度 {completion_rate:.1f}% >= 95%，跳過收集")
        return existing_count, 0

    total_collected = 0

    for attempt in range(max_retries):
        try:
            print(f"收集 {stock_id} ({stock_name}) 資料 (第 {attempt + 1} 次嘗試)...")

            # 1. 收集股價資料
            df = finmind_collector.get_stock_price_data(stock_id, start_date, end_date)
            if not df.empty:
                saved_count = save_stock_prices(db_manager, stock_id, df.to_dict('records'))
                total_collected += saved_count
                print(f"  📈 股價資料: {saved_count} 筆")

            # 2. 收集現金流量表資料
            try:
                cash_flow_data = finmind_collector._make_request(
                    dataset="TaiwanStockCashFlowsStatement",
                    data_id=stock_id,
                    start_date=start_date,
                    end_date=end_date
                )
                if cash_flow_data['data']:
                    cash_flow_count = save_cash_flow_data(db_manager, cash_flow_data['data'], stock_id)
                    total_collected += cash_flow_count
                    print(f"  💰 現金流量: {cash_flow_count} 筆")
            except Exception as e:
                print(f"  ❌ 現金流量收集失敗: {e}")

            # 3. 收集除權除息結果資料
            try:
                dividend_result_data = finmind_collector._make_request(
                    dataset="TaiwanStockDividendResult",
                    data_id=stock_id,
                    start_date=start_date,
                    end_date=end_date
                )
                if dividend_result_data['data']:
                    dividend_count = save_dividend_result_data(db_manager, dividend_result_data['data'], stock_id)
                    total_collected += dividend_count
                    print(f"  🎯 除權除息: {dividend_count} 筆")
            except Exception as e:
                print(f"  ❌ 除權除息收集失敗: {e}")

            if total_collected > 0:
                print(f"✅ {stock_id} 完成，總收集 {total_collected} 筆資料")
                logger.info(f"{stock_id} ({stock_name}) 收集完成，儲存 {total_collected} 筆資料")
                return existing_count, total_collected
            else:
                print(f"❌ {stock_id} 無資料")
                return existing_count, 0
                
        except Exception as e:
            error_msg = str(e)
            print(f"{stock_id} 第 {attempt + 1} 次嘗試失敗: {error_msg}")
            logger.error(f"{stock_id} 第 {attempt + 1} 次嘗試失敗: {error_msg}")

            # 如果是API限制錯誤，進行智能等待
            if "402" in error_msg or "Payment Required" in error_msg or "API請求限制" in error_msg:
                if attempt < max_retries - 1:  # 不是最後一次嘗試
                    wait_for_api_reset()
                else:
                    print(f"{stock_id} 達到最大重試次數，跳過")
                    return existing_count, 0
            else:
                # 其他錯誤，短暫等待後重試
                if attempt < max_retries - 1:
                    print(f"等待 5 秒後重試...")
                    time.sleep(5)

    print(f"{stock_id} 收集失敗，已達最大重試次數")
    return existing_count, 0

def ensure_stocks_in_database(db_manager):
    """確保股票資訊存在於資料庫中"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        for stock in SELECTED_STOCKS:
            cursor.execute("""
                INSERT OR REPLACE INTO stocks
                (stock_id, stock_name, market, is_etf, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                stock['stock_id'],
                stock['stock_name'],
                stock['market'],
                1 if stock['is_etf'] else 0,
                datetime.now()
            ))

        conn.commit()
        logger.info("股票資訊已更新到資料庫")

    except Exception as e:
        logger.error(f"更新股票資訊失敗: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集10檔精選股票的10年資料')
    parser.add_argument('--start-date', default='2015-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=3, help='批次大小 (預設: 3)')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前3檔股票)')

    args = parser.parse_args()

    print("=" * 60)
    print("📊 10檔精選股票10年資料收集系統")
    print("=" * 60)
    print(f"收集期間: {args.start_date} ~ {args.end_date}")
    print(f"批次大小: {args.batch_size}")
    print(f"精選股票: {len(SELECTED_STOCKS)} 檔")
    if args.test:
        print("🧪 測試模式：只收集前3檔股票")
    print("=" * 60)

    # 顯示股票清單
    print("\n精選股票清單:")
    for i, stock in enumerate(SELECTED_STOCKS, 1):
        etf_mark = " (ETF)" if stock['is_etf'] else ""
        print(f"  {i:2d}. {stock['stock_id']} - {stock['stock_name']}{etf_mark}")

    print("=" * 60)

    # 初始化
    init_logging()
    logger.info("開始10檔精選股票10年資料收集")

    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        finmind_collector = FinMindDataCollector()

        # 確保股票資訊存在於資料庫中
        ensure_stocks_in_database(db_manager)

        total_existing = 0
        total_collected = 0
        success_count = 0
        failed_stocks = []

        start_time = datetime.now()

        # 如果是測試模式，只處理前3檔股票
        stocks_to_process = SELECTED_STOCKS[:3] if args.test else SELECTED_STOCKS

        for i, stock_info in enumerate(stocks_to_process, 1):
            print(f"\n[{i}/{len(stocks_to_process)}] 處理 {stock_info['stock_id']} ({stock_info['stock_name']})")

            try:
                existing, collected = collect_stock_data_with_retry(
                    db_manager, finmind_collector, stock_info,
                    args.start_date, args.end_date
                )

                total_existing += existing
                total_collected += collected

                if collected > 0 or existing > 0:
                    success_count += 1
                else:
                    failed_stocks.append(stock_info['stock_id'])

                # 股票間休息，避免請求過於頻繁
                if i < len(SELECTED_STOCKS):
                    print(f"休息 3 秒...")
                    time.sleep(3)

            except Exception as e:
                print(f"{stock_info['stock_id']} 處理失敗: {e}")
                logger.error(f"處理 {stock_info['stock_id']} 失敗: {e}")
                failed_stocks.append(stock_info['stock_id'])

        # 計算執行時間
        end_time = datetime.now()
        execution_time = end_time - start_time

        # 最終統計
        print("\n" + "=" * 60)
        print("10檔精選股票收集完成")
        print("=" * 60)
        print(f"執行時間: {execution_time}")
        print(f"成功股票: {success_count}/{len(SELECTED_STOCKS)}")
        print(f"現有資料: {total_existing:,} 筆")
        print(f"新收集資料: {total_collected:,} 筆")
        print(f"總資料量: {total_existing + total_collected:,} 筆")

        if failed_stocks:
            print(f"失敗股票: {', '.join(failed_stocks)}")

        print("=" * 60)

        # 顯示各股票資料統計
        print("\n各股票資料統計:")
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        for stock in SELECTED_STOCKS:
            cursor.execute("""
                SELECT COUNT(*) FROM stock_prices
                WHERE stock_id = ? AND date BETWEEN ? AND ?
            """, (stock['stock_id'], args.start_date, args.end_date))

            count = cursor.fetchone()[0]
            print(f"  {stock['stock_id']} ({stock['stock_name']}): {count:,} 筆")

        conn.close()

        logger.info(f"10檔精選股票收集完成，新收集 {total_collected} 筆資料，總計 {total_existing + total_collected} 筆")

        if success_count == len(SELECTED_STOCKS):
            print("\n所有股票資料收集成功！")
        else:
            print(f"\n{len(SELECTED_STOCKS) - success_count} 檔股票收集失敗，請檢查日誌")

    except Exception as e:
        error_msg = f"10檔精選股票收集失敗: {e}"
        print(f"{error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
