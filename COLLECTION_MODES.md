# 📊 股票收集模式說明

## 🎯 三種收集模式

### 1. 📋 預設清單 (24檔)
**精選的主要股票和ETF**

```bash
python scripts/collect_data.py --test
```

**包含股票:**
- **上市股票 (11檔)**: 2330台積電、2317鴻海、2454聯發科等
- **ETF (8檔)**: 0050元大台灣50、0056元大高股息等  
- **上櫃股票 (5檔)**: 6223旺矽、4966譜瑞-KY等

**特點:**
- ✅ 收集速度快 (5-10分鐘)
- ✅ 適合測試和學習
- ✅ API請求少 (~240次)

---

### 2. 🏢 主要股票 (3,782檔) ⭐ **推薦**
**上市公司 + 上櫃公司 + 00開頭ETF**

```bash
python scripts/collect_data.py --main-stocks --test
```

**包含股票:**
- **上市股票 (TWSE)**: 1,963檔
- **上櫃股票 (TPEX)**: 1,385檔
- **00開頭ETF**: 434檔 (如 0050、0056、00878等)

**特點:**
- ✅ 涵蓋主要投資標的
- ✅ 排除權證、特別股等
- ✅ 適合專業分析
- ⚠️ 收集時間較長 (2-6小時)
- ⚠️ API請求多 (~38,000次)

---

### 3. 🎯 指定股票 (任意數量)
**自選任意股票代碼**

```bash
python scripts/collect_data.py --stocks 2330 8299 0050 0056
```

**特點:**
- ✅ 完全自定義
- ✅ 不受清單限制
- ✅ 收集時間可控
- ✅ 適合特定需求

---

## 🚀 推薦使用方式

### 🧪 初次使用
```bash
# 1. 先測試預設清單
python scripts/collect_data.py --test

# 2. 確認系統正常後，收集主要股票
python scripts/collect_data.py --main-stocks --test
```

### 💼 專業使用
```bash
# 收集主要股票的完整10年資料
python scripts/collect_data.py --main-stocks --skip-existing

# 分批收集 (推薦，自動處理API限制)
python scripts/collect_batch.py --test
```

### 🎯 特定需求
```bash
# 只收集台積電和幾檔ETF
python scripts/collect_data.py --stocks 2330 0050 0056 00878

# 收集特定時間範圍
python scripts/collect_data.py --main-stocks --start-date 2020-01-01 --end-date 2024-12-31
```

## ⚡ 效率優化功能

### 🔄 智能跳過
**自動跳過已有完整資料的股票**

```bash
# 啟用跳過功能 (推薦)
python scripts/collect_data.py --main-stocks --skip-existing

# 分批收集預設啟用跳過功能
python scripts/collect_batch.py --test
```

### ⏰ 智能等待
**遇到API限制時智能計算等待時間**

- 原本固定等待: 65分鐘
- 智能等待: 5-55分鐘 (根據實際時間)
- 平均節省: 30-50分鐘

### 📦 分批收集
**自動處理大量股票收集**

```bash
# 分批收集主要股票 (推薦)
python scripts/collect_batch.py --test --batch-size 200
```

## 📊 模式比較

| 模式 | 股票數 | 收集時間 | API請求 | 適用場景 |
|------|--------|----------|---------|----------|
| **預設清單** | 24檔 | 5-10分鐘 | ~240次 | 測試、學習、演示 |
| **主要股票** | 3,782檔 | 2-6小時 | ~38,000次 | 專業分析、研究 |
| **指定股票** | 任意 | 視數量而定 | 視數量而定 | 特定需求 |

## 🎯 您的需求: 上市櫃 + 00開頭ETF

**正確命令:**
```bash
# 測試模式
python scripts/collect_data.py --main-stocks --test

# 完整收集
python scripts/collect_data.py --main-stocks --skip-existing

# 分批收集 (推薦)
python scripts/collect_batch.py --test
```

**包含範圍:**
- ✅ 所有上市公司 (TWSE): 1,963檔
- ✅ 所有上櫃公司 (TPEX): 1,385檔
- ✅ 00開頭ETF: 434檔 (0050、0056、00878等)
- ❌ 排除: 其他ETF代碼 (006208、008XX等)
- ❌ 排除: 權證、特別股、存託憑證

## ⚠️ 重要提醒

### API限制
- **免費版**: 300次請求/小時
- **主要股票模式**: 需要約38,000次請求
- **建議**: 使用分批收集或付費API

### 收集策略
1. **先測試**: `--test` 模式驗證功能
2. **啟用跳過**: `--skip-existing` 避免重複收集
3. **分批處理**: 使用 `collect_batch.py` 自動處理API限制
4. **監控進度**: 查看日誌了解收集狀況

## 🎉 總結

- **您的需求**: 使用 `--main-stocks` 參數
- **推薦方式**: 分批收集腳本
- **最佳命令**: `python scripts/collect_batch.py --test`

這樣就能收集到所有上市櫃公司和00開頭的ETF了！ 🚀
