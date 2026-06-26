import ChatInput from "../Chat/ChatInput";
import ChatMessages from "../Chat/ChatMessages";
import { VIEWS } from "../../utils/constants";

export default function Sidebar({ dashboard }) {
  const {
    activeView,
    doUpload,
    fileInputRef,
    handleQuery,
    input,
    isOnline,
    loading,
    messageEndRef,
    messages,
    rowCount,
    runAnomalies,
    runDeepDive,
    setActiveView,
    setInput,
    setViewData,
  } = dashboard;

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-brand">
          <div className="chat-logo">⚡</div>
          <div className="chat-brand-text">
            <span className="chat-brand-name">DASH.AI</span>
            <span className="chat-brand-sub">BI Co-Pilot</span>
          </div>
        </div>

        <div className="chat-status">
          <div className={`status-dot ${isOnline ? "on" : "off"}`} />
          <span className="chat-status-text">
            {isOnline ? `${rowCount.toLocaleString()} rows` : "Offline"}
          </span>
          <span className="chat-status-badge">{isOnline ? "LIVE" : "OFF"}</span>
        </div>

        <button
          id="chat-upload-btn"
          name="chat-upload-btn"
          className="chat-upload-btn"
          type="button"
          onClick={() => fileInputRef.current?.click()}
        >
          📁 Upload CSV
        </button>
        <input
          id="file-upload"
          name="file-upload"
          type="file"
          accept=".csv"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={(event) => doUpload(event.target.files?.[0])}
          aria-label="Upload CSV"
        />
      </div>

      <ChatMessages
        loading={loading}
        messageEndRef={messageEndRef}
        messages={messages}
        onSuggestionClick={handleQuery}
      />

      <div className="chat-actions">
        <button
          id="act-deepdive"
          name="act-deepdive"
          className={`chat-action-btn ${activeView === VIEWS.DEEP_DIVE ? "active" : ""}`}
          type="button"
          onClick={runDeepDive}
          disabled={loading}
        >
          🔬 Deep Dive
        </button>
        <button
          id="act-whatif"
          name="act-whatif"
          className={`chat-action-btn ${activeView === VIEWS.WHAT_IF ? "active" : ""}`}
          type="button"
          onClick={() => {
            setActiveView(VIEWS.WHAT_IF);
            setViewData(null);
          }}
          disabled={loading}
        >
          🎯 What-If
        </button>
        <button
          id="act-anomalies"
          name="act-anomalies"
          className={`chat-action-btn ${activeView === VIEWS.ANOMALIES ? "active" : ""}`}
          type="button"
          onClick={runAnomalies}
          disabled={loading}
        >
          🔍 Anomalies
        </button>
      </div>

      <ChatInput
        input={input}
        loading={loading}
        onInputChange={setInput}
        onSubmit={handleQuery}
      />
    </div>
  );
}
