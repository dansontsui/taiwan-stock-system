# 🚀 台股潛力股分析系統 - 資料架構擴展計劃

## 📊 當前資料架構
- ✅ stocks (股票基本資料)
- ✅ stock_prices (日K線股價資料)
- ✅ technical_indicators (技術指標)
- ✅ etf_dividends (ETF配息)
- ✅ data_updates (資料更新記錄)

## 🎯 新增資料表設計

### 1. 財務報表資料 (Financial Statements)

#### 1.1 綜合損益表 (Income Statement)
```sql
CREATE TABLE income_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,  -- 1,2,3,4 (季報) 或 0 (年報)
    report_type TEXT NOT NULL, -- 'Q' (季報) 或 'A' (年報)
    
    -- 營收相關
    revenue REAL,              -- 營業收入
    operating_revenue REAL,    -- 營業毛利
    operating_expenses REAL,   -- 營業費用
    operating_income REAL,     -- 營業利益
    
    -- 損益相關
    non_operating_income REAL, -- 營業外收入
    pre_tax_income REAL,       -- 稅前淨利
    income_tax REAL,           -- 所得稅費用
    net_income REAL,           -- 本期淨利
    
    -- 每股盈餘
    eps REAL,                  -- 基本每股盈餘
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, year, quarter, report_type)
);
```

#### 1.2 資產負債表 (Balance Sheet)
```sql
CREATE TABLE balance_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    report_type TEXT NOT NULL,
    
    -- 資產
    current_assets REAL,       -- 流動資產
    non_current_assets REAL,   -- 非流動資產
    total_assets REAL,         -- 資產總計
    
    -- 負債
    current_liabilities REAL,  -- 流動負債
    non_current_liabilities REAL, -- 非流動負債
    total_liabilities REAL,    -- 負債總計
    
    -- 股東權益
    shareholders_equity REAL,  -- 股東權益總計
    
    -- 重要項目
    cash_and_equivalents REAL, -- 現金及約當現金
    inventory REAL,            -- 存貨
    accounts_receivable REAL,  -- 應收帳款
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, year, quarter, report_type)
);
```

#### 1.3 現金流量表 (Cash Flow Statement)
```sql
CREATE TABLE cash_flow_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    report_type TEXT NOT NULL,
    
    -- 營業活動現金流量
    operating_cash_flow REAL,
    
    -- 投資活動現金流量
    investing_cash_flow REAL,
    
    -- 融資活動現金流量
    financing_cash_flow REAL,
    
    -- 本期現金流量變動
    net_cash_flow REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, year, quarter, report_type)
);
```

### 2. 除權息資料 (Dividend & Rights)

```sql
CREATE TABLE dividend_rights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    
    -- 除權息日期
    ex_dividend_date DATE,     -- 除息日
    ex_rights_date DATE,       -- 除權日
    
    -- 股利資訊
    cash_dividend REAL,        -- 現金股利
    stock_dividend REAL,       -- 股票股利
    
    -- 配股資訊
    rights_ratio REAL,         -- 配股比例
    rights_price REAL,         -- 配股價格
    
    -- 其他
    dividend_yield REAL,       -- 殖利率
    payout_ratio REAL,         -- 配息率
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, year)
);
```

### 3. 月營收資料 (Monthly Revenue)

```sql
CREATE TABLE monthly_revenues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    
    -- 營收資料
    revenue REAL NOT NULL,     -- 當月營收
    revenue_mom REAL,          -- 月增率 (%)
    revenue_yoy REAL,          -- 年增率 (%)
    
    -- 累計營收
    cumulative_revenue REAL,   -- 累計營收
    cumulative_yoy REAL,       -- 累計年增率 (%)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, year, month)
);
```

### 4. 財務比率 (Financial Ratios)

