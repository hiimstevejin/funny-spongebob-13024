"use client";

import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Tooltip,
} from "recharts";

interface LineChartViewProps {
  data: { month: string; mrr: number }[];
}

export default function LineChartView({ data }: LineChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart width={500} height={300} data={data}>
        <CartesianGrid />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="mrr" />
      </LineChart>
    </ResponsiveContainer>
  );
}
