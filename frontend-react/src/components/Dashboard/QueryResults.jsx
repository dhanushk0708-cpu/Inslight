import ChartRenderer from "../Charts/ChartRenderer";
import DataTable from "../Common/DataTable";
import { kpiIcon } from "../../utils/formatters";

export default function QueryResults({
  onToggleSql,
  showSql,
  viewData,
}) {
  return (
    <div className="slide-up">
      {viewData.kpi_cards?.length > 0 && (
        <div className="kpi-grid">
          {viewData.kpi_cards.map((kpi, index) => {
            const { icon, className } = kpiIcon(kpi.label);

            return (
              <div className="kpi-card" key={`${kpi.label}-${index}`}>
                <div className="kpi-header">
                  <div className="kpi-label">{kpi.label}</div>
                  <div className={`kpi-icon ${className}`}>{icon}</div>
                </div>
                <div className="kpi-value">{kpi.value}</div>
                {kpi.trend && (
                  <span className={`kpi-trend ${kpi.trend_direction || "neutral"}`}>
                    {kpi.trend_direction === "up" ? "↑" : "↓"} {kpi.trend}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {viewData.narrative && <div className="narrative">{viewData.narrative}</div>}

      <div className={`chart-grid ${!viewData.secondary_chart ? "single" : ""}`}>
        {viewData.main_chart && <ChartRenderer config={viewData.main_chart} />}
        {viewData.secondary_chart && (
          <ChartRenderer config={viewData.secondary_chart} />
        )}
      </div>

      {viewData.main_chart?.data && (
        <DataTable data={viewData.main_chart.data} title="Data" />
      )}

      {viewData.sql_query && (
        <div>
          <button
            id="btn-sql"
            name="btn-sql"
            className="btn btn-ghost"
            type="button"
            onClick={onToggleSql}
          >
            {showSql ? "▾ Hide" : "▸ Show"} SQL
          </button>
          {showSql && <div className="sql-block">{viewData.sql_query}</div>}
        </div>
      )}
    </div>
  );
}
