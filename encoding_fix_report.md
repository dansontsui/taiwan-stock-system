# 編碼修復報告

## 問題描述
用戶反映 backtesting.log 檔案在 Windows 系統上顯示為亂碼，需要修復編碼問題以確保 Windows 和 Mac 系統的兼容性。

## 修復內容

### 1. 日誌系統編碼修復

#### 修復檔案：`potential_stock_predictor/backtesting_system.py`
- **修復前**：使用預設編碼（UTF-8）
```python
logging.FileHandler('backtesting.log')
```

- **修復後**：使用 ASCII 編碼並設定錯誤處理
```python
logging.FileHandler('backtesting.log', encoding='ascii', errors='replace')
```

#### 修復檔案：`potential_stock_predictor/src/utils/logger.py`
- **修復前**：UTF-8 編碼
```python
encoding='utf-8'
```

- **修復後**：ASCII 編碼並設定錯誤處理
```python
encoding='ascii',
errors='replace'  # 將無法編碼的字符替換為 '?'
```

### 2. JSON 報告檔案編碼修復

#### 修復檔案：`potential_stock_predictor/src/utils/helpers.py`
- **save_json 函數修復**：
  - 修復前：`encoding='utf-8'`, `ensure_ascii=False`
  - 修復後：`encoding='ascii'`, `ensure_ascii=True`, `errors='replace'`

- **load_json 函數增強**：
  - 新增多編碼支援：嘗試 ascii, utf-8, cp1252, big5
  - 增加錯誤處理機制

#### 修復檔案：`potential_stock_predictor/backtesting_system.py`
- **回測報告保存**：
  - 修復前：`encoding='utf-8'`, `ensure_ascii=False`
  - 修復後：`encoding='ascii'`, `ensure_ascii=True`, `errors='replace'`

#### 修復檔案：`potential_stock_predictor/simple_train.py`
- **模型資訊保存**：
  - 修復前：`encoding='utf-8'`, `ensure_ascii=False`
  - 修復後：`encoding='ascii'`, `ensure_ascii=True`, `errors='replace'`

## 測試結果

### 編碼測試
執行編碼測試腳本，結果顯示：
- ✅ 日誌檔案已創建
- ✅ 檔案大小：302 bytes
- ✅ 非 ASCII 字節數：0
- ✅ 純 ASCII 檔案，跨平台兼容性良好
- ✅ 中文字符正確替換為 `?`，避免編碼問題

### 回測系統測試
- ✅ 回測系統正常啟動
- ✅ 日誌配置正確應用
- ✅ 無編碼錯誤

### JSON 報告檢查
檢查現有的 JSON 報告檔案：
- ✅ `backtest_report_20250801_154006.json` - 純 ASCII 格式
- ✅ 檔案可正常讀取和解析

## 修復效果

### 優點
1. **跨平台兼容性**：ASCII 編碼確保在 Windows 和 Mac 上都能正常顯示
2. **無亂碼問題**：中文字符被安全替換為 `?`，避免顯示亂碼
3. **向後兼容**：load_json 函數支援多種編碼，可讀取舊檔案
4. **錯誤處理**：使用 `errors='replace'` 確保不會因編碼問題導致程式崩潰

### 注意事項
1. **中文字符顯示**：中文字符會顯示為 `?`，這是為了確保跨平台兼容性的權衡
2. **檔案大小**：ASCII 編碼可能會略微增加檔案大小（因為中文字符被替換）
3. **可讀性**：對於需要中文顯示的場景，建議使用終端機輸出而非日誌檔案

## 建議

### 短期建議
1. 測試修復後的系統，確認日誌檔案在 Windows 上正常顯示
2. 如需要中文顯示，可考慮在終端機輸出中保留中文，僅在檔案輸出中使用 ASCII

### 長期建議
1. 考慮實作雙語日誌系統：終端機顯示中文，檔案保存英文
2. 建立編碼標準文件，確保未來開發遵循相同標準
3. 定期測試跨平台兼容性

## 總結

編碼修復已完成，主要變更包括：
- 日誌系統改用 ASCII 編碼
- JSON 報告檔案改用 ASCII 編碼
- 增加錯誤處理機制
- 保持向後兼容性

修復後的系統應該能夠在 Windows 和 Mac 系統上正常顯示日誌檔案，不再出現亂碼問題。
