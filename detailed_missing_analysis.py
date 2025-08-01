#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細的資料庫缺失分析
"""

import sqlite3
from pathlib import Path

def detailed_analysis():
    """詳細分析資料庫缺失情況"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print('找不到資料庫檔案')
        return

    print('台股資料庫詳細缺失分析')
    print('=' * 80)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 1. 獲取所有活躍股票清單
        cursor.execute("""
        SELECT stock_id, stock_name, market
        FROM stocks 
        WHERE is_active = 1 AND stock_id NOT LIKE '00%'
        AND stock_id GLOB '[0-9]*'
        ORDER BY stock_id
        """)
        stocks = cursor.fetchall()
        total_stocks = len(stocks)
        print(f'總股票數: {total_stocks} 檔')
        
        # 2. 各資料表統計
        tables_info = [
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'), 
            ('financial_statements', '財務報表資料'),
            ('dividend_policies', '股利政策資料'),
            ('stock_scores', '潛力股分析'),
            ('dividend_results', '除權除息'),
            ('cash_flow_statements', '現金流量表')
        ]

        print('\n各資料表詳細統計:')
        print('-' * 80)
        
        for table_name, table_desc in tables_info:
            # 檢查資料表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f'{table_desc:15} : 資料表不存在')
                continue
            
            # 總記錄數
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            total_records = cursor.fetchone()[0]
            
            # 有資料的股票數量
            cursor.execute(f'SELECT COUNT(DISTINCT stock_id) FROM {table_name}')
            stock_count = cursor.fetchone()[0]
            
            # 覆蓋率
            coverage_rate = (stock_count / total_stocks) * 100
            missing_count = total_stocks - stock_count
            
            print(f'{table_desc:15} : {total_records:8,} 筆記錄, {stock_count:4} 檔股票 ({coverage_rate:5.1f}%), {missing_count:4} 檔缺失')

        # 3. 找出完全沒有資料的股票
        print('\n完全沒有任何資料的股票:')
        print('-' * 80)
        
        stock_ids = [stock[0] for stock in stocks]
        
        # 檢查每檔股票在各資料表的情況
        stocks_with_no_data = []
        
        for stock_id, stock_name, market in stocks:
            has_any_data = False
            
            for table_name, _ in tables_info:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    continue
                    
                cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?', (stock_id,))
                if cursor.fetchone()[0] > 0:
                    has_any_data = True
                    break
            
            if not has_any_data:
                stocks_with_no_data.append((stock_id, stock_name, market))
        
        if stocks_with_no_data:
            print(f'發現 {len(stocks_with_no_data)} 檔股票完全沒有資料:')
            for i, (stock_id, stock_name, market) in enumerate(stocks_with_no_data[:20]):
                print(f'{i+1:2}. {stock_id} ({stock_name}) [{market}]')
            if len(stocks_with_no_data) > 20:
                print(f'... 還有 {len(stocks_with_no_data) - 20} 檔')
        else:
            print('所有股票都至少有一種資料')

        # 4. 各資料表缺失的具體股票（前20檔）
        print('\n各資料表缺失股票詳情:')
        print('-' * 80)
        
        for table_name, table_desc in tables_info:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                continue
            
            # 獲取有資料的股票
            cursor.execute(f'SELECT DISTINCT stock_id FROM {table_name}')
            has_data_stocks = {row[0] for row in cursor.fetchall()}
            
            # 找出缺失的股票
            missing_stocks = []
            for stock_id, stock_name, market in stocks:
                if stock_id not in has_data_stocks:
                    missing_stocks.append((stock_id, stock_name, market))
            
            if missing_stocks:
                print(f'\n{table_desc} - 缺失 {len(missing_stocks)} 檔股票:')
                for i, (stock_id, stock_name, market) in enumerate(missing_stocks[:20]):
                    print(f'  {i+1:2}. {stock_id} ({stock_name}) [{market}]')
                if len(missing_stocks) > 20:
                    print(f'  ... 還有 {len(missing_stocks) - 20} 檔')

        # 5. 資料最完整的股票（前10檔）
        print('\n資料最完整的股票 (前10檔):')
        print('-' * 80)
        
        stock_completeness = []
        
        for stock_id, stock_name, market in stocks:
            data_count = 0
            
            for table_name, _ in tables_info:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    continue
                    
                cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?', (stock_id,))
                if cursor.fetchone()[0] > 0:
                    data_count += 1
            
            stock_completeness.append((stock_id, stock_name, market, data_count))
        
        # 排序並顯示
        stock_completeness.sort(key=lambda x: x[3], reverse=True)
        
        for i, (stock_id, stock_name, market, data_count) in enumerate(stock_completeness[:10]):
            completeness_rate = (data_count / len(tables_info)) * 100
            print(f'{i+1:2}. {stock_id} ({stock_name}) [{market}] - {data_count}/7 項資料 ({completeness_rate:.1f}%)')

    except Exception as e:
        print(f'分析過程發生錯誤: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print('\n詳細分析完成')

if __name__ == '__main__':
    detailed_analysis()
