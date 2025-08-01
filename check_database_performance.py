#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫效能問題
"""

import sqlite3
import time

def check_database():
    """檢查資料庫效能"""
    db_path = 'data/taiwan_stock.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查資料庫效能問題...")
        
        # 1. 檢查索引
        cursor.execute("PRAGMA index_list(stock_prices)")
        indexes = cursor.fetchall()
        print(f"🔗 stock_prices 索引: {[i[1] for i in indexes]}")
        
        # 2. 測試查詢效能
        print("\n⏱️ 測試查詢效能...")
        
        queries = [
            ("股票數量", "SELECT COUNT(DISTINCT stock_id) FROM stock_prices WHERE stock_id LIKE '1%'"),
            ("最新日期", "SELECT MAX(date) FROM stock_prices"),
            ("最舊日期", "SELECT MIN(date) FROM stock_prices"),
            ("樣本資料", "SELECT stock_id, date, close_price FROM stock_prices LIMIT 5"),
            ("12xx股票", "SELECT DISTINCT stock_id FROM stock_prices WHERE stock_id LIKE '12%' LIMIT 10"),
            ("14xx股票", "SELECT DISTINCT stock_id FROM stock_prices WHERE stock_id LIKE '14%' LIMIT 10"),
        ]
        
        for name, query in queries:
            print(f"  🔍 {name}...")
            start_time = time.time()
            
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                elapsed_time = time.time() - start_time
                
                print(f"    ✅ 完成，耗時: {elapsed_time:.3f} 秒")
                if name in ["樣本資料", "12xx股票", "14xx股票"]:
                    print(f"    📋 結果: {result[:5]}")
                else:
                    print(f"    📈 結果: {result[0] if result else 'No data'}")
                    
                # 如果查詢時間過長，停止測試
                if elapsed_time > 30:
                    print(f"    ⚠️  查詢時間過長，停止後續測試")
                    break
                    
            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"    ❌ 失敗，耗時: {elapsed_time:.3f} 秒，錯誤: {e}")
        
        # 3. 檢查資料庫大小
        print("\n📊 檢查資料庫資訊...")
        
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        db_size_mb = (page_count * page_size) / (1024 * 1024)
        print(f"📈 資料庫大小: {db_size_mb:.2f} MB")
        print(f"📋 頁面數量: {page_count:,}")
        print(f"📋 頁面大小: {page_size} bytes")
        
        # 4. 檢查表格大小
        cursor.execute("SELECT COUNT(*) FROM stock_prices WHERE rowid <= 1000")
        sample_count = cursor.fetchone()[0]
        print(f"📈 前1000行記錄數: {sample_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")

if __name__ == "__main__":
    check_database()
