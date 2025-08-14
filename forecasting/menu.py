#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣股市營收預測系統 - 互動式選單
提供完整的預測、回測、參數調校與多變量特徵整合功能
"""
from __future__ import annotations
import os
import sys
import json
import time
from typing import Optional

# 處理相對導入問題
if __name__ == "__main__":
    # 當直接執行時，調整路徑
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    # 切換到專案根目錄以確保資料庫路徑正確
    os.chdir(project_root)
    from forecasting.config import cfg, ensure_dirs, setup_prophet_logging
    from forecasting.db import latest_month_in_db, fetch_schema_overview
    from forecasting.cli import run_forecast, run_roll_check, run_forecast_with_specific_model
else:
    # 當作為模組導入時，使用相對導入
    from .config import cfg, ensure_dirs, setup_prophet_logging
    from .db import latest_month_in_db, fetch_schema_overview
    from .cli import run_forecast, run_roll_check, run_forecast_with_specific_model


def _safe_setup_stdout():
    """設定標準輸出編碼，避免 Windows cp950 錯誤"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def _p(msg: str):
    """安全輸出中文訊息"""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.write(msg.encode("utf-8", "ignore").decode("utf-8", "ignore") + "\n")
        except Exception:
            pass


def analyze_prediction_trends(stock_id: str, baseline_values: dict) -> dict:
    """分析預測趨勢方向"""
    try:
        if __name__ == "__main__":
            from forecasting.db import load_monthly_revenue
        else:
            from .db import load_monthly_revenue

        # 載入歷史資料
        rows, _ = load_monthly_revenue(stock_id)
        if not rows:
            return None

        # 轉換為DataFrame並排序
        import pandas as pd
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
        df = df.sort_values("date").drop_duplicates("date")

        if df.empty:
            return None

        # 獲取最新營收資料
        latest_row = df.iloc[-1]
        latest_revenue = float(latest_row["revenue"])
        latest_month = latest_row["date"].strftime("%Y-%m")

        # 計算預測月份
        next_month = (latest_row["date"] + pd.offsets.MonthBegin(1)).strftime("%Y-%m")

        # 分析各模型的趨勢方向
        model_trends = {}
        for model_name, value_str in baseline_values.items():
            try:
                # 移除千分位符號並轉換為數值
                predicted_value = float(value_str.replace(",", ""))
                change_amount = predicted_value - latest_revenue
                change_percent = (change_amount / latest_revenue) * 100
                trend_direction = "上漲" if change_amount > 0 else "下跌"

                model_trends[model_name] = {
                    "predicted_value": predicted_value,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "trend_direction": trend_direction
                }
            except (ValueError, TypeError):
                continue

        return {
            "latest_month": latest_month,
            "latest_revenue": latest_revenue,
            "latest_revenue_formatted": f"{latest_revenue:,.0f}",
            "prediction_month": next_month,
            "model_trends": model_trends
        }

    except Exception as e:
        print(f"趨勢分析失敗: {e}")
        return None


def get_backtest_metrics(stock_id: str) -> dict:
    """獲取回測指標（趨勢準確率、MAPE、RMSE）"""
    try:
        if __name__ == "__main__":
            from forecasting.param_store import _load_all
        else:
            from .param_store import _load_all

        # 從 best_params.json 中讀取回測結果
        data = _load_all()
        stock_data = data.get(stock_id, {})

        # 查找回測結果
        metrics_data = {}
        for key, value in stock_data.items():
            if key.endswith("_backtest_result") and isinstance(value, dict):
                model_name = key.replace("_backtest_result", "")
                metrics_data[model_name] = {
                    "trend_accuracy": value.get("trend_accuracy"),
                    "mape": value.get("mape"),
                    "rmse": value.get("rmse"),
                    "n_predictions": value.get("n_predictions")
                }

        return metrics_data if metrics_data else None

    except Exception as e:
        print(f"獲取回測指標失敗: {e}")
        return None


