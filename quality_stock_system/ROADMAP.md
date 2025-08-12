# 路線圖（Roadmap）

Phase 1: 資料與指標打底（1-2 週）
- 完成資料表：financial_statements / balance_sheets / cash_flow_statements / dividend_policies
- 建立 financial_ratios（派生：ROE、毛利、營益、負債比、PE/PB/殖利率）
- 以 SQL 產出 mart_quality_factors_yearly / mart_dividend_stability
- 以 stock_prices 建立 vol_1y 與 beta_1y
- 範例 SQL：sql/examples.sql
- 匯出清單 MVP：質化分數與估值分位 CSV（UTF-8-SIG）

Phase 2: 規則化與產業分流（1-2 週）
- 建立 rule_profile（DB/JSON）與分數演算法
- 新增金融/週期/科技的分流邏輯
- 估值快照 mart_valuation_snapshot（分位計算）
- CLI：python -m quality_stock_system.cli export --profile conservative

Phase 3: 視覺化與回測（2 週）
- 報表頁：ROE/FCF/股利/估值多年趨勢與分位視圖
- 年再平衡回測（5-10 年）與風險控制（產業權重上限）
- 整合到主系統 Web/Streamlit

跨期工作
- 完善資料品質（生效日期、缺值、極端值）
- 補齊測試與 CI，確保 Win/mac 都能通過

