"use client";

import { useState } from "react";
import AreaChartView from "@/components/AreaChartView";
import BarChartView from "@/components/BarChartView";
import LineChartView from "@/components/LineChartView";

interface ChartsProps {
  data: { month: string; mrr: number }[];
}

type ChartType = "areaChart" | "barChart" | "lineChart";

export default function Charts({ data }: ChartsProps) {
  const [chartType, setChartType] = useState("lineChart");

  return (
    <section>
      <select
        value={chartType}
        onChange={(e) => setChartType(e.target.value as ChartType)}
        className="rounded-md border border-gray-300 px-3 py-2 text-sm"
      >
        <option value="areaChart">Area Chart</option>
        <option value="barChart">Bar Chart</option>
        <option value="lineChart">Line Chart</option>
      </select>
      <div className="h-[400px] w-full min-w-0">
        {chartType === "areaChart" && <AreaChartView data={data} />}
        {chartType === "barChart" && <BarChartView data={data} />}
        {chartType === "lineChart" && <LineChartView data={data} />}
      </div>
    </section>
  );
}
