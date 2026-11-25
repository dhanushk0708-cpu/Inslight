import BarChart from "./BarChart";
import LineChart from "./LineChart";
import PieChart from "./PieChart";

export default function ChartRenderer({ config }) {
  if (!config?.data?.length) {
    return null;
  }

  const { type, data, x_axis: xAxis, y_axis: yAxis, title } = config;

  if (type === "line" || type === "area") {
    return <LineChart data={data} xKey={xAxis} yKey={yAxis} title={title} />;
  }

  if (type === "pie") {
    return <PieChart data={data} xKey={xAxis} yKey={yAxis} title={title} />;
  }

  return <BarChart data={data} xKey={xAxis} yKey={yAxis} title={title} />;
}
