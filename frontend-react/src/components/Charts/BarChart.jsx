import { COLORS } from "../../utils/constants";
import { fmt } from "../../utils/formatters";

export default function BarChart({ data, xKey, yKey, title }) {
  if (!data?.length) {
    return null;
  }

  const values = data.map((item) => Number(item[yKey]) || 0);
  const maxValue = Math.max(...values, 1);

  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="bar-chart">
        {data.slice(0, 20).map((item, index) => {
          const value = Number(item[yKey]) || 0;
          const height = Math.max((value / maxValue) * 100, 3);
          const color = COLORS[index % COLORS.length];

          return (
            <div className="bar-group" key={`${item[xKey]}-${index}`}>
              <div className="bar-value">{fmt(value)}</div>
              <div
                className="bar"
                style={{
                  height: `${height}%`,
                  background: `linear-gradient(180deg,${color},${color}55)`,
                  boxShadow: `0 0 10px ${color}22`,
                }}
                title={`${item[xKey]}: ${fmt(value)}`}
              />
              <div className="bar-label" title={String(item[xKey])}>
                {String(item[xKey]).slice(0, 12)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
