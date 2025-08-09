from __future__ import annotations
import argparse
import json
import os
import sys
import pandas as pd
from .config import cfg, ensure_dirs
from .db import load_monthly_revenue, latest_month_in_db, fetch_schema_overview
from .features import to_monthly_df, build_features
from .predictor import choose_best_model, forecast_with_model
from .param_store import get_best_model
from .scenarios import expand_scenarios
from .anomaly import anomaly_checks
from .visualization import plot_history_vs_forecast, plot_errors, plot_scenarios


def _safe_setup_stdout():
    try:
        # 避免 Windows cp950 編碼錯誤
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def _p(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.write(msg.encode("utf-8", "ignore").decode("utf-8", "ignore") + "\n")
        except Exception:
            pass


def to_utf8_sig(path: str) -> str:
    # Windows cp950 相容輸出
    return path


def run_forecast(stock_id: str) -> dict:
    ensure_dirs()
    rows, warnings = load_monthly_revenue(stock_id)
    hist_df = to_monthly_df(rows)
    if hist_df.empty:
        raise SystemExit(f"{stock_id} 無月營收資料")

    feat_df = build_features(hist_df)
    # 優先使用回測/調校保存的最佳模型
    preferred = get_best_model(stock_id)
    if preferred:
        best_name, pred_point, metrics_df = forecast_with_model(feat_df, stock_id=stock_id, model_name=preferred)
    else:
        best_name, pred_point, metrics_df = choose_best_model(feat_df, stock_id=stock_id)

    # 展開情境
    scenarios_df = expand_scenarios(pred_point, hist_df)

    # 先以基準情境作為 anomaly 檢查的輸入
    baseline = scenarios_df[scenarios_df["scenario"] == "baseline"][
        ["date", "forecast_value", "lower_bound", "upper_bound"]
    ].copy()
    checked = anomaly_checks(hist_df, baseline)

    # 用調整後值覆寫 baseline，再合併三情境輸出（保守/樂觀仍保留區間，供參考）
    scenarios_df = scenarios_df.merge(
        checked[["date", "adjusted_value", "anomaly_flag"]], on="date", how="left"
    )
    scenarios_df.loc[scenarios_df["scenario"] == "baseline", "forecast_value"] = scenarios_df.loc[
        scenarios_df["scenario"] == "baseline", "adjusted_value"
    ]
    scenarios_df["anomaly_flag"] = scenarios_df["anomaly_flag"].fillna(0).astype(int)
    scenarios_df = scenarios_df.drop(columns=["adjusted_value"], errors="ignore")

    # 輸出 CSV / JSON
    out_base = os.path.join(cfg.output_dir, f"{stock_id}_forecast")
    csv_path = to_utf8_sig(out_base + ".csv")
    json_path = to_utf8_sig(out_base + ".json")

    # 轉換日期格式 YYYY-MM
    out_df = scenarios_df.copy()
    out_df["date"] = pd.to_datetime(out_df["date"]).dt.strftime("%Y-%m")
    out_df = out_df[["date", "scenario", "forecast_value", "lower_bound", "upper_bound", "anomaly_flag"]]
    out_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(json_path, "w", encoding="utf-8-sig") as f:
        f.write(out_df.to_json(orient="records", force_ascii=False))

    # 視覺化
    hist_plot = plot_history_vs_forecast(hist_df, checked.rename(columns={"adjusted_value": "forecast_value"}))
    err_plot = plot_errors(metrics_df)
    sc_plot = plot_scenarios(scenarios_df)

    # 友善中文輸出（格式化數字）
    def fmt(v):
        try:
            return f"{float(v):,.0f}"
        except Exception:
            return str(v)

    pretty = scenarios_df.copy()
    # 轉換日期為 YYYY-MM 以利 JSON 序列化
    pretty["date"] = pd.to_datetime(pretty["date"]).dt.strftime("%Y-%m")
    pretty["forecast_value_fmt"] = pretty["forecast_value"].apply(fmt)
    pretty["lower_bound_fmt"] = pretty["lower_bound"].apply(fmt)
    pretty["upper_bound_fmt"] = pretty["upper_bound"].apply(fmt)

    result = {
        "最佳模型": best_name,
        "CSV路徑": csv_path,
        "JSON路徑": json_path,
        "歷史對比圖": hist_plot,
        "誤差圖": err_plot,
        "情境圖": sc_plot,
        "警告": warnings,
        "預測摘要": pretty[["date", "scenario", "forecast_value_fmt", "lower_bound_fmt", "upper_bound_fmt", "anomaly_flag"]]
            .rename(columns={
                "date": "日期",
                "scenario": "情境",
                "forecast_value_fmt": "預測值",
                "lower_bound_fmt": "下界",
                "upper_bound_fmt": "上界",
                "anomaly_flag": "異常",
            })
            .to_dict(orient="records"),
    }
    # 為了相容現有流程與測試，加入英文鍵別名
    result.update({
        "best_model": best_name,
        "csv": csv_path,
        "json": json_path,
        "history_plot": hist_plot,
        "error_plot": err_plot,
        "scenarios_plot": sc_plot,
        "warnings": warnings,
    })
    return result


def run_roll_check(stock_id: str, last_known_month: str | None) -> bool:
    """每日檢查是否有新資料（最新月份變更）。有新資料則回傳 True。"""
    latest = latest_month_in_db(stock_id)
    if latest != last_known_month:
        return True
    return False


def run_menu():
    _safe_setup_stdout()
    _p("=== 台灣股市營收預測系統 選單 ===")
    while True:
        _p("1) 單次預測（輸出CSV/JSON與圖表）")
        _p("2) 啟動每日滾動檢查模式（需常駐）")
        _p("3) 查詢資料庫最新月份")
        _p("4) 檢視資料庫重點表格與欄位")
        _p("q) 離開")
        sel = input("> 請輸入選項: ").strip().lower()
        if sel == "1":
            stock_id = input("> 請輸入股票代碼(4碼): ").strip()
            try:
                result = run_forecast(stock_id)
                _p(json.dumps(result, ensure_ascii=False, indent=2))
            except SystemExit as e:
                _p(str(e))
            except Exception as e:
                _p(f"執行失敗: {e}")
        elif sel == "2":
            stock_id = input("> 請輸入股票代碼(4碼): ").strip()
            _p("將開始每日檢查模式，按 Ctrl+C 可中止。")
            try:
                import time
                last = latest_month_in_db(stock_id)
                _p(f"初始最新月份: {last}")
                while True:
                    if run_roll_check(stock_id, last):
                        _p("偵測到新資料，重新執行預測...")
                        result = run_forecast(stock_id)
                        _p(json.dumps(result, ensure_ascii=False, indent=2))
                        last = latest_month_in_db(stock_id)
                    time.sleep(24 * 60 * 60)
            except KeyboardInterrupt:
                _p("已停止每日檢查模式")
        elif sel == "3":
            stock_id = input("> 請輸入股票代碼(4碼): ").strip()
            _p(f"最新月份: {latest_month_in_db(stock_id)}")
        elif sel == "4":
            _p(json.dumps(fetch_schema_overview(), ensure_ascii=False, indent=2))
        elif sel in {"q", "quit", "exit"}:
            _p("再見！")
            break
        else:
            _p("無效選項，請重試。\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="台灣股市營收滾動預測系統")
    parser.add_argument("stock_id", nargs="?", help="股票代碼（4碼）")
    parser.add_argument("--roll", action="store_true", help="啟用每日滾動檢查模式（偵測新資料即重新預測）")
    parser.add_argument("--menu", action="store_true", help="進入互動式選單模式")
    args = parser.parse_args(argv)

    if args.menu or args.stock_id is None:
        run_menu()
        return 0

    _safe_setup_stdout()
    if args.roll:
        # 簡易輪詢模式（示範）：實務上可改用排程或檔案監控
        import time
        last = latest_month_in_db(args.stock_id)
        _p(f"初始最新月份: {last}")
        while True:
            if run_roll_check(args.stock_id, last):
                _p("偵測到新資料，重新執行預測...")
                result = run_forecast(args.stock_id)
                _p(json.dumps(result, ensure_ascii=False, indent=2))
                last = latest_month_in_db(args.stock_id)
            time.sleep(24 * 60 * 60)  # 每日檢查一次
    else:
        result = run_forecast(args.stock_id)
        _p(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())

