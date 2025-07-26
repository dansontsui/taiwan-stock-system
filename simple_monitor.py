#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版監控系統 - 即時顯示收集進度
"""

import sys
import os
import time
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager

def get_data_statistics():
    """獲取資料統計"""
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    tables = [
        ('stocks', '股票基本資料'),
        ('stock_prices', '股價資料'),
        ('monthly_revenues', '月營收資料'),
        ('financial_statements', '綜合損益表'),
        ('balance_sheets', '資產負債表'),
        ('cash_flow_statements', '現金流量表'),
        ('dividend_policies', '股利政策'),
        ('dividend_results', '除權息結果'),
        ('financial_ratios', '財務比率'),
        ('stock_scores', '潛力股評分'),
        ('technical_indicators', '技術指標'),
        ('etf_dividends', 'ETF配息'),
        ('data_updates', '資料更新記錄')
    ]
    
    stats = {}
    for table, name in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[name] = count
        except:
            stats[name] = 0
    
    # 獲取最新資料時間
    try:
        cursor.execute("SELECT MAX(date) FROM stock_prices")
        latest_price = cursor.fetchone()[0]
        stats['最新股價時間'] = latest_price
    except:
        stats['最新股價時間'] = 'N/A'
    
    try:
        cursor.execute("SELECT MAX(revenue_year), MAX(revenue_month) FROM monthly_revenues WHERE revenue_year = (SELECT MAX(revenue_year) FROM monthly_revenues)")
        latest_revenue = cursor.fetchone()
        if latest_revenue[0]:
            stats['最新營收時間'] = f"{latest_revenue[0]}年{latest_revenue[1]}月"
        else:
            stats['最新營收時間'] = 'N/A'
    except:
        stats['最新營收時間'] = 'N/A'
    
    conn.close()
    return stats

def display_progress():
    """顯示進度"""
    print("=" * 60)
    print("📊 台股資料收集 - 即時監控")
    print("=" * 60)
    print("⏰ 啟動時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔄 更新頻率: 30秒")
    print("💡 按 Ctrl+C 停止監控")
    print("=" * 60)
    
    try:
        while True:
            # 清除螢幕
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("=" * 60)
            print("📊 台股資料收集 - 即時監控")
            print("=" * 60)
            print(f"⏰ 監控時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # 獲取統計資料
            stats = get_data_statistics()
            
            print("📈 資料收集統計:")
            print("-" * 40)
            
            for name, count in stats.items():
                if name not in ['最新股價時間', '最新營收時間']:
                    print(f"{name:<15}: {count:>10,} 筆")
            
            print()
            print("⏰ 最新資料時間:")
            print("-" * 40)
            print(f"股價資料: {stats['最新股價時間']}")
            print(f"營收資料: {stats['最新營收時間']}")
            
            print()
            print("📊 資料覆蓋率分析:")
            print("-" * 40)
            
            # 計算覆蓋率
            total_stocks = stats['股票基本資料']
            if total_stocks > 0:
                # 計算各類資料的覆蓋率
                coverage_tables = [
                    ('股價資料', 'stock_prices'),
                    ('月營收資料', 'monthly_revenues'),
                    ('綜合損益表', 'financial_statements'),
                    ('現金流量表', 'cash_flow_statements'),
                    ('除權息結果', 'dividend_results')
                ]
                
                db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                for name, table in coverage_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(DISTINCT stock_id) FROM {table}")
                        covered_stocks = cursor.fetchone()[0]
                        coverage_rate = (covered_stocks / total_stocks * 100) if total_stocks > 0 else 0
                        print(f"{name:<15}: {covered_stocks:>4} / {total_stocks} ({coverage_rate:>5.1f}%)")
                    except:
                        print(f"{name:<15}: {'檢查失敗':>15}")
                
                conn.close()
            
            print()
            print("=" * 60)
            print("💡 提示:")
            print("- 如需啟動收集，請執行: python scripts/collect_comprehensive_batch.py")
            print("- 如需Web介面，請執行: python run.py")
            print("- 按 Ctrl+C 停止監控")
            print("=" * 60)
            
            # 等待30秒
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n👋 監控已停止")
                break
                
    except KeyboardInterrupt:
        print("\n👋 監控已停止")

if __name__ == "__main__":
    display_progress()
