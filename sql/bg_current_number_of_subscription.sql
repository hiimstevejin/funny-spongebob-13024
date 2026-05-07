SELECT
  status,
  COUNT(id),
FROM `stripe_demo.subscription_current`
GROUP BY status
ORDER BY status;
