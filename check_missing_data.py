#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫中各重要資料表的缺失情況
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# 設置輸出編碼
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    except:
        pass  # 如果設置失敗就跳過

def check_missing_data():
    """檢查各資料表的缺失情況"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print('❌ 找不到資料庫檔案')
        return

    print('🔍 台股資料庫缺失資料分析')
    print('=' * 80)
    print(f'📅 分析時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    conn = sqlite3.connect(str(db_path))
    
    try:
        # 1. 獲取所有活躍股票清單
        print('📊 獲取股票清單...')
        stock_query = """
        SELECT stock_id, stock_name, market, industry
        FROM stocks 
        WHERE is_active = 1 AND stock_id NOT LIKE '00%'
        ORDER BY stock_id
        """
        stocks_df = pd.read_sql_query(stock_query, conn)
        # 過濾只包含數字的股票代碼
        stocks_df = stocks_df[stocks_df['stock_id'].str.isdigit()]
        total_stocks = len(stocks_df)
        print(f'✅ 總股票數: {total_stocks:,} 檔')
        print(f'   - 上市 (TWSE): {len(stocks_df[stocks_df["market"] == "TWSE"]):,} 檔')
        print(f'   - 上櫃 (TPEX): {len(stocks_df[stocks_df["market"] == "TPEX"]):,} 檔')
        print()

        # 2. 檢查各資料表的覆蓋情況
        tables_to_check = {
            'stock_prices': '股價資料',
            'monthly_revenues': '月營收資料', 
            'financial_statements': '財務報表資料',
            'dividend_policies': '股利政策資料',
            'stock_scores': '潛力股分析',
            'dividend_results': '除權除息',
            'cash_flow_statements': '現金流量表'
        }

        missing_summary = {}
        
        for table_name, table_desc in tables_to_check.items():
            print(f'🔍 檢查 {table_desc} ({table_name})...')
            
            # 檢查資料表是否存在
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f'   ❌ 資料表不存在')
                missing_summary[table_desc] = {'missing_count': total_stocks, 'missing_stocks': list(stocks_df['stock_id'])}
                continue
            
            # 獲取有資料的股票
            has_data_query = f"""
            SELECT DISTINCT stock_id 
            FROM {table_name}
            WHERE stock_id IN ({','.join(['?' for _ in stocks_df['stock_id']])})
            """
            has_data_df = pd.read_sql_query(has_data_query, conn, params=list(stocks_df['stock_id']))
            
            # 計算缺失的股票
            has_data_stocks = set(has_data_df['stock_id'])
            all_stocks = set(stocks_df['stock_id'])
            missing_stocks = all_stocks - has_data_stocks
            
            coverage_rate = (len(has_data_stocks) / total_stocks) * 100
            missing_count = len(missing_stocks)
            
            print(f'   📈 覆蓋率: {coverage_rate:.1f}% ({len(has_data_stocks):,}/{total_stocks:,})')
            print(f'   ❌ 缺失: {missing_count:,} 檔股票')
            
            if missing_count > 0:
                missing_summary[table_desc] = {
                    'missing_count': missing_count,
                    'missing_stocks': sorted(list(missing_stocks))
                }
            
            print()

        # 3. 顯示缺失摘要
        print('📋 缺失資料摘要')
        print('=' * 80)
        
        if not missing_summary:
            print('🎉 所有資料表都有完整覆蓋！')
        else:
            for table_desc, info in missing_summary.items():
                missing_count = info['missing_count']
                missing_rate = (missing_count / total_stocks) * 100
                print(f'{table_desc:15} : {missing_count:4,} 檔缺失 ({missing_rate:5.1f}%)')
            
            print()
            
            # 4. 顯示缺失最多的股票（前20檔）
            print('🔍 缺失資料最多的股票 (前20檔):')
            print('-' * 60)
            
            # 計算每檔股票缺失的資料表數量
            stock_missing_count = {}
            for table_desc, info in missing_summary.items():
                for stock_id in info['missing_stocks']:
                    if stock_id not in stock_missing_count:
                        stock_missing_count[stock_id] = []
                    stock_missing_count[stock_id].append(table_desc)
            
            # 排序並顯示
            sorted_missing = sorted(stock_missing_count.items(), 
                                  key=lambda x: len(x[1]), reverse=True)
            
            for i, (stock_id, missing_tables) in enumerate(sorted_missing[:20]):
                stock_info = stocks_df[stocks_df['stock_id'] == stock_id].iloc[0]
                stock_name = stock_info['stock_name']
                market = stock_info['market']
                missing_count = len(missing_tables)
                
                print(f'{i+1:2}. {stock_id} ({stock_name}) [{market}] - 缺失 {missing_count} 項')
                print(f'    缺失項目: {", ".join(missing_tables)}')
                print()

        # 5. 各資料表詳細統計
        print('📊 各資料表詳細統計')
        print('=' * 80)
        
        for table_name, table_desc in tables_to_check.items():
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f'{table_desc:15} : 資料表不存在')
                continue
                
            # 總記錄數
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            total_records = cursor.fetchone()[0]
            
            # 股票數量
            cursor.execute(f'SELECT COUNT(DISTINCT stock_id) FROM {table_name}')
            stock_count = cursor.fetchone()[0]
            
            # 最新資料日期
            try:
                cursor.execute(f'SELECT MAX(date) FROM {table_name}')
                latest_date = cursor.fetchone()[0]
            except:
                try:
                    cursor.execute(f'SELECT MAX(analysis_date) FROM {table_name}')
                    latest_date = cursor.fetchone()[0]
                except:
                    latest_date = '無日期欄位'
            
            print(f'{table_desc:15} : {total_records:8,} 筆記錄, {stock_count:4,} 檔股票, 最新: {latest_date}')

    except Exception as e:
        print(f'❌ 分析過程發生錯誤: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print()
    print('✅ 缺失資料分析完成')

if __name__ == '__main__':
    check_missing_data()
