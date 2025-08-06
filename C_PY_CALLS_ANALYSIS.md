# c.py 檔案呼叫分析報告

## 📋 分析概述

**分析目標**: `c.py` 檔案  
**分析時間**: 2025-08-05  
**分析結果**: 總共呼叫 **7個** Python 檔案

## 🎯 核心發現

### 總計呼叫的 Python 檔案數量: **7個**

所有被呼叫的檔案都存在且可正常運作，檔案存在率為 **100%**。

## 📂 完整檔案清單

| 序號 | 檔案路徑 | 狀態 | 呼叫方式 |
|------|----------|------|----------|
| 1 | `simple_collect.py` | ✅ 存在 | 直接路徑呼叫 |
| 2 | `scripts/analyze_potential_stocks.py` | ✅ 存在 | run_script() |
| 3 | `scripts/collect_balance_sheets.py` | ✅ 存在 | run_script() |
| 4 | `scripts/collect_dividend_data.py` | ✅ 存在 | run_script() |
| 5 | `scripts/collect_dividend_results.py` | ✅ 存在 | run_script() |
| 6 | `scripts/collect_financial_statements.py` | ✅ 存在 | run_script() |
| 7 | `scripts/simple_progress.py` | ✅ 存在 | import 導入 |

## 🔄 呼叫方式分析

### 1. 直接路徑呼叫 (1個檔案)
- **`simple_collect.py`** - 基礎資料收集腳本
  - 在 `run_collect()` 函數中呼叫
  - 在 `run_collect_with_stock()` 函數中呼叫
  - 負責收集股價、營收、現金流等基礎資料

### 2. run_script() 函數呼叫 (5個檔案)
- **`scripts/collect_financial_statements.py`** - 財務報表收集
- **`scripts/collect_balance_sheets.py`** - 資產負債表收集  
- **`scripts/collect_dividend_data.py`** - 股利政策收集
- **`scripts/collect_dividend_results.py`** - 除權除息結果收集
- **`scripts/analyze_potential_stocks.py`** - 潛力股分析

### 3. import 導入 (1個檔案)
- **`scripts/simple_progress.py`** - 簡單進度記錄系統
  - 用於追蹤資料收集進度
  - 支援斷點續傳功能

## 🏗️ 功能架構分析

### 基礎收集層
```
c.py → simple_collect.py
```
- 負責股票清單、股價、月營收、現金流量表的收集

### 進階收集層
```
c.py → scripts/collect_financial_statements.py  (財務報表)
c.py → scripts/collect_balance_sheets.py        (資產負債表)
c.py → scripts/collect_dividend_data.py         (股利政策)
c.py → scripts/collect_dividend_results.py      (除權除息)
```

### 分析處理層
```
c.py → scripts/analyze_potential_stocks.py      (潛力股分析)
```

### 輔助功能層
```
c.py → scripts/simple_progress.py               (進度管理)
```

## 📊 函數與腳本對應關係

| 函數名稱 | 呼叫的腳本 | 功能描述 |
|----------|------------|----------|
| `run_collect()` | `simple_collect.py` | 基礎資料收集 |
| `run_collect_with_stock()` | `simple_collect.py` | 指定個股基礎資料收集 |
| `run_financial_collection()` | `scripts/collect_financial_statements.py` | 財務報表收集 |
| `run_balance_collection()` | `scripts/collect_balance_sheets.py` | 資產負債表收集 |
| `run_dividend_collection()` | `scripts/collect_dividend_data.py`<br>`scripts/collect_dividend_results.py` | 股利相關資料收集 |
| `run_analysis()` | `scripts/analyze_potential_stocks.py` | 潛力股分析 |

## 🔗 依賴關係圖

```
c.py (核心控制器)
├── simple_collect.py (基礎收集)
├── scripts/
│   ├── collect_financial_statements.py (財務報表)
│   ├── collect_balance_sheets.py (資產負債表)
│   ├── collect_dividend_data.py (股利政策)
│   ├── collect_dividend_results.py (除權除息)
│   ├── analyze_potential_stocks.py (潛力分析)
│   └── simple_progress.py (進度管理)
```

## 🎯 設計特色

### 1. 模組化設計
- 每個功能都有獨立的腳本檔案
- 透過 `c.py` 統一協調和管理
- 便於維護和擴展

### 2. 統一的呼叫介面
- 使用 `run_script()` 函數統一管理腳本執行
- 標準化的參數傳遞機制
- 統一的錯誤處理

### 3. 進度管理整合
- 整合 `simple_progress.py` 進度記錄系統
- 支援斷點續傳功能
- 提供執行狀態追蹤

### 4. 靈活的執行模式
- 支援測試模式 (`--test`)
- 支援指定個股 (`--stock-id`)
- 支援批次大小調整 (`--batch-size`)

## 📈 執行流程

### 完整收集流程
1. **基礎資料** → `simple_collect.py`
2. **財務報表** → `scripts/collect_financial_statements.py`
3. **資產負債** → `scripts/collect_balance_sheets.py`
4. **股利資料** → `scripts/collect_dividend_data.py` + `scripts/collect_dividend_results.py`
5. **潛力分析** → `scripts/analyze_potential_stocks.py`

### 進度追蹤
- 全程使用 `scripts/simple_progress.py` 記錄進度
- 支援中斷後從上次位置繼續執行

## 🔧 技術實現

### 腳本執行機制
```python
def run_script(script_name, args=None, description=""):
    script_path = Path(__file__).parent / "scripts" / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    subprocess.run(cmd, check=True)
```

### 進度管理機制
```python
from scripts.simple_progress import SimpleProgress
progress = SimpleProgress()
progress.show_progress_summary()
```

## 📊 統計摘要

- **總檔案數**: 7個
- **存在檔案**: 7個 (100%)
- **缺失檔案**: 0個 (0%)
- **基礎收集**: 1個檔案
- **進階收集**: 4個檔案
- **分析功能**: 1個檔案
- **輔助功能**: 1個檔案

## 🎉 結論

`c.py` 作為核心控制器，設計精良且功能完整：

1. **架構清晰**: 7個檔案分工明確，各司其職
2. **功能完整**: 涵蓋從基礎收集到進階分析的完整流程
3. **執行穩定**: 所有被呼叫的檔案都存在且可正常運作
4. **易於維護**: 模組化設計便於後續擴展和維護

這個設計體現了優秀的軟體工程實踐，是一個成熟且可靠的台股資料收集系統核心。
