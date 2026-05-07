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

interface BarChartViewProps {
  data: { month: string; mrr: number }[];
}

export default function BarChartView({ data }: BarChartViewProps) {
  return (
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
        <Bar dataKey="mrr" fill="#b8c99a" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
