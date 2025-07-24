# 🚀 台股十年資料收集系統

## 📋 系統簡介

台股十年資料收集系統是一個全自動化的台股資料收集與分析平台，能夠收集2015-2025年間的完整台股資料，並提供智能潛力股分析功能。

### ✨ 核心特色

- 🤖 **全自動化收集**: 一鍵啟動，無需人工干預
- 🧠 **智能等待機制**: 遇到API限制自動等待70分鐘
- 📊 **增量收集**: 只收集缺失資料，避免重複
- 🔍 **實時監控**: 即時顯示收集進度和API狀態
- 🎯 **潛力股分析**: 多維度股票評分系統
- 🌐 **Web介面整合**: 美觀的Streamlit介面

## 🎯 快速開始

### 1. 一鍵完整收集

```bash
cd taiwan_stock_system
python scripts/collect_all_10years.py --batch-size 5
```

### 2. 啟動監控

```bash
# 新開終端視窗
python monitor_collection.py
```

### 3. 查看Web介面

```bash
# 收集完成後
python run.py
```

訪問：http://localhost:8501

## 📊 資料收集範圍

| 資料類型 | 預估數量 | 收集期間 | 說明 |
|---------|---------|---------|------|
| 股票基本資料 | 2,800筆 | - | 上市櫃股票基本資訊 |
| 股價資料 | 500,000筆 | 2015-2025 | 十年日K線資料 |
| 月營收資料 | 60,000筆 | 2015-2025 | 每月營收及成長率 |
| 綜合損益表 | 500,000筆 | 2015-2025 | 季報、年報財務資料 |
| 資產負債表 | 1,200,000筆 | 2015-2025 | 財務結構資料 |
| 股利政策 | 8,000筆 | 2015-2025 | 配息配股資料 |
| 財務比率 | 35,000筆 | 2015-2025 | 自動計算財務指標 |
| 潛力股評分 | 50筆 | 即時 | 綜合評分分析 |

## 🔧 執行方式

### 方式一：完整自動收集（推薦）

```bash
# 基本執行
python scripts/collect_all_10years.py

# 自訂參數
python scripts/collect_all_10years.py --batch-size 5
```

### 方式二：分步驟執行

```bash
# 1. 股價資料
python scripts/collect_stock_prices_smart.py --start-date 2015-01-01 --end-date 2025-12-31

# 2. 月營收資料
python scripts/collect_monthly_revenue.py --start-date 2015-01-01 --end-date 2025-12-31

# 3. 財務報表
python scripts/collect_financial_statements.py --start-date 2015-01-01 --end-date 2025-12-31

# 4. 資產負債表
python scripts/collect_balance_sheets.py --start-date 2015-01-01 --end-date 2025-12-31

# 5. 股利政策
python scripts/collect_dividend_data.py --start-date 2015-01-01 --end-date 2025-12-31

# 6. 計算成長率
python scripts/calculate_revenue_growth.py

# 7. 潛力股分析
python scripts/analyze_potential_stocks.py --top 50
```

### 方式三：指定股票收集

```bash
# 收集特定股票
python scripts/collect_stock_prices_smart.py --stock-id 2330
python scripts/analyze_potential_stocks.py --stock-id 2330
```

## 📈 監控與檢查

### 即時監控

```bash
python monitor_collection.py
```

**監控功能**：
- 🌐 API狀態檢查（402錯誤檢測）
- ⏰ 智能等待狀態顯示
- 📊 資料收集進度追蹤
- 🔧 智能等待機制配置驗證

### 狀態檢查

```bash
python check_status.py
```

**檢查項目**：
- 最近402錯誤狀況
- 收集進度和速度
- 系統運行狀況

## 🧠 智能功能

### 1. 智能等待機制

- **自動檢測**: 檢測402 API限制錯誤
- **智能等待**: 自動等待70分鐘後重試
- **進度顯示**: 顯示等待進度和剩餘時間
- **全腳本支援**: 所有收集腳本都支援

### 2. 自動跳過機制

- **完成度檢查**: 檢查資料完成度
- **智能跳過**: 完成度≥90%自動跳過
- **避免重複**: 不重複收集已完成資料

### 3. 增量收集機制

- **缺失檢測**: 檢測缺失的日期範圍
- **精準收集**: 只收集缺失資料
- **效率提升**: 大幅提升收集效率

