#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
個股資料缺失查詢工具
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def check_stock_data_coverage():
    """檢查個股資料覆蓋情況"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print('❌ 找不到資料庫檔案')
        return

    print('🔍 台股個股資料缺失查詢')
    print('=' * 60)
    print(f'📅 查詢時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    conn = sqlite3.connect(str(db_path))
    
    try:
        # 1. 獲取所有活躍股票清單
        stock_query = """
        SELECT stock_id, stock_name, market
        FROM stocks 
        WHERE is_active = 1 AND stock_id NOT LIKE '00%'
        AND stock_id GLOB '[0-9]*'
        ORDER BY stock_id
        """
        cursor = conn.cursor()
        cursor.execute(stock_query)
        stocks = cursor.fetchall()
        total_stocks = len(stocks)
        print(f'📊 總股票數: {total_stocks:,} 檔')
        
        stock_ids = [stock[0] for stock in stocks]
        
        # 2. 檢查各資料表
        tables_to_check = [
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'), 
            ('financial_statements', '財務報表資料'),
            ('dividend_policies', '股利政策資料'),
            ('stock_scores', '潛力股分析'),
            ('dividend_results', '除權除息'),
            ('cash_flow_statements', '現金流量表')
        ]

        print('📈 各資料表覆蓋情況:')
        print('-' * 60)
        
        missing_data = {}
        coverage_stats = {}
        
        for table_name, table_desc in tables_to_check:
            # 檢查資料表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f'{table_desc:15} : ❌ 資料表不存在')
                missing_data[table_desc] = stock_ids.copy()
                coverage_stats[table_desc] = {'coverage': 0.0, 'missing': total_stocks, 'records': 0}
                continue
            
            # 獲取有資料的股票
            cursor.execute(f"SELECT DISTINCT stock_id FROM {table_name}")
            has_data_stocks = [row[0] for row in cursor.fetchall()]
            
            # 總記錄數
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            total_records = cursor.fetchone()[0]
            
            # 計算缺失的股票
            missing_stocks = [stock_id for stock_id in stock_ids if stock_id not in has_data_stocks]
            
            coverage_rate = ((total_stocks - len(missing_stocks)) / total_stocks) * 100
            missing_count = len(missing_stocks)
            
            # 狀態圖示
            if coverage_rate >= 95:
                status = '🟢'
            elif coverage_rate >= 80:
                status = '🟡'
            elif coverage_rate >= 50:
                status = '🟠'
            else:
                status = '🔴'
            
            print(f'{table_desc:15} : {status} {coverage_rate:5.1f}% ({total_stocks-missing_count:,}/{total_stocks:,}) - {total_records:,} 筆記錄')
            
            coverage_stats[table_desc] = {
                'coverage': coverage_rate,
                'missing': missing_count,
                'records': total_records
            }
            
            if missing_count > 0:
                missing_data[table_desc] = missing_stocks

        # 3. 顯示缺失最嚴重的資料表
        print('\n⚠️  資料缺失最嚴重的項目:')
        print('-' * 60)
        
        sorted_coverage = sorted(coverage_stats.items(), key=lambda x: x[1]['coverage'])
        for table_desc, stats in sorted_coverage[:3]:
            missing_rate = 100 - stats['coverage']
            print(f'{table_desc:15} : 缺失 {stats["missing"]:,} 檔 ({missing_rate:.1f}%)')

        # 4. 顯示缺失資料最多的股票（前20檔）
        if missing_data:
            print('\n🔍 缺失資料最多的個股 (前20檔):')
            print('-' * 60)
            
            # 計算每檔股票缺失的資料表數量
            stock_missing_count = {}
            for table_desc, missing_stocks in missing_data.items():
                for stock_id in missing_stocks:
                    if stock_id not in stock_missing_count:
                        stock_missing_count[stock_id] = []
                    stock_missing_count[stock_id].append(table_desc)
            
            # 排序並顯示
            sorted_missing = sorted(stock_missing_count.items(), 
                                  key=lambda x: len(x[1]), reverse=True)
            
            for i, (stock_id, missing_tables) in enumerate(sorted_missing[:20]):
                # 獲取股票名稱
                stock_info = next((s for s in stocks if s[0] == stock_id), None)
                stock_name = stock_info[1] if stock_info else '未知'
                market = stock_info[2] if stock_info else '未知'
                missing_count = len(missing_tables)
                
                # 狀態圖示
                if missing_count <= 2:
                    status = '🟡'
                elif missing_count <= 4:
                    status = '🟠'
                else:
                    status = '🔴'
                
                print(f'{i+1:2}. {status} {stock_id} ({stock_name}) [{market}] - 缺失 {missing_count}/7 項')
                
                if missing_count <= 4:  # 只顯示缺失項目較少的詳細資訊
                    print(f'     缺失項目: {", ".join(missing_tables)}')

        # 5. 資料完整度統計
        print('\n📊 資料完整度統計:')
        print('-' * 60)
        
        complete_stocks = 0  # 7項資料都完整的股票
        partial_stocks = 0   # 部分資料缺失的股票
        empty_stocks = 0     # 大部分資料缺失的股票
        
        if missing_data:
            stock_missing_count = {}
            for table_desc, missing_stocks in missing_data.items():
                for stock_id in missing_stocks:
                    stock_missing_count[stock_id] = stock_missing_count.get(stock_id, 0) + 1
            
            for stock_id in stock_ids:
                missing_count = stock_missing_count.get(stock_id, 0)
                if missing_count == 0:
                    complete_stocks += 1
                elif missing_count <= 3:
                    partial_stocks += 1
                else:
                    empty_stocks += 1
        else:
            complete_stocks = total_stocks
        
        print(f'🟢 資料完整 (0項缺失)    : {complete_stocks:4,} 檔 ({complete_stocks/total_stocks*100:.1f}%)')
        print(f'🟡 部分缺失 (1-3項缺失)  : {partial_stocks:4,} 檔 ({partial_stocks/total_stocks*100:.1f}%)')
        print(f'🔴 大量缺失 (4+項缺失)   : {empty_stocks:4,} 檔 ({empty_stocks/total_stocks*100:.1f}%)')

        # 6. 建議收集優先順序
        print('\n💡 建議資料收集優先順序:')
        print('-' * 60)
        
        priority_order = [
            ('除權除息', '影響股價計算準確性'),
            ('現金流量表', '完善財務分析基礎'),
            ('股利政策資料', '提升投資決策品質'),
            ('月營收資料', '補強營運表現追蹤'),
            ('財務報表資料', '強化基本面分析'),
            ('潛力股分析', '提供投資建議'),
            ('股價資料', '維持資料完整性')
        ]
        
        for i, (item, reason) in enumerate(priority_order, 1):
            if item in coverage_stats:
                coverage = coverage_stats[item]['coverage']
                if coverage < 95:
                    status = '🔴' if coverage < 50 else '🟡'
                    print(f'{i}. {status} {item:12} ({coverage:5.1f}%) - {reason}')

    except Exception as e:
        print(f'❌ 查詢過程發生錯誤: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print()
    print('✅ 個股資料缺失查詢完成')
    print('💡 提示: 可使用 python start.py daily 進行增量資料更新')

def check_specific_stock(stock_id):
    """檢查特定股票的資料情況"""
    db_path = Path('data/taiwan_stock.db')
    if not db_path.exists():
        print('❌ 找不到資料庫檔案')
        return

    conn = sqlite3.connect(str(db_path))
    
    try:
        # 檢查股票是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT stock_id, stock_name, market FROM stocks WHERE stock_id = ?", (stock_id,))
        stock_info = cursor.fetchone()
        
        if not stock_info:
            print(f'❌ 找不到股票代碼: {stock_id}')
            return
        
        stock_name = stock_info[1]
        market = stock_info[2]
        
        print(f'🔍 個股資料查詢: {stock_id} ({stock_name}) [{market}]')
        print('=' * 60)
        
        tables_to_check = [
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'), 
            ('financial_statements', '財務報表資料'),
            ('dividend_policies', '股利政策資料'),
            ('stock_scores', '潛力股分析'),
            ('dividend_results', '除權除息'),
            ('cash_flow_statements', '現金流量表')
        ]
        
        for table_name, table_desc in tables_to_check:
            # 檢查資料表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f'{table_desc:15} : ❌ 資料表不存在')
                continue
            
            # 檢查該股票是否有資料
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?", (stock_id,))
            record_count = cursor.fetchone()[0]
            
            if record_count > 0:
                # 獲取最新資料日期
                try:
                    cursor.execute(f"SELECT MAX(date) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                    latest_date = cursor.fetchone()[0]
                except:
                    try:
                        cursor.execute(f"SELECT MAX(analysis_date) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                        latest_date = cursor.fetchone()[0]
                    except:
                        latest_date = '無日期'
                
                print(f'{table_desc:15} : ✅ {record_count:,} 筆記錄 (最新: {latest_date})')
            else:
                print(f'{table_desc:15} : ❌ 無資料')
    
    except Exception as e:
        print(f'❌ 查詢過程發生錯誤: {e}')
    
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 查詢特定股票
        stock_id = sys.argv[1]
        check_specific_stock(stock_id)
    else:
        # 查詢整體情況
        check_stock_data_coverage()
