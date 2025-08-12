# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List
from .utils import get_conn, OUTPUT_DIR, safe_write_csv, safe_write_json, log
import datetime


def load_quality_list(profile: str = 'conservative') -> pd.DataFrame:
    json_path = os.path.join(OUTPUT_DIR, f'quality_list_{profile}.json')
    if not os.path.exists(json_path):
        raise FileNotFoundError(f'找不到清單 JSON: {json_path}，請先執行匯出清單')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if df.empty or 'stock_id' not in df.columns:
        raise ValueError('清單為空，無成分股可回測')
    # 加入排名（1 開始）
    df = df.reset_index().rename(columns={'index': 'rank'})
    df['rank'] = df['rank'] + 1
    return df[['stock_id','rank']]


def _first_last_prices(df: pd.DataFrame) -> pd.DataFrame:
    # df: columns [stock_id, date, close_price]
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    first = df.sort_values('date').groupby(['stock_id','year']).first().reset_index().rename(columns={'close_price':'close_price_first'})
    last = df.sort_values('date').groupby(['stock_id','year']).last().reset_index().rename(columns={'close_price':'close_price_last'})
    rep = last.merge(first, on=['stock_id','year'])
    # 安全計算年度報酬，避免除以 0 或 inf
    rep['year_return_raw'] = np.where((rep['close_price_first'] > 0) & (rep['close_price_last'] > 0),
                                      rep['close_price_last'] / rep['close_price_first'] - 1.0,
                                      np.nan)
    # 保留原價以供明細輸出
    return rep[['stock_id','year','close_price_first','close_price_last','year_return_raw']]


def _load_dividends(conn, stock_ids: List[str], year: int) -> pd.DataFrame:
    """載入指定年度的股利資料（現金股利、股票股利）。
    回傳：
      - 若有日期欄位：columns = [stock_id, dt, cash_amt, stock_ratio]
      - 若無日期欄位：columns = [stock_id, cash_div_ps, stock_ratio_total]（全年總和）
    """
    try:
        cols = pd.read_sql_query("PRAGMA table_info(dividend_policies)", conn)
        available = set(cols['name'].tolist()) if not cols.empty else set()
        if not available:
            return pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids)})
        date_col = None
        for c in ['ex_date', 'pay_date', 'announcement_date', 'record_date', 'date']:
            if c in available:
                date_col = c
                break
        # 欄位命名對齊：
        #  - stock_earnings_distrubtion：股票股利（比率，例如 0.1 表示配 10% 股票股利）
        #  - cash_earnings_distrubtion：現金股利（每股）
        cash_cols = [c for c in ['cash_earnings_distribution','cash_earnings_distrubtion','cash_statutory_surplus','cash_capital_reserve','cash_dividend'] if c in available]
        if 'stock_earnings_distribution' in available:
            stock_col = 'stock_earnings_distribution'
        elif 'stock_earnings_distrubtion' in available:
            stock_col = 'stock_earnings_distrubtion'
        else:
            stock_col = None
        if not cash_cols and stock_col is None:
            return pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids), 'stock_ratio_total':[0.0]*len(stock_ids)})
        q_marks = ','.join(['?']*len(stock_ids))
        if date_col:
            select_cols = [f"{'+'.join(cash_cols)} AS cash_amt"]
            if stock_col:
                select_cols.append(f"{stock_col} AS stock_ratio")
            else:
                select_cols.append("0.0 AS stock_ratio")
            sel = ', '.join(select_cols)
            df = pd.read_sql_query(
                f"SELECT stock_id, {date_col} AS dt, {sel} FROM dividend_policies WHERE stock_id IN ({q_marks})",
                conn, params=stock_ids
            )
            if df.empty:
                return pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids), 'stock_ratio_total':[0.0]*len(stock_ids)})
            df['dt'] = pd.to_datetime(df['dt'], errors='coerce')
            df['year'] = df['dt'].dt.year
            df = df[df['year'] == int(year)][['stock_id','dt','cash_amt','stock_ratio']]
            return df
        else:
            year_col = 'year' if 'year' in available else None
            if year_col is None:
                return pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids)})
            select_cols = [f"{'+'.join(cash_cols)} AS cash_amt"]
            if stock_col:
                select_cols.append(f"{stock_col} AS stock_ratio")
            else:
                select_cols.append("0.0 AS stock_ratio")
            sel = ', '.join(select_cols)
            df = pd.read_sql_query(
                f"SELECT stock_id, {year_col} AS y, {sel} FROM dividend_policies WHERE stock_id IN ({q_marks}) AND {year_col}=?",
                conn, params=(stock_ids + [str(year)])
            )
            if df.empty:
                return pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids), 'stock_ratio_total':[0.0]*len(stock_ids)})
            def _to_year(v):
                try:
                    if isinstance(v, str) and v.endswith('年'):
                        return int(v[:-1]) + 1911
                    return int(v)
                except Exception:
                    return None
            df['y'] = df['y'].apply(_to_year)
            df = df[df['y'] == int(year)]
            df_cash = df.groupby('stock_id', as_index=False)['cash_amt'].sum().rename(columns={'cash_amt':'cash_div_ps'})
            df_stock = df.groupby('stock_id', as_index=False)['stock_ratio'].sum().rename(columns={'stock_ratio':'stock_ratio_total'})
            out = df_cash.merge(df_stock, on='stock_id', how='outer').fillna(0.0)
            return out
    except Exception:
        return pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids)})


