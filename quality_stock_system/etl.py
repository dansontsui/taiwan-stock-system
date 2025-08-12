# -*- coding: utf-8 -*-
"""
ETL to build marts for quality stock screening.
- mart_quality_factors_yearly
- mart_dividend_stability
Safe against missing tables: will create marts if not exists and skip missing sources with warnings.
"""
from __future__ import annotations
import math
from typing import List, Tuple
import pandas as pd
from .utils import get_conn, log

CREATE_MART_VAL = """
CREATE TABLE IF NOT EXISTS mart_valuation_snapshot (
  stock_id TEXT NOT NULL,
  snap_date TEXT NOT NULL,
  pe_pct_5y REAL,
  pb_pct_5y REAL,
  PRIMARY KEY(stock_id, snap_date)
);
"""

CREATE_MART_QUALITY = """
CREATE TABLE IF NOT EXISTS mart_quality_factors_yearly (
  stock_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  roe_5y_avg REAL,
  revenue_cagr_5y REAL,
  fcf_positive_years_5y INTEGER,
  net_debt_to_equity REAL,
  interest_coverage REAL,
  accruals_3y_avg REAL,
  PRIMARY KEY(stock_id, year)
);
"""

CREATE_MART_DIVIDEND = """
CREATE TABLE IF NOT EXISTS mart_dividend_stability (
  stock_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  cash_div_years INTEGER,
  dividend_growth_5y REAL,
  payout_ratio_range_ok INTEGER,
  PRIMARY KEY(stock_id, year)
);
"""

# Helpers

