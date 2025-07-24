# 🚀 基於FinMind API的潛力股分析資料庫設計

## 📊 FinMind API 可用資料集

### ✅ 基本面資料 (11種)
1. **TaiwanStockFinancialStatements** - 綜合損益表
2. **TaiwanStockBalanceSheet** - 資產負債表  
3. **TaiwanStockCashFlowsStatement** - 現金流量表
4. **TaiwanStockDividend** - 股利政策表
5. **TaiwanStockDividendResult** - 除權除息結果表
6. **TaiwanStockMonthRevenue** - 月營收表
7. **TaiwanStockCapitalReductionReferencePrice** - 減資恢復買賣參考價格
8. **TaiwanStockMarketValue** - 股價市值表 (付費)
9. **TaiwanStockDelisting** - 股票下市櫃表
10. **TaiwanStockMarketValueWeight** - 市值比重表 (付費)
11. **TaiwanStockSplitPrice** - 股票分割後參考價

## 🗄️ 新增資料表設計

### 1. 綜合損益表 (Financial Statements)
```sql
CREATE TABLE financial_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    type TEXT NOT NULL,           -- FinMind的type欄位 (如: EPS, Revenue等)
    value REAL,                   -- 數值
    origin_name TEXT,             -- 中文名稱
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date, type)
);
```

### 2. 資產負債表 (Balance Sheet)
```sql
CREATE TABLE balance_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    type TEXT NOT NULL,           -- 如: TotalAssets, TotalLiabilities等
    value REAL,
    origin_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date, type)
);
```

### 3. 現金流量表 (Cash Flow Statement)
```sql
CREATE TABLE cash_flow_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    type TEXT NOT NULL,           -- 如: CashFlowsFromOperatingActivities等
    value REAL,
    origin_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date, type)
);
```

### 4. 股利政策表 (Dividend Policy)
```sql
CREATE TABLE dividend_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    year TEXT NOT NULL,
    
    -- 股票股利
    stock_earnings_distribution REAL,
    stock_statutory_surplus REAL,
    stock_ex_dividend_trading_date DATE,
    
    -- 現金股利
    cash_earnings_distribution REAL,
    cash_statutory_surplus REAL,
    cash_ex_dividend_trading_date DATE,
    cash_dividend_payment_date DATE,
    
    -- 員工分紅
    total_employee_stock_dividend REAL,
    total_employee_cash_dividend REAL,
    
    -- 其他資訊
    participate_distribution_total_shares REAL,
    announcement_date DATE,
    announcement_time TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date, year)
);
```

### 5. 除權息結果表 (Dividend Results)
```sql
CREATE TABLE dividend_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,           -- 除權息日期
    
    before_price REAL,            -- 除權息前價格
    after_price REAL,             -- 除權息後價格
    stock_and_cache_dividend REAL, -- 股利金額
    stock_or_cache_dividend TEXT, -- 除權或除息
    
    -- 當日交易資訊
    max_price REAL,
    min_price REAL,
    open_price REAL,
    reference_price REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date)
);
```

### 6. 月營收表 (Monthly Revenue)
```sql
CREATE TABLE monthly_revenues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,           -- 資料發布日期
    country TEXT,                 -- 國家
    revenue BIGINT,               -- 營收金額
    revenue_month INTEGER,        -- 營收月份
    revenue_year INTEGER,         -- 營收年份
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, revenue_year, revenue_month)
);
```

### 7. 股價市值表 (Market Value) - 需付費會員
```sql
CREATE TABLE market_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    market_value BIGINT,          -- 市值
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date)
);
```

### 8. 市值比重表 (Market Value Weight) - 需付費會員
```sql
CREATE TABLE market_value_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    stock_name TEXT,
    date DATE NOT NULL,
    rank INTEGER,                 -- 排名
    weight_per REAL,              -- 權重百分比
    type TEXT,                    -- twse/tpex
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date, type)
);
```

### 9. 股票分割表 (Stock Split)
```sql
CREATE TABLE stock_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    type TEXT,                    -- 分割/反分割
    before_price REAL,
    after_price REAL,
    max_price REAL,
    min_price REAL,
    open_price REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date)
);
```

