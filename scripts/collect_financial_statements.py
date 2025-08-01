#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
綜合損益表資料收集腳本
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
        os.path.join(log_dir, 'collect_financial_statements.log'),
        rotation="50 MB",
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

def get_financial_statements_data(collector, stock_id, start_date, end_date):
    """獲取單一股票的綜合損益表資料"""
    try:
        # 使用FinMind API獲取綜合損益表資料
        data = collector._make_request(
            dataset="TaiwanStockFinancialStatements",
            data_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if data and 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            logger.info(f"股票 {stock_id} 獲取到 {len(df)} 筆綜合損益表資料")
            return df
        else:
            logger.warning(f"股票 {stock_id} 無綜合損益表資料")
            return None
            
    except Exception as e:
        logger.error(f"獲取股票 {stock_id} 綜合損益表資料失敗: {e}")
        return None

def save_financial_statements_data(db_manager, df, stock_id):
    """儲存綜合損益表資料到資料庫"""
    if df is None or df.empty:
        return 0
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    
    try:
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO financial_statements 
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
                logger.warning(f"儲存綜合損益表資料失敗 {stock_id} {row.get('date', 'N/A')} {row.get('type', 'N/A')}: {e}")
                continue
        
        conn.commit()
        logger.info(f"股票 {stock_id} 成功儲存 {saved_count} 筆綜合損益表資料")
        
    except Exception as e:
        logger.error(f"儲存綜合損益表資料時發生錯誤: {e}")
        conn.rollback()
        
    finally:
        conn.close()
    
    return saved_count

def calculate_financial_ratios(db_manager, stock_id):
    """計算財務比率"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 獲取該股票的綜合損益表資料，按日期分組
        cursor.execute("""
            SELECT date, type, value
            FROM financial_statements 
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
            revenue = metrics.get('Revenue', 0)
            cost_of_goods = metrics.get('CostOfGoodsSold', 0)
            gross_profit = metrics.get('GrossProfit', 0)
            operating_income = metrics.get('OperatingIncome', 0)
            net_income = metrics.get('IncomeAfterTaxes', 0)
            
            # 計算比率
            gross_margin = None
            operating_margin = None
            net_margin = None
            
            if revenue and revenue > 0:
                if gross_profit:
                    gross_margin = (gross_profit / revenue) * 100
                if operating_income:
                    operating_margin = (operating_income / revenue) * 100
                if net_income:
                    net_margin = (net_income / revenue) * 100
            
            # 儲存到財務比率表
            if any([gross_margin, operating_margin, net_margin]):
                cursor.execute("""
                    INSERT OR REPLACE INTO financial_ratios 
                    (stock_id, date, gross_margin, operating_margin, net_margin, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    stock_id, date, gross_margin, operating_margin, net_margin, datetime.now()
                ))
                updated_count += 1
        
        conn.commit()
        logger.info(f"股票 {stock_id} 財務比率計算完成，更新 {updated_count} 筆記錄")
        return updated_count
        
    except Exception as e:
        logger.error(f"計算財務比率失敗 {stock_id}: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def collect_financial_statements_batch(stock_list, start_date, end_date, batch_size=5):
    """批次收集綜合損益表資料"""
    print(f" 開始收集綜合損益表資料")
    print(f" 日期範圍: {start_date} ~ {end_date}")
    print(f" 股票數量: {len(stock_list)}")
    print(f" 批次大小: {batch_size}")
    print("=" * 60)
    
    # 初始化
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    collector = FinMindDataCollector(
        api_url=Config.FINMIND_API_URL,
        api_token=Config.FINMIND_API_TOKEN
    )
    
    total_saved = 0
    total_ratios = 0
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
                print(f" 收集 {stock_id} ({stock_name}) 綜合損益表資料...")
                
                # 獲取綜合損益表資料
                df = get_financial_statements_data(collector, stock_id, start_date, end_date)
                
                if df is not None and not df.empty:
                    # 儲存資料
                    saved_count = save_financial_statements_data(db_manager, df, stock_id)
                    total_saved += saved_count
                    
                    # 計算財務比率
                    ratio_count = calculate_financial_ratios(db_manager, stock_id)
                    total_ratios += ratio_count
                    
                    print(f" {stock_id} 完成，儲存 {saved_count} 筆資料，計算 {ratio_count} 筆比率")
                else:
                    print(f"  {stock_id} 無資料")
                
                # 控制請求頻率
                time.sleep(1)
                
            except Exception as e:
                error_msg = str(e)
                print(f" {stock_id} 失敗: {error_msg}")
                logger.error(f"收集 {stock_id} 綜合損益表失敗: {error_msg}")
                failed_stocks.append((stock_id, error_msg))
                
                # 如果是API限制錯誤，等待70分鐘
                if "402" in error_msg or "Payment Required" in error_msg:
                    wait_for_api_reset()
                else:
                    time.sleep(3)
        
        # 批次間休息
        if i + batch_size < len(stock_list):
            print(f"  批次完成，休息10秒...")
            time.sleep(10)
    
    # 顯示結果
    print("\n" + "=" * 60)
    print(" 綜合損益表資料收集完成")
    print("=" * 60)
    print(f" 成功收集: {len(stock_list) - len(failed_stocks)} 檔股票")
    print(f" 總儲存筆數: {total_saved}")
    print(f" 財務比率筆數: {total_ratios}")
    print(f" 失敗股票: {len(failed_stocks)} 檔")
    
    if failed_stocks:
        print("\n失敗股票清單:")
        for stock_id, error in failed_stocks[:10]:  # 只顯示前10個
            print(f"  {stock_id}: {error}")
        if len(failed_stocks) > 10:
            print(f"  ... 還有 {len(failed_stocks) - 10} 檔")
    
    return total_saved, total_ratios, failed_stocks

def show_sample_data(db_manager, limit=5):
    """顯示範例資料"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        print("\n 綜合損益表資料範例:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT stock_id, date, type, value, origin_name
            FROM financial_statements 
            WHERE type IN ('Revenue', 'GrossProfit', 'OperatingIncome', 'IncomeAfterTaxes', 'EPS')
            ORDER BY stock_id, date DESC, type
            LIMIT ?
        """, (limit * 5,))
        
        for row in cursor.fetchall():
            stock_id, date, type_name, value, origin_name = row
            print(f"{stock_id} {date} {type_name:<20} {value:>15,.0f} ({origin_name})")
        
        print("\n 財務比率資料範例:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT stock_id, date, gross_margin, operating_margin, net_margin
            FROM financial_ratios 
            ORDER BY stock_id, date DESC
            LIMIT ?
        """, (limit,))
        
        for row in cursor.fetchall():
            stock_id, date, gross_margin, operating_margin, net_margin = row
            print(f"{stock_id} {date} 毛利率:{gross_margin or 0:>6.1f}% 營業利益率:{operating_margin or 0:>6.1f}% 淨利率:{net_margin or 0:>6.1f}%")
        
    except Exception as e:
        print(f"顯示範例資料失敗: {e}")
    finally:
        conn.close()

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='收集台股綜合損益表資料')
    parser.add_argument('--start-date', default='2020-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=5, help='批次大小')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前5檔股票)')
    parser.add_argument('--stock-id', help='指定股票代碼')

    args = parser.parse_args()

    print("=" * 60)
    if args.stock_id:
        print(f"台股綜合損益表資料收集系統 - 個股 {args.stock_id}")
    else:
        print("台股綜合損益表資料收集系統")
    print("=" * 60)

    # 初始化日誌
    init_logging()
    logger.info("開始收集綜合損益表資料")

    try:
        # 獲取股票清單
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

        if args.test and not args.stock_id:
            stock_list = stock_list[:5]
            print(" 測試模式：只收集前5檔股票")

        if not stock_list:
            if args.stock_id:
                print(f" 找不到股票代碼: {args.stock_id}")
            else:
                print(" 未找到股票資料，請先執行股票清單收集")
            return
        
        # 開始收集
        total_saved, total_ratios, failed_stocks = collect_financial_statements_batch(
            stock_list=stock_list,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size
        )
        
        # 顯示範例資料
        if total_saved > 0:
            show_sample_data(db_manager)
        
        logger.info(f"綜合損益表資料收集完成，共儲存 {total_saved} 筆資料，計算 {total_ratios} 筆比率")
        
    except Exception as e:
        error_msg = f"綜合損益表資料收集失敗: {e}"
        print(f" {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
