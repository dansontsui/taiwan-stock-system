#!/usr/bin/env python3
"""
簡化版特徵生成器

避免複雜的導入問題，直接生成基本特徵
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
    SELECT stock_id, stock_name, market, industry
    FROM stocks 
    WHERE is_active = 1 AND stock_id NOT LIKE '00%'
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
    
    df = pd.read_sql_query(query, conn, params=(stock_id, start_date, end_date))
    conn.close()
    
    return df

def get_monthly_revenue(stock_id, start_date, end_date):
    """獲取月營收資料"""
    conn = connect_database()
    
    query = """
    SELECT revenue_year, revenue_month, revenue, 
           revenue_growth_mom, revenue_growth_yoy, date
    FROM monthly_revenues 
    WHERE stock_id = ? AND date >= ? AND date <= ?
    ORDER BY revenue_year, revenue_month
    """
    
    df = pd.read_sql_query(query, conn, params=(stock_id, start_date, end_date))
    conn.close()
    
    return df

def calculate_technical_features(price_df):
    """計算技術指標特徵"""
    if price_df.empty or len(price_df) < 20:
        return {}
    
    features = {}
    close_prices = price_df['close_price']
    volumes = price_df['volume']
    
    # 移動平均
    for window in [5, 10, 20]:
        if len(close_prices) >= window:
            ma = close_prices.rolling(window=window).mean()
            features[f'price_ma_{window}'] = ma.iloc[-1] if not ma.empty else 0
            
            # 價格相對於移動平均的位置
            current_price = close_prices.iloc[-1]
            features[f'price_vs_ma_{window}'] = (current_price - ma.iloc[-1]) / ma.iloc[-1] if ma.iloc[-1] > 0 else 0
    
    # 成交量移動平均
    for window in [5, 10, 20]:
        if len(volumes) >= window:
            vol_ma = volumes.rolling(window=window).mean()
            features[f'volume_ma_{window}'] = vol_ma.iloc[-1] if not vol_ma.empty else 0
            
            # 成交量相對於平均的比率
            current_volume = volumes.iloc[-1]
            features[f'volume_vs_ma_{window}'] = current_volume / vol_ma.iloc[-1] if vol_ma.iloc[-1] > 0 else 0
    
    # 價格波動率
    returns = close_prices.pct_change()
    if len(returns) >= 20:
        volatility = returns.rolling(window=20).std() * np.sqrt(252)
        features['price_volatility'] = volatility.iloc[-1] if not volatility.empty else 0
    
    # RSI指標
    if len(close_prices) >= 14:
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        features['rsi'] = rsi.iloc[-1] if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50
    
    # 動量指標
    for window in [5, 10, 20]:
        if len(close_prices) >= window:
            momentum = close_prices / close_prices.shift(window) - 1
            features[f'momentum_{window}'] = momentum.iloc[-1] if not momentum.empty and not pd.isna(momentum.iloc[-1]) else 0
    
    return features

def calculate_revenue_features(revenue_df):
    """計算月營收特徵"""
    if revenue_df.empty:
        return {}
    
    features = {}
    
    # 最近的營收成長率
    if len(revenue_df) >= 2:
        latest_revenue = revenue_df.iloc[-1]['revenue']
        prev_revenue = revenue_df.iloc[-2]['revenue']
        features['revenue_mom_latest'] = (latest_revenue - prev_revenue) / prev_revenue if prev_revenue > 0 else 0
    
    # 年增率特徵
    if 'revenue_growth_yoy' in revenue_df.columns:
        yoy_growth = revenue_df['revenue_growth_yoy'].dropna()
        if not yoy_growth.empty:
            features['revenue_yoy_mean'] = yoy_growth.mean()
            features['revenue_yoy_latest'] = yoy_growth.iloc[-1] if len(yoy_growth) > 0 else 0
    
    # 連續成長月數
    if 'revenue_growth_mom' in revenue_df.columns:
        mom_growth = revenue_df['revenue_growth_mom'].dropna()
        if not mom_growth.empty:
            consecutive_growth = 0
            for growth in reversed(mom_growth.tolist()):
                if growth > 0:
                    consecutive_growth += 1
                else:
                    break
            features['revenue_consecutive_growth_months'] = consecutive_growth
    
    # 營收穩定性
    if len(revenue_df) >= 12:
        recent_revenues = revenue_df['revenue'].tail(12)
        cv = recent_revenues.std() / recent_revenues.mean() if recent_revenues.mean() > 0 else 0
        features['revenue_stability_cv'] = cv
    
    return features

def generate_features_for_stock(stock_id, end_date):
    """為單一股票生成特徵"""
    try:
        # 計算需要的歷史資料範圍
        end_dt = pd.to_datetime(end_date)
        start_dt = end_dt - timedelta(days=2*365)  # 回看2年
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # 獲取原始資料
        price_df = get_stock_prices(stock_id, start_date, end_date)
        revenue_df = get_monthly_revenue(stock_id, start_date, end_date)
        
        if price_df.empty:
            return None
        
        # 生成特徵
        features = {}
        
        # 技術指標特徵
        tech_features = calculate_technical_features(price_df)
        features.update(tech_features)
        
        # 月營收特徵
        revenue_features = calculate_revenue_features(revenue_df)
        features.update(revenue_features)
        
        # 基本特徵
        features['stock_id_numeric'] = int(stock_id) if stock_id.isdigit() else 0
        features['market_type'] = 1 if int(stock_id) < 2000 else 2  # 上市/上櫃
        
        # 時間特徵
        features['month'] = end_dt.month
        features['quarter'] = end_dt.quarter
        features['is_quarter_end'] = 1 if end_dt.month in [3, 6, 9, 12] else 0
        
        # 添加股票ID和特徵日期
        features['stock_id'] = stock_id
        features['feature_date'] = end_date
        
        return features
        
    except Exception as e:
        print(f"❌ 股票 {stock_id} 特徵生成失敗: {e}")
        return None

def main():
    """主程式"""
    print("🔬 簡化版特徵生成器")
    print("=" * 50)
    
    # 獲取參數
    if len(sys.argv) > 1:
        end_date = sys.argv[1]
    else:
        end_date = input("請輸入特徵計算日期 (YYYY-MM-DD，預設今天): ").strip()
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📅 特徵計算日期: {end_date}")
    
    # 獲取股票清單
    try:
        stock_list = get_stock_list()
        print(f"📊 找到 {len(stock_list)} 個股票")
    except Exception as e:
        print(f"❌ 獲取股票清單失敗: {e}")
        return
    
    # 生成特徵
    all_features = []
    successful_count = 0
    
    for i, (_, stock) in enumerate(stock_list.iterrows()):
        stock_id = stock['stock_id']
        
        # 進度顯示
        if (i + 1) % 50 == 0:
            print(f"⏳ 已處理 {i + 1}/{len(stock_list)} 個股票")
        
        features = generate_features_for_stock(stock_id, end_date)
        if features:
            all_features.append(features)
            successful_count += 1
    
    if all_features:
        # 轉換為DataFrame
        features_df = pd.DataFrame(all_features)
        
        # 確保輸出目錄存在
        output_dir = Path("data/features")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 儲存結果
        output_file = output_dir / f"features_{end_date}.csv"
        features_df.to_csv(output_file, index=False)
        
        print(f"\n✅ 特徵生成完成！")
        print(f"📁 儲存位置: {output_file}")
        print(f"📊 成功處理: {successful_count}/{len(stock_list)} 個股票")
        print(f"🔢 特徵數量: {len(features_df.columns) - 2} 個")  # 排除stock_id和feature_date
        
        # 顯示特徵樣本
        print(f"\n📋 特徵樣本 (前5個股票):")
        feature_cols = [col for col in features_df.columns if col not in ['stock_id', 'feature_date']]
        print(features_df[['stock_id'] + feature_cols[:5]].head())
        
    else:
        print("❌ 沒有成功生成任何特徵")

if __name__ == "__main__":
    main()