def get_backtest_trend_accuracy(stock_id: str) -> dict:
    """獲取回測趨勢準確率（向後相容）"""
    metrics = get_backtest_metrics(stock_id)
    if metrics:
        return {model: data["trend_accuracy"] for model, data in metrics.items()
                if data["trend_accuracy"] is not None}
    return None


def show_main_menu():
    """顯示主選單"""
    _p("\n" + "="*60)
    _p("🏢 台灣股市營收預測系統 - 互動式選單")
    _p("="*60)
    _p("📊 基本功能")
    _p("  1) 單次預測（輸出CSV/JSON與圖表）")
    _p("  2) 啟動每日滾動檢查模式（需常駐）")
    _p("  3) 查詢資料庫最新月份")
    _p("  4) 檢視資料庫重點表格與欄位")
    _p("")
    _p("🔧 進階功能")
    _p("  5) 回測與模型評估")
    _p("  6) 參數調校與優化")
    _p("  7) 多變量特徵整合")
    _p("  8) 批量預測多檔股票")
    _p("")
    _p("📊 預測結果統計")
    _p("  11) 查看預測結果統計表")
    _p("  12) 匯出預測結果到CSV")
    _p("  13) 手動添加預測結果到統計表")
    _p("")
    _p("⚙️  系統設定")
    _p("  9) 模型啟用設定")
    _p("  10) 系統狀態檢查")
    _p("")
    _p("  q) 離開系統")
    _p("-"*60)


