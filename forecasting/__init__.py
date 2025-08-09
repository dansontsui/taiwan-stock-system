"""
台灣股市營收預測系統 - forecasting 套件初始化
說明：
- 提供模組化的介面來進行資料讀取、特徵工程、模型訓練、情境預測與結果輸出
- 為了跨平台（Mac/Windows）相容，請務必以 UTF-8 編碼開啟/寫入檔案（建議 UTF-8-SIG）
"""
from __future__ import annotations

__all__ = [
    "config",
    "db",
    "features",
    "predictor",
    "anomaly",
    "scenarios",
    "visualization",
]

