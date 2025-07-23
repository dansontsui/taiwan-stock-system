#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試跳過已有資料功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager

def check_existing_data(db_manager, stock_id, start_date, end_date):
    """檢查股票是否已有完整資料"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
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
        
        if min_date <= start_date and max_date >= end_date:
            return True, f"已有完整資料 ({count:,}筆, {min_date}~{max_date})"
        else:
            return False, f"資料不完整 ({count:,}筆, {min_date}~{max_date})"
            
    except Exception as e:
        return False, f"檢查失敗: {e}"

def test_skip_scenarios():
    """測試不同的跳過場景"""
    print("🧪 跳過已有資料功能測試")
    print("="*70)
    
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    
    # 測試場景
    test_cases = [
        {
            'name': '完全涵蓋的時間範圍',
            'stocks': ['2330', '8299', '0050'],
            'start_date': '2020-01-01',
            'end_date': '2024-12-31'
        },
        {
            'name': '部分涵蓋的時間範圍',
            'stocks': ['2330', '8299', '0050'],
            'start_date': '2010-01-01',  # 早於資料開始時間
            'end_date': '2024-12-31'
        },
        {
            'name': '超出範圍的時間',
            'stocks': ['2330', '8299', '0050'],
            'start_date': '2020-01-01',
            'end_date': '2030-12-31'  # 晚於資料結束時間
        },
        {
            'name': '混合存在和不存在的股票',
            'stocks': ['2330', '9999', '0050', '8888'],
            'start_date': '2020-01-01',
            'end_date': '2024-12-31'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 測試場景 {i}: {case['name']}")
        print(f"   時間範圍: {case['start_date']} ~ {case['end_date']}")
        print(f"   測試股票: {', '.join(case['stocks'])}")
        print("-" * 70)
        
        stocks_to_collect = []
        stocks_skipped = []
        
        for stock_id in case['stocks']:
            has_data, reason = check_existing_data(
                db_manager, stock_id, case['start_date'], case['end_date']
            )
            
            if has_data:
                stocks_skipped.append({'stock_id': stock_id, 'reason': reason})
                status = "✅ 跳過"
            else:
                stocks_to_collect.append({'stock_id': stock_id, 'reason': reason})
                status = "❌ 需要收集"
            
            print(f"   {stock_id}: {status} - {reason}")
        
        print(f"\n   📊 結果統計:")
        print(f"   需要收集: {len(stocks_to_collect)} 檔")
        print(f"   跳過收集: {len(stocks_skipped)} 檔")
        
        if len(stocks_to_collect) == 0:
            print(f"   🎉 所有股票都已有完整資料，無需收集！")

def test_database_stats():
    """測試資料庫統計資訊"""
    print(f"\n📊 資料庫統計資訊")
    print("="*70)
    
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # 查看所有股票的資料統計
    cursor.execute('''
        SELECT s.stock_id, s.stock_name, s.is_etf,
               COUNT(sp.date) as record_count,
               MIN(sp.date) as earliest_date,
               MAX(sp.date) as latest_date
        FROM stocks s
        LEFT JOIN stock_prices sp ON s.stock_id = sp.stock_id
        GROUP BY s.stock_id, s.stock_name, s.is_etf
        ORDER BY record_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    print(f"{'股票代碼':<8} {'股票名稱':<12} {'類型':<6} {'記錄數':<8} {'最早日期':<12} {'最新日期':<12}")
    print("-" * 70)
    
    total_records = 0
    stocks_with_data = 0
    
    for row in results:
        stock_id, stock_name, is_etf, count, earliest, latest = row
        
        if count > 0:
            stocks_with_data += 1
            total_records += count
        
        stock_type = "ETF" if is_etf else "股票"
        count_str = f"{count:,}" if count else "0"
        earliest_str = earliest or "N/A"
        latest_str = latest or "N/A"
        
        print(f"{stock_id:<8} {stock_name[:10]:<12} {stock_type:<6} {count_str:<8} {earliest_str:<12} {latest_str:<12}")
    
    print("-" * 70)
    print(f"總計: {len(results)} 檔股票, {stocks_with_data} 檔有資料, {total_records:,} 筆記錄")

def simulate_collection_with_skip():
    """模擬帶有跳過功能的收集過程"""
    print(f"\n🎯 模擬收集過程")
    print("="*70)
    
    # 模擬要收集的股票清單
    target_stocks = ['2330', '8299', '0050', '0056', '9999', '8888']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    print(f"目標股票: {', '.join(target_stocks)}")
    print(f"時間範圍: {start_date} ~ {end_date}")
    print()
    
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    
    stocks_to_collect = []
    stocks_skipped = []
    api_requests_saved = 0
    
    for stock_id in target_stocks:
        has_data, reason = check_existing_data(db_manager, stock_id, start_date, end_date)
        
        if has_data:
            stocks_skipped.append({'stock_id': stock_id, 'reason': reason})
            api_requests_saved += 1  # 每檔股票節省1次API請求
            print(f"✅ {stock_id}: 跳過 - {reason}")
        else:
            stocks_to_collect.append({'stock_id': stock_id, 'reason': reason})
            print(f"❌ {stock_id}: 需要收集 - {reason}")
    
    print(f"\n📊 收集統計:")
    print(f"原始股票數: {len(target_stocks)} 檔")
    print(f"需要收集: {len(stocks_to_collect)} 檔")
    print(f"跳過收集: {len(stocks_skipped)} 檔")
    print(f"節省API請求: {api_requests_saved} 次")
    
    if api_requests_saved > 0:
        efficiency = (api_requests_saved / len(target_stocks)) * 100
        print(f"效率提升: {efficiency:.1f}%")
        print(f"💡 跳過功能大幅提升了收集效率！")
    else:
        print(f"⚠️  所有股票都需要收集")

def main():
    """主函數"""
    print("🚀 跳過已有資料功能完整測試")
    print("="*70)
    
    # 測試不同場景
    test_skip_scenarios()
    
    # 顯示資料庫統計
    test_database_stats()
    
    # 模擬收集過程
    simulate_collection_with_skip()
    
    print("\n" + "="*70)
    print("✅ 測試完成！")
    print("="*70)

if __name__ == "__main__":
    main()
