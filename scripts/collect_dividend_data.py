#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股利政策資料收集腳本
"""

import sys
import os
import time
import argparse
import warnings
from datetime import datetime, timedelta
import pandas as pd
# from tqdm import tqdm  # 暫時註解掉避免依賴問題

# 隱藏 DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from app.services.data_collector import FinMindDataCollector
from loguru import logger

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

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'collect_dividend_data.log'),
        rotation="50 MB",
        retention="30 days",
        level="INFO"
    )



def get_dividend_data(collector, stock_id, start_date, end_date):
    """獲取股利政策資料"""
    try:
        data = collector._make_request(
            dataset="TaiwanStockDividend",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if data and 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            logger.info(f"股票 {stock_id} 獲取到 {len(df)} 筆股利政策資料")
            return df
        else:
            logger.warning(f"股票 {stock_id} 無股利政策資料")
            return None
            
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "Payment Required" in error_msg:
            raise Exception(f"API請求限制: {error_msg}")
        logger.error(f"獲取股票 {stock_id} 股利政策資料失敗: {e}")
        return None

def save_dividend_data(db_manager, df, stock_id):
    """儲存股利政策資料"""
    if df is None or df.empty:
        return 0
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    
    try:
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO dividend_policies 
                    (stock_id, date, year, stock_earnings_distribution, stock_statutory_surplus,
                     stock_ex_dividend_trading_date, cash_earnings_distribution, cash_statutory_surplus,
                     cash_ex_dividend_trading_date, cash_dividend_payment_date, total_employee_stock_dividend,
                     total_employee_cash_dividend, participate_distribution_total_shares,
                     announcement_date, announcement_time, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row['year'],
                    row.get('StockEarningsDistribution'),
                    row.get('StockStatutorySurplus'),
                    row.get('StockExDividendTradingDate') if row.get('StockExDividendTradingDate') != '0' else None,
                    row.get('CashEarningsDistribution'),
                    row.get('CashStatutorySurplus'),
                    row.get('CashExDividendTradingDate') if row.get('CashExDividendTradingDate') != '0' else None,
                    row.get('CashDividendPaymentDate') if row.get('CashDividendPaymentDate') != '0' else None,
                    row.get('TotalEmployeeStockDividend'),
                    row.get('TotalEmployeeCashDividend'),
                    row.get('ParticipateDistributionOfTotalShares'),
                    row.get('AnnouncementDate') if row.get('AnnouncementDate') != '0' else None,
                    row.get('AnnouncementTime'),
                    datetime.now()
                ))
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"儲存股利政策資料失敗 {stock_id} {row.get('date', 'N/A')}: {e}")
                continue
        
        conn.commit()
        logger.info(f"股票 {stock_id} 成功儲存 {saved_count} 筆股利政策資料")
        
    except Exception as e:
        logger.error(f"儲存股利政策資料時發生錯誤: {e}")
        conn.rollback()
        
    finally:
        conn.close()
    
    return saved_count

def collect_dividend_batch(stock_list, start_date, end_date, batch_size=3):
    """批次收集股利政策資料"""
    print(f"開始收集股利政策資料")
    print(f"日期範圍: {start_date} ~ {end_date}")
    print(f"股票數量: {len(stock_list)}")
    print(f"批次大小: {batch_size}")
    print("=" * 60)
    
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
        print(f"處理批次 {batch_idx}/{total_batches} ({len(batch)} 檔股票)")
        
        for stock in batch:
            stock_id = stock['stock_id']
            stock_name = stock.get('stock_name', stock_id)
            
            try:
                print(f" 收集 {stock_id} ({stock_name}) 股利政策資料...")
                
                df = get_dividend_data(collector, stock_id, start_date, end_date)
                
                if df is not None and not df.empty:
                    saved_count = save_dividend_data(db_manager, df, stock_id)
                    total_saved += saved_count
                    print(f" {stock_id} 完成，儲存 {saved_count} 筆資料")
                else:
                    print(f"  {stock_id} 無資料")
                
                time.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                print(f"{stock_id} 失敗: {error_msg}")
                logger.error(f"收集 {stock_id} 股利政策失敗: {error_msg}")
                failed_stocks.append((stock_id, error_msg))
                
                # 如果是API限制錯誤，智能等待
                if is_api_limit_error(error_msg):
                    smart_wait_for_api_reset()
                else:
                    time.sleep(5)
        
        if i + batch_size < len(stock_list):
            print(f"  批次完成，休息15秒...")
            time.sleep(15)
    
    print("\n" + "=" * 60)
    print("股利政策資料收集完成")
    print("=" * 60)
    print(f"成功收集: {len(stock_list) - len(failed_stocks)} 檔股票")
    print(f"總儲存筆數: {total_saved}")
    print(f"失敗股票: {len(failed_stocks)} 檔")
    
    return total_saved, failed_stocks

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集台股股利政策資料')
    parser.add_argument('--start-date', default='2015-01-01', help='開始日期')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期')
    parser.add_argument('--batch-size', type=int, default=3, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式')
    parser.add_argument('--stock-id', help='指定股票代碼')

    args = parser.parse_args()

    print("=" * 60)
    if args.stock_id:
        print(f"台股股利政策資料收集系統 - 個股 {args.stock_id}")
    else:
        print("台股股利政策資料收集系統")
    print("=" * 60)

    init_logging()
    logger.info("開始收集股利政策資料")

    # 重置執行時間計時器
    reset_execution_timer()

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
            print(" 測試模式：只收集前5檔股票")

        if not stock_list:
            if args.stock_id:
                print(f" 找不到股票代碼: {args.stock_id}")
            else:
                print(" 未找到股票資料")
            return
        
        total_saved, failed_stocks = collect_dividend_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )
        
        logger.info(f"股利政策資料收集完成，共儲存 {total_saved} 筆資料")
        
    except Exception as e:
        error_msg = f"股利政策資料收集失敗: {e}"
        print(f" {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
