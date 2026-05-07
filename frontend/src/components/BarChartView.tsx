"use client";

import {
  BarChart,
  Bar,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Tooltip,
} from "recharts";

interface BarChartViewProps {
  data: { month: string; mrr: number }[];
}

export default function BarChartView({ data }: BarChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart width={500} height={300} data={data}>
        <CartesianGrid />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar type="monotone" dataKey="mrr" />
      </BarChart>
    </ResponsiveContainer>
  );
}
