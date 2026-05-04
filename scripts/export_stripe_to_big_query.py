import os
from datetime import datetime, timezone

import stripe
from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

load_dotenv()

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET", "stripe_demo")

if not STRIPE_API_KEY:
    raise ValueError("STRIPE_API_KEY not set")

if not GCP_PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID not set")

client = stripe.StripeClient(STRIPE_API_KEY)
bq = bigquery.Client(project=GCP_PROJECT_ID)

CUSTOMER_SCHEMA = [
    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("email", "STRING"),
    bigquery.SchemaField("name", "STRING"),
    bigquery.SchemaField("created_at", "STRING"),
    bigquery.SchemaField("test_clock", "STRING"),
    bigquery.SchemaField("signup_cohort", "STRING"),
]

SUBSCRIPTION_SCHEMA = [
    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("created_at", "STRING"),
    bigquery.SchemaField("current_period_start", "STRING"),
    bigquery.SchemaField("current_period_end", "STRING"),
    bigquery.SchemaField("canceled_at", "STRING"),
    bigquery.SchemaField("ended_at", "STRING"),
    bigquery.SchemaField("price_id", "STRING"),
    bigquery.SchemaField("billing_interval", "STRING"),
    bigquery.SchemaField("interval_count", "INTEGER"),
    bigquery.SchemaField("unit_amount", "INTEGER"),
    bigquery.SchemaField("currency", "STRING"),
    bigquery.SchemaField("mrr_amount", "FLOAT"),
    bigquery.SchemaField("test_clock", "STRING"),
    bigquery.SchemaField("plan_name", "STRING"),
]


def ts_to_iso(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def calc_mrr(unit_amount, interval, interval_count):
    if interval == "month":
        return unit_amount / interval_count
    elif interval == "year":
        return unit_amount / 12
    return float(unit_amount)


def ensure_dataset():
    dataset_ref = bq.dataset(BQ_DATASET)
    try:
        bq.get_dataset(dataset_ref)
    except NotFound:
        bq.create_dataset(bigquery.Dataset(dataset_ref))
        print(f"Created dataset {BQ_DATASET}")


def ensure_table(table_id, schema):
    table_ref = bq.dataset(BQ_DATASET).table(table_id)
    try:
        bq.get_table(table_ref)
        print(f"Table {table_id} exists")
    except NotFound:
        bq.create_table(bigquery.Table(table_ref, schema=schema))
        print(f"Created table {table_id}")
    return bq.get_table(table_ref)


product_cache = {}


def get_product_name(product_id):
    if not product_id:
        return None
    if product_id not in product_cache:
        product = client.v1.products.retrieve(product_id)
        product_cache[product_id] = product.name
    return product_cache[product_id]


def transform_subscription(sub, clock):
    item = sub.items.data[0] if sub.items and sub.items.data else None
    price = item.price if item else None
    unit_amount = price.unit_amount if price else 0
    interval = price.recurring.interval if price and price.recurring else "month"
    interval_count = price.recurring.interval_count if price and price.recurring else 1
    plan_name = None
    if price and price.product:
        plan_name = get_product_name(price.product)

    return {
        "id": sub.id,
        "customer_id": sub.customer,
        "status": sub.status,
        "created_at": ts_to_iso(sub.created),
        "current_period_start": ts_to_iso(item.current_period_start if item else None),
        "current_period_end": ts_to_iso(item.current_period_end if item else None),
        "canceled_at": ts_to_iso(sub.canceled_at),
        "ended_at": ts_to_iso(sub.ended_at),
        "price_id": price.id if price else None,
        "billing_interval": interval,
        "interval_count": interval_count,
        "unit_amount": unit_amount,
        "currency": price.currency if price else None,
        "mrr_amount": calc_mrr(unit_amount, interval, interval_count),
        "test_clock": ts_to_iso(clock.frozen_time),
        "plan_name": plan_name,
    }


def transform_customer(cust, clock_frozen_time=None):
    created = cust.created
    cohort = (
        datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m")
        if created
        else None
    )
    test_clock_iso = None
    if clock_frozen_time:
        test_clock_iso = ts_to_iso(clock_frozen_time)

    return {
        "id": cust.id,
        "email": cust.email,
        "name": cust.name,
        "created_at": ts_to_iso(created),
        "test_clock": test_clock_iso,
        "signup_cohort": cohort,
    }


def main():
    ensure_dataset()
    customer_table = ensure_table("customer", CUSTOMER_SCHEMA)
    subscription_table = ensure_table("subscriptions", SUBSCRIPTION_SCHEMA)

    customer_rows = {}
    subscription_rows = []

    clocks = client.v1.test_helpers.test_clocks.list()
    for clock in clocks.auto_paging_iter():
        subs = client.v1.subscriptions.list(
            {
                "test_clock": clock.id,
                "status": "all",
                "limit": 1000,
                "expand": ["data.items.data.price"],
            }
        )
        for sub in subs.auto_paging_iter():
            subscription_rows.append(transform_subscription(sub, clock))
            if sub.customer not in customer_rows:
                cust = client.v1.customers.retrieve(sub.customer)
                customer_rows[cust.id] = transform_customer(
                    cust, clock_frozen_time=clock.frozen_time
                )

    print(
        f"Inserting {len(customer_rows)} customers, {len(subscription_rows)} subscriptions"
    )

    if customer_rows:
        errors = bq.insert_rows_json(customer_table, list(customer_rows.values()))
        if errors:
            print(f"Customer insert errors: {errors}")
        else:
            print("Customers inserted OK")

    if subscription_rows:
        errors = bq.insert_rows_json(subscription_table, subscription_rows)
        if errors:
            print(f"Subscription insert errors: {errors}")
        else:
            print("Subscriptions inserted OK")


if __name__ == "__main__":
    main()
