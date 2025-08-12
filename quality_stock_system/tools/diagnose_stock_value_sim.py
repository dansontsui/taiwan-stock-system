# -*- coding: utf-8 -*-
import sys, sqlite3
import pandas as pd

# 使用方法：
# python -m quality_stock_system.tools.diagnose_stock_value_sim <db_path> <stock_id> <year> [sl_pct] [--price-table T] [--date-col D] [--price-col P] [--verbose]
# 範例：
# python -m quality_stock_system.tools.diagnose_stock_value_sim quality_stock_system/data/taiwan_stock.db 1808 2024 0.15
# python -m quality_stock_system.tools.diagnose_stock_value_sim quality_stock_system/data/ts.db 1808 2024 0.15 --price-table daily_prices --date-col trade_date --price-col close --verbose

PRICE_DATE_CAND = ['date','trade_date','tdate']
PRICE_COL_CAND = ['close_price','close','adj_close','price']


def _detect_price_table(conn: sqlite3.Connection):
    tbls = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    tables = tbls['name'].tolist() if not tbls.empty else []
    for t in tables:
        try:
            info = pd.read_sql_query(f"PRAGMA table_info({t})", conn)
            cols = set(info['name'].tolist()) if not info.empty else set()
            if 'stock_id' in cols and any(c in cols for c in PRICE_DATE_CAND) and any(c in cols for c in PRICE_COL_CAND):
                # 偵測欄位名
                dcol = next((c for c in PRICE_DATE_CAND if c in cols), None)
                pcol = next((c for c in PRICE_COL_CAND if c in cols), None)
                return t, dcol, pcol
        except Exception:
            continue
    return None, None, None


def diagnose(db_path: str, stock_id: str, year: int, sl_pct: float = 0.15, price_table: str|None=None, date_col: str|None=None, price_col: str|None=None, verbose: bool=False):
    conn = sqlite3.connect(db_path)
    # 取得價格表與欄位
    if not price_table or not date_col or not price_col:
        t, dcol, pcol = _detect_price_table(conn)
        price_table = price_table or t
        date_col = date_col or dcol
        price_col = price_col or pcol
    if not price_table or not date_col or not price_col:
        raise RuntimeError('找不到價格表或欄位，請使用 --price-table/--date-col/--price-col 指定')

    prices = pd.read_sql_query(
        f"SELECT {date_col} AS dt, {price_col} AS px FROM {price_table} WHERE stock_id=? AND strftime('%Y', {date_col})=? ORDER BY {date_col}",
        conn, params=(stock_id, str(year))
    )
    if prices.empty:
        raise RuntimeError('⚠️ 無該年度日收盤資料（請確認 stock_id/year 與表名/欄位設定）')

    # 嘗試偵測股利日期欄位
    cols = pd.read_sql_query("PRAGMA table_info(dividend_policies)", conn)
    available = set(cols['name'].tolist()) if not cols.empty else set()
    dcol2 = None
    for c in ['ex_date','pay_date','announcement_date','record_date','date']:
        if c in available:
            dcol2 = c
            break
    cash_cols = [c for c in ['cash_earnings_distribution','cash_earnings_distrubtion','cash_statutory_surplus','cash_capital_reserve','cash_dividend'] if c in available]
    if 'stock_earnings_distribution' in available:
        stock_col = 'stock_earnings_distribution'
    elif 'stock_earnings_distrubtion' in available:
        stock_col = 'stock_earnings_distrubtion'
    else:
        stock_col = None

    events = []
    if 'dividend_policies' in pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].tolist():
        if dcol2:
            sel = []
            sel.append(("+".join(cash_cols) if cash_cols else "0.0") + " AS cash_amt")
            sel.append((stock_col if stock_col else "0.0") + " AS stock_ratio")
            sql = f"SELECT {dcol2} AS dt, {', '.join(sel)} FROM dividend_policies WHERE stock_id=?"
            ev = pd.read_sql_query(sql, conn, params=(stock_id,))
            if not ev.empty:
                ev['dt'] = pd.to_datetime(ev['dt'], errors='coerce')
                ev['y'] = ev['dt'].dt.year
                ev = ev[ev['y']==year]
                ev = ev.dropna(subset=['dt'])
                ev = ev.sort_values('dt')
                events = ev[['dt','cash_amt','stock_ratio']].values.tolist()
        elif 'year' in available:
            sel = []
            sel.append(("+".join(cash_cols) if cash_cols else "0.0") + " AS cash_amt")
            sel.append((stock_col if stock_col else "0.0") + " AS stock_ratio")
            sql = f"SELECT year AS y, {', '.join(sel)} FROM dividend_policies WHERE stock_id=? AND year=?"
            ev = pd.read_sql_query(sql, conn, params=(stock_id, str(year)))
            if not ev.empty:
                cash_amt = float(ev['cash_amt'].sum()) if 'cash_amt' in ev.columns else 0.0
                stock_ratio = float(ev['stock_ratio'].sum()) if 'stock_ratio' in ev.columns else 0.0
                events = [[None, cash_amt, stock_ratio]]

    # 模擬
    prices['dt'] = pd.to_datetime(prices['dt'])
    entry_date = prices['dt'].iloc[0]
    entry_p = float(prices['px'].iloc[0])
    shares = 1.0 / entry_p
    cash_recv = 0.0
    sl_val_thr = 1.0 - sl_pct
    rolling_high_val = 1.0
    stop = None
    idx = 0

    track = []
    for i in range(1, len(prices)):
        d = prices['dt'].iloc[i]
        px = float(prices['px'].iloc[i])
        # 套用事件（若有日期，採用到當日為止）
        daily_events = []
        while idx < len(events) and events[idx][0] is not None and pd.to_datetime(events[idx][0]) <= d:
            _, cash_amt_i, stock_ratio_i = events[idx]
            stock_ratio_i = float(stock_ratio_i) if pd.notna(stock_ratio_i) else 0.0
            cash_amt_i = float(cash_amt_i) if pd.notna(cash_amt_i) else 0.0
            if stock_ratio_i != 0.0:
                shares *= (1.0 + stock_ratio_i)
            if cash_amt_i != 0.0:
                cash_recv += cash_amt_i * shares
            daily_events.append((float(stock_ratio_i), float(cash_amt_i)))
            idx += 1
        val_now = px * shares + cash_recv
        rolling_high_val = max(rolling_high_val, val_now)
        track.append((d.date().isoformat(), px, shares, cash_recv, val_now, daily_events))
        if (stop is None) and (val_now <= sl_val_thr):
            stop = (d.date().isoformat(), px, val_now, '停損(價值)')
            break

    last_date = prices['dt'].iloc[-1]
    last_p = float(prices['px'].iloc[-1])
    while idx < len(events) and events[idx][0] is None:
        _, cash_amt_i, stock_ratio_i = events[idx]
        stock_ratio_i = float(stock_ratio_i) if pd.notna(stock_ratio_i) else 0.0
        cash_amt_i = float(cash_amt_i) if pd.notna(cash_amt_i) else 0.0
        if stock_ratio_i != 0.0:
            shares *= (1.0 + stock_ratio_i)
        if cash_amt_i != 0.0:
            cash_recv += cash_amt_i * shares
        idx += 1
    val_end = last_p * shares + cash_recv

    return {
        'entry_date': entry_date.date().isoformat(),
        'entry_price': entry_p,
        'events': events,
        'stop': stop,
        'val_end': val_end,
        'price_table': price_table,
        'date_col': date_col,
        'price_col': price_col,
        'track_head': track[:10],
        'track_tail': track[-10:],
    }


