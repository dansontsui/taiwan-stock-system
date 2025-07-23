#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料收集腳本 - 收集10年台股歷史資料
"""

import sys
import os
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
        os.path.join(log_dir, 'collect_data.log'),
        rotation="50 MB",
        retention="30 days",
        level="INFO"
    )

def save_stock_info(db_manager: DatabaseManager, stock_list: list):
    """儲存股票基本資訊"""
    logger.info("儲存股票基本資訊...")
    
    # 準備資料
    stock_data = []
    for stock in stock_list:
        stock_data.append({
            'stock_id': stock['stock_id'],
            'stock_name': stock['stock_name'],
            'market': stock['market'],
            'is_etf': stock['is_etf'],
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
    
    # 批量插入
    try:
        db_manager.bulk_insert('stocks', stock_data)
        logger.info(f"成功儲存 {len(stock_data)} 檔股票基本資訊")
    except Exception as e:
        logger.error(f"儲存股票基本資訊失敗: {e}")
        # 嘗試逐一插入
        success_count = 0
        for stock in stock_data:
            try:
                db_manager.bulk_insert('stocks', [stock])
                success_count += 1
            except Exception as e2:
                logger.warning(f"股票 {stock['stock_id']} 可能已存在，跳過")
        
        logger.info(f"逐一插入完成，成功 {success_count} 檔")

def save_price_data(db_manager: DatabaseManager, price_data: dict):
    """儲存股價資料"""
    logger.info("儲存股價資料...")
    
    total_records = 0
    
    for stock_id, df in tqdm(price_data.items(), desc="儲存股價資料"):
        if df.empty:
            continue
        
        try:
            # 轉換為字典列表
            records = df.to_dict('records')
            
            # 添加時間戳
            for record in records:
                record['created_at'] = datetime.now()
            
            # 批量插入
            db_manager.bulk_insert('stock_prices', records)
            total_records += len(records)
            
            logger.info(f"股票 {stock_id}: 儲存 {len(records)} 筆資料")
            
        except Exception as e:
            logger.error(f"儲存股票 {stock_id} 價格資料失敗: {e}")
    
    logger.info(f"股價資料儲存完成，總計 {total_records} 筆")

def save_dividend_data(db_manager: DatabaseManager, dividend_data: dict):
    """儲存配息資料"""
    if not dividend_data:
        logger.info("無配息資料需要儲存")
        return
    
    logger.info("儲存配息資料...")
    
    total_records = 0
    
    for stock_id, df in dividend_data.items():
        if df.empty:
            continue
        
        try:
            # 轉換為字典列表
            records = df.to_dict('records')
            
            # 添加時間戳
            for record in records:
                record['created_at'] = datetime.now()
            
            # 批量插入
            db_manager.bulk_insert('etf_dividends', records)
            total_records += len(records)
            
            logger.info(f"ETF {stock_id}: 儲存 {len(records)} 筆配息資料")
            
        except Exception as e:
            logger.error(f"儲存 ETF {stock_id} 配息資料失敗: {e}")
    
    logger.info(f"配息資料儲存完成，總計 {total_records} 筆")

def update_data_status(db_manager: DatabaseManager, stock_id: str, 
                      update_type: str, status: str = 'success', 
                      error_message: str = None):
    """更新資料收集狀態"""
    try:
        record = {
            'stock_id': stock_id,
            'update_type': update_type,
            'last_update_date': datetime.now().date(),
            'status': status,
            'error_message': error_message,
            'created_at': datetime.now()
        }
        
        db_manager.bulk_insert('data_updates', [record])
        
    except Exception as e:
        logger.error(f"更新資料狀態失敗: {e}")

def check_existing_data(db_manager, stock_id, start_date, end_date):
    """檢查股票是否已有完整資料"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # 檢查是否有該股票的資料
        cursor.execute('''
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM stock_prices
            WHERE stock_id = ?
        ''', (stock_id,))

        result = cursor.fetchone()
        conn.close()

        if not result or result[0] == 0:
            return False, "無資料"

        count, min_date, max_date = result

        # 檢查資料範圍是否涵蓋需求範圍
        if min_date <= start_date and max_date >= end_date:
            return True, f"已有完整資料 ({count:,}筆, {min_date}~{max_date})"
        else:
            return False, f"資料不完整 ({count:,}筆, {min_date}~{max_date})"

    except Exception as e:
        return False, f"檢查失敗: {e}"

