# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import itertools
import pandas as pd
from typing import List, Tuple, Dict
from .backtest import run_equal_weight_backtest
from .utils import OUTPUT_DIR, log


def param_grid(values: Dict[str, List[float]]) -> List[Dict[str, float]]:
    keys = list(values.keys())
    prod = list(itertools.product(*[values[k] for k in keys]))
    return [dict(zip(keys, p)) for p in prod]


def sweep_params(db_path: str, profile: str, dynamic: bool, sl_list: List[float], tp_list: List[float], tsl_list: List[float]) -> str:
    rows = []
    combos = param_grid({'sl': sl_list, 'tp': tp_list, 'tsl': tsl_list})
    for c in combos:
        res = run_equal_weight_backtest(db_path, profile=profile, dynamic=dynamic, include_dividends=True,
                                        sl_pct=c['sl'], tp_pct=c['tp'], tsl_pct=c['tsl'])
        s = res['summary']
        # 處理 None 值的顯示
        sl_display = c['sl'] if c['sl'] is not None else 'None'
        tp_display = c['tp'] if c['tp'] is not None else 'None'
        tsl_display = c['tsl'] if c['tsl'] is not None else 'None'
        rows.append([sl_display, tp_display, tsl_display, s['annualized_return'], s['max_drawdown'], s['win_rate']])
    df = pd.DataFrame(rows, columns=['sl_pct','tp_pct','tsl_pct','年化報酬','最大回撤','勝率'])
    out_csv = os.path.join(OUTPUT_DIR, 'backtest_param_sweep.csv')
    df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    log(f"📊 已輸出參數掃描結果: {out_csv}")
    return out_csv

