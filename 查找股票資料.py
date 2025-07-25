#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找指定股票在所有資料表中的資料
"""

import sqlite3
import sys
import os
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    db_path = Config.DATABASE_PATH
except:
    db_path = "data/taiwan_stock.db"

def get_all_tables():
    """獲取所有資料表名稱"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tables
    except Exception as e:
        print(f"❌ 獲取資料表失敗: {e}")
        return []

def check_stock_in_table(stock_id, table_name):
    """檢查股票在指定資料表中的資料"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表結構，確認是否有stock_id欄位
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'stock_id' not in columns:
            conn.close()
            return None, "無stock_id欄位"
        
        # 查詢該股票的資料數量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE stock_id = ?", (stock_id,))
        count = cursor.fetchone()[0]
        
        result = {
            'count': count,
            'columns': columns,
            'sample_data': None,
            'date_range': None
        }
        
        if count > 0:
            # 獲取範例資料 (前3筆)
            cursor.execute(f"SELECT * FROM {table_name} WHERE stock_id = ? LIMIT 3", (stock_id,))
            result['sample_data'] = cursor.fetchall()
            
            # 如果有date欄位，獲取日期範圍
            if 'date' in columns:
                cursor.execute(f"SELECT MIN(date), MAX(date) FROM {table_name} WHERE stock_id = ?", (stock_id,))
                date_range = cursor.fetchone()
                if date_range[0] and date_range[1]:
                    result['date_range'] = f"{date_range[0]} ~ {date_range[1]}"
        
        conn.close()
        return result, None
        
    except Exception as e:
        return None, str(e)

def format_sample_data(sample_data, columns, max_samples=2):
    """格式化範例資料"""
    if not sample_data:
        return "無範例資料"
    
    formatted = []
    for i, row in enumerate(sample_data[:max_samples]):
        formatted.append(f"      第{i+1}筆:")
        for j, col_name in enumerate(columns[:6]):  # 只顯示前6個欄位
            value = row[j] if j < len(row) else 'NULL'
            # 限制顯示長度
            if isinstance(value, str) and len(value) > 30:
                value = value[:30] + "..."
            formatted.append(f"        {col_name}: {value}")
        if len(columns) > 6:
            formatted.append(f"        ... (還有{len(columns)-6}個欄位)")
        formatted.append("")
    
    return "\n".join(formatted)

def search_stock_data(stock_id):
    """搜尋指定股票的所有資料"""
    print("=" * 80)
    print(f"🔍 搜尋股票 {stock_id} 在所有資料表中的資料")
    print("=" * 80)
    
    # 首先檢查股票是否存在
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT stock_id, stock_name FROM stocks WHERE stock_id = ?", (stock_id,))
        stock_info = cursor.fetchone()
        conn.close()
        
        if stock_info:
            print(f"📋 股票資訊: {stock_info[0]} - {stock_info[1]}")
        else:
            print(f"⚠️ 警告: 股票 {stock_id} 不存在於 stocks 表中")
    except:
        print(f"⚠️ 無法檢查股票基本資訊")
    
    print("=" * 80)
    
    # 獲取所有資料表
    tables = get_all_tables()
    
    if not tables:
        print("❌ 無法獲取資料表列表")
        return
    
    print(f"📊 檢查 {len(tables)} 個資料表...")
    print()
    
    # 統計結果
    has_data_tables = []
    no_data_tables = []
    no_stock_id_tables = []
    error_tables = []
    
    total_records = 0
    
    # 檢查每個資料表
    for table_name in tables:
        result, error = check_stock_in_table(stock_id, table_name)
        
        if error:
            if "無stock_id欄位" in error:
                no_stock_id_tables.append(table_name)
                print(f"⏭️  {table_name:<25} - 無stock_id欄位")
            else:
                error_tables.append((table_name, error))
                print(f"❌ {table_name:<25} - 錯誤: {error}")
        elif result:
            if result['count'] > 0:
                has_data_tables.append((table_name, result))
                total_records += result['count']
                
                print(f"✅ {table_name:<25} - {result['count']:>6,} 筆")
                if result['date_range']:
                    print(f"   📅 日期範圍: {result['date_range']}")
                
                # 顯示範例資料
                if result['sample_data']:
                    print(f"   📋 範例資料:")
                    sample_text = format_sample_data(result['sample_data'], result['columns'])
                    print(sample_text)
                
            else:
                no_data_tables.append(table_name)
                print(f"⚪ {table_name:<25} - 0 筆")
    
    # 顯示統計摘要
    print("\n" + "=" * 80)
    print("📊 統計摘要")
    print("=" * 80)
    print(f"🎯 股票代號: {stock_id}")
    print(f"📈 有資料的表: {len(has_data_tables)} 個")
    print(f"⚪ 無資料的表: {len(no_data_tables)} 個")
    print(f"⏭️  無stock_id欄位的表: {len(no_stock_id_tables)} 個")
    print(f"❌ 錯誤的表: {len(error_tables)} 個")
    print(f"📊 總資料筆數: {total_records:,} 筆")
    
    # 詳細列表
    if has_data_tables:
        print(f"\n✅ 有資料的表 ({len(has_data_tables)} 個):")
        for table_name, result in has_data_tables:
            date_info = f" ({result['date_range']})" if result['date_range'] else ""
            print(f"   • {table_name}: {result['count']:,} 筆{date_info}")
    
    if no_data_tables:
        print(f"\n⚪ 無資料的表 ({len(no_data_tables)} 個):")
        for table_name in no_data_tables:
            print(f"   • {table_name}")
    
    if no_stock_id_tables:
        print(f"\n⏭️  無stock_id欄位的表 ({len(no_stock_id_tables)} 個):")
        for table_name in no_stock_id_tables:
            print(f"   • {table_name}")
    
    if error_tables:
        print(f"\n❌ 錯誤的表 ({len(error_tables)} 個):")
        for table_name, error in error_tables:
            print(f"   • {table_name}: {error}")

def main():
    """主函數"""
    print("🔍 股票資料查找工具")
    print("=" * 80)
    
    # 檢查資料庫是否存在
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return
    
    # 獲取股票代號
    if len(sys.argv) > 1:
        stock_id = sys.argv[1].strip()
    else:
        stock_id = input("請輸入股票代號: ").strip()
    
    if not stock_id:
        print("❌ 請提供有效的股票代號")
        return
    
    # 搜尋股票資料
    search_stock_data(stock_id)
    
    print(f"\n🕐 查詢完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
