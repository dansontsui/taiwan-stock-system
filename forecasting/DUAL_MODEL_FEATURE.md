# 雙模型預測功能說明

## 🎯 功能概述

已成功實現選單中單次預測功能的雙模型顯示，現在會同時展示 XGBoost 和 Prophet 兩種模型的預測結果，並清楚標註哪個是回測最佳模型。

## ✨ 新功能特色

### 1. 雙模型同時預測
- **XGBoost 模型**：機器學習回歸模型
- **Prophet 模型**：Facebook 時間序列預測模型
- 兩個模型獨立運行，各自產生完整的預測結果

### 2. 智能最佳模型標註
- 🏆 自動標註回測最佳模型（基於之前的回測結果）
- 若尚未進行回測，會提示建議先執行回測分析
- 最佳模型會在標題後顯示 `🏆 (回測最佳)` 標記

### 3. 獨立檔案輸出
- **CSV 檔案**：`{stock_id}_{model_name}_forecast.csv`
- **JSON 檔案**：`{stock_id}_{model_name}_forecast.json`
- **圖表檔案**：`history_vs_forecast_{model_name}.png`
- 避免檔案覆蓋，每個模型都有獨立的輸出檔案

### 4. 詳細比較摘要
- 顯示兩個模型的完整預測結果
- 基準情境預測值直接比較
- 清楚標示哪個是回測最佳模型的預測值

## 📊 輸出範例

```
============================================================
📊 雙模型預測結果比較
============================================================

📈 XGBoost 模型
----------------------------------------
📁 CSV檔案: outputs\forecasts\2385_XGBoost_forecast.csv
📁 JSON檔案: outputs\forecasts\2385_XGBoost_forecast.json
📈 圖表檔案: outputs\forecasts\history_vs_forecast_XGBoost.png
📋 預測摘要:
   2025-07 conservative: 7,982,526,928 (異常: 0)
   2025-07 baseline: 8,343,054,336 (異常: 0)
   2025-07 optimistic: 8,703,581,744 (異常: 0)

📈 Prophet 模型 🏆 (回測最佳)
----------------------------------------
📁 CSV檔案: outputs\forecasts\2385_Prophet_forecast.csv
📁 JSON檔案: outputs\forecasts\2385_Prophet_forecast.json
📈 圖表檔案: outputs\forecasts\history_vs_forecast_Prophet.png
📋 預測摘要:
   2025-07 conservative: 7,589,234,488 (異常: 0)
   2025-07 baseline: 7,949,761,896 (異常: 0)
   2025-07 optimistic: 8,310,289,303 (異常: 0)

============================================================
📊 模型比較摘要
============================================================
🏆 回測最佳模型: Prophet

📊 基準情境預測值比較:
   XGBoost: 8,343,054,336
   Prophet: 7,949,761,896 🏆
```

## 🔧 技術實現

### 新增函數
- `run_forecast_with_specific_model(stock_id, model_name)`: 使用指定模型進行預測
- 修改 `handle_single_forecast()`: 同時調用兩個模型並格式化輸出

### 視覺化增強
- 所有圖表函數新增 `title_suffix` 參數
- 檔案名稱自動加入模型名稱避免覆蓋
- 圖表標題包含模型識別資訊

### 相容性保證
- 完全向後相容，不影響現有功能
- 支援 Mac/Windows 跨平台執行
- UTF-8-SIG 編碼避免中文顯示問題

## 🚀 使用方式

1. 啟動選單：`python forecasting/menu.py`
2. 選擇功能：`1) 單次預測`
3. 輸入股票代碼：例如 `2385`
4. 系統會自動執行雙模型預測並顯示比較結果

## 📁 輸出檔案結構

```
outputs/forecasts/
├── {stock_id}_XGBoost_forecast.csv
├── {stock_id}_XGBoost_forecast.json
├── {stock_id}_Prophet_forecast.csv
├── {stock_id}_Prophet_forecast.json
├── history_vs_forecast_XGBoost.png
├── history_vs_forecast_Prophet.png
├── errors_XGBoost.png
├── errors_Prophet.png
├── scenarios_XGBoost.png
└── scenarios_Prophet.png
```

## ✅ 測試驗證

- ✅ 雙模型獨立預測功能
- ✅ 最佳模型自動識別
- ✅ 檔案獨立輸出不覆蓋
- ✅ CSV/JSON 格式正確
- ✅ 中文顯示無編碼問題
- ✅ 跨平台相容性

## 🎯 後續建議

1. 可考慮加入 LSTM 模型到比較中
2. 可增加模型準確度指標的即時比較
3. 可加入歷史預測準確度統計
4. 可提供模型選擇建議功能

---

**更新日期**: 2025-08-14  
**功能狀態**: ✅ 已完成並測試通過
