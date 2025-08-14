"""
回測與模型評估模組
提供時間滾動交叉驗證、MAPE/RMSE評估、趨勢方向準確率計算等功能
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from .features import to_monthly_df, build_features
from .predictor import train_prophet, train_lstm, train_xgboost, mape, rmse
from .config import cfg


def rolling_window_split(df: pd.DataFrame, window_months: int = 12, step_months: int = 1) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    時間滾動視窗分割
    Args:
        df: 特徵資料框
        window_months: 訓練視窗月數
        step_months: 步進月數
    Returns:
        [(train_df, test_df), ...] 的清單
    """
    splits = []
    df_sorted = df.sort_values('date').reset_index(drop=True)
    
    for i in range(window_months, len(df_sorted), step_months):
        if i >= len(df_sorted):
            break
        
        train_end_idx = i
        test_start_idx = i
        test_end_idx = min(i + 1, len(df_sorted))  # 預測下一期
        
        if test_end_idx > len(df_sorted):
            break
            
        train_df = df_sorted.iloc[:train_end_idx].copy()
        test_df = df_sorted.iloc[test_start_idx:test_end_idx].copy()
        
        if len(train_df) >= window_months and len(test_df) > 0:
            splits.append((train_df, test_df))
    
    return splits


def calculate_trend_accuracy(y_true: np.ndarray, y_pred: np.ndarray, y_prev: np.ndarray) -> float:
    """
    計算趨勢方向準確率
    Args:
        y_true: 實際值
        y_pred: 預測值  
        y_prev: 前期實際值
    Returns:
        趨勢方向準確率 (0-1)
    """
    if len(y_true) != len(y_pred) or len(y_true) != len(y_prev):
        return 0.0
    
    # 計算實際趨勢方向 (上升=1, 下降=0)
    actual_trend = (y_true > y_prev).astype(int)
    # 計算預測趨勢方向
    predicted_trend = (y_pred > y_prev).astype(int)
    
    # 計算準確率
    correct_predictions = (actual_trend == predicted_trend).sum()
    total_predictions = len(actual_trend)
    
    return correct_predictions / total_predictions if total_predictions > 0 else 0.0


def backtest_model(model_name: str, df: pd.DataFrame, stock_id: str, window_months: int = 36) -> Dict:
    """
    對單一模型進行回測
    Args:
        model_name: 模型名稱 ('Prophet', 'LSTM', 'XGBoost')
        df: 特徵資料框
        window_months: 訓練視窗月數
    Returns:
        回測結果字典
    """
    # 選擇訓練函數
    if model_name == 'Prophet':
        if not cfg.enable_prophet:
            return {"error": "Prophet 已停用"}
        train_func = train_prophet
    elif model_name == 'LSTM':
        if not cfg.enable_lstm:
            return {"error": "LSTM 已停用"}
        train_func = train_lstm
    elif model_name == 'XGBoost':
        if not cfg.enable_xgboost:
            return {"error": "XGBoost 已停用"}
        train_func = train_xgboost
    else:
        return {"error": f"未知模型: {model_name}"}
    
    # 時間滾動分割
    splits = rolling_window_split(df, window_months=window_months)
    
    if len(splits) < 3:
        return {"error": f"資料不足，僅能產生 {len(splits)} 個分割"}
    
    predictions = []
    actuals = []
    previous_values = []
    errors = []
    history_records = []  # 新增：詳細歷史紀錄

    for i, (train_df, test_df) in enumerate(splits):
        try:
            # 訓練模型
            model, pred_df, metrics = train_func(train_df, stock_id=stock_id)

            # 取得預測值
            if not pred_df.empty and 'forecast_value' in pred_df.columns:
                pred_value = float(pred_df['forecast_value'].iloc[0])
            else:
                continue
            
            # 取得實際值
            if not test_df.empty and 'y' in test_df.columns:
                actual_value = float(test_df['y'].iloc[0])
            else:
                continue
            
            # 取得前期值（用於趨勢計算）
            if len(train_df) > 0 and 'y' in train_df.columns:
                prev_value = float(train_df['y'].iloc[-1])
            else:
                continue
            
            predictions.append(pred_value)
            actuals.append(actual_value)
            previous_values.append(prev_value)

            # 新增：記錄詳細歷史
            test_date = test_df['date'].iloc[0] if 'date' in test_df.columns else f"Period_{i}"
            error_pct = abs(pred_value - actual_value) / actual_value * 100 if actual_value != 0 else 0

            history_records.append({
                "period": i + 1,
                "test_date": test_date.strftime('%Y-%m') if hasattr(test_date, 'strftime') else str(test_date),
                "predicted": pred_value,
                "actual": actual_value,
                "error_pct": error_pct,
                "error_abs": abs(pred_value - actual_value)
            })

        except Exception as e:
            errors.append(f"分割 {i}: {str(e)}")
            continue
    
    if len(predictions) == 0:
        return {"error": "無有效預測結果", "details": errors}
    
    # 計算評估指標
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    previous_values = np.array(previous_values)
    
    mape_score = mape(actuals, predictions)
    rmse_score = rmse(actuals, predictions)
    trend_accuracy = calculate_trend_accuracy(actuals, predictions, previous_values)
    
    return {
        "model": model_name,
        "n_predictions": len(predictions),
        "mape": mape_score,
        "rmse": rmse_score,
        "trend_accuracy": trend_accuracy,
        "predictions": predictions.tolist(),
        "actuals": actuals.tolist(),
        "errors": errors,
        "history": history_records  # 新增：詳細歷史紀錄
    }


