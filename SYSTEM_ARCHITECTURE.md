# Taiwan Stock System 系統架構說明

## 📋 系統概述

Taiwan Stock System 是一個完整的台股資料收集、分析和展示系統，支援跨平台運行（Windows/macOS/Linux），提供命令列和Web介面兩種操作方式。

## 🏗️ 系統架構

### 1. 啟動層 (Entry Points)

#### 主要啟動腳本
- **`start.py`** - 系統主入口
  - 提供互動式選單 (16個功能選項)
  - 支援命令列參數快速執行
  - 跨平台顏色支援 (Windows/Unix)
  - 虛擬環境檢查
  - 進度管理整合

- **`run.py`** - Web介面啟動器
  - 依賴套件檢查
  - 自動啟動 Streamlit 應用
  - 資料庫存在性驗證
  - 降級到命令列模式

- **`c.py`** - 核心資料收集控制器
  - 協調各種收集腳本
  - 支援斷點續傳
  - 批次處理管理
  - 個股/全市場收集

### 2. 資料收集層 (Data Collection)

#### 基礎收集腳本
- **`simple_collect.py`** - 基礎資料收集
  - 股價資料 (TaiwanStockPrice)
  - 月營收資料 (TaiwanStockMonthRevenue)
  - 現金流量表 (TaiwanStockCashFlowsStatement)
  - API限制檢測與智能等待

#### 專門收集腳本 (`scripts/`)
- **`collect_financial_statements.py`** - 財務報表收集
- **`collect_balance_sheets.py`** - 資產負債表收集
- **`collect_dividend_data.py`** - 股利政策收集
- **`collect_dividend_results.py`** - 除權除息結果收集
- **`collect_daily_update.py`** - 每日增量更新
- **`analyze_potential_stocks.py`** - 潛力股分析

#### 輔助功能
- **`scripts/smart_wait.py`** - 智能等待機制
- **`scripts/progress_manager.py`** - 進度管理
- **`scripts/simple_progress.py`** - 簡單進度記錄

### 3. 資料存儲層 (Data Storage)

#### 資料庫結構 (`data/taiwan_stock.db`)
```sql
-- 主要資料表
stocks                  -- 股票清單 (2,822筆)
stock_prices           -- 股價資料 (5,107,665筆)
monthly_revenues       -- 月營收資料 (210,350筆)
financial_statements   -- 財務報表 (1,142,499筆)
dividend_policies      -- 股利政策 (8,743筆)
stock_scores          -- 潛力股分析 (256筆)
dividend_results      -- 除權除息結果
cash_flow_statements  -- 現金流量表
balance_sheets        -- 資產負債表
financial_ratios      -- 財務比率
```

### 4. Web應用層 (Web Application)

#### Streamlit 儀表板
- **`app/web/dashboard.py`** - 主要儀表板
  - K線圖表展示
  - 成交量分析
  - 財務指標展示
  - 互動式查詢介面

#### 服務層
- **`app/services/query_service.py`** - 查詢服務
- **`app/services/data_collector.py`** - 資料收集服務

#### 工具層
- **`app/utils/database.py`** - 資料庫工具
- **`app/utils/simple_database.py`** - 簡化資料庫管理

#### 模板
- **`templates/base.html`** - 基礎模板
- **`templates/index.html`** - 首頁模板
- **`templates/stock_detail.html`** - 個股詳情模板

### 5. 配置層 (Configuration)

#### 配置檔案
- **`config.py`** - 系統配置
  - 資料庫路徑配置
  - FinMind API 配置
  - 技術指標參數
  - 圖表配置

#### 環境配置
- **`.env`** - 環境變數 (可選)
- **`requirements.txt`** - Python 依賴清單

### 6. 輔助功能

#### 日誌系統
- **`logs/`** - 日誌檔案目錄
  - 收集過程日誌
  - 錯誤記錄
  - 進度追蹤

#### 進度管理
- **`data/progress/`** - 進度檔案
- **`data/simple_progress/`** - 簡單進度記錄

## 🔄 資料流程

### 資料收集流程
1. **初始化** - 檢查資料庫和環境
2. **股票清單** - 獲取活躍股票清單
3. **基礎資料** - 收集股價、營收、現金流
4. **財務資料** - 收集財報、資產負債表
5. **股利資料** - 收集股利政策和除權除息
6. **分析處理** - 計算潛力股評分

### Web展示流程
1. **資料查詢** - 從資料庫讀取資料
2. **資料處理** - 格式化和計算指標
3. **圖表生成** - 使用 Plotly 生成互動圖表
4. **介面展示** - Streamlit 渲染頁面

## 🎯 主要功能

### 資料收集功能
- ✅ 基礎資料收集 (股價、營收、現金流)
- ✅ 財務報表收集 (損益表、資產負債表)
- ✅ 股利資料收集 (政策、除權除息)
- ✅ 潛力股分析
- ✅ 每日增量更新
- ✅ 斷點續傳支援

### 查詢分析功能
- ✅ 個股資料查詢
- ✅ 資料完整性檢查
- ✅ 缺失資料分析
- ✅ 潛力股排名
- ✅ 財務指標計算

### Web介面功能
- ✅ 互動式K線圖
- ✅ 成交量分析
- ✅ 財務指標展示
- ✅ 多股票比較
- ✅ 響應式設計

## 🛠️ 技術特色

### 跨平台支援
- Windows/macOS/Linux 相容
- 編碼問題自動處理
- 路徑分隔符自動適配

### 智能等待機制
- API限制自動檢測
- 智能重試機制
- 進度保存與恢復

### 模組化設計
- 功能分離，易於維護
- 配置集中管理
- 錯誤處理完善

### 效能優化
- 批次處理
- 資料快取
- 增量更新

## 📊 資料統計

根據測試結果，系統目前包含：
- **股票數量**: 2,822 檔
- **股價記錄**: 5,107,665 筆
- **營收記錄**: 210,350 筆
- **財報記錄**: 1,142,499 筆
- **股利記錄**: 8,743 筆
- **分析記錄**: 256 筆

## 🚀 使用方式

### 命令列模式
```bash
# 互動式選單
python start.py

# 直接執行功能
python start.py all          # 收集所有股票基礎資料
python start.py test         # 測試模式
python start.py complete     # 完整資料收集
python start.py web          # 啟動Web介面
```

### Web介面模式
```bash
python run.py
# 或
python start.py web
```

## 📝 總結

Taiwan Stock System 是一個功能完整、架構清晰的台股資料系統，具備：

1. **完整的資料收集能力** - 涵蓋股價、財報、股利等各類資料
2. **智能的錯誤處理** - API限制檢測、斷點續傳、進度管理
3. **友好的使用介面** - 命令列選單和Web儀表板
4. **優秀的跨平台支援** - Windows/macOS/Linux 通用
5. **模組化的系統設計** - 易於擴展和維護

系統已經過測試驗證，所有核心組件運行正常，資料庫包含豐富的歷史資料，可以滿足台股分析的各種需求。