def _apply_stoploss_and_dividends(prices: pd.DataFrame,
                                   trading_year: int,
                                   include_dividends: bool,
                                   sl_pct: float | None,
                                   conn,
                                   tp_pct: float | None = None,
                                   tsl_pct: float | None = None,
                                   trigger_priority: str = 'chronological') -> pd.DataFrame:
    """對單一年度逐檔計算：進場/出場/停損/停利/移動停損、含息/不含息報酬。
    prices: columns [stock_id, date, close_price]（已為該年度資料）
    回傳：stock_id, year, entry_date, exit_date, entry_price, exit_price, raw_return, cash_div, total_return
    """
    if prices.empty:
        return pd.DataFrame(columns=['stock_id','year','entry_date','exit_date','entry_price','exit_price','raw_return','cash_div','total_return'])
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'], errors='coerce')
    out_rows = []
    stock_ids = sorted(prices['stock_id'].astype(str).unique().tolist())
    # 預先載入全年現金股利（若有日期欄位，保留逐筆，否則只得全年總額）
    div_df = pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids)})
    if include_dividends:
        got_dates = False
        try:
            div_df = _load_dividends(conn, stock_ids, trading_year)
            got_dates = ('dt' in div_df.columns)
        except Exception:
            pass
        if div_df is None or div_df.empty:
            div_df = pd.DataFrame({'stock_id': stock_ids, 'cash_div_ps': [0.0]*len(stock_ids)})
        if 'stock_id' in div_df.columns:
            div_df['stock_id'] = div_df['stock_id'].astype(str)
    for sid, g in prices.groupby('stock_id'):
        g = g.sort_values('date').reset_index(drop=True)
        entry_date = g['date'].iloc[0]
        entry_p = float(g['close_price'].iloc[0])
        exit_date = g['date'].iloc[-1]
        exit_p = float(g['close_price'].iloc[-1])
        exit_reason = '期末'

        # 若有日期型股利資料：以「資產價值」（price*shares+cash）做停損/停利/移動停損判斷
        has_dt = include_dividends and ('dt' in div_df.columns)
        if has_dt and entry_p > 0:
            # 標準化：期初資產值=1.0，shares=1/entry_p
            shares = 1.0 / entry_p
            cash_recv = 0.0
            value_entry = 1.0
            sl_val_thr = (1.0 - float(sl_pct)) if sl_pct is not None else None
            tp_val_thr = (1.0 + float(tp_pct)) if tp_pct is not None else None
            rolling_high_val = value_entry
            # 準備該股的股利事件（日期排序）
            ev = div_df[div_df['stock_id']==str(sid)].copy()
            ev['dt'] = pd.to_datetime(ev['dt'], errors='coerce')
            ev = ev.dropna(subset=['dt']).sort_values('dt') if not ev.empty else ev
            ev_idx = 0
            ev_list = ev[['dt','cash_amt','stock_ratio']].values.tolist() if not ev.empty else []
            # 逐日：先應用 <= 當日的股利事件，再計算當日資產值
            for i in range(1, len(g)):
                d = g['date'].iloc[i]
                px = float(g['close_price'].iloc[i])
                # 套用所有 dt<=d 的事件
                while ev_idx < len(ev_list) and pd.to_datetime(ev_list[ev_idx][0]) <= d:
                    _, cash_amt_i, stock_ratio_i = ev_list[ev_idx]
                    stock_ratio_i = float(stock_ratio_i) if pd.notna(stock_ratio_i) else 0.0
                    cash_amt_i = float(cash_amt_i) if pd.notna(cash_amt_i) else 0.0
                    if stock_ratio_i != 0.0:
                        shares *= (1.0 + stock_ratio_i)
                    if cash_amt_i != 0.0:
                        cash_recv += cash_amt_i * shares
                    ev_idx += 1
                # 計算當日資產值
                val_now = px * shares + cash_recv
                rolling_high_val = max(rolling_high_val, val_now)
                hits = []
                if sl_val_thr is not None and val_now <= sl_val_thr:
                    hits.append(('停損', d, px))
                if tp_val_thr is not None and val_now >= tp_val_thr:
                    hits.append(('停利', d, px))
                if tsl_pct is not None and rolling_high_val>0 and val_now <= rolling_high_val * (1.0 - float(tsl_pct)):
                    hits.append(('移動停損', d, px))
                if not hits:
                    continue
                if trigger_priority == 'tp_first':
                    order = {'停利':0,'停損':1,'移動停損':2}
                elif trigger_priority == 'sl_first':
                    order = {'停損':0,'停利':1,'移動停損':2}
                else:
                    order = {'停損':0,'停利':1,'移動停損':2}
                hits.sort(key=lambda x: order.get(x[0], 99))
                exit_reason, exit_date, exit_p = hits[0]
                break
            # 出場時的資產值（若未提前出場，需把期末之前所有事件套用）
            if exit_reason == '期末':
                # 套用所有剩餘事件到期末
                while ev_idx < len(ev_list) and pd.to_datetime(ev_list[ev_idx][0]) <= exit_date:
                    _, cash_amt_i, stock_ratio_i = ev_list[ev_idx]
                    stock_ratio_i = float(stock_ratio_i) if pd.notna(stock_ratio_i) else 0.0
                    cash_amt_i = float(cash_amt_i) if pd.notna(cash_amt_i) else 0.0
                    if stock_ratio_i != 0.0:
                        shares *= (1.0 + stock_ratio_i)
                    if cash_amt_i != 0.0:
                        cash_recv += cash_amt_i * shares
                    ev_idx += 1
            # 最終資產值
            val_exit = exit_p * shares + cash_recv
            raw_ret = (exit_p/entry_p - 1.0) if (entry_p>0 and exit_p>0) else np.nan
            cash_div = cash_recv
            stock_ratio_agg = None  # 已以 shares 模擬，不再用倍增近似
            total_ret = (val_exit / value_entry - 1.0)
        else:
            # 無日期事件：回退到近似處理（僅期末加總股利與股票股利）
            # 目標停利價/停損價（相對進場）
            sl_thr = (entry_p * (1.0 - float(sl_pct))) if (sl_pct is not None and entry_p>0) else None
            tp_thr = (entry_p * (1.0 + float(tp_pct))) if (tp_pct is not None and entry_p>0) else None
            rolling_high = entry_p
            for i in range(1, len(g)):
                px = float(g['close_price'].iloc[i])
                d = g['date'].iloc[i]
                rolling_high = max(rolling_high, px)
                hits = []
                if sl_thr is not None and px <= sl_thr:
                    hits.append(('停損', d, px))
                if tp_thr is not None and px >= tp_thr:
                    hits.append(('停利', d, px))
                if tsl_pct is not None and rolling_high>0 and px <= rolling_high * (1.0 - float(tsl_pct)):
                    hits.append(('移動停損', d, px))
                if not hits:
                    continue
                if trigger_priority == 'tp_first':
                    order = {'停利':0,'停損':1,'移動停損':2}
                elif trigger_priority == 'sl_first':
                    order = {'停損':0,'停利':1,'移動停損':2}
                else:
                    order = {'停損':0,'停利':1,'移動停損':2}
                hits.sort(key=lambda x: order.get(x[0], 99))
                exit_reason, exit_date, exit_p = hits[0]
                break
            raw_ret = (exit_p/entry_p - 1.0) if (entry_p>0 and exit_p>0) else np.nan
            cash_div = 0.0
            stock_ratio_agg = 0.0
            if include_dividends:
                if exit_reason == '期末':
                    cash_div = float(div_df[div_df['stock_id']==str(sid)]['cash_div_ps'].sum()) if not div_df.empty else 0.0
                    stock_ratio_agg = float(div_df[div_df['stock_id']==str(sid)]['stock_ratio_total'].sum()) if 'stock_ratio_total' in div_df.columns else 0.0
                else:
                    cash_div = 0.0
                    stock_ratio_agg = 0.0
            adj_exit_p = exit_p * (1.0 + stock_ratio_agg)
            total_ret = ((adj_exit_p - entry_p + cash_div) / entry_p) if entry_p>0 else np.nan
        out_rows.append([
            str(sid), int(trading_year), entry_date.date().isoformat(), exit_date.date().isoformat(),
            entry_p, exit_p, raw_ret, cash_div, total_ret, exit_reason
        ])
    return pd.DataFrame(out_rows, columns=['stock_id','year','entry_date','exit_date','entry_price','exit_price','raw_return','cash_div','total_return','exit_reason'])


