#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股歷史股價系統配置文件
"""

import os
from datetime import datetime, timedelta

class Config:
    """基礎配置"""
    
    # 專案根目錄
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 資料庫配置
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'taiwan_stock.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # FinMind API 配置
    FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
    FINMIND_API_TOKEN = os.getenv('FINMIND_API_TOKEN', '')  # 可選，提高請求限制
    
    # 資料收集配置
    DATA_START_DATE = "2015-01-01"  # 10年歷史資料
    DATA_END_DATE = datetime.now().strftime("%Y-%m-%d")
    
    # 股票範圍配置
    INCLUDE_TWSE = True  # 包含上市股票
    INCLUDE_TPEX = True  # 包含上櫃股票
    INCLUDE_ETF = True   # 包含ETF
    
    # 快取配置
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300  # 5分鐘
    
    # 日誌配置
    LOG_LEVEL = "INFO"
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'taiwan_stock.log')
    
    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'taiwan-stock-system-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API 配置
    API_RATE_LIMIT = "300 per hour"  # FinMind 免費版限制
    
    # 資料更新配置
    AUTO_UPDATE = True
    UPDATE_TIME = "18:00"  # 每日更新時間
    
    # 技術指標預設參數
    TECHNICAL_INDICATORS = {
        'MA': [5, 10, 20, 60],  # 移動平均週期
        'EMA': [12, 26],        # 指數移動平均
        'RSI': [14],            # RSI週期
        'MACD': [12, 26, 9],    # MACD參數
        'BOLLINGER': [20, 2],   # 布林通道參數
        'KD': [9, 3, 3],        # KD指標參數
    }
    
    # 圖表配置
    CHART_CONFIG = {
        'default_period': 252,  # 預設顯示一年資料
        'candlestick_colors': {
            'up': '#00ff00',
            'down': '#ff0000'
        },
        'volume_colors': {
            'up': '#90EE90',
            'down': '#FFB6C1'
        }
    }

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    LOG_LEVEL = "WARNING"

    # 生產環境使用更安全的密鑰
    SECRET_KEY = os.getenv('SECRET_KEY', 'production-secret-key-change-me')

class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    DATABASE_PATH = ':memory:'  # 使用記憶體資料庫
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
