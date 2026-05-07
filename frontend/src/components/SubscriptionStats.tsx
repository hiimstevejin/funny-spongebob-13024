"use client";

import {
  BarChart,
  Bar,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface SubscriptionData {
  month: string;
  contributing_subscriptions: number;
  mrr_amount: number;
  avg_mrr_per_subscription: number;
}

interface SubscriptionStatsProps {
  data: SubscriptionData[];
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function SubscriptionStats({ data }: SubscriptionStatsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="border border-card-border bg-card p-6">
        <h3 className="mb-4 text-sm font-medium tracking-wide text-neutral-500">
          Active Subscriptions by Month
        </h3>
        <div className="h-[280px] w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid stroke="#2a2a2a" strokeDasharray="3 3" />
              <XAxis
                dataKey="month"
                tick={{ fill: "#787878", fontSize: 12 }}
                axisLine={{ stroke: "#2a2a2a" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#787878", fontSize: 12 }}
                axisLine={{ stroke: "#2a2a2a" }}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e1e1e",
                  border: "1px solid #2a2a2a",
                  borderRadius: 8,
                  color: "#e5e5e5",
                }}
              />
              <Bar
                dataKey="contributing_subscriptions"
                name="Active Subscriptions"
                fill="#8a9a6c"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="border border-card-border bg-card p-6">
        <h3 className="mb-4 text-sm font-medium tracking-wide text-neutral-500">
          Monthly Breakdown
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#2a2a2a]">
                <th className="py-3 pr-4 font-medium text-neutral-500">
                  Month
                </th>
                <th className="py-3 pr-4 text-right font-medium text-neutral-500">
                  Subs
                </th>
                <th className="py-3 pr-4 text-right font-medium text-neutral-500">
                  MRR
                </th>
                <th className="py-3 text-right font-medium text-neutral-500">
                  Avg / Sub
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr
                  key={row.month}
                  className="border-b border-[#1a1a1a] last:border-0"
                >
                  <td className="py-3 pr-4 font-medium text-neutral-200">
                    {row.month}
                  </td>
                  <td className="py-3 pr-4 text-right font-[family-name:var(--font-geist-mono)] tabular-nums text-neutral-300">
                    {row.contributing_subscriptions}
                  </td>
                  <td className="py-3 pr-4 text-right font-[family-name:var(--font-geist-mono)] tabular-nums text-neutral-300">
                    {formatCurrency(row.mrr_amount)}
                  </td>
                  <td className="py-3 text-right font-[family-name:var(--font-geist-mono)] tabular-nums text-neutral-300">
                    {formatCurrency(Math.round(row.avg_mrr_per_subscription))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
