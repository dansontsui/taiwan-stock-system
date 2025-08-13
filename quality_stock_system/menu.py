# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from .utils import log, OUTPUT_DIR, DEFAULT_DB
from .etl import build_all_marts
from .export import export_quality_list
from .rules import DEFAULT_PROFILES


def render_menu() -> str:
    lines = [
        "============================================================",
        "🏢 長期存股『績優股』篩選系統 - 功能選單",
        "============================================================",
        "📊 基本功能",
        "  1) 建立 marts（品質/股利/估值）",
        "  2) 匯出清單（CSV/JSON）",
        "  8) 批量匯出年度清單（寫入歷史）",
        "  3) 檢視輸出資料夾",
        "",
        "🔧 進階功能",
        "  4) 查看規則模板（profiles）",
        "",
        "📈  回測與視覺化",
        "  6) 年度簡易回測（產出 CSV 報告）",
        "  7) 生成清單視覺化 HTML 報告",
        "  9) 參數網格掃描（停損/停利/移動停損）",
        " 10) 用掃描結果最佳參數一鍵回測",
        "",
        "⚙️  系統",
        "  5) 顯示環境參數",
        "",
        "  q) 離開系統",
        "------------------------------------------------------------",
    ]
    return "\n".join(lines)


def run_menu():
    while True:
        log(render_menu())
        try:
            choice = input("🎯 請選擇功能 (1-5, q): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = 'q'

        if choice == '1':
            db = input(f"🔌 請輸入資料庫路徑（預設 {DEFAULT_DB}）: ").strip() or DEFAULT_DB
            log("🔧 開始建立 marts ...")
            try:
                build_all_marts(db)
                log("🎉 完成")
            except Exception as e:
                log(f"❌ 建立失敗: {e}")
        elif choice == '2':
            prof = input("📁 請輸入規則模板（conservative/value，預設 conservative）: ").strip() or 'conservative'
            top_s = input("🔢 匯出筆數 Top N（預設 100）: ").strip()
            try:
                top_n = int(top_s) if top_s else 100
            except Exception:
                top_n = 100
            year_s = input("📅 鎖定評估年度（例如 2024，空白代表不鎖定）: ").strip()
            as_of_date = input("🗓  as_of_date 標記（YYYY-MM-DD，可空白）: ").strip()
            year_i = int(year_s) if year_s else None
            db = input(f"🔌 請輸入資料庫路徑（預設 {DEFAULT_DB}）: ").strip() or DEFAULT_DB
            log("📤 開始輸出清單 ...")
            try:
                # 需求：選單 2 重新建立歷史檔案，避免累加
                from .history import clear_history
                clear_history()
                res = export_quality_list(profile=prof, top_n=top_n, db_path=db, year=year_i, as_of_date=as_of_date or None)
                if res:
                    log(f"📄 CSV: {res['csv']}")
                    log(f"🗂  JSON: {res['json']}")
                    log(f"📊 筆數: {res['count']}")
                log("🎉 完成（歷史檔案已重建並寫入）")
            except Exception as e:
                log(f"❌ 匯出失敗: {e}")
        elif choice == '3':
            log(f"📂 輸出資料夾: {OUTPUT_DIR}")
            for name in os.listdir(OUTPUT_DIR):
                log(f" - {name}")
        elif choice == '4':
            log("📘 可用規則模板（profiles）：")
            for k, v in DEFAULT_PROFILES.items():
                log(f"- {k}: thresholds={v.get('thresholds',{})}, weights={v.get('weights',{})}")
        elif choice == '5':
            log("🔧 環境參數：")
            log(f"  TS_DB_PATH: {DEFAULT_DB}")
            log(f"  QS_OUTPUT_DIR: {OUTPUT_DIR}")
        elif choice == '8':
            # 批量匯出年度清單（若未輸入起訖年，將自動偵測 DB 內最小與最大年度）
            prof = input("📁 規則模板（conservative/value，預設 conservative）: ").strip() or 'conservative'
            start_y = input("📅 起始年度（例如 2018，空白自動偵測）: ").strip()
            end_y = input("📅 結束年度（例如 2024，空白自動偵測）: ").strip()
            top_s = input("🔢 Top N（預設 100）: ").strip()
            try:
                top_n = int(top_s) if top_s else 100
            except Exception:
                top_n = 100
            db = input(f"🔌 資料庫路徑（預設 {DEFAULT_DB}）: ").strip() or DEFAULT_DB
            try:
                # 自動偵測年度範圍
                if not start_y or not end_y:
                    from .utils import get_conn
                    import pandas as pd
                    with get_conn(db) as conn:
                        try:
                            rng = pd.read_sql_query("SELECT MIN(year) AS min_y, MAX(year) AS max_y FROM mart_quality_factors_yearly", conn)
                            min_y = int(rng['min_y'].iloc[0]) if pd.notna(rng['min_y'].iloc[0]) else None
                            max_y = int(rng['max_y'].iloc[0]) if pd.notna(rng['max_y'].iloc[0]) else None
                        except Exception:
                            min_y = max_y = None
                    from datetime import datetime
                    cur_y = datetime.now().year
                    if min_y is None:
                        min_y = cur_y - 7  # 預設近 7 年
                    if max_y is None:
                        max_y = cur_y - 1  # 交易年通常使用上一年資料
                    sy, ey = min_y, max_y
                    log(f"ℹ️  自動偵測年度範圍：{sy}~{ey}")
                else:
                    sy, ey = int(start_y), int(end_y)
                if sy > ey:
                    sy, ey = ey, sy
                from .export import export_quality_list
                # 需求：選單 8 開始前清空歷史檔，避免累加
                from .history import clear_history
                clear_history()
                for y in range(sy, ey+1):
                    as_of = f"{y}-12-31"
                    log(f"➡️  匯出年度 {y}（as_of_date={as_of}）...")
                    export_quality_list(profile=prof, top_n=top_n, db_path=db, year=y, as_of_date=as_of)
                log("🎉 批量匯出完成（歷史檔案已重建並寫入）")
            except Exception as e:
                log(f"❌ 批量匯出失敗: {e}")
        elif choice == '6':
            # 正式：年度再構成回測（可選靜態/動態）
            from .backtest import run_equal_weight_backtest
            prof = input("📁 請輸入規則模板（conservative/value，預設 conservative）: ").strip() or 'conservative'
            mode = input("🔄 回測模式（static=靜態名單 / dynamic=年度再構成，預設 dynamic）: ").strip().lower() or 'dynamic'
            dynamic = (mode != 'static')
            db = input(f"🔌 請輸入資料庫路徑（預設 {DEFAULT_DB}）: ").strip() or DEFAULT_DB
            try:
                # 新增：含息與停損參數（預設含息、固定 15% 停損）
                inc_div = True
                sl_pct = 0.15
                tp_s = input("🎯 停利%（空白略過）: ").strip()
                tsl_s = input("🛡️  移動停損%（空白略過）: ").strip()
                tp = float(tp_s)/100.0 if tp_s else None
                tsl = float(tsl_s)/100.0 if tsl_s else None
                res = run_equal_weight_backtest(db, profile=prof, dynamic=dynamic, include_dividends=inc_div, sl_pct=sl_pct, tp_pct=tp, tsl_pct=tsl)
                log(f"📄 報告（投組匯總）: {res['report_csv']}")
                log(f"📄 明細（成分股年度報酬）: {os.path.join(OUTPUT_DIR, 'backtest_portfolio_details.csv')}")
                s = res['summary']
                log(f"📌 摘要：年化報酬={s['annualized_return']:.2%}、最大回撤={s['max_drawdown']:.2%}、勝率={s['win_rate']:.2%}")
            except Exception as e:
                log(f"❌ 回測失敗: {e}")
        elif choice == '7':
            # 生成簡易 HTML（示意）：列出清單 JSON 的前 N 名與關鍵指標
            json_path = os.path.join(OUTPUT_DIR, 'quality_list_conservative.json')
            html_path = os.path.join(OUTPUT_DIR, 'quality_list_report.html')
            try:
                import json
                if not os.path.exists(json_path):
                    log("⚠️ 找不到清單 JSON，請先執行匯出清單")
                else:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    rows = data[:50]
                    html = [
                        '<!DOCTYPE html><html><head><meta charset="utf-8" /><title>Quality List Report</title></head><body>',
                        '<h2>Quality List (Top)</h2>',
                        '<table border="1" cellspacing="0" cellpadding="6">',
                        '<tr><th>stock_id</th><th>year</th><th>roe_5y_avg</th><th>revenue_cagr_5y</th><th>cash_div_years</th><th>pe_pct_5y</th><th>pb_pct_5y</th><th>score</th></tr>'
                    ]
                    for r in rows:
                        html.append('<tr>' + ''.join(
                            f"<td>{str(r.get(k,''))}</td>" for k in ['stock_id','year','roe_5y_avg','revenue_cagr_5y','cash_div_years','pe_pct_5y','pb_pct_5y','score']
                        ) + '</tr>')
                    html.append('</table></body></html>')
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(html))
                    log(f"🌐 已輸出視覺化 HTML: {html_path}")
            except Exception as e:
                log(f"❌ 視覺化失敗: {e}")
        elif choice == '9':
            # 參數網格掃描
            from .sweep import sweep_params
            prof = input("📁 規則模板（conservative/value，預設 conservative）: ").strip() or 'conservative'
            mode = input("🔄 回測模式（static=靜態名單 / dynamic=年度再構成，預設 dynamic）: ").strip().lower() or 'dynamic'
            dynamic = (mode != 'static')
            db = input(f"🔌 資料庫路徑（預設 {DEFAULT_DB}）: ").strip() or DEFAULT_DB
            # 擴大網格範圍（包含不停利/不移動停損）：
            sl_list = [0.10, 0.15, 0.20]
            tp_list = [None, 0.20, 0.30, 0.50]  # None = 不停利
            tsl_list = [None, 0.10, 0.15]       # None = 不移動停損
            log("🔎 開始參數網格掃描（含息）...")
            try:
                out_csv = sweep_params(db, prof, dynamic, sl_list, tp_list, tsl_list)
                log(f"📄 掃描結果: {out_csv}")
            except Exception as e:
                log(f"❌ 掃描失敗: {e}")
        elif choice == '10':
            # 用掃描結果最佳參數一鍵回測
            from .best_params import pick_best_params
            from .backtest import run_equal_weight_backtest
            prof = input("📁 規則模板（conservative/value，預設 conservative）: ").strip() or 'conservative'
            mode = input("🔄 回測模式（static=靜態名單 / dynamic=年度再構成，預設 dynamic）: ").strip().lower() or 'dynamic'
            dynamic = (mode != 'static')
            db = input(f"🔌 資料庫路徑（預設 {DEFAULT_DB}）: ").strip() or DEFAULT_DB
            obj = input("🎯 目標（annualized/mdd/annualized_minus_half_mdd，預設 annualized_minus_half_mdd）: ").strip() or 'annualized_minus_half_mdd'
            try:
                sl, tp, tsl = pick_best_params(objective=obj)
                sl_str = f"{sl:.0%}" if sl is not None else "無"
                tp_str = f"{tp:.0%}" if tp is not None else "無"
                tsl_str = f"{tsl:.0%}" if tsl is not None else "無"
                log(f"🏆 最佳參數：停損={sl_str}、停利={tp_str}、移動停損={tsl_str}")
                res = run_equal_weight_backtest(db, profile=prof, dynamic=dynamic, include_dividends=True, sl_pct=sl, tp_pct=tp, tsl_pct=tsl)
                log(f"📄 報告（投組匯總）: {res['report_csv']}")
                log(f"📄 明細（成分股年度報酬）: {os.path.join(OUTPUT_DIR, 'backtest_portfolio_details.csv')}")
                s = res['summary']
                log(f"📌 摘要：年化報酬={s['annualized_return']:.2%}、最大回撤={s['max_drawdown']:.2%}、勝率={s['win_rate']:.2%}")
            except Exception as e:
                log(f"❌ 一鍵回測失敗: {e}")
            json_path = os.path.join(OUTPUT_DIR, 'quality_list_conservative.json')
            html_path = os.path.join(OUTPUT_DIR, 'quality_list_report.html')
            try:
                import json
                if not os.path.exists(json_path):
                    log("⚠️ 找不到清單 JSON，請先執行匯出清單")
                else:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    rows = data[:50]
                    html = [
                        '<!DOCTYPE html><html><head><meta charset="utf-8" /><title>Quality List Report</title></head><body>',
                        '<h2>Quality List (Top)</h2>',
                        '<table border="1" cellspacing="0" cellpadding="6">',
                        '<tr><th>stock_id</th><th>year</th><th>roe_5y_avg</th><th>revenue_cagr_5y</th><th>cash_div_years</th><th>pe_pct_5y</th><th>pb_pct_5y</th><th>score</th></tr>'
                    ]
                    for r in rows:
                        html.append('<tr>' + ''.join(
                            f"<td>{str(r.get(k,''))}</td>" for k in ['stock_id','year','roe_5y_avg','revenue_cagr_5y','cash_div_years','pe_pct_5y','pb_pct_5y','score']
                        ) + '</tr>')
                    html.append('</table></body></html>')
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(html))
                    log(f"🌐 已輸出視覺化 HTML: {html_path}")
            except Exception as e:
                log(f"❌ 視覺化失敗: {e}")
        elif choice == 'q':
            log("👋 感謝使用！")
            break
        else:
            log("⚠️ 無效選項，請重新輸入")


if __name__ == '__main__':
    # 允許一鍵入口：python -m quality_stock_system.menu
    run_menu()

