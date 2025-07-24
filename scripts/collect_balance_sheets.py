#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資產負債表資料收集腳本
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager as DatabaseManager
from app.services.data_collector import FinMindDataCollector
from loguru import logger

def init_logging():
    """初始化日誌"""
    log_dir = os.path.join(Config.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        os.path.join(log_dir, 'collect_balance_sheets.log'),
        rotation="50 MB",
        retention="30 days",
        level="INFO"
    )

def wait_for_api_reset():
    """等待API限制重置 - 70分鐘"""
    wait_minutes = 70
    print(f"\n⏰ 遇到API限制，等待 {wait_minutes} 分鐘...")
    print("=" * 60)
    
    for remaining in range(wait_minutes * 60, 0, -60):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\r⏳ [{current_time}] 剩餘等待時間: {hours:02d}:{minutes:02d}:00", end="", flush=True)
        time.sleep(60)
    
    print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] 等待完成，繼續收集...")

def get_balance_sheet_data(collector, stock_id, start_date, end_date):
    """獲取資產負債表資料"""
    try:
        data = collector._make_request(
            dataset="TaiwanStockBalanceSheet",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if data and 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            logger.info(f"股票 {stock_id} 獲取到 {len(df)} 筆資產負債表資料")
            return df
        else:
            logger.warning(f"股票 {stock_id} 無資產負債表資料")
            return None
            
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "Payment Required" in error_msg:
            raise Exception(f"API請求限制: {error_msg}")
        logger.error(f"獲取股票 {stock_id} 資產負債表資料失敗: {e}")
        return None

def save_balance_sheet_data(db_manager, df, stock_id):
    """儲存資產負債表資料"""
    if df is None or df.empty:
        return 0
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    
    try:
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO balance_sheets 
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
                logger.warning(f"儲存資產負債表資料失敗 {stock_id} {row.get('date', 'N/A')} {row.get('type', 'N/A')}: {e}")
                continue
        
        conn.commit()
        logger.info(f"股票 {stock_id} 成功儲存 {saved_count} 筆資產負債表資料")
        
    except Exception as e:
        logger.error(f"儲存資產負債表資料時發生錯誤: {e}")
        conn.rollback()
        
    finally:
        conn.close()
    
    return saved_count

def calculate_balance_sheet_ratios(db_manager, stock_id):
    """計算資產負債表相關比率"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT date, type, value
            FROM balance_sheets 
            WHERE stock_id = ?
            ORDER BY date, type
        """, (stock_id,))
        
        data = cursor.fetchall()
        
        if not data:
            return 0
        
        # 按日期分組處理
        date_groups = {}
        for date, type_name, value in data:
            if date not in date_groups:
                date_groups[date] = {}
            date_groups[date][type_name] = value
        
        updated_count = 0
        
        for date, metrics in date_groups.items():
            # 計算關鍵財務比率
            total_assets = metrics.get('TotalAssets', 0)
            total_liabilities = metrics.get('TotalLiabilities', 0)
            current_assets = metrics.get('CurrentAssets', 0)
            current_liabilities = metrics.get('CurrentLiabilities', 0)
            
            # 計算比率
            debt_ratio = None
            current_ratio = None
            
            if total_assets and total_assets > 0:
                if total_liabilities:
                    debt_ratio = (total_liabilities / total_assets) * 100
            
            if current_liabilities and current_liabilities > 0:
                if current_assets:
                    current_ratio = current_assets / current_liabilities
            
            # 更新財務比率表
            if debt_ratio is not None or current_ratio is not None:
                cursor.execute("""
                    INSERT OR REPLACE INTO financial_ratios 
                    (stock_id, date, debt_ratio, current_ratio, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(stock_id, date) DO UPDATE SET
                    debt_ratio = COALESCE(excluded.debt_ratio, debt_ratio),
                    current_ratio = COALESCE(excluded.current_ratio, current_ratio)
                """, (
                    stock_id, date, debt_ratio, current_ratio, datetime.now()
                ))
                updated_count += 1
        
        conn.commit()
        logger.info(f"股票 {stock_id} 資產負債表比率計算完成，更新 {updated_count} 筆記錄")
        return updated_count
        
    except Exception as e:
        logger.error(f"計算資產負債表比率失敗 {stock_id}: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def collect_balance_sheet_batch(stock_list, start_date, end_date, batch_size=3):
    """批次收集資產負債表資料"""
    print(f"📊 開始收集資產負債表資料")
    print(f"📅 日期範圍: {start_date} ~ {end_date}")
    print(f"📈 股票數量: {len(stock_list)}")
    print(f"🔄 批次大小: {batch_size}")
    print("=" * 60)
    
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    collector = FinMindDataCollector(
        api_url=Config.FINMIND_API_URL,
        api_token=Config.FINMIND_API_TOKEN
    )
    
    total_saved = 0
    total_ratios = 0
    failed_stocks = []
    
    for i in tqdm(range(0, len(stock_list), batch_size), desc="收集進度"):
        batch = stock_list[i:i + batch_size]
        
        for stock in batch:
            stock_id = stock['stock_id']
            stock_name = stock.get('stock_name', stock_id)
            
            try:
                print(f"📊 收集 {stock_id} ({stock_name}) 資產負債表資料...")
                
                df = get_balance_sheet_data(collector, stock_id, start_date, end_date)
                
                if df is not None and not df.empty:
                    saved_count = save_balance_sheet_data(db_manager, df, stock_id)
                    total_saved += saved_count
                    
                    ratio_count = calculate_balance_sheet_ratios(db_manager, stock_id)
                    total_ratios += ratio_count
                    
                    print(f"✅ {stock_id} 完成，儲存 {saved_count} 筆資料，計算 {ratio_count} 筆比率")
                else:
                    print(f"⚠️  {stock_id} 無資料")
                
                time.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ {stock_id} 失敗: {error_msg}")
                logger.error(f"收集 {stock_id} 資產負債表失敗: {error_msg}")
                failed_stocks.append((stock_id, error_msg))
                
                if "API請求限制" in error_msg or "402" in error_msg:
                    wait_for_api_reset()
                else:
                    time.sleep(5)
        
        if i + batch_size < len(stock_list):
            print(f"⏸️  批次完成，休息15秒...")
            time.sleep(15)
    
    print("\n" + "=" * 60)
    print("📊 資產負債表資料收集完成")
    print("=" * 60)
    print(f"✅ 成功收集: {len(stock_list) - len(failed_stocks)} 檔股票")
    print(f"💾 總儲存筆數: {total_saved}")
    print(f"📈 財務比率筆數: {total_ratios}")
    print(f"❌ 失敗股票: {len(failed_stocks)} 檔")
    
    return total_saved, total_ratios, failed_stocks

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集台股資產負債表資料')
    parser.add_argument('--start-date', default='2020-01-01', help='開始日期')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期')
    parser.add_argument('--batch-size', type=int, default=3, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("台股資產負債表資料收集系統")
    print("=" * 60)
    
    init_logging()
    logger.info("開始收集資產負債表資料")
    
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
            print("🧪 測試模式：只收集前3檔股票")
        
        if not stock_list:
            print("❌ 未找到股票資料")
            return
        
        total_saved, total_ratios, failed_stocks = collect_balance_sheet_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )
        
        logger.info(f"資產負債表資料收集完成，共儲存 {total_saved} 筆資料，計算 {total_ratios} 筆比率")
        
    except Exception as e:
        error_msg = f"資產負債表資料收集失敗: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
