#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本版特徵生成器 - 只使用核心套件
避免高級機器學習套件的依賴問題
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    SELECT stock_id, stock_name, market, industry
    FROM stocks
    WHERE is_active = 1
    AND stock_id NOT LIKE '00%'
    AND LENGTH(stock_id) = 4
    AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
    ORDER BY stock_id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

def get_stock_prices(stock_id, start_date, end_date):
    """獲取股價資料"""
    conn = connect_database()
    
    query = """
    SELECT date, open_price, high_price, low_price, close_price, volume
    FROM stock_prices 
    WHERE stock_id = ? AND date >= ? AND date <= ?
    ORDER BY date
    """
    
    df = pd.read_sql_query(query, conn, params=[stock_id, start_date, end_date])
    conn.close()
    
    return df

def get_monthly_revenue(stock_id, start_year, start_month, end_year, end_month):
    """獲取月營收資料"""
    conn = connect_database()

    query = """
    SELECT revenue_year, revenue_month, revenue
    FROM monthly_revenues
    WHERE stock_id = ?
    AND (revenue_year > ? OR (revenue_year = ? AND revenue_month >= ?))
    AND (revenue_year < ? OR (revenue_year = ? AND revenue_month <= ?))
    ORDER BY revenue_year, revenue_month
    """

    df = pd.read_sql_query(query, conn, params=[
        stock_id, start_year, start_year, start_month,
        end_year, end_year, end_month
    ])
    conn.close()

    return df

def calculate_technical_features(prices_df):
    """計算技術指標特徵"""
    if len(prices_df) < 60:
        return {}
    
    features = {}
    
    # 移動平均
    prices_df['ma_5'] = prices_df['close_price'].rolling(window=5).mean()
    prices_df['ma_10'] = prices_df['close_price'].rolling(window=10).mean()
    prices_df['ma_20'] = prices_df['close_price'].rolling(window=20).mean()
    prices_df['ma_60'] = prices_df['close_price'].rolling(window=60).mean()
    
    # 成交量指標
    prices_df['volume_ma_5'] = prices_df['volume'].rolling(window=5).mean()
    prices_df['volume_ma_10'] = prices_df['volume'].rolling(window=10).mean()
    prices_df['volume_ma_20'] = prices_df['volume'].rolling(window=20).mean()

    # 波動率
    prices_df['returns'] = prices_df['close_price'].pct_change()
    volatility_20 = prices_df['returns'].rolling(window=20).std()

    # RSI
    rsi = calculate_rsi(prices_df['close_price'], 14)

    # 獲取最新資料 (在所有計算完成後)
    latest = prices_df.iloc[-1]

    # 價格相對位置
    features['price_vs_ma_5'] = (latest['close_price'] / latest['ma_5'] - 1) if pd.notna(latest['ma_5']) else 0
    features['price_vs_ma_20'] = (latest['close_price'] / latest['ma_20'] - 1) if pd.notna(latest['ma_20']) else 0
    features['price_vs_ma_60'] = (latest['close_price'] / latest['ma_60'] - 1) if pd.notna(latest['ma_60']) else 0

    # 波動率特徵
    features['price_volatility'] = volatility_20.iloc[-1] if pd.notna(volatility_20.iloc[-1]) else 0

    # RSI 特徵
    features['rsi_14'] = rsi.iloc[-1] if pd.notna(rsi.iloc[-1]) else 50

    # 成交量特徵
    if pd.notna(latest['volume_ma_20']) and latest['volume_ma_20'] > 0:
        features['volume_vs_ma_20'] = (latest['volume'] / latest['volume_ma_20'] - 1)
    else:
        features['volume_vs_ma_20'] = 0
    
    # 動量指標
    if len(prices_df) >= 20:
        features['momentum_5'] = (latest['close_price'] / prices_df['close_price'].iloc[-6] - 1) if len(prices_df) > 5 else 0
        features['momentum_10'] = (latest['close_price'] / prices_df['close_price'].iloc[-11] - 1) if len(prices_df) > 10 else 0
        features['momentum_20'] = (latest['close_price'] / prices_df['close_price'].iloc[-21] - 1) if len(prices_df) > 20 else 0
    else:
        features['momentum_5'] = 0
        features['momentum_10'] = 0
        features['momentum_20'] = 0
    
    return features

