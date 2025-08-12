# -*- coding: utf-8 -*-
"""
Export quality list based on simple conservative rules using marts.
Outputs CSV (UTF-8-SIG) and JSON.
"""
from __future__ import annotations
import os
import pandas as pd
from .utils import get_conn, ascii_path, safe_write_csv, safe_write_json, OUTPUT_DIR, log
from .rules import load_profile

HEADER = [
    'stock_id', 'year', 'roe_5y_avg', 'revenue_cagr_5y', 'cash_div_years', 'pe_pct_5y', 'pb_pct_5y'
]


def _calc_risk_metrics(db_path: str, year: int):
    """計算單一年度的風險指標（年度報酬、最大回撤）。
    使用 stock_prices 的當年日價，輸出 columns: stock_id, risk_year_return, risk_mdd
    """
    import pandas as pd
    from .utils import get_conn
    with get_conn(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT stock_id, date, close_price FROM stock_prices WHERE strftime('%Y', date)=?",
            conn, params=(str(year),)
        )
    if df.empty:
        return pd.DataFrame(columns=['stock_id','risk_year_return','risk_mdd'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date','close_price'])
    out = []
    for sid, g in df.groupby('stock_id'):
        g = g.sort_values('date')
        first = g['close_price'].iloc[0]
        last = g['close_price'].iloc[-1]
        yr = (last/first - 1.0) if (first and first>0 and last>0) else float('nan')
        # MDD 計算
        cummax = g['close_price'].cummax()
        dd = (g['close_price']/cummax - 1.0).min() if len(g)>0 else float('nan')
        out.append({'stock_id': str(sid), 'risk_year_return': yr, 'risk_mdd': float(dd) if pd.notna(dd) else dd})
    return pd.DataFrame(out)


def export_quality_list(profile: str = 'conservative', top_n: int = 100, db_path: str | None = None, year: int | None = None, as_of_date: str | None = None):
    prof = load_profile(profile)
    thr = prof.get('thresholds', {})
    w = prof.get('weights', {})
    risk_cfg = prof.get('risk', {})

    # load marts
    with get_conn(db_path) as conn:
        try:
            q = pd.read_sql_query("SELECT * FROM mart_quality_factors_yearly", conn)
        except Exception:
            log('⚠️ 找不到 mart_quality_factors_yearly，請先建立 marts')
            q = pd.DataFrame()
        try:
            d = pd.read_sql_query("SELECT * FROM mart_dividend_stability", conn)
        except Exception:
            log('⚠️ 找不到 mart_dividend_stability，請先建立 marts')
            d = pd.DataFrame()
        try:
            v = pd.read_sql_query("SELECT * FROM mart_valuation_snapshot", conn)
        except Exception:
            v = pd.DataFrame()

    # if both empty, try valuation-only export skeleton
    if q.empty and d.empty and not 'v' in locals():
        log('❌ 無資料可輸出')
        return None

    # 若指定 year，過濾品質資料至該年
    target_year = year
    if year is not None and not q.empty:
        q = q[q['year'] == int(year)]
    if year is not None and not d.empty:
        d = d[d['year'] == int(year)]

    # merge marts
    df = q if not q.empty else pd.DataFrame()
    if not df.empty and not d.empty:
        df = df.merge(d[['stock_id','year','cash_div_years']], on=['stock_id','year'], how='left')
    elif df.empty:
        df = d
    if (not isinstance(df, pd.DataFrame)) or df.empty:
        df = pd.DataFrame()
    if not v.empty:
        v_latest = v.sort_values('snap_date').drop_duplicates('stock_id', keep='last')
        if df.empty:
            df = v_latest[['stock_id','pe_pct_5y','pb_pct_5y']].copy()
            df['year'] = target_year if target_year is not None else 0
        else:
            df = df.merge(v_latest[['stock_id','pe_pct_5y','pb_pct_5y']], on='stock_id', how='left')

    # 若為 strict 模式，缺指標直接不通過
    require_fields = bool(thr.get('require_fields', False))

    # 風險指標（以交易年度 year+1 的前年/當年資料皆可，這裡先用指定 year 年的風險）
    risk_df = pd.DataFrame()
    if year is not None and risk_cfg:
        try:
            risk_df = _calc_risk_metrics(db_path or '', int(year))
        except Exception:
            risk_df = pd.DataFrame()
    if isinstance(df, pd.DataFrame) and not df.empty and not risk_df.empty:
        df = df.merge(risk_df, on='stock_id', how='left')

    # filters from profile
    def _flt(x):
        ok = True
        # require_fields 只檢查門檻中實際存在的欄位
        if require_fields:
            for f in thr.keys():
                if f in ['roe_5y_avg','revenue_cagr_5y','cash_div_years','pe_pct_5y','pb_pct_5y'] and pd.isna(x.get(f, None)):
                    return False
        if 'roe_5y_avg' in x and pd.notna(x['roe_5y_avg']) and 'roe_5y_avg' in thr:
            ok &= (x['roe_5y_avg'] >= thr['roe_5y_avg'])
        if 'revenue_cagr_5y' in x and pd.notna(x['revenue_cagr_5y']) and 'revenue_cagr_5y' in thr:
            ok &= (x['revenue_cagr_5y'] >= thr['revenue_cagr_5y'])
        if 'cash_div_years' in x and pd.notna(x['cash_div_years']) and 'cash_div_years' in thr:
            ok &= (x['cash_div_years'] >= thr['cash_div_years'])
        if 'pe_pct_5y' in x and pd.notna(x['pe_pct_5y']) and 'pe_pct_5y' in thr:
            ok &= (x['pe_pct_5y'] <= thr['pe_pct_5y'])
        if 'pb_pct_5y' in x and pd.notna(x['pb_pct_5y']) and 'pb_pct_5y' in thr:
            ok &= (x['pb_pct_5y'] <= thr['pb_pct_5y'])
        # 風險過濾
        if 'risk_year_return' in x and pd.notna(x['risk_year_return']) and 'year_return_gt' in risk_cfg:
            ok &= (x['risk_year_return'] > float(risk_cfg['year_return_gt']))
        if 'risk_mdd' in x and pd.notna(x['risk_mdd']) and 'mdd_le' in risk_cfg:
            ok &= (x['risk_mdd'] >= -float(risk_cfg['mdd_le']))  # mdd 為負值，需大於等於 -閾值
        return ok

    if isinstance(df, pd.DataFrame) and not df.empty:
        df = df[df.apply(_flt, axis=1)]
        # scoring using profile weights
        # guard: ensure Series
        r_roe = df['roe_5y_avg'] if 'roe_5y_avg' in df.columns else pd.Series([0]*len(df))
        r_cagr = df['revenue_cagr_5y'] if 'revenue_cagr_5y' in df.columns else pd.Series([0]*len(df))
        r_div = df['cash_div_years'] if 'cash_div_years' in df.columns else pd.Series([0]*len(df))
        r_roe = r_roe.fillna(0)
        r_cagr = r_cagr.fillna(0) * 100
        r_div = r_div.fillna(0)
        score = r_roe * w.get('roe_5y_avg', 0.4) + r_cagr * w.get('revenue_cagr_5y', 0.3) + r_div * w.get('cash_div_years', 0.3)
        df['score'] = score
        # ensure sort keys exist
        for col in ['roe_5y_avg','revenue_cagr_5y']:
            if col not in df.columns:
                df[col] = 0
        df = df.sort_values(['score','roe_5y_avg','revenue_cagr_5y'], ascending=[False, False, False]).head(top_n)

    # export
    out_csv = ascii_path(OUTPUT_DIR, f'quality_list_{profile}.csv')
    out_json = ascii_path(OUTPUT_DIR, f'quality_list_{profile}.json')

    # ensure columns exist
    if isinstance(df, pd.DataFrame) and not df.empty:
        for col in HEADER:
            if col not in df.columns:
                df[col] = ''
        cols = HEADER + ['score'] if 'score' in df.columns else HEADER
        rows = df[cols].fillna('').values.tolist()
    else:
        cols, rows = (HEADER, [])
    # 產出一份中文化的入選理由報告（每檔）
    reason_rows = []
    if isinstance(df, pd.DataFrame) and not df.empty:
        # Debug: 檢查 df 的年度資訊
        log(f"🔍 Debug: df 年度範圍 {df['year'].min() if 'year' in df.columns else 'N/A'} - {df['year'].max() if 'year' in df.columns else 'N/A'}")
        for _, r in df.iterrows():
            y_v = r.get('year', None)
            actual_year = int(target_year) if target_year is not None else (int(y_v) if pd.notna(y_v) and str(y_v).strip()!='' else 0)
            reason_rows.append([
                r.get('stock_id',''),
                actual_year,
                float(r.get('roe_5y_avg', 0)) if pd.notna(r.get('roe_5y_avg')) else '',
                float(r.get('revenue_cagr_5y', 0)) if pd.notna(r.get('revenue_cagr_5y')) else '',
                int(r.get('cash_div_years', 0)) if pd.notna(r.get('cash_div_years')) else '',
                float(r.get('pe_pct_5y', 1)) if pd.notna(r.get('pe_pct_5y')) else '',
                float(r.get('pb_pct_5y', 1)) if pd.notna(r.get('pb_pct_5y')) else '',
                float(r.get('score', 0)) if pd.notna(r.get('score')) else ''
            ])
    reason_cols = ['股票代碼','入選年度','ROE五年均值','營收五年CAGR','連續配息年數','PE五年分位','PB五年分位','綜合分數']
    out_reason = ascii_path(OUTPUT_DIR, f'quality_list_{profile}_reasons.csv')

    # 若指定年度，則追加模式寫入（批量匯出時保留多年資料）
    if target_year is not None:
        # 檢查檔案是否存在，決定是否寫入標題
        write_header = not os.path.exists(out_reason)
        try:
            import csv
            with open(out_reason, 'a', encoding='utf-8-sig', newline='') as f:
                w = csv.writer(f)
                if write_header:
                    w.writerow(reason_cols)
                w.writerows(reason_rows)
            log(f'📋 已追加入選理由: {out_reason} （{len(reason_rows)} 筆，{target_year}年）')
        except Exception as e:
            log(f'⚠️ 寫入理由報告失敗: {e}')
    else:
        # 未指定年度時，覆蓋模式（單次匯出）
        safe_write_csv(out_reason, reason_rows, reason_cols)

    safe_write_csv(out_csv, rows, cols)
    safe_write_json(out_json, df.to_dict(orient='records') if isinstance(df, pd.DataFrame) else [])

    # 寫入歷史（年度鎖定/標記 as_of_date）
    try:
        from .history import append_history
        # 為歷史加上 rank 欄（1-based）
        if isinstance(df, pd.DataFrame) and not df.empty:
            df_hist = df.reset_index(drop=True).copy()
            df_hist['rank'] = df_hist.index + 1
            # 年度鎖定（若未指定，嘗試以 df 的 year 欄位最大值當年度）
            hist_year = int(year if year is not None else (df_hist['year'].dropna().max() if 'year' in df_hist.columns else 0))
            append_history(profile, hist_year, as_of_date or '', df_hist)
    except Exception as e:
        log(f'⚠️ 寫入清單歷史失敗: {e}')

    log(f'✅ 清單已輸出: {out_csv}')
    log(f'✅ JSON 已輸出: {out_json}')
    return {'csv': out_csv, 'json': out_json, 'count': 0 if df is None else len(df)}

