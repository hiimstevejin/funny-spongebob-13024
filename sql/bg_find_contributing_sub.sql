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
  COUNT(DISTINCT h.subscription_id) AS contributing_subscriptions,
  SUM(h.mrr_amount) / 100 AS mrr_amount,
  AVG(h.mrr_amount) / 100 AS avg_mrr_per_subscription
FROM month_ends m
JOIN `stripe_demo.subscription_history` h
  ON TIMESTAMP(h.valid_from) <= m.month_end_ts
  AND (
    h.valid_to IS NULL
    OR TIMESTAMP(h.valid_to) > m.month_end_ts
  )
WHERE h.status IN ('active')
GROUP BY month
ORDER BY month;
