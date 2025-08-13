# Quick Start（操作指南）

本指南說明如何使用「長期存股績優股」篩選系統的操作順序與常用指令。

## 1) 建立 marts（品質/股利/估值）
- 指令（CLI）：
```
python -m quality_stock_system.cli build-marts --db data/taiwan_stock.db
```
- 日誌（中文）：會顯示建立 `mart_quality_factors_yearly`、`mart_dividend_stability`、`mart_valuation_snapshot` 的狀態。

## 2) 匯出清單（CSV/JSON）
- 指令（CLI）：
```
python -m quality_stock_system.cli export --profile conservative --top 100 --db data/taiwan_stock.db --year 2024 --as-of-date 2024-12-31
```
- 輸出路徑（ASCII）：
  - `quality_stock_system/data/quality_list_conservative.csv`（UTF-8-SIG）
  - `quality_stock_system/data/quality_list_conservative.json`
  - `quality_stock_system/data/quality_list_conservative_reasons.csv`（入選理由，中文欄位）
- 歷史寫入：
  - 每次 export 會自動把清單寫入 `quality_stock_system/data/history/quality_list_history.csv`
  - 欄位：profile, year, as_of_date, stock_id, rank, score, 指標欄位...
- 關於 year 與 as_of_date：
  - `--year`（評估年度鎖定）：用該年資料產生清單（建議回測使用）
  - `--as-of-date`：標記清單生成日期（字串標記，便於追蹤）

## 3) 使用操作選單（推薦）
- 一鍵入口：
```
python -m quality_stock_system.menu
```
- 或（等效）：
```
python -c "from quality_stock_system.menu import run_menu; run_menu()"
```
- 選單操作順序（建議）：
  1. 選 1 → 建立 marts（輸入資料庫路徑或使用預設）
  2. 選 2 → 匯出清單（選擇 profile 與 Top N、輸入資料庫路徑）
  3. 選 8 → 批量匯出年度清單（輸入起訖年，系統自動寫入歷史；reasons 會以追加模式累積多年度）
  4. 選 6 → 年度等權重再平衡回測（預設含息、停損 15%；可輸入停利% 與 移動停損%）
  5. 選 9 → 參數網格掃描（輸出 backtest_param_sweep.csv，用來挑選最佳 sl/tp/tsl）
  6. 選 10 → 用掃描結果最佳參數一鍵回測（目標 annualized/mdd/annualized_minus_half_mdd）
  7. 視需要選 3/4/5 → 檢視輸出、查看模板與環境參數
  8. 選 7 → 生成清單視覺化 HTML（quality_list_report.html，前 50 名）

## 範例：一次建立 2018~2024 年的清單，然後跑動態回測（含息 + 停損/停利/移動停損）
- CLI 批次（Windows PowerShell）：
```
$years = 2018..2024
foreach ($y in $years) {
  python -m quality_stock_system.cli export --profile conservative --top 100 --db data/taiwan_stock.db --year $y --as-of-date "$y-12-31"
}
```
- 回測（選單 6）：
  - 預設含息、停損 15%，可另輸入停利%與移動停損%
- 參數網格掃描（選單 9）：
  - 擴大網格：sl=[10%,15%,20%]、tp=[無,20%,30%,50%]、tsl=[無,10%,15%]
  - 總共 3×4×3 = 36 組參數組合（包含不停利/不移動停損）
  - 結果 CSV：quality_stock_system/data/backtest_param_sweep.csv
- 一鍵回測（選單 10）：
  - 自動讀取 backtest_param_sweep.csv，依目標挑選最佳 sl/tp/tsl 後回測
  - 目標選項：annualized（年化最大）/ mdd（回撤最小）/ annualized_minus_half_mdd（年化 − 0.5×|MDD| 最大）
- 報表說明：
  - backtest_portfolio_report.csv 的「期末資金」是含息的（包含股票股利+現金股利的資產價值）
  - 股票股利換算：1.2元 = 12%（假設面額10元），會調整持股數量
- 單一標的診斷工具（處理股票股利/現金股利對停損的影響）：
  - 用於驗證除權價跳水是否會誤觸停損（資產價值法）
  - 基本用法（DB 在專案根 data/）：
    - python -m quality_stock_system.tools.diagnose_stock_value_sim data/taiwan_stock.db 1808 2024 0.15
  - 指定價格表/欄位用法：
    - python -m quality_stock_system.tools.diagnose_stock_value_sim data/taiwan_stock.db 1808 2024 0.15 --price-table stock_prices --date-col date --price-col close_price
  - 詳細軌跡（--verbose）：
    - python -m quality_stock_system.tools.diagnose_stock_value_sim data/taiwan_stock.db 1808 2024 0.15 --price-table stock_prices --date-col date --price-col close_price --verbose

## 4) Profile（規則模板）說明
- conservative（穩健）
  - 門檻（摘要）：`roe_5y_avg >= 10`、`revenue_cagr_5y >= 0.03`、`cash_div_years >= 3`、估值分位 `pe_pct_5y/pb_pct_5y <= 0.6`
  - 加權（摘要）：ROE 40%、CAGR 30%、配息年數 30%
- value（價值）
  - 門檻：`pe_pct_5y/pb_pct_5y <= 0.4`
  - 加權：valuation 權重較高

## 5) 匯出檔案編碼與跨平台
- CSV 採用 UTF-8-SIG，Windows Excel 開啟不會出現亂碼
- 檔名、欄位名使用 ASCII，避免 cp950 問題
- CLI 與日誌使用中文描述
- 系統會同步將所有 CLI 日誌寫入：`quality_stock_system/data/logs/qs.log`

## 6) 常見問題
- 看不到輸出？先執行 build-marts
- 缺某些資料表？系統會顯示中文警告並跳過；補齊資料後重跑 build-marts
- 想調整門檻？請參考 `quality_stock_system/rules.py` 或後續加入 JSON 規則檔

