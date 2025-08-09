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
    from forecasting.cli import run_forecast, run_roll_check
else:
    # 當作為模組導入時，使用相對導入
    from .config import cfg, ensure_dirs, setup_prophet_logging
    from .db import latest_month_in_db, fetch_schema_overview
    from .cli import run_forecast, run_roll_check


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
    _p("⚙️  系統設定")
    _p("  9) 模型啟用設定")
    _p("  10) 系統狀態檢查")
    _p("")
    _p("  q) 離開系統")
    _p("-"*60)


def handle_single_forecast():
    """處理單次預測"""
    stock_id = input("📈 請輸入股票代碼(4碼): ").strip()
    if not stock_id:
        _p("❌ 股票代碼不能為空")
        return
    
    try:
        _p(f"🔄 正在預測 {stock_id} 的營收...")
        result = run_forecast(stock_id)
        _p("✅ 預測完成！")
        _p(f"📊 最佳模型: {result['最佳模型']}")
        _p(f"📁 CSV檔案: {result['CSV路徑']}")
        _p(f"📁 JSON檔案: {result['JSON路徑']}")
        _p(f"📈 圖表檔案: {result['歷史對比圖']}")
        
        if result['警告']:
            _p("⚠️  警告訊息:")
            for warning in result['警告']:
                _p(f"   - {warning}")
        
        _p("\n📋 預測摘要:")
        for item in result['預測摘要']:
            _p(f"   {item['日期']} {item['情境']}: {item['預測值']} (異常: {item['異常']})")
            
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

    _p("⚙️  開始參數調校...")
    _p("⚠️  此過程可能需要較長時間，請耐心等待...")

    try:
        if __name__ == "__main__":
            from forecasting.tuning import comprehensive_tuning
        else:
            from .tuning import comprehensive_tuning
        result = comprehensive_tuning(stock_id)

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
        choice = input("🎯 請選擇功能 (1-10, q): ").strip().lower()
        
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
        elif choice in {"q", "quit", "exit"}:
            _p("👋 感謝使用台灣股市營收預測系統，再見！")
            break
        else:
            _p("❌ 無效選項，請重新選擇")
        
        input("\n⏸️  按 Enter 繼續...")


if __name__ == "__main__":
    main()