def handle_single_forecast():
    """處理單次預測 - 同時顯示 XGBoost 和 Prophet 兩種模型結果"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return

    try:
        _p(f"🔄 正在預測 {stock_id} 的營收...")

        # 獲取回測最佳模型
        if __name__ == "__main__":
            from forecasting.param_store import get_best_model
        else:
            from .param_store import get_best_model
        best_model = get_best_model(stock_id)

        # 同時執行 XGBoost 和 Prophet 預測
        results = {}
        model_names = ["XGBoost", "Prophet"]

        for model_name in model_names:
            try:
                _p(f"   🔄 執行 {model_name} 預測...")
                result = run_forecast_with_specific_model(stock_id, model_name)
                results[model_name] = result
                _p(f"   ✅ {model_name} 預測完成")
            except Exception as e:
                _p(f"   ❌ {model_name} 預測失敗: {e}")
                results[model_name] = None

        _p("\n" + "="*60)
        _p("📊 雙模型預測結果比較")
        _p("="*60)

        # 獲取回測指標
        backtest_metrics = get_backtest_metrics(stock_id)

        # 顯示每個模型的結果
        for model_name in model_names:
            result = results.get(model_name)
            if result is None:
                continue

            # 標註是否為回測最佳模型
            is_best = (best_model == model_name)
            best_marker = " 🏆 (回測最佳)" if is_best else ""

            # 獲取該模型的回測誤差率
            error_info = ""
            if backtest_metrics and model_name in backtest_metrics:
                metrics = backtest_metrics[model_name]
                mape = metrics.get("mape")
                if mape is not None:
                    error_info = f" (回測誤差率: {mape:.1f}%)"

            _p(f"\n📈 {model_name} 模型{best_marker}{error_info}")
            _p("-" * 40)
            _p(f"📁 CSV檔案: {result['CSV路徑']}")
            _p(f"📁 JSON檔案: {result['JSON路徑']}")
            _p(f"📈 圖表檔案: {result['歷史對比圖']}")

            if result['警告']:
                _p("⚠️  警告訊息:")
                for warning in result['警告']:
                    _p(f"   - {warning}")

            _p("📋 預測摘要:")
            for item in result['預測摘要']:
                _p(f"   {item['日期']} {item['情境']}: {item['預測值']} (異常: {item['異常']})")

        # 顯示模型比較摘要
        _p("\n" + "="*60)
        _p("📊 模型比較摘要")
        _p("="*60)

        if best_model:
            _p(f"🏆 回測最佳模型: {best_model}")
        else:
            _p("ℹ️  尚未進行回測，建議先執行選單功能 5 進行回測分析")

        # 比較基準情境預測值
        baseline_values = {}
        for model_name in model_names:
            result = results.get(model_name)
            if result and result['預測摘要']:
                for item in result['預測摘要']:
                    if item['情境'] == 'baseline':
                        baseline_values[model_name] = item['預測值']
                        break

        if len(baseline_values) >= 2:
            _p("\n📊 基準情境預測值比較:")
            for model_name, value in baseline_values.items():
                is_best = (best_model == model_name)
                best_marker = " 🏆" if is_best else ""
                _p(f"   {model_name}: {value}{best_marker}")

        # 顯示趨勢分析和回測準確率
        _p("\n" + "="*60)
        _p("📈 趨勢分析與回測表現")
        _p("="*60)

        # 獲取歷史資料進行趨勢分析
        trend_analysis = analyze_prediction_trends(stock_id, baseline_values)
        if trend_analysis:
            _p(f"📅 最新營收月份: {trend_analysis['latest_month']}")
            _p(f"💰 最新營收金額: {trend_analysis['latest_revenue_formatted']}")
            _p(f"📊 預測月份: {trend_analysis['prediction_month']}")

            _p("\n🔍 各模型趨勢預測:")
            for model_name in model_names:
                if model_name in trend_analysis['model_trends']:
                    trend_info = trend_analysis['model_trends'][model_name]
                    is_best = (best_model == model_name)
                    best_marker = " 🏆" if is_best else ""

                    trend_icon = "📈" if trend_info['trend_direction'] == "上漲" else "📉"
                    _p(f"   {trend_icon} {model_name}{best_marker}: {trend_info['trend_direction']} "
                       f"({trend_info['change_percent']:+.1f}%)")

        # 顯示回測詳細指標
        if backtest_metrics:
            _p("\n📊 回測表現指標:")
            for model_name in model_names:
                if model_name in backtest_metrics:
                    metrics = backtest_metrics[model_name]
                    is_best = (best_model == model_name)
                    best_marker = " 🏆" if is_best else ""

                    mape = metrics.get("mape")
                    trend_accuracy = metrics.get("trend_accuracy")
                    n_predictions = metrics.get("n_predictions", 0)

                    if mape is not None and trend_accuracy is not None:
                        # MAPE 評級
                        mape_icon = "✅" if mape <= 8.0 else "⚠️" if mape <= 15.0 else "❌"
                        # 趨勢準確率評級
                        trend_icon = "✅" if trend_accuracy >= 0.8 else "⚠️" if trend_accuracy >= 0.6 else "❌"

                        _p(f"   {model_name}{best_marker}:")
                        _p(f"     {mape_icon} 誤差率(MAPE): {mape:.1f}%")
                        _p(f"     {trend_icon} 趨勢準確率: {trend_accuracy:.1%}")
                        _p(f"     📊 回測次數: {n_predictions} 次")
                    else:
                        _p(f"   ❓ {model_name}: 回測資料不完整")
        else:
            _p("\nℹ️  尚無回測指標資料，建議先執行選單功能 5 進行回測分析")

    except Exception as e:
        _p(f"❌ 預測失敗: {e}")


def handle_rolling_check():
    """處理每日滾動檢查"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return
    
    _p("🔄 將開始每日檢查模式，按 Ctrl+C 可中止...")
    try:
        last = latest_month_in_db(stock_id)
        _p(f"📅 初始最新月份: {last}")
        
        while True:
            if run_roll_check(stock_id, last):
                _p("🆕 偵測到新資料，重新執行預測...")
                result = run_forecast(stock_id)
                _p("✅ 預測更新完成！")
                _p(json.dumps(result, ensure_ascii=False, indent=2))
                last = latest_month_in_db(stock_id)
            else:
                _p("⏳ 無新資料，等待中...")
            
            time.sleep(24 * 60 * 60)  # 每日檢查一次
            
    except KeyboardInterrupt:
        _p("⏹️  已停止每日檢查模式")


