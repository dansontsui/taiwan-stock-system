# 📈 台股潛力股分析系統

一個完整的台灣股市資料分析系統，支援十年歷史資料收集、智能潛力股分析、財務指標計算和視覺化展示。

## 🎯 系統特色

### 🚀 **整合式資料收集系統** (NEW!)
- **一鍵完整收集**: 整合所有散落功能，從12.5%提升至100%整合度
- **五階段收集流程**: 基礎資料→財務報表→資產負債→股利資料→潛力分析
- **智能等待機制**: 遇到API限制自動等待70分鐘
- **增量收集**: 只收集缺失資料，避免重複請求
- **實時監控**: 即時顯示收集進度和API狀態
- **跨平台支援**: 完全支援 Windows、macOS、Linux
- **友善選單介面**: 12個選項的分類選單，操作更直觀

### � **股票財務分析報告生成器** (NEW!)
- **一鍵生成Excel報告**: 輸入股票代號，自動生成完整財務分析
- **6大工作表**: 基本資訊、月營收、季度財務、年度財務、股利政策、潛力分析
- **專業格式化**: 千分位符號、百分比格式、表格美化、自動調整欄寬
- **Mac完全兼容**: UTF-8編碼，無cp950問題，完美支援macOS
- **智能錯誤處理**: 缺失資料自動標註"無資料"，容錯查詢機制
- **測試驗證**: 已成功生成台積電(2330)完整財務分析報告

### �📅 **每日增量更新系統** (NEW!)
- **智能檢測**: 自動檢測各類資料的最後更新時間
- **增量更新**: 只收集從上次更新到今日的缺失資料
- **一鍵執行**: 簡單命令保持資料庫最新狀態
- **Web整合**: 在系統狀態頁面直接執行每日更新
- **完整日誌**: 詳細的執行記錄和統計摘要
- **進度顯示**: 實時進度條和任務狀態顯示

### 📊 **智能資料統計系統** (NEW!)
- **資料品質分析**: 市場分布、完整度統計、熱門股票
- **趨勢分析**: 近期資料增長、潛力股評分分布
- **實時監控**: 自動檢測收集完成狀態，30秒更新頻率
- **Web可視化**: 直觀的統計圖表和指標
- **批次大小優化**: 預設批次大小調整為50，提升收集效率

### 🎯 **FinMind風格個股分析系統** (NEW!)
- **專業級設計**: 仿FinMind的現代化介面設計
- **五大分析標籤**: 總覽、技術分析、基本面、現金流、評分
- **完整技術指標**: RSI、MACD、移動平均線、布林通道
- **現金流分析**: 營運、投資、融資現金流完整分析
- **智能評分系統**: A+到D級評等，多維度潛力評估
- **即時分析功能**: 可直接在Web介面執行潛力股分析

### 📊 **核心功能**
- **完整歷史資料**: 支援10年台股歷史資料
- **多元股票支援**: 上市、上櫃股票及ETF
- **即時查詢**: 快速股價查詢和統計分析
- **排行榜功能**: 漲跌幅、成交量排行
- **互動式介面**: Streamlit Web介面，FinMind風格設計
- **資料視覺化**: 增強版K線圖、技術指標圖表、現金流分析圖

## 🏗️ 系統架構

```
台股潛力股分析系統
├── 整合式收集層 (NEW! 100%整合)
│   ├── 基礎資料收集 (股價、月營收、現金流)
│   ├── 財務報表收集 (綜合損益表)
│   ├── 資產負債收集 (資產負債表、財務比率)
│   ├── 股利資料收集 (股利政策、除權除息)
│   └── 潛力股分析 (評分排名)
├── 友善介面層 (NEW!)
│   ├── 12選項分類選單
│   ├── 跨平台啟動腳本
│   ├── 命令列參數支援
│   └── 即時進度顯示
├── 每日增量更新層
│   ├── 智能檢測機制
│   ├── 增量資料收集
│   ├── 進度顯示系統
│   ├── 自動潛力分析更新
│   └── Web介面整合
├── 資料儲存層 (SQLite)
│   ├── 股價資料表
│   ├── 財務報表表
│   ├── 資產負債表
│   ├── 股利政策表
│   ├── 財務比率表
│   └── 潛力股評分表
├── 智能分析層
│   ├── 財務比率計算
│   ├── 潛力股評分
│   └── EPS預估
├── Web介面層 (Streamlit)
│   ├── FinMind風格個股分析
│   ├── 五大分析標籤頁
│   ├── 潛力股排行榜
│   ├── 每日更新狀態
│   └── 智能資料統計
└── 監控層
    ├── 實時進度監控
    ├── API狀態檢測
    ├── 智能等待管理
    └── 每日更新監控
```