def collect_historical_data(start_date: str = None, end_date: str = None,
                          stock_filter: list = None, use_full_list: bool = False,
                          use_main_stocks: bool = False, skip_existing: bool = False):
    """收集歷史資料主函數"""
    
    # 設定預設日期
    if not start_date:
        start_date = Config.DATA_START_DATE
    if not end_date:
        end_date = Config.DATA_END_DATE
    
    print("=" * 60)
    print("台股歷史股價系統 - 資料收集")
    print("=" * 60)
    print(f"資料期間: {start_date} ~ {end_date}")
    print(f"預估時間: 約 30-60 分鐘 (取決於網路速度)")
    print("=" * 60)
    
    # 初始化
    init_logging()
    logger.info(f"開始收集歷史資料: {start_date} ~ {end_date}")
    
    # 建立資料庫連接
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    
    # 建立資料收集器
    collector = FinMindDataCollector(
        api_url=Config.FINMIND_API_URL,
        api_token=Config.FINMIND_API_TOKEN
    )
    
    try:
        # 1. 取得股票清單
        print("\n1. 取得股票清單...")
        if use_main_stocks:
            print("   使用主要股票清單 (上市+上櫃+00開頭ETF)...")
            stock_list = collector.get_stock_list(use_full_list=True)
            # 篩選主要股票：上市、上櫃、00開頭ETF
            stock_list = [s for s in stock_list if (
                s['market'] in ['TWSE', 'TPEX'] and (
                    not s['is_etf'] or s['stock_id'].startswith('00')
                )
            )]
        elif use_full_list:
            print("   使用完整股票清單 (從 FinMind API 獲取)...")
            stock_list = collector.get_stock_list(use_full_list=use_full_list)
        else:
            print("   使用預定義股票清單...")
            stock_list = collector.get_stock_list(use_full_list=use_full_list)
        
        # 如果有指定股票篩選
        if stock_filter:
            stock_list = [s for s in stock_list if s['stock_id'] in stock_filter]
            print(f"   篩選後股票數量: {len(stock_list)}")

        print(f"   股票清單: {len(stock_list)} 檔")

        # 檢查已有資料，跳過不需要的股票
        if skip_existing:
            print(f"\n   檢查已有資料...")
            stocks_to_collect = []
            stocks_skipped = []

            for stock in stock_list:
                has_data, reason = check_existing_data(db_manager, stock['stock_id'], start_date, end_date)

                if has_data:
                    stocks_skipped.append({
                        'stock': stock,
                        'reason': reason
                    })
                else:
                    stocks_to_collect.append(stock)

            print(f"   需要收集: {len(stocks_to_collect)} 檔")
            print(f"   跳過收集: {len(stocks_skipped)} 檔")

            if len(stocks_skipped) > 0:
                print(f"   跳過範例: {stocks_skipped[0]['stock']['stock_id']} {stocks_skipped[0]['stock']['stock_name']} - {stocks_skipped[0]['reason']}")

            stock_list = stocks_to_collect

            if len(stock_list) == 0:
                print("\n🎉 所有股票都已有完整資料，無需收集！")
                return
        
        # 2. 儲存股票基本資訊
        print("\n2. 儲存股票基本資訊...")
        save_stock_info(db_manager, stock_list)
        
        # 3. 批量收集資料
        print("\n3. 開始收集歷史資料...")
        print("   這可能需要一些時間，請耐心等待...")
        
        collected_data = collector.collect_batch_data(
            stock_list=stock_list,
            start_date=start_date,
            end_date=end_date,
            batch_size=5  # 減少批次大小以避免請求限制
        )
        
        # 4. 儲存股價資料
        print("\n4. 儲存股價資料...")
        save_price_data(db_manager, collected_data['price_data'])
        
        # 5. 儲存配息資料
        print("\n5. 儲存配息資料...")
        save_dividend_data(db_manager, collected_data['dividend_data'])
        
        # 6. 更新收集狀態
        print("\n6. 更新收集狀態...")
        for stock in stock_list:
            stock_id = stock['stock_id']
            
            # 檢查是否有資料
            if stock_id in collected_data['price_data']:
                update_data_status(db_manager, stock_id, 'price', 'success')
            else:
                update_data_status(db_manager, stock_id, 'price', 'failed', '無資料')
            
            # ETF 配息狀態
            if stock['is_etf']:
                if stock_id in collected_data['dividend_data']:
                    update_data_status(db_manager, stock_id, 'dividend', 'success')
                else:
                    update_data_status(db_manager, stock_id, 'dividend', 'failed', '無配息資料')
        
        # 7. 顯示統計資訊
        print("\n" + "=" * 60)
        print("資料收集完成統計")
        print("=" * 60)
        
        # 資料庫統計
        stock_count = db_manager.get_table_count('stocks')
        price_count = db_manager.get_table_count('stock_prices')
        dividend_count = db_manager.get_table_count('etf_dividends')
        
        print(f"股票數量: {stock_count:,}")
        print(f"股價記錄: {price_count:,}")
        print(f"配息記錄: {dividend_count:,}")
        print(f"資料庫大小: {db_manager.get_database_size()}")
        
        # 成功率統計
        success_stocks = len(collected_data['price_data'])
        total_stocks = len(stock_list)
        success_rate = (success_stocks / total_stocks) * 100 if total_stocks > 0 else 0
        
        print(f"收集成功率: {success_rate:.1f}% ({success_stocks}/{total_stocks})")
        
        print("\n✅ 資料收集完成！")
        print("\n下一步:")
        print("1. 執行 python run.py 啟動系統")
        print("2. 瀏覽器開啟 http://localhost:5000 查看系統")
        
        logger.info("歷史資料收集成功完成")
        
    except Exception as e:
        error_msg = f"資料收集失敗: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        raise
    
    finally:
        db_manager.close()

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='台股歷史資料收集')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--stocks', nargs='+', help='指定股票代碼')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集少量資料)')
    parser.add_argument('--full-list', action='store_true', help='使用完整股票清單 (從 FinMind API 獲取所有股票)')
    parser.add_argument('--main-stocks', action='store_true', help='收集主要股票 (上市+上櫃+00開頭ETF)')
    parser.add_argument('--batch-size', type=int, default=200, help='批次大小 (預設200檔)')
    parser.add_argument('--wait-on-limit', action='store_true', help='遇到API限制時自動等待')
    parser.add_argument('--skip-existing', action='store_true', help='跳過已有完整資料的股票')
    
    args = parser.parse_args()
    
    # 測試模式
    if args.test:
        print("🧪 測試模式：只收集最近1個月的資料")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        stock_filter = ['2330', '0050', '0056']  # 只收集3檔股票
    else:
        start_date = args.start_date
        end_date = args.end_date
        stock_filter = args.stocks
    
    collect_historical_data(start_date, end_date, stock_filter, args.full_list, args.main_stocks, args.skip_existing)

if __name__ == "__main__":
    main()
