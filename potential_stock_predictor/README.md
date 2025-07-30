# 🚀 潛力股預測系統

基於台灣股票系統的機器學習預測模組，用於識別具有潛力的股票。

## 🎯 系統目標

預測在財務資料公布後**20個交易日內股價上漲超過5%**的股票，幫助投資者識別潛力股。

## ✅ 系統狀態

**🎉 系統已完全建立並測試通過！**

- ✅ **資料處理**: 2,192個股票，24個核心特徵
- ✅ **模型訓練**: Random Forest (AUC: 0.647, F1: 0.726)
- ✅ **預測服務**: 成功生成TOP 20潛力股排行榜
- ✅ **用戶介面**: 零記憶負擔的選單系統
- ✅ **文檔完整**: 快速上手指南和詳細說明

**最新預測結果**: 茂迪(6244) 98.5%機率、聯合再生(3576) 98.1%機率

## 🚀 快速開始

### ⚡ 一鍵啟動（推薦）

```bash
cd potential_stock_predictor
python start.py
```

然後跟著選單操作：
1. 選單 1 → 1 (快速測試)
2. 選單 2 → 4 (批次處理資料)
3. 選單 3 → 1 (訓練模型)
4. 選單 4 → 1 (生成排行榜)

**🎯 5分鐘完成設置，立即獲得潛力股排行榜！**

### 📋 選單系統功能

- **🧪 系統測試**: 快速測試、完整測試、基本示範
- **🔬 資料處理**: 特徵生成、目標變數生成、批次處理
- **🤖 模型訓練**: 基本模型、所有模型、超參數調校
- **🔮 執行預測**: 排行榜生成、特定股票預測
- **📊 查看結果**: 最新排行榜、歷史預測、性能報告

### ⚡ 命令列快速執行

```bash
# 生成特徵資料
python simple_features.py 2024-06-30

# 生成目標變數
python simple_targets.py 2024-01-01 2024-06-30

# 訓練模型
python simple_train.py data/features/features_2024-06-30.csv data/targets/targets_quarterly_2024-06-30.csv

# 生成排行榜
python simple_predict.py ranking random_forest 20
```

## ✨ 主要功能

### 🔬 特徵工程
- **月營收特徵**: YoY成長率、MoM成長率、連續成長月數
- **財務比率特徵**: ROE、ROA、毛利率、營業利益率
- **現金流特徵**: 營運現金流、自由現金流、現金流比率
- **技術指標特徵**: 股價波動率、RSI、動量指標

### 🤖 機器學習模型
- **LightGBM**: 梯度提升決策樹
- **XGBoost**: 極端梯度提升
- **Random Forest**: 隨機森林
- **Logistic Regression**: 邏輯回歸

### 📊 預測服務
- 單一股票預測
- 批次股票預測
- 潛力股排行榜生成
- 預測結果歷史追蹤

## 📁 專案結構

```
potential_stock_predictor/
├── config/                 # 配置檔案
│   └── config.py           # 主配置檔案
├── data/                   # 資料目錄
│   ├── raw/               # 原始資料
│   ├── processed/         # 處理後資料
│   ├── features/          # 特徵資料
│   └── predictions/       # 預測結果
├── models/                 # 訓練好的模型
├── src/                    # 核心程式碼
│   ├── features/          # 特徵工程
│   │   ├── feature_engineering.py
│   │   └── target_generator.py
│   ├── models/            # 模型訓練與預測
│   │   ├── model_trainer.py
│   │   └── predictor.py
│   └── utils/             # 工具模組
│       ├── database.py
│       ├── logger.py
│       └── helpers.py
├── notebooks/              # Jupyter 分析筆記本
├── tests/                  # 測試檔案
├── main.py                 # 主執行程式
├── requirements.txt        # 依賴套件
└── README.md              # 說明文檔
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd potential_stock_predictor
pip install -r requirements.txt
```

### 2. 初始化配置

```python
from config.config import ensure_directories
ensure_directories()
```

### 3. 生成特徵和目標變數

```bash
# 生成特徵
python main.py generate-features --date 2024-06-30

# 生成目標變數
python main.py generate-targets --start-date 2022-01-01 --end-date 2024-06-30 --frequency quarterly
```

### 4. 訓練模型

```bash
python main.py train-models --features-file data/features/features_2024-06-30.csv --targets-file data/targets/targets_quarterly_2024-06-30.csv
```

### 5. 執行預測

```bash
# 預測特定股票
python main.py predict --stock-ids 2330,2317,2454 --model lightgbm

# 生成潛力股排行榜
python main.py ranking --top-k 50 --model lightgbm
```

## 💻 程式化使用

### 快速預測

