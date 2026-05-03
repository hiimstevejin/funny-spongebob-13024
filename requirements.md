# Interpretation (Written in my own words AI (x))

## Tech Stack

- Source: Stripe API (Python)
- Warehouse: Google BigQuery (SQL)
- Frontend: ReactJS

## The Scope (In my own words)

build data pipeline that interprets Stripe data and visualize

## Prereq

### Data Generation (Python Script)

50 - 100 custsomers each with Subscription status

- Active, Canceled, Past Due
- use Stripe Test Clocks to simulate real time (bill history of 6 months)
  https://docs.stripe.com/billing/testing/test-clocks
- can use AI to help Test Clock advancement logic to populate invoices across months

### Pipeline (Python)

load the data created in strip into Google BigQuery

- Write script to fetch objects (Subscriptions, Invoices, Charges, or Events _up to me_)
- Load them into BigQuery tables

### Logic (SQL)

MRR is normalized monthly value of active recurring subscriptions.

1. Write SQL query in BigQuery to calculate MRR for each month in the dataset
2. out put should return: month | mrr_amount

### Visualization (React)

Build UI to display data

1. Connect to either BigQuery directly or simple API endpoint
2. Render a Line Chart showing the MRR trend over the 3-6 month period generated

## Deliverables

1. README.md: instructions on how to run data generator and start the app
2. /scripts: Python data generation and ETL scripts
3. /sql: The BigQuery SQL logic used to calculate MRR
4. /frontend react app code
5. screenshot of the final dashboard

## Interview Review

focus more on system design choices

1. Accuracy Check: compare my MRR against Stripe's built in analytics
2. Verification: How to validate numbers?
3. Arcitecture: Therea are one-time script. How would you architect this to keep BigQuery in sync with Stripe automatically? Batch processing vs real-time webhooks
4. Retrospective: If building this again for a production environment handling millions of dollars, what would you do differently?
