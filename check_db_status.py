#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的資料庫狀態查詢腳本
"""

import sqlite3
import os
from datetime import datetime

def check_database_status():
    """檢查資料庫狀態"""
    db_path = "data/taiwan_stock.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    print("=" * 60)
    print("📊 台股資料庫狀態檢查")
    print("=" * 60)
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查資料庫大小
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        print(f"📁 資料庫大小: {db_size:.1f} MB")
        print()
        
        # 檢查各表的資料量
        tables = [
            ('stocks', '股票基本資料'),
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '綜合損益表'),
            ('balance_sheets', '資產負債表'),
            ('dividend_policies', '股利政策'),
            ('financial_ratios', '財務比率'),
            ('stock_scores', '潛力股評分')
        ]
        
        print("📊 資料表統計:")
        print("-" * 40)
        
        for table_name, table_desc in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"{table_desc:12}: {count:>8,} 筆")
            except sqlite3.OperationalError:
                print(f"{table_desc:12}: {'表不存在':>8}")
        
        print()
        
        # 檢查股價資料的日期範圍
        try:
            cursor.execute("SELECT MIN(date), MAX(date), COUNT(DISTINCT stock_id) FROM stock_prices")
            result = cursor.fetchone()
            if result[0]:
                print("📅 股價資料範圍:")
                print(f"   最早日期: {result[0]}")
                print(f"   最新日期: {result[1]}")
                print(f"   涵蓋股票: {result[2]} 檔")
                print()
        except:
            pass
        
        # 檢查最近的資料更新
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM stock_prices 
                WHERE created_at > datetime('now', '-1 day')
            """)
            recent_count = cursor.fetchone()[0]
            print(f"📈 最近24小時新增股價資料: {recent_count:,} 筆")
            
            cursor.execute("""
                SELECT COUNT(*) FROM stock_prices 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            hourly_count = cursor.fetchone()[0]
            print(f"📈 最近1小時新增股價資料: {hourly_count:,} 筆")
            print()
        except:
            pass
        
        # 檢查潛力股分析狀況
        try:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN total_score >= 75 THEN 1 END) as excellent,
                    COUNT(CASE WHEN total_score >= 60 AND total_score < 75 THEN 1 END) as good,
                    COUNT(CASE WHEN total_score < 60 THEN 1 END) as average,
                    COUNT(*) as total
                FROM stock_scores
            """)
            scores = cursor.fetchone()
            if scores[3] > 0:
                print("🎯 潛力股分析分布:")
                print(f"   優質股票(75+分): {scores[0]} 檔")
                print(f"   良好股票(60-74分): {scores[1]} 檔")
                print(f"   一般股票(<60分): {scores[2]} 檔")
                print(f"   總計已分析: {scores[3]} 檔")
                print()
        except:
            pass
        
        # 檢查市場分布
        try:
            cursor.execute("""
                SELECT market, COUNT(*) 
                FROM stocks 
                WHERE market IS NOT NULL 
                GROUP BY market 
                ORDER BY COUNT(*) DESC
            """)
            markets = cursor.fetchall()
            if markets:
                print("🏢 市場分布:")
                market_names = {'TWSE': '上市', 'TPEX': '上櫃', 'EMERGING': '興櫃'}
                for market, count in markets:
                    market_name = market_names.get(market, market)
                    print(f"   {market_name}: {count} 檔")
                print()
        except:
            pass
        
        conn.close()
        
        print("=" * 60)
        print("✅ 資料庫狀態檢查完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 檢查資料庫時發生錯誤: {e}")

if __name__ == "__main__":
    check_database_status()
