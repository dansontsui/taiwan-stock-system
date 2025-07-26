#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復版現金流量表收集腳本 - 批次大小50，移除有問題的財務比率計算
"""

import sys
import os
import time
import argparse
import pandas as pd
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
        os.path.join(log_dir, 'collect_cash_flows_fixed.log'),
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def wait_for_api_reset():
    """等待API限制重置"""
    wait_minutes = 70
    print(f"\n⏰ API請求限制已達上限，等待 {wait_minutes} 分鐘...", flush=True)
    print("=" * 60, flush=True)

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=wait_minutes)

    print(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"預計結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 60, flush=True)

    # 每分鐘顯示進度
    for remaining in range(wait_minutes, 0, -1):
        print(f"⏳ 剩餘等待時間: {remaining} 分鐘", flush=True)
        time.sleep(60)

    print("✅ 等待完成，繼續收集", flush=True)

def get_cash_flow_data(collector, stock_id, start_date, end_date):
    """獲取現金流量表資料"""
    try:
        data = collector._make_request(
            dataset="TaiwanStockCashFlowsStatement",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )

        if not data['data']:
            logger.warning(f"股票 {stock_id} 無現金流量表資料")
            return None

        df = pd.DataFrame(data['data'])

        # 處理日期欄位
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date

        # 檢查必要欄位
        required_columns = ['date', 'stock_id', 'type', 'value']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"股票 {stock_id} 現金流資料缺少必要欄位")
            return None

        logger.info(f"獲取 {stock_id} 現金流量表資料: {len(df)} 筆")
        return df

    except Exception as e:
        logger.error(f"獲取 {stock_id} 現金流量表資料失敗: {e}")
        return None

def save_cash_flow_data(db_manager, stock_id, df):
    """儲存現金流量表資料到資料庫"""
    if df is None or df.empty:
        return 0

    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        saved_count = 0
        for _, row in df.iterrows():
            # 檢查是否已存在
            cursor.execute("""
                SELECT id FROM cash_flow_statements
                WHERE stock_id = ? AND date = ? AND type = ?
            """, (stock_id, row['date'], row['type']))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO cash_flow_statements
                    (stock_id, date, type, value, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    stock_id, row['date'], row['type'], row['value'],
                    datetime.now()
                ))
                saved_count += 1

        conn.commit()
        logger.info(f"儲存 {stock_id} 現金流量表資料: {saved_count} 筆")
        return saved_count

    except Exception as e:
        logger.error(f"儲存 {stock_id} 現金流量表資料失敗: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def collect_cash_flow_batch(stock_list, start_date, end_date, batch_size=50):
    """批次收集現金流量表資料"""
    print("=" * 60, flush=True)
    print("🚀 開始收集現金流量表資料", flush=True)
    print("=" * 60, flush=True)
    print(f"📅 日期範圍: {start_date} ~ {end_date}", flush=True)
    print(f"📊 股票數量: {len(stock_list)}", flush=True)
    print(f"🔢 批次大小: {batch_size}", flush=True)
    print("=" * 60, flush=True)

    db_manager = DatabaseManager(Config.DATABASE_PATH)
    collector = FinMindDataCollector(
        api_url=Config.FINMIND_API_URL,
        api_token=Config.FINMIND_API_TOKEN
    )

    total_saved = 0
    failed_stocks = []

    total_batches = (len(stock_list) + batch_size - 1) // batch_size
    for batch_idx, i in enumerate(range(0, len(stock_list), batch_size), 1):
        batch = stock_list[i:i + batch_size]
        print(f"\n📦 批次 {batch_idx}/{total_batches} ({len(batch)} 檔股票)", flush=True)

        for stock in batch:
            stock_id = stock['stock_id']
            stock_name = stock.get('stock_name', stock_id)

            try:
                print(f"💰 收集 {stock_id} ({stock_name}) 現金流資料...", flush=True)

                df = get_cash_flow_data(collector, stock_id, start_date, end_date)
                if df is not None:
                    saved_count = save_cash_flow_data(db_manager, stock_id, df)
                    total_saved += saved_count
                    print(f"   ✅ {stock_id} 完成: +{saved_count} 筆", flush=True)
                else:
                    print(f"   ⏭️  {stock_id} 無資料", flush=True)

            except Exception as e:
                error_msg = str(e)
                failed_stocks.append((stock_id, error_msg))
                print(f"   ❌ {stock_id} 失敗: {error_msg}", flush=True)
                logger.error(f"收集 {stock_id} 失敗: {error_msg}")

                # API限制處理
                if "API" in error_msg or "402" in error_msg:
                    wait_for_api_reset()
                else:
                    time.sleep(5)

        # 批次間休息
        if i + batch_size < len(stock_list):
            print(f"⏰ 批次休息15秒... (已處理 {i + len(batch)}/{len(stock_list)})", flush=True)
            time.sleep(15)

    print("\n" + "=" * 60, flush=True)
    print("🎉 現金流量表資料收集完成", flush=True)
    print("=" * 60, flush=True)
    print(f"📊 成功收集: {len(stock_list) - len(failed_stocks)} 檔股票", flush=True)
    print(f"💾 總儲存筆數: {total_saved}", flush=True)
    print(f"❌ 失敗股票: {len(failed_stocks)} 檔", flush=True)

    return total_saved, failed_stocks

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='現金流量表資料收集')
    parser.add_argument('--start-date', default='2015-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=50, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式（只收集前3檔股票）')

    args = parser.parse_args()

    # 初始化
    init_logging()
    logger.info("開始現金流量表資料收集")

    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # 獲取股票清單
        cursor.execute("""
            SELECT stock_id, stock_name FROM stocks
            WHERE is_etf = 0 AND LENGTH(stock_id) = 4
            ORDER BY stock_id
        """)
        stock_list = [{'stock_id': row[0], 'stock_name': row[1]} for row in cursor.fetchall()]
        conn.close()

        # 測試模式
        if args.test:
            stock_list = stock_list[:3]
            print("🧪 測試模式：只收集前3檔股票", flush=True)

        total_saved, failed_stocks = collect_cash_flow_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )

        if failed_stocks:
            print(f"\n❌ 失敗股票清單:", flush=True)
            for stock_id, error in failed_stocks:
                print(f"   {stock_id}: {error}", flush=True)

        print(f"\n📈 收集完成統計:", flush=True)
        print(f"   💾 總儲存筆數: {total_saved}", flush=True)
        logger.info(f"現金流量表收集完成，總儲存 {total_saved} 筆資料")

    except Exception as e:
        error_msg = f"現金流量表收集失敗: {e}"
        print(f"❌ {error_msg}", flush=True)
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
