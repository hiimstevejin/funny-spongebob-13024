"""
Stripe test-data generator using Test Clocks.
Follows the TIMECLOCK.md lifecycle:
  create clock → create customer → create subscription
  → advance (≤2 billing periods/step) → poll ready → update/cancel
  → delete clock

Rate-limit mitigation: advance clock a few minutes before any
subscription updates (Stripe counts all requests against the
frozen timestamp).
"""

import calendar
import os
import random
import time
from collections import Counter
from datetime import datetime, timezone

import stripe
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("STRIPE_API_KEY")
if not api_key:
    raise ValueError("STRIPE_API_KEY not set")

client = stripe.StripeClient(api_key)

random.seed(42)

BILLING_INTERVAL_SECS = 30 * 24 * 3600  # 30 days in seconds
MAX_STEP_SECS = 58 * 24 * 3600  # 58 days in seconds
RATE_LIMIT_BUFFER_SECS = 5 * 60
TODAY_TS = int(datetime(2026, 5, 3, tzinfo=timezone.utc).timestamp())
COHORT_MONTHS = [
    (2025, 11),
    (2025, 12),
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4),
]
PLAN_CONFIG = {
    "plus": {"amount": 1000, "name": "Plus Plan"},
    "pro": {"amount": 5000, "name": "Pro Plan"},
    "pro_max": {"amount": 10000, "name": "Pro Max Plan"},
}
PLAN_ORDER = ["plus", "pro", "pro_max"]
PM_VISA = "pm_card_visa"
PM_FAIL = "pm_card_chargeCustomerFail"


def to_ts(year, month, day):
    """Convert a date to a Unix timestamp."""
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp())


def wait_clock(clock_id, timeout=180):
    """Poll until clock status == 'ready' and wait upto 3 minutes for transaction"""
    for _ in range(timeout):
        c = client.v1.test_helpers.test_clocks.retrieve(clock_id)
        if c.status == "ready":  # stripe finished processing
            return c
        if c.status == "internal_failure":
            raise RuntimeError(f"Clock {clock_id}: internal_failure")
        time.sleep(1)
    raise TimeoutError(f"Clock {clock_id}: not ready after {timeout}s")


def advance_clock(clock_id, target_ts):
    """Advance in steps of ≤2 billing periods (TIMECLOCK.md constraint)."""
    c = client.v1.test_helpers.test_clocks.retrieve(clock_id)
    current = c.frozen_time

    while current < target_ts:
        next_ts = min(current + MAX_STEP_SECS, target_ts)
        client.v1.test_helpers.test_clocks.advance(
            clock_id, {"frozen_time": int(next_ts)}
        )
        wait_clock(clock_id)
        current = next_ts


def advance_rate_limit_buffer(clock_id):
    """Advance a few minutes to reset Stripe's per-frozen-time rate counter
    before making additional subscription API calls (TIMECLOCK.md caveat)."""
    c = client.v1.test_helpers.test_clocks.retrieve(clock_id)
    buf_ts = c.frozen_time + RATE_LIMIT_BUFFER_SECS
    if buf_ts <= TODAY_TS:
        client.v1.test_helpers.test_clocks.advance(clock_id, {"frozen_time": buf_ts})
        wait_clock(clock_id)


def get_or_create_prices():
    """Create or retrieve Stripe price objects for each plan."""
    prices = {}
    for key, cfg in PLAN_CONFIG.items():
        found = client.v1.prices.list({"lookup_keys": [f"demo_{key}"], "active": True})
        if found.data:
            prices[key] = found.data[0].id
            print(f"  reuse {key}: {prices[key]}")
        else:
            prod = client.v1.products.create({"name": cfg["name"]})
            price = client.v1.prices.create(
                {
                    "product": prod.id,
                    "unit_amount": cfg["amount"],
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "lookup_key": f"demo_{key}",
                }
            )
            prices[key] = price.id
            print(f"  created {key}: {prices[key]}")
    return prices