def handle_latest_month():
    """查詢資料庫最新月份"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return
    
    latest = latest_month_in_db(stock_id)
    _p(f"📅 {stock_id} 最新營收月份: {latest}")


def handle_schema_overview():
    """檢視資料庫重點表格與欄位"""
    _p("🗄️  資料庫重點表格與欄位:")
    schema = fetch_schema_overview()
    _p(json.dumps(schema, ensure_ascii=False, indent=2))


def handle_backtest():
    """處理回測與模型評估"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return

    window_months = input("📅 請輸入訓練視窗月數 (預設36): ").strip()
    try:
        window_months = int(window_months) if window_months else 36
    except ValueError:
        window_months = 36

    _p(f"🔬 開始回測 {stock_id}，訓練視窗: {window_months} 個月...")

    try:
        if __name__ == "__main__":
            from forecasting.backtest import run_backtest_analysis
        else:
            from .backtest import run_backtest_analysis
        result = run_backtest_analysis(stock_id, window_months)

        if "error" in result:
            _p(f"❌ 回測失敗: {result['error']}")
            return

        _p("✅ 回測完成！")
        _p(f"📊 資料範圍: {result['date_range']}")
        _p(f"📈 資料點數: {result['data_points']}")
        _p("📁 已自動匯出最佳模型回測歷史CSV於 outputs/forecasts/")

        backtest = result['backtest']
        if backtest.get('best_model'):
            _p(f"🏆 最佳模型: {backtest['best_model']} (MAPE: {backtest['best_mape']:.2f}%)")
            _p(f"🎯 目標達成: {'✅' if backtest['meets_targets'] else '❌'}")

        _p("\n📋 模型表現摘要:")
        for item in backtest.get('summary', []):
            _p(f"   {item['模型']}: MAPE {item['MAPE']}, 趨勢準確率 {item['趨勢準確率']}")

        # 顯示最佳模型的詳細回測歷史
        if backtest.get('best_model') and backtest.get('results'):
            best_model_result = backtest['results'].get(backtest['best_model'])
            if best_model_result and 'history' in best_model_result:
                _p(f"\n📊 {backtest['best_model']} 詳細回測歷史:")
                _p("期數\t回測年月\t預測數據\t\t實際數據\t\t誤差(%)")
                _p("-" * 70)

                for record in best_model_result['history'][:10]:  # 顯示前10筆
                    pred_str = f"{record['predicted']:,.0f}"
                    actual_str = f"{record['actual']:,.0f}"
                    error_str = f"{record['error_pct']:.2f}%"
                    _p(f"{record['period']}\t{record['test_date']}\t{pred_str:>12}\t{actual_str:>12}\t{error_str:>8}")

                if len(best_model_result['history']) > 10:
                    _p(f"... (共 {len(best_model_result['history'])} 筆紀錄)")

                # 生成回測歷史圖表
                try:
                    if __name__ == "__main__":
                        from forecasting.visualization import plot_backtest_history
                    else:
                        from .visualization import plot_backtest_history

                    chart_path = plot_backtest_history(best_model_result, stock_id, backtest['best_model'])
                    _p(f"📈 回測歷史圖表已生成: {chart_path}")

                    # 生成互動式HTML表格（可滑鼠查看數字）
                    try:
                        if __name__ == "__main__":
                            from forecasting.interactive import save_backtest_history_html
                        else:
                            from .interactive import save_backtest_history_html
                        # 1) 生成最佳模型的單頁HTML（兼容），保留
                        csv_path = os.path.join(cfg.output_dir, f"{stock_id}_{backtest['best_model']}_backtest_history.csv")
                        html_path = save_backtest_history_html(stock_id, backtest['best_model'], csv_path)
                        if html_path:
                            _p(f"🖥️  互動式回測歷史已生成: {html_path}")

                        # 2) 生成所有模型的高互動分頁版HTML
                        if __name__ == "__main__":
                            from forecasting.interactive import create_interactive_backtest_html
                        else:
                            from .interactive import create_interactive_backtest_html
                        all_models = backtest.get('results', {})
                        html_multi = create_interactive_backtest_html(stock_id, all_models, cfg.output_dir)
                        if html_multi:
                            _p(f"🖥️  所有模型分頁版互動HTML: {html_multi}")
                    except Exception as html_e:
                        _p(f"⚠️  HTML 生成失敗: {html_e}")
                except Exception as chart_e:
                    _p(f"⚠️  圖表生成失敗: {chart_e}")

    except Exception as e:
        _p(f"❌ 回測失敗: {e}")


