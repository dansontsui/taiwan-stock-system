#!/usr/bin/env python3
"""
輔助工具函數
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pickle
import json
from pathlib import Path

def calculate_trading_days(start_date: str, end_date: str, 
                          holidays: List[str] = None) -> int:
    """
    計算交易日數量（排除週末和假日）
    
    Args:
        start_date: 開始日期
        end_date: 結束日期
        holidays: 假日列表
        
    Returns:
        交易日數量
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # 生成日期範圍
    date_range = pd.date_range(start=start, end=end, freq='D')
    
    # 排除週末
    weekdays = date_range[date_range.weekday < 5]
    
    # 排除假日
    if holidays:
        holiday_dates = pd.to_datetime(holidays)
        weekdays = weekdays[~weekdays.isin(holiday_dates)]
    
    return len(weekdays)

def get_next_trading_day(date: str, n_days: int = 1) -> str:
    """
    獲取下一個交易日
    
    Args:
        date: 基準日期
        n_days: 向前推進的交易日數
        
    Returns:
        下一個交易日
    """
    current_date = pd.to_datetime(date)
    trading_days = 0
    
    while trading_days < n_days:
        current_date += timedelta(days=1)
        # 排除週末
        if current_date.weekday() < 5:
            trading_days += 1
    
    return current_date.strftime('%Y-%m-%d')

def calculate_returns(prices: pd.Series, periods: int = 1) -> pd.Series:
    """
    計算報酬率
    
    Args:
        prices: 價格序列
        periods: 計算期間
        
    Returns:
        報酬率序列
    """
    return prices.pct_change(periods=periods)

def calculate_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    """
    計算波動率
    
    Args:
        returns: 報酬率序列
        window: 計算視窗
        
    Returns:
        波動率序列
    """
    return returns.rolling(window=window).std() * np.sqrt(252)  # 年化波動率

def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    計算RSI指標 (Relative Strength Index)

    Args:
        prices: 價格序列
        window: 計算視窗

    Returns:
        RSI序列
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    # 避免除零錯誤
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    # 處理邊界情況
    rsi = rsi.fillna(50)  # 無法計算時使用中性值50
    rsi = rsi.clip(0, 100)  # 確保RSI在0-100範圍內

    return rsi

def calculate_moving_average(data: pd.Series, window: int) -> pd.Series:
    """
    計算移動平均
    
    Args:
        data: 資料序列
        window: 視窗大小
        
    Returns:
        移動平均序列
    """
    return data.rolling(window=window).mean()

def calculate_momentum(prices: pd.Series, window: int = 10) -> pd.Series:
    """
    計算動量指標
    
    Args:
        prices: 價格序列
        window: 計算視窗
        
    Returns:
        動量指標序列
    """
    return prices / prices.shift(window) - 1

def normalize_features(df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
    """
    特徵標準化
    
    Args:
        df: 特徵DataFrame
        method: 標準化方法 ('standard', 'minmax', 'robust')
        
    Returns:
        標準化後的DataFrame
    """
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    
    if method == 'standard':
        scaler = StandardScaler()
    elif method == 'minmax':
        scaler = MinMaxScaler()
    elif method == 'robust':
        scaler = RobustScaler()
    else:
        raise ValueError(f"不支援的標準化方法: {method}")
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df_normalized = df.copy()
    df_normalized[numeric_columns] = scaler.fit_transform(df[numeric_columns])
    
    return df_normalized

def save_model(model, file_path: str):
    """
    儲存模型
    
    Args:
        model: 模型物件
        file_path: 儲存路徑
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'wb') as f:
        pickle.dump(model, f)

def load_model(file_path: str):
    """
    載入模型
    
    Args:
        file_path: 模型檔案路徑
        
    Returns:
        模型物件
    """
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def save_json(data: Dict, file_path: str):
    """
    儲存JSON檔案 - 使用 ASCII 編碼確保跨平台兼容性

    Args:
        data: 資料字典
        file_path: 儲存路徑
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(file_path: str) -> Dict:
    """
    載入JSON檔案 - 支援多種編碼

    Args:
        file_path: 檔案路徑

    Returns:
        資料字典
    """
    # 嘗試不同編碼
    encodings = ['utf-8', 'ascii', 'cp1252', 'big5']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except (UnicodeDecodeError, UnicodeError):
            continue

    # 如果所有編碼都失敗，使用錯誤處理
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return json.load(f)

def get_financial_quarter(date: str) -> Tuple[int, int]:
    """
    根據日期獲取財務季度
    
    Args:
        date: 日期字串
        
    Returns:
        (年份, 季度)
    """
    dt = pd.to_datetime(date)
    year = dt.year
    quarter = (dt.month - 1) // 3 + 1
    return year, quarter

def filter_outliers(data: pd.Series, method: str = 'iqr', 
                   threshold: float = 1.5) -> pd.Series:
    """
    過濾異常值
    
    Args:
        data: 資料序列
        method: 過濾方法 ('iqr', 'zscore')
        threshold: 閾值
        
    Returns:
        過濾後的資料序列
    """
    if method == 'iqr':
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        return data[(data >= lower_bound) & (data <= upper_bound)]
    
    elif method == 'zscore':
        z_scores = np.abs((data - data.mean()) / data.std())
        return data[z_scores <= threshold]
    
    else:
        raise ValueError(f"不支援的過濾方法: {method}")

def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2) -> Dict[str, pd.Series]:
    """
    計算布林通道

    Args:
        prices: 價格序列
        window: 移動平均視窗
        num_std: 標準差倍數

    Returns:
        包含上軌、中軌、下軌的字典
    """
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()

    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)

    return {
        'upper': upper_band,
        'middle': sma,
        'lower': lower_band
    }

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    計算MACD指標

    Args:
        prices: 價格序列
        fast: 快線EMA週期
        slow: 慢線EMA週期
        signal: 信號線EMA週期

    Returns:
        包含MACD線、信號線、柱狀圖的字典
    """
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                        k_window: int = 14, d_window: int = 3) -> Dict[str, pd.Series]:
    """
    計算隨機指標 (Stochastic Oscillator)

    Args:
        high: 最高價序列
        low: 最低價序列
        close: 收盤價序列
        k_window: %K計算視窗
        d_window: %D平滑視窗

    Returns:
        包含%K和%D的字典
    """
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()

    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_window).mean()

    return {
        'k_percent': k_percent.fillna(50),
        'd_percent': d_percent.fillna(50)
    }

def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    計算威廉指標 (Williams %R)

    Args:
        high: 最高價序列
        low: 最低價序列
        close: 收盤價序列
        window: 計算視窗

    Returns:
        Williams %R序列
    """
    highest_high = high.rolling(window=window).max()
    lowest_low = low.rolling(window=window).min()

    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))

    return williams_r.fillna(-50)

def create_time_features(date_series: pd.Series) -> pd.DataFrame:
    """
    創建時間特徵

    Args:
        date_series: 日期序列

    Returns:
        時間特徵DataFrame
    """
    dates = pd.to_datetime(date_series)

    features = pd.DataFrame({
        'year': dates.dt.year,
        'month': dates.dt.month,
        'quarter': dates.dt.quarter,
        'day_of_week': dates.dt.dayofweek,
        'day_of_year': dates.dt.dayofyear,
        'is_month_start': dates.dt.is_month_start.astype(int),
        'is_month_end': dates.dt.is_month_end.astype(int),
        'is_quarter_start': dates.dt.is_quarter_start.astype(int),
        'is_quarter_end': dates.dt.is_quarter_end.astype(int)
    })

    return features