def calculate_rsi(prices, window=14):
    """計算RSI指標"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_revenue_features(revenue_df):
    """計算營收特徵"""
    if len(revenue_df) == 0:
        return {}

    features = {}

    # 計算年成長率和月成長率
    revenue_df = revenue_df.sort_values(['revenue_year', 'revenue_month'])

    # 計算 YoY 成長率
    revenue_df['revenue_yoy_growth'] = 0.0
    revenue_df['revenue_mom_growth'] = 0.0

    for i in range(len(revenue_df)):
        current_row = revenue_df.iloc[i]
        current_year = current_row['revenue_year']
        current_month = current_row['revenue_month']
        current_revenue = current_row['revenue']

        # 計算 YoY 成長率 (與去年同月比較)
        last_year_data = revenue_df[
            (revenue_df['revenue_year'] == current_year - 1) &
            (revenue_df['revenue_month'] == current_month)
        ]

        if len(last_year_data) > 0 and last_year_data.iloc[0]['revenue'] > 0:
            last_year_revenue = last_year_data.iloc[0]['revenue']
            yoy_growth = (current_revenue - last_year_revenue) / last_year_revenue * 100
            revenue_df.iloc[i, revenue_df.columns.get_loc('revenue_yoy_growth')] = yoy_growth

        # 計算 MoM 成長率 (與上月比較)
        if i > 0:
            last_month_revenue = revenue_df.iloc[i-1]['revenue']
            if last_month_revenue > 0:
                mom_growth = (current_revenue - last_month_revenue) / last_month_revenue * 100
                revenue_df.iloc[i, revenue_df.columns.get_loc('revenue_mom_growth')] = mom_growth

    # 最新營收成長率
    if len(revenue_df) > 0:
        latest = revenue_df.iloc[-1]
        features['revenue_yoy_growth'] = latest['revenue_yoy_growth']
        features['revenue_mom_growth'] = latest['revenue_mom_growth']
        features['latest_revenue'] = latest['revenue']
    else:
        features['revenue_yoy_growth'] = 0
        features['revenue_mom_growth'] = 0
        features['latest_revenue'] = 0

    # 營收穩定性 (最近6個月的變異係數)
    if len(revenue_df) >= 6:
        recent_yoy = revenue_df['revenue_yoy_growth'].tail(6)
        if recent_yoy.std() > 0 and abs(recent_yoy.mean()) > 0:
            features['revenue_stability_cv'] = recent_yoy.std() / abs(recent_yoy.mean())
        else:
            features['revenue_stability_cv'] = 0
    else:
        features['revenue_stability_cv'] = 1

    # 連續成長月數
    consecutive_growth = 0
    for i in range(len(revenue_df) - 1, -1, -1):
        if revenue_df.iloc[i]['revenue_yoy_growth'] > 0:
            consecutive_growth += 1
        else:
            break
    features['consecutive_growth_months'] = consecutive_growth

    # 平均營收成長率 (最近12個月)
    if len(revenue_df) >= 12:
        features['avg_revenue_growth_12m'] = revenue_df['revenue_yoy_growth'].tail(12).mean()
    else:
        features['avg_revenue_growth_12m'] = revenue_df['revenue_yoy_growth'].mean() if len(revenue_df) > 0 else 0

    return features

def generate_features_for_stock(stock_id, end_date):
    """為單一股票生成特徵"""
    try:
        # 計算開始日期（往前推2年）
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=730)  # 2年
        start_date = start_dt.strftime('%Y-%m-%d')

        # 獲取股價資料
        prices_df = get_stock_prices(stock_id, start_date, end_date)
        if len(prices_df) < 60:
            logger.warning(f"股票 {stock_id} 價格資料不足: {len(prices_df)} 筆")
            return None

        # 獲取營收資料 (使用年月格式)
        start_year = start_dt.year
        start_month = start_dt.month
        end_year = end_dt.year
        end_month = end_dt.month

        revenue_df = get_monthly_revenue(stock_id, start_year, start_month, end_year, end_month)

        # 生成特徵
        features = {'stock_id': stock_id, 'date': end_date}

        # 技術指標特徵
        tech_features = calculate_technical_features(prices_df)
        features.update(tech_features)

        # 營收特徵
        revenue_features = calculate_revenue_features(revenue_df)
        features.update(revenue_features)

        # 基本資訊
        features['stock_id_numeric'] = int(stock_id) if stock_id.isdigit() else hash(stock_id) % 10000

        logger.info(f"成功生成股票 {stock_id} 的特徵，包含 {len(features)-2} 個特徵")
        return features

    except Exception as e:
        logger.error(f"生成股票 {stock_id} 特徵時發生錯誤: {e}")
        return None

def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方法: python simple_features_basic.py <end_date> [stock_ids]")
        print("範例: python simple_features_basic.py 2024-06-30")
        print("範例: python simple_features_basic.py 2024-06-30 8299,2330,1301")
        sys.exit(1)

    end_date = sys.argv[1]
    specific_stocks = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    
    print("基本版特徵生成器")
    print("=" * 50)
    print(f"目標日期: {end_date}")
    
    # 確保輸出目錄存在
    output_dir = Path("data/features")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 獲取股票清單
        if specific_stocks:
            # 處理指定股票
            print(f"處理指定股票: {specific_stocks}")
            stocks_data = []
            conn = connect_database()

            for stock_id in specific_stocks:
                stock_id = stock_id.strip()
                query = """
                SELECT stock_id, stock_name, market, industry
                FROM stocks
                WHERE stock_id = ? AND is_active = 1
                """
                result = pd.read_sql_query(query, conn, params=[stock_id])
                if len(result) > 0:
                    stocks_data.append(result.iloc[0])
                else:
                    print(f"警告: 找不到股票 {stock_id}")

            conn.close()

            if stocks_data:
                stocks_df = pd.DataFrame(stocks_data)
            else:
                print("錯誤: 沒有找到任何指定的股票")
                return
        else:
            # 處理所有股票
            stocks_df = get_stock_list()
            print(f"找到 {len(stocks_df)} 檔股票")
            print("處理所有股票...")
        
        # 生成特徵
        all_features = []
        success_count = 0
        
        for idx, stock in stocks_df.iterrows():
            stock_id = stock['stock_id']
            print(f"處理股票 {idx+1}/{len(stocks_df)}: {stock_id} ({stock['stock_name']})")
            
            features = generate_features_for_stock(stock_id, end_date)
            if features:
                all_features.append(features)
                success_count += 1
        
        if all_features:
            # 轉換為DataFrame並保存
            features_df = pd.DataFrame(all_features)
            
            # 填充缺失值
            numeric_columns = features_df.select_dtypes(include=[np.number]).columns
            features_df[numeric_columns] = features_df[numeric_columns].fillna(0)
            
            # 保存結果
            output_file = output_dir / f"features_basic_{end_date}.csv"
            features_df.to_csv(output_file, index=False)
            
            print(f"\n特徵生成完成！")
            print(f"成功處理: {success_count}/{len(stocks_df)} 檔股票")
            print(f"特徵數量: {len(features_df.columns)-2} 個")
            print(f"輸出檔案: {output_file}")
            
            # 顯示特徵統計
            print(f"\n特徵統計:")
            for col in features_df.columns:
                if col not in ['stock_id', 'date']:
                    mean_val = features_df[col].mean()
                    print(f"  {col}: 平均值 {mean_val:.4f}")
        
        else:
            print("沒有成功生成任何特徵")
            
    except Exception as e:
        logger.error(f"特徵生成過程發生錯誤: {e}")
        print(f"錯誤: {e}")

if __name__ == "__main__":
    main()
