import re
from forecasting.interactive import generate_html_template


def test_trend_accuracy_percentage_rendering():
    stock_id = "9999"
    models_data = {
        "Prophet": {
            "history": [{"period": 1, "test_date": "2024-01", "predicted": 100.0, "actual": 110.0, "error_pct": 9.09}],
            "mape": 12.34,
            "trend_accuracy": 0.6321,  # fraction 0-1 from backtest
        },
        "XGBoost": {
            "history": [{"period": 1, "test_date": "2024-01", "predicted": 90.0, "actual": 100.0, "error_pct": 10.0}],
            "mape": 18.76,
            "trend_accuracy": 0.566,
        },
    }
    html = generate_html_template(stock_id, models_data)

    # 應顯示為百分比格式（例：63.2% / 56.6%），而不是 0.6%
    assert "63.2%" in html or "63.21%" in html
    assert "56.6%" in html or "56.60%" in html

    # 不應出現 0.6% 這種縮小 100 倍的錯誤
    assert "0.6%" not in html
