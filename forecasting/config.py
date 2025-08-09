from __future__ import annotations
import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Config:
    # 預設資料庫路徑（相對於專案根目錄）
    db_path: str = os.getenv("TS_DB_PATH", os.path.join("data", "taiwan_stock.db"))
    # 輸出資料夾
    output_dir: str = os.getenv("TS_OUTPUT_DIR", os.path.join("outputs", "forecasts"))
    # 預測視窗
    forecast_horizon_months: int = 1
    # 訓練最少年限
    min_years_history: int = 10
    # 交叉驗證回溯年數（用於報告/評估）
    backtest_years: int = 1
    # 隨機種子
    random_seed: int = 42
    # 模型啟用旗標（為提升穩定性，預設僅啟用 XGBoost）
    enable_prophet: bool = _env_bool("TS_ENABLE_PROPHET", True)
    enable_lstm: bool = _env_bool("TS_ENABLE_LSTM", False)
    enable_xgboost: bool = _env_bool("TS_ENABLE_XGBOOST", True)
    # Prophet 穩定性設定
    prophet_stable_mode: bool = _env_bool("TS_PROPHET_STABLE", True)


cfg = Config()


def ensure_dirs():
    os.makedirs(cfg.output_dir, exist_ok=True)


def setup_prophet_logging():
    """設定 Prophet 日誌等級，減少 cmdstanpy 錯誤訊息"""
    if cfg.prophet_stable_mode:
        import logging
        logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
        logging.getLogger('prophet').setLevel(logging.WARNING)

