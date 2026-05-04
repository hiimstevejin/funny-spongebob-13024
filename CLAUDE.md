# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important

- Always use Context7 to find latest documentation when interacting with frameworks or API
- Do not read .env files and never refer to any information inside of it

## Project Overview

Stripe MRR pipeline take-home. Pulls Stripe test data → loads into BigQuery → calculates MRR via SQL → visualizes in React.

## Tech Stack

- **Data generation**: Python + Stripe API (test mode, Test Clocks for time simulation)
- **Warehouse**: Google BigQuery
- **Frontend**: React

## Directory Layout

```
scripts/    # Python: data generation + ETL (Stripe → BigQuery)
sql/        # BigQuery SQL for MRR calculation
frontend/   # React app (MRR line chart)
screenshots/# Final dashboard screenshot
```

## Key Constraints

- Use **Stripe Test Clocks** to simulate 6 months of billing history across 50–100 customers
- Customers must have Subscription objects with status: `active`, `canceled`, or `past_due`
- MRR SQL output shape: `month | mrr_amount`
- MRR = normalized monthly value of active recurring subscriptions only (exclude canceled/past_due)
- React chart connects to BigQuery directly or via a simple API endpoint
