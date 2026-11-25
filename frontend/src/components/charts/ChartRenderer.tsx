import React from "react";
import { BarChart } from "./BarChart";
import { LineChart } from "./LineChart";
import { PieChart } from "./PieChart";
import { HorizontalBarChart } from "./HorizontalBarChart";
import { ScatterChartCard } from "./ScatterChartCard";
import { ChartConfig } from "../../types";

interface ChartRendererProps {
  config: ChartConfig;
}

export const ChartRenderer: React.FC<ChartRendererProps> = ({ config }) => {
  if (!config?.data?.length) return null;
  const { type, data, x_axis, y_axis, title } = config;

  if (type === "line" || type === "area") {
    return <LineChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
  }
  if (type === "pie") {
    return <PieChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
  }
  if (type === "horizontal_bar") {
    return <HorizontalBarChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
  }
  if (type === "scatter") {
    return <ScatterChartCard data={data} xKey={x_axis} yKey={y_axis} title={title} />;
  }
  return <BarChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
};
