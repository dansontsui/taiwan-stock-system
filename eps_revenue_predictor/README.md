# 📊 EPS與營收成長預測系統

## 🎯 專案概述

基於財務公式的EPS與營收成長預測系統，採用 **80% 財務公式 + 20% 專用型AI模型** 的混合預測方法。

### 核心功能
- 下個月營收成長預測
- 下季EPS成長預測  
- 基於4個核心特徵：EPS趨勢、營收成長率、毛利率變化、營業費用率變化
- 完整回測系統與詳細報告
- 專用型AI智能調整

### 測試股票
**2385 群光電子** - 作為系統開發與測試的主要標的

## 🏗️ 專案結構

```
eps_revenue_predictor/
├── config/                    # 配置管理
│   ├── settings.py           # 系統配置
│   └── formulas.py           # 財務公式定義
├── src/                      # 核心程式碼
│   ├── data/                 # 資料處理層
│   │   ├── database_manager.py
│   │   ├── data_collector.py
│   │   └── data_validator.py
│   ├── predictors/           # 預測引擎
│   │   ├── revenue_predictor.py
│   │   ├── eps_predictor.py
│   │   └── formula_engine.py
│   ├── analysis/             # 分析模組
│   │   ├── trend_analyzer.py
│   │   ├── ratio_analyzer.py
│   │   └── adjustment_engine.py
│   ├── models/               # 專用型AI模型
│   │   ├── adjustment_model.py
│   │   └── ensemble_predictor.py
│   ├── backtesting/          # 回測系統
│   │   ├── backtest_engine.py
│   │   ├── performance_metrics.py
│   │   └── report_generator.py
│   └── utils/                # 工具模組
│       ├── logger.py
│       ├── helpers.py
│       └── validators.py
├── tests/                    # 測試模組
├── reports/                  # 報告輸出
├── logs/                     # 日誌檔案
├── docs/                     # 文件
├── main.py                   # 主程式入口
├── requirements.txt          # 依賴套件
└── test_2385.py             # 2385測試腳本
```

## 🔧 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 測試2385群光電子
```bash
python test_2385.py
```

### 3. 執行主程式
```bash
python main.py
```

## 📈 預測方法

### 財務公式 (80%權重)
- **營收預測**: 趨勢外推 + 季節調整 + 年增率分析
- **EPS預測**: 營收預測 × 利潤率趨勢 ÷ 流通股數

### 專用型AI調整 (20%權重)  
- **調整因子**: 營收品質、利潤率穩定性、產業比較、市場環境
- **模型類型**: 輕量級梯度提升模型
- **調整範圍**: ±20%以內的微調

## 🎯 開發狀態

- [x] 專案結構建立
- [ ] 基礎配置系統
- [ ] 資料處理模組
- [ ] 財務公式引擎
- [ ] 專用型AI模型
- [ ] 回測系統
- [ ] 2385測試驗證

## 📊 測試目標

使用2385群光電子驗證：
1. 營收預測準確率 > 70%
2. EPS預測準確率 > 65%  
3. 方向預測準確率 > 75%
4. 系統穩定性與效能

---

**開發中** - 持續更新中...
