#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分批收集股票資料腳本 - 自動處理API限制
"""

import sys
import os
import time
from datetime import datetime, timedelta
import argparse

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager
from app.services.data_collector import FinMindDataCollector
from loguru import logger

def calculate_wait_time(start_time):
    """計算智能等待時間"""
    current_time = datetime.now()
    elapsed_minutes = (current_time - start_time).total_seconds() / 60

    # API限制是每小時重置，所以計算到下一個小時的時間
    minutes_in_hour = current_time.minute
    seconds_in_minute = current_time.second

    # 計算到下一個小時還需要多少時間
    minutes_to_next_hour = 60 - minutes_in_hour
    seconds_to_next_hour = (minutes_to_next_hour * 60) - seconds_in_minute

    # 加上5分鐘緩衝時間
    total_wait_seconds = seconds_to_next_hour + (5 * 60)

    return total_wait_seconds, elapsed_minutes

def wait_for_api_reset(start_time=None):
    """智能等待API限制重置"""
    if start_time is None:
        start_time = datetime.now()

    wait_seconds, elapsed_minutes = calculate_wait_time(start_time)

    print("\n" + "="*60)
    print("⏰ API請求限制已達上限，智能等待重置...")
    print("="*60)
    print(f"📊 本輪已運行: {elapsed_minutes:.1f} 分鐘")
    print(f"⏳ 預計等待: {wait_seconds/60:.1f} 分鐘")
    print("="*60)

    # 顯示倒計時
    for remaining in range(int(wait_seconds), 0, -60):
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\r⏳ [{current_time}] 剩餘等待時間: {hours:02d}:{minutes:02d}:00", end="", flush=True)
        time.sleep(60)

    print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] 等待完成，繼續收集資料...")
    print("="*60)

def collect_batch_with_retry(collector, stock_batch, start_date, end_date, batch_start_time, max_retries=3):
    """收集一批股票資料，支援重試"""
    for attempt in range(max_retries):
        try:
            print(f"\n📊 收集批次資料 (第 {attempt + 1} 次嘗試)...")
            collected_data = collector.collect_batch_data(
                stock_list=stock_batch,
                start_date=start_date,
                end_date=end_date,
                batch_size=10
            )
            return collected_data
            
        except Exception as e:
            error_msg = str(e)
            
            # 檢查是否為API限制錯誤
            if "402" in error_msg or "Payment Required" in error_msg:
                print(f"\n⚠️  遇到API限制錯誤: {error_msg}")
                if attempt < max_retries - 1:
                    wait_for_api_reset(batch_start_time)
                    # 重置開始時間為等待後的時間
                    batch_start_time = datetime.now()
                    continue
                else:
                    raise Exception("API限制錯誤，已達最大重試次數")
            
            # 其他錯誤
            elif attempt < max_retries - 1:
                print(f"⚠️  收集失敗 (第 {attempt + 1} 次): {error_msg}")
                print("等待30秒後重試...")
                time.sleep(30)
                continue
            else:
                raise e
    
    return None

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

def collect_main_stocks_batch(start_date=None, end_date=None, batch_size=200, skip_existing=True):
    """分批收集主要股票資料"""
    
    # 設定預設日期
    if not start_date:
        start_date = Config.DATA_START_DATE
    if not end_date:
        end_date = Config.DATA_END_DATE
    
    print("="*60)
    print("📈 台股主要股票分批收集系統")
    print("="*60)
    print(f"資料期間: {start_date} ~ {end_date}")
    print(f"批次大小: {batch_size} 檔")
    print("="*60)
    
    # 初始化
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    collector = FinMindDataCollector(
        api_url=Config.FINMIND_API_URL,
        api_token=Config.FINMIND_API_TOKEN
    )
    
    try:
        # 1. 取得完整股票清單
        print("\n1. 取得股票清單...")
        stock_list = collector.get_stock_list(use_full_list=True)
        
        # 篩選主要股票：上市、上櫃、00開頭ETF
        main_stocks = [s for s in stock_list if (
            s['market'] in ['TWSE', 'TPEX'] and (
                # 排除01開頭的特殊股票（權證等）
                not s['stock_id'].startswith('01') and
                not s['stock_id'].startswith('02') and
                # ETF只保留00開頭的
                (not s['is_etf'] or s['stock_id'].startswith('00'))
            )
        )]
        
        print(f"   完整清單: {len(stock_list)} 檔")
        print(f"   篩選後: {len(main_stocks)} 檔")
        
        # 統計分布
        twse_count = len([s for s in main_stocks if s['market'] == 'TWSE' and not s['is_etf']])
        tpex_count = len([s for s in main_stocks if s['market'] == 'TPEX' and not s['is_etf']])
        etf_count = len([s for s in main_stocks if s['is_etf']])
        
        print(f"   上市股票: {twse_count} 檔")
        print(f"   上櫃股票: {tpex_count} 檔")
        print(f"   00開頭ETF: {etf_count} 檔")

        # 2. 檢查已有資料，過濾需要收集的股票 (預設啟用)
        if skip_existing:
            print(f"\n2. 檢查已有資料...")
            stocks_to_collect = []
            stocks_skipped = []

            for i, stock in enumerate(main_stocks):
                if i % 100 == 0:
                    print(f"   檢查進度: {i}/{len(main_stocks)}")

                has_data, reason = check_existing_data(db_manager, stock['stock_id'], start_date, end_date)

                if has_data:
                    stocks_skipped.append({
                        'stock': stock,
                        'reason': reason
                    })
                else:
                    stocks_to_collect.append(stock)
        else:
            print(f"\n2. 跳過資料檢查 (--no-skip 已啟用)")
            stocks_to_collect = main_stocks
            stocks_skipped = []

        print(f"   檢查完成:")
        print(f"   需要收集: {len(stocks_to_collect)} 檔")
        print(f"   跳過收集: {len(stocks_skipped)} 檔")

        if len(stocks_skipped) > 0:
            print(f"\n   跳過的股票範例 (前5檔):")
            for i, item in enumerate(stocks_skipped[:5]):
                stock = item['stock']
                reason = item['reason']
                print(f"   {i+1}. {stock['stock_id']} {stock['stock_name']} - {reason}")

        if len(stocks_to_collect) == 0:
            print("\n🎉 所有股票都已有完整資料，無需收集！")
            return

        # 3. 分批處理需要收集的股票
        total_batches = (len(stocks_to_collect) + batch_size - 1) // batch_size
        print(f"\n3. 開始分批收集 (共 {total_batches} 批)...")

        successful_batches = 0
        total_collected = 0

        # 記錄整體開始時間
        overall_start_time = datetime.now()

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(stocks_to_collect))
            stock_batch = stocks_to_collect[start_idx:end_idx]
            
            print(f"\n" + "="*50)
            print(f"📦 處理第 {batch_num + 1}/{total_batches} 批")
            print(f"股票範圍: {start_idx + 1} ~ {end_idx}")
            print(f"批次大小: {len(stock_batch)} 檔")
            print("="*50)
            
            try:
                # 記錄這批的開始時間
                batch_start_time = datetime.now()

                # 收集這批股票的資料
                collected_data = collect_batch_with_retry(
                    collector, stock_batch, start_date, end_date, batch_start_time
                )
                
                if collected_data:
                    # 儲存資料 (這裡可以加入儲存邏輯)
                    batch_collected = len(collected_data.get('stock_prices', {}))
                    total_collected += batch_collected
                    successful_batches += 1
                    
                    print(f"✅ 第 {batch_num + 1} 批完成，收集 {batch_collected} 檔股票資料")
                else:
                    print(f"❌ 第 {batch_num + 1} 批失敗")
                
                # 批次間等待，避免請求過快
                if batch_num < total_batches - 1:
                    print("⏳ 等待10秒後處理下一批...")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"❌ 第 {batch_num + 1} 批處理失敗: {e}")
                
                # 詢問是否繼續
                response = input("\n是否繼續處理下一批？(y/n): ").lower()
                if response != 'y':
                    break
        
        # 3. 總結
        print("\n" + "="*60)
        print("📊 分批收集完成統計")
        print("="*60)
        print(f"成功批次: {successful_batches}/{total_batches}")
        print(f"新收集股票: {total_collected} 檔")
        print(f"跳過股票: {len(stocks_skipped)} 檔")
        print(f"總股票數: {len(main_stocks)} 檔")
        if total_batches > 0:
            print(f"收集成功率: {successful_batches/total_batches*100:.1f}%")
        
        if successful_batches == total_batches:
            print("🎉 所有批次收集完成！")
        else:
            print("⚠️  部分批次收集失敗，可稍後重新執行")
        
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='分批收集台股主要股票資料')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=200, help='批次大小 (預設200檔)')
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集近1個月)')
    parser.add_argument('--no-skip', action='store_true', help='不跳過已有資料的股票 (預設會跳過)')
    
    args = parser.parse_args()
    
    # 測試模式
    if args.test:
        print("🧪 測試模式：只收集最近1個月的資料")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
    else:
        start_date = args.start_date
        end_date = args.end_date
    
    collect_main_stocks_batch(start_date, end_date, args.batch_size, not args.no_skip)

if __name__ == "__main__":
    main()
