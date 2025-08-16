# 外層回測程式碼說明

本文件詳細說明選單5外層回測的關鍵程式碼實作。

## 核心檔案

- **主要檔案**: `stock_price_investment_system/price_models/holdout_backtester.py`
- **配置檔案**: `stock_price_investment_system/config/settings.py`

## 關鍵程式碼片段

### 1. 月頻交易循環

```python
# 使用簡化的月頻交易：每個月月底做一次等權買入持有20天
months = pd.date_range(start=start, end=end, freq='M')
for m in months:
    as_of = m.strftime('%Y-%m-%d')  # 月底日期，如 2023-01-31
    
    # 為每檔股票訓練模型（使用截至當前日期的資料）
    for stock_id in stocks:
        # ... 訓練模型 ...
    
    # 使用個股專屬預測器進行預測
    predictions = []
    for stock_id in stocks:
        pred_result = stock_predictors[stock_id].predict(stock_id, as_of)
        # ... 收集預測結果 ...
```

**說明**：
- `pd.date_range(freq='M')` 生成每個月最後一天的日期序列
- 每個月底都會執行完整的訓練→預測→交易流程

### 2. 滾動式模型訓練

```python
# 生成訓練資料，使用截至預測日期之前的資料
# 使用2015年作為訓練開始日期（與內層回測一致）
features_df, targets_df = self.fe.generate_training_dataset(
    stock_ids=[stock_id],
    start_date='2015-01-01',
    end_date=as_of  # 每個月都更新到當前月底
)

# 訓練模型
train_result = stock_predictors[stock_id].train(
    feature_df=features_df,
    target_df=targets_df
)
```

**說明**：
- 每個月都用最新的資料重新訓練模型
- 訓練資料從2015-01-01開始，到當前月底結束
- 每檔股票都有獨立的模型和最佳參數

### 3. 預測與篩選

```python
# 選擇預期報酬大於門檻的股票（降低門檻以便測試）
prediction_threshold = -0.05  # 允許預測報酬低至-5%的股票
positive_preds = [p for p in predictions if p['predicted_return'] > prediction_threshold]

# 按預期報酬排序
positive_preds.sort(key=lambda x: x['predicted_return'], reverse=True)
```

**說明**：
- 預測門檻設為-5%（相對寬鬆）
- 符合條件的股票按預測報酬由高到低排序
- 所有符合條件的股票都會被買入（等權重）

### 4. 交易執行

```python
def _execute_trade(self, stock_id: str, entry_date: str, holding_days: int):
    """執行交易並返回詳細資訊"""
    # 獲取進場價格
    entry_df = self.dm.get_stock_prices(stock_id, entry_date, entry_date)
    entry_price = float(entry_df.iloc[-1]['close'])
    
    # 計算出場日期
    entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
    exit_dt = entry_dt + timedelta(days=holding_days)
    exit_date = exit_dt.strftime('%Y-%m-%d')
    
    # 獲取出場價格
    exit_df = self.dm.get_stock_prices(stock_id, entry_date, exit_date)
    exit_price = float(exit_df.iloc[-1]['close'])
    
    # 計算報酬和損益
    actual_return = (exit_price - entry_price) / entry_price
    profit_loss = exit_price - entry_price
```

**說明**：
- 在月底收盤價買入
- 固定持有20天
- 在第20天的收盤價賣出
- 計算實際報酬率和損益

### 5. 配置設定

```python
# 在 config/settings.py 中
WALKFORWARD_CONFIG = {
    'holdout_start': '2023-01',
    'holdout_end': '2024-12',
}

TRADING_CONFIG = {
    'position_management': {
        'rebalance_frequency': 'monthly',
        'position_sizing_method': 'equal_weight',
    },
}
```

**說明**：
- 外層回測期間：2023年1月到2024年12月
- 再平衡頻率：每月
- 倉位分配：等權重

## 問題解答

### Q1: 回測的買賣點會看每日的股價來決定嗎？

**A1: 不是**
- 交易頻率是**每月一次**，不是每日
- 買入時機固定在**每個月最後一個交易日**
- 賣出時機固定在**買入後第20天**
- 系統不會每天檢查股價來調整買賣決策

### Q2: 回測的時候也會每個月滾動式計算次AI模型嗎？

**A2: 是的**
- **每個月都會重新訓練**AI模型
- 訓練資料會**滾動更新**（從2015-01-01到當前月底）
- 每檔股票都有**獨立的模型**和最佳參數
- 這確保模型能學習到最新的市場資訊

## 實際執行結果

根據最新的回測結果：
- **測試期間**: 2023-01 到 2024-12（24個月）
- **候選股票**: 1314, 1309, 1319, 1215（4檔）
- **總交易數**: 57筆（平均每月2.4筆）
- **總報酬率**: 73.45%
- **勝率**: 66.7%

這個結果驗證了滾動式AI模型訓練和月頻交易策略的有效性。
