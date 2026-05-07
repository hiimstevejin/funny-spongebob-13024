"use client";

import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface LineChartViewProps {
  data: { month: string; mrr: number }[];
}

export default function LineChartView({ data }: LineChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
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
        <Line
          type="monotone"
          dataKey="mrr"
          stroke="#b8c99a"
          strokeWidth={2}
          dot={{ fill: "#b8c99a", r: 4 }}
          activeDot={{ r: 6, fill: "#d4e0b8" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
