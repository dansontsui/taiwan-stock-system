from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from .features import build_features, train_test_split_time
from .config import cfg
from .param_store import get_best_params, get_best_model


def _safe_import(module_name: str):
    try:
        return __import__(module_name)
    except Exception:
        return None


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return np.inf
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def train_prophet(df: pd.DataFrame, stock_id: Optional[str] = None) -> Tuple[object, pd.DataFrame, Dict[str, float]]:
    if not cfg.enable_prophet:
        raise ImportError("Prophet 已停用或未安裝")
    prophet = _safe_import("prophet") or _safe_import("fbprophet")
    if prophet is None:
        raise ImportError("Prophet 未安裝")
    from prophet import Prophet  # type: ignore

    data = df[["date", "y"]].rename(columns={"date": "ds", "y": "y"}).copy()
    # 讀取個股最佳參數
    best = get_best_params(stock_id, "Prophet") if stock_id else None
    kwargs = dict(weekly_seasonality=False, daily_seasonality=False, yearly_seasonality=True)
    if isinstance(best, dict):
        kwargs.update({k: v for k, v in best.items() if k in {
            'changepoint_prior_scale','seasonality_prior_scale','holidays_prior_scale','seasonality_mode','yearly_seasonality','weekly_seasonality','daily_seasonality'
        }})
    model = Prophet(**kwargs)
    # 設定更穩定的優化器，避免 macOS 權限問題
    try:
        model.fit(data)
    except Exception as e:
        # 如果遇到權限問題，使用更保守的設定重試
        if "Operation not permitted" in str(e):
            import logging
            logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
            model = Prophet(uncertainty_samples=0, **kwargs)  # 關閉不確定性採樣
            model.fit(data)
        else:
            raise e
    future = model.make_future_dataframe(periods=1, freq="MS")
    forecast = model.predict(future)
    pred = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(1)
    pred = pred.rename(columns={"ds": "date", "yhat": "forecast_value", "yhat_lower": "lower_bound", "yhat_upper": "upper_bound"})
    metrics = {"MAPE": np.nan, "RMSE": np.nan}
    return model, pred, metrics


def train_lstm(df: pd.DataFrame, stock_id: Optional[str] = None) -> Tuple[object, pd.DataFrame, Dict[str, float]]:
    if not cfg.enable_lstm:
        raise ImportError("LSTM 已停用或未安裝")
    tf = _safe_import("tensorflow")
    if tf is None:
        raise ImportError("TensorFlow 未安裝")
    import tensorflow as tf  # type: ignore

    # 使用簡單單變量 LSTM，視為 demo，可擴充
    series = df["y"].astype(float).values.reshape(-1, 1)
    win = 12
    X, y = [], []
    for i in range(len(series) - win):
        X.append(series[i : i + win])
        y.append(series[i + win])
    if len(X) < 10:
        raise RuntimeError("資料不足以訓練 LSTM")
    X = np.array(X)
    y = np.array(y)

    # 讀取個股最佳參數
    best = get_best_params(stock_id, "LSTM") if stock_id else None
    lstm_units = int(best.get('lstm_units', 32)) if isinstance(best, dict) else 32
    win = int(best.get('window_size', 12)) if isinstance(best, dict) else 12
    epochs = int(best.get('epochs', 50)) if isinstance(best, dict) else 50
    batch_size = int(best.get('batch_size', 16)) if isinstance(best, dict) else 16

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(win, 1)),
        tf.keras.layers.LSTM(lstm_units),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)

    # 產生一步預測
    last_win = series[-win:][None, :, :]
    yhat = float(model.predict(last_win, verbose=0).reshape(-1)[0])
    pred = pd.DataFrame({
        "date": [pd.to_datetime(df["date"].max()) + pd.offsets.MonthBegin(1)],
        "forecast_value": [yhat],
    })
    metrics = {"MAPE": np.nan, "RMSE": np.nan}
    return model, pred, metrics


