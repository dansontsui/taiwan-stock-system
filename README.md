# 📈 台股歷史股價系統

一個完整的台灣股市歷史資料分析系統，支援10年歷史股價資料收集、查詢、分析和視覺化。

## 🎯 系統特色

- **完整歷史資料**: 支援10年台股歷史資料收集
- **多元股票支援**: 上市、上櫃股票及ETF
- **即時查詢**: 快速股價查詢和統計分析
- **排行榜功能**: 漲跌幅、成交量排行
- **互動式介面**: 命令列和Web介面
- **資料視覺化**: K線圖、成交量圖表
- **ETF配息追蹤**: 完整的ETF配息記錄

## 🏗️ 系統架構

```
台股歷史股價系統
├── 資料收集層 (FinMind API)
├── 資料儲存層 (SQLite)
├── 業務邏輯層 (查詢服務)
├── 介面層 (Web + CLI)
└── 視覺化層 (圖表)
```

## 📊 資料來源

- **主要資料源**: [FinMind API](https://finmindtrade.com/)
- **資料類型**: 股價、成交量、配息資料
- **更新頻率**: 每日更新
- **資料範圍**: 2015年至今 (10年+)

## 🚀 快速開始

### 1. 安裝依賴套件

```bash
# 安裝基本套件
pip install pandas requests tqdm loguru

# 安裝Web介面套件 (可選)
pip install streamlit plotly
```

### 2. 系統初始化

```bash
# 初始化資料庫
python scripts/init_database.py
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
├── scripts/               # 腳本
│   ├── init_database.py   # 資料庫初始化
│   └── collect_data.py    # 資料收集
├── logs/                  # 日誌檔案
├── config.py              # 配置檔案
├── simple_demo.py         # 簡單演示
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

## 📝 開發計畫

### 已完成功能 ✅
- [x] 資料庫設計與建立
- [x] FinMind API 資料收集
- [x] 基本查詢功能
- [x] 命令列介面
- [x] 股票排行榜
- [x] 互動式查詢

### 開發中功能 🚧
- [ ] Web 介面完善
- [ ] 技術指標計算
- [ ] 資料視覺化圖表
- [ ] 自動更新機制

### 未來功能 📋
- [ ] 更多技術指標
- [ ] 投資組合分析
- [ ] 回測功能
- [ ] 警示系統
- [ ] API 服務

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

*最後更新: 2025-07-22*  
*版本: 1.0.0*  
*作者: Taiwan Stock System Team*
