# CSV欄位中文化完成

## 🎉 **修正完成！**

### ✅ **修正內容**

1. **選單5的 holdout_trades.csv 欄位改為中文**
2. **選單5b的 stop_loss_trades.csv 欄位改為中文**
3. **兩邊欄位完全對齊，差異部分放在後面**

## 📊 **統一的中文欄位順序**

### **基本資訊（與選單5相同）**
```csv
進場日, 股票代號, 模型, 預測報酬,
進場價, 出場日, 出場價, 持有天數
```

### **選單5的計算結果（等權重，無交易成本）**
```csv
毛報酬, 毛損益, 20日最大報酬, 20日最小報酬
```

### **選單5a/5b的計算結果（定期定額，含交易成本）**
```csv
股數, 投資金額, 月底價值,
淨報酬, 淨損益, 交易成本
```

### **選單5b專屬欄位（停損停利）**
```csv
出場原因, 成本影響
```

## 🔍 **欄位對照表**

| 中文欄位名稱 | 原英文欄位 | 說明 |
|-------------|-----------|------|
| 進場日 | entry_date | 買入日期 |
| 股票代號 | stock_id | 股票代碼 |
| 模型 | model_type | 預測模型類型 |
| 預測報酬 | predicted_return | 模型預測的報酬率 |
| 進場價 | entry_price | 買入價格 |
| 出場日 | exit_date | 賣出日期 |
| 出場價 | exit_price | 賣出價格 |
| 持有天數 | holding_days | 持有期間 |
| 毛報酬 | actual_return_gross | 不含交易成本的報酬率 |
| 毛損益 | profit_loss_gross | 不含交易成本的損益金額 |
| 20日最大報酬 | max_return_20d | 持有期間最高報酬率 |
| 20日最小報酬 | min_return_20d | 持有期間最低報酬率 |
| 股數 | shares | 購買股數 |
| 投資金額 | investment_amount | 實際投資金額 |
| 月底價值 | month_end_value | 月底持股價值 |
| 淨報酬 | actual_return_net | 扣除交易成本後的報酬率 |
| 淨損益 | profit_loss_net | 扣除交易成本後的損益金額 |
| 交易成本 | transaction_costs | 交易成本詳細資訊 |
| 出場原因 | exit_reason | 停損停利出場原因 |
| 成本影響 | cost_impact | 交易成本對報酬的影響 |

## 📁 **檔案輸出對比**

### **選單5輸出**
```
📁 holdout_YYYYMM_YYYYMM_XXX_kXX_XX_TIMESTAMP/
├── 📄 holdout_trades_TIMESTAMP.csv        # 中文欄位
├── 📄 holdout_TIMESTAMP.json
└── 📄 holdout_monthly_TIMESTAMP_YYYYMMDD.csv
```

### **選單5b輸出**
```
📁 holdout_YYYYMM_YYYYMM_XXX_kXX_XX_SLX%TPX%_TIMESTAMP/
├── 📄 stop_loss_trades_TIMESTAMP.csv      # 中文欄位
├── 📄 stop_loss_results_TIMESTAMP.json
├── 📄 stop_loss_summary_TIMESTAMP.md
└── 📄 holdout_monthly_TIMESTAMP_YYYYMMDD.csv
```

## 🎯 **欄位對齊說明**

### **完全相同的欄位（1-12欄）**
兩邊CSV的前12個欄位完全相同：
- 基本資訊：進場日 ~ 持有天數
- 毛報酬計算：毛報酬 ~ 20日最小報酬

### **選單5a/5b額外欄位（13-18欄）**
定期定額投資專屬：
- 股數、投資金額、月底價值
- 淨報酬、淨損益、交易成本

### **選單5b專屬欄位（19-20欄）**
停損停利專屬：
- 出場原因、成本影響

## 💡 **出場原因說明**

| 出場原因 | 英文值 | 說明 |
|---------|--------|------|
| normal | normal | 正常到期（持有滿20個交易日） |
| take_profit | take_profit | 停利出場（達到停利點） |
| stop_loss | stop_loss | 停損出場（達到停損點） |
| no_data | no_data | 無價格資料 |

## 📈 **成本影響計算**

```
成本影響 = 毛報酬 - 淨報酬
```

**範例**：
- 毛報酬：5.00%
- 淨報酬：4.29%
- 成本影響：0.71%

表示交易成本降低了0.71%的報酬率。

## 🎯 **使用效果**

### ✅ **完全對齊**
- 選單5和5b的CSV可以直接比較
- 前12個欄位完全相同
- 新增欄位清楚標示差異

### ✅ **中文化**
- 所有欄位名稱都是中文
- 更直觀易懂
- 符合台灣使用習慣

### ✅ **向後相容**
- 保持原有的計算邏輯
- 只是欄位名稱中文化
- 不影響現有功能

## 🚀 **立即使用**

現在您可以：
1. **執行選單5** - 獲得中文欄位的 holdout_trades.csv
2. **執行選單5b** - 獲得中文欄位的 stop_loss_trades.csv
3. **直接比較** - 兩個CSV檔案的欄位完全對齊
4. **清楚分析** - 停損停利的效果一目了然

**所有CSV輸出現在都是中文欄位，且完全對齊！** 🎯

---

*修正完成時間: 2025-08-27*
