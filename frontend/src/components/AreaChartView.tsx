"use client";

import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Tooltip,
} from "recharts";

interface AreaChartViewProps {
  data: { month: string; mrr: number }[];
}

export default function AreaChartView({ data }: AreaChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart width={500} height={300} data={data}>
        <CartesianGrid />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Area type="monotone" dataKey="mrr" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