```sql
CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    
    -- 獲利能力
    roe REAL,                  -- 股東權益報酬率
    roa REAL,                  -- 資產報酬率
    gross_margin REAL,         -- 毛利率
    operating_margin REAL,     -- 營業利益率
    net_margin REAL,           -- 淨利率
    
    -- 財務結構
    debt_ratio REAL,           -- 負債比率
    debt_to_equity REAL,       -- 負債股東權益比
    current_ratio REAL,        -- 流動比率
    quick_ratio REAL,          -- 速動比率
    
    -- 經營效率
    inventory_turnover REAL,   -- 存貨週轉率
    receivables_turnover REAL, -- 應收帳款週轉率
    total_asset_turnover REAL, -- 總資產週轉率
    
    -- 市場價值
    pe_ratio REAL,             -- 本益比
    pb_ratio REAL,             -- 股價淨值比
    dividend_yield REAL,       -- 殖利率
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, year, quarter)
);
```

### 5. 潛力股評分 (Potential Stock Scoring)

```sql
CREATE TABLE stock_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    
    -- 各項評分 (0-100分)
    financial_score REAL,     -- 財務面評分
    growth_score REAL,        -- 成長性評分
    profitability_score REAL, -- 獲利能力評分
    stability_score REAL,     -- 穩定性評分
    valuation_score REAL,     -- 估值評分
    
    -- 綜合評分
    total_score REAL,         -- 總分
    grade TEXT,               -- 評等 (A+, A, B+, B, C+, C, D)
    
    -- 評分依據
    scoring_factors TEXT,     -- JSON格式，記錄評分因子
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, analysis_date)
);
```

### 6. 產業分類與比較 (Industry Classification)

```sql
CREATE TABLE industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_code TEXT UNIQUE NOT NULL,
    industry_name TEXT NOT NULL,
    parent_industry TEXT,     -- 上層產業分類
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 更新stocks表，加入產業關聯
ALTER TABLE stocks ADD COLUMN industry_code TEXT;
ALTER TABLE stocks ADD FOREIGN KEY (industry_code) REFERENCES industries (industry_code);
```

## 🔄 資料收集策略

### 1. 資料來源優先順序
1. **FinMind API** (主要來源)
   - 財務報表資料
   - 月營收資料
   - 除權息資料
   
2. **公開資訊觀測站** (補充來源)
   - 即時公告
   - 詳細財務資料
   
3. **台灣證券交易所** (驗證來源)
   - 基本市場資料

### 2. 更新頻率
- **日K線**: 每日更新
- **月營收**: 每月10日後更新
- **季報**: 每季結束後45天內更新
- **年報**: 每年結束後120天內更新
- **除權息**: 每年3-8月密集更新

### 3. 資料品質控制
- 資料完整性檢查
- 異常值偵測
- 歷史資料一致性驗證
- 多來源資料交叉驗證

## 📈 潛力股分析模型

### 1. 財務健康度評估
- 獲利能力趨勢
- 財務結構穩定性
- 現金流量品質

### 2. 成長性分析
- 營收成長率
- 獲利成長率
- 市場佔有率變化

### 3. 估值分析
- 相對估值 (PE, PB)
- 絕對估值 (DCF)
- 產業比較

### 4. 風險評估
- 財務風險
- 營運風險
- 市場風險

## 🎯 實施階段

### Phase 1: 基礎財務資料 (4週)
- 實作財務報表資料收集
- 建立月營收資料收集
- 基礎財務比率計算

### Phase 2: 進階分析功能 (4週)
- 除權息資料整合
- 潛力股評分系統
- 產業比較功能

### Phase 3: 智能分析 (4週)
- 機器學習模型
- 預測分析
- 投資建議系統

---

# 🚀 台股十年資料收集系統 - 完整使用指南

## 📋 系統概述

台股十年資料收集系統是一個全自動化的資料收集平台，能夠收集2015-2025年間的完整台股資料，包含股價、財務報表、月營收、股利政策等多維度資料，並提供智能潛力股分析功能。

### ✨ 系統特色

- 🤖 **全自動化**: 一鍵啟動，無需人工干預
- 🧠 **智能等待**: 遇到API限制自動等待70分鐘
- 📊 **增量收集**: 只收集缺失資料，避免重複
- 🔍 **實時監控**: 即時顯示收集進度和狀態
- 🎯 **潛力分析**: 多維度股票潛力評分系統

