from __future__ import annotations
import numpy as np
import pandas as pd


def scenario_bands(point_forecast: float, base_std: float) -> dict:
    """根據點估與基礎標準差，產生三種情境與95%區間。
    - Conservative: 均值 - 0.5*std，區間 ±1.96 sd
    - Baseline: 均值
    - Optimistic: 均值 + 0.5*std
    """
    z = 1.96
    scenarios = {}
    for name, shift in {
        "conservative": -0.5,
        "baseline": 0.0,
        "optimistic": 0.5,
    }.items():
        mu = point_forecast + shift * base_std
        lower = max(0.0, mu - z * base_std)
        upper = mu + z * base_std
        scenarios[name] = {
            "forecast_value": mu,
            "lower_bound": lower,
            "upper_bound": upper,
        }
    return scenarios


def expand_scenarios(df_point: pd.DataFrame, hist_df: pd.DataFrame) -> pd.DataFrame:
    """將單點預測展開為三種情境。
    base_std 估計：使用過去12個月 revenue 的標準差（若不足則用整體）。
    """
    if df_point.empty:
        return df_point
    hist_sorted = hist_df.sort_values("date")
    if len(hist_sorted) >= 12:
        base_std = float(hist_sorted["revenue"].tail(12).std(ddof=0))
    else:
        base_std = float(hist_sorted["revenue"].std(ddof=0)) if not hist_sorted.empty else 0.0
    base_std = base_std if np.isfinite(base_std) and base_std > 0 else max(1.0, df_point["forecast_value"].std(ddof=0) if "forecast_value" in df_point.columns else 1.0)

    records = []
    for _, r in df_point.iterrows():
        d = r["date"]
        pf = float(r["forecast_value"]) if pd.notna(r["forecast_value"]) else 0.0
        sc = scenario_bands(pf, base_std)
        for name, vals in sc.items():
            records.append({
                "date": d,
                "scenario": name,
                **vals,
            })
    return pd.DataFrame(records)

