# Data Export

This file provides instructions on how to export stripe data to Google BigQuery using Python

## Script logic

In Stripe, customer to subscription is one to many relationship so customer id is saved inside of subscription object.

The script should, fetch all Test Clock subscriptions, and for each subscription

- extract customer_id
- fetch customer associated with that id and load them into two different tables mentioned below

## Tables

Generate two tables based on customer and subscription data

### customer

contains columns

- id: unique identifier for customer
- email: <string> customer email
- name: <string> customer name
- created_at: <string> iso time of account creation
- test_clock: <string> test clock time for customer
- signup_cohort: <string> signup cohort (period or quarter of signup)

### Subscriptions

contains columns

- id: unique identifier for subscriptions
- customer_id: customer id associated with this subscription
- status: <string> active, past_due, canceled
- created_at: <string> iso time of subscription creation
- current_period_start: <string> subscription period start
- current_period_end: <string> subscription period end
- canceled_at <string> if canceled, canceled time
- ended_at <string> if terminated, end time
- price_id <stirng> plus, pro, promax type of plan
- billing_interval <string> monthly, yearly ...
- interval_count <integer> every 2, 3 months not really relevant
- unit_amount <integer> defaults to 1
- currency <string> USD
- mrr_amount <Float> normalized montly recurring revenue amount in the smallest currency unit
- test_clock <string> test clock time for subscription
- plan_name <string> name of the plan

## MRR Calculation

MRR is calculated from subscription pricing, not from invoices or charges. Invoices and charges represent billing and payment activity, while MRR represents the normalized monthly value of active recurring subscriptions.

Examples:

- `$50/month` → `$50 MRR`
- `$600/year` → `$50 MRR`
- `$300 every 3 months` → `$100 MRR`

The `mrr_amount` field stores this normalized monthly value and is later summed in BigQuery by month.