## 🎯 快速開始

### 1. 一鍵完整收集（推薦）

```bash
cd taiwan_stock_system
python scripts/collect_all_10years.py --batch-size 5
```

### 2. 啟動監控程序

```bash
# 新開終端視窗
python monitor_collection.py
```

### 3. 啟動Web介面

```bash
# 收集完成後
python run.py
```

訪問：http://localhost:8501

## 📊 資料收集範圍

### 收集期間
- **時間範圍**: 2015年1月1日 - 2025年12月31日（十年）
- **資料頻率**: 日線、月線、季報、年報

### 資料類型

| 資料類型 | 預估數量 | 說明 |
|---------|---------|------|
| 股票基本資料 | 2,800筆 | 上市櫃股票基本資訊 |
| 股價資料 | 500,000筆 | 十年日K線資料 |
| 月營收資料 | 60,000筆 | 每月營收及成長率 |
| 綜合損益表 | 500,000筆 | 季報、年報財務資料 |
| 資產負債表 | 1,200,000筆 | 財務結構資料 |
| 股利政策 | 8,000筆 | 配息配股資料 |
| 財務比率 | 35,000筆 | 自動計算財務指標 |
| 潛力股評分 | 50筆 | 綜合評分分析 |

## 🔧 執行方式詳解

### 方式一：完整自動收集

```bash
# 基本執行
python scripts/collect_all_10years.py

# 自訂參數執行
python scripts/collect_all_10years.py --batch-size 5 --skip-stock-prices
```

**參數說明**：
- `--batch-size`: 批次大小（建議3-5）
- `--skip-stock-prices`: 跳過股價資料收集

### 方式二：分步驟執行

#### 1. 股價資料收集（智能版）
```bash
python scripts/collect_stock_prices_smart.py \
  --start-date 2015-01-01 \
  --end-date 2025-12-31 \
  --batch-size 5 \
  --skip-threshold 90
```

#### 2. 月營收資料收集
```bash
python scripts/collect_monthly_revenue.py \
  --start-date 2015-01-01 \
  --end-date 2025-12-31 \
  --batch-size 5
```

#### 3. 綜合損益表收集
```bash
python scripts/collect_financial_statements.py \
  --start-date 2015-01-01 \
  --end-date 2025-12-31 \
  --batch-size 3
```

#### 4. 資產負債表收集
```bash
python scripts/collect_balance_sheets.py \
  --start-date 2015-01-01 \
  --end-date 2025-12-31 \
  --batch-size 3
```

#### 5. 股利政策收集
```bash
python scripts/collect_dividend_data.py \
  --start-date 2015-01-01 \
  --end-date 2025-12-31 \
  --batch-size 3
```

#### 6. 營收成長率計算
```bash
python scripts/calculate_revenue_growth.py
```

#### 7. 潛力股分析
```bash
python scripts/analyze_potential_stocks.py --top 50
```

### 方式三：指定股票收集

```bash
# 收集特定股票的完整資料
python scripts/collect_stock_prices_smart.py --stock-id 2330 --start-date 2015-01-01 --end-date 2025-12-31
python scripts/analyze_potential_stocks.py --stock-id 2330
```

## 📈 監控與狀態檢查

### 即時監控程序

```bash
python monitor_collection.py
```

**監控功能**：
- 🌐 **API狀態檢查**: 實時402錯誤檢測
- ⏰ **智能等待狀態**: 顯示等待進度
- 📊 **收集進度**: 各類資料收集狀況
- 🔧 **配置驗證**: 智能等待機制狀態

### 狀態檢查工具

```bash
python check_status.py
```

**檢查項目**：
- 最近402錯誤狀況
- 收集進度和速度
- 智能等待機制狀態
- 系統運行狀況

## 🧠 智能功能詳解

### 1. 智能等待機制

**功能**：
- 自動檢測402 API限制錯誤
- 智能等待70分鐘後自動重試
- 顯示等待進度和剩餘時間

