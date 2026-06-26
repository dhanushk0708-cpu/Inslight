import { VIEWS } from "../../utils/constants";

export default function ResultsHeader({ activeView, columns, rowCount }) {
  return (
    <div className="results-topbar">
      <div className="results-topbar-left">
        <h2>
          {activeView === VIEWS.QUERY && "Query Results"}
          {activeView === VIEWS.DEEP_DIVE && "Deep Dive Analysis"}
          {activeView === VIEWS.WHAT_IF && "What-If Scenario"}
          {activeView === VIEWS.ANOMALIES && "Anomaly Detection"}
          {activeView === VIEWS.UPLOAD && "Dataset Profile"}
          {activeView === VIEWS.WELCOME && "Dashboard"}
        </h2>
        <span className="results-badge">
          {activeView === VIEWS.WELCOME
            ? "READY"
            : activeView === VIEWS.WHAT_IF
            ? "SIMULATE"
            : "LIVE"}
        </span>
      </div>

      <div className="results-topbar-right">
        {columns && <span className="results-chip">📐 {columns.length} cols</span>}
        {rowCount > 0 && <span className="results-chip">📊 {rowCount.toLocaleString()}</span>}
      </div>
    </div>
  );
}
