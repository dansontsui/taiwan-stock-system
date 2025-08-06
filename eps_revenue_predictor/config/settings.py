# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - System Configuration
系統配置檔案
"""

import os
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
# 修正資料庫路徑 - 指向正確的taiwan_stock.db位置
DB_PATH = PROJECT_ROOT.parent / "data" / "taiwan_stock.db"

# 資料庫配置
DATABASE_CONFIG = {
    'path': DB_PATH,
    'timeout': 30,
    'check_same_thread': False
}

# 預測配置
PREDICTION_CONFIG = {
    # 測試股票
    'test_stock': '2385',  # 群光電子
    'test_stock_name': '群光電子',
    
    # 預測參數
    'revenue_lookback_months': 12,  # 營收回看月數
    'eps_lookback_quarters': 8,     # EPS回看季數
    'margin_lookback_quarters': 8,  # 利潤率回看季數
    
    # 預測方法權重
    'formula_weight': 0.8,          # 財務公式權重 80%
    'ai_adjustment_weight': 0.2,    # AI調整權重 20%
    
    # 信心水準閾值
    'high_confidence_threshold': 0.8,
    'medium_confidence_threshold': 0.6,
    
    # 預測範圍限制
    'max_growth_rate': 2.0,         # 最大成長率 200%
    'min_growth_rate': -0.8,        # 最小成長率 -80%
}

# 財務公式配置
FORMULA_CONFIG = {
    # 營收預測方法權重
    'revenue_methods': {
        'trend_extrapolation': 0.4,    # 趨勢外推法
        'moving_average': 0.3,         # 移動平均法
        'yoy_trend': 0.3              # 年增率趨勢法
    },
    
    # EPS預測組件
    'eps_components': {
        'revenue_weight': 0.5,         # 營收影響權重
        'margin_weight': 0.3,          # 利潤率影響權重
        'efficiency_weight': 0.2       # 營運效率影響權重
    },
    
    # 季節調整參數
    'seasonal_adjustment': True,
    'seasonal_window': 24,             # 季節調整視窗(月)
}

# AI模型配置
AI_MODEL_CONFIG = {
    'model_type': 'lightgbm',
    'features': [
        'revenue_volatility',          # 營收波動性
        'margin_trend',               # 利潤率趨勢
        'opex_efficiency',            # 營業費用效率
        'industry_momentum',          # 產業動能
        'market_sentiment'            # 市場情緒
    ],
    'adjustment_range': 0.2,          # 調整範圍 ±20%
    'training_window': 36,            # 訓練視窗(月)
    'retrain_frequency': 6            # 重新訓練頻率(月)
}

# 回測配置
BACKTEST_CONFIG = {
    'start_date': '2020-01-01',
    'end_date': '2024-12-31',
    'prediction_frequency': 'quarterly',  # 預測頻率
    'validation_method': 'rolling_window',
    'accuracy_tolerance': 0.1,            # 準確率容忍度 ±10%
    
    # 績效指標
    'metrics': [
        'accuracy',                       # 準確率
        'mae',                           # 平均絕對誤差
        'rmse',                          # 均方根誤差
        'direction_accuracy'             # 方向準確率
    ]
}

# 日誌配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': PROJECT_ROOT / 'logs' / 'predictor.log',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'encoding': 'ascii'  # 改為ASCII避免編碼問題
}

# 報告配置
REPORT_CONFIG = {
    'output_dir': PROJECT_ROOT / 'reports',
    'formats': ['html', 'csv'],
    'include_charts': True,
    'chart_style': 'seaborn',
    'encoding': 'utf-8'
}

# 確保目錄存在
def ensure_directories():
    """確保必要的目錄存在"""
    directories = [
        PROJECT_ROOT / 'logs',
        PROJECT_ROOT / 'reports',
        PROJECT_ROOT / 'models',
        PROJECT_ROOT / 'data'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("Configuration loaded successfully")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Database path: {DATABASE_CONFIG['path']}")
    print(f"Test stock: {PREDICTION_CONFIG['test_stock']} ({PREDICTION_CONFIG['test_stock_name']})")