**配置狀態**：
- ✅ collect_stock_prices_smart.py
- ✅ collect_monthly_revenue.py
- ✅ collect_financial_statements.py
- ✅ collect_balance_sheets.py
- ✅ collect_dividend_data.py

### 2. 自動跳過機制

**跳過條件**：
- 資料完成度 ≥ 90%（可調整）
- 避免重複收集已完成的資料

**跳過範例**：
```
✅ 月營收資料已完成 119.6% (59,787 筆)，跳過收集
✅ 綜合損益表已完成 2628.5% (525,698 筆)，跳過收集
```

### 3. 增量收集機制

**功能**：
- 檢測缺失的日期範圍
- 只收集缺失的資料
- 大幅提升收集效率

## 🎯 潛力股分析系統

### 評分維度

#### 1. 財務健康度（40%權重）
- **毛利率**（30分）: ≥30% 滿分
- **營業利益率**（25分）: ≥15% 滿分
- **淨利率**（25分）: ≥10% 滿分
- **負債比率**（20分）: ≤30% 滿分

#### 2. 成長潛力（40%權重）
- **平均營收年增率**（60分）: ≥20% 滿分
- **成長穩定性**（40分）: 正成長月數比例

#### 3. 配息穩定性（20%權重）
- **配息連續性**（50分）: 連續配息年數
- **配息穩定性**（50分）: 配息變異係數

### 評等標準

| 評等 | 分數範圍 | 說明 |
|------|---------|------|
| A+ | 85分以上 | 優質潛力股 |
| A | 75-84分 | 良好潛力股 |
| B+ | 65-74分 | 中等潛力股 |
| B | 55-64分 | 一般潛力股 |
| C+ | 45-54分 | 觀察股票 |
| C | 35-44分 | 風險股票 |
| D | 35分以下 | 高風險股票 |

### EPS預估功能

**預估方法**：
1. 取最近3個月營收
2. 計算歷史平均淨利率
3. 預估季淨利 = 季營收 × 平均淨利率
4. 預估EPS = 預估淨利 ÷ 流通股數

**範例**：
```
台泥(1101) EPS預估:
- 預估季營收: 35.4億元
- 平均淨利率: 8.3%
- 預估淨利: 2.9億元
- 預估EPS: 0.30元
```

## 🌐 Web介面功能

### Streamlit WebUI

**啟動方式**：
```bash
python run.py
```

**功能頁面**：
- 📊 **市場總覽**: 整體市場狀況
- 🔍 **股票查詢**: 個股資料查詢
- 📈 **股價圖表**: K線圖與技術分析
- 🏆 **排行榜**: 漲跌幅排行
- 🎯 **潛力股分析**: 潛力股排行榜
- ⚙️ **系統狀態**: 資料收集狀況

### 潛力股分析頁面

**功能**：
- 潛力股排行榜顯示
- 評分分布圖表
- 統計資訊展示
- 一鍵執行分析

### 股票詳細頁面

**新增功能**：
- 🎯 潛力評分顯示
- 💰 EPS預估分析
- 📊 配息穩定性分析
- 🚀 一鍵潛力分析

## ⚙️ 參數配置

### 批次大小建議

| 資料類型 | 建議批次大小 | 說明 |
|---------|-------------|------|
| 股價資料 | 5-10 | API限制較寬鬆 |
| 月營收 | 5 | 中等API限制 |
| 財務報表 | 3 | API限制較嚴格 |
| 資產負債表 | 3 | API限制較嚴格 |
| 股利政策 | 3 | API限制較嚴格 |

### 日期範圍設定

```bash
# 十年完整資料
--start-date 2015-01-01 --end-date 2025-12-31

# 最近五年
--start-date 2020-01-01 --end-date 2025-12-31

# 最近一年
--start-date 2024-01-01 --end-date 2025-12-31
```

## 🔍 故障排除

### 常見問題

#### 1. 402 API限制錯誤
**現象**：收集中斷，顯示402錯誤
**解決**：系統會自動等待70分鐘後重試

