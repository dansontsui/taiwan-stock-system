# 指標資料模型與來源對應（Data Model）

此文件說明各指標對應到資料庫哪個表、欄位與計算方式，便於之後以 SQL/ETL 計算並回寫到 marts。

主要來源表：
- financial_statements（損益、EPS）
- balance_sheets（資產負債）
- cash_flow_statements（現金流）
- monthly_revenues（月營收）
- dividend_policies（股利政策）
- stock_prices（日K）
- financial_ratios（估值/比率快取）

指標到來源對應：
- revenue_cagr_5y：monthly_revenues 聚年 → CAGR 計算
- roe_5y_avg/roe_5y_std：financial_ratios.roe 或由 statements + equity 計
- gross_margin_trend/op_margin_trend：financial_ratios.gross_margin/operating_margin 趨勢
- eps_stability：financial_statements(EPS) 年合併與波動度
- fcf_positive_years_5y：cash_flow_statements(CFO, CAPEX) → FCF=CFO-CAPEX → 正年數
- accruals_3y_avg：(NetIncome−CFO)/TotalAssets → statements + cashflow + balance
- net_debt_to_equity：NetDebt/Equity → (TotalDebt−Cash)/Equity
- interest_coverage：EBIT/InterestExpense → statements
- altman_z：以 statements + balance + 市值（market_values/股價*股數）
- dividend 指標：dividend_policies → 連續年數、支付率、成長率
- valuation 指標：financial_ratios.pe_ratio/pb_ratio + stock_prices → 歷史分位
- risk 指標：stock_prices → 1y 波動度、Beta（對大盤回歸）

marts 建議欄位（簡化）：
- mart_quality_factors_yearly(stock_id, year, roe_5y_avg, revenue_cagr_5y, fcf_positive_years_5y, net_debt_to_equity, interest_coverage, altman_z, accruals_3y_avg,...)
- mart_dividend_stability(stock_id, year, cash_div_years, dividend_growth_5y, payout_ratio_range_ok)
- mart_valuation_snapshot(stock_id, snap_date, pe_pct_5y, pb_pct_5y, ev_ebit_rel, ev_fcf_rel)

