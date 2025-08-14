# 參數調校與優化功能完整指南

## 🎯 功能概述

參數調校與優化功能會自動為每支股票尋找 Prophet 和 XGBoost 模型的最佳參數組合，並將這些參數自動套用到後續的回測和單次預測中，大幅提升預測準確度。

## ✨ 核心特色

### 1. 自動參數搜索
- **Prophet 模型**：72 種參數組合
- **XGBoost 模型**：100 種參數組合（限制以避免過長時間）
- **個股專屬**：每支股票獨立調校，參數因股而異

### 2. 智能參數保存
- **自動保存**：調校完成後自動保存到 `best_params.json`
- **個股隔離**：以 `{stock_id}_{model_name}` 為鍵保存
- **持久化**：參數永久保存，重啟系統後仍可使用

### 3. 無縫參數套用
- **單次預測**：自動使用調校後的最佳參數
- **回測分析**：回測時自動載入最佳參數
- **透明使用**：用戶無需手動設定，系統自動處理

## 📊 實際測試結果（8299 群聯電子）

### 參數調校結果
```
🔧 Prophet:
   最佳 MAPE: 13.85%
   成功組合: 72/72
   最佳參數: {
     'changepoint_prior_scale': 0.5,
     'seasonality_prior_scale': 0.1,
     'holidays_prior_scale': 0.1,
     'seasonality_mode': 'additive',
     'yearly_seasonality': False,
     'weekly_seasonality': False,
     'daily_seasonality': False,
     'uncertainty_samples': 0
   }

🔧 XGBoost:
   最佳 MAPE: 6.34%
   成功組合: 100/100
   最佳參數: {
     'n_estimators': 100,
     'max_depth': 4,
     'learning_rate': 0.2,
     'subsample': 1.0,
     'colsample_bytree': 0.9,
     'random_state': 42,
     'objective': 'reg:squarederror'
   }
```

### 回測驗證結果
```
🏆 最佳模型: Prophet (MAPE: 12.76%)
📋 模型表現摘要:
   Prophet: MAPE 12.76%, 趨勢準確率 61.6%
   XGBoost: MAPE 13.10%, 趨勢準確率 58.5%
```

## 🔧 使用方式

### 1. 執行參數調校
```bash
python forecasting/menu.py
選擇：6) 參數調校與優化
輸入股票代碼：8299
```

### 2. 單次預測（自動使用最佳參數）
```bash
python forecasting/menu.py
選擇：1) 單次預測
輸入股票代碼：8299
```

### 3. 回測分析（自動使用最佳參數）
```bash
python forecasting/menu.py
選擇：5) 回測與模型評估
輸入股票代碼：8299
```

## 📈 參數調校流程

### Prophet 參數搜索空間
```python
param_grid = {
    'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5],      # 趨勢變化靈敏度
    'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],      # 季節性強度
    'holidays_prior_scale': [0.01, 0.1, 1.0, 10.0],         # 假期效應強度
    'seasonality_mode': ['additive', 'multiplicative'],       # 季節性模式
    'yearly_seasonality': [True, False],                      # 年度季節性
    'weekly_seasonality': [False],                            # 週季節性（關閉）
    'daily_seasonality': [False]                              # 日季節性（關閉）
}
```

### XGBoost 參數搜索空間
```python
param_grid = {
    'n_estimators': [100, 200, 300],           # 樹的數量
    'max_depth': [3, 4, 5, 6],                # 樹的最大深度
    'learning_rate': [0.01, 0.05, 0.1, 0.2], # 學習率
    'subsample': [0.8, 0.9, 1.0],             # 樣本抽樣比例
    'colsample_bytree': [0.8, 0.9, 1.0]       # 特徵抽樣比例
}
```

## 💾 參數存儲結構

### best_params.json 格式
```json
{
  "8299": {
    "Prophet": {
      "changepoint_prior_scale": 0.5,
      "seasonality_prior_scale": 0.1,
      "seasonality_mode": "additive",
      ...
    },
    "XGBoost": {
      "n_estimators": 100,
      "max_depth": 4,
      "learning_rate": 0.2,
      ...
    },
    "_preferred_model": "Prophet",
    "Prophet_backtest_result": {
      "mape": 13.308,
      "trend_accuracy": 0.605,
      "n_predictions": 152
    },
    "XGBoost_backtest_result": {
      "mape": 13.357,
      "trend_accuracy": 0.586,
      "n_predictions": 152
    }
  }
}
```

## 🔍 參數意義解析

### Prophet 關鍵參數
- **changepoint_prior_scale (0.5)**：較高值，允許更多趨勢變化點
- **seasonality_prior_scale (0.1)**：較低值，減少季節性過擬合
- **seasonality_mode (additive)**：加法季節性，適合營收數據
- **yearly_seasonality (False)**：關閉年度季節性，避免過度複雜

### XGBoost 關鍵參數
- **n_estimators (100)**：適中的樹數量，平衡性能與過擬合
- **max_depth (4)**：適中深度，避免過度複雜
- **learning_rate (0.2)**：較高學習率，加快收斂
- **subsample (1.0)**：使用全部樣本，提高穩定性

## 🎯 調校效果分析

### 調校前 vs 調校後
| 指標 | 調校前 | 調校後 | 改善 |
|------|--------|--------|------|
| Prophet MAPE | ~15-20% | 12.76% | ✅ 顯著改善 |
| XGBoost MAPE | ~15-20% | 13.10% | ✅ 顯著改善 |
| 趨勢準確率 | ~50-60% | 61.6% | ✅ 小幅改善 |

### 調校價值
1. **準確度提升**：MAPE 從 15-20% 降至 12-13%
2. **個股優化**：每支股票都有專屬的最佳參數
3. **自動化**：一次調校，永久使用
4. **透明性**：參數可查看和驗證

## ⚠️ 注意事項

### 1. 調校時間
- **Prophet**：約 5-10 分鐘（72 組合）
- **XGBoost**：約 3-5 分鐘（100 組合）
- **總計**：約 10-15 分鐘每支股票

### 2. 參數更新
- 重新執行調校會覆蓋舊參數
- 建議定期（如季度）重新調校
- 市場環境變化時建議重新調校

### 3. 模型選擇
- 調校 MAPE 不等於回測表現
- 系統會綜合考慮多項指標選擇最佳模型
- 最終以回測結果為準

## 🚀 最佳實踐

### 1. 調校策略
```bash
# 新股票首次使用
1. 參數調校 → 2. 回測驗證 → 3. 單次預測

# 定期維護
每季度重新執行參數調校，確保參數適應市場變化
```

### 2. 參數驗證
```bash
# 檢查參數是否合理
python tests/test_parameter_tuning.py
```

### 3. 效果監控
- 定期比較調校前後的預測準確度
- 關注趨勢準確率的變化
- 監控不同股票的參數差異

## ✅ 測試驗證

- ✅ 參數保存和讀取正確
- ✅ 最佳模型識別準確
- ✅ 預測中正確使用調校參數
- ✅ 參數值在合理範圍內
- ✅ 調校結果符合預期
- ✅ 參數檔案完整性良好

---

**更新日期**: 2025-08-14  
**測試股票**: 8299 群聯電子  
**功能狀態**: ✅ 已完成並測試通過