def handle_parameter_tuning():
    """處理參數調校與優化"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return

    # 詢問測試年數
    _p("📊 請選擇調校測試期間:")
    _p("  1) 1年 (預設，較快)")
    _p("  2) 2年 (更多驗證資料，可能更準確)")
    _p("  3) 3年 (最多驗證資料，較慢)")

    while True:
        test_choice = input("請選擇 (1-3): ").strip()
        if test_choice in ["1", "2", "3"]:
            test_years = int(test_choice)
            break
        _p("❌ 請輸入 1、2 或 3")

    _p(f"⚙️  開始參數調校（使用 {test_years} 年測試資料）...")
    _p("⚠️  此過程可能需要較長時間，請耐心等待...")

    try:
        if __name__ == "__main__":
            from forecasting.tuning import comprehensive_tuning
        else:
            from .tuning import comprehensive_tuning
        result = comprehensive_tuning(stock_id, test_years=test_years)

        if "error" in result:
            _p(f"❌ 參數調校失敗: {result['error']}")
            return

        _p("✅ 參數調校完成！")

        for model_name, tuning_result in result['tuning_results'].items():
            if "error" in tuning_result:
                _p(f"❌ {model_name}: {tuning_result['error']}")
            else:
                _p(f"🔧 {model_name}:")
                _p(f"   最佳 MAPE: {tuning_result['best_mape']:.2f}%")
                _p(f"   成功組合: {tuning_result['successful_combinations']}/{tuning_result['n_combinations']}")
                _p(f"   最佳參數: {tuning_result['best_params']}")

    except Exception as e:
        _p(f"❌ 參數調校失敗: {e}")


def handle_multivariate_features():
    """處理多變量特徵整合"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return

    _p("📊 開始多變量特徵整合...")

    try:
        if __name__ == "__main__":
            from forecasting.db import load_monthly_revenue
            from forecasting.features import to_monthly_df, build_features
            from forecasting.multivariate import integrate_multivariate_features, analyze_feature_importance
        else:
            from .db import load_monthly_revenue
            from .features import to_monthly_df, build_features
            from .multivariate import integrate_multivariate_features, analyze_feature_importance

        # 載入基礎資料
        rows, warnings = load_monthly_revenue(stock_id)
        if not rows:
            _p(f"❌ 無法載入 {stock_id} 的營收資料")
            return

        base_df = build_features(to_monthly_df(rows))

        # 整合多變量特徵
        enhanced_df = integrate_multivariate_features(base_df, stock_id)

        _p(f"✅ 特徵整合完成！")
        _p(f"📊 原始特徵: {len(base_df.columns)} 個")
        _p(f"📊 整合後特徵: {len(enhanced_df.columns)} 個")

        # 分析特徵重要性
        _p("🔍 分析特徵重要性...")
        importance_result = analyze_feature_importance(enhanced_df)

        if "error" not in importance_result:
            _p("📈 前10個重要特徵:")
            for item in importance_result['feature_importance'][:10]:
                _p(f"   {item['特徵']}: {item['重要性']}")
        else:
            _p(f"⚠️  特徵重要性分析失敗: {importance_result['error']}")

    except Exception as e:
        _p(f"❌ 多變量特徵整合失敗: {e}")


def handle_batch_forecast():
    """處理批量預測"""
    _p("📦 批量預測功能")
    stock_list = input("📈 請輸入股票代碼清單(用逗號分隔): ").strip()
    if not stock_list:
        _p("❌ 股票代碼清單不能為空")
        return
    
    stocks = [s.strip() for s in stock_list.split(",")]
    _p(f"🔄 開始批量預測 {len(stocks)} 檔股票...")
    
    results = {}
    for i, stock_id in enumerate(stocks, 1):
        try:
            _p(f"📊 [{i}/{len(stocks)}] 預測 {stock_id}...")
            result = run_forecast(stock_id)
            results[stock_id] = result
            _p(f"✅ {stock_id} 預測完成")
        except Exception as e:
            _p(f"❌ {stock_id} 預測失敗: {e}")
            results[stock_id] = {"error": str(e)}
    
    # 儲存批量結果
    ensure_dirs()
    batch_file = os.path.join(cfg.output_dir, "batch_forecast_results.json")
    with open(batch_file, "w", encoding="utf-8-sig") as f:
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
    
    _p(f"📁 批量預測結果已儲存至: {batch_file}")


