"use client";

import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface AreaChartViewProps {
  data: { month: string; mrr: number }[];
}

export default function AreaChartView({ data }: AreaChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="sageGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#b8c99a" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#b8c99a" stopOpacity={0} />
          </linearGradient>
        </defs>
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
          tickFormatter={(v: number) => `$${v}`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e1e1e",
            border: "1px solid #2a2a2a",
            borderRadius: 8,
            color: "#e5e5e5",
          }}
        />
        <Area
          type="monotone"
          dataKey="mrr"
          stroke="#b8c99a"
          strokeWidth={2}
          fill="url(#sageGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
