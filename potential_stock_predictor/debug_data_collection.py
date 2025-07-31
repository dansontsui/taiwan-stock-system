#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試資料收集過程
"""

import sys
import os
sys.path.append('src')

from utils.database import DatabaseManager
import pandas as pd
from datetime import datetime, timedelta

def debug_data_collection():
    """調試資料收集"""
    try:
        # 初始化資料庫管理器
        db_manager = DatabaseManager()
        
        # 測試股票和日期
        stock_id = "8299"
        end_date = "2025-05-31"
        
        # 計算開始日期（回看2年）
        end_dt = pd.to_datetime(end_date)
        start_dt = end_dt - timedelta(days=2*365)
        start_date = start_dt.strftime('%Y-%m-%d')
        
        print(f"測試股票: {stock_id}")
        print(f"日期範圍: {start_date} 到 {end_date}")
        print("=" * 50)
        
        # 1. 檢查股價資料
        print("1. 檢查股價資料:")
        stock_prices = db_manager.get_stock_prices(stock_id, start_date, end_date)
        print(f"   股價資料筆數: {len(stock_prices)}")
        if len(stock_prices) > 0:
            print(f"   日期範圍: {stock_prices['date'].min()} 到 {stock_prices['date'].max()}")
            print(f"   最新5筆資料:")
            print(stock_prices.tail()[['date', 'close_price', 'volume']])
        else:
            print("   沒有股價資料")
        
        # 2. 檢查營收資料
        print("\n2. 檢查營收資料:")
        monthly_revenue = db_manager.get_monthly_revenue(stock_id, start_date, end_date)
        print(f"   營收資料筆數: {len(monthly_revenue)}")
        if len(monthly_revenue) > 0:
            print(f"   最新5筆資料:")
            print(monthly_revenue.tail()[['revenue_year', 'revenue_month', 'revenue']])
        else:
            print("   沒有營收資料")
        
        # 3. 檢查財務報表
        print("\n3. 檢查財務報表:")
        financial_statements = db_manager.get_financial_statements(stock_id, start_date, end_date)
        print(f"   財務報表筆數: {len(financial_statements)}")
        if len(financial_statements) > 0:
            print(f"   欄位: {list(financial_statements.columns)}")
        else:
            print("   沒有財務報表資料")
        
        # 4. 檢查資產負債表
        print("\n4. 檢查資產負債表:")
        balance_sheets = db_manager.get_balance_sheets(stock_id, start_date, end_date)
        print(f"   資產負債表筆數: {len(balance_sheets)}")
        if len(balance_sheets) > 0:
            print(f"   欄位: {list(balance_sheets.columns)}")
        else:
            print("   沒有資產負債表資料")
        
        # 5. 檢查現金流
        print("\n5. 檢查現金流:")
        cash_flow = db_manager.get_cash_flow(stock_id, start_date, end_date)
        print(f"   現金流筆數: {len(cash_flow)}")
        if len(cash_flow) > 0:
            print(f"   欄位: {list(cash_flow.columns)}")
        else:
            print("   沒有現金流資料")
        
        # 6. 模擬驗證邏輯
        print("\n6. 模擬驗證邏輯:")
        raw_data = {
            'stock_prices': stock_prices,
            'monthly_revenue': monthly_revenue,
            'financial_statements': financial_statements,
            'balance_sheets': balance_sheets,
            'cash_flow': cash_flow
        }
        
        # 檢查股價資料
        if raw_data['stock_prices'].empty:
            print("   ❌ 股價資料為空")
            return
        else:
            print(f"   ✅ 股價資料: {len(raw_data['stock_prices'])} 筆")
        
        # 檢查資料數量
        if len(raw_data['stock_prices']) < 30:
            print(f"   ❌ 股價資料不足30天: {len(raw_data['stock_prices'])} 筆")
            return
        else:
            print(f"   ✅ 股價資料充足: {len(raw_data['stock_prices'])} 筆")
        
        # 檢查最新日期
        latest_price_date = raw_data['stock_prices']['date'].max()
        print(f"   最新股價日期: {latest_price_date}")
        
        if pd.to_datetime(latest_price_date) < pd.to_datetime('2022-01-01'):
            print("   ❌ 最新資料太舊")
            return
        else:
            print("   ✅ 最新資料符合要求")
        
        print("\n✅ 所有驗證通過，應該可以生成特徵")
        
    except Exception as e:
        print(f"調試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_collection()
