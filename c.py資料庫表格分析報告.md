# c.py 資料庫表格存取分析報告

## 📊 總覽

**c.py 直接存取的表格數量：4 個**  
**系統總表格數量：15 個**  
**資料庫路徑：** `data/taiwan_stock.db`

---

## 🎯 c.py 直接存取的表格（4個）

### 1. stocks - 股票基本資料表
- **用途：** 儲存股票代碼、名稱、市場別、產業別等基本資訊
- **c.py 操作：** 查詢股票清單
- **記錄數：** 2,822 筆
- **欄位數：** 9 個
- **主要欄位：** stock_id, stock_name, market, industry, listing_date
- **SQL 操作：**
  ```sql
  SELECT stock_id, stock_name FROM stocks 
  WHERE LENGTH(stock_id) = 4 
  AND stock_id GLOB '[0-9][0-9][0-9][0-9]'
  AND stock_id NOT LIKE '00%'
  ORDER BY stock_id
  ```

### 2. stock_prices - 股價資料表
- **用途：** 儲存每日股價資料（開高低收、成交量、成交金額等）
- **c.py 操作：** 插入/更新股價資料
- **記錄數：** 5,107,533 筆
- **欄位數：** 12 個
- **主要欄位：** id, stock_id, date, open_price, high_price, low_price, close_price, volume
- **資料來源：** FinMind API - TaiwanStockPrice
- **SQL 操作：**
  ```sql
  INSERT OR REPLACE INTO stock_prices 
  (stock_id, date, open_price, high_price, low_price, close_price, 
   volume, trading_money, trading_turnover, spread, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  ```

### 3. monthly_revenues - 月營收資料表
- **用途：** 儲存公司每月營收資料及成長率
- **c.py 操作：** 插入/更新月營收資料
- **記錄數：** 210,350 筆
- **欄位數：** 10 個
- **主要欄位：** id, stock_id, date, country, revenue, revenue_month, revenue_year
- **資料來源：** FinMind API - TaiwanStockMonthRevenue
- **SQL 操作：**
  ```sql
  INSERT OR REPLACE INTO monthly_revenues 
  (stock_id, date, country, revenue, revenue_month, revenue_year, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?)
  ```

### 4. cash_flow_statements - 現金流量表
- **用途：** 儲存現金流量相關財務資料
- **c.py 操作：** 插入/更新現金流資料
- **記錄數：** 48,762 筆
- **欄位數：** 7 個
- **主要欄位：** id, stock_id, date, type, value, origin_name
- **資料來源：** FinMind API - TaiwanStockCashFlowsStatement
- **SQL 操作：**
  ```sql
  INSERT OR REPLACE INTO cash_flow_statements 
  (stock_id, date, type, value, origin_name, created_at)
  VALUES (?, ?, ?, ?, ?, ?)
  ```

---

## 📋 系統其他表格（11個）

這些表格存在於系統中，但 c.py 不直接存取：

| 序號 | 表格名稱 | 描述 | 記錄數 |
|------|----------|------|--------|
| 1 | technical_indicators | 技術指標表 | 0 筆 |
| 2 | etf_dividends | ETF配息表 | 35 筆 |
| 3 | data_updates | 資料更新記錄表 | 75 筆 |
| 4 | market_values | 市值資料表 | 0 筆 |
| 5 | stock_splits | 股票分割表 | 0 筆 |
| 6 | dividend_results | 除權除息結果表 | 126 筆 |
| 7 | financial_statements | 綜合損益表 | 資料量大 |
| 8 | balance_sheets | 資產負債表 | 資料量大 |
| 9 | dividend_policies | 股利政策表 | 資料量大 |
| 10 | financial_ratios | 財務比率表 | 資料量大 |
| 11 | stock_scores | 潛力股評分表 | 資料量大 |

---

## 🔄 c.py 資料收集流程

### 1. 執行流程
```
c.py → simple_collect.py → FinMind API → 資料庫
```

### 2. 詳細步驟
1. **查詢股票清單**：從 `stocks` 表獲取要收集的股票代碼
2. **API 資料收集**：呼叫 FinMind API 獲取三類資料
   - TaiwanStockPrice（股價資料）
   - TaiwanStockMonthRevenue（月營收資料）
   - TaiwanStockCashFlowsStatement（現金流資料）
3. **資料儲存**：將收集到的資料分別儲存到對應表格

### 3. 資料對應關係
- **TaiwanStockPrice** → `stock_prices` 表
- **TaiwanStockMonthRevenue** → `monthly_revenues` 表
- **TaiwanStockCashFlowsStatement** → `cash_flow_statements` 表

---

## 📈 資料量統計

| 表格 | 記錄數 | 佔比 |
|------|--------|------|
| stock_prices | 5,107,533 筆 | 94.8% |
| monthly_revenues | 210,350 筆 | 3.9% |
| cash_flow_statements | 48,762 筆 | 0.9% |
| stocks | 2,822 筆 | 0.1% |
| **總計** | **5,369,467 筆** | **100%** |

---

## 🎯 總結

### c.py 的核心功能
- **主要任務**：從 FinMind API 收集台股資料
- **存取表格**：4 個核心資料表格
- **收集範圍**：股價、月營收、現金流三大類資料
- **執行方式**：透過 simple_collect.py 執行實際的資料收集工作

### 資料特點
- **股價資料**：佔總資料量的 94.8%，是最大宗的資料
- **月營收資料**：提供公司營運狀況的月度追蹤
- **現金流資料**：反映公司財務健康狀況
- **基本資料**：提供股票篩選和識別功能

### 系統架構
c.py 專注於資料收集，其他 11 個表格由系統的其他模組負責，形成完整的台股分析系統。