#### 2. 資料庫鎖定錯誤
**現象**：database is locked
**解決**：
```bash
# 檢查是否有其他程序在使用資料庫
ps aux | grep python
# 終止衝突程序後重新執行
```

#### 3. 記憶體不足
**現象**：程序被系統終止
**解決**：
```bash
# 降低批次大小
python scripts/collect_all_10years.py --batch-size 3
```

#### 4. 網路連線問題
**現象**：連線超時
**解決**：檢查網路連線，系統會自動重試

### 日誌檢查

```bash
# 檢查收集日誌
tail -f logs/collect_all_10years.log

# 檢查股價收集日誌
tail -f logs/collect_stock_prices_smart.log

# 檢查潛力股分析日誌
tail -f logs/analyze_potential_stocks.log
```

## 📊 效能優化

### 收集效能

**預估時間**：
- 股價資料：6-8小時（包含等待時間）
- 基本面資料：2-4小時（包含等待時間）
- 總計：8-12小時

**優化建議**：
1. 使用SSD硬碟提升I/O效能
2. 確保穩定的網路連線
3. 適當調整批次大小
4. 避免同時執行多個收集程序

### 資料庫優化

```sql
-- 建立索引提升查詢效能
CREATE INDEX idx_stock_prices_stock_date ON stock_prices(stock_id, date);
CREATE INDEX idx_monthly_revenues_stock_date ON monthly_revenues(stock_id, revenue_year, revenue_month);
CREATE INDEX idx_financial_ratios_stock_date ON financial_ratios(stock_id, date);
```

## 🎉 最佳實踐

### 1. 首次執行

```bash
# 1. 進入專案目錄
cd taiwan_stock_system

# 2. 啟動完整收集
python scripts/collect_all_10years.py --batch-size 5

# 3. 啟動監控（新終端）
python monitor_collection.py

# 4. 等待完成（8-12小時）

# 5. 啟動Web介面
python run.py
```

### 2. 定期更新

```bash
# 每月更新月營收
python scripts/collect_monthly_revenue.py --start-date 2025-01-01 --end-date 2025-12-31

# 每季更新財務報表
python scripts/collect_financial_statements.py --start-date 2025-01-01 --end-date 2025-12-31

# 重新分析潛力股
python scripts/analyze_potential_stocks.py --top 50
```

### 3. 資料驗證

```bash
# 檢查資料完整性
python check_status.py

# 驗證潛力股分析
python scripts/analyze_potential_stocks.py --stock-id 2330
```

## 🚀 進階功能

### 自訂分析腳本

```python
# 範例：自訂潛力股篩選條件
from app.utils.simple_database import SimpleDatabaseManager
from config import Config

db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
conn = db_manager.get_connection()

# 篩選ROE > 15% 且負債比 < 50% 的股票
query = """
SELECT s.stock_id, s.stock_name, fr.roe, fr.debt_ratio
FROM stocks s
JOIN financial_ratios fr ON s.stock_id = fr.stock_id
WHERE fr.roe > 15 AND fr.debt_ratio < 50
ORDER BY fr.roe DESC
"""

results = conn.execute(query).fetchall()
```

### API整合

```python
# 範例：取得潛力股排行榜API
import requests

response = requests.get('http://localhost:8501/api/stocks')
potential_stocks = response.json()
```

## 📞 技術支援

### 系統需求
- Python 3.8+
- 8GB+ RAM
- 10GB+ 可用硬碟空間
- 穩定網路連線

### 相依套件
```bash
pip install streamlit pandas numpy plotly loguru requests sqlite3
```

### 聯絡資訊
- 📧 技術問題：請查看日誌文件
- 📚 文件更新：請參考此說明文件
- 🐛 錯誤回報：請提供詳細日誌資訊

---

**🎯 恭喜！您現在擁有完整的台股十年資料收集系統！**

這個系統將為您提供：
- 📊 完整的十年台股資料
- 🧠 智能的潛力股分析
- 🌐 美觀的Web介面
- 🤖 全自動化的資料收集

**立即開始您的台股投資分析之旅！** 🚀📈💎
