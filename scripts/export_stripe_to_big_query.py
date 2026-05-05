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


INVOICE_SCHEMA = [
    bigquery.SchemaField("invoice_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("subscription_id", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("billing_reason", "STRING"),
    bigquery.SchemaField("created_at", "STRING"),
    bigquery.SchemaField("period_start", "STRING"),
    bigquery.SchemaField("period_end", "STRING"),
    bigquery.SchemaField("amount_due", "INTEGER"),
    bigquery.SchemaField("amount_paid", "INTEGER"),
    bigquery.SchemaField("currency", "STRING"),
    bigquery.SchemaField("test_clock", "STRING"),
]


def ts_to_iso(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def calc_mrr(unit_amount, interval, interval_count):
    if not unit_amount:
        return 0.0

    interval_count = interval_count or 1

    if interval == "month":
        return unit_amount / interval_count

    if interval == "year":
        return unit_amount / (12 * interval_count)

    if interval == "week":
        return unit_amount * 52 / 12 / interval_count

    return float(unit_amount)


def ensure_dataset():
    dataset_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}"

    try:
        bq.get_dataset(dataset_id)
        print(f"Dataset {dataset_id} exists")
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        bq.create_dataset(dataset)
        print(f"Created dataset {dataset_id}")


def load_rows(table_name, rows, schema):
    if not rows:
        print(f"No rows for {table_name}")
        return

    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = bq.load_table_from_json(
        rows,
        table_id,
        job_config=job_config,
    )

    job.result()

    print(f"Loaded {len(rows)} rows into {table_id}")


product_cache = {}


def get_product_name(product_id):
    if not product_id:
        return None

    if product_id not in product_cache:
        product = client.v1.products.retrieve(product_id)
        product_cache[product_id] = product.name

    return product_cache[product_id]


def get_customer_id(customer):
    if isinstance(customer, str):
        return customer
    return customer.id


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
        "customer_id": get_customer_id(sub.customer),
        "status": sub.status,
        "created_at": ts_to_iso(sub.created),
        "current_period_start": ts_to_iso(item.current_period_start if item else None),
        "current_period_end": ts_to_iso(item.current_period_end if item else None),
        "canceled_at": ts_to_iso(getattr(sub, "canceled_at", None)),
        "ended_at": ts_to_iso(getattr(sub, "ended_at", None)),
        "price_id": price.id if price else None,
        "billing_interval": interval,
        "interval_count": interval_count,
        "unit_amount": unit_amount,
        "currency": price.currency if price else None,
        "mrr_amount": calc_mrr(unit_amount, interval, interval_count),
        "test_clock": ts_to_iso(clock.frozen_time),
        "plan_name": plan_name,
    }


def transform_invoice(inv, clock_frozen_time=None):
    return {
        "invoice_id": inv.id,
        "customer_id": get_customer_id(inv.customer),
        "subscription_id": (
            getattr(inv, "subscription", None)
            or getattr(
                getattr(getattr(inv, "parent", None), "subscription_details", None),
                "subscription",
                None,
            )
        ),
        "status": inv.status,
        "billing_reason": inv.billing_reason,
        "created_at": ts_to_iso(inv.created),
        "period_start": ts_to_iso(inv.period_start),
        "period_end": ts_to_iso(inv.period_end),
        "amount_due": inv.amount_due,
        "amount_paid": inv.amount_paid,
        "currency": inv.currency,
        "test_clock": ts_to_iso(clock_frozen_time),
    }


def transform_customer(cust, clock_frozen_time=None):
    created = cust.created

    signup_cohort = (
        datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m")
        if created
        else None
    )

    return {
        "id": cust.id,
        "email": cust.email,
        "name": cust.name,
        "created_at": ts_to_iso(created),
        "test_clock": ts_to_iso(clock_frozen_time),
        "signup_cohort": signup_cohort,
    }


def main():
    ensure_dataset()

    customer_rows = {}
    subscription_rows = []
    invoice_rows = []

    clocks = client.v1.test_helpers.test_clocks.list({"limit": 100})

    for clock in clocks.auto_paging_iter():
        clock_customer_ids = set()

        subs = client.v1.subscriptions.list(
            {
                "test_clock": clock.id,
                "status": "all",
                "limit": 100,
                "expand": ["data.items.data.price"],
            }
        )

        for sub in subs.auto_paging_iter():
            customer_id = get_customer_id(sub.customer)

            subscription_rows.append(transform_subscription(sub, clock))
            clock_customer_ids.add(customer_id)

            if customer_id not in customer_rows:
                cust = client.v1.customers.retrieve(customer_id)
                customer_rows[cust.id] = transform_customer(
                    cust,
                    clock_frozen_time=clock.frozen_time,
                )

        for customer_id in clock_customer_ids:
            invs = client.v1.invoices.list(
                params={
                    "customer": customer_id,
                    "limit": 100,
                }
            )

            for inv in invs.auto_paging_iter():
                invoice_rows.append(transform_invoice(inv, clock.frozen_time))

    print(
        f"Fetched {len(customer_rows)} customers, "
        f"{len(subscription_rows)} subscriptions, "
        f"{len(invoice_rows)} invoices"
    )

    load_rows("customer", list(customer_rows.values()), CUSTOMER_SCHEMA)
    load_rows("subscriptions", subscription_rows, SUBSCRIPTION_SCHEMA)
    load_rows("invoice", invoice_rows, INVOICE_SCHEMA)

    print("Done exporting Stripe data to BigQuery.")


if __name__ == "__main__":
    main()
