"""
參數調校與優化模組
提供 Prophet、XGBoost、LSTM 的超參數優化功能
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from itertools import product
from .features import train_test_split_time
from .predictor import mape, rmse, _safe_import
from .config import cfg


def tune_prophet_params(df: pd.DataFrame, param_grid: Dict = None) -> Dict:
    """
    Prophet 參數調校
    Args:
        df: 特徵資料框
        param_grid: 參數網格
    Returns:
        最佳參數與評估結果
    """
    if not cfg.enable_prophet:
        return {"error": "Prophet 已停用"}
    
    prophet = _safe_import("prophet")
    if prophet is None:
        return {"error": "Prophet 未安裝"}
    
    from prophet import Prophet
    
    # 預設參數網格
    if param_grid is None:
        param_grid = {
            'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5],
            'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
            'holidays_prior_scale': [0.01, 0.1, 1.0, 10.0],
            'seasonality_mode': ['additive', 'multiplicative'],
            'yearly_seasonality': [True, False],
            'weekly_seasonality': [False],
            'daily_seasonality': [False]
        }
    
    # 準備資料
    data = df[["date", "y"]].rename(columns={"date": "ds", "y": "y"}).copy()
    train_df, test_df = train_test_split_time(df)
    
    if test_df.empty:
        return {"error": "測試資料不足"}
    
    train_data = train_df[["date", "y"]].rename(columns={"date": "ds", "y": "y"})
    test_data = test_df[["date", "y"]].rename(columns={"date": "ds", "y": "y"})
    
    # 生成參數組合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    param_combinations = list(product(*param_values))
    
    best_params = None
    best_mape = float('inf')
    results = []
    
    print(f"🔄 測試 {len(param_combinations)} 種參數組合...")
    
    for i, param_combo in enumerate(param_combinations):
        try:
            params = dict(zip(param_names, param_combo))
            
            # 訓練模型
            model = Prophet(**params)
            model.fit(train_data)
            
            # 預測
            future = model.make_future_dataframe(periods=len(test_data), freq='MS')
            forecast = model.predict(future)
            
            # 取得測試期預測
            test_forecast = forecast.tail(len(test_data))
            y_true = test_data['y'].values
            y_pred = test_forecast['yhat'].values
            
            # 計算指標
            mape_score = mape(y_true, y_pred)
            rmse_score = rmse(y_true, y_pred)
            
            results.append({
                'params': params,
                'mape': mape_score,
                'rmse': rmse_score
            })
            
            if mape_score < best_mape:
                best_mape = mape_score
                best_params = params
            
            if (i + 1) % 10 == 0:
                print(f"   完成 {i + 1}/{len(param_combinations)} 組合")
                
        except Exception as e:
            print(f"   參數組合 {i} 失敗: {e}")
            continue
    
    return {
        'best_params': best_params,
        'best_mape': best_mape,
        'all_results': results,
        'n_combinations': len(param_combinations),
        'successful_combinations': len(results)
    }


def tune_xgboost_params(df: pd.DataFrame, param_grid: Dict = None) -> Dict:
    """
    XGBoost 參數調校
    Args:
        df: 特徵資料框
        param_grid: 參數網格
    Returns:
        最佳參數與評估結果
    """
    if not cfg.enable_xgboost:
        return {"error": "XGBoost 已停用"}
    
    xgb = _safe_import("xgboost")
    if xgb is None:
        return {"error": "XGBoost 未安裝"}
    
    from xgboost import XGBRegressor
    
    # 預設參數網格
    if param_grid is None:
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [3, 4, 5, 6],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [0.8, 0.9, 1.0]
        }
    
    # 準備特徵
    target = "y"
    feature_cols = [c for c in df.columns if c not in {"date", "revenue", target, "actual_month"}]
    
    train_df, test_df = train_test_split_time(df)
    
    if test_df.empty:
        return {"error": "測試資料不足"}
    
    # 確保特徵都是數值型
    X_train = train_df[feature_cols].select_dtypes(include=[np.number]).values
    y_train = train_df[target].values
    X_test = test_df[feature_cols].select_dtypes(include=[np.number]).values
    y_test = test_df[target].values
    
    # 生成參數組合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    param_combinations = list(product(*param_values))
    
    # 限制組合數量以避免過長時間
    if len(param_combinations) > 100:
        param_combinations = param_combinations[:100]
        print(f"⚠️  參數組合過多，限制為前 100 組")
    
    best_params = None
    best_mape = float('inf')
    results = []
    
    print(f"🔄 測試 {len(param_combinations)} 種參數組合...")
    
    for i, param_combo in enumerate(param_combinations):
        try:
            params = dict(zip(param_names, param_combo))
            params['random_state'] = cfg.random_seed
            params['objective'] = 'reg:squarederror'
            
            # 訓練模型
            model = XGBRegressor(**params)
            model.fit(X_train, y_train)
            
            # 預測
            y_pred = model.predict(X_test)
            
            # 計算指標
            mape_score = mape(y_test, y_pred)
            rmse_score = rmse(y_test, y_pred)
            
            results.append({
                'params': params,
                'mape': mape_score,
                'rmse': rmse_score
            })
            
            if mape_score < best_mape:
                best_mape = mape_score
                best_params = params
            
            if (i + 1) % 10 == 0:
                print(f"   完成 {i + 1}/{len(param_combinations)} 組合")
                
        except Exception as e:
            print(f"   參數組合 {i} 失敗: {e}")
            continue
    
    return {
        'best_params': best_params,
        'best_mape': best_mape,
        'all_results': results,
        'n_combinations': len(param_combinations),
        'successful_combinations': len(results)
    }


def tune_lstm_params(df: pd.DataFrame, param_grid: Dict = None) -> Dict:
    """
    LSTM 參數調校
    Args:
        df: 特徵資料框
        param_grid: 參數網格
    Returns:
        最佳參數與評估結果
    """
    if not cfg.enable_lstm:
        return {"error": "LSTM 已停用"}
    
    tf = _safe_import("tensorflow")
    if tf is None:
        return {"error": "TensorFlow 未安裝"}
    
    import tensorflow as tf
    
    # 預設參數網格
    if param_grid is None:
        param_grid = {
            'window_size': [6, 12, 18],
            'lstm_units': [16, 32, 64],
            'epochs': [30, 50, 100],
            'batch_size': [8, 16, 32]
        }
    
    # 準備時間序列資料
    series = df["y"].astype(float).values.reshape(-1, 1)
    
    # 生成參數組合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    param_combinations = list(product(*param_values))
    
    # 限制組合數量
    if len(param_combinations) > 50:
        param_combinations = param_combinations[:50]
        print(f"⚠️  參數組合過多，限制為前 50 組")
    
    best_params = None
    best_mape = float('inf')
    results = []
    
    print(f"🔄 測試 {len(param_combinations)} 種參數組合...")
    
    for i, param_combo in enumerate(param_combinations):
        try:
            params = dict(zip(param_names, param_combo))
            window_size = params['window_size']
            lstm_units = params['lstm_units']
            epochs = params['epochs']
            batch_size = params['batch_size']
            
            # 準備訓練資料
            X, y = [], []
            for j in range(len(series) - window_size):
                X.append(series[j : j + window_size])
                y.append(series[j + window_size])
            
            if len(X) < 20:  # 資料太少
                continue
                
            X = np.array(X)
            y = np.array(y)
            
            # 分割訓練/測試
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            if len(X_test) == 0:
                continue
            
            # 建立模型
            model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(window_size, 1)),
                tf.keras.layers.LSTM(lstm_units),
                tf.keras.layers.Dense(1),
            ])
            model.compile(optimizer="adam", loss="mse")
            
            # 訓練
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
            
            # 預測
            y_pred = model.predict(X_test, verbose=0).reshape(-1)
            y_test_flat = y_test.reshape(-1)
            
            # 計算指標
            mape_score = mape(y_test_flat, y_pred)
            rmse_score = rmse(y_test_flat, y_pred)
            
            results.append({
                'params': params,
                'mape': mape_score,
                'rmse': rmse_score
            })
            
            if mape_score < best_mape:
                best_mape = mape_score
                best_params = params
            
            if (i + 1) % 5 == 0:
                print(f"   完成 {i + 1}/{len(param_combinations)} 組合")
                
        except Exception as e:
            print(f"   參數組合 {i} 失敗: {e}")
            continue
    
    return {
        'best_params': best_params,
        'best_mape': best_mape,
        'all_results': results,
        'n_combinations': len(param_combinations),
        'successful_combinations': len(results)
    }


def comprehensive_tuning(stock_id: str) -> Dict:
    """
    對所有啟用模型進行綜合參數調校
    Args:
        stock_id: 股票代碼
    Returns:
        綜合調校結果
    """
    from .db import load_monthly_revenue
    from .features import to_monthly_df, build_features
    
    # 載入資料
    rows, warnings = load_monthly_revenue(stock_id)
    if not rows:
        return {"error": f"無法載入 {stock_id} 的營收資料"}
    
    # 建立特徵
    df = to_monthly_df(rows)
    feat_df = build_features(df)
    
    results = {}

    # Prophet 調校
    if cfg.enable_prophet:
        print("🔧 調校 Prophet 參數...")
        res = tune_prophet_params(feat_df)
        results['Prophet'] = res
        if 'best_params' in res and res['best_params']:
            from .param_store import save_best_params
            save_best_params(stock_id, 'Prophet', res['best_params'])

    # XGBoost 調校
    if cfg.enable_xgboost:
        print("🔧 調校 XGBoost 參數...")
        res = tune_xgboost_params(feat_df)
        results['XGBoost'] = res
        if 'best_params' in res and res['best_params']:
            from .param_store import save_best_params
            save_best_params(stock_id, 'XGBoost', res['best_params'])

    # LSTM 調校
    if cfg.enable_lstm:
        print("🔧 調校 LSTM 參數...")
        res = tune_lstm_params(feat_df)
        results['LSTM'] = res
        if 'best_params' in res and res['best_params']:
            from .param_store import save_best_params
            save_best_params(stock_id, 'LSTM', res['best_params'])

    # 前後比較摘要（若需要，可擴充：先跑一次原參數回測再比較）
    summary = []
    for model_name, res in results.items():
        if isinstance(res, dict) and 'best_mape' in res:
            summary.append({
                '模型': model_name,
                '最佳MAPE(優化後)': f"{res['best_mape']:.2f}%",
                '最佳參數': res.get('best_params')
            })

    return {
        'stock_id': stock_id,
        'tuning_results': results,
        'summary': summary,
        'warnings': warnings
    }
