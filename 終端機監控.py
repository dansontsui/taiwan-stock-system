#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股分析系統終端機監控
提供即時的終端機介面監控，不需要Web瀏覽器
"""

import sys
import os
import time
import sqlite3
from datetime import datetime, timedelta
import argparse

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """顯示標題"""
    print("=" * 80)
    print("📊 台股分析系統終端機監控")
    print("=" * 80)
    print(f"🕐 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def get_database_stats():
    """獲取資料庫統計"""
    try:
        # 嘗試使用config
        try:
            from config import Config
            db_path = Config.DATABASE_PATH
        except:
            db_path = "data/taiwan_stock.db"
        
        if not os.path.exists(db_path):
            return None, "資料庫檔案不存在"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = [
            ('stocks', '股票基本資料'),
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '綜合損益表'),
            ('balance_sheets', '資產負債表'),
            ('cash_flow_statements', '現金流量表'),
            ('dividend_results', '除權除息結果'),
            ('dividend_policies', '股利政策'),
            ('financial_ratios', '財務比率'),
            ('stock_scores', '潛力股評分')
        ]
        
        stats = {}
        total_records = 0
        
        for table_name, display_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[display_name] = count
                total_records += count
            except:
                stats[display_name] = 0
        
        # 獲取最新更新時間
        latest_updates = {}
        for table_name, display_name in tables:
            try:
                if table_name == 'stock_prices':
                    cursor.execute(f"SELECT MAX(date) FROM {table_name}")
                elif table_name == 'monthly_revenues':
                    cursor.execute(f"SELECT MAX(revenue_year || '-' || printf('%02d', revenue_month)) FROM {table_name}")
                else:
                    cursor.execute(f"SELECT MAX(date) FROM {table_name}")
                
                latest = cursor.fetchone()[0]
                latest_updates[display_name] = latest if latest else "無資料"
            except:
                latest_updates[display_name] = "無資料"
        
        conn.close()
        return (stats, latest_updates, total_records), None
        
    except Exception as e:
        return None, f"資料庫連接失敗: {e}"

def get_top_stocks():
    """獲取熱門股票"""
    try:
        try:
            from config import Config
            db_path = Config.DATABASE_PATH
        except:
            db_path = "data/taiwan_stock.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取有評分的股票
        cursor.execute("""
            SELECT s.stock_id, s.stock_name, ss.total_score
            FROM stocks s
            JOIN stock_scores ss ON s.stock_id = ss.stock_id
            ORDER BY ss.total_score DESC
            LIMIT 10
        """)
        
        top_stocks = cursor.fetchall()
        conn.close()
        
        return top_stocks
        
    except Exception as e:
        return []

def get_recent_activity():
    """獲取最近活動"""
    try:
        try:
            from config import Config
            db_path = Config.DATABASE_PATH
        except:
            db_path = "data/taiwan_stock.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        activities = []
        
        # 檢查最近的股價更新
        try:
            cursor.execute("""
                SELECT stock_id, date, COUNT(*) as count
                FROM stock_prices
                WHERE date >= date('now', '-7 days')
                GROUP BY stock_id, date
                ORDER BY date DESC
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                activities.append(f"📈 {row[0]} 股價更新 {row[2]} 筆 ({row[1]})")
        except:
            pass
        
        # 檢查最近的營收更新
        try:
            cursor.execute("""
                SELECT stock_id, revenue_year, revenue_month, revenue
                FROM monthly_revenues
                ORDER BY revenue_year DESC, revenue_month DESC
                LIMIT 3
            """)
            
            for row in cursor.fetchall():
                activities.append(f"📊 {row[0]} 營收更新 {row[1]}/{row[2]:02d} ({row[3]:,.0f})")
        except:
            pass
        
        conn.close()
        return activities[:10]
        
    except Exception as e:
        return [f"❌ 獲取活動失敗: {e}"]

def display_dashboard():
    """顯示儀表板"""
    clear_screen()
    print_header()
    
    # 獲取資料庫統計
    db_result, error = get_database_stats()
    
    if error:
        print(f"❌ {error}")
        return
    
    stats, latest_updates, total_records = db_result
    
    # 顯示資料庫統計
    print("📊 資料庫統計")
    print("-" * 40)
    for name, count in stats.items():
        latest = latest_updates.get(name, "無資料")
        print(f"{name:<15} {count:>8,} 筆  (最新: {latest})")
    
    print("-" * 40)
    print(f"{'總計':<15} {total_records:>8,} 筆")
    
    # 顯示熱門股票
    print("\n🏆 潛力股排行榜")
    print("-" * 40)
    top_stocks = get_top_stocks()
    
    if top_stocks:
        for i, (stock_id, stock_name, score) in enumerate(top_stocks, 1):
            print(f"{i:2d}. {stock_id} {stock_name:<10} {score:>6.1f}分")
    else:
        print("   暫無評分資料")
    
    # 顯示最近活動
    print("\n📈 最近活動")
    print("-" * 40)
    activities = get_recent_activity()
    
    if activities:
        for activity in activities:
            print(f"   {activity}")
    else:
        print("   暫無最近活動")
    
    print("\n" + "=" * 80)
    print("💡 按 Ctrl+C 停止監控 | 每30秒自動更新")
    print("=" * 80)

def monitor_mode():
    """監控模式"""
    print("🚀 啟動終端機監控模式...")
    print("💡 按 Ctrl+C 可隨時停止")
    time.sleep(2)
    
    try:
        while True:
            display_dashboard()
            time.sleep(30)  # 每30秒更新一次
    except KeyboardInterrupt:
        clear_screen()
        print("👋 監控已停止")

def single_view():
    """單次查看模式"""
    display_dashboard()
    input("\n按 Enter 鍵退出...")

def show_detailed_stats():
    """顯示詳細統計"""
    clear_screen()
    print_header()
    
    db_result, error = get_database_stats()
    
    if error:
        print(f"❌ {error}")
        return
    
    stats, latest_updates, total_records = db_result
    
    print("📊 詳細資料庫統計")
    print("=" * 60)
    
    for name, count in stats.items():
        latest = latest_updates.get(name, "無資料")
        percentage = (count / total_records * 100) if total_records > 0 else 0
        
        print(f"📋 {name}")
        print(f"   記錄數量: {count:,} 筆 ({percentage:.1f}%)")
        print(f"   最新資料: {latest}")
        print(f"   狀態: {'✅ 有資料' if count > 0 else '❌ 無資料'}")
        print()
    
    print("=" * 60)
    print(f"總計: {total_records:,} 筆記錄")
    
    input("\n按 Enter 鍵返回...")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='台股分析系統終端機監控')
    parser.add_argument('--mode', choices=['monitor', 'view', 'stats'], 
                       default='monitor', help='運行模式')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'monitor':
            monitor_mode()
        elif args.mode == 'view':
            single_view()
        elif args.mode == 'stats':
            show_detailed_stats()
    except KeyboardInterrupt:
        print("\n👋 程式已退出")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")

if __name__ == "__main__":
    main()
