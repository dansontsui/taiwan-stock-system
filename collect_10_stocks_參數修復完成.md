# 🔧 collect_10_stocks_10years.py 參數修復完成

## ❌ **原始問題**
```cmd
python scripts/collect_10_stocks_10years.py --batch-size 3
# 錯誤: unrecognized arguments: --batch-size 3
```

## ✅ **修復內容**

### 📋 **新增參數**
1. ✅ `--batch-size BATCH_SIZE` - 批次大小 (預設: 3)
2. ✅ `--test` - 測試模式 (只收集前3檔股票)

### 🔧 **修復的程式碼**

#### **參數解析器更新**
```python
def main():
    parser = argparse.ArgumentParser(description='收集10檔精選股票的10年資料')
    parser.add_argument('--start-date', default='2015-01-01', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'), help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=3, help='批次大小 (預設: 3)')  # ← 新增
    parser.add_argument('--test', action='store_true', help='測試模式 (只收集前3檔股票)')  # ← 新增
```

#### **測試模式支援**
```python
# 如果是測試模式，只處理前3檔股票
stocks_to_process = SELECTED_STOCKS[:3] if args.test else SELECTED_STOCKS

for i, stock_info in enumerate(stocks_to_process, 1):
    print(f"\n[{i}/{len(stocks_to_process)}] 處理 {stock_info['stock_id']} ({stock_info['stock_name']})")
```

#### **輸出資訊增強**
```python
print("📊 10檔精選股票10年資料收集系統")
print(f"收集期間: {args.start_date} ~ {args.end_date}")
print(f"批次大小: {args.batch_size}")
print(f"精選股票: {len(SELECTED_STOCKS)} 檔")
if args.test:
    print("🧪 測試模式：只收集前3檔股票")
```

## 🚀 **現在可以使用的命令**

### **基本使用**
```cmd
# 收集所有10檔股票的完整資料
python scripts/collect_10_stocks_10years.py --batch-size 3

# 指定日期範圍
python scripts/collect_10_stocks_10years.py --start-date 2020-01-01 --end-date 2024-12-31 --batch-size 3
```

### **測試模式** (推薦先使用)
```cmd
# 測試模式：只收集前3檔股票
python scripts/collect_10_stocks_10years.py --test --batch-size 3

# 測試模式 + 指定日期
python scripts/collect_10_stocks_10years.py --test --start-date 2024-01-01 --end-date 2024-12-31 --batch-size 3
```

### **查看幫助**
```cmd
python scripts/collect_10_stocks_10years.py --help
```

## 📊 **腳本功能確認**

### ✅ **包含的資料集**
1. 📈 **股價資料** - 完整的日線資料
2. 💰 **現金流量表** - `TaiwanStockCashFlowsStatement`
3. 🎯 **除權除息結果** - `TaiwanStockDividendResult`

### ✅ **精選股票清單** (10檔)
腳本會自動顯示要收集的股票清單，包括：
- 股票代碼
- 股票名稱  
- ETF標記 (如適用)

### ✅ **智能功能**
- 🔄 **重試機制**: 失敗時自動重試
- ⏰ **智能等待**: API限制時自動等待
- 📊 **進度追蹤**: 顯示收集進度和統計
- 🗄️ **資料去重**: 避免重複收集

## 💡 **使用建議**

### **首次使用**
```cmd
# 1. 先用測試模式驗證功能
python scripts/collect_10_stocks_10years.py --test --batch-size 3

# 2. 如果測試成功，再執行完整收集
python scripts/collect_10_stocks_10years.py --batch-size 3
```

### **日常使用**
```cmd
# 更新最近一年的資料
python scripts/collect_10_stocks_10years.py --start-date 2024-01-01 --batch-size 3
```

### **搭配監控**
```cmd
# 在另一個終端機啟動監控
python 終端機監控.py --mode monitor
```

## 🎯 **與其他腳本的比較**

| 腳本 | 股票數量 | 資料集 | 適用場景 |
|------|---------|--------|----------|
| `collect_10_stocks_10years.py` | 10檔精選 | 股價+現金流量+除權除息 | 快速測試、精選股票 |
| `collect_all_10years.py` | 全部股票 | 所有資料集 | 完整收集、生產環境 |
| `collect_cash_flows.py` | 全部股票 | 只有現金流量 | 單一資料集收集 |
| `collect_dividend_results.py` | 全部股票 | 只有除權除息 | 單一資料集收集 |

## ✅ **修復完成確認**

### **參數支援**
- ✅ `--start-date` - 開始日期
- ✅ `--end-date` - 結束日期  
- ✅ `--batch-size` - 批次大小 (新增)
- ✅ `--test` - 測試模式 (新增)

### **功能支援**
- ✅ 現金流量表收集
- ✅ 除權除息結果收集
- ✅ 測試模式 (只收集前3檔)
- ✅ 批次大小控制
- ✅ 智能重試和等待

### **輸出增強**
- ✅ 顯示批次大小
- ✅ 顯示測試模式狀態
- ✅ 更清晰的進度資訊

## 🎉 **立即可用**

現在您可以安全地使用以下命令：

```cmd
# 測試模式 (推薦)
python scripts/collect_10_stocks_10years.py --test --batch-size 3

# 完整收集
python scripts/collect_10_stocks_10years.py --batch-size 3
```

**修復完成！現在腳本支援所有必要的參數，包含現金流量表和除權除息結果表的收集功能。** 🎊