def handle_model_settings():
    """處理模型啟用設定"""
    _p("⚙️  目前模型啟用狀態:")
    _p(f"   Prophet: {'✅ 啟用' if cfg.enable_prophet else '❌ 停用'}")
    _p(f"   LSTM: {'✅ 啟用' if cfg.enable_lstm else '❌ 停用'}")
    _p(f"   XGBoost: {'✅ 啟用' if cfg.enable_xgboost else '❌ 停用'}")
    _p("")
    _p("💡 要修改設定，請使用環境變數:")
    _p("   TS_ENABLE_PROPHET=1/0")
    _p("   TS_ENABLE_LSTM=1/0") 
    _p("   TS_ENABLE_XGBOOST=1/0")


def handle_system_status():
    """處理系統狀態檢查"""
    _p("🔍 系統狀態檢查:")
    
    # 檢查套件安裝狀態
    packages = {
        "prophet": "Prophet 時間序列預測",
        "xgboost": "XGBoost 梯度提升",
        "tensorflow": "TensorFlow 深度學習",
        "matplotlib": "圖表繪製",
        "pandas": "資料處理",
        "numpy": "數值計算"
    }
    
    for pkg, desc in packages.items():
        try:
            __import__(pkg)
            _p(f"   ✅ {desc} ({pkg})")
        except ImportError:
            _p(f"   ❌ {desc} ({pkg}) - 未安裝")
    
    # 檢查資料庫連線
    try:
        if __name__ == "__main__":
            from forecasting.db import get_conn
        else:
            from .db import get_conn
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM monthly_revenues")
            count = cur.fetchone()[0]
            _p(f"   ✅ 資料庫連線正常 (營收資料: {count:,} 筆)")
    except Exception as e:
        _p(f"   ❌ 資料庫連線失敗: {e}")
    
    # 檢查輸出目錄
    if os.path.exists(cfg.output_dir):
        _p(f"   ✅ 輸出目錄: {cfg.output_dir}")
    else:
        _p(f"   ⚠️  輸出目錄不存在，將自動建立: {cfg.output_dir}")


def main():
    """主程式入口"""
    _safe_setup_stdout()
    ensure_dirs()
    setup_prophet_logging()  # 設定 Prophet 穩定模式

    while True:
        show_main_menu()
        choice = input("🎯 請選擇功能 (1-13, q): ").strip().lower()
        
        if choice == "1":
            handle_single_forecast()
        elif choice == "2":
            handle_rolling_check()
        elif choice == "3":
            handle_latest_month()
        elif choice == "4":
            handle_schema_overview()
        elif choice == "5":
            handle_backtest()
        elif choice == "6":
            handle_parameter_tuning()
        elif choice == "7":
            handle_multivariate_features()
        elif choice == "8":
            handle_batch_forecast()
        elif choice == "9":
            handle_model_settings()
        elif choice == "10":
            handle_system_status()
        elif choice == "11":
            handle_prediction_results_view()
        elif choice == "12":
            handle_prediction_results_export()
        elif choice == "13":
            handle_manual_add_prediction()
        elif choice in {"q", "quit", "exit"}:
            _p("👋 感謝使用台灣股市營收預測系統，再見！")
            break
        else:
            _p("❌ 無效選項，請重新選擇")
        
        input("\n⏸️  按 Enter 繼續...")


