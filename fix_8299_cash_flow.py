#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復8299現金流資料收集問題
"""

import sys
import os
import time
import requests
import pandas as pd
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
except ImportError:
    class Config:
        DATABASE_PATH = os.getenv('DATABASE_PATH', "data/taiwan_stock.db")
        FINMIND_API_URL = os.getenv('FINMIND_API_URL', "https://api.finmindtrade.com/api/v4/data")
        FINMIND_API_TOKEN = os.getenv('FINMIND_API_TOKEN', '')

def get_cash_flow_data_direct(stock_id="8299", start_date="2022-01-01", end_date="2024-06-30"):
    """直接從FinMind API獲取現金流資料"""
    
    print(f"獲取股票 {stock_id} 的現金流資料...")
    print(f"時間範圍: {start_date} ~ {end_date}")
    
    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": "TaiwanStockCashFlowsStatement",
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": Config.FINMIND_API_TOKEN
        }
        
        print(f"發送API請求...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                print(f"✅ 成功獲取 {len(df)} 筆現金流資料")
                print(f"欄位: {list(df.columns)}")
                
                # 顯示樣本資料
                print(f"前5筆資料:")
                for i, record in enumerate(df.head(5).to_dict('records')):
                    print(f"  {i+1}. {record}")
                
                return df
            else:
                print(f"❌ API回應正常但無資料")
                return None
        else:
            print(f"❌ API請求失敗: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 獲取現金流資料失敗: {e}")
        return None

def save_cash_flow_to_database(df, stock_id):
    """將現金流資料儲存到資料庫"""
    
    if df is None or df.empty:
        print("❌ 沒有資料可儲存")
        return 0
    
    print(f"開始儲存現金流資料到資料庫...")
    
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # 檢查表結構
        cursor.execute("PRAGMA table_info(cash_flow_statements)")
        columns = cursor.fetchall()
        print(f"資料庫表結構:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        saved_count = 0
        
        for _, row in df.iterrows():
            try:
                # 檢查資料是否已存在
                cursor.execute("""
                    SELECT COUNT(*) FROM cash_flow_statements 
                    WHERE stock_id = ? AND date = ? AND type = ?
                """, (row['stock_id'], row['date'], row['type']))
                
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    cursor.execute("""
                        INSERT INTO cash_flow_statements 
                        (stock_id, date, type, value, origin_name, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['stock_id'],
                        row['date'],
                        row['type'],
                        row['value'],
                        row.get('origin_name', ''),
                        datetime.now()
                    ))
                    saved_count += 1
                else:
                    print(f"  跳過重複資料: {row['date']} - {row['type']}")
                
            except Exception as e:
                print(f"  儲存單筆資料失敗: {e}")
                print(f"  資料: {dict(row)}")
                continue
        
        conn.commit()
        print(f"✅ 成功儲存 {saved_count} 筆現金流資料")
        
        # 驗證儲存結果
        cursor.execute("SELECT COUNT(*) FROM cash_flow_statements WHERE stock_id = ?", (stock_id,))
        total_count = cursor.fetchone()[0]
        print(f"✅ 股票 {stock_id} 現在總共有 {total_count} 筆現金流資料")
        
        conn.close()
        return saved_count
        
    except Exception as e:
        print(f"❌ 儲存現金流資料失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return 0

def verify_data_in_database(stock_id):
    """驗證資料庫中的資料"""
    
    print(f"\n驗證股票 {stock_id} 在資料庫中的資料...")
    
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # 檢查各種資料類型的數量
        data_types = {
            'stock_prices': '股價資料',
            'monthly_revenues': '月營收資料',
            'financial_statements': '財務報表',
            'balance_sheets': '資產負債表',
            'cash_flow_statements': '現金流量表'
        }
        
        print(f"股票 {stock_id} 資料統計:")
        for table, name in data_types.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE stock_id = ?", (stock_id,))
                count = cursor.fetchone()[0]
                print(f"  {name}: {count} 筆")
                
                if count > 0 and table == 'cash_flow_statements':
                    # 顯示現金流資料的樣本
                    cursor.execute(f"""
                        SELECT date, type, value, origin_name 
                        FROM {table} 
                        WHERE stock_id = ? 
                        ORDER BY date DESC 
                        LIMIT 5
                    """, (stock_id,))
                    
                    samples = cursor.fetchall()
                    print(f"    最新5筆現金流資料:")
                    for sample in samples:
                        print(f"      {sample[0]} - {sample[1]}: {sample[2]:,.0f} ({sample[3]})")
                        
            except Exception as e:
                print(f"  {name}: 查詢失敗 - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 驗證資料失敗: {e}")

def main():
    """主函數"""
    
    print("=" * 80)
    print("8299 現金流資料修復工具")
    print("=" * 80)
    
    stock_id = "8299"
    start_date = "2022-01-01"
    end_date = "2024-06-30"
    
    # 1. 獲取現金流資料
    df = get_cash_flow_data_direct(stock_id, start_date, end_date)
    
    if df is not None:
        # 2. 儲存到資料庫
        saved_count = save_cash_flow_to_database(df, stock_id)
        
        # 3. 驗證結果
        verify_data_in_database(stock_id)
        
        print(f"\n" + "=" * 80)
        print("修復完成！")
        print("=" * 80)
        print(f"獲取資料: {len(df)} 筆")
        print(f"儲存資料: {saved_count} 筆")
        
        if saved_count > 0:
            print("✅ 8299 現金流資料修復成功！")
        else:
            print("⚠️ 沒有新資料需要儲存")
    else:
        print("❌ 無法獲取現金流資料，修復失敗")

if __name__ == "__main__":
    main()
