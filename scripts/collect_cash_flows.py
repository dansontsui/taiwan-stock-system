#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

FinMind APITaiwanStockCashFlowsStatement
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
import pandas as pd

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
    """API"""
    print("API請求限制，等待70分鐘後重試...")
    for i in range(70, 0, -1):
        print(f"\r剩餘等待時間: {i} 分鐘", end="", flush=True)
        time.sleep(60)
    print("\n等待完成，繼續收集...")

def get_cash_flow_data(collector, stock_id, start_date, end_date):
    """"""
    try:
        data = collector._make_request(
            dataset="TaiwanStockCashFlowsStatement",
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
        required_columns = ['date', 'stock_id', 'type', 'value']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f": {col}")
                return None
        
        # 
        df = df.dropna(subset=['date', 'stock_id', 'type'])
        
        return df
        
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "Payment Required" in error_msg:
            raise Exception("API")
        else:
            logger.error(f": {e}")
            raise e

def save_cash_flow_data(db_manager, df, stock_id):
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
                    INSERT OR REPLACE INTO cash_flow_statements 
                    (stock_id, date, type, value, origin_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row['stock_id'],
                    row['date'],
                    row['type'],
                    row['value'],
                    row.get('origin_name', ''),
                    datetime.now()
                ))
                saved_count += 1
                
            except Exception as e:
                logger.warning(f" {stock_id} {row.get('date', 'N/A')} {row.get('type', 'N/A')}: {e}")
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

def calculate_cash_flow_ratios(db_manager, stock_id):
    """"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 
        cursor.execute("""
            SELECT date, type, value
            FROM cash_flow_statements
            WHERE stock_id = ?
            ORDER BY date DESC
        """, (stock_id,))
        
        cash_flow_data = cursor.fetchall()
        
        if not cash_flow_data:
            return 0
        
        # 
        date_groups = {}
        for date, type_name, value in cash_flow_data:
            if date not in date_groups:
                date_groups[date] = {}
            date_groups[date][type_name] = value
        
        ratio_count = 0
        
        for date, data in date_groups.items():
            # 
            operating_cash_flow = data.get('CashFlowsFromOperatingActivities', 0)
            investing_cash_flow = data.get('CashProvidedByInvestingActivities', 0)
            financing_cash_flow = data.get('CashProvidedByFinancingActivities', 0)
            
            # 
            cursor.execute("""
                SELECT value FROM financial_statements
                WHERE stock_id = ? AND date = ? AND type = 'IncomeAfterTaxes'
            """, (stock_id, date))
            
            net_income_result = cursor.fetchone()
            net_income = net_income_result[0] if net_income_result else 0
            
            # 
            cash_flow_quality = 0
            if net_income != 0:
                cash_flow_quality = operating_cash_flow / net_income
            
            # 
            # 
            cursor.execute("""
                SELECT id FROM financial_ratios
                WHERE stock_id = ? AND date = ?
            """, (stock_id, date))

            existing = cursor.fetchone()

            if existing:
                # 
                cursor.execute("""
                    UPDATE financial_ratios SET
                    operating_cash_flow = ?,
                    investing_cash_flow = ?,
                    financing_cash_flow = ?,
                    cash_flow_quality = ?,
                    created_at = ?
                    WHERE stock_id = ? AND date = ?
                """, (
                    operating_cash_flow, investing_cash_flow,
                    financing_cash_flow, cash_flow_quality, datetime.now(),
                    stock_id, date
                ))
            else:
                # 
                cursor.execute("""
                    INSERT INTO financial_ratios
                    (stock_id, date, operating_cash_flow, investing_cash_flow,
                     financing_cash_flow, cash_flow_quality, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_id, date, operating_cash_flow, investing_cash_flow,
                    financing_cash_flow, cash_flow_quality, datetime.now()
                ))
            
            ratio_count += 1
        
        conn.commit()
        logger.info(f" {stock_id}  {ratio_count} ")
        
    except Exception as e:
        logger.error(f" {stock_id}: {e}")
        ratio_count = 0
    finally:
        conn.close()
    
    return ratio_count

def collect_cash_flow_batch(stock_list, start_date, end_date, batch_size=3):
    """"""
    print("開始收集現金流量表資料")
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
    total_ratios = 0
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

                df = get_cash_flow_data(collector, stock_id, start_date, end_date)

                if df is not None and not df.empty:
                    saved_count = save_cash_flow_data(db_manager, df, stock_id)
                    total_saved += saved_count

                    ratio_count = calculate_cash_flow_ratios(db_manager, stock_id)
                    total_ratios += ratio_count

                    print(f"{stock_id}  {saved_count}  {ratio_count} ")
                else:
                    print(f"{stock_id} ")
                
                time.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                print(f"{stock_id} 失敗: {error_msg}")
                logger.error(f"收集 {stock_id} 現金流量表失敗: {error_msg}")
                failed_stocks.append((stock_id, error_msg))
                
                if "API" in error_msg or "402" in error_msg:
                    wait_for_api_reset()
                else:
                    time.sleep(5)
        
        if i + batch_size < len(stock_list):
            print("15...")
            time.sleep(15)
    
    print("\n" + "=" * 60)
    print("現金流量表資料收集完成")
    print("=" * 60)
    print(f"成功收集: {len(stock_list) - len(failed_stocks)} 檔股票")
    print(f"總儲存筆數: {total_saved}")
    print(f"現金流量比率筆數: {total_ratios}")
    print(f"失敗股票: {len(failed_stocks)} 檔")
    
    return total_saved, total_ratios, failed_stocks

def main():
    """"""
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--start-date', default='2015-01-01', help=' (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help=' (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=3, help='')
    parser.add_argument('--test', action='store_true', help='3')
    
    args = parser.parse_args()
    
    try:
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
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
        
        if args.test:
            stock_list = stock_list[:3]
            print("3")
        
        if not stock_list:
            print("")
            return

        total_saved, total_ratios, failed_stocks = collect_cash_flow_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )

        if failed_stocks:
            print(f"\n:")
            for stock_id, error in failed_stocks:
                print(f"   {stock_id}: {error}")

        print(f"\n收集完成統計:")
        print(f"   總儲存筆數: {total_saved}")
        print(f"   現金流量比率: {total_ratios}")
        print(f"   成功股票: {len(stock_list) - len(failed_stocks)}")
        print(f"   失敗股票: {len(failed_stocks)}")
        
    except Exception as e:
        logger.error(f"現金流量表收集失敗: {e}")
        print(f"執行失敗: {e}")

if __name__ == "__main__":
    main()
