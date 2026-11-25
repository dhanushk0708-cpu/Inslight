import ResultsHeader from "../Header/ResultsHeader";
import Loading from "../Common/Loading";
import QueryResults from "./QueryResults";
import DeepDiveResults from "./DeepDiveResults";
import WhatIfResults from "./WhatIfResults";
import AnomaliesResults from "./AnomaliesResults";
import UploadProfile from "./UploadProfile";
import { VIEWS } from "../../utils/constants";

export default function ResultsPanel({ dashboard }) {
  const {
    activeView,
    health,
    loading,
    loadingText,
    rowCount,
    runWhatIf,
    setShowSql,
    setWiDiscount,
    setWiPrice,
    setWiUnits,
    showSql,
    viewData,
    wiDiscount,
    wiPrice,
    wiUnits,
  } = dashboard;

  return (
    <div className="results-panel">
      <ResultsHeader
        activeView={activeView}
        columns={health?.columns}
        rowCount={rowCount}
      />

      <div className="results-content">
        {activeView === VIEWS.WELCOME && !loading && (
          <div className="welcome-results fade-in">
            <div className="icon">🚀</div>
            <h3>Your AI Dashboard</h3>
            <p>
              Ask questions in the chat, run Deep Dive, What-If simulations, or
              detect anomalies. Results appear here instantly.
            </p>
          </div>
        )}

        {loading && <Loading text={loadingText} />}

        {activeView === VIEWS.QUERY && viewData && !viewData.error && !loading && (
          <QueryResults
            onToggleSql={() => setShowSql((current) => !current)}
            showSql={showSql}
            viewData={viewData}
          />
        )}

        {activeView === VIEWS.QUERY && viewData?.error && !loading && (
          <div className="error-box fade-in">
            <span>⚠️</span>
            <div>
              <strong>{viewData.error}</strong>
              {viewData.suggestion && (
                <p style={{ marginTop: 4, opacity: 0.8, fontSize: 12 }}>
                  {viewData.suggestion}
                </p>
              )}
            </div>
          </div>
        )}

        {activeView === VIEWS.DEEP_DIVE && viewData && !viewData.error && !loading && (
          <DeepDiveResults viewData={viewData} />
        )}

        {activeView === VIEWS.WHAT_IF && !loading && (
          <WhatIfResults
            loading={loading}
            runWhatIf={runWhatIf}
            setWiDiscount={setWiDiscount}
            setWiPrice={setWiPrice}
            setWiUnits={setWiUnits}
            viewData={viewData}
            wiDiscount={wiDiscount}
            wiPrice={wiPrice}
            wiUnits={wiUnits}
          />
        )}

        {activeView === VIEWS.ANOMALIES && viewData && !loading && (
          <AnomaliesResults viewData={viewData} />
        )}

        {activeView === VIEWS.UPLOAD && viewData && !loading && (
          <UploadProfile viewData={viewData} />
        )}
      </div>
    </div>
  );
}
