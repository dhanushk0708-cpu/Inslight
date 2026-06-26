import { COLORS } from "../../utils/constants";
import { fmt } from "../../utils/formatters";

export default function PieChart({ data, xKey, yKey, title }) {
  if (!data?.length) {
    return null;
  }

  const slices = data.slice(0, 8);
  const total =
    slices.reduce((sum, item) => sum + (Number(item[yKey]) || 0), 0) || 1;
  let cumulativeAngle = 0;

  const paths = slices.map((item, index) => {
    const value = Number(item[yKey]) || 0;
    const angle = (value / total) * 360;
    const startAngle = cumulativeAngle;
    cumulativeAngle += angle;

    const radius = 82;
    const centerX = 100;
    const centerY = 100;
    const start = ((startAngle - 90) * Math.PI) / 180;
    const end = ((cumulativeAngle - 90) * Math.PI) / 180;

    return {
      path: `M ${centerX} ${centerY} L ${centerX + radius * Math.cos(start)} ${
        centerY + radius * Math.sin(start)
      } A ${radius} ${radius} 0 ${angle > 180 ? 1 : 0} 1 ${
        centerX + radius * Math.cos(end)
      } ${centerY + radius * Math.sin(end)} Z`,
      color: COLORS[index % COLORS.length],
      label: String(item[xKey]),
      percentage: ((value / total) * 100).toFixed(1),
      value,
    };
  });

  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="pie-container">
        <svg className="pie-svg" viewBox="0 0 200 200">
          {paths.map((slice, index) => (
            <path
              key={`${slice.label}-${index}`}
              d={slice.path}
              fill={slice.color}
              stroke="#111520"
              strokeWidth="2"
              style={{ filter: `drop-shadow(0 2px 4px ${slice.color}33)` }}
            >
              <title>{`${slice.label}: ${fmt(slice.value)} (${slice.percentage}%)`}</title>
            </path>
          ))}
          <circle cx="100" cy="100" r="40" fill="#111520" />
          <text
            x="100"
            y="96"
            textAnchor="middle"
            fill="#f1f3f9"
            fontSize="15"
            fontWeight="800"
          >
            {fmt(total)}
          </text>
          <text
            x="100"
            y="110"
            textAnchor="middle"
            fill="#505872"
            fontSize="8.5"
            fontWeight="600"
          >
            TOTAL
          </text>
        </svg>
        <div className="pie-legend">
          {paths.map((slice, index) => (
            <div className="legend-item" key={`${slice.label}-legend-${index}`}>
              <div
                className="legend-dot"
                style={{ background: slice.color }}
              />
              <span>{slice.label.slice(0, 18)}</span>
              <span className="legend-pct">{slice.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
