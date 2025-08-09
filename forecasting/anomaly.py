from __future__ import annotations
import numpy as np
import pandas as pd


def anomaly_checks(df_hist: pd.DataFrame, df_pred: pd.DataFrame) -> pd.DataFrame:
    """
    根據規則標記/調整異常：
    - 預測值 > 1.5 × 歷史最大營收 → anomaly=1
    - ASP/毛利率穩定但營收成長 > 30% → 假設無 ASP/毛利率欄位，改用近12月平均做穩定代理
    - 季節性偏差 > 3× 歷史標準差 → 以同月份歷史均值/標準差比較
    df_pred 需包含: date, forecast_value
    回傳新增欄位: anomaly_flag, adjusted_value, lower_bound, upper_bound
    """
    out = df_pred.copy()

    # 規則1：相對歷史最大值
    hist_max = float(df_hist["revenue"].max()) if not df_hist.empty else np.nan

    # 規則2：近12月均值作為穩定基準
    hist_ma12 = (
        df_hist.sort_values("date")["revenue"].rolling(12, min_periods=6).mean().iloc[-1]
        if len(df_hist) > 0
        else np.nan
    )

    # 規則3：季節性分組
    hist_by_month = df_hist.copy()
    if not hist_by_month.empty:
        hist_by_month["month"] = hist_by_month["date"].dt.month

    flags = []
    adjusted = []
    lowers = []
    uppers = []

    for _, r in out.iterrows():
        fv = float(r["forecast_value"]) if pd.notna(r["forecast_value"]) else np.nan
        date = pd.to_datetime(r["date"]).to_period("M").to_timestamp()
        m = date.month
        flag = 0
        lb = float(r.get("lower_bound", np.nan))
        ub = float(r.get("upper_bound", np.nan))
        adj = fv

        if pd.notna(hist_max) and fv > 1.5 * hist_max:
            flag = 1
            adj = min(fv, 1.5 * hist_max)

        if pd.notna(hist_ma12):
            # 若近12月均值為穩定且本期 > 1.3x 均值
            if fv > 1.3 * hist_ma12:
                flag = 1
                # 平滑到 1.3x
                adj = min(adj, 1.3 * hist_ma12)

        if not hist_by_month.empty:
            mu = hist_by_month.loc[hist_by_month["month"] == m, "revenue"].mean()
            sd = hist_by_month.loc[hist_by_month["month"] == m, "revenue"].std(ddof=0)
            if pd.notna(mu) and pd.notna(sd) and sd > 0:
                if abs(fv - mu) > 3 * sd:
                    flag = 1
                    # 將值調整到 3sd 邊界
                    adj = mu + np.sign(fv - mu) * 3 * sd

        # 信賴區間也跟著調整以免上下界亂序
        if pd.notna(lb) and pd.notna(ub):
            if adj < lb:
                lb = adj * 0.95
            if adj > ub:
                ub = adj * 1.05

        flags.append(flag)
        adjusted.append(adj)
        lowers.append(lb)
        uppers.append(ub)

    out["anomaly_flag"] = flags
    out["adjusted_value"] = adjusted
    out["lower_bound"] = lowers
    out["upper_bound"] = uppers
    return out