def handle_prediction_results_view():
    """查看預測結果統計表"""
    _p("📊 預測結果統計表")
    _p("=" * 80)

    try:
        if __name__ == "__main__":
            from forecasting.db import get_latest_prediction_summary
        else:
            from .db import get_latest_prediction_summary

        results = get_latest_prediction_summary()

        if not results:
            _p("📋 目前沒有預測結果記錄")
            _p("💡 請先執行「單次預測」功能來產生預測結果")
            return

        # 表格標題
        _p(f"{'股票代碼':<8} {'股票名稱':<12} {'模型':<8} {'預測月份':<8} {'預測營收':<15} {'最新營收':<15} {'趨勢準確率':<10} {'誤差率':<8} {'預測時間':<16}")
        _p("=" * 80)

        # 顯示結果
        for row in results:
            stock_id = row['stock_id'] or 'N/A'
            stock_name = (row['stock_name'] or 'N/A')[:10]  # 限制長度
            model_name = row['model_name'] or 'N/A'
            target_month = row['target_month'] or 'N/A'

            # 格式化營收數字
            predicted_revenue = row['predicted_revenue']
            pred_revenue_str = f"{predicted_revenue/1e8:.1f}億" if predicted_revenue else 'N/A'

            latest_revenue = row['latest_revenue']
            latest_revenue_str = f"{latest_revenue/1e8:.1f}億" if latest_revenue else 'N/A'

            # 格式化準確率和誤差率
            trend_accuracy = row['trend_accuracy']
            trend_acc_str = f"{trend_accuracy*100:.1f}%" if trend_accuracy else 'N/A'

            mape = row['mape']
            mape_str = f"{mape:.1f}%" if mape else 'N/A'

            # 格式化預測時間
            prediction_date = row['prediction_date'][:16] if row['prediction_date'] else 'N/A'

            _p(f"{stock_id:<8} {stock_name:<12} {model_name:<8} {target_month:<8} {pred_revenue_str:<15} {latest_revenue_str:<15} {trend_acc_str:<10} {mape_str:<8} {prediction_date:<16}")

        _p("=" * 80)
        _p(f"📋 共顯示 {len(results)} 筆預測結果")

    except Exception as e:
        _p(f"❌ 查詢預測結果失敗: {e}")


