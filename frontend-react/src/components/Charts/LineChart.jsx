import { COLORS } from "../../utils/constants";
import { fmt } from "../../utils/formatters";

export default function LineChart({ data, xKey, yKey, title }) {
  if (!data?.length) {
    return null;
  }

  const values = data.map((item) => Number(item[yKey]) || 0);
  const maxValue = Math.max(...values, 1);
  const minValue = Math.min(...values, 0);
  const range = maxValue - minValue || 1;
  const width = 700;
  const height = 230;
  const padding = 46;
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;
  const points = data.map((item, index) => ({
    x: padding + (index / Math.max(data.length - 1, 1)) * plotWidth,
    y:
      padding +
      plotHeight -
      (((Number(item[yKey]) || 0) - minValue) / range) * plotHeight,
  }));
  const path = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
  const areaPath = `${path} L ${points[points.length - 1].x} ${
    padding + plotHeight
  } L ${points[0].x} ${padding + plotHeight} Z`;
  const gradientId = `line-gradient-${(title || "chart").replace(/\W/g, "")}`;

  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="line-chart-container">
        <svg
          className="line-chart-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS[0]} stopOpacity="0.2" />
              <stop offset="100%" stopColor={COLORS[0]} stopOpacity="0" />
            </linearGradient>
          </defs>

          {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
            const y = padding + plotHeight * (1 - fraction);

            return (
              <g key={fraction}>
                <line
                  x1={padding}
                  y1={y}
                  x2={width - padding}
                  y2={y}
                  stroke="rgba(255,255,255,.04)"
                />
                <text
                  x={padding - 8}
                  y={y + 4}
                  textAnchor="end"
                  fill="#505872"
                  fontSize="10"
                  fontWeight="600"
                >
                  {fmt(minValue + range * fraction)}
                </text>
              </g>
            );
          })}

          <path d={areaPath} fill={`url(#${gradientId})`} />
          <path
            d={path}
            fill="none"
            stroke={COLORS[0]}
            strokeWidth="2.5"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 5px ${COLORS[0]}44)` }}
          />

          {points.map((point, index) => (
            <circle
              key={`${point.x}-${point.y}`}
              cx={point.x}
              cy={point.y}
              r="3.5"
              fill={COLORS[0]}
              stroke="#111520"
              strokeWidth="2"
            >
              <title>{`${data[index][xKey]}: ${fmt(data[index][yKey])}`}</title>
            </circle>
          ))}

          {data.length <= 14 &&
            points.map((point, index) => (
              <text
                key={`label-${point.x}-${point.y}`}
                x={point.x}
                y={height - 6}
                textAnchor="middle"
                fill="#505872"
                fontSize="9.5"
              >
                {String(data[index][xKey]).slice(0, 7)}
              </text>
            ))}
        </svg>
      </div>
    </div>
  );
}