## 🎯 潛力股分析

### 評分系統

#### 財務健康度（40%權重）
- 毛利率（30分）
- 營業利益率（25分）
- 淨利率（25分）
- 負債比率（20分）

#### 成長潛力（40%權重）
- 平均營收年增率（60分）
- 成長穩定性（40分）

#### 配息穩定性（20%權重）
- 配息連續性（50分）
- 配息穩定性（50分）

### 評等標準

| 評等 | 分數 | 說明 |
|------|------|------|
| A+ | 85+ | 優質潛力股 |
| A | 75-84 | 良好潛力股 |
| B+ | 65-74 | 中等潛力股 |
| B | 55-64 | 一般潛力股 |
| C+ | 45-54 | 觀察股票 |
| C | 35-44 | 風險股票 |
| D | <35 | 高風險股票 |

### EPS預估

**預估公式**：
```
預估EPS = (最近3個月營收 × 歷史平均淨利率) ÷ 流通股數
```

## 🌐 Web介面功能

### 原有功能
- 📊 市場總覽
- 🔍 股票查詢
- 📈 股價圖表（K線圖）
- 🏆 漲跌幅排行榜

### 新增功能
- 🎯 **潛力股分析頁面**: 排行榜、統計圖表
- 💰 **EPS預估顯示**: 在股票詳細頁面
- 📊 **潛力評分顯示**: 評等、各項分數
- 🚀 **一鍵分析**: 為特定股票執行分析

## ⚙️ 參數配置

### 批次大小建議

| 資料類型 | 建議值 | 說明 |
|---------|-------|------|
| 股價資料 | 5-10 | API限制較寬鬆 |
| 月營收 | 5 | 中等限制 |
| 財務報表 | 3 | 限制較嚴格 |

### 常用參數

```bash
--batch-size 5          # 批次大小
--start-date 2015-01-01 # 開始日期
--end-date 2025-12-31   # 結束日期
--skip-threshold 90     # 跳過閾值(%)
--stock-id 2330         # 指定股票
--top 50               # 分析股票數量
```

## 🔍 故障排除

### 常見問題

1. **402 API限制**: 系統自動等待70分鐘
2. **資料庫鎖定**: 檢查是否有其他程序使用
3. **記憶體不足**: 降低批次大小
4. **網路問題**: 檢查連線，系統會自動重試

### 日誌檢查

```bash
# 主要日誌
tail -f logs/collect_all_10years.log

# 股價收集日誌
tail -f logs/collect_stock_prices_smart.log

# 潛力股分析日誌
tail -f logs/analyze_potential_stocks.log
```

## 📊 效能資訊

### 預估執行時間
- **股價資料**: 6-8小時（含等待）
- **基本面資料**: 2-4小時（含等待）
- **總計**: 8-12小時

### 系統需求
- Python 3.8+
- 8GB+ RAM
- 10GB+ 硬碟空間
- 穩定網路連線

## 🎉 使用範例

### 完整執行流程

```bash
# 1. 進入目錄
cd taiwan_stock_system

# 2. 啟動收集（終端1）
python scripts/collect_all_10years.py --batch-size 5

# 3. 啟動監控（終端2）
python monitor_collection.py

# 4. 等待完成（8-12小時）

# 5. 檢查狀態
python check_status.py

# 6. 啟動Web介面
python run.py
```

### 定期更新

```bash
# 每月更新營收
python scripts/collect_monthly_revenue.py --start-date 2025-01-01

# 重新分析潛力股
python scripts/analyze_potential_stocks.py --top 50
```

## 📞 技術支援

### 相依套件
```bash
pip install streamlit pandas numpy plotly loguru requests
```

### 重要文件
- `database_expansion_plan.md`: 完整技術文件
- `logs/`: 所有執行日誌
- `data/taiwan_stock.db`: SQLite資料庫

---

## 🎯 總結

**台股十年資料收集系統**為您提供：

✅ **完整資料**: 十年台股多維度資料  
✅ **智能收集**: 自動化處理API限制  
✅ **潛力分析**: 多維度股票評分系統  
✅ **Web介面**: 美觀的分析介面  
✅ **實時監控**: 收集進度即時追蹤  

**立即開始您的台股投資分析之旅！** 🚀📈💎
