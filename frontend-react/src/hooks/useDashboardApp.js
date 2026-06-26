import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../services/api";
import { timeNow } from "../utils/formatters";
import { VIEWS } from "../utils/constants";

export function useDashboardApp() {
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState(VIEWS.WELCOME);
  const [viewData, setViewData] = useState(null);
  const [showSql, setShowSql] = useState(false);
  const [history, setHistory] = useState([]);
  const [wiPrice, setWiPrice] = useState(0);
  const [wiDiscount, setWiDiscount] = useState(0);
  const [wiUnits, setWiUnits] = useState(0);

  const messageEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const addAiMessage = useCallback((text, suggestions = []) => {
    setMessages((current) => [
      ...current,
      { role: "ai", text, time: timeNow(), suggestions },
    ]);
  }, []);

  const addUserMessage = useCallback((text) => {
    setMessages((current) => [
      ...current,
      { role: "user", text, time: timeNow() },
    ]);
  }, []);

  useEffect(() => {
    let active = true;

    api
      .fetchHealth()
      .then((healthData) => {
        if (!active) {
          return;
        }

        setHealth(healthData);

        if (healthData.status === "healthy" && healthData.row_count > 0) {
          addAiMessage(
            `Welcome! I have **${healthData.row_count.toLocaleString()} rows** loaded from \`${healthData.table_name}\` with ${healthData.columns?.length || 0} columns. Ask me anything or use the quick actions below!`
          );
        } else {
          addAiMessage(
            "Welcome to DASH.AI! Upload a CSV file to get started — use the 📁 button above."
          );
        }
      })
      .catch(() => {
        if (!active) {
          return;
        }

        setHealth({ status: "error" });
        addAiMessage(
          "⚠️ Cannot connect to backend. Make sure the server is running on port 8000."
        );
      });

    return () => {
      active = false;
    };
  }, [addAiMessage]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleQuery = useCallback(
    async (nextQuery = "") => {
      const query = nextQuery || input;

      if (!query.trim() || loading) {
        return;
      }

      setInput("");
      addUserMessage(query);
      setLoading(true);
      setActiveView(VIEWS.QUERY);
      setViewData(null);
      setShowSql(false);

      try {
        const data = await api.query(query, history.slice(-6));
        setViewData(data);
        setHistory((current) => [...current, { role: "user", content: query }]);

        if (data.error) {
          addAiMessage(
            `⚠️ ${data.error}${data.suggestion ? `\n\n💡 ${data.suggestion}` : ""}`
          );
        } else {
          const kpiSummary =
            data.kpi_cards
              ?.map((kpi) => `**${kpi.label}**: ${kpi.value}`)
              .join(" · ") || "";

          addAiMessage(
            `${data.narrative || "Here are your results."}\n\n${
              kpiSummary ? `📊 ${kpiSummary}` : ""
            }`,
            data.suggested_followups || []
          );
        }
      } catch (error) {
        addAiMessage(`❌ Connection failed: ${error.message}`);
      } finally {
        setLoading(false);
      }
    },
    [addAiMessage, addUserMessage, history, input, loading]
  );

  const runDeepDive = useCallback(async () => {
    addUserMessage("🔬 Run Deep Dive Analysis");
    setLoading(true);
    setActiveView(VIEWS.DEEP_DIVE);
    setViewData(null);

    try {
      const data = await api.deepDive();
      setViewData(data);
      addAiMessage(
        data.root_cause_analysis ||
          "Deep dive analysis complete. Check the results panel →",
        []
      );
    } catch (error) {
      addAiMessage(`❌ ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [addAiMessage, addUserMessage]);

  const runWhatIf = useCallback(async () => {
    addUserMessage(
      `🎯 What-If: Price ${wiPrice > 0 ? "+" : ""}${wiPrice}%, Discount ${
        wiDiscount > 0 ? "+" : ""
      }${wiDiscount}%, Volume ${wiUnits > 0 ? "+" : ""}${wiUnits}%`
    );
    setLoading(true);
    setActiveView(VIEWS.WHAT_IF);
    setViewData(null);

    try {
      const data = await api.whatIf({
        price_change: wiPrice,
        discount_change: wiDiscount,
        units_change: wiUnits,
      });

      setViewData(data);
      addAiMessage(data.ai_commentary || "Scenario analysis complete.", []);
    } catch (error) {
      addAiMessage(`❌ ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [addAiMessage, addUserMessage, wiDiscount, wiPrice, wiUnits]);

  const runAnomalies = useCallback(async () => {
    addUserMessage("🔍 Scan for Anomalies");
    setLoading(true);
    setActiveView(VIEWS.ANOMALIES);
    setViewData(null);

    try {
      const data = await api.fetchAnomalies();
      setViewData(data);
      addAiMessage(
        data.count > 0
          ? `Found **${data.count} anomalies** in your data. Check details in the results panel →`
          : "✅ No significant anomalies detected. Your data looks clean!",
        []
      );
    } catch (error) {
      addAiMessage(`❌ ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [addAiMessage, addUserMessage]);

  const doUpload = useCallback(
    async (file) => {
      if (!file) {
        return;
      }

      addUserMessage(`📁 Uploading: ${file.name}`);
      setLoading(true);
      setActiveView(VIEWS.UPLOAD);
      setViewData(null);

      try {
        const data = await api.uploadCsv(file);

        if (data.profile) {
          setViewData(data.profile);
          setHealth((current) => ({
            ...(current || {}),
            status: "healthy",
            row_count: data.profile.rows,
            columns:
              data.profile.column_info?.map((column) => column.name) || [],
            table_name: data.profile.filename?.replace(".csv", ""),
          }));
          addAiMessage(
            `✅ Loaded **${data.profile.rows.toLocaleString()} rows** × **${data.profile.columns} columns** (Quality: ${data.profile.data_quality_score}%). Ready to analyze!`,
            data.profile.suggested_questions || []
          );
        } else {
          addAiMessage(`⚠️ Upload issue: ${data.detail || "Unknown error"}`);
        }
      } catch (error) {
        addAiMessage(`❌ Upload failed: ${error.message}`);
      } finally {
        setLoading(false);
      }
    },
    [addAiMessage, addUserMessage]
  );

  const isOnline = health?.status === "healthy";
  const rowCount = health?.row_count || 0;

  const loadingText = useMemo(() => {
    if (activeView === VIEWS.DEEP_DIVE) {
      return "Running deep analysis...";
    }

    if (activeView === VIEWS.ANOMALIES) {
      return "Scanning for anomalies...";
    }

    if (activeView === VIEWS.WHAT_IF) {
      return "Simulating scenario...";
    }

    if (activeView === VIEWS.UPLOAD) {
      return "Processing dataset...";
    }

    return "Generating insights...";
  }, [activeView]);

  return {
    activeView,
    addAiMessage,
    doUpload,
    fileInputRef,
    handleQuery,
    health,
    input,
    isOnline,
    loading,
    loadingText,
    messageEndRef,
    messages,
    rowCount,
    runAnomalies,
    runDeepDive,
    runWhatIf,
    setActiveView,
    setInput,
    setShowSql,
    setViewData,
    setWiDiscount,
    setWiPrice,
    setWiUnits,
    showSql,
    viewData,
    wiDiscount,
    wiPrice,
    wiUnits,
  };
}
