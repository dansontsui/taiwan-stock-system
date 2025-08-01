#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
from pathlib import Path
import traceback

def debug_query():
    """調試查詢問題"""
    db_path = Path('data/taiwan_stock.db')
    
    if not db_path.exists():
        print('❌ 資料庫檔案不存在')
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        # 測試簡單查詢
        print("🔍 測試簡單查詢...")
        simple_query = "SELECT COUNT(*) as count FROM stock_prices"
        result = pd.read_sql_query(simple_query, conn)
        print(f"✅ 簡單查詢成功，總筆數: {result.iloc[0]['count']:,}")
        
        # 測試帶參數的查詢 - 使用原始方法
        print("\n🔍 測試帶參數查詢 (原始方法)...")
        stock_id = "6146"
        start_date = "2024-01-01"
        end_date = "2024-03-31"
        
        query = """
        SELECT date, open_price, high_price, low_price, close_price, volume
        FROM stock_prices 
        WHERE stock_id = ? AND date >= ? AND date <= ?
        ORDER BY date
        """
        
        try:
            result = pd.read_sql_query(query, conn, params=(stock_id, start_date, end_date))
            print(f"✅ 帶參數查詢成功，找到 {len(result)} 筆資料")
            if len(result) > 0:
                print("前 3 筆資料:")
                print(result.head(3).to_string(index=False))
        except Exception as e:
            print(f"❌ 帶參數查詢失敗: {e}")
            print("完整錯誤訊息:")
            traceback.print_exc()
            
            # 嘗試不同的參數傳遞方式
            print("\n🔍 嘗試不同的參數傳遞方式...")
            try:
                # 方法 1: 使用字典
                result = pd.read_sql_query(query, conn, params={'stock_id': stock_id, 'start_date': start_date, 'end_date': end_date})
                print("✅ 字典參數方式成功")
            except Exception as e2:
                print(f"❌ 字典參數方式失敗: {e2}")
                
                # 方法 2: 使用列表
                try:
                    result = pd.read_sql_query(query, conn, params=[stock_id, start_date, end_date])
                    print("✅ 列表參數方式成功")
                except Exception as e3:
                    print(f"❌ 列表參數方式失敗: {e3}")
                    
                    # 方法 3: 直接拼接 SQL
                    try:
                        direct_query = f"""
                        SELECT date, open_price, high_price, low_price, close_price, volume
                        FROM stock_prices 
                        WHERE stock_id = '{stock_id}' AND date >= '{start_date}' AND date <= '{end_date}'
                        ORDER BY date
                        """
                        result = pd.read_sql_query(direct_query, conn)
                        print(f"✅ 直接拼接 SQL 成功，找到 {len(result)} 筆資料")
                    except Exception as e4:
                        print(f"❌ 直接拼接 SQL 失敗: {e4}")
        
        # 檢查 pandas 版本
        print(f"\n📦 Pandas 版本: {pd.__version__}")
        
        conn.close()
        
    except Exception as e:
        print(f'❌ 連接資料庫時發生錯誤: {e}')
        traceback.print_exc()

if __name__ == '__main__':
    debug_query()
