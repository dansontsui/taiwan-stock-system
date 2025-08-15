# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 系統配置檔案
Stock Price Investment System - System Configuration
"""

import os
from pathlib import Path
from typing import Dict, Any

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
SYSTEM_ROOT = PROJECT_ROOT.parent  # taiwan-stock-system根目錄

# 資料庫配置
DATABASE_CONFIG = {
    'path': SYSTEM_ROOT / "data" / "taiwan_stock.db",
    'timeout': 30,
    'check_same_thread': False
}

# Walk-forward 驗證配置
WALKFORWARD_CONFIG = {
    # 時間範圍
    'training_start': '2015-01',
    'training_end': '2022-12',
    'holdout_start': '2023-01',
    'holdout_end': '2024-12',
    
    # 視窗設定
    'train_window_months': 48,  # 訓練視窗48個月
    'test_window_months': 12,   # 測試視窗12個月
    'stride_months': 12,        # 步長12個月
    
    # 最小資料要求
    'min_training_samples': 10,  # 進一步降低最小樣本數要求，適合小樣本測試
    'min_stock_history_months': 60,
}

# 特徵工程配置
FEATURE_CONFIG = {
    # 營收特徵
    'revenue_features': {
        'yoy_periods': [1, 3, 6, 12],  # YoY計算期間
        'mom_periods': [1, 3, 6],      # MoM計算期間
        'ma_periods': [3, 6, 12],      # 移動平均期間
        'volatility_window': 12,       # 波動性計算視窗
    },
    
    # 技術特徵
    'technical_features': {
        'ma_periods': [5, 20, 60],     # 移動平均線
        'rsi_period': 14,              # RSI期間
        'macd_fast': 12,               # MACD快線
        'macd_slow': 26,               # MACD慢線
        'macd_signal': 9,              # MACD信號線
        'volume_ma_period': 20,        # 成交量移動平均
    },
    
    # 產業特徵
    'industry_features': {
        'enable_industry_encoding': True,
        'enable_market_cap_features': True,
        'enable_listing_age_features': True,
    }
}

# 模型配置
MODEL_CONFIG = {
    # 主要模型
    'primary_model': 'xgboost',
    
    # XGBoost參數
    'xgboost_params': {
        'objective': 'reg:squarederror',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'n_jobs': -1,
    },
    
    # LightGBM參數
    'lightgbm_params': {
        'objective': 'regression',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'n_jobs': -1,
        'verbose': -1,
    },
    
    # 信心區間設定
    'confidence_config': {
        'enable_quantile_regression': True,
        'quantiles': [0.1, 0.25, 0.5, 0.75, 0.9],
        'ensemble_size': 5,
    }
}

# 選股配置
SELECTION_CONFIG = {
    # 候選池生成門檻
    'candidate_pool_thresholds': {
        'min_win_rate': 0.52,          # 最小勝率52%
        'min_profit_loss_ratio': 1.2,  # 最小盈虧比1.2
        'min_trade_count': 5,          # 最小交易次數
        'min_folds_with_trades': 2,    # 最少有交易的fold數
        'max_drawdown_threshold': 0.25, # 最大回撤門檻25%
    },
    
    # 選股規則
    'selection_rules': {
        'min_expected_return': 0.02,   # 最小預期報酬5%
        'min_confidence_score': 0.3,   # 最小信心分數60%
        'technical_confirmation': True, # 技術面確認
        'max_correlation': 0.7,        # 最大相關性70%
    }
}

# 交易策略配置
TRADING_CONFIG = {
    # 倉位管理
    'position_management': {
        'max_single_position': 0.05,   # 單股最大權重5%
        'max_total_positions': 20,     # 最大持股數量
        'rebalance_frequency': 'monthly', # 再平衡頻率
        'position_sizing_method': 'equal_weight', # 等權重
    },
    
    # 風險控制
    'risk_management': {
        'stop_loss': 0.12,             # 停損12%
        'take_profit': 0.20,           # 停利20%
        'max_holding_period': 90,      # 最大持有期90天
        'enable_atr_stops': False,     # 是否啟用ATR動態停損
        'atr_multiplier': 2.0,         # ATR倍數
    },
    
    # 交易成本
    'transaction_costs': {
        'commission_rate': 0.001425,   # 手續費0.1425%
        'tax_rate': 0.003,             # 證交稅0.3%
        'slippage_bps': 5,             # 滑價5個基點
    }
}

# 回測配置
BACKTEST_CONFIG = {
    # 初始資金
    'initial_capital': 1000000,        # 初始資金100萬
    
    # 報告設定
    'reporting': {
        'enable_html_reports': True,
        'enable_csv_exports': True,
        'enable_interactive_charts': True,
        'chart_library': 'plotly',
    },
    
    # 績效指標
    'performance_metrics': [
        'total_return',
        'annualized_return',
        'sharpe_ratio',
        'max_drawdown',
        'win_rate',
        'profit_loss_ratio',
        'calmar_ratio',
        'sortino_ratio',
    ]
}

# 輸出配置
OUTPUT_CONFIG = {
    # 編碼設定
    'encoding': 'utf-8-sig',
    'locale': 'zh_TW',

    # 檔案路徑（所有輸出都在系統資料夾內）
    'paths': {
        'reports': PROJECT_ROOT / 'reports',
        'logs': PROJECT_ROOT / 'logs',
        'models': PROJECT_ROOT / 'models',
        'data_cache': PROJECT_ROOT / 'data' / 'cache',
        'walk_forward_results': PROJECT_ROOT / 'results' / 'walk_forward',
        'candidate_pools': PROJECT_ROOT / 'results' / 'candidate_pools',
        'holdout_results': PROJECT_ROOT / 'results' / 'holdout',
        'backtest_results': PROJECT_ROOT / 'results' / 'backtest',
    },

    # 日誌設定
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_encoding': 'utf-8',
    }
}

# CLI選單配置
CLI_CONFIG = {
    'menu_items': [
        {'id': '1', 'name': '執行月度流程（營收→股價→選股→建議→報告）', 'icon': '⚙️'},
        {'id': '2', 'name': '只跑股價預測', 'icon': '📈'},
        {'id': '3', 'name': '執行內層 walk-forward（訓練期：2015–2022）', 'icon': '🔄'},
        {'id': '4', 'name': '生成 candidate pool（由內層結果套門檻）', 'icon': '🎯'},
        {'id': '5', 'name': '執行外層回測（2023–2024）', 'icon': '🏆'},
        {'id': '6', 'name': '顯示/編輯 config 檔案', 'icon': '⚙️'},
        {'id': '7', 'name': '匯出報表（HTML / CSV）', 'icon': '📋'},
        {'id': '8', 'name': '模型管理（列出 / 匯出 / 刪除）', 'icon': '🗂️'},
    ],
    
    'default_params': {
        'train_window': 48,
        'test_window': 12,
        'stride': 12,
        'include_delisted': False,
    }
}

def get_config(section: str = None) -> Dict[str, Any]:
    """獲取配置"""
    configs = {
        'database': DATABASE_CONFIG,
        'walkforward': WALKFORWARD_CONFIG,
        'feature': FEATURE_CONFIG,
        'model': MODEL_CONFIG,
        'selection': SELECTION_CONFIG,
        'trading': TRADING_CONFIG,
        'backtest': BACKTEST_CONFIG,
        'output': OUTPUT_CONFIG,
        'cli': CLI_CONFIG,
    }
    
    if section:
        return configs.get(section, {})
    return configs

def update_config(section: str, updates: Dict[str, Any]) -> bool:
    """更新配置"""
    try:
        # 這裡可以實作配置更新邏輯
        # 暫時返回True表示成功
        return True
    except Exception:
        return False