def main():
    if len(sys.argv) < 4:
        print("用法: python -m quality_stock_system.tools.diagnose_stock_value_sim <db_path> <stock_id> <year> [sl_pct] [--price-table T] [--date-col D] [--price-col P]")
        sys.exit(1)
    db_path = sys.argv[1]
    stock_id = str(sys.argv[2])
    year = int(sys.argv[3])
    sl_pct = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 0.15
    # 解析可選參數
    price_table = None
    date_col = None
    price_col = None
    verbose = False
    args = sys.argv[5:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--price-table' and i+1 < len(args):
            price_table = args[i+1]; i += 2; continue
        if a == '--date-col' and i+1 < len(args):
            date_col = args[i+1]; i += 2; continue
        if a == '--price-col' and i+1 < len(args):
            price_col = args[i+1]; i += 2; continue
        if a == '--verbose':
            verbose = True; i += 1; continue
        i += 1

    try:
        res = diagnose(db_path, stock_id, year, sl_pct, price_table, date_col, price_col, verbose)
        print(f"標的: {stock_id} 年度: {year}")
        print(f"進場日: {res['entry_date']} 進場價: {res['entry_price']}")
        if res['events']:
            print("股利事件（日期, 股票股利比率, 現金股利/股）:")
            for dt, cash_amt, stock_ratio in res['events']:
                dts = (pd.to_datetime(dt).date().isoformat() if dt is not None else '年度')
                print(f" - {dts}, stock_ratio={float(stock_ratio):.4f}, cash={float(cash_amt):.4f}")
        if res['stop']:
            d, px, val, reason = res['stop']
            print(f"觸發：{reason} 於 {d}，當日收盤 {px}，資產值倍率 {val:.4f}")
        else:
            print("未觸發停損(價值)")
        print(f"期末資產值倍率：{res['val_end']:.4f}")
        print(f"價格表推斷: {res['price_table']} (date={res['date_col']}, price={res['price_col']})")
        if verbose:
            print("--- 資產值軌跡（前10/後10）---")
            for tag, track in [('HEAD', res['track_head']), ('TAIL', res['track_tail'])]:
                print(f"[{tag}] 共 {len(track)} 筆")
                for row in track:
                    d, px, sh, cash, val, events = row
                    evs = ', '.join([f"stock+{er:.2f}x,cash+{ec:.2f}" for er, ec in events]) if events else '-'
                    print(f"  {d}: px={px}, shares={sh:.4f}, cash={cash:.4f}, val={val:.4f}, events={evs}")
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")

if __name__ == '__main__':
    main()

