# Data Generation

This file provides the instruction to populate test stripe account using python with test user payment data to simulate subscriptions across the last 6 months, use test-clock in stripe

### Assumptions

- There are 100 users for the last 6 months
- There are 3 subscription status (Active, Canceled, Past Due)
- There are 3 tier plans that charge different rates
  Plus = $10,
  Pro = $50,
  Pro-max = $100
- Users would have different invoice dates because their signup dates are different

### Edge cases

There are edge case behavior of customers and the chance of happening

- User changes their plan to lower plan 10%
- User unsubscribes 5%
- User upgrades 15%
- User refunds their plan 5%

## Script

The script should do the following

1. Create Stripe prices
2. Generate 100 customer scenarios
3. Spread them across signup months
4. Create one Test Clock per customer
5. Create customer + payment method + subscription
6. Advance simulated time
7. Apply scenario behavior:
   - canceled
   - past_due
   - upgraded
   - downgraded
   - refunded
   - unsubscribed
8. Print invoice history
9. Save result
10. Print summary

## Data

### Customer

reference

https://docs.stripe.com/api/customers

customer object should contain

- id: <string> identifier
- email: <string> customer's email
- name: <string> customer's name
- test_clock: <string> test
- payment_method <string> pm_card_visa for successful payment, pm_card_chargeCustomerFail to simulate Past Due status
- invoice_settings <object> contains default_payment_method for automatic payment
- metadata: <object> store info such as internal_id for our own service, signup_cohort to track when they joined

example

```json
{
  "email": "tester_01@example.com",
  "name": "Test User 01",
  "test_clock": "clock_12345",
  "payment_method": "pm_card_visa",
  "invoice_settings": {
    "default_payment_method": "pm_card_visa"
  },
  "metadata": {
    "internal_id": "user_sh_001",
    "signup_cohort": "2026-Q1",
    "experiment_group": "A"
  }
}
```

### Subscriptions

reference

https://docs.stripe.com/api/subscriptions/object

subscription object should contain

- id <string> identifier
- customer <string> stripe customer id
- status <string> active, past_due or canceled
- items <array> contains price: for price model and quantity
- metadata <object> containing plan_name and signup_cohort
- payment_behavior <string> default_incomplete

example

```json
# The payload for stripe.Subscription.create()
{
  "customer": "cus_98765",
  "items": [
    {
      "price": "price_PRO_PLAN_ID",
      "quantity": 1
    }
  ],
  "metadata": {
    "plan_name": "pro",
    "signup_cohort": "2026-01"
  },
  "payment_behavior": "default_incomplete"
}
```
