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
  const [chartType, setChartType] = useState<ChartType>("lineChart");

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium tracking-wide text-neutral-500">
          MRR Trend
        </h2>
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value as ChartType)}
          className="border border-[#2a2a2a] bg-[#141414] px-5 py-2 text-sm text-neutral-300 outline-none focus:border-[#b8c99a]"
        >
          <option value="lineChart">Line Chart</option>
          <option value="areaChart">Area Chart</option>
          <option value="barChart">Bar Chart</option>
        </select>
      </div>
      <div className="h-[400px] w-full min-w-0">
        {chartType === "areaChart" && <AreaChartView data={data} />}
        {chartType === "barChart" && <BarChartView data={data} />}
        {chartType === "lineChart" && <LineChartView data={data} />}
      </div>
    </section>
  );
}
