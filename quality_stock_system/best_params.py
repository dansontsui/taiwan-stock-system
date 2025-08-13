# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import pandas as pd
from .utils import OUTPUT_DIR

def pick_best_params(csv_path: str|None=None, objective: str='annualized_minus_half_mdd'):
    if not csv_path:
        csv_path = os.path.join(OUTPUT_DIR, 'backtest_param_sweep.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    # 期望欄位：sl_pct,tp_pct,tsl_pct,年化報酬,最大回撤,勝率
    if objective == 'annualized':
        df = df.sort_values('年化報酬', ascending=False)
    elif objective == 'mdd':
        df = df.sort_values('最大回撤')  # 越小越好（負值更小）
    else:
        # 年化 - 0.5*|MDD|（平衡效率與風險）
        df['score'] = df['年化報酬'] - 0.5 * (df['最大回撤'].abs())
        df = df.sort_values('score', ascending=False)
    row = df.iloc[0]
    # 處理 None 值
    sl = None if row['sl_pct'] == 'None' else float(row['sl_pct'])
    tp = None if row['tp_pct'] == 'None' else float(row['tp_pct'])
    tsl = None if row['tsl_pct'] == 'None' else float(row['tsl_pct'])
    return sl, tp, tsl

