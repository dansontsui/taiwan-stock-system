# Project Status (taiwan-stock-system)

本文件記錄目前專案的重要狀態，提供新的 agent/協作者快速接手與延續記憶。

## 環境與路徑
- 專案根目錄：g:\WorkFolder\taiwan-stock-system
- 預設資料庫路徑（環境變數可覆蓋）：data/taiwan_stock.db
  - utils.DEFAULT_DB = os.environ.get('TS_DB_PATH', os.path.join('data','taiwan_stock.db'))
- 輸出資料夾：quality_stock_system/data
  - QS_OUTPUT_DIR（可用環境變數覆蓋）

## 主要功能模組與檔案
- quality_stock_system/menu.py
  - 互動選單：
    - 1) 建立 marts
    - 2) 匯出清單（CSV/JSON）
      - 會清除並重建 data/history/quality_list_history.csv
    - 3) 檢視輸出資料夾
    - 4) 查看規則模板（profiles）
    - 5) 顯示環境參數
    - 6) 年度回測（含息/停損/停利/移動停損；資金模擬：初始 100 萬等資金配置）
    - 7) 生成清單視覺化 HTML（示意）
    - 8) 批量匯出年度清單（會清除並重建 history 檔案，再逐年累積）
    - 9) 參數網格掃描（含 None：不停利/不移動停損）
    - 10) 用掃描結果最佳參數一鍵回測（可選目標 annualized/mdd/annualized_minus_half_mdd）

- quality_stock_system/export.py
  - export_quality_list(...) 產出：
    - quality_stock_system/data/quality_list_{profile}.csv
    - quality_stock_system/data/quality_list_{profile}.json
    - reasons（quality_list_{profile}_reasons.csv）支援批量年度追加
  - 寫入歷史：history.append_history(..., clear_first=...)；
    - 單次匯出（選單 2 / CLI export 未指定 year）會清除並重建歷史
    - 批量匯出（選單 8 / CLI bulk-export）由外層先清除，再逐年追加

- quality_stock_system/history.py
  - HIST_FILE = quality_stock_system/data/history/quality_list_history.csv
  - clear_history()：刪除歷史檔案
  - append_history(..., clear_first=False)：追加寫入（可選擇先清除）

- quality_stock_system/backtest.py
  - run_equal_weight_backtest(..., include_dividends=True, sl_pct=0.15, tp_pct=None, tsl_pct=None, initial_capital=1_000_000.0)
  - 特點：
    - 資金模擬：每年固定 100 萬，等資金分配到當年成分股
    - 含息（現金股利 + 股票股利）
      - dividend_policies 欄位：
        - 現金：cash_earnings_distribution（並相容 cash_earnings_distrubtion）
        - 股票：stock_earnings_distribution（並相容 stock_earnings_distrubtion）
      - 日期欄位優先使用：stock_ex_dividend_trading_date、cash_ex_dividend_trading_date（或 cash_dividend_payment_date）、ex_date、pay_date、announcement_date、record_date、date
      - 股票股利單位換算：元/股 → 比率；假設面額 10 元：ratio = value/10（例：1.2 元 → 0.12）
    - 停損/停利/移動停損：
      - 有日期時用「資產價值」判斷（price*shares + cash），避開除權價跳水誤觸
      - 無日期時使用保守近似：期末一次加總，提前出場不計
    - 匯總報表（backtest_portfolio_report.csv）欄位：年度、成分股數、期初資金、期末資金（整數）、年度報酬率、累積報酬值
    - 明細（backtest_portfolio_details.csv）：進出場、出場理由、含息/不含息報酬、股利

- quality_stock_system/sweep.py
  - sweep_params(...)：以固定資金與含息邏輯下，網格掃描 sl/tp/tsl 組合
  - CSV：quality_stock_system/data/backtest_param_sweep.csv

- quality_stock_system/best_params.py
  - pick_best_params(..., objective)：從 CSV 擇優（支援 None 參數）

- quality_stock_system/tools/diagnose_stock_value_sim.py
  - 單一標的診斷工具（資產價值法）：
    - 可指定價格表/欄位：--price-table / --date-col / --price-col
    - --verbose：輸出前/後 10 筆資產值軌跡（日期、px、shares、cash、val、events）

## 重要輸出檔案（一覽）
- 清單：
  - quality_stock_system/data/quality_list_{profile}.csv
  - quality_stock_system/data/quality_list_{profile}.json
  - quality_stock_system/data/quality_list_{profile}_reasons.csv（批量多年追加）
- 歷史：
  - quality_stock_system/data/history/quality_list_history.csv（選單2/8前會清空重建）
- 回測：
  - quality_stock_system/data/backtest_portfolio_report.csv（期末資金為含息/含股利資產）
  - quality_stock_system/data/backtest_portfolio_details.csv
  - quality_stock_system/data/backtest_param_sweep.csv

## 使用建議流程
1) 選 1 建 marts
2) 選 8 批量匯出多年度清單（reasons 會追加、多年度）
3) 選 6 回測（含息 + 停損15%，可輸入停利/移動停損）
4) 選 9 掃描參數（含 None 選項）
5) 選 10 用最佳參數一鍵回測
6) 如需檢查除權影響，用 diagnose_stock_value_sim（可加 --verbose）

## 資料庫結構（關鍵表與欄位）
- 價格表（名稱可變，預設 stock_prices）：
  - 欄位：stock_id, date, close_price（或 trade_date/close 等，診斷工具支援自動/自訂）
- 股利表：dividend_policies
  - 現金股利欄位：cash_earnings_distribution（相容 _distrubtion）
  - 股票股利欄位：stock_earnings_distribution（相容 _distrubtion）
  - 日期欄位：stock_ex_dividend_trading_date、cash_ex_dividend_trading_date、cash_dividend_payment_date、ex_date、pay_date、announcement_date、record_date、date
- marts：mart_quality_factors_yearly（自動偵測年度範圍用）

## 目前既知特別處理與假設
- 股票股利單位換算預設以面額 10 元轉成比例；若未來提供更精確定義，可調整換算
- 提前出場（有日期）時只計當日前的股利；無日期時提前出場不計
- 報表/CSV 都使用 UTF-8-SIG，CLI/日誌中文，避免 Windows cp950

## 測試（pytest）
- 已涵蓋：
  - 含息與停損/停利/移動停損的基本行為
  - 股票股利與現金股利（含日期/年度）
  - 資金模擬與固定資金分配
  - 網格掃描與最佳參數挑選
  - history 清除/重建的流程

## 待續可能優化
- 還原價支援（adjusted price）模式
- 股票股利更精確的股數/面額轉換與稅務考量
- 提前出場資金是否在年度內再分配的選項化
- 診斷工具輸出 CSV（軌跡）