def run_equal_weight_backtest(db_path: str,
                              profile: str = 'conservative',
                              dynamic: bool = False,
                              include_dividends: bool = True,
                              sl_pct: float | None = 0.15,
                              tp_pct: float | None = None,
                              tsl_pct: float | None = None,
                              trigger_priority: str = 'chronological',
                              initial_capital: float = 1_000_000.0) -> Dict:
    """年度等權重再平衡回測（資金模擬版）。
    - dynamic=False：使用當前清單 Top N（靜態名單）
    - dynamic=True：使用清單歷史，每年以該年的 Top N（動態再構成）
    - include_dividends：是否將當年股利（現金與股票）計入報酬
    - sl_pct/tp_pct/tsl_pct：固定停損/停利/移動停損百分比（0.15=15%）
    - initial_capital：期初資金（預設 100 萬）
    資金配置：每年等資金配置到當年的持股，提前出場後資金不再投入（留現金）。
    輸出中文欄位 CSV 與 JSON 摘要。
    """
    # 產業/公司資料（兩種模式都會用到）
    with get_conn(db_path) as conn:
        # 嘗試讀取 stocks 基本欄位，若缺欄位則以空字串補上
        try:
            stocks_meta = pd.read_sql_query("SELECT stock_id, stock_name, industry FROM stocks", conn)
        except Exception:
            stocks_meta = pd.read_sql_query("SELECT stock_id FROM stocks", conn)
            stocks_meta['stock_name'] = ''
            stocks_meta['industry'] = ''
    # 統一股票代碼型別為字串，避免 int/str 合併錯誤
    if not stocks_meta.empty:
        stocks_meta['stock_id'] = stocks_meta['stock_id'].astype(str)
        if 'stock_name' not in stocks_meta.columns:
            stocks_meta['stock_name'] = ''
        if 'industry' not in stocks_meta.columns:
            stocks_meta['industry'] = ''

    if dynamic:
        from .history import load_history
        hist = load_history(profile)
        if hist.empty:
            raise ValueError('找不到清單歷史，請先以指定年度匯出清單並寫入歷史')
        # 準備 (year -> DataFrame with stock_id, rank)
        # 確保 stock_id 皆為字串
        hist['stock_id'] = hist['stock_id'].astype(str)
        year_map = {int(y): g.sort_values('rank')[['stock_id','rank']].reset_index(drop=True) for y, g in hist.groupby('year')}
        years_sorted = sorted(year_map.keys())
        # 依年度取價、計算年度報酬、等權與明細
        records = []
        details_list = []
        with get_conn(db_path) as conn:
            for y in years_sorted:
                g = year_map[y]
                # 同一年若歷史檔中同一股票重複出現，保留排名最前者
                g = g.sort_values('rank').drop_duplicates('stock_id', keep='first')
                ids = g['stock_id'].tolist()
                if not ids:
                    continue
                # 使用「隔年」的報酬：以 y 年清單在 y+1 年一開年買進、年底賣出
                trading_year = y + 1
                q_marks = ','.join(['?']*len(ids))
                prices = pd.read_sql_query(
                    f"SELECT stock_id, date, close_price FROM stock_prices WHERE stock_id IN ({q_marks}) AND strftime('%Y', date)=?",
                    conn, params=(ids + [str(trading_year)])
                )
                if prices.empty:
                    continue
                # 應用停損與（含息）報酬計算
                perf_y = _apply_stoploss_and_dividends(prices, trading_year, include_dividends, sl_pct, conn, tp_pct=tp_pct, tsl_pct=tsl_pct, trigger_priority=trigger_priority)
                # 資金模擬：等資金分配
                n = perf_y['stock_id'].nunique() if not perf_y.empty else 0
                cap_begin = initial_capital
                cap_alloc = (cap_begin / n) if n > 0 else 0.0
                cap_end = 0.0
                if n > 0:
                    for _, r in perf_y.iterrows():
                        entry_p = float(r['entry_price']) if pd.notna(r['entry_price']) else 0.0
                        cash_div = float(r['cash_div']) if pd.notna(r['cash_div']) else 0.0
                        total_ret = float(r['total_return']) if pd.notna(r['total_return']) else 0.0
                        # 金額方式：cap_alloc * (1 + total_ret)
                        cap_end += cap_alloc * (1.0 + total_ret)
                port_ret = (cap_end/cap_begin - 1.0) if cap_begin>0 and n>0 else np.nan
                records.append([trading_year, port_ret, n, cap_begin, cap_end])
                rep_y = perf_y.merge(g, on='stock_id', how='left').merge(stocks_meta, on='stock_id', how='left')
                rep_y['selected'] = rep_y['rank'].notna()
                rep_y['year'] = trading_year
                details_list.append(rep_y)
        port = pd.DataFrame(records, columns=['year','年度報酬率','成分股數','期初資金','期末資金']).sort_values('year')
        rep = pd.concat(details_list, ignore_index=True) if details_list else pd.DataFrame(columns=['stock_id','year','entry_date','exit_date','entry_price','exit_price','raw_return','cash_div','total_return','rank','stock_name','industry','selected'])
    else:
        top_df = load_quality_list(profile)  # columns: stock_id, rank
        stock_ids = top_df['stock_id'].tolist()
        with get_conn(db_path) as conn:
            # 只抓取清單中的股票收盤價
            q_marks = ','.join(['?'] * len(stock_ids))
            prices = pd.read_sql_query(
                f"SELECT stock_id, date, close_price FROM stock_prices WHERE stock_id IN ({q_marks})",
                conn, params=stock_ids
            )
        if prices.empty:
            raise ValueError('無股價資料可供回測')
        # 個股年度報酬（含停損/含息）
        perf_all = []
        for y in sorted(pd.to_datetime(prices['date']).dt.year.unique()):
            prices_y = prices[pd.to_datetime(prices['date']).dt.year == y]
            with get_conn(db_path) as conn:
                perf_y = _apply_stoploss_and_dividends(prices_y, int(y), include_dividends, sl_pct, conn, tp_pct=tp_pct, tsl_pct=tsl_pct, trigger_priority=trigger_priority)
            perf_all.append(perf_y)
        rep = pd.concat(perf_all, ignore_index=True) if perf_all else pd.DataFrame()
        # 合併排名與基本資料
        # 確保字串型別一致
        rep['stock_id'] = rep['stock_id'].astype(str)
        top_df['stock_id'] = top_df['stock_id'].astype(str)
        rep = rep.merge(top_df, on='stock_id', how='left')
        rep['selected'] = rep['rank'].notna()
        # 投組資金模擬：每年以 initial_capital 等資金分配到該年所有清單股
        years_sorted = sorted(pd.to_datetime(prices['date']).dt.year.unique())
        records = []
        for y in years_sorted:
            perf_y = rep[rep['year']==int(y)]
            n = perf_y['stock_id'].nunique() if not perf_y.empty else 0
            cap_begin = initial_capital
            cap_alloc = (cap_begin / n) if n>0 else 0.0
            cap_end = 0.0
            if n>0:
                for _, r in perf_y.iterrows():
                    total_ret = float(r['total_return']) if pd.notna(r['total_return']) else 0.0
                    cap_end += cap_alloc * (1.0 + total_ret)
            port_ret = (cap_end/cap_begin - 1.0) if cap_begin>0 and n>0 else np.nan
            records.append([int(y), port_ret, n, cap_begin, cap_end])
        port = pd.DataFrame(records, columns=['year','年度報酬率','成分股數','期初資金','期末資金']).sort_values('year')

    # 中文明細輸出
    rep = rep.merge(stocks_meta, on='stock_id', how='left')
    details = rep.rename(columns={
        'stock_id':'股票代碼', 'stock_name':'公司名稱', 'industry':'產業別',
        'year':'年度',
        'entry_date':'進場日', 'exit_date':'出場日',
        'entry_price':'進場價', 'exit_price':'出場價',
        'raw_return':'年度報酬率(不含息)', 'cash_div':'現金股利合計', 'total_return':'年度報酬率(含息)',
        'rank':'清單排名', 'selected':'是否入選', 'exit_reason':'出場理由'
    })
    details['是否入選'] = details['是否入選'].map(lambda x: '是' if bool(x) else '否')
    # 防止缺欄位報錯，若缺公司名稱/產業別則以空字串補上
    for col in ['公司名稱','產業別']:
        if col not in details.columns:
            details[col] = ''
    details = details[['年度','股票代碼','公司名稱','產業別','清單排名','進場日','出場日','進場價','出場價','出場理由','年度報酬率(不含息)','現金股利合計','年度報酬率(含息)','是否入選']]
    details = details.sort_values(['年度','清單排名'])
    out_details = os.path.join(OUTPUT_DIR, 'backtest_portfolio_details.csv')
    safe_write_csv(out_details,
                   [[int(r['年度']), str(r['股票代碼']), (int(r['清單排名']) if pd.notna(r['清單排名']) else 0),
                     str(r['公司名稱']) if pd.notna(r['公司名稱']) else '',
                     str(r['產業別']) if pd.notna(r['產業別']) else '',
                     str(r['進場日']) if pd.notna(r['進場日']) else '',
                     str(r['出場日']) if pd.notna(r['出場日']) else '',
                     float(r['進場價']) if pd.notna(r['進場價']) else '',
                     float(r['出場價']) if pd.notna(r['出場價']) else '',
                     str(r['出場理由']) if pd.notna(r['出場理由']) else '',
                     float(r['年度報酬率(不含息)']) if pd.notna(r['年度報酬率(不含息)']) else '',
                     float(r['現金股利合計']) if pd.notna(r['現金股利合計']) else '',
                     float(r['年度報酬率(含息)']) if pd.notna(r['年度報酬率(含息)']) else '',
                     str(r['是否入選'])]
                    for _, r in details.iterrows()],
                   ['年度','股票代碼','公司名稱','產業別','清單排名','進場日','出場日','進場價','出場價','出場理由','年度報酬率(不含息)','現金股利合計','年度報酬率(含息)','是否入選'])

    # 投組等權（動態模式已算於前，靜態模式上方已算）
    if dynamic:
        pass
    else:
        pass

    # 累積報酬與績效指標（以含息報酬為主）
    port['累積報酬值'] = (1.0 + port['年度報酬率']).cumprod()
    years = len(port)
    cagr = float(port['累積報酬值'].iloc[-1]) ** (1.0 / years) - 1.0 if years > 0 else 0.0
    # 最大回撤
    cum = port['累積報酬值']
    roll_max = cum.cummax()
    drawdown = (cum / roll_max) - 1.0
    mdd = float(drawdown.min()) if not drawdown.empty else 0.0
    # 勝率（年度報酬率 > 0 的比例）
    win_rate = float((port['年度報酬率'] > 0).mean()) if years > 0 else 0.0

    # 匯出 CSV（中文欄位）
    out_csv = os.path.join(OUTPUT_DIR, 'backtest_portfolio_report.csv')
    header = ['年度', '成分股數', '期初資金', '期末資金', '年度報酬率', '累積報酬值']
    rows = [
        [int(r['year']), int(r['成分股數']), int(round(float(r['期初資金']))), int(round(float(r['期末資金']))), float(r['年度報酬率']), float(r['累積報酬值'])]
        for _, r in port.iterrows()
    ]
    safe_write_csv(out_csv, rows, header)

    # 匯出摘要 JSON
    summary = {
        'profile': profile,
        'years': years,
        'annualized_return': cagr,   # 年化報酬率
        'max_drawdown': mdd,         # 最大回撤
        'win_rate': win_rate,        # 勝率（比例）
    }
    out_json = os.path.join(OUTPUT_DIR, 'backtest_portfolio_summary.json')
    safe_write_json(out_json, summary)

    log(f"📄 已輸出回測報告: {out_csv}")
    log(f"🧾 已輸出回測摘要: {out_json}")

    return {'report_csv': out_csv, 'summary_json': out_json, 'summary': summary}

