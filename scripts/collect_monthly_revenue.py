#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月營收資料收集腳本
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
import pandas as pd
# from tqdm import tqdm  # 暫時註解掉避免依賴問題

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
        os.path.join(log_dir, 'collect_monthly_revenue.log'),
        rotation="50 MB",
        retention="30 days",
        level="INFO"
    )

def wait_for_api_reset():
    """等待API限制重置 - 70分鐘"""
    wait_minutes = 70
    print(f"\nAPI請求限制已達上限，智能等待 {wait_minutes} 分鐘...")
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

        print(f"\r[{current_time}] 剩餘: {hours:02d}:{minutes:02d}:00 | 進度: {progress:.1f}%", end="", flush=True)
        time.sleep(60)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待完成，繼續收集資料...")
    print("=" * 60)

def get_monthly_revenue_data(collector, stock_id, start_date, end_date):
    """獲取單一股票的月營收資料"""
    try:
        # 使用FinMind API獲取月營收資料
        data = collector._make_request(
            dataset="TaiwanStockMonthRevenue",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if data and 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            logger.info(f"股票 {stock_id} 獲取到 {len(df)} 筆月營收資料")
            return df
        else:
            logger.warning(f"股票 {stock_id} 無月營收資料")
            return None
            
    except Exception as e:
        logger.error(f"獲取股票 {stock_id} 月營收資料失敗: {e}")
        return None

def save_monthly_revenue_data(db_manager, df, stock_id):
    """儲存月營收資料到資料庫"""
    if df is None or df.empty:
        return 0
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    
    try:
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
                    datetime.now()
                ))
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"儲存月營收資料失敗 {stock_id} {row.get('date', 'N/A')}: {e}")
                continue
        
        conn.commit()
        logger.info(f"股票 {stock_id} 成功儲存 {saved_count} 筆月營收資料")
        
    except Exception as e:
        logger.error(f"儲存月營收資料時發生錯誤: {e}")
        conn.rollback()
        
    finally:
        conn.close()
    
    return saved_count

def calculate_growth_rates(db_manager, stock_id):
    """計算月營收成長率"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 獲取該股票的月營收資料，按年月排序
        cursor.execute("""
            SELECT revenue_year, revenue_month, revenue
            FROM monthly_revenues 
            WHERE stock_id = ?
            ORDER BY revenue_year, revenue_month
        """, (stock_id,))
        
        data = cursor.fetchall()
        
        if len(data) < 2:
            return
        
        # 計算月增率和年增率
        for i in range(len(data)):
            year, month, revenue = data[i]
            
            # 計算月增率 (MoM)
            mom_growth = None
            if i > 0:
                prev_revenue = data[i-1][2]
                if prev_revenue and prev_revenue > 0:
                    mom_growth = ((revenue - prev_revenue) / prev_revenue) * 100
            
            # 計算年增率 (YoY)
            yoy_growth = None
            # 找去年同月的資料
            for j in range(i):
                prev_year, prev_month, prev_revenue = data[j]
                if prev_year == year - 1 and prev_month == month:
                    if prev_revenue and prev_revenue > 0:
                        yoy_growth = ((revenue - prev_revenue) / prev_revenue) * 100
                    break
            
            # 更新成長率資料
            if mom_growth is not None or yoy_growth is not None:
                cursor.execute("""
                    UPDATE monthly_revenues 
                    SET revenue_growth_mom = ?, revenue_growth_yoy = ?
                    WHERE stock_id = ? AND revenue_year = ? AND revenue_month = ?
                """, (mom_growth, yoy_growth, stock_id, year, month))
        
        conn.commit()
        logger.info(f"股票 {stock_id} 成長率計算完成")
        
    except Exception as e:
        logger.error(f"計算成長率失敗 {stock_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def collect_monthly_revenue_batch(stock_list, start_date, end_date, batch_size=10):
    """批次收集月營收資料"""
    print(f"開始收集月營收資料")
    print(f"日期範圍: {start_date} ~ {end_date}")
    print(f"股票數量: {len(stock_list)}")
    print(f"批次大小: {batch_size}")
    print("=" * 60)
    
    # 初始化
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    collector = FinMindDataCollector(
        api_url=Config.FINMIND_API_URL,
        api_token=Config.FINMIND_API_TOKEN
    )
    
    total_saved = 0
    failed_stocks = []
    
    # 分批處理
    total_batches = (len(stock_list) + batch_size - 1) // batch_size
    for batch_idx, i in enumerate(range(0, len(stock_list), batch_size), 1):
        batch = stock_list[i:i + batch_size]
        print(f"處理批次 {batch_idx}/{total_batches} ({len(batch)} 檔股票)")
        
        for stock in batch:
            stock_id = stock['stock_id']
            stock_name = stock.get('stock_name', stock_id)
            
            try:
                print(f"收集 {stock_id} ({stock_name}) 月營收資料...")
                
                # 獲取月營收資料
                df = get_monthly_revenue_data(collector, stock_id, start_date, end_date)
                
                if df is not None and not df.empty:
                    # 儲存資料
                    saved_count = save_monthly_revenue_data(db_manager, df, stock_id)
                    total_saved += saved_count
                    
                    # 計算成長率
                    calculate_growth_rates(db_manager, stock_id)
                    
                    print(f"{stock_id} 完成，儲存 {saved_count} 筆資料")
                else:
                    print(f"{stock_id} 無資料")
                
                # 控制請求頻率
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = str(e)
                print(f"{stock_id} 失敗: {error_msg}")
                logger.error(f"收集 {stock_id} 月營收失敗: {error_msg}")
                failed_stocks.append((stock_id, error_msg))
                
                # 如果是API限制錯誤，等待70分鐘
                if "402" in error_msg or "Payment Required" in error_msg:
                    wait_for_api_reset()
                else:
                    time.sleep(2)
        
        # 批次間休息
        if i + batch_size < len(stock_list):
            print(f"批次完成，休息5秒...")
            time.sleep(5)
    
    # 顯示結果
    print("\n" + "=" * 60)
    print("月營收資料收集完成")
    print("=" * 60)
    print(f"成功收集: {len(stock_list) - len(failed_stocks)} 檔股票")
    print(f"總儲存筆數: {total_saved}")
    print(f"失敗股票: {len(failed_stocks)} 檔")
    
    if failed_stocks:
        print("\n失敗股票清單:")
        for stock_id, error in failed_stocks[:10]:  # 只顯示前10個
            print(f"  {stock_id}: {error}")
        if len(failed_stocks) > 10:
            print(f"  ... 還有 {len(failed_stocks) - 10} 檔")
    
    return total_saved, failed_stocks

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集台股月營收資料')
    parser.add_argument('--start-date', default='2020-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=10, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前10檔股票)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("台股月營收資料收集系統")
    print("=" * 60)
    
    # 初始化日誌
    init_logging()
    logger.info("開始收集月營收資料")
    
    try:
        # 獲取股票清單
        db_manager = DatabaseManager(Config.DATABASE_PATH)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 只選擇真正的上市公司股票 (4位數字股票代碼)
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
            stock_list = stock_list[:10]
            print("測試模式：只收集前10檔股票")
        
        if not stock_list:
            print("未找到股票資料，請先執行股票清單收集")
            return
        
        # 開始收集
        total_saved, failed_stocks = collect_monthly_revenue_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )
        
        logger.info(f"月營收資料收集完成，共儲存 {total_saved} 筆資料")
        
    except Exception as e:
        error_msg = f"月營收資料收集失敗: {e}"
        print(f"{error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
