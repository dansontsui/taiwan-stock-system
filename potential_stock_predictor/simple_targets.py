#!/usr/bin/env python3
"""
簡化版目標變數生成器

生成預測目標：20個交易日內股價上漲超過5%
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def connect_database():
    """連接資料庫"""
    db_path = Path("../data/taiwan_stock.db")
    if not db_path.exists():
        raise FileNotFoundError(f"找不到資料庫檔案: {db_path}")
    
    return sqlite3.connect(str(db_path))

def get_stock_list():
    """獲取股票清單"""
    conn = connect_database()
    
    query = """
    SELECT stock_id, stock_name
    FROM stocks
    WHERE is_active = 1 AND stock_id NOT LIKE '00%'
    ORDER BY stock_id
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    # 過濾只包含數字的股票代碼
    df = df[df['stock_id'].str.isdigit()]

    return df

def get_stock_prices(stock_id, start_date, end_date):
    """獲取股價資料"""
    conn = connect_database()
    
    query = """
    SELECT date, close_price, high_price
    FROM stock_prices 
    WHERE stock_id = ? AND date >= ? AND date <= ?
    ORDER BY date
    """
    
    df = pd.read_sql_query(query, conn, params=(stock_id, start_date, end_date))
    conn.close()
    
    return df

def get_next_trading_day(date_str, n_days=1):
    """獲取下一個交易日（簡化版，只排除週末）"""
    current_date = pd.to_datetime(date_str)
    trading_days = 0
    
    while trading_days < n_days:
        current_date += timedelta(days=1)
        # 排除週末
        if current_date.weekday() < 5:
            trading_days += 1
    
    return current_date.strftime('%Y-%m-%d')

def calculate_target_for_stock(stock_id, feature_date):
    """計算單一股票的目標變數"""
    try:
        # 計算預測期間
        prediction_start = get_next_trading_day(feature_date, 1)
        prediction_end = get_next_trading_day(feature_date, 25)  # 多取一些天數確保有20個交易日
        
        # 獲取預測期間的股價資料
        price_df = get_stock_prices(stock_id, prediction_start, prediction_end)
        
        if price_df.empty or len(price_df) < 15:  # 至少需要15個交易日
            return None
        
        # 獲取基準價格（特徵日期的收盤價）
        base_start = (pd.to_datetime(feature_date) - timedelta(days=5)).strftime('%Y-%m-%d')
        base_end = (pd.to_datetime(feature_date) + timedelta(days=5)).strftime('%Y-%m-%d')
        base_price_df = get_stock_prices(stock_id, base_start, base_end)
        
        if base_price_df.empty:
            return None
        
        # 找到最接近特徵日期的交易日價格
        base_price_df['date'] = pd.to_datetime(base_price_df['date'])
        feature_dt = pd.to_datetime(feature_date)
        
        valid_dates = base_price_df[base_price_df['date'] <= feature_dt]
        if valid_dates.empty:
            valid_dates = base_price_df[base_price_df['date'] > feature_dt]
            if valid_dates.empty:
                return None
        
        closest_idx = (valid_dates['date'] - feature_dt).abs().idxmin()
        base_price = base_price_df.loc[closest_idx, 'close_price']
        
        if base_price <= 0:
            return None
        
        # 計算預測期間內的最大報酬率
        max_price = price_df['high_price'].max()
        max_return = (max_price - base_price) / base_price
        
        # 找到最大報酬率發生的日期
        max_return_idx = price_df['high_price'].idxmax()
        max_return_date = price_df.loc[max_return_idx, 'date']
        
        # 判斷是否達到目標報酬率（5%）
        target = 1 if max_return >= 0.05 else 0
        
        return {
            'stock_id': stock_id,
            'feature_date': feature_date,
            'target': target,
            'max_return': max_return,
            'max_return_date': max_return_date,
            'trading_days_count': len(price_df)
        }
        
    except Exception as e:
        print(f"❌ 股票 {stock_id} 目標變數計算失敗: {e}")
        return None

