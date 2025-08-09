# 📊 台灣股市營收預測系統 - 專案狀態記錄

## 🎯 專案概述

這是一個完整的台灣股市營收預測系統，整合多種 AI/ML 模型、回測驗證、參數優化與互動式視覺化功能。

### 核心模組位置
- **主要模組**：`forecasting/` 目錄
- **測試檔案**：`tests/test_forecasting.py`, `tests/test_improvements.py`
- **輸出目錄**：`outputs/forecasts/`
- **啟動腳本**：`run_menu.py`

## ✅ 已完成功能

### 1. 核心預測系統
- **AI/ML 模型**：Prophet、XGBoost、LSTM
- **個股專屬參數**：每支股票獨立訓練與優化
- **自動模型選擇**：基於 MAPE 選擇最佳模型
- **異常檢測**：智能識別與調整異常預測值

### 2. 互動式選單系統 (`forecasting/menu.py`)
```
📊 基本功能 (1-4)：
1. ✅ 單次預測（輸出CSV/JSON與圖表）
2. ✅ 每日滾動檢查模式
3. ✅ 查詢資料庫最新月份
4. ✅ 檢視資料庫表格結構

🔧 進階功能 (5-8)：
5. ✅ 回測與模型評估
6. ✅ 參數調校與優化
7. ✅ 多變量特徵整合
8. ✅ 批量預測多檔股票

⚙️ 系統設定 (9-10)：
9. ✅ 模型啟用設定查看
10. ✅ 系統狀態檢查
```

### 3. 回測與驗證系統 (`forecasting/backtest.py`)
- **時間滾動視窗**：支援自訂訓練視窗（預設36個月）
- **詳細歷史記錄**：每期預測 vs 實際對比
- **CSV 自動匯出**：`{stock_id}_{model_name}_backtest_history.csv`
- **模型表現指標**：MAPE、RMSE、趨勢準確率

### 4. 參數優化系統 (`forecasting/tuning.py`)
- **自動化超參數搜尋**：Prophet、XGBoost、LSTM
- **交叉驗證**：時間序列分割驗證
- **參數儲存**：`outputs/forecasts/best_params.json`
- **個股專屬**：以 `{stock_id, model_name}` 為鍵儲存

### 5. 高互動視覺化 (`forecasting/interactive.py`)
- **Plotly 折線圖**：可縮放、懸停查看數值
- **分頁展示**：所有模型的詳細分析與比較
- **英文圖表**：避免中文字體問題
- **HTML 輸出**：`{stock_id}_interactive_backtest.html`

### 6. 智能預測邏輯修正
- **優先使用最佳模型**：單次預測優先採用回測/調校保存的最佳模型
- **參數自動載入**：使用個股專屬的最佳參數
- **回退機制**：若指定模型失敗，自動回退到自動選模

## 📁 檔案結構

```
forecasting/
├── menu.py              # 互動式選單（主入口）
├── cli.py               # 命令列介面
├── predictor.py         # 模型預測核心
├── backtest.py          # 回測驗證系統
├── tuning.py            # 參數調校系統
├── interactive.py       # 高互動 HTML 生成
├── param_store.py       # 參數儲存管理
├── config.py            # 配置管理
├── db.py               # 資料庫操作
├── features.py         # 特徵工程
├── anomaly.py          # 異常檢測
├── scenarios.py        # 情境預測
├── visualization.py    # 視覺化
├── multivariate.py     # 多變量特徵
└── SYSTEM_ARCHITECTURE.md  # 系統架構文件
```

## 🎯 系統架構特色

### AI/ML 與財務邏輯佔比
- **AI/ML 模型**：≈ 85%（主要預測來源）
- **財務邏輯與規則**：≈ 15%（異常檢測與合理性約束）

### 個股模型架構
- 每支股票獨立訓練與參數優化
- 參數以 `{stock_id, model_name}` 為鍵儲存
- 單次預測優先使用回測/調校保存的最佳模型

### 特徵工程
- **時間特徵**：滯後值（lag1/3/6/12）、移動平均（ma3/6/12）
- **季節特徵**：月份 one-hot 編碼
- **多變量特徵**：財務報表、比率指標（可選）