def handle_prediction_results_export():
    """匯出預測結果到CSV"""
    _p("📤 匯出預測結果到CSV")

    try:
        if __name__ == "__main__":
            from forecasting.db import get_latest_prediction_summary
        else:
            from .db import get_latest_prediction_summary

        results = get_latest_prediction_summary()

        if not results:
            _p("📋 目前沒有預測結果記錄")
            return

        # 轉換為 DataFrame
        import pandas as pd
        df = pd.DataFrame(results)

        # 重新命名欄位為中文
        df = df.rename(columns={
            'stock_id': '股票代碼',
            'stock_name': '股票名稱',
            'model_name': '模型',
            'prediction_date': '預測時間',
            'target_month': '預測月份',
            'predicted_revenue': '預測營收',
            'latest_revenue': '最新營收',
            'latest_revenue_month': '最新營收月份',
            'trend_accuracy': '趨勢準確率',
            'mape': '誤差率MAPE',
            'scenario': '情境'
        })

        # 格式化數值
        if '預測營收' in df.columns:
            df['預測營收(億元)'] = df['預測營收'].apply(lambda x: f"{x/1e8:.2f}" if pd.notna(x) else '')
        if '最新營收' in df.columns:
            df['最新營收(億元)'] = df['最新營收'].apply(lambda x: f"{x/1e8:.2f}" if pd.notna(x) else '')
        if '趨勢準確率' in df.columns:
            df['趨勢準確率(%)'] = df['趨勢準確率'].apply(lambda x: f"{x*100:.1f}" if pd.notna(x) else '')
        if '誤差率MAPE' in df.columns:
            df['誤差率MAPE(%)'] = df['誤差率MAPE'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else '')

        # 選擇要匯出的欄位
        export_columns = ['股票代碼', '股票名稱', '模型', '預測月份', '預測營收(億元)',
                         '最新營收(億元)', '最新營收月份', '趨勢準確率(%)', '誤差率MAPE(%)', '預測時間']
        df_export = df[export_columns]

        # 匯出檔案
        import os
        os.makedirs("outputs/reports", exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outputs/reports/prediction_results_{timestamp}.csv"

        df_export.to_csv(filename, index=False, encoding='utf-8-sig')

        _p(f"✅ 預測結果已匯出到: {filename}")
        _p(f"📊 共匯出 {len(df_export)} 筆記錄")

    except Exception as e:
        _p(f"❌ 匯出預測結果失敗: {e}")


def handle_manual_add_prediction():
    """手動添加預測結果到統計表"""
    _p("📝 手動添加預測結果到統計表")
    _p("=" * 50)

    try:
        # 輸入股票資訊
        stock_id = input("請輸入股票代碼(4碼): ").strip()
        if not stock_id or len(stock_id) != 4:
            _p("❌ 請輸入有效的4碼股票代碼")
            return

        stock_name = input("請輸入股票名稱(可選): ").strip() or stock_id

        # 選擇模型
        _p("請選擇模型:")
        _p("  1) Prophet")
        _p("  2) XGBoost")
        _p("  3) LSTM")

        model_choice = input("請選擇 (1-3): ").strip()
        model_map = {"1": "Prophet", "2": "XGBoost", "3": "LSTM"}
        if model_choice not in model_map:
            _p("❌ 請選擇有效的模型")
            return
        model_name = model_map[model_choice]

        # 輸入預測資訊
        target_month = input("請輸入預測月份(YYYY-MM): ").strip()
        if not target_month or len(target_month) != 7 or target_month[4] != '-':
            _p("❌ 請輸入有效的月份格式(如: 2025-08)")
            return

        try:
            predicted_revenue = float(input("請輸入預測營收(元): ").strip())
        except ValueError:
            _p("❌ 請輸入有效的數字")
            return

        # 輸入最新營收資訊(可選)
        latest_revenue_str = input("請輸入最新營收(元，可選): ").strip()
        latest_revenue = None
        if latest_revenue_str:
            try:
                latest_revenue = float(latest_revenue_str)
            except ValueError:
                _p("⚠️  最新營收格式錯誤，將設為空值")

        latest_revenue_month = input("請輸入最新營收月份(YYYY-MM，可選): ").strip() or None

        # 輸入回測指標(可選)
        trend_accuracy_str = input("請輸入趨勢準確率(0-1，可選): ").strip()
        trend_accuracy = None
        if trend_accuracy_str:
            try:
                trend_accuracy = float(trend_accuracy_str)
                if not 0 <= trend_accuracy <= 1:
                    _p("⚠️  趨勢準確率應在0-1之間，將設為空值")
                    trend_accuracy = None
            except ValueError:
                _p("⚠️  趨勢準確率格式錯誤，將設為空值")

        mape_str = input("請輸入誤差率MAPE(%)，可選): ").strip()
        mape = None
        if mape_str:
            try:
                mape = float(mape_str)
                if mape < 0:
                    _p("⚠️  MAPE應為正數，將設為空值")
                    mape = None
            except ValueError:
                _p("⚠️  MAPE格式錯誤，將設為空值")

        # 保存到資料庫
        if __name__ == "__main__":
            from forecasting.db import save_prediction_result
        else:
            from .db import save_prediction_result

        save_prediction_result(
            stock_id=stock_id,
            stock_name=stock_name,
            model_name=model_name,
            target_month=target_month,
            predicted_revenue=predicted_revenue,
            latest_revenue=latest_revenue,
            latest_revenue_month=latest_revenue_month,
            trend_accuracy=trend_accuracy,
            mape=mape,
            scenario='baseline'
        )

        _p("✅ 預測結果已成功添加到統計表")
        _p(f"📊 股票: {stock_id} ({stock_name})")
        _p(f"📊 模型: {model_name}")
        _p(f"📊 預測月份: {target_month}")
        _p(f"📊 預測營收: {predicted_revenue:,.0f} 元 ({predicted_revenue/1e8:.1f}億)")

    except Exception as e:
        _p(f"❌ 添加預測結果失敗: {e}")


if __name__ == "__main__":
    main()