def comprehensive_backtest(df: pd.DataFrame, stock_id: str, window_months: int = 36) -> Dict:
    """
    對所有啟用的模型進行綜合回測
    Args:
        df: 特徵資料框
        window_months: 訓練視窗月數
    Returns:
        綜合回測結果
    """
    models_to_test = []
    
    if cfg.enable_prophet:
        models_to_test.append('Prophet')
    if cfg.enable_lstm:
        models_to_test.append('LSTM')
    if cfg.enable_xgboost:
        models_to_test.append('XGBoost')
    
    if not models_to_test:
        return {"error": "沒有啟用的模型可供回測"}
    
    results = {}
    summary = []
    
    for model_name in models_to_test:
        print(f"🔄 回測 {model_name}...")
        result = backtest_model(model_name, df, stock_id, window_months)
        results[model_name] = result
        
        if "error" not in result:
            summary.append({
                "模型": model_name,
                "預測次數": result["n_predictions"],
                "MAPE": f"{result['mape']:.2f}%",
                "RMSE": f"{result['rmse']:,.0f}",
                "趨勢準確率": f"{result['trend_accuracy']*100:.1f}%"
            })
    
    # 找出最佳模型
    best_model = None
    best_mape = float('inf')
    
    for model_name, result in results.items():
        if "error" not in result and result["mape"] < best_mape:
            best_mape = result["mape"]
            best_model = model_name
    
    return {
        "results": results,
        "summary": summary,
        "best_model": best_model,
        "best_mape": best_mape,
        "target_mape": 8.0,
        "target_trend_accuracy": 80.0,
        "meets_targets": best_mape <= 8.0 and any(
            r.get("trend_accuracy", 0) * 100 >= 80.0 
            for r in results.values() 
            if "error" not in r
        )
    }


def run_backtest_analysis(stock_id: str, window_months: int = 36) -> Dict:
    """
    執行完整的回測分析
    Args:
        stock_id: 股票代碼
        window_months: 訓練視窗月數
    Returns:
        完整回測分析結果
    """
    from .db import load_monthly_revenue
    
    # 載入資料
    rows, warnings = load_monthly_revenue(stock_id)
    if not rows:
        return {"error": f"無法載入 {stock_id} 的營收資料"}
    
    # 建立特徵
    df = to_monthly_df(rows)
    if df.empty:
        return {"error": "資料轉換失敗"}
    
    feat_df = build_features(df)
    if feat_df.empty:
        return {"error": "特徵建立失敗"}
    
    # 執行回測
    backtest_results = comprehensive_backtest(feat_df, stock_id, window_months)

    # 匯出各模型的歷史紀錄為 CSV（含最佳與非最佳）
    try:
        from .config import ensure_dirs
        ensure_dirs()
        import pandas as pd
        results_all = backtest_results.get('results', {})
        for model_name, res in results_all.items():
            history = res.get('history', [])
            if history:
                df_hist = pd.DataFrame(history)
                df_hist.insert(0, 'stock_id', stock_id)
                df_hist.insert(1, 'model_name', model_name)
                # 重新命名欄位符合需求
                df_hist = df_hist.rename(columns={
                    'period': 'period',
                    'test_date': 'test_date',
                    'predicted': 'predicted_value',
                    'actual': 'actual_value',
                    'error_pct': 'error_percentage',
                    'error_abs': 'error_absolute',
                })
                # 指定欄位順序
                cols = [
                    'period', 'test_date', 'stock_id', 'model_name',
                    'predicted_value', 'actual_value', 'error_percentage', 'error_absolute'
                ]
                df_hist = df_hist[[c for c in cols if c in df_hist.columns]]
                out_csv = os.path.join(cfg.output_dir, f"{stock_id}_{model_name}_backtest_history.csv")
                df_hist.to_csv(out_csv, index=False, encoding='utf-8-sig')
    except Exception:
        pass

    # 保存最佳模型名稱供單次預測使用
    try:
        from .param_store import save_best_model, _load_all, _save_all
        if backtest_results.get('best_model'):
            save_best_model(stock_id, backtest_results['best_model'])

        # 保存各模型的回測結果（包含趨勢準確率）
        data = _load_all()
        stock_data = data.setdefault(stock_id, {})

        results_all = backtest_results.get('results', {})
        for model_name, result in results_all.items():
            if "error" not in result:
                backtest_key = f"{model_name}_backtest_result"
                stock_data[backtest_key] = {
                    "mape": result.get("mape", 0),
                    "rmse": result.get("rmse", 0),
                    "trend_accuracy": result.get("trend_accuracy", 0),
                    "n_predictions": result.get("n_predictions", 0)
                }

        _save_all(data)
    except Exception as e:
        print(f"保存回測結果失敗: {e}")
        pass

    return {
        "stock_id": stock_id,
        "data_points": len(feat_df),
        "date_range": f"{feat_df['date'].min().strftime('%Y-%m')} ~ {feat_df['date'].max().strftime('%Y-%m')}",
        "warnings": warnings,
        "backtest": backtest_results
    }
