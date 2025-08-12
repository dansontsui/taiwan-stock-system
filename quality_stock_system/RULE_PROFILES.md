# 規則模板（Rule Profiles）

本文件定義不同投資風格的門檻參數（可儲存於 DB table: rule_profile 或 JSON）。

共用參數：
- years_window: 5
- exclude_financials: true
- min_coverage_years: 5

穩健派（conservative）
- roe_5y_avg >= 10
- revenue_cagr_5y >= 0.03
- fcf_positive_years_5y >= 3
- net_debt_to_equity <= 0.5
- interest_coverage >= 5
- cash_div_years >= 5
- payout_ratio_range_ok = true (0.3~0.7)
- pe_pct_5y <= 0.6 OR pb_pct_5y <= 0.6

高現金流（cashflow）
- fcf_positive_years_5y >= 4
- accruals_3y_avg <= 0.08
- net_debt_to_equity <= 0.4
- cash_div_years >= 5
- dividend_growth_5y >= 0

價值型（value）
- pe_pct_5y <= 0.4
- pb_pct_5y <= 0.4
- ev_fcf_rel <= 1.0

分數加權（示例）
- financial_health: 40%
- growth: 20%
- dividend: 20%
- valuation: 20%