```python
import potential_stock_predictor as psp

# 快速預測潛力股
results = psp.quick_predict(stock_ids=['2330', '2317'], model_type='lightgbm')
print(results)

# 訓練所有模型
training_results = psp.train_models()
```

### 詳細使用

```python
from potential_stock_predictor.src.features.feature_engineering import FeatureEngineer
from potential_stock_predictor.src.models.predictor import Predictor

# 特徵工程
feature_engineer = FeatureEngineer()
features = feature_engineer.generate_features('2330', '2024-06-30')

# 預測
predictor = Predictor()
prediction = predictor.predict_single_stock('2330')
ranking = predictor.generate_potential_stock_ranking(top_k=20)
```

## 📊 資料來源

系統使用台灣股票系統資料庫中的以下資料：

- **stock_prices**: 股價資料（開高低收、成交量）
- **monthly_revenues**: 月營收資料
- **financial_statements**: 綜合損益表
- **balance_sheets**: 資產負債表
- **cash_flow_statements**: 現金流量表

## 🔧 配置說明

### 目標變數配置

```python
FEATURE_CONFIG = {
    'target_definition': {
        'prediction_days': 20,      # 預測未來20個交易日
        'target_return': 0.05,      # 目標漲幅5%
        'min_trading_days': 15      # 最少需要15個交易日的資料
    }
}
```

### 模型配置

```python
MODEL_CONFIG = {
    'model_types': ['lightgbm', 'xgboost', 'random_forest', 'logistic_regression'],
    'default_model': 'lightgbm',
    'model_version': 'v1.0'
}
```

### 預測配置

```python
PREDICTION_CONFIG = {
    'confidence_threshold': 0.6,   # 預測信心閾值
    'top_k_stocks': 50,           # 排行榜股票數量
    'exclude_patterns': ['00'],    # 排除00開頭的股票（ETF）
}
```

## 🧪 測試

```bash
# 執行所有測試
python main.py test

# 執行特定模組測試
python main.py test --module test_feature_engineering

# 直接執行測試
python -m pytest tests/ -v
```

## 📈 性能指標

模型評估使用以下指標：

- **Accuracy**: 準確率
- **Precision**: 精確率
- **Recall**: 召回率
- **F1-Score**: F1分數
- **ROC AUC**: ROC曲線下面積
- **PR AUC**: Precision-Recall曲線下面積

### 🎯 最新測試結果

**資料統計**:
- 處理股票數: 2,192 個
- 特徵數量: 24 個核心特徵
- 訓練樣本: 4,278 個
- 正樣本比例: 57.81%

**模型性能**:
- **Random Forest**: AUC 0.647, F1 0.726
- **Logistic Regression**: AUC 0.644, F1 0.726

**預測結果**:
- 預測為潛力股: 1,423 個 (64.9%)
- 平均預測機率: 0.595
- TOP 5 潛力股:
  1. 茂迪(6244) - 98.5%機率
  2. 聯合再生(3576) - 98.1%機率
  3. 喬鼎(3057) - 97.7%機率
  4. 國碩(2406) - 97.5%機率
  5. 松瑞藥(4167) - 97.1%機率

## 🔍 特徵重要性

根據最新訓練結果，TOP 10 重要特徵：

1. **price_volatility** (9.53%) - 價格波動率
2. **momentum_20** (6.37%) - 20日動量
3. **revenue_stability_cv** (6.27%) - 營收穩定性
4. **volume_ma_20** (5.60%) - 20日成交量均線
5. **stock_id_numeric** (5.42%) - 股票代碼數值
6. **volume_ma_10** (5.25%) - 10日成交量均線
7. **price_vs_ma_5** (5.11%) - 價格相對5日均線
8. **price_vs_ma_20** (4.99%) - 價格相對20日均線
9. **volume_vs_ma_20** (4.85%) - 成交量相對20日均線
10. **volume_ma_5** (4.81%) - 5日成交量均線

## 📚 完整文檔

- **QUICKSTART.md** - 5分鐘快速上手指南
- **USAGE.md** - 詳細使用說明和選單功能
- **INSTALL.md** - 安裝指南和環境設置
- **README.md** - 本文檔，系統總體介紹

## 📝 注意事項

1. **資料品質**: 確保資料庫中有足夠的歷史資料
2. **模型更新**: 建議定期重新訓練模型以保持預測準確性
3. **風險提醒**: 預測結果僅供參考，投資決策需謹慎
4. **ETF排除**: 系統自動排除00開頭的ETF股票

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 📞 聯絡資訊

- 專案維護者: Taiwan Stock System Team
- 電子郵件: [your-email@example.com]
- 專案連結: [https://github.com/your-username/taiwan-stock-system]

---

**⚠️ 免責聲明**: 本系統提供的預測結果僅供參考，不構成投資建議。投資有風險，決策需謹慎。
