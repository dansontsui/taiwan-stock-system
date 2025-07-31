#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 c.py 存取的資料庫表格
"""

import sys
import os
import sqlite3
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    DATABASE_PATH = Config.DATABASE_PATH
except:
    DATABASE_PATH = "data/taiwan_stock.db"

def analyze_database_tables():
    """分析資料庫表格結構"""
    
    print("=" * 80)
    print("c.py 存取的資料庫表格分析")
    print("=" * 80)
    print(f"資料庫路徑: {DATABASE_PATH}")
    print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # c.py 實際存取的表格（根據 simple_collect.py 分析）
        tables_info = {
            # c.py 直接存取的表格
            'stocks': {
                'description': '股票基本資料表',
                'purpose': '儲存股票代碼、名稱、市場別、產業別等基本資訊',
                'accessed_by_c': True,
                'operation': '查詢股票清單'
            },
            'stock_prices': {
                'description': '股價資料表', 
                'purpose': '儲存每日股價資料（開高低收、成交量、成交金額等）',
                'accessed_by_c': True,
                'operation': '插入/更新股價資料'
            },
            'monthly_revenues': {
                'description': '月營收資料表',
                'purpose': '儲存公司每月營收資料及成長率',
                'accessed_by_c': True,
                'operation': '插入/更新月營收資料'
            },
            'cash_flow_statements': {
                'description': '現金流量表',
                'purpose': '儲存現金流量相關財務資料',
                'accessed_by_c': True,
                'operation': '插入/更新現金流資料'
            },
            
            # 系統中存在但 c.py 不直接存取的表格
            'technical_indicators': {
                'description': '技術指標表',
                'purpose': '儲存各種技術分析指標數值',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'etf_dividends': {
                'description': 'ETF配息表',
                'purpose': '儲存ETF配息相關資訊',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'data_updates': {
                'description': '資料更新記錄表',
                'purpose': '記錄資料更新狀態和錯誤訊息',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'market_values': {
                'description': '市值資料表',
                'purpose': '儲存市值、本益比、股價淨值比等估值指標',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'stock_splits': {
                'description': '股票分割表',
                'purpose': '記錄股票分割事件',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'dividend_results': {
                'description': '除權除息結果表',
                'purpose': '儲存除權除息實際執行結果',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'financial_statements': {
                'description': '綜合損益表',
                'purpose': '儲存損益表相關財務資料',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'balance_sheets': {
                'description': '資產負債表',
                'purpose': '儲存資產負債表相關財務資料',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'dividend_policies': {
                'description': '股利政策表',
                'purpose': '儲存股利分配政策資訊',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'financial_ratios': {
                'description': '財務比率表',
                'purpose': '儲存各種財務比率指標',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            },
            'stock_scores': {
                'description': '潛力股評分表',
                'purpose': '儲存股票評分和分析結果',
                'accessed_by_c': False,
                'operation': '由其他模組使用'
            }
        }
        
        # 統計 c.py 直接存取的表格
        c_accessed_tables = [name for name, info in tables_info.items() if info['accessed_by_c']]
        other_tables = [name for name, info in tables_info.items() if not info['accessed_by_c']]
        
        print(f"c.py 直接存取的表格數量: {len(c_accessed_tables)} 個")
        print(f"系統其他表格數量: {len(other_tables)} 個")
        print(f"資料庫總表格數量: {len(tables_info)} 個")
        print()
        
        # 顯示 c.py 直接存取的表格詳細資訊
        print("=" * 80)
        print("c.py 直接存取的表格 (4個)")
        print("=" * 80)
        
        for i, table_name in enumerate(c_accessed_tables, 1):
            info = tables_info[table_name]
            print(f"{i}. {table_name}")
            print(f"   描述: {info['description']}")
            print(f"   用途: {info['purpose']}")
            print(f"   操作: {info['operation']}")
            
            # 檢查表格是否存在並獲取記錄數
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   記錄數: {count:,} 筆")
            except sqlite3.OperationalError:
                print(f"   記錄數: 表格不存在")
            
            # 獲取表格結構
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                if columns:
                    print(f"   欄位數: {len(columns)} 個")
                    print(f"   主要欄位: {', '.join([col[1] for col in columns[:5]])}")
                    if len(columns) > 5:
                        print(f"   ... 等共 {len(columns)} 個欄位")
            except sqlite3.OperationalError:
                print(f"   欄位: 無法獲取結構")
            
            print()
        
        # 顯示系統其他表格概要
        print("=" * 80)
        print(f"系統其他表格 ({len(other_tables)}個) - 概要")
        print("=" * 80)
        
        for i, table_name in enumerate(other_tables, 1):
            info = tables_info[table_name]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                count_str = f"{count:,} 筆"
            except sqlite3.OperationalError:
                count_str = "不存在"
            
            print(f"{i:2d}. {table_name:<25} - {info['description']:<15} ({count_str})")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("總結")
        print("=" * 80)
        print("c.py 主要功能:")
        print("• 從 FinMind API 收集台股資料")
        print("• 存取 4 個核心資料表格")
        print("• 收集股價、月營收、現金流三類資料")
        print("• 透過 simple_collect.py 執行實際的資料收集工作")
        print()
        print("資料收集流程:")
        print("1. 從 stocks 表查詢股票清單")
        print("2. 呼叫 FinMind API 獲取資料")
        print("3. 將資料儲存到對應的表格中")
        print("   - TaiwanStockPrice → stock_prices")
        print("   - TaiwanStockMonthRevenue → monthly_revenues") 
        print("   - TaiwanStockCashFlowsStatement → cash_flow_statements")
        
    except Exception as e:
        print(f"分析失敗: {e}")

def main():
    """主程式"""
    analyze_database_tables()

if __name__ == "__main__":
    main()
