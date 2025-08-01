#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

FinMind APITaiwanStockDividendResult
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
import pandas as pd
import sqlite3

# Python 3.12 SQLite
sqlite3.register_adapter(datetime, lambda x: x.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda x: datetime.fromisoformat(x.decode()))

#  Python 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import Config
    from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
    from app.services.data_collector import FinMindDataCollector
    from loguru import logger
except ImportError as e:
    print(f"模組導入失敗: {e}")
    print("請確認在正確的專案目錄中執行")
    sys.exit(1)

def wait_for_api_reset():
    """API請求限制等待"""
    print("API請求限制，等待70分鐘後重試...")
    for i in range(70, 0, -1):
        print(f"\r剩餘等待時間: {i} 分鐘", end="", flush=True)
        time.sleep(60)
    print("\n等待完成，繼續收集...")

def get_dividend_result_data(collector, stock_id, start_date, end_date):
    """"""
    try:
        data = collector._make_request(
            dataset="TaiwanStockDividendResult",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data['data']:
            return None
        
        df = pd.DataFrame(data['data'])
        
        # 
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        # 
        required_columns = ['date', 'stock_id']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f": {col}")
                return None
        
        # 
        df = df.dropna(subset=['date', 'stock_id'])
        
        return df
        
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "Payment Required" in error_msg:
            raise Exception("API")
        else:
            logger.error(f": {e}")
            raise e

def save_dividend_result_data(db_manager, df, stock_id):
    """"""
    if df is None or df.empty:
        return 0
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    
    try:
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO dividend_results
                    (stock_id, date, before_price, after_price,
                     stock_and_cache_dividend, stock_or_cache_dividend,
                     max_price, min_price, open_price, reference_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    str(row['date']),  # 
                    float(row.get('before_price', 0)) if row.get('before_price') else None,
                    float(row.get('after_price', 0)) if row.get('after_price') else None,
                    float(row.get('stock_and_cache_dividend', 0)) if row.get('stock_and_cache_dividend') else None,
                    str(row.get('stock_or_cache_dividend', '')),
                    float(row.get('max_price', 0)) if row.get('max_price') else None,
                    float(row.get('min_price', 0)) if row.get('min_price') else None,
                    float(row.get('open_price', 0)) if row.get('open_price') else None,
                    float(row.get('reference_price', 0)) if row.get('reference_price') else None,
                    datetime.now().isoformat()  # ISO
                ))
                saved_count += 1
                
            except Exception as e:
                logger.warning(f" {stock_id} {row.get('date', 'N/A')}: {e}")
                continue
        
        conn.commit()
        logger.info(f" {stock_id}  {saved_count} ")
        
    except Exception as e:
        conn.rollback()
        logger.error(f": {e}")
        saved_count = 0
    finally:
        conn.close()
    
    return saved_count

def analyze_dividend_performance(db_manager, stock_id):
    """"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 
        cursor.execute("""
            SELECT date, before_price, after_price, stock_and_cache_dividend,
                   max_price, min_price, reference_price
            FROM dividend_results
            WHERE stock_id = ?
            ORDER BY date DESC
        """, (stock_id,))
        
        dividend_data = cursor.fetchall()
        
        if not dividend_data:
            return 0
        
        analysis_count = 0
        
        for date, before_price, after_price, dividend, max_price, min_price, ref_price in dividend_data:
            if not all([before_price, after_price, dividend, max_price, min_price]):
                continue
            
            # 
            fill_right_ratio = 0
            if ref_price and ref_price > 0:
                # 
                fill_right_ratio = ((max_price - ref_price) / ref_price) * 100
            
            # 
            price_performance = 0
            if before_price and before_price > 0:
                price_performance = ((after_price - before_price + dividend) / before_price) * 100
            
            # 
            dividend_yield = 0
            if before_price and before_price > 0:
                dividend_yield = (dividend / before_price) * 100
            
            # 
            cursor.execute("""
                INSERT OR REPLACE INTO dividend_analysis
                (stock_id, ex_dividend_date, fill_right_ratio,
                 price_performance, dividend_yield, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                stock_id, date, fill_right_ratio,
                price_performance, dividend_yield, datetime.now().isoformat()
            ))
            
            analysis_count += 1
        
        conn.commit()
        logger.info(f" {stock_id}  {analysis_count} ")
        
    except Exception as e:
        logger.error(f" {stock_id}: {e}")
        analysis_count = 0
    finally:
        conn.close()
    
    return analysis_count

