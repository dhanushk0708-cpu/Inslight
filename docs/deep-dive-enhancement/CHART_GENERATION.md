# Dynamic Chart Generation

Charts are generated conditionally based on detected dataset columns and rendered via `ChartRenderer.tsx` (`recharts`):

| Chart Key | Chart Type | Required Columns |
|---|---|---|
| `revenue_trend` | Line (`LineChart`) | `date`, `revenue` |
| `profit_trend` | Line (`LineChart`) | `date`, `revenue`, `profit`/`cost` |
| `monthly_growth` | Line (`LineChart`) | `date` (>= 2 months), `revenue` |
| `revenue_by_category` | Bar (`BarChart`) | `category`, `revenue` |
| `profit_by_category` | Bar (`BarChart`) | `category`, `profit`/`cost` |
| `revenue_share` | Donut (`PieChart`) | `category`, `revenue` |
| `top_products` | Horizontal Bar (`HorizontalBarChart`) | `product`, `revenue` |
| `bottom_products` | Horizontal Bar (`HorizontalBarChart`) | `product`, `revenue` |
| `product_margins` | Bar (`BarChart`) | `product`, `profit`/`cost` |
| `revenue_vs_profit_scatter` | Scatter (`ScatterChartCard`) | `product`, `revenue`, `profit`/`cost` |
| `regional_performance` | Bar (`BarChart`) | `region`, `revenue` |
| `forecast_vs_actual` | Line (`LineChart`) | `date`, `revenue` (>= 5 periods) |
| `customer_concentration` | Bar (`BarChart`) | `customer_id`, `revenue` |

Every chart includes an analytical `interpretation` caption and an **Enlarge (`⤢`)** modal button.