## 📊 實際測試結果

### 2385 群創光電測試
- **參數優化**：Prophet 256組參數，最佳 MAPE 5.03%
- **回測驗證**：Prophet MAPE 10.14%，XGBoost 17.77%
- **最佳模型**：Prophet（已保存至 best_params.json）
- **輸出檔案**：完整 CSV、PNG、HTML 生成

### 2330 台積電測試
- **回測結果**：Prophet MAPE 12.09%，XGBoost 18.64%
- **趨勢準確率**：Prophet 72.9%，XGBoost 54.2%
- **目標達成**：❌ MAPE > 8%，需進一步優化

## 🚀 啟動方式

### 1. 互動式選單（推薦）
```bash
cd forecasting
python menu.py
```

### 2. 命令列使用
```bash
# 單次預測
python -m forecasting.cli 2330

# 每日滾動檢查
python -m forecasting.cli 2330 --roll
```

### 3. 完整預測流程
```bash
# 1. 參數調校
選單 6 → 輸入股票代號

# 2. 回測驗證（會保存最佳模型）
選單 5 → 輸入股票代號 → 訓練視窗 36

# 3. 單次預測（使用最佳模型）
選單 1 → 輸入股票代號
```

## 🧪 測試狀態

### 單元測試
```bash
# 執行所有測試
pytest -q

# 特定測試
pytest tests/test_forecasting.py
pytest tests/test_improvements.py
```

### 測試覆蓋
- ✅ 回測歷史 CSV 匯出
- ✅ 參數儲存與載入
- ✅ 系統架構文件存在
- ✅ 端到端預測流程

## 📈 輸出檔案範例

```
outputs/forecasts/
├── 2385_forecast.csv                    # 預測結果
├── 2385_forecast.json                   # 預測結果 JSON
├── 2385_Prophet_backtest_history.csv    # Prophet 回測歷史
├── 2385_XGBoost_backtest_history.csv    # XGBoost 回測歷史
├── 2385_Prophet_backtest_history.png    # 回測圖表
├── 2385_interactive_backtest.html       # 高互動分頁版 HTML
├── best_params.json                     # 最佳參數與模型
└── *.png                               # 各種圖表
```

## 🎯 模型表現目標

| 指標 | 目標值 | 當前最佳 | 狀態 |
|------|--------|----------|------|
| MAPE | ≤ 8% | 10.14% (2385) | ❌ 需改進 |
| 趨勢準確率 | ≥ 80% | 72.9% (2385) | ❌ 需改進 |
| 回測期數 | ≥ 24 期 | 152 期 | ✅ 達成 |

## 🔧 環境變數

```bash
export TS_DB_PATH="data/taiwan_stock.db"
export TS_ENABLE_PROPHET=1
export TS_ENABLE_LSTM=1
export TS_ENABLE_XGBOOST=1
export TS_OUTPUT_DIR="outputs/forecasts"
```

## 📝 重要改進記錄

### 2025-08-09 重大更新
1. **個股模型架構**：確認並實現每支股票獨立參數優化
2. **回測歷史 CSV 匯出**：自動匯出詳細歷史記錄
3. **自動化參數優化**：整合到選單，自動保存最佳參數
4. **高互動 HTML**：Plotly 折線圖 + 分頁展示
5. **智能預測邏輯**：單次預測優先使用最佳模型

### 關鍵修正
- **邏輯矛盾修正**：單次預測現在會使用回測確定的最佳模型
- **圖表英文化**：避免中文字體問題
- **檔名防覆蓋**：加入股票代號與模型名稱

## 🚀 後續優化方向

1. **提升 MAPE**：目前 10-12%，目標 ≤ 8%
2. **參數搜尋空間擴大**：更多參數組合測試
3. **多變量特徵強化**：整合更多財務指標
4. **趨勢準確率提升**：目標 ≥ 80%
5. **異常檢測優化**：改善早期高誤差期間

---

**最後更新**：2025-08-09  
**系統版本**：v2.0  
**測試狀態**：✅ 全部通過
