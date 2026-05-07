import Charts from "@/components/Charts";
import SubscriptionStats from "@/components/SubscriptionStats";
import { getBaseUrl } from "@/lib/getBaseUrl";

type MrrData = {
  month: string;
  mrr: number;
};

type SubscriptionData = {
  month: string;
  contributing_subscriptions: number;
  mrr_amount: number;
  avg_mrr_per_subscription: number;
};

async function getMrrData(): Promise<MrrData[]> {
  const baseUrl = getBaseUrl();
  const res = await fetch(`${baseUrl}/api/mrr`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch MRR data");
  return res.json();
}

async function getSubscriptionData(): Promise<SubscriptionData[]> {
  const baseUrl = getBaseUrl();
  const res = await fetch(`${baseUrl}/api/subscriptions`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch subscription data");
  return res.json();
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default async function Home() {
  const [mrrData, subData] = await Promise.all([
    getMrrData(),
    getSubscriptionData(),
  ]);

  const latestMrr = mrrData.length > 0 ? mrrData[mrrData.length - 1].mrr : 0;
  const prevMrr = mrrData.length > 1 ? mrrData[mrrData.length - 2].mrr : 0;
  const mrrGrowth = prevMrr > 0 ? ((latestMrr - prevMrr) / prevMrr) * 100 : 0;

  const latestSubs =
    subData.length > 0
      ? subData[subData.length - 1].contributing_subscriptions
      : 0;
  const latestAvg =
    subData.length > 0
      ? subData[subData.length - 1].avg_mrr_per_subscription
      : 0;

  const kpis = [
    {
      label: "Current MRR",
      value: formatCurrency(latestMrr),
      delta: mrrGrowth,
    },
    {
      label: "Active Subscriptions",
      value: latestSubs.toLocaleString(),
      delta: null,
    },
    {
      label: "Avg MRR / Subscription",
      value: formatCurrency(Math.round(latestAvg)),
      delta: null,
    },
    {
      label: "MoM Growth",
      value: `${mrrGrowth >= 0 ? "+" : ""}${mrrGrowth.toFixed(1)}%`,
      delta: mrrGrowth,
    },
  ];

  return (
    <main className="min-h-screen bg-dash-bg">
      <nav className="border-b border-card-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center gap-8 px-6 py-4">
          <span className="text-lg font-semibold tracking-tight text-sage">
            MRR
          </span>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-8 flex items-baseline justify-between">
          <h1 className="text-3xl font-light tracking-tight text-neutral-100">
            Overview
          </h1>
          <span className="border rounded-xl border-card-border bg-card px-3 py-1 text-xs text-neutral-500">
            BigQuery
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {kpis.map((kpi) => (
            <div
              key={kpi.label}
              className="border border-card-border bg-card p-5"
            >
              <p className="text-xs font-medium tracking-wide text-neutral-500">
                {kpi.label}
              </p>
              <p className="mt-3 font-[family-name:var(--font-geist-mono)] text-3xl font-light tabular-nums text-neutral-100">
                {kpi.value}
              </p>
              {kpi.delta !== null && (
                <p
                  className={`mt-2 text-xs font-medium ${kpi.delta >= 0 ? "text-sage" : "text-red-400"}`}
                >
                  {kpi.delta >= 0 ? "+" : ""}
                  {kpi.delta.toFixed(1)}% from prior month
                </p>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 border border-card-border bg-card p-6">
          <Charts data={mrrData} />
        </div>

        <div className="mt-6">
          <SubscriptionStats data={subData} />
        </div>
      </div>
    </main>
  );
}
