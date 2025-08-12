# -*- coding: utf-8 -*-
"""
Rule profiles for quality screening.
Profiles are lightweight and ASCII-only keys; CLI/logs can be Chinese.
"""
from __future__ import annotations
import json
import os
from typing import Dict, Any

DEFAULT_PROFILES = {
    "conservative": {
        "years_window": 5,
        "exclude_financials": True,
        "thresholds": {
            "roe_5y_avg": 10.0,
            "revenue_cagr_5y": 0.03,
            "cash_div_years": 3,
            # 估值分位（可缺資料時忽略）
            "pe_pct_5y": 0.60,
            "pb_pct_5y": 0.60,
        },
        "weights": {
            "roe_5y_avg": 0.4,
            "revenue_cagr_5y": 0.3,  # 乘以 100 後再乘權重
            "cash_div_years": 0.3
        }
    },
    "value": {
        "years_window": 5,
        "exclude_financials": False,
        "thresholds": {
            "pe_pct_5y": 0.40,
            "pb_pct_5y": 0.40
        },
        "weights": {
            "roe_5y_avg": 0.2,
            "revenue_cagr_5y": 0.2,
            "cash_div_years": 0.2,
            "valuation": 0.4
        }
    },
    "strict": {
        "years_window": 5,
        "exclude_financials": True,
        "thresholds": {
            "revenue_cagr_5y": 0.05,
            "cash_div_years": 3,
            "require_fields": True  # 重新開啟嚴格檢查
        },
        "risk": {
            "year_return_gt": 0.0,
            "mdd_le": 0.30
        },
        "weights": {
            "revenue_cagr_5y": 0.60,
            "cash_div_years": 0.40
        }
    }
}


def load_profile(name: str, path: str | None = None) -> Dict[str, Any]:
    """Load rule profile from JSON file or fallback to defaults."""
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_PROFILES.get(name, DEFAULT_PROFILES['conservative'])

