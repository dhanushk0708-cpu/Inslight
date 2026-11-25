import BarChart from "../Charts/BarChart";
import LineChart from "../Charts/LineChart";
import PieChart from "../Charts/PieChart";

export default function DeepDiveResults({ viewData }) {
  return (
    <div className="slide-up">
      {viewData.root_cause_analysis && (
        <div className="narrative">{viewData.root_cause_analysis}</div>
      )}

      {viewData.monthly_trend && (
        <LineChart
          data={viewData.monthly_trend}
          xKey="month"
          yKey="total_revenue"
          title="Monthly Revenue Trend"
        />
      )}

      {viewData.revenue_by_category && (
        <div className="chart-grid">
          <BarChart
            data={viewData.revenue_by_category}
            xKey="product_category"
            yKey="total_revenue"
            title="Revenue by Category"
          />
          <PieChart
            data={viewData.revenue_by_category}
            xKey="product_category"
            yKey="total_revenue"
            title="Revenue Share"
          />
        </div>
      )}

      {viewData.recommendations?.length > 0 && (
        <div className="card">
          <div className="card-title">Recommendations</div>
          {viewData.recommendations.map((recommendation, index) => (
            <div
              key={`${recommendation.action}-${index}`}
              style={{
                padding: "10px 0",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                gap: 10,
              }}
            >
              <span style={{ fontSize: 18 }}>
                {recommendation.priority === "high"
                  ? "🔴"
                  : recommendation.priority === "medium"
                  ? "🟡"
                  : "🟢"}
              </span>
              <div>
                <strong style={{ fontSize: 13.5 }}>{recommendation.action}</strong>
                <p
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    marginTop: 2,
                  }}
                >
                  Expected: {recommendation.expected_impact}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