### 10. 財務比率計算表 (自行計算)
```sql
CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    
    -- 獲利能力 (從損益表計算)
    gross_margin REAL,            -- 毛利率
    operating_margin REAL,        -- 營業利益率
    net_margin REAL,              -- 淨利率
    roe REAL,                     -- 股東權益報酬率
    roa REAL,                     -- 資產報酬率
    
    -- 財務結構 (從資產負債表計算)
    debt_ratio REAL,              -- 負債比率
    current_ratio REAL,           -- 流動比率
    
    -- 成長率 (從月營收計算)
    revenue_growth_mom REAL,      -- 營收月增率
    revenue_growth_yoy REAL,      -- 營收年增率
    
    -- 估值指標
    pe_ratio REAL,                -- 本益比 (需股價資料)
    pb_ratio REAL,                -- 股價淨值比
    dividend_yield REAL,          -- 殖利率
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, date)
);
```

### 11. 潛力股評分表
```sql
CREATE TABLE stock_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    analysis_date DATE NOT NULL,
    
    -- 各項評分 (0-100分)
    financial_health_score REAL,  -- 財務健康度
    profitability_score REAL,     -- 獲利能力
    growth_score REAL,            -- 成長性
    valuation_score REAL,         -- 估值合理性
    dividend_score REAL,          -- 配息穩定性
    
    -- 綜合評分
    total_score REAL,
    grade TEXT,                   -- A+, A, B+, B, C+, C, D
    
    -- 評分依據 (JSON格式)
    score_details TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks (stock_id),
    UNIQUE(stock_id, analysis_date)
);
```

## 📈 資料收集優先順序

### Phase 1: 基礎財務資料 (免費)
1. **月營收** - TaiwanStockMonthRevenue
2. **股利政策** - TaiwanStockDividend  
3. **除權息結果** - TaiwanStockDividendResult
4. **股票分割** - TaiwanStockSplitPrice

### Phase 2: 詳細財務報表 (免費)
1. **綜合損益表** - TaiwanStockFinancialStatements
2. **資產負債表** - TaiwanStockBalanceSheet
3. **現金流量表** - TaiwanStockCashFlowsStatement

### Phase 3: 進階資料 (需付費)
1. **股價市值** - TaiwanStockMarketValue
2. **市值比重** - TaiwanStockMarketValueWeight

### Phase 4: 分析功能
1. **財務比率計算**
2. **潛力股評分系統**
3. **產業比較分析**

## 🔄 資料更新策略

### 更新頻率
- **月營收**: 每月10日後更新
- **季報資料**: 每季結束後45天內
- **年報資料**: 每年結束後120天內
- **除權息**: 3-8月密集更新
- **股價市值**: 每日更新 (付費)

### 資料品質控制
- 重複資料檢查
- 異常值偵測
- 資料完整性驗證
- 歷史資料一致性檢查

## 💡 潛力股分析指標

### 1. 財務健康度 (Financial Health)
- **獲利能力**: 毛利率、營業利益率、淨利率趨勢
- **財務結構**: 負債比率、流動比率
- **現金流量**: 營業現金流量品質

### 2. 成長性分析 (Growth Analysis)
- **營收成長**: 月營收年增率、季增率
- **獲利成長**: EPS成長率
- **市值成長**: 市值變化趨勢

### 3. 估值分析 (Valuation)
- **本益比**: PE相對歷史水準
- **股價淨值比**: PB相對同業
- **殖利率**: 配息穩定性

### 4. 風險評估 (Risk Assessment)
- **財務風險**: 負債水準、現金流穩定性
- **營運風險**: 營收波動度
- **市場風險**: 股價波動度

## 🎯 實施建議

### 第一階段 (4週): 基礎資料收集
1. 實作月營收資料收集
2. 實作股利政策資料收集
3. 實作除權息結果資料收集
4. 建立基礎財務比率計算

### 第二階段 (4週): 財務報表分析
1. 實作綜合損益表資料收集
2. 實作資產負債表資料收集
3. 實作現金流量表資料收集
4. 建立進階財務比率計算

### 第三階段 (4週): 潛力股評分系統
1. 建立評分演算法
2. 實作潛力股篩選功能
3. 建立產業比較分析
4. 實作投資建議系統