def collect_dividend_result_batch(stock_list, start_date, end_date, batch_size=3):
    """"""
    print("開始收集除權除息結果資料")
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
    total_analysis = 0
    failed_stocks = []
    
    total_batches = (len(stock_list) + batch_size - 1) // batch_size
    for batch_idx, i in enumerate(range(0, len(stock_list), batch_size), 1):
        batch = stock_list[i:i + batch_size]
        print(f"  {batch_idx}/{total_batches} ({len(batch)} )")
        
        for stock in batch:
            stock_id = stock['stock_id']
            stock_name = stock.get('stock_name', stock_id)
            
            try:
                print(f" {stock_id} ({stock_name}) ...")
                
                df = get_dividend_result_data(collector, stock_id, start_date, end_date)
                
                if df is not None and not df.empty:
                    saved_count = save_dividend_result_data(db_manager, df, stock_id)
                    total_saved += saved_count
                    
                    analysis_count = analyze_dividend_performance(db_manager, stock_id)
                    total_analysis += analysis_count
                    
                    print(f"{stock_id}  {saved_count}  {analysis_count} ")
                else:
                    print(f"{stock_id} ")
                
                time.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                print(f"{stock_id} 失敗: {error_msg}")
                logger.error(f"收集 {stock_id} 除權除息結果失敗: {error_msg}")
                failed_stocks.append((stock_id, error_msg))
                
                if "API" in error_msg or "402" in error_msg:
                    wait_for_api_reset()
                else:
                    time.sleep(5)
        
        if i + batch_size < len(stock_list):
            print("15...")
            time.sleep(15)
    
    print("\n" + "=" * 60)
    print("除權除息結果收集完成")
    print("=" * 60)
    print(f"成功收集: {len(stock_list) - len(failed_stocks)} 檔股票")
    print(f"總儲存筆數: {total_saved}")
    print(f"除權除息分析: {total_analysis}")
    print(f"失敗股票: {len(failed_stocks)} 檔")
    
    return total_saved, total_analysis, failed_stocks

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集台股除權除息結果資料')
    parser.add_argument('--start-date', default='2015-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=3, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前3檔股票)')
    parser.add_argument('--stock-id', help='指定股票代碼')

    args = parser.parse_args()
    
    print("=" * 60)
    if args.stock_id:
        print(f"台股除權除息結果資料收集系統 - 個股 {args.stock_id}")
    else:
        print("台股除權除息結果資料收集系統")
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
            stock_list = stock_list[:3]
            print("測試模式：只收集前3檔股票")

        if not stock_list:
            if args.stock_id:
                print(f"找不到股票代碼: {args.stock_id}")
            else:
                print("未找到股票資料")
            return
        
        total_saved, total_analysis, failed_stocks = collect_dividend_result_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )
        
        if failed_stocks:
            print(f"\n失敗的股票:")
            for stock_id, error in failed_stocks:
                print(f"   {stock_id}: {error}")

        print(f"\n收集完成統計:")
        print(f"   總儲存筆數: {total_saved}")
        print(f"   除權除息分析: {total_analysis}")
        print(f"   成功股票: {len(stock_list) - len(failed_stocks)}")
        print(f"   失敗股票: {len(failed_stocks)}")
        
    except Exception as e:
        logger.error(f"除權除息結果收集失敗: {e}")
        print(f"執行失敗: {e}")

if __name__ == "__main__":
    main()
