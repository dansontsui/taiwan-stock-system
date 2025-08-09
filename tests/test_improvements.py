from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))

import os
import sqlite3
import pandas as pd


def create_db_with_years(tmp_path, years=6):
    db_path = os.path.join(tmp_path, "taiwan_stock_test.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE monthly_revenues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id TEXT,
            date TEXT,
            country TEXT,
            revenue REAL,
            revenue_month INTEGER,
            revenue_year INTEGER,
            created_at TEXT
        );
        """
    )
    rows = []
    base = 100.0
    start_year = 2019
    for y in range(start_year, start_year + years):
        for m in range(1, 13):
            date = f"{y}-{m:02d}-01"
            season = 1.0 + 0.1 * (1 if m in (3, 12) else 0)
            trend = 1.0 + 0.02 * (y - start_year)
            revenue = base * season * trend
            rows.append(("9999", date, "TW", revenue, m, y, date))
    cur.executemany(
        "INSERT INTO monthly_revenues (stock_id, date, country, revenue, revenue_month, revenue_year, created_at) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return db_path


def test_backtest_history_csv_export(tmp_path, monkeypatch):
    # 設定環境
    db_path = create_db_with_years(tmp_path, years=6)
    monkeypatch.setenv("TS_DB_PATH", db_path)
    monkeypatch.setenv("TS_ENABLE_PROPHET", "0")
    monkeypatch.setenv("TS_ENABLE_LSTM", "0")
    monkeypatch.setenv("TS_ENABLE_XGBOOST", "1")

    # 重新載入設定
    from importlib import reload
    import forecasting.config as config
    reload(config)

    # 執行回測並檢查 CSV
    from forecasting.backtest import run_backtest_analysis
    result = run_backtest_analysis("9999", window_months=12)
    assert "error" not in result
    out_dir = config.cfg.output_dir
    # XGBoost CSV 是否存在
    csv_path = os.path.join(out_dir, "9999_XGBoost_backtest_history.csv")
    assert os.path.exists(csv_path)

    # 內容欄位是否正確
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    expected_cols = [
        "period", "test_date", "stock_id", "model_name",
        "predicted_value", "actual_value", "error_percentage", "error_absolute"
    ]
    for c in expected_cols:
        assert c in df.columns


def test_param_store_loads_without_error(tmp_path, monkeypatch):
    # 環境與資料
    db_path = create_db_with_years(tmp_path, years=6)
    monkeypatch.setenv("TS_DB_PATH", db_path)
    monkeypatch.setenv("TS_ENABLE_PROPHET", "0")
    monkeypatch.setenv("TS_ENABLE_LSTM", "0")
    monkeypatch.setenv("TS_ENABLE_XGBOOST", "1")

    from importlib import reload
    import forecasting.config as config
    reload(config)

    # 儲存最佳參數
    from forecasting.param_store import save_best_params, get_best_params
    save_best_params("9999", "XGBoost", {"n_estimators": 50, "max_depth": 3})
    assert get_best_params("9999", "XGBoost") is not None

    # 構建特徵並呼叫選模（確保可載入參數不出錯）
    from forecasting.db import load_monthly_revenue
    from forecasting.features import to_monthly_df, build_features
    from forecasting.predictor import choose_best_model

    rows, _ = load_monthly_revenue("9999")
    feat = build_features(to_monthly_df(rows))
    name, pred, metrics = choose_best_model(feat, stock_id="9999")
    assert name in {"XGBoost", "SeasonalMA"}
    assert not pred.empty


def test_system_architecture_doc_exists():
    assert os.path.exists(os.path.join("forecasting", "SYSTEM_ARCHITECTURE.md"))


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))

