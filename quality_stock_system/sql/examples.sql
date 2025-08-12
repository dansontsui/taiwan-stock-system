-- examples.sql (ASCII only)

-- 5y revenue CAGR (from monthly_revenues)
WITH rev AS (
  SELECT stock_id, strftime('%Y', date) AS y, SUM(revenue) AS rev
  FROM monthly_revenues
  GROUP BY stock_id, y
),
rev5 AS (
  SELECT stock_id,
         MIN(CASE WHEN y = strftime('%Y','now','-5 years') THEN rev END) AS rev_old,
         MAX(CASE WHEN y = strftime('%Y','now','-1 years') THEN rev END) AS rev_new
  FROM rev
  GROUP BY stock_id
)
SELECT stock_id,
       (POWER(1.0 * rev_new / NULLIF(rev_old,0), 1.0/4) - 1) AS cagr_5y
FROM rev5
WHERE rev_old IS NOT NULL AND rev_new IS NOT NULL;

-- roe filter example (requires financial_ratios)
SELECT s.stock_id, fr.roe, fr.debt_ratio
FROM stocks s
JOIN financial_ratios fr ON s.stock_id = fr.stock_id
WHERE fr.roe > 10 AND fr.debt_ratio < 50
ORDER BY fr.roe DESC;

