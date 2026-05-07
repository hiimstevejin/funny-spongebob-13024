SELECT
  status,
  COUNT(id),
FROM `project-14804b7b-f02e-414e-a61.stripe_demo.subscription_current`
GROUP BY status
ORDER BY status;
