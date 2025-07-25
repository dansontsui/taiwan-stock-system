#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能股價資料收集腳本 - 包含跳過已完成資料和智能等待功能
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import Config
    from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
    from app.services.data_collector import FinMindDataCollector
    from loguru import logger
except ImportError as e:
    print(f"❌ 模組導入失敗: {e}")
    print("💡 請確認在正確的專案目錄中執行")
    sys.exit(1)

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger.add(
        os.path.join(log_dir, 'collect_stock_prices_smart.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def wait_for_api_reset():
    """等待API限制重置 - 70分鐘"""
    wait_minutes = 70
    print(f"\n API請求限制已達上限，智能等待 {wait_minutes} 分鐘...")
    print("=" * 60)

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=wait_minutes)

    print(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"預計結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    for remaining in range(wait_minutes * 60, 0, -60):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        current_time = datetime.now().strftime("%H:%M:%S")
        progress = ((wait_minutes * 60 - remaining) / (wait_minutes * 60)) * 100

        print(f"\r [{current_time}] 剩餘: {hours:02d}:{minutes:02d}:00 | 進度: {progress:.1f}%", end="", flush=True)
        time.sleep(60)

    print(f"\n [{datetime.now().strftime('%H:%M:%S')}] 等待完成，繼續收集資料...")
    print("=" * 60)

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

def get_missing_date_ranges(db_manager, stock_id, start_date, end_date):
    """獲取缺失的日期範圍"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT date FROM stock_prices
            WHERE stock_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (stock_id, start_date, end_date))

        existing_dates = set(row[0] for row in cursor.fetchall())

        # 生成所有日期範圍
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        all_dates = set()
        current_dt = start_dt
        while current_dt <= end_dt:
            # 只包含工作日（週一到週五）
            if current_dt.weekday() < 5:
                all_dates.add(current_dt.strftime('%Y-%m-%d'))
            current_dt += timedelta(days=1)

        missing_dates = all_dates - existing_dates

        # 將缺失日期組織成連續範圍
        if not missing_dates:
            return []

        sorted_dates = sorted(missing_dates)
        ranges = []
        range_start = sorted_dates[0]
        range_end = sorted_dates[0]

        for i in range(1, len(sorted_dates)):
            current_date = datetime.strptime(sorted_dates[i], '%Y-%m-%d')
            prev_date = datetime.strptime(sorted_dates[i-1], '%Y-%m-%d')

            if (current_date - prev_date).days <= 3:  # 允許週末間隔
                range_end = sorted_dates[i]
            else:
                ranges.append((range_start, range_end))
                range_start = sorted_dates[i]
                range_end = sorted_dates[i]

        ranges.append((range_start, range_end))
        return ranges

    except Exception as e:
        logger.error(f"獲取 {stock_id} 缺失日期範圍失敗: {e}")
        return [(start_date, end_date)]  # 如果出錯，返回完整範圍
    finally:
        conn.close()

def collect_stock_prices_incremental(db_manager, finmind_collector, stock_id, start_date, end_date, skip_threshold=90):
    """增量收集股價資料"""

    # 檢查現有資料
    existing_count, expected_count, completion_rate = check_existing_data(db_manager, stock_id, start_date, end_date)

    print(f" {stock_id} 資料狀況:")
    print(f"  現有資料: {existing_count:,} 筆")
    print(f"  預期資料: {expected_count:,} 筆")
    print(f"  完成度: {completion_rate:.1f}%")

    # 如果完成度超過閾值，跳過
    if completion_rate >= skip_threshold:
        print(f" {stock_id} 完成度 {completion_rate:.1f}% >= {skip_threshold}%，跳過收集")
        return existing_count, 0

    # 獲取缺失的日期範圍
    missing_ranges = get_missing_date_ranges(db_manager, stock_id, start_date, end_date)

    if not missing_ranges:
        print(f" {stock_id} 無缺失資料")
        return existing_count, 0

    print(f" {stock_id} 發現 {len(missing_ranges)} 個缺失範圍")

    total_collected = 0

    for i, (range_start, range_end) in enumerate(missing_ranges, 1):
        print(f"📥 收集範圍 {i}/{len(missing_ranges)}: {range_start} ~ {range_end}")

        try:
            # 收集該範圍的資料
            df = finmind_collector.get_stock_price_data(stock_id, range_start, range_end)
            data = df.to_dict('records') if not df.empty else []

            if data and len(data) > 0:
                saved_count = save_stock_prices(db_manager, stock_id, data)
                total_collected += saved_count
                print(f" 範圍 {i} 完成，收集 {saved_count} 筆資料")
            else:
                print(f"  範圍 {i} 無資料")

            # 範圍間休息
            time.sleep(1)

        except Exception as e:
            error_msg = str(e)
            print(f" 範圍 {i} 失敗: {error_msg}")
            logger.error(f"收集 {stock_id} 範圍 {range_start}~{range_end} 失敗: {error_msg}")

            # 如果是API限制錯誤，等待70分鐘
            if "402" in error_msg or "Payment Required" in error_msg:
                wait_for_api_reset()
            else:
                time.sleep(3)

    return existing_count, total_collected

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

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='智能股價資料收集')
    parser.add_argument('--start-date', default='2024-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=10, help='批次大小')
    parser.add_argument('--skip-threshold', type=int, default=90, help='跳過閾值 (%)')
    parser.add_argument('--stock-id', help='指定股票代碼')
    parser.add_argument('--test', action='store_true', help='測試模式（只收集少量資料）')

    args = parser.parse_args()

    print("=" * 60)
    print("智能股價資料收集系統")
    print("=" * 60)
    print(f"收集期間: {args.start_date} ~ {args.end_date}")
    print(f"批次大小: {args.batch_size}")
    print(f"跳過閾值: {args.skip_threshold}%")
    print("=" * 60)

    # 初始化
    init_logging()
    logger.info("開始智能股價資料收集")

    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        finmind_collector = FinMindDataCollector()

        # 獲取股票清單
        if args.stock_id:
            stock_ids = [args.stock_id]
        else:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT stock_id FROM stocks
                WHERE is_etf = 0 AND LENGTH(stock_id) = 4
                ORDER BY stock_id
            """)
            stock_ids = [row[0] for row in cursor.fetchall()]
            conn.close()


        # 測試模式：只處理前3檔股票
        if args.test:
            stock_ids = stock_ids[:3]
            print("測試模式：只收集前3檔股票")
        print(f" 準備收集 {len(stock_ids)} 檔股票資料")

        total_existing = 0
        total_collected = 0
        processed_count = 0
        skipped_count = 0

        for i, stock_id in enumerate(stock_ids, 1):
            print(f"\n [{i}/{len(stock_ids)}] 處理 {stock_id}")

            try:
                existing, collected = collect_stock_prices_incremental(
                    db_manager, finmind_collector, stock_id,
                    args.start_date, args.end_date, args.skip_threshold
                )

                total_existing += existing
                total_collected += collected
                processed_count += 1

                if collected == 0:
                    skipped_count += 1

                # 批次間休息
                if i % args.batch_size == 0:
                    print(f"\n  批次休息30秒... (已處理 {i}/{len(stock_ids)})")
                    time.sleep(30)

            except Exception as e:
                print(f" {stock_id} 處理失敗: {e}")
                logger.error(f"處理 {stock_id} 失敗: {e}")

        # 最終統計
        print("\n" + "=" * 60)
        print(" 智能股價收集完成")
        print("=" * 60)
        print(f"處理股票: {processed_count}/{len(stock_ids)}")
        print(f"跳過股票: {skipped_count}")
        print(f"現有資料: {total_existing:,} 筆")
        print(f"新收集資料: {total_collected:,} 筆")
        print(f"總資料量: {total_existing + total_collected:,} 筆")
        print("=" * 60)

        logger.info(f"智能股價收集完成，新收集 {total_collected} 筆資料")

    except Exception as e:
        error_msg = f"智能股價收集失敗: {e}"
        print(f" {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
