#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速狀態檢查腳本
"""

import sys
import os
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.utils.simple_database import SimpleDatabaseManager

def get_quick_status():
    """獲取快速狀態"""
    db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📊 台股資料收集狀態 - 快速檢查")
    print("=" * 60)
    print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 基本統計
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
        ('stock_scores', '潛力股評分')
    ]
    
    print("📈 資料收集統計:")
    print("-" * 40)
    
    total_stocks = 0
    for table, name in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{name:<15}: {count:>10,} 筆")
            
            if table == 'stocks':
                total_stocks = count
        except:
            print(f"{name:<15}: {'表格不存在':>10}")
    
    print()
    print("📊 資料覆蓋率分析:")
    print("-" * 40)
    
    if total_stocks > 0:
        # 檢查各類資料的覆蓋率
        coverage_tables = [
            ('stock_prices', '股價資料'),
            ('monthly_revenues', '月營收資料'),
            ('financial_statements', '綜合損益表'),
            ('cash_flow_statements', '現金流量表'),
            ('dividend_results', '除權息結果')
        ]
        
        for table, name in coverage_tables:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT stock_id) FROM {table}")
                covered_stocks = cursor.fetchone()[0]
                coverage_rate = (covered_stocks / total_stocks * 100) if total_stocks > 0 else 0
                print(f"{name:<15}: {covered_stocks:>4} / {total_stocks} ({coverage_rate:>5.1f}%)")
            except:
                print(f"{name:<15}: {'檢查失敗':>15}")
    
    print()
    print("⏰ 最新資料時間:")
    print("-" * 40)
    
    # 檢查最新資料時間
    try:
        cursor.execute("SELECT MAX(date) FROM stock_prices")
        latest_price = cursor.fetchone()[0]
        print(f"股價資料最新日期: {latest_price}")
    except:
        print("股價資料: 無資料")
    
    try:
        cursor.execute("SELECT MAX(revenue_year), MAX(revenue_month) FROM monthly_revenues WHERE revenue_year = (SELECT MAX(revenue_year) FROM monthly_revenues)")
        latest_revenue = cursor.fetchone()
        if latest_revenue[0]:
            print(f"營收資料最新: {latest_revenue[0]}年{latest_revenue[1]}月")
        else:
            print("營收資料: 無資料")
    except:
        print("營收資料: 無資料")
    
    try:
        cursor.execute("SELECT MAX(date) FROM financial_statements")
        latest_financial = cursor.fetchone()[0]
        print(f"財務報表最新日期: {latest_financial}")
    except:
        print("財務報表: 無資料")
    
    conn.close()
    
    print()
    print("=" * 60)
    print("💡 提示:")
    print("- 如需詳細監控，請執行: python monitor_collection.py")
    print("- 如需啟動收集，請執行: python scripts/collect_comprehensive_batch.py")
    print("- 如需Web介面，請執行: python run.py")
    print("=" * 60)

if __name__ == "__main__":
    get_quick_status()
