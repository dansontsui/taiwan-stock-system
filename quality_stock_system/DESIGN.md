# 系統設計與架構（Quality Stock Screening）

目標：建置可參數化、可回測、可視覺化的長期存股「績優股」篩選系統。

核心原則：
- 避免未來函數：以公告日/生效日對齊；回測採用該時點可得資料。
- 參數化：門檻、觀察年限、產業分流邏輯皆可由 profile 控制。
- 可擴充：以 marts（快取表）承接跨來源計算後的結果，供 API/前端/CLI 直接查用。
- 跨平台與編碼：輸出 CSV/JSON 以 UTF-8-SIG，檔名與欄位名 ASCII。

模組化設計：
1) data model（資料模型）
   - 來源表：financial_statements / balance_sheets / cash_flow_statements / monthly_revenues / dividend_policies / stock_prices / financial_ratios
   - marts：
     - mart_quality_factors_yearly（品質/體質/現金流/風險指標彙總，年或 TTM）
     - mart_dividend_stability（連續配息年數、支付率、股利成長）
     - mart_valuation_snapshot（估值分位、歷史中位數/分位）

2) rules（規則引擎）
   - rule_profile：策略檔（JSON/DB table），包含門檻、啟用與例外（金融/週期/科技分流）
   - score：將多指標轉為 0~100 分並加權（品質/成長/配息/估值）

3) pipeline（排程）
   - daily/weekly：估值/波動度快照更新
   - quarterly/yearly：財報更新後重算 marts

4) outputs（產出）
   - 清單 CSV/JSON：品質分數、估值分位、產業相對排名
   - 報表圖表（後續）：趨勢圖（ROE、毛利率、FCF、股利）、估值箱形圖

指標摘要（以 ASCII 命名）：
- profitability: roe_5y_avg, roe_5y_std, gross_margin_trend, op_margin_trend, eps_stability
- growth: revenue_cagr_5y, yoy_stability
- cashflow: fcf_positive_years_5y, accruals_3y_avg
- structure: net_debt_to_equity, interest_coverage, altman_z
- dividend: cash_div_years, payout_ratio_range_ok, dividend_growth_5y
- valuation: pe_pct_5y, pb_pct_5y, ev_ebit_rel, ev_fcf_rel
- risk: vol_1y, beta_1y

例外與分流：
- financial_sector=true：改用 CAR、NPL、cost_income_ratio 等（本版先排除金融股或使用寬鬆規則）。

執行流程（簡述）：
1. 建置 marts：以 SQL/ETL 計算指標至 mart_* 表
2. 套用 rule_profile：產生 pass/fail 與 score
3. 輸出清單：排序（score desc, valuation_pct asc），匯出 CSV/JSON（UTF-8-SIG）

