WITH months AS (
  SELECT month_start
  FROM UNNEST(
    GENERATE_DATE_ARRAY(
      DATE '2025-11-01',
      DATE '2026-04-01',
      INTERVAL 1 MONTH
    )
  ) AS month_start
),

month_ends AS (
  SELECT
    month_start,
    TIMESTAMP(DATETIME(LAST_DAY(month_start), TIME '23:59:59')) AS month_end_ts
  FROM months
)

SELECT
  FORMAT_DATE('%Y-%m', m.month_start) AS month,
  SUM(h.mrr_amount) / 100 AS mrr_amount
FROM month_ends m
JOIN `project-14804b7b-f02e-414e-a61.stripe_demo.subscription_history` h
  ON TIMESTAMP(h.valid_from) <= m.month_end_ts
  AND (
    h.valid_to IS NULL
    OR TIMESTAMP(h.valid_to) > m.month_end_ts
  )
WHERE h.status IN ('active', 'past_due')
GROUP BY month
ORDER BY month;