def main():
    print("=== populate_stripe2.py ===\n")

    print("Prices:")
    prices = get_or_create_prices()

    statuses = ["active"] * 60 + ["past_due"] * 20 + ["canceled"] * 20
    random.shuffle(statuses)

    per_cohort = len(statuses) // len(COHORT_MONTHS)
    assignments = []

    for i, (yr, mo) in enumerate(COHORT_MONTHS):
        start = i * per_cohort
        end = start + per_cohort if i < len(COHORT_MONTHS) - 1 else len(statuses)
        for j in range(start, end):
            max_day = min(calendar.monthrange(yr, mo)[1], 28)
            day = random.randint(1, max_day)
            assignments.append((yr, mo, day, statuses[j]))

    active_idxs = [i for i, (_, _, _, s) in enumerate(assignments) if s == "active"]
    random.shuffle(active_idxs)

    upgrade_set = set(active_idxs[:15])
    downgrade_set = set(active_idxs[15:25])
    refund_set = set(active_idxs[25:30])
    unsub_set = set(active_idxs[30:35])

    results = []

    for idx, (yr, mo, day, intent) in enumerate(assignments):
        n = idx + 1
        cohort = f"{yr}-{mo:02d}"
        signup_ts = to_ts(yr, mo, day)
        plan = random.choices(PLAN_ORDER, weights=[50, 35, 15], k=1)[0]

        print(f"\n[{n:3d}/100] cohort={cohort}  plan={plan:7s}  intent={intent}")

        clock_id = None
        try:
            # Step 1: Create simulation
            clock = client.v1.test_helpers.test_clocks.create(
                {"frozen_time": signup_ts, "name": f"user_{n:03d}"}
            )
            clock_id = clock.id

            # Step 2: Set up simulation — customer + subscription
            cust = client.v1.customers.create(
                {
                    "email": f"user_{n:03d}@example.com",
                    "name": f"Test User {n:03d}",
                    "test_clock": clock_id,
                    "metadata": {
                        "internal_id": f"user_sh_{n:03d}",
                        "signup_cohort": cohort,
                        "experiment_group": random.choice(["A", "B"]),
                    },
                }
            )

            pm = client.v1.payment_methods.attach(PM_VISA, {"customer": cust.id})
            client.v1.customers.update(
                cust.id,
                {"invoice_settings": {"default_payment_method": pm.id}},
            )

            sub = client.v1.subscriptions.create(
                {
                    "customer": cust.id,
                    "items": [{"price": prices[plan], "quantity": 1}],
                    "metadata": {"plan_name": plan, "signup_cohort": cohort},
                }
            )

            # Step 3 & 4: Advance time + monitor/handle changes
            if intent == "canceled":
                months = random.randint(1, 4)
                cancel_ts = min(signup_ts + months * 30 * 24 * 3600, TODAY_TS)
                advance_clock(clock_id, cancel_ts)
                sub = client.v1.subscriptions.retrieve(sub.id)
                if sub.status != "canceled":
                    # Buffer before cancel to avoid rate-limit on the frozen ts
                    advance_rate_limit_buffer(clock_id)
                    client.v1.subscriptions.cancel(sub.id)
                print(f"  canceled after ~{months}mo")

            elif intent == "past_due":
                mid_ts = min(signup_ts + MAX_STEP_SECS, TODAY_TS)
                advance_clock(clock_id, mid_ts)

                # Swap payment method; buffer first to avoid rate limit
                advance_rate_limit_buffer(clock_id)
                fail_pm = client.v1.payment_methods.attach(
                    PM_FAIL, {"customer": cust.id}
                )
                client.v1.customers.update(
                    cust.id,
                    {"invoice_settings": {"default_payment_method": fail_pm.id}},
                )

                advance_clock(clock_id, TODAY_TS)
                print("  switched to fail card → past_due")

            else:
                advance_clock(clock_id, TODAY_TS)
                sub = client.v1.subscriptions.retrieve(sub.id)

                if idx in upgrade_set:
                    p_idx = PLAN_ORDER.index(plan)
                    if p_idx < 2:
                        new_plan = PLAN_ORDER[p_idx + 1]
                        advance_rate_limit_buffer(clock_id)
                        client.v1.subscriptions.update(
                            sub.id,
                            {
                                "items": [
                                    {
                                        "id": sub["items"]["data"][0].id,
                                        "price": prices[new_plan],
                                    }
                                ],
                                "proration_behavior": "always_invoice",
                                "metadata": {
                                    "plan_name": new_plan,
                                    "signup_cohort": cohort,
                                },
                            },
                        )
                        print(f"  upgraded {plan} → {new_plan}")

                elif idx in downgrade_set:
                    p_idx = PLAN_ORDER.index(plan)
                    if p_idx > 0:
                        new_plan = PLAN_ORDER[p_idx - 1]
                        advance_rate_limit_buffer(clock_id)
                        client.v1.subscriptions.update(
                            sub.id,
                            {
                                "items": [
                                    {
                                        "id": sub["items"]["data"][0].id,
                                        "price": prices[new_plan],
                                    }
                                ],
                                "proration_behavior": "always_invoice",
                                "metadata": {
                                    "plan_name": new_plan,
                                    "signup_cohort": cohort,
                                },
                            },
                        )
                        print(f"  downgraded {plan} → {new_plan}")

                elif idx in refund_set:
                    invs = client.v1.invoices.list(
                        {"customer": cust.id, "limit": 1, "status": "paid"}
                    )
                    if invs.data and getattr(invs.data[0], "charge", None):
                        client.v1.refunds.create({"charge": invs.data[0].charge})
                        print("  refunded latest paid invoice")

                elif idx in unsub_set:
                    advance_rate_limit_buffer(clock_id)
                    client.v1.subscriptions.cancel(sub.id)
                    print("  unsubscribed (edge case)")

            final_sub = client.v1.subscriptions.retrieve(sub.id)
            print(f"  final status: {final_sub.status}")

            invs = client.v1.invoices.list({"customer": cust.id, "limit": 10})
            for inv in invs.data:
                print(
                    "    invoice:",
                    datetime.fromtimestamp(inv.created, timezone.utc).date(),
                    "| period:",
                    datetime.fromtimestamp(inv.period_start, timezone.utc).date(),
                    "→",
                    datetime.fromtimestamp(inv.period_end, timezone.utc).date(),
                    "| status:",
                    inv.status,
                )

            results.append(
                {
                    "n": n,
                    "customer_id": cust.id,
                    "subscription_id": sub.id,
                    "clock_id": clock_id,
                    "plan": plan,
                    "intent": intent,
                    "final_status": final_sub.status,
                    "cohort": cohort,
                }
            )

        except stripe.StripeError as e:
            print(f"  STRIPE ERROR: {getattr(e, 'user_message', str(e))}")
            results.append({"n": n, "error": str(e)})

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"n": n, "error": str(e)})

    ok = [r for r in results if "error" not in r]
    err = [r for r in results if "error" in r]

    print(f"\n\n=== Summary: {len(ok)} ok / {len(err)} errors ===")
    if ok:
        print("Final status dist:", dict(Counter(r["final_status"] for r in ok)))
        print("Plan dist:        ", dict(Counter(r["plan"] for r in ok)))
    if err:
        print(f"Failed: {[r['n'] for r in err]}")


if __name__ == "__main__":
    main()