def generate_quarterly_dates(start_date, end_date):
    """生成季度日期"""
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    dates = []
    current_year = start_dt.year
    
    while current_year <= end_dt.year:
        for quarter_end_month in [3, 6, 9, 12]:
            quarter_date = datetime(current_year, quarter_end_month, 
                                  [31, 30, 30, 31][quarter_end_month//3 - 1])
            
            # 調整2月份
            if quarter_end_month == 3:
                quarter_date = datetime(current_year, 3, 31)
            elif quarter_end_month == 6:
                quarter_date = datetime(current_year, 6, 30)
            elif quarter_end_month == 9:
                quarter_date = datetime(current_year, 9, 30)
            else:  # 12月
                quarter_date = datetime(current_year, 12, 31)
            
            if start_dt <= quarter_date <= end_dt:
                dates.append(quarter_date.strftime('%Y-%m-%d'))
        
        current_year += 1
    
    return dates

def main():
    """主程式"""
    print("🎯 簡化版目標變數生成器")
    print("=" * 50)
    
    # 獲取參數
    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        start_date = input("請輸入開始日期 (YYYY-MM-DD，預設2022-01-01): ").strip()
        if not start_date:
            start_date = "2022-01-01"
        
        end_date = input("請輸入結束日期 (YYYY-MM-DD，預設2024-06-30): ").strip()
        if not end_date:
            end_date = "2024-06-30"
    
    print(f"📅 日期範圍: {start_date} ~ {end_date}")
    
    # 生成季度特徵日期
    feature_dates = generate_quarterly_dates(start_date, end_date)
    print(f"📊 季度特徵日期: {len(feature_dates)} 個")
    print(f"   {', '.join(feature_dates)}")
    
    # 獲取股票清單
    try:
        stock_list = get_stock_list()
        print(f"📈 找到 {len(stock_list)} 個股票")
    except Exception as e:
        print(f"❌ 獲取股票清單失敗: {e}")
        return
    
    # 生成目標變數
    all_targets = []
    total_combinations = len(stock_list) * len(feature_dates)
    processed = 0
    
    for feature_date in feature_dates:
        print(f"\n⏳ 處理日期: {feature_date}")
        date_targets = []
        
        for i, (_, stock) in enumerate(stock_list.iterrows()):
            stock_id = stock['stock_id']
            
            target = calculate_target_for_stock(stock_id, feature_date)
            if target:
                date_targets.append(target)
            
            processed += 1
            
            # 進度顯示
            if (i + 1) % 200 == 0:
                print(f"   已處理 {i + 1}/{len(stock_list)} 個股票")
        
        print(f"   ✅ {feature_date}: 成功生成 {len(date_targets)} 個目標變數")
        all_targets.extend(date_targets)
    
    if all_targets:
        # 轉換為DataFrame
        targets_df = pd.DataFrame(all_targets)
        
        # 分析目標變數分布
        total_samples = len(targets_df)
        positive_samples = (targets_df['target'] == 1).sum()
        positive_ratio = positive_samples / total_samples if total_samples > 0 else 0
        avg_return = targets_df['max_return'].mean()
        
        print(f"\n📊 目標變數統計:")
        print(f"   總樣本數: {total_samples}")
        print(f"   正樣本數: {positive_samples}")
        print(f"   正樣本比例: {positive_ratio:.2%}")
        print(f"   平均最大報酬率: {avg_return:.2%}")
        
        # 確保輸出目錄存在
        output_dir = Path("data/targets")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 儲存結果
        output_file = output_dir / f"targets_quarterly_{end_date}.csv"
        targets_df.to_csv(output_file, index=False)
        
        print(f"\n✅ 目標變數生成完成！")
        print(f"📁 儲存位置: {output_file}")
        
        # 顯示樣本
        print(f"\n📋 目標變數樣本:")
        print(targets_df.head())
        
    else:
        print("❌ 沒有成功生成任何目標變數")

if __name__ == "__main__":
    main()
