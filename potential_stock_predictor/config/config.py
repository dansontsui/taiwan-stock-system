#!/usr/bin/env python3
"""
潛力股預測系統配置檔案
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
MAIN_PROJECT_ROOT = PROJECT_ROOT.parent

# 資料庫配置
DATABASE_CONFIG = {
    'path': MAIN_PROJECT_ROOT / 'data' / 'taiwan_stock.db',
    'timeout': 30
}

# 資料路徑配置
DATA_PATHS = {
    'raw_data': PROJECT_ROOT / 'data' / 'raw',
    'processed_data': PROJECT_ROOT / 'data' / 'processed',
    'features': PROJECT_ROOT / 'data' / 'features',
    'predictions': PROJECT_ROOT / 'data' / 'predictions'
}

# 模型配置
MODEL_CONFIG = {
    'models_dir': PROJECT_ROOT / 'models',
    'model_types': ['lightgbm', 'xgboost', 'random_forest', 'logistic_regression'],
    'default_model': 'lightgbm',
    'model_version': 'v1.0'
}

# 特徵工程配置
FEATURE_CONFIG = {
    # 目標變數定義
    'target_definition': {
        'prediction_days': 20,  # 預測未來20個交易日
        'target_return': 0.05,  # 目標漲幅5%
        'min_trading_days': 15  # 最少需要15個交易日的資料
    },
    
    # 月營收特徵
    'revenue_features': {
        'lookback_months': 12,  # 回看12個月
        'growth_periods': [1, 3, 6, 12],  # 計算1,3,6,12月成長率
        'rolling_windows': [3, 6, 12]  # 滾動平均視窗
    },
    
    # 財務比率特徵
    'financial_features': {
        'lookback_quarters': 8,  # 回看8季
        'key_ratios': [
            'ROE', 'ROA', 'gross_margin', 'operating_margin',
            'net_margin', 'debt_ratio', 'current_ratio',
            'quick_ratio', 'inventory_turnover', 'receivables_turnover'
        ]
    },
    
    # 技術指標特徵
    'technical_features': {
        'price_windows': [5, 10, 20, 60],  # 價格移動平均視窗
        'volume_windows': [5, 10, 20],     # 成交量移動平均視窗
        'volatility_window': 20,           # 波動率計算視窗
        'rsi_window': 14,                  # RSI計算視窗
        'momentum_windows': [5, 10, 20]    # 動量指標視窗
    }
}

# 模型訓練配置
TRAINING_CONFIG = {
    # 資料分割
    'train_test_split': {
        'test_size': 0.2,
        'validation_size': 0.2,
        'time_series_split': True,  # 使用時序分割
        'min_train_samples': 1000
    },
    
    # 交叉驗證
    'cross_validation': {
        'cv_folds': 5,
        'time_series_cv': True,
        'gap_days': 30  # 訓練和驗證資料間的間隔天數
    },
    
    # 超參數調校
    'hyperparameter_tuning': {
        'method': 'optuna',  # 'optuna' or 'grid_search'
        'n_trials': 100,
        'timeout': 3600,  # 1小時
        'n_jobs': -1
    }
}

# 模型評估配置
EVALUATION_CONFIG = {
    'metrics': [
        'accuracy', 'precision', 'recall', 'f1_score',
        'roc_auc', 'precision_recall_auc'
    ],
    'threshold_optimization': True,
    'feature_importance': True,
    'shap_analysis': True
}

# 預測配置
PREDICTION_CONFIG = {
    'batch_size': 100,
    'confidence_threshold': 0.6,
    'top_k_stocks': 50,
    'exclude_patterns': ['00'],  # 排除00開頭的股票
    'min_market_cap': 1e9,  # 最小市值10億
    'min_avg_volume': 1000  # 最小平均成交量1000張
}

# 日誌配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': PROJECT_ROOT / 'logs' / 'predictor.log',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# 確保目錄存在
def ensure_directories():
    """確保所有必要的目錄存在"""
    for path in DATA_PATHS.values():
        path.mkdir(parents=True, exist_ok=True)
    
    MODEL_CONFIG['models_dir'].mkdir(parents=True, exist_ok=True)
    LOGGING_CONFIG['file_path'].parent.mkdir(parents=True, exist_ok=True)

# 獲取日期範圍
def get_date_ranges():
    """獲取訓練和預測的日期範圍"""
    end_date = datetime.now().date()
    
    # 訓練資料：過去5年
    train_start = end_date - timedelta(days=5*365)
    
    # 預測資料：最近3個月
    predict_start = end_date - timedelta(days=90)
    
    return {
        'train_start': train_start.isoformat(),
        'train_end': end_date.isoformat(),
        'predict_start': predict_start.isoformat(),
        'predict_end': end_date.isoformat()
    }

# 模型超參數配置
HYPERPARAMETERS = {
    'lightgbm': {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': [31, 50, 100],
        'learning_rate': [0.01, 0.05, 0.1],
        'feature_fraction': [0.8, 0.9, 1.0],
        'bagging_fraction': [0.8, 0.9, 1.0],
        'bagging_freq': [5],
        'min_child_samples': [20, 50, 100],
        'verbosity': -1
    },
    
    'xgboost': {
        'objective': 'binary:logistic',
        'eval_metric': 'logloss',
        'max_depth': [3, 6, 9],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [100, 200, 300],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0],
        'random_state': 42
    },
    
    'random_forest': {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None],
        'random_state': 42
    },
    
    'logistic_regression': {
        'C': [0.1, 1.0, 10.0],
        'penalty': ['l1', 'l2'],
        'solver': ['liblinear', 'saga'],
        'max_iter': [1000],
        'random_state': 42
    }
}

if __name__ == "__main__":
    # 初始化目錄
    ensure_directories()
    print("✅ 潛力股預測系統配置初始化完成")
    print(f"📁 專案根目錄: {PROJECT_ROOT}")
    print(f"🗄️ 資料庫路徑: {DATABASE_CONFIG['path']}")
    print(f"📊 模型目錄: {MODEL_CONFIG['models_dir']}")
