# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import csv
import pandas as pd
from typing import Optional
from .utils import OUTPUT_DIR, log

HIST_DIR = os.path.join(OUTPUT_DIR, 'history')
HIST_FILE = os.path.join(HIST_DIR, 'quality_list_history.csv')


def ensure_history_dir():
    os.makedirs(HIST_DIR, exist_ok=True)


def clear_history():
    """清除歷史檔案，重新開始記錄。"""
    ensure_history_dir()
    if os.path.exists(HIST_FILE):
        try:
            os.remove(HIST_FILE)
            log(f'🗑️ 已清除歷史檔案: {HIST_FILE}')
        except Exception as e:
            log(f'⚠️ 清除歷史檔案失敗: {e}')


def append_history(profile: str, year: int, as_of_date: str, df: pd.DataFrame, clear_first: bool = False) -> str:
    """將本次清單寫入歷史檔（CSV 追加）。
    若檔案被鎖定（Windows 常見），會改寫入 timestamp 後備檔，避免中斷流程。
    必要欄位：stock_id, score（若有）, rank（若有）。
    也會寫入指標欄位以利分析。

    Args:
        clear_first: 是否先清除歷史檔案（選單2/8使用）
    """
    ensure_history_dir()

    # 若需要清除歷史檔案
    if clear_first:
        clear_history()

    # 準備 rows
    rows = []
    for i, r in df.reset_index(drop=True).iterrows():
        rows.append([
            profile,
            int(year),
            str(as_of_date or ''),
            r.get('stock_id',''),
            int(r.get('rank', i+1)),
            float(r.get('score', 0)) if pd.notna(r.get('score', None)) else '',
            float(r.get('roe_5y_avg', 0)) if pd.notna(r.get('roe_5y_avg', None)) else '',
            float(r.get('revenue_cagr_5y', 0)) if pd.notna(r.get('revenue_cagr_5y', None)) else '',
            int(r.get('cash_div_years', 0)) if pd.notna(r.get('cash_div_years', None)) else '',
            float(r.get('pe_pct_5y', 0)) if pd.notna(r.get('pe_pct_5y', None)) else '',
            float(r.get('pb_pct_5y', 0)) if pd.notna(r.get('pb_pct_5y', None)) else '',
        ])
    header = ['profile','year','as_of_date','stock_id','rank','score','roe_5y_avg','revenue_cagr_5y','cash_div_years','pe_pct_5y','pb_pct_5y']
    write_header = not os.path.exists(HIST_FILE)
    try:
        with open(HIST_FILE, 'a', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(header)
            w.writerows(rows)
        log(f'🧾 已寫入清單歷史: {HIST_FILE} （{len(rows)} 筆）')
        return HIST_FILE
    except Exception:
        # 後備檔名：加 timestamp，避免被鎖住時失敗
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        alt = os.path.join(HIST_DIR, f'quality_list_history_{ts}.csv')
        with open(alt, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        log(f'🟡 歷史檔被鎖定，已寫入後備檔: {alt} （{len(rows)} 筆）')
        return alt


def load_history(profile: Optional[str] = None) -> pd.DataFrame:
    if not os.path.exists(HIST_FILE):
        return pd.DataFrame()
    df = pd.read_csv(HIST_FILE, encoding='utf-8-sig')
    if profile:
        df = df[df['profile'] == profile]
    return df

