from __future__ import annotations
import math
from typing import List, Tuple
import pandas as pd


def to_monthly_df(rows: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    df = df.sort_values("date").drop_duplicates("date")
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    產生特徵：
    - y: revenue
    - 滯後值: lag1, lag3, lag6, lag12
    - 移動平均: ma3, ma6, ma12
    - 季節性: month_1..month_12（one-hot）
    自動處理缺失值與異常值（以IQR裁剪）。
    """
    if df.empty:
        return df
    out = df.copy()
    out["y"] = out["revenue"].astype(float)

    for l in [1, 3, 6, 12]:
        out[f"lag{l}"] = out["y"].shift(l)
    for w in [3, 6, 12]:
        out[f"ma{w}"] = out["y"].rolling(window=w, min_periods=1).mean()

    # IQR 異常值裁剪
    q1 = out["y"].quantile(0.25)
    q3 = out["y"].quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - 3 * iqr, q3 + 3 * iqr
    out["y"] = out["y"].clip(lower=low, upper=high)

    # 季節性 one-hot
    out["month"] = out["date"].dt.month
    month_dummies = pd.get_dummies(out["month"], prefix="month", dtype=int)
    out = pd.concat([out, month_dummies], axis=1)

    # 缺失值處理：以前向填補為主，剩餘用整體中位數
    out = out.sort_values("date")
    out = out.ffill()
    for col in out.columns:
        if out[col].isna().any():
            if pd.api.types.is_numeric_dtype(out[col]):
                out[col] = out[col].fillna(out[col].median())
            else:
                out[col] = out[col].bfill()

    return out


def train_test_split_time(df: pd.DataFrame, backtest_years: int = 1) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df.copy(), df.copy()
    last_date = df["date"].max()
    cutoff = (last_date - pd.DateOffset(years=backtest_years)).to_period("M").to_timestamp()
    train_df = df[df["date"] < cutoff]
    test_df = df[df["date"] >= cutoff]
    return train_df, test_df