def _table_exists(conn, name: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def build_quality_mart(db_path: str | None = None) -> None:
    """Build mart_quality_factors_yearly from available sources.
    If sources are missing, fill with NULLs and warn.
    """
    with get_conn(db_path) as conn:
        conn.execute(CREATE_MART_QUALITY)
        # Basic stock universe
        if not _table_exists(conn, 'stocks'):
            log('⚠️ 缺少 stocks 表，無法建立樣本集')
            return
        stocks = pd.read_sql_query("SELECT stock_id FROM stocks", conn)
        if stocks.empty:
            log('⚠️ stocks 無資料')
            return

        # Determine years from monthly_revenues if available
        years = None
        if _table_exists(conn, 'monthly_revenues'):
            df_rev = pd.read_sql_query(
                "SELECT stock_id, strftime('%Y', date) as y, SUM(revenue) AS rev FROM monthly_revenues GROUP BY stock_id, y",
                conn)
            if not df_rev.empty:
                years = sorted(df_rev['y'].dropna().unique())
        if years is None:
            years = ['2020','2021','2022','2023','2024']  # fallback
            log('⚠️ 使用預設年度範圍，請補齊 monthly_revenues 資料')

        # Pre-aggregations
        # 5y revenue CAGR per stock per latest year in window
        rev_agg = None
        if _table_exists(conn, 'monthly_revenues'):
            rev_agg = pd.read_sql_query(
                """
                WITH rev AS (
                  SELECT stock_id, strftime('%Y', date) AS y, SUM(revenue) AS rev
                  FROM monthly_revenues GROUP BY stock_id, y
                )
                SELECT r1.stock_id, r2.y AS year,
                       CASE WHEN r1.rev>0 THEN POWER(r2.rev*1.0/r1.rev, 1.0/4) - 1 ELSE NULL END AS revenue_cagr_5y
                FROM rev r1
                JOIN rev r2 ON r1.stock_id=r2.stock_id AND CAST(r2.y AS INTEGER)-CAST(r1.y AS INTEGER)=4
                """,
                conn)
        else:
            log('⚠️ 缺少 monthly_revenues，無法計算 revenue_cagr_5y')

        # ROE 5y avg（以 Python 端計算，避免 SQLite 窗函數相容性問題）
        roe_agg = None
        if _table_exists(conn, 'financial_ratios'):
            df_fr = pd.read_sql_query("SELECT stock_id, date, roe FROM financial_ratios", conn)
            if not df_fr.empty and 'roe' in df_fr.columns:
                df_fr['date'] = pd.to_datetime(df_fr['date'], errors='coerce')
                df_fr['year'] = df_fr['date'].dt.year
                yearly = df_fr.dropna(subset=['year']).groupby(['stock_id','year'], as_index=False)['roe'].mean()
                # 對每檔股票做 5 年滾動平均
                parts = []
                for sid, g in yearly.groupby('stock_id'):
                    g = g.sort_values('year')
                    g['roe_5y_avg'] = g['roe'].rolling(window=5, min_periods=2).mean()
                    parts.append(g[['stock_id','year','roe_5y_avg']])
                if parts:
                    roe_agg = pd.concat(parts, ignore_index=True)
        else:
            log('⚠️ 缺少 financial_ratios，無法計算 roe_5y_avg')

        # Assemble mart rows
        import math
        def _safe_float(v):
            try:
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        return None
                    return float(v)
                # pandas may give numpy types or strings
                vf = float(v)
                if math.isnan(vf) or math.isinf(vf):
                    return None
                return vf
            except Exception:
                return None

        rows = []
        for stock_id in stocks['stock_id']:
            for y in years:
                year = int(y)
                rec = {
                    'stock_id': stock_id,
                    'year': year,
                    'roe_5y_avg': None,
                    'revenue_cagr_5y': None,
                    'fcf_positive_years_5y': None,
                    'net_debt_to_equity': None,
                    'interest_coverage': None,
                    'accruals_3y_avg': None,
                }
                if rev_agg is not None:
                    hit = rev_agg[(rev_agg['stock_id']==stock_id) & (rev_agg['year']==str(year))]
                    if not hit.empty:
                        rec['revenue_cagr_5y'] = _safe_float(hit['revenue_cagr_5y'].iloc[0])
                if roe_agg is not None:
                    hit = roe_agg[(roe_agg['stock_id']==stock_id) & (roe_agg['year']==str(year))]
                    if not hit.empty:
                        rec['roe_5y_avg'] = _safe_float( hit['roe_5y_avg'].iloc[0] )
                rows.append(rec)
        # Upsert rows
        if rows:
            df_out = pd.DataFrame(rows)
            df_out.to_sql('mart_quality_factors_yearly', conn, if_exists='replace', index=False)
            log(f'✅ 建立 mart_quality_factors_yearly，共 {len(df_out)} 筆')
        else:
            log('⚠️ 無可輸出資料（品質 mart）')


def build_dividend_mart(db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(CREATE_MART_DIVIDEND)
        if not _table_exists(conn, 'stocks'):
            log('⚠️ 缺少 stocks 表，無法建立樣本集')
            return
        stocks = pd.read_sql_query("SELECT stock_id FROM stocks", conn)
        if stocks.empty:
            log('⚠️ stocks 無資料')
            return
        # 讀取配息原始資料（每年是否有現金股利）
        div_years = None
        if _table_exists(conn, 'dividend_policies'):
            div_years = pd.read_sql_query(
                """
                SELECT stock_id, year,
                       CASE WHEN SUM(CASE WHEN (cash_earnings_distribution>0 OR cash_statutory_surplus>0) THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END AS has_dividend
                FROM dividend_policies GROUP BY stock_id, year
                """,
                conn)
            if not div_years.empty:
                # 處理民國年格式（如「100年」）轉西元年
                def convert_year(y):
                    try:
                        if isinstance(y, str) and y.endswith('年'):
                            return int(y[:-1]) + 1911  # 民國年轉西元年
                        return int(y)
                    except:
                        return None
                div_years['year'] = div_years['year'].apply(convert_year)
                div_years = div_years.dropna(subset=['year'])
                div_years['year'] = div_years['year'].astype(int)
        else:
            log('⚠️ 缺少 dividend_policies，無法計算配息年數')
        # 年度範圍：自動偵測 dividend 或 revenues 的年份；否則 fallback
        years = None
        if div_years is not None and not div_years.empty:
            years = sorted(div_years['year'].dropna().unique().tolist())
        if years is None and _table_exists(conn, 'monthly_revenues'):
            y2 = pd.read_sql_query("SELECT DISTINCT CAST(strftime('%Y', date) AS INTEGER) AS year FROM monthly_revenues", conn)
            if not y2.empty:
                years = sorted(y2['year'].dropna().unique().tolist())
        if years is None:
            import datetime as _dt
            years = list(range(2014, _dt.datetime.now().year+1))
            log('⚠️ 使用預設年度範圍建立股利 mart')
        # 以過去 5 年滾動視窗計算 cash_div_years（連續配息年數的 proxy）
        rows = []
        for stock_id in stocks['stock_id']:
            div_map = {}
            if div_years is not None and not div_years.empty:
                div_map = {int(r['year']): int(r['has_dividend']) for _, r in div_years[div_years['stock_id']==stock_id].iterrows()}
            for year in years:
                rec = {
                    'stock_id': stock_id,
                    'year': int(year),
                    'cash_div_years': None,
                    'dividend_growth_5y': None,
                    'payout_ratio_range_ok': None,
                }
                # 過去五年（含當年）的有配息年數
                cnt = 0
                for y in range(year-4, year+1):
                    if div_map.get(y, 0) == 1:  # 該年有配息
                        cnt += 1
                rec['cash_div_years'] = int(cnt)
                rows.append(rec)
        if rows:
            df_out = pd.DataFrame(rows)
            df_out.to_sql('mart_dividend_stability', conn, if_exists='replace', index=False)
            log(f'✅ 建立 mart_dividend_stability，共 {len(df_out)} 筆')
        else:
            log('⚠️ 無可輸出資料（股利 mart）')


def build_valuation_mart(db_path: str | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(CREATE_MART_VAL)
        if not _table_exists(conn, 'stocks'):
            log('⚠️ 缺少 stocks，略過估值快照')
            return
        # 優先使用 financial_ratios；若缺，走 fallback：以收盤價與近一年/年度 EPS、淨值推估 PB
        if _table_exists(conn, 'financial_ratios'):
            df = pd.read_sql_query(
                """
                WITH hist AS (
                  SELECT stock_id, date, pe_ratio, pb_ratio
                  FROM financial_ratios
                  WHERE date >= date('now','-5 years')
                ), curr AS (
                  SELECT h.stock_id, MAX(h.date) AS snap_date
                  FROM hist h GROUP BY h.stock_id
                )
                SELECT c.stock_id, c.snap_date,
                       (
                         SELECT 1.0*SUM(CASE WHEN h2.pe_ratio <= h1.pe_ratio THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0)
                         FROM hist h2 WHERE h2.stock_id=h1.stock_id
                       ) AS pe_pct_5y,
                       (
                         SELECT 1.0*SUM(CASE WHEN h3.pb_ratio <= h1.pb_ratio THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0)
                         FROM hist h3 WHERE h3.stock_id=h1.stock_id
                       ) AS pb_pct_5y
                FROM hist h1
                JOIN curr c ON h1.stock_id=c.stock_id AND h1.date=c.snap_date
                """,
                conn)
            if df.empty:
                log('⚠️ 無估值資料可產生快照')
                return
            df.to_sql('mart_valuation_snapshot', conn, if_exists='replace', index=False)
            log(f'✅ 建立 mart_valuation_snapshot，共 {len(df)} 筆')
        else:
            # fallback：以每檔股票近 5 年的 PB（由市價/每股淨值推估）分位；PE 暫設為 NULL
            # 需求：需有 stock_prices（收盤價）與每股淨值（Equity/Share）。若無法取得股本，則以 PB ≈ MarketCap/BookValue（簡化處理）。
            if not _table_exists(conn, 'stock_prices'):
                log('⚠️ 缺少 financial_ratios 且無 stock_prices，無法計算估值分位')
                return
            # 先取近 5 年日收盤價的年度最後收盤價
            prices = pd.read_sql_query(
                "SELECT stock_id, date, close_price FROM stock_prices WHERE date >= date('now','-5 years')",
                conn)
            if prices.empty:
                log('⚠️ stock_prices 無近五年資料，無法計算 PB 分位')
                return
            prices['date'] = pd.to_datetime(prices['date'], errors='coerce')
            prices['year'] = prices['date'].dt.year
            last_close = prices.sort_values('date').groupby(['stock_id','year']).last().reset_index()[['stock_id','year','close_price']]
            # 嘗試取得每股淨值（book value per share），若無則只能略過 PB 分位
            # 這裡僅放置框架，實際需有 shares/Equity 資料表支持
            df_pb = last_close.copy()
            df_pb['pb_ratio'] = None  # TODO: 填入由 Equity/Shares 計算的每股淨值後，計算 PB
            # 以空結果提醒
            log('⚠️ 使用 fallback 估值：尚未取得每股淨值資料，PB 分位無法計算')


def build_all_marts(db_path: str | None = None) -> None:
    log('🚧 開始建立品質與股利 marts ...')
    build_quality_mart(db_path)
    build_dividend_mart(db_path)
    build_valuation_mart(db_path)
    log('🎉 marts 建立完成')

