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


SUBSCRIPTION_CURRENT_SCHEMA = [
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

SUBSCRIPTION_HISTORY_SCHEMA = [
    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("subscription_id", "STRING"),
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("price_id", "STRING"),
    bigquery.SchemaField("billing_interval", "STRING"),
    bigquery.SchemaField("interval_count", "INTEGER"),
    bigquery.SchemaField("unit_amount", "INTEGER"),
    bigquery.SchemaField("currency", "STRING"),
    bigquery.SchemaField("mrr_amount", "FLOAT"),
    bigquery.SchemaField("valid_from", "STRING"),
    bigquery.SchemaField("valid_to", "STRING"),
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


def get_price_from_subscription(sub):
    item = sub.items.data[0] if sub.items and sub.items.data else None
    if not item:
        return None

    price = item.price

    # If price was not expanded, Stripe may return only the price ID.
    if isinstance(price, str):
        return client.v1.prices.retrieve(price)

    return price


def calc_mrr_for_status(unit_amount, interval, interval_count, status):
    # Store 0 MRR for terminal canceled/deleted states.
    if status in ("canceled", "incomplete_expired"):
        return 0.0

    return calc_mrr(unit_amount, interval, interval_count)


def extract_subscription_state_from_event(event):
    sub = event.data.object
    price = get_price_from_subscription(sub)

    unit_amount = price.unit_amount if price else 0
    interval = price.recurring.interval if price and price.recurring else "month"
    interval_count = price.recurring.interval_count if price and price.recurring else 1
    status = sub.status

    if event.type == "customer.subscription.deleted":
        status = "canceled"

    return {
        "subscription_id": sub.id,
        "customer_id": get_customer_id(sub.customer),
        "status": status,
        "price_id": price.id if price else None,
        "billing_interval": interval,
        "interval_count": interval_count,
        "unit_amount": unit_amount,
        "currency": price.currency if price else None,
        "mrr_amount": calc_mrr_for_status(
            unit_amount,
            interval,
            interval_count,
            status,
        ),
    }


def states_are_different(old_state, new_state):
    if old_state is None or new_state is None:
        return True

    fields = [
        "status",
        "price_id",
        "billing_interval",
        "interval_count",
        "unit_amount",
        "currency",
        "mrr_amount",
    ]

    return any(old_state.get(field) != new_state.get(field) for field in fields)


def fetch_subscription_event_objects():
    event_objects = []

    event_types = [
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ]

    for event_type in event_types:
        events = client.v1.events.list(
            {
                "type": event_type,
                "limit": 100,
            }
        )

        for event in events.auto_paging_iter():
            event_objects.append(event)

    return event_objects


def get_subscription_event_effective_time(event):
    sub = event.data.object

    if event.type == "customer.subscription.created":
        return ts_to_iso(sub.created)

    if event.type == "customer.subscription.deleted":
        canceled_at = getattr(sub, "canceled_at", None)
        ended_at = getattr(sub, "ended_at", None)
        return ts_to_iso(canceled_at or ended_at or event.created)

    if event.type == "customer.subscription.updated":
        # For plan/status changes, the best available simulated time is usually
        # the subscription's current period start, or the cancellation timestamp
        # if the update is tied to cancellation.
        canceled_at = getattr(sub, "canceled_at", None)
        ended_at = getattr(sub, "ended_at", None)
        current_period_start = getattr(sub, "current_period_start", None)

        return ts_to_iso(
            canceled_at or ended_at or current_period_start or event.created
        )

    return ts_to_iso(event.created)


def build_subscription_history_from_events(events):
    events_by_subscription = {}

    for event in events:
        sub = event.data.object
        subscription_id = sub.id

        if subscription_id not in events_by_subscription:
            events_by_subscription[subscription_id] = []

        events_by_subscription[subscription_id].append(event)

    history_rows = []

    for subscription_id, sub_events in events_by_subscription.items():
        sub_events.sort(key=lambda e: (e.created, e.id))

        current_row = None
        current_state = None

        for event in sub_events:
            event_time = get_subscription_event_effective_time(event)
            new_state = extract_subscription_state_from_event(event)

            if current_row is None:
                current_row = {
                    "id": f"{subscription_id}_{event.created}_{event.id}",
                    **new_state,
                    "valid_from": event_time,
                    "valid_to": None,
                }
                current_state = new_state
                continue

            if states_are_different(current_state, new_state):
                current_row["valid_to"] = event_time
                history_rows.append(current_row)

                current_row = {
                    "id": f"{subscription_id}_{event.created}_{event.id}",
                    **new_state,
                    "valid_from": event_time,
                    "valid_to": None,
                }
                current_state = new_state

        if current_row:
            history_rows.append(current_row)

    return history_rows


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

    subscription_event_objects = fetch_subscription_event_objects()
    subscription_history_rows = build_subscription_history_from_events(
        subscription_event_objects
    )
    print(
        f"Fetched {len(customer_rows)} customers, "
        f"{len(subscription_rows)} subscriptions, "
        f"{len(subscription_history_rows)} subscription history rows, "
        f"{len(invoice_rows)} invoices"
    )

    load_rows("customer", list(customer_rows.values()), CUSTOMER_SCHEMA)
    load_rows("subscription_current", subscription_rows, SUBSCRIPTION_CURRENT_SCHEMA)
    load_rows(
        "subscription_history",
        subscription_history_rows,
        SUBSCRIPTION_HISTORY_SCHEMA,
    )
    load_rows("invoice", invoice_rows, INVOICE_SCHEMA)

    print("Done exporting Stripe data to BigQuery.")


if __name__ == "__main__":
    main()