## 📊 資料來源與範圍

- **主要資料源**: [FinMind API](https://finmindtrade.com/)
- **資料類型**: 股價、財務報表、月營收、股利政策、財務比率
- **收集期間**: 2015-2025年 (十年完整資料)
- **資料量**: 預估200萬筆以上
- **更新方式**: 智能增量更新

## 🚀 快速開始

### ⚡ 整合式資料收集（推薦）

```bash
# 1. 安裝依賴套件
pip install pandas requests tqdm loguru streamlit plotly

# 2. 使用友善選單介面
python start.py

# 3. 或直接執行完整收集
python c.py complete

# 4. 測試模式（推薦新手）
python c.py complete-test

# 5. 啟動Web介面
python run.py
```

**全新體驗！** 整合式系統提供12個選項的分類選單，從基礎到進階一應俱全。

### 🎯 個別功能收集

```bash
# 財務報表資料收集
python c.py financial

# 資產負債表資料收集
python c.py balance

# 股利相關資料收集
python c.py dividend

# 潛力股分析
python c.py analysis

# 基礎資料收集
python c.py all      # 所有股票
python c.py main     # 主要股票
python c.py test     # 測試模式
```

### � 生成股票財務分析報告 (NEW!)

```bash
# 生成單一股票完整財務分析報告
python generate_stock_report.py 2330  # 台積電
python generate_stock_report.py 0050  # 元大台灣50
python generate_stock_report.py 2454  # 聯發科

# 測試報告生成器功能
python test_report_generator.py

# 輸出檔案格式
# {股票代號}_{股票名稱}_財務分析報告_{日期}.xlsx
# 包含6個工作表: 基本資訊、月營收、季度財務、年度財務、股利政策、潛力分析
```

**Mac用戶**: 完全支援macOS，無編碼問題！

### �📅 每日增量更新（推薦）

```bash
# 每日執行一次，保持資料最新
python scripts/collect_daily_update.py

# 或使用快速腳本
python daily_update.py

# 同時啟動監控
python monitor_collection.py
```

**每日更新特色**：
- 🤖 **智能檢測**: 自動檢測需要更新的資料類型
- ⏰ **智能等待**: 遇到402錯誤自動等待70分鐘
- 📊 **進度顯示**: 實時顯示執行進度和狀態
- 🌐 **Web整合**: 可在Web介面直接執行
- 📈 **統計摘要**: 詳細的執行結果和資料統計

### 📋 傳統方式

```bash
# 1. 初始化資料庫
python scripts/init_database.py

# 2. 收集基本股票資料
python scripts/collect_stocks.py
```

### 3. 收集資料

#### 🎯 方式A: 互動式選單 (推薦)
```bash
python scripts/menu.py
```
**不用記命令，點選即可！包含所有功能的友善介面。**

#### 🛠️ 方式B: 命令列操作
```bash
# 方式1: 收集測試資料 (24檔精選股票，近1個月)
python scripts/collect_data.py --test

# 方式2: 收集主要股票 (上市+上櫃+00開頭ETF，3,782檔，測試模式)
python scripts/collect_data.py --main-stocks --test

# 方式3: 收集指定股票
python scripts/collect_data.py --stocks 2330 0050 8299

# 方式4: 收集主要股票10年資料 (上市+上櫃+00開頭ETF)
python scripts/collect_data.py --main-stocks
```

### 4. 啟動系統

```bash
# 命令列版本
python simple_demo.py

# Web版本
python run.py
# 瀏覽器自動開啟 http://localhost:8501
```

## 📁 專案結構

```
taiwan_stock_system/
├── app/                    # 應用程式核心
│   ├── models/            # 資料模型
│   ├── services/          # 業務邏輯
│   │   ├── data_collector.py    # 資料收集
│   │   └── query_service.py     # 查詢服務
│   ├── utils/             # 工具模組
│   │   └── simple_database.py   # 資料庫管理
│   └── web/               # Web介面
│       └── dashboard.py         # Streamlit儀表板
├── data/                  # 資料目錄
│   └── taiwan_stock.db    # SQLite資料庫
├── scripts/               # 腳本目錄
│   ├── init_database.py   # 資料庫初始化
│   ├── collect_data.py    # 資料收集
│   ├── collect_all_10years.py    # 十年資料收集
│   ├── collect_daily_update.py   # 每日增量更新
│   ├── collect_financial_statements.py # 財務報表收集 (NEW!)
│   ├── collect_balance_sheets.py       # 資產負債表收集 (NEW!)
│   ├── collect_dividend_data.py        # 股利資料收集 (NEW!)
│   └── analyze_potential_stocks.py     # 潛力股分析
├── logs/                  # 日誌檔案
├── config.py              # 配置檔案
├── c.py                   # 整合式收集腳本 (NEW!)
├── start.py               # 跨平台啟動腳本 (NEW!)
├── simple_demo.py         # 簡單演示
├── daily_update.py        # 每日更新快速腳本
├── monitor_collection.py  # 收集監控系統
└── run.py                 # 系統啟動
```

## 💻 功能展示

### 系統資訊
```
📊 系統資訊
============================================================
股票數量: 4
股價記錄: 10,279
配息記錄: 35
資料庫大小: 1.75 MB
資料範圍: 2015-01-05 ~ 2025-07-23
```

### 市場總覽
```
🏢 市場總覽
============================================================
最新交易日: 2025-07-23
總股票數: 4
上漲股票: 0
下跌股票: 4
平盤股票: 0
總成交量: 2.19億
總成交金額: 700.36億
```

### 漲跌幅排行
```
🏆 今日漲幅排行 TOP 10
============================================================
排名   代碼       名稱           收盤價      漲跌       漲跌幅
-----------------------------------------------------------------
1    0050     元大台灣50       50.55    -0.35     -0.69%
2    0056     元大高股息        34.42    -0.38     -1.09%
3    2330     台積電          1130.00  -20.00     -1.74%
4    8299     群聯            498.00   -9.00     -1.78%
```

### 股票詳細資訊
```
📈 股票詳細資訊: 8299 (群聯)
============================================================
股票名稱: 群聯
市場: TWSE
是否為ETF: 否

最新價格資訊 (2025-07-23):
開盤價: 502.00
最高價: 510.00
最低價: 495.00
收盤價: 498.00
漲跌: -9.00
成交量: 105.88萬
成交金額: 52.84億

近30日統計:
最高價: 526.00
最低價: 463.00
平均價: 498.07
總成交量: 2.57億
交易天數: 22
```

### 股票清單選項
```
📋 股票清單模式
============================================================
預設模式 (24檔):     精選主要股票，快速測試
完整模式 (3,782檔):  所有上市上櫃股票，專業分析
  - 上市 (TWSE): 2,171檔
  - 上櫃 (TPEX): 1,611檔
  - ETF: 434檔
指定模式:           自選任意股票代碼
```

## 🔧 進階使用

### 股票清單選擇

```bash
# 預設清單 (24檔精選股票)
python scripts/collect_data.py --test

# 主要股票 (上市+上櫃+00開頭ETF，3,782檔)
python scripts/collect_data.py --main-stocks --test

# 指定股票 (不受清單限制)
python scripts/collect_data.py --stocks 2330 8299 3008 0050
```

### 收集完整歷史資料

```bash
# 收集10年完整資料 - 預設清單 (24檔)
python scripts/collect_data.py

# 收集10年完整資料 - 主要股票 (上市+上櫃+00開頭ETF，3,782檔)
python scripts/collect_data.py --main-stocks

# 收集指定時間範圍 - 主要股票
python scripts/collect_data.py --main-stocks --start-date 2000-01-01 --end-date 2024-12-31

# 收集指定股票的完整資料
python scripts/collect_data.py --stocks 2330 8299 --start-date 2020-01-01
```

### 資料庫管理

```bash
# 查看資料庫狀態
python -c "
from app.utils.simple_database import SimpleDatabaseManager
from config import Config
db = SimpleDatabaseManager(Config.DATABASE_PATH)
print(f'資料庫大小: {db.get_database_size()}')
print(f'股票數量: {db.get_table_count(\"stocks\")}')
print(f'股價記錄: {db.get_table_count(\"stock_prices\")}')
"
```

### API 使用範例

```python
from app.utils.simple_database import SimpleDatabaseManager
from app.services.query_service import StockQueryService
from config import Config

# 初始化
db_manager = SimpleDatabaseManager(Config.DATABASE_PATH)
query_service = StockQueryService(db_manager)

# 查詢股票資訊
stock_info = query_service.get_stock_info('2330')
print(f"股票名稱: {stock_info['stock_name']}")

# 查詢最新價格
latest_price = query_service.get_latest_price('2330')
print(f"最新價格: {latest_price['close_price']}")

# 查詢歷史價格
prices = query_service.get_stock_prices('2330', limit=10)
for price in prices:
    print(f"{price['date']}: {price['close_price']}")
```

## 📈 支援的股票

### 預設清單 (24檔)
**主要上市股票 (11檔)**
- **2330** 台積電、**2317** 鴻海、**2454** 聯發科
- **2412** 中華電、**2882** 國泰金、**2891** 中信金
- **2886** 兆豐金、**2303** 聯電、**2002** 中鋼
- **1301** 台塑、**8299** 群聯

**主要ETF (8檔)**
- **0050** 元大台灣50、**0056** 元大高股息
- **006208** 富邦台50、**00878** 國泰永續高股息
- **00881** 國泰台灣5G+、**00692** 富邦公司治理
- **00713** 元大台灣高息低波、**00757** 統一FANG+

**上櫃股票 (5檔)**
- **6223** 旺矽、**4966** 譜瑞-KY、**3443** 創意
- **6415** 矽力-KY、**4919** 新唐

### 主要股票清單 (3,782檔)
- **上市股票 (TWSE)**: 1,963檔
- **上櫃股票 (TPEX)**: 1,385檔
- **00開頭ETF**: 434檔
- **自動更新**: 從 FinMind API 即時獲取

### 使用建議
| 模式 | 股票數 | 收集時間 | 適用場景 |
|------|--------|----------|----------|
| **預設清單** | 24檔 | 5-10分鐘 | 測試、學習、演示 |
| **主要股票** | 3,782檔 | 2-6小時 | 專業分析、研究 |
| **指定股票** | 任意 | 視數量而定 | 特定需求 |

## ⚙️ 系統需求

### 基本需求
- Python 3.7+
- 網路連線 (資料收集時)
- 磁碟空間: 1-2 GB (完整資料)

### 必要套件
```bash
# 基本功能
pip install pandas requests tqdm loguru

# Web介面 (可選)
pip install streamlit plotly

# 或使用 requirements.txt
pip install -r requirements.txt
```

## 🔒 API 限制

### FinMind API
- **免費版**: 300次請求/小時
- **註冊版**: 600次請求/小時
- **付費版**: 更高限制

### 建議使用方式
- **預設清單**: 約240次請求 (1小時內完成)
- **主要股票**: 約38,000次請求 (需要60-100小時)
- **分批收集**: 避免超過API限制
- **智能跳過**: 避免重複收集已有資料

## 🛠️ 故障排除

### 常見問題

1. **資料庫初始化失敗**
   ```bash
   # 檢查目錄權限
   ls -la data/
   
   # 重新初始化
   rm -f data/taiwan_stock.db
   python scripts/init_database.py
   ```

2. **資料收集失敗**
   ```bash
   # 檢查網路連線
   ping api.finmindtrade.com
   
   # 使用測試模式
   python scripts/collect_data.py --test
   ```

3. **系統啟動失敗**
   ```bash
   # 檢查依賴套件
   python -c "import pandas, requests; print('OK')"
   
   # 使用簡單版本
   python simple_demo.py
   ```

---

# 🚀 十年資料收集系統詳細說明

## 📊 系統概述

十年資料收集系統是本專案的核心功能，能夠自動收集2015-2025年間的完整台股資料，包含股價、財務報表、月營收、股利政策等多維度資料。

## 🎯 主要功能

### 1. 全自動化收集
```bash
python scripts/collect_all_10years.py --batch-size 5
```

### 2. 智能等待機制
- 自動檢測402 API限制錯誤
- 智能等待70分鐘後自動重試
- 顯示等待進度和剩餘時間

### 3. 增量收集
- 檢測缺失的資料範圍
- 只收集缺失資料，避免重複
- 大幅提升收集效率

### 4. 實時監控
```bash
python monitor_collection.py
```

### 5. 潛力股分析
```bash
python scripts/analyze_potential_stocks.py --top 50
```

### 6. 每日增量更新 (NEW!)
```bash
# 基本執行
python scripts/collect_daily_update.py

# 自訂參數
python scripts/collect_daily_update.py --batch-size 5 --days-back 7

# 快速執行
python daily_update.py
```

**每日更新功能**：
- **股價資料**: 從最後收集日期到今日的增量更新
- **月營收資料**: 檢查是否有新的月份資料需要收集
- **財務報表**: 在財報公布期間檢查新的季報資料
- **股利政策**: 在股利公布期間（3-8月）檢查新的配息資料
- **潛力分析**: 收集完成後自動更新潛力股分析

## � 實際收集資料統計

**當前資料庫狀態**（最新更新 2025-07-25）：

| 資料類型 | 實際數量 | 說明 |
|---------|---------|------|
| 股票基本資料 | 10筆 | 精選股票 |
| 股價資料 | 25,716筆 | 十年歷史股價 |
| 月營收資料 | 603筆 | 每月營收及成長率 |
| 綜合損益表 | 3,029筆 | 季報、年報財務資料 |
| 資產負債表 | 15,461筆 | 財務結構資料 |
| 股利政策 | 125筆 | 配息配股資料 |
| 財務比率 | 147筆 | 自動計算財務指標 |
| 潛力股評分 | 9筆 | 綜合評分分析 |

### 🎯 系統優化成果
- ✅ **emoji編碼問題已修復**: 完全支援Windows cp950編碼
- ✅ **智能增量更新**: 避免重複API請求，節省配額
- ✅ **營收成長率計算**: 已完成594筆記錄更新
- ✅ **跨平台兼容**: Windows、macOS、Linux完全支援

## 📈 預估收集容量

| 資料類型 | 預估數量 | 說明 |
|---------|---------|------|
| 股價資料 | 500,000筆 | 十年日K線資料 |
| 月營收資料 | 60,000筆 | 每月營收及成長率 |
| 綜合損益表 | 500,000筆 | 季報、年報財務資料 |
| 資產負債表 | 1,200,000筆 | 財務結構資料 |
| 股利政策 | 8,000筆 | 配息配股資料 |
| 財務比率 | 35,000筆 | 自動計算財務指標 |
| 潛力股評分 | 50筆 | 綜合評分分析 |

## 🎯 潛力股分析系統

### 評分維度
- **財務健康度**（40%）: 毛利率、營業利益率、淨利率、負債比率
- **成長潛力**（40%）: 營收年增率、成長穩定性
- **配息穩定性**（20%）: 配息連續性、配息穩定性

### 評等標準
- **A+** (85+分): 優質潛力股
- **A** (75-84分): 良好潛力股
- **B+** (65-74分): 中等潛力股
- **B** (55-64分): 一般潛力股
- **C+** (45-54分): 觀察股票
- **C** (35-44分): 風險股票
- **D** (<35分): 高風險股票

## 🌐 Web介面整合

系統已完全整合到原有的Streamlit Web介面中：

### 新增頁面
- **潛力股分析**: 排行榜、統計圖表、評分分布

### 增強功能
- **股票詳細頁面**: 顯示潛力評分、EPS預估
- **一鍵分析**: 為特定股票執行潛力分析

## 📚 詳細文件

- **完整使用指南**: `README_十年資料收集系統.md`
- **每日更新指南**: `README_每日更新功能.md` 🆕
- **快速開始**: `QUICKSTART.md`
- **技術文件**: `database_expansion_plan.md`

## 📝 開發計畫

### 已完成功能 ✅
- [x] 資料庫設計與建立
- [x] FinMind API 資料收集
- [x] 基本查詢功能
- [x] Streamlit Web介面
- [x] 股票排行榜
- [x] **十年資料收集系統**
- [x] **智能等待機制**
- [x] **潛力股分析系統**
- [x] **EPS預估功能**
- [x] **實時監控系統**
- [x] **每日增量更新系統**
- [x] **Web介面整合**
- [x] **進度顯示功能**
- [x] **智能資料統計**
- [x] **資料品質分析**
- [x] **股票財務分析報告生成器**
- [x] **Excel專業格式化**
- [x] **Mac跨平台兼容**
- [x] **智能容錯查詢**
- [x] **FinMind風格個股分析頁面**
- [x] **五大分析標籤頁系統**
- [x] **完整技術指標整合**
- [x] **現金流分析功能**
- [x] **批次大小優化(50)**
- [x] **整合式資料收集系統** 🆕 ✅
- [x] **12選項友善選單介面** 🆕 ✅
- [x] **跨平台啟動腳本** 🆕 ✅
- [x] **五階段完整收集流程** 🆕 ✅
- [x] **100%功能整合度** 🆕 ✅

### 開發中功能 🚧
- [ ] 更多技術指標
- [ ] 投資組合分析
- [ ] 回測功能
- [ ] 監控系統自動停止優化

### 未來功能 📋
- [ ] 機器學習預測模型
- [ ] 警示系統
- [ ] API 服務
- [ ] 行動版介面
- [ ] 資料收集排程系統

## 🖥️ 跨平台支援

### ✅ 完全支援的作業系統
- **Windows 10/11**: 完整測試，包含PowerShell執行政策處理
- **macOS**: 完全兼容，UTF-8編碼原生支援
- **Linux**: Ubuntu、CentOS、Debian等主流發行版

### 🔧 平台特定注意事項

#### Windows
- 已修復emoji編碼問題（cp950編碼兼容）
- 如遇PowerShell執行政策問題，建議使用cmd或VSCode終端
- 所有腳本已優化Windows兼容性

#### macOS
- 原生UTF-8支援，無編碼問題
- 建議使用Terminal.app或iTerm2
- Python 3.8+ 推薦使用Homebrew安裝

#### Linux
- 完全支援各主流發行版
- 建議Python 3.8+
- 可使用系統包管理器安裝依賴

### 📦 依賴安裝

```bash
# 所有平台通用
pip install -r requirements.txt

# macOS (推薦使用Homebrew)
brew install python3
pip3 install -r requirements.txt

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip
pip3 install -r requirements.txt
```

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發環境設置
```bash
git clone <repository>
cd taiwan_stock_system
python scripts/init_database.py
python scripts/collect_data.py --test
```

## 📄 授權條款

MIT License - 詳見 LICENSE 檔案

## 📞 聯絡資訊

如有問題或建議，請透過 GitHub Issues 聯絡。

---

*最後更新: 2025-07-31*
*版本: 1.7.0*
*重大更新: 整合式資料收集系統完全可用，功能整合度從12.5%提升至100%*
*新增功能: 12選項友善選單、跨平台啟動腳本、五階段完整收集流程*
*系統優化: 完整整合所有散落的資料收集功能，提供統一操作介面*
*測試驗證: 所有功能已通過完整測試，包含跨平台相容性驗證*
*作者: Taiwan Stock System Team*