def train_xgboost(df: pd.DataFrame, stock_id: Optional[str] = None) -> Tuple[object, pd.DataFrame, Dict[str, float]]:
    if not cfg.enable_xgboost:
        raise ImportError("XGBoost 已停用或未安裝")
    xgb = _safe_import("xgboost")
    if xgb is None:
        raise ImportError("XGBoost 未安裝")
    from xgboost import XGBRegressor  # type: ignore

    # 取特徵與標的
    target = "y"
    feature_cols = [c for c in df.columns if c not in {"date", "revenue", target, "actual_month"}]

    train_df, test_df = train_test_split_time(df)
    # 確保特徵都是數值型
    X_train = train_df[feature_cols].select_dtypes(include=[np.number]).values
    y_train = train_df[target].values
    X_test = test_df[feature_cols].select_dtypes(include=[np.number]).values
    y_test = test_df[target].values

    best = get_best_params(stock_id, "XGBoost") if stock_id else None
    params = dict(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=cfg.random_seed,
        objective="reg:squarederror",
    )
    if isinstance(best, dict):
        params.update({k: v for k, v in best.items() if k in params})
    model = XGBRegressor(**params)
    model.fit(X_train, y_train)
    # 若訓練集為空（例如回測視窗太短），使用全部資料訓練
    if X_train.size == 0 or y_train.size == 0:
        X_train = df[feature_cols].select_dtypes(include=[np.number]).values
        y_train = df[target].values
        X_test = np.empty((0, X_train.shape[1])) if X_train.size > 0 else np.empty((0, 0))
        y_test = np.array([])



    # 測試集評估
    if len(X_test) > 0:
        y_pred = model.predict(X_test)
        metrics = {"MAPE": mape(y_test, y_pred), "RMSE": rmse(y_test, y_pred)}
    else:
        metrics = {"MAPE": np.nan, "RMSE": np.nan}

    # 下一期特徵（使用最後一列特徵往前移）
    last_row = df.iloc[-1].copy()
    next_date = pd.to_datetime(df["date"].max()) + pd.offsets.MonthBegin(1)
    # 滯後特徵更新：簡化處理，使用現有 ma 與 lag 的延伸
    next_feat = last_row.copy()
    # 不能用當期 y，先以 ma12 作 proxy
    if "ma12" in df.columns:
        next_feat[target] = float(df["ma12"].iloc[-1])
    # 移除非特徵欄，確保只有數值特徵
    numeric_features = [c for c in feature_cols if c in df.select_dtypes(include=[np.number]).columns]
    next_feat_values = next_feat[numeric_features].values.reshape(1, -1)
    yhat = float(model.predict(next_feat_values)[0])
    pred = pd.DataFrame({
        "date": [next_date],
        "forecast_value": [yhat],
    })
    return model, pred, metrics


def choose_best_model(df: pd.DataFrame, stock_id: Optional[str] = None) -> Tuple[str, pd.DataFrame, pd.DataFrame]:
    """嘗試 Prophet / LSTM / XGBoost，回傳最佳模型名稱、點估預測、評估指標表。未安裝的自動跳過。"""
    models = []
    metrics_rows = []

    # 逐一嘗試，忽略安裝問題
    for name, trainer in [
        ("Prophet", train_prophet),
        ("LSTM", train_lstm),
        ("XGBoost", train_xgboost),
    ]:
        try:
            _, pred, metrics = trainer(df, stock_id=stock_id)
            models.append((name, pred, metrics))
        except Exception as e:
            metrics_rows.append({"model": name, "MAPE": np.nan, "RMSE": np.nan, "note": str(e)})

    # 若沒有任何模型成功，回退到簡單季節性移動平均
    if not models:
        preds = df[["date", "y"]].copy()
        preds["ma12"] = preds["y"].rolling(12, min_periods=1).mean()
        yhat = float(preds["ma12"].iloc[-1])
        pred = pd.DataFrame({
            "date": [pd.to_datetime(df["date"].max()) + pd.offsets.MonthBegin(1)],
            "forecast_value": [yhat],
        })
        metrics_df = pd.DataFrame(metrics_rows + [{"model": "SeasonalMA", "MAPE": np.nan, "RMSE": np.nan}])
        return "SeasonalMA", pred, metrics_df

    # 選擇 MAPE 最低者（若空則以 RMSE）
    for name, pred, metrics in models:
        metrics_rows.append({"model": name, **metrics})
    metrics_df = pd.DataFrame(metrics_rows)

    best_row = metrics_df.sort_values(by=["MAPE", "RMSE"], na_position="last").iloc[0]
    best_name = best_row["model"]

    # 找出對應預測
    matching_models = [p for (n, p, _) in models if n == best_name]
    if matching_models:
        best_pred = matching_models[0]
    else:
        # 回退到 SeasonalMA
        preds = df[["date", "y"]].copy()
        preds["ma12"] = preds["y"].rolling(12, min_periods=1).mean()
        yhat = float(preds["ma12"].iloc[-1])
        pred = pd.DataFrame({
            "date": [pd.to_datetime(df["date"].max()) + pd.offsets.MonthBegin(1)],
            "forecast_value": [yhat],
        })
        best_pred = pred
        best_name = "SeasonalMA"
    return best_name, best_pred, metrics_df


def forecast_with_model(df: pd.DataFrame, stock_id: Optional[str], model_name: str) -> Tuple[str, pd.DataFrame, pd.DataFrame]:
    """依指定模型名稱進行預測，回傳 (模型名稱, 預測點估, 指標)"""
    mapping = {
        "Prophet": train_prophet,
        "LSTM": train_lstm,
        "XGBoost": train_xgboost,
    }
    trainer = mapping.get(model_name)
    if trainer is None:
        # 回退自動選模
        return choose_best_model(df, stock_id=stock_id)
    try:
        _, pred, metrics = trainer(df, stock_id=stock_id)
        metrics_df = pd.DataFrame([{ "model": model_name, **metrics }])
        return model_name, pred, metrics_df
    except Exception:
        # 若指定模型失敗，回退自動選模
        return choose_best_model(df, stock_id=stock_id)

