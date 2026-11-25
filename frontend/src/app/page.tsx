"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { AuthService } from "../services/auth-service";
import { apiRequest } from "../services/api-client";
import {
  User,
  ChatMessage,
  QueryResult,
  WhatIfData,
  DeepDiveData,
  AnomalyData,
  DatasetProfile,
  RootCauseData,
  ForecastData,
  BusinessAlert,
  AlertRuleItem,
  DataQualityReport,
  ComparisonData,
  SavedDashboardItem,
  DatasetRelationshipItem,
  Dataset,
  RelationshipCandidateItem,
  RelationshipValidationResult,
  RelationshipPreviewResult,
  NotificationItem,
  AuditLogItem,
  PresentationItem,
} from "../types";
import { KPIGrid } from "../features/analytics/KPIGrid";
import { ChartRenderer } from "../components/charts/ChartRenderer";
import { DataTable } from "../components/common/DataTable";
import { MarkdownRenderer } from "../components/common/MarkdownRenderer";
import { Loading } from "../components/ui/Loading";
import { BrandLogo } from "../components/ui/BrandLogo";
import { SkeletonGrid } from "../components/ui/Skeleton";
import { ChatMessages } from "../features/chat/ChatMessages";
import { ChatInput } from "../features/chat/ChatInput";
import { WhatIfPanel } from "../features/what-if/WhatIfPanel";
import { AnomaliesPanel } from "../features/anomalies/AnomaliesPanel";
import { DatasetProfileView } from "../features/dataset/DatasetProfileView";
import { DeepDiveView } from "../features/analytics/DeepDiveView";
import { ReportsView } from "../features/reports/ReportsView";
import { ReportModal } from "../features/reports/ReportModal";
import { RootCausePanel } from "../features/rca/RootCausePanel";
import { ForecastingPanel } from "../features/forecasting/ForecastingPanel";
import { AlertsPanel } from "../features/alerts/AlertsPanel";
import { DataQualityPanel } from "../features/data-quality/DataQualityPanel";
import { ComparisonPanel } from "../features/comparisons/ComparisonPanel";
import { DashboardStudio } from "../features/dashboards/DashboardStudio";
import { RelationshipsPanel } from "../features/relationships/RelationshipsPanel";
import { NotificationsPanel } from "../features/notifications/NotificationsPanel";
import { PresentationStudio } from "../features/presentations/PresentationStudio";
import { AdminPanel } from "../features/admin/AdminPanel";

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function DashboardPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [activeDataset, setActiveDataset] = useState<any>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState<
    | "welcome"
    | "query"
    | "deepdive"
    | "whatif"
    | "anomalies"
    | "upload"
    | "reports"
    | "rca"
    | "forecast"
    | "alerts"
    | "quality"
    | "compare"
    | "studio"
    | "relationships"
    | "notifications"
    | "presentations"
    | "admin"
  >("welcome");
  const [queryData, setQueryData] = useState<QueryResult | null>(null);
  const [whatIfData, setWhatIfData] = useState<WhatIfData | null>(null);
  const [deepDiveData, setDeepDiveData] = useState<DeepDiveData | null>(null);
  const [anomalyData, setAnomalyData] = useState<AnomalyData | null>(null);
  const [profileData, setProfileData] = useState<DatasetProfile | null>(null);
  const [rcaData, setRcaData] = useState<RootCauseData | null>(null);
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [alerts, setAlerts] = useState<BusinessAlert[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRuleItem[]>([]);
  const [qualityReport, setQualityReport] = useState<DataQualityReport | null>(null);
  const [cleanedPreview, setCleanedPreview] = useState<Array<Record<string, any>> | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [currentDashboard, setCurrentDashboard] = useState<any | null>(null);
  const [savedDashboards, setSavedDashboards] = useState<SavedDashboardItem[]>([]);
  const [relationships, setRelationships] = useState<DatasetRelationshipItem[]>([]);
  const [userDatasets, setUserDatasets] = useState<Dataset[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadNotifCount, setUnreadNotifCount] = useState<number>(0);
  const [presentations, setPresentations] = useState<PresentationItem[]>([]);
  const [adminUsers, setAdminUsers] = useState<User[]>([]);
  const [adminAuditLogs, setAdminAuditLogs] = useState<AuditLogItem[]>([]);
  const [adminSystemStatus, setAdminSystemStatus] = useState<any>(null);
  const [showSql, setShowSql] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [chatCollapsed, setChatCollapsed] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [highlightedSection, setHighlightedSection] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{ role: string; content: string }>>([]);

  const showToast = useCallback((msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg((curr) => (curr === msg ? null : curr)), 2800);
  }, []);

  const msgEndRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Authentication & Initialization
  useEffect(() => {
    const user = AuthService.getUser();
    if (!user && !AuthService.getToken()) {
      router.push("/login");
      return;
    }
    setCurrentUser(user);

    // Fetch live user and active dataset status
    AuthService.fetchCurrentUser().then((u) => {
      if (u) setCurrentUser(u);
    });

    apiRequest("/api/v1/health")
      .then((h) => {
        setHealth(h);
        return apiRequest<any>("/api/v1/datasets/active");
      })
      .then((activeDs) => {
        if (activeDs && (activeDs.row_count > 0 || activeDs.rows > 0)) {
          setActiveDataset(activeDs);
          const count = activeDs.row_count || activeDs.rows;
          const fname = activeDs.original_filename || activeDs.filename || "dataset.csv";
          addAiMessage(
            `Welcome to **INSLIGHT**! I have **${count.toLocaleString()} records** loaded from \`${fname}\` ready for analysis.`
          );
        } else {
          setActiveDataset(null);
          addAiMessage("Welcome to INSLIGHT! Upload a CSV file or start exploring your business metrics.");
        }
      })
      .catch(() => {
        setHealth({ status: "healthy" });
        setActiveDataset(null);
        addAiMessage("Welcome to INSLIGHT! Upload a CSV file or start exploring your business metrics.");
      });
  }, [router]);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addAiMessage = (text: string, suggestions: string[] = []) => {
    setMessages((prev) => [...prev, { role: "ai", text, time: timeNow(), suggestions }]);
  };

  const addUserMessage = (text: string) => {
    setMessages((prev) => [...prev, { role: "user", text, time: timeNow() }]);
  };

  /* ━━━ QUERY EXECUTION VIA AI BI AGENT ━━━ */
  const handleQuery = useCallback(
    async (queryText: string) => {
      if (!queryText.trim() || loading) return;
      addUserMessage(queryText);
      setLoading(true);
      setShowSql(false);

      try {
        const agentRes = await apiRequest<any>("/api/v1/agent/query", {
          method: "POST",
          body: JSON.stringify({
            question: queryText,
            history: history.slice(-6),
          }),
        });

        setHistory((h) => [...h, { role: "user", content: queryText }]);

        if (agentRes.status === "rejected") {
          addAiMessage(`⚠️ ${agentRes.answer}`, agentRes.suggested_follow_ups || []);
          return;
        }

        // Route UI view based on selected tool
        if (agentRes.tool_used === "root_cause_analysis" && agentRes.data) {
          setRcaData(agentRes.data);
          setActiveView("rca");
        } else if (agentRes.tool_used === "forecasting" && agentRes.data) {
          setForecastData(agentRes.data);
          setActiveView("forecast");
        } else if (agentRes.tool_used === "comparative_analytics" && agentRes.data) {
          setComparisonData(agentRes.data);
          setActiveView("compare");
        } else {
          // Route strategic_analysis, sql_query, or general business intelligence
          setQueryData({
            kpi_cards: agentRes.kpi_results || agentRes.data?.kpi_cards || [],
            main_chart: agentRes.charts?.main_chart || agentRes.data?.main_chart,
            secondary_chart: agentRes.charts?.secondary_chart || agentRes.data?.secondary_chart,
            opportunities: agentRes.opportunities || agentRes.data?.opportunities || [],
            risks: agentRes.risks || agentRes.data?.risks || [],
            supporting_table: agentRes.supporting_table || agentRes.data?.supporting_table,
            narrative: agentRes.answer || agentRes.data?.narrative || "",
            summary: agentRes.summary || agentRes.data?.summary,
            analytical_steps: agentRes.analytical_steps || agentRes.reasoning_steps || [],
            suggested_followups: agentRes.suggested_follow_ups || agentRes.data?.suggested_followups || [],
            sql_query: agentRes.data?.sql_query,
            error: agentRes.error || agentRes.data?.error,
            available_columns: agentRes.dataset_metadata?.columns || agentRes.data?.available_columns,
          });
          setActiveView("query");
        }

        const reasoning = agentRes.reasoning_steps?.length > 0
          ? `\n\n*Agent Workflow:*\n${agentRes.reasoning_steps.join("\n")}`
          : "";

        addAiMessage(
          `${agentRes.answer}${reasoning}`,
          agentRes.suggested_follow_ups || []
        );
      } catch (err: any) {
        addAiMessage(`❌ Query error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    },
    [history, loading]
  );

  /* ━━━ PHASE 3 HANDLERS ━━━ */
  const runRCA = async () => {
    setLoading(true);
    setActiveView("rca");
    try {
      const data = await apiRequest<RootCauseData>("/api/v1/analytics/rca", { method: "POST", body: "{}" });
      setRcaData(data);
    } catch (e: any) {
      addAiMessage(`❌ Root Cause Analysis error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const runForecast = async (horizon: number = 30, method: string = "auto") => {
    setLoading(true);
    setActiveView("forecast");
    try {
      const data = await apiRequest<ForecastData>("/api/v1/analytics/forecast", {
        method: "POST",
        body: JSON.stringify({ horizon, method }),
      });
      setForecastData(data);
    } catch (e: any) {
      addAiMessage(`❌ Forecasting error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    setLoading(true);
    setActiveView("alerts");
    try {
      const [alertList, ruleList] = await Promise.all([
        apiRequest<BusinessAlert[]>("/api/v1/alerts"),
        apiRequest<AlertRuleItem[]>("/api/v1/alerts/rules"),
      ]);
      setAlerts(alertList || []);
      setAlertRules(ruleList || []);
    } catch (e: any) {
      addAiMessage(`❌ Alert service error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const scanAlerts = async () => {
    setLoading(true);
    try {
      const updated = await apiRequest<BusinessAlert[]>("/api/v1/alerts/scan", { method: "POST" });
      setAlerts(updated || []);
      addAiMessage(`🔍 Scan complete. Found ${updated?.length || 0} active alerts.`);
    } catch (e: any) {
      addAiMessage(`❌ Scan error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const markAlertRead = async (id: string) => {
    try {
      await apiRequest(`/api/v1/alerts/${id}/read`, { method: "PATCH" });
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
    } catch (e) {
      console.error(e);
    }
  };

  const resolveAlert = async (id: string) => {
    try {
      await apiRequest(`/api/v1/alerts/${id}/resolve`, { method: "PATCH" });
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_resolved: true } : a)));
    } catch (e) {
      console.error(e);
    }
  };

  const createAlertRule = async (name: string, metric: string, cond: string, thresh: number) => {
    try {
      const newRule = await apiRequest<AlertRuleItem>("/api/v1/alerts/rules", {
        method: "POST",
        body: JSON.stringify({ name, metric_name: metric, condition: cond, threshold_value: thresh }),
      });
      setAlertRules((prev) => [...prev, newRule]);
      addAiMessage(`✅ Configured alert rule: '${name}'.`);
    } catch (e: any) {
      addAiMessage(`❌ Rule creation error: ${e.message}`);
    }
  };

  const runQualityAudit = async () => {
    setLoading(true);
    setActiveView("quality");
    try {
      const active = await apiRequest<any>("/api/v1/datasets/active");
      if (!active?.id) throw new Error("No active dataset loaded.");
      const res = await apiRequest<DataQualityReport>(`/api/v1/datasets/${active.id}/quality`, { method: "POST" });
      setQualityReport(res);
    } catch (e: any) {
      addAiMessage(`❌ Data Quality error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const previewCleaned = async () => {
    try {
      const active = await apiRequest<any>("/api/v1/datasets/active");
      if (!active?.id) return;
      const res = await apiRequest<any>(`/api/v1/datasets/${active.id}/quality/preview`);
      setCleanedPreview(res.preview_records || []);
    } catch (e) {
      console.error(e);
    }
  };

  const runComparison = async (mode: string = "period") => {
    setLoading(true);
    setActiveView("compare");
    try {
      const data = await apiRequest<ComparisonData>("/api/v1/analytics/compare", {
        method: "POST",
        body: JSON.stringify({ comparison_mode: mode }),
      });
      setComparisonData(data);
    } catch (e: any) {
      addAiMessage(`❌ Comparison error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateDashboard = async (prompt: string) => {
    setLoading(true);
    setActiveView("studio");
    try {
      const data = await apiRequest<any>("/api/v1/dashboards/generate", {
        method: "POST",
        body: JSON.stringify({ prompt }),
      });
      setCurrentDashboard(data);
    } catch (e: any) {
      addAiMessage(`❌ Dashboard Builder error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveDashboard = async (title: string, desc: string, layout: any) => {
    try {
      const saved = await apiRequest<SavedDashboardItem>("/api/v1/dashboards", {
        method: "POST",
        body: JSON.stringify({ title, description: desc, layout_config: layout }),
      });
      setSavedDashboards((prev) => [saved, ...prev]);
      addAiMessage(`✅ Saved dashboard: '${title}'.`);
    } catch (e: any) {
      addAiMessage(`❌ Save dashboard error: ${e.message}`);
    }
  };

  const fetchSavedDashboards = async () => {
    setActiveView("studio");
    try {
      const list = await apiRequest<SavedDashboardItem[]>("/api/v1/dashboards");
      setSavedDashboards(list || []);
      if (!currentDashboard) {
        generateDashboard("Executive sales summary dashboard");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteDashboard = async (id: string) => {
    try {
      await apiRequest(`/api/v1/dashboards/${id}`, { method: "DELETE" });
      setSavedDashboards((prev) => prev.filter((d) => d.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRelationships = async () => {
    setLoading(true);
    setActiveView("relationships");
    try {
      const [rels, dsList] = await Promise.all([
        apiRequest<DatasetRelationshipItem[]>("/api/v1/relationships"),
        apiRequest<Dataset[]>("/api/v1/datasets").catch(() => []),
      ]);
      setRelationships(rels || []);
      setUserDatasets(dsList || []);
    } catch (e: any) {
      addAiMessage(`❌ Relationship service error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const detectRelationshipCandidates = async (
    sourceId: string,
    targetId: string
  ): Promise<RelationshipCandidateItem[]> => {
    return apiRequest<RelationshipCandidateItem[]>("/api/v1/relationships/candidates", {
      method: "POST",
      body: JSON.stringify({ source_dataset_id: sourceId, target_dataset_id: targetId }),
    });
  };

  const validateRelationship = async (
    sourceId: string,
    targetId: string,
    sourceCol: string,
    targetCol: string
  ): Promise<RelationshipValidationResult> => {
    return apiRequest<RelationshipValidationResult>("/api/v1/relationships/validate", {
      method: "POST",
      body: JSON.stringify({
        source_dataset_id: sourceId,
        target_dataset_id: targetId,
        source_column: sourceCol,
        target_column: targetCol,
      }),
    });
  };

  const previewRelationshipJoin = async (
    sourceId: string,
    targetId: string,
    sourceCol: string,
    targetCol: string,
    limit: number = 10
  ): Promise<RelationshipPreviewResult> => {
    return apiRequest<RelationshipPreviewResult>("/api/v1/relationships/preview", {
      method: "POST",
      body: JSON.stringify({
        source_dataset_id: sourceId,
        target_dataset_id: targetId,
        source_column: sourceCol,
        target_column: targetCol,
        limit,
      }),
    });
  };

  const saveRelationship = async (
    sourceId: string,
    targetId: string,
    sourceCol: string,
    targetCol: string,
    relType: string
  ) => {
    const res = await apiRequest<DatasetRelationshipItem>("/api/v1/relationships", {
      method: "POST",
      body: JSON.stringify({
        source_dataset_id: sourceId,
        target_dataset_id: targetId,
        source_column: sourceCol,
        target_column: targetCol,
        relationship_type: relType,
      }),
    });
    setRelationships((prev) => [res, ...prev.filter((r) => r.id !== res.id)]);
    showToast(`Relationship established: ${sourceCol} ➔ ${targetCol} (${relType})`);
    addAiMessage(
      `🔗 Successfully configured relationship between **${res.source_dataset_name || "Source"}** and **${res.target_dataset_name || "Target"}** on key \`${sourceCol} = ${targetCol}\` (Type: ${relType}).`
    );
    return true;
  };

  const deleteRelationship = async (id: string) => {
    await apiRequest(`/api/v1/relationships/${id}`, { method: "DELETE" });
    setRelationships((prev) => prev.filter((r) => r.id !== id));
    showToast("Relationship deleted.");
    addAiMessage("🗑️ Dataset relationship deleted.");
  };

  /* ━━━ PHASE 4 HANDLERS ━━━ */
  const refreshUnreadCount = useCallback(async () => {
    try {
      const res = await apiRequest<{ unread_count: number }>("/api/v1/notifications/unread-count");
      setUnreadNotifCount(res?.unread_count || 0);
    } catch {}
  }, []);

  useEffect(() => {
    refreshUnreadCount();
    const id = setInterval(refreshUnreadCount, 30000);
    return () => clearInterval(id);
  }, [refreshUnreadCount]);

  const fetchNotifications = async () => {
    setLoading(true);
    setActiveView("notifications");
    try {
      const items = await apiRequest<NotificationItem[]>("/api/v1/notifications");
      setNotifications(items || []);
      setUnreadNotifCount((items || []).filter((n) => !n.is_read).length);
    } catch (e: any) {
      addAiMessage(`❌ Notifications error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const markNotifRead = async (id: string) => {
    await apiRequest(`/api/v1/notifications/${id}/read`, { method: "PATCH" });
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadNotifCount((c) => Math.max(0, c - 1));
  };

  const markAllNotifsRead = async () => {
    await apiRequest("/api/v1/notifications/read-all", { method: "PATCH" });
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadNotifCount(0);
  };

  const deleteNotif = async (id: string) => {
    await apiRequest(`/api/v1/notifications/${id}`, { method: "DELETE" });
    setNotifications((prev) => {
      const next = prev.filter((n) => n.id !== id);
      setUnreadNotifCount(next.filter((n) => !n.is_read).length);
      return next;
    });
  };

  const fetchPresentations = async () => {
    setLoading(true);
    setActiveView("presentations");
    try {
      const items = await apiRequest<PresentationItem[]>("/api/v1/presentations");
      setPresentations(items || []);
    } catch (e: any) {
      addAiMessage(`❌ Presentations error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminData = async () => {
    setLoading(true);
    setActiveView("admin");
    try {
      const [usersRes, logsRes, statusRes] = await Promise.all([
        apiRequest<User[]>("/api/v1/admin/users"),
        apiRequest<{ items: AuditLogItem[] }>("/api/v1/admin/audit-logs?limit=50"),
        apiRequest<any>("/api/v1/admin/system-status"),
      ]);
      setAdminUsers(usersRes || []);
      setAdminAuditLogs(logsRes?.items || []);
      setAdminSystemStatus(statusRes);
    } catch (e: any) {
      addAiMessage(`❌ Admin access error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  /* ━━━ DEEP DIVE ━━━ */
  const runDeepDive = async (refresh: boolean = false) => {
    addUserMessage(refresh ? "↻ Refresh Deep Dive Business Analysis" : "🔬 Run Deep Dive Business Analysis");
    setLoading(true);
    setActiveView("deepdive");
    try {
      const data = await apiRequest<DeepDiveData>(`/api/v1/deep-dive?refresh=${refresh}`, { method: "POST" });
      setDeepDiveData(data);
      const findings = data.executive_summary?.key_findings || [];
      const summaryMsg = findings.length > 0
        ? `### Deep Dive Analysis Complete\n\n${findings.map((f) => `- ${f}`).join("\n")}\n\nExplore all 10 interactive sections and charts in the research workspace →`
        : data.root_cause_analysis || "Deep dive analysis complete. View details in the results panel →";
      addAiMessage(summaryMsg, [
        "Which products generate the highest profit?",
        "Which regions are underperforming?",
        "What are the biggest risks?",
      ]);
    } catch (err: any) {
      addAiMessage(`❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const jumpToDeepDiveSection = (sectionId: string) => {
    setActiveView("deepdive");
    setHighlightedSection(sectionId);
    setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  };

  /* ━━━ WHAT-IF ━━━ */
  const runWhatIfSimulation = async (price: number, discount: number, units: number) => {
    addUserMessage(
      `🎯 What-If Scenario: Price ${price > 0 ? "+" : ""}${price}%, Discount ${discount > 0 ? "+" : ""}${discount}%, Volume ${units > 0 ? "+" : ""}${units}%`
    );
    setLoading(true);
    setActiveView("whatif");
    try {
      const data = await apiRequest<WhatIfData>("/api/v1/what-if", {
        method: "POST",
        body: JSON.stringify({ price_change: price, discount_change: discount, units_change: units }),
      });
      setWhatIfData(data);
      addAiMessage(data.ai_commentary || "Scenario simulation calculated.");
    } catch (err: any) {
      addAiMessage(`❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /* ━━━ ANOMALIES ━━━ */
  const runAnomaliesScan = async () => {
    addUserMessage("🔍 Scan for Statistical Outliers & Anomalies");
    setLoading(true);
    setActiveView("anomalies");
    try {
      const data = await apiRequest<AnomalyData>("/api/v1/anomalies");
      setAnomalyData(data);
      addAiMessage(
        data.count > 0
          ? `Detected **${data.count} anomalies** in your business metrics. Check details in the results panel →`
          : "✅ All clear. No statistically significant anomalies found."
      );
    } catch (err: any) {
      addAiMessage(`❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /* ━━━ FILE UPLOAD ━━━ */
  const handleUpload = async (file: File) => {
    if (!file) return;
    addUserMessage(`📁 Uploading: ${file.name}`);
    setLoading(true);
    setActiveView("upload");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await apiRequest<any>("/api/v1/datasets/upload", {
        method: "POST",
        body: fd,
      });

      if (res.profile) {
        setProfileData(res.profile);
        const count = res.profile.rows || res.profile.row_count || 0;
        const fname = res.profile.filename || file.name;
        setActiveDataset({
          id: res.dataset_id || res.profile.id,
          table_name: fname.replace(".csv", ""),
          original_filename: fname,
          filename: fname,
          row_count: count,
          rows: count,
          columns: res.profile.column_info?.map((c: any) => c.name) || [],
        });
        setHealth((prev: any) => ({
          ...prev,
          status: "healthy",
          row_count: count,
          columns: res.profile.column_info?.map((c: any) => c.name) || [],
          table_name: fname.replace(".csv", ""),
        }));
        addAiMessage(
          `✅ Loaded **${count.toLocaleString()} records** × **${res.profile.columns} columns** (Quality Score: ${res.profile.data_quality_score}%). Your dataset is isolated and ready!`,
          res.profile.suggested_questions || []
        );
        apiRequest<Dataset[]>("/api/v1/datasets").then(setUserDatasets).catch(() => {});
      }
    } catch (err: any) {
      addAiMessage(`❌ Upload error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const isOnline = health?.status === "healthy";
  const rowCount = activeDataset?.row_count || activeDataset?.rows || health?.row_count || 0;
  const datasetName = (activeDataset?.original_filename || activeDataset?.filename || activeDataset?.table_name || "").replace(".csv", "");

  return (
    <div className="app">
      {/* ━━━ LEFT: CHAT PANEL ━━━ */}
      <div className={`chat-panel ${chatCollapsed ? "collapsed" : ""}`}>
        <div className="chat-header">
          <div className="chat-brand">
            <BrandLogo size={38} />
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <button
                type="button"
                className="btn btn-ghost"
                style={{ fontSize: 11, padding: "4px 8px" }}
                onClick={() => {
                  setMessages([]);
                  setHistory([]);
                  setActiveView("welcome");
                  addAiMessage("Started a fresh analysis session. Ask any question or launch Deep Dive.");
                }}
                title="Start New Analysis"
              >
                + New
              </button>
              {currentUser && (
                <button
                  type="button"
                  className="btn btn-ghost"
                  style={{ fontSize: 11, padding: "4px 9px" }}
                  onClick={() => AuthService.logout()}
                  title={`Signed in as ${currentUser.email}`}
                >
                  Sign out
                </button>
              )}
            </div>
          </div>

          <div className="chat-status">
            <div className={`status-dot ${isOnline && rowCount > 0 ? "on" : "off"}`} />
            <span className="chat-status-text">
              {rowCount > 0
                ? `${datasetName || "Dataset"} (${rowCount.toLocaleString()} records)`
                : (isOnline ? "No dataset loaded" : "Connecting...")}
            </span>
            <span className="chat-status-badge">{rowCount > 0 ? "LOADED" : (isOnline ? "READY" : "OFF")}</span>
          </div>

          <button
            type="button"
            className="chat-upload-btn"
            onClick={() => fileRef.current?.click()}
          >
            📁 Upload CSV Dataset
          </button>
          <input
            type="file"
            accept=".csv"
            ref={fileRef}
            style={{ display: "none" }}
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            aria-label="Upload CSV Dataset"
          />
        </div>

        {/* Messages */}
        <ChatMessages
          messages={messages}
          loading={loading}
          loadingStage={
            activeView === "deepdive"
              ? "Computing KPIs, segment trends, anomalies & 10-section research report..."
              : undefined
          }
          onSelectSuggestion={handleQuery}
          onJumpToSection={deepDiveData ? jumpToDeepDiveSection : undefined}
          messagesEndRef={msgEndRef as React.RefObject<HTMLDivElement>}
        />

        <div className="chat-actions">
          <button
            type="button"
            className={`chat-action-btn ${activeView === "deepdive" ? "active" : ""}`}
            onClick={() => runDeepDive(false)}
            disabled={loading}
          >
            🔬 Deep Dive
          </button>
          <button
            type="button"
            className={`chat-action-btn ${activeView === "whatif" ? "active" : ""}`}
            onClick={() => setActiveView("whatif")}
            disabled={loading}
          >
            🎯 What-If
          </button>
          <button
            type="button"
            className={`chat-action-btn ${activeView === "anomalies" ? "active" : ""}`}
            onClick={runAnomaliesScan}
            disabled={loading}
          >
            🔍 Anomalies
          </button>
          <button
            type="button"
            className={`chat-action-btn ${activeView === "reports" ? "active" : ""}`}
            onClick={() => setActiveView("reports")}
            disabled={loading}
          >
            📊 Reports
          </button>
        </div>

        {/* Multiline Composer with Integrated Voice & Read-Aloud */}
        <ChatInput
          onSend={handleQuery}
          loading={loading}
          lastAiText={messages.slice().reverse().find((m) => m.role === "ai")?.text}
        />
      </div>

      {/* ━━━ RIGHT: RESULTS PANEL ━━━ */}
      <div className="results-panel">
        <div className="results-topbar" style={{ flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setChatCollapsed((c) => !c)}
              title={chatCollapsed ? "Expand AI Assistant" : "Collapse AI Assistant"}
              style={{ padding: "5px 9px", fontSize: 12 }}
              aria-label="Toggle AI Assistant sidebar"
            >
              {chatCollapsed ? "☰ AI Chat" : "◧"}
            </button>
            <div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.7px", textTransform: "uppercase", fontWeight: 700 }}>
                INSLIGHT / {activeView === "admin" || activeView === "notifications" ? "Operations" : activeView === "reports" || activeView === "presentations" ? "Reporting" : "Intelligence"}
              </div>
              <h2 style={{ margin: 0 }}>
                {activeView === "query" && "AI Business Query & Insights"}
                {activeView === "rca" && "Root Cause Analysis (RCA)"}
                {activeView === "forecast" && "Predictive Forecasting"}
                {activeView === "alerts" && "Intelligent Business Alerts"}
                {activeView === "quality" && "Data Quality Assistant"}
                {activeView === "compare" && "Comparative Analytics"}
                {activeView === "studio" && "AI Dashboard Studio"}
                {activeView === "relationships" && "Multi-Dataset Relational Links"}
                {activeView === "deepdive" && "Deep Dive Analysis"}
                {activeView === "whatif" && "What-If Scenario Simulator"}
                {activeView === "anomalies" && "Anomaly Detection Feed"}
                {activeView === "upload" && "Dataset Schema & Quality"}
                {activeView === "reports" && "Business Reports & Automation"}
                {activeView === "presentations" && "AI PowerPoint Studio"}
                {activeView === "notifications" && "Notification Center"}
                {activeView === "admin" && "Administration & Audit Logs"}
                {activeView === "welcome" && "Executive Command Center"}
              </h2>
            </div>
            <span className="results-badge">
              {activeView === "welcome" ? "READY" : activeView === "whatif" ? "SIMULATION" : "ACTIVE"}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            {rowCount > 0 && (
              <span className="results-chip">
                📊 {datasetName || "Dataset"} ({rowCount.toLocaleString()} rows)
              </span>
            )}
            <button
              type="button"
              onClick={fetchNotifications}
              className="results-chip"
              style={{ cursor: "pointer", borderColor: unreadNotifCount > 0 ? "rgba(99, 102, 241, 0.45)" : undefined }}
              title="Open Notification Center"
            >
              🔔 {unreadNotifCount > 0 ? `${unreadNotifCount} unread` : "Inbox"}
            </button>
            {currentUser && (
              <span className="results-chip">
                👤 {currentUser.name}
                {currentUser.role && (
                  <span style={{ fontSize: 9, fontWeight: 800, color: currentUser.role === "admin" ? "#a5b4fc" : "#34d399", textTransform: "uppercase" }}>
                    {currentUser.role}
                  </span>
                )}
              </span>
            )}
          </div>
        </div>

        {/* Phase 3 Sub-Navigation Pills */}
        <div
          style={{
            display: "flex",
            gap: 6,
            overflowX: "auto",
            padding: "8px 16px",
            background: "rgba(15, 23, 42, 0.75)",
            borderBottom: "1px solid #1F2937",
            alignItems: "center"
          }}
        >
          <button
            type="button"
            onClick={() => setActiveView("query")}
            className={`chat-action-btn ${activeView === "query" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            💬 Query
          </button>
          <button
            type="button"
            onClick={runRCA}
            className={`chat-action-btn ${activeView === "rca" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            🔬 Root Cause
          </button>
          <button
            type="button"
            onClick={() => runForecast(30, "auto")}
            className={`chat-action-btn ${activeView === "forecast" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            📈 Forecast
          </button>
          <button
            type="button"
            onClick={fetchAlerts}
            className={`chat-action-btn ${activeView === "alerts" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            🔔 Alerts
          </button>
          <button
            type="button"
            onClick={runQualityAudit}
            className={`chat-action-btn ${activeView === "quality" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            🛡️ Quality
          </button>
          <button
            type="button"
            onClick={() => runComparison("period")}
            className={`chat-action-btn ${activeView === "compare" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            ⚖️ Benchmark
          </button>
          <button
            type="button"
            onClick={fetchSavedDashboards}
            className={`chat-action-btn ${activeView === "studio" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            📊 Studio
          </button>
          <button
            type="button"
            onClick={fetchRelationships}
            className={`chat-action-btn ${activeView === "relationships" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            🔗 Multi-Dataset
          </button>
          <button
            type="button"
            onClick={() => setActiveView("reports")}
            className={`chat-action-btn ${activeView === "reports" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            📄 Reports
          </button>
          <button
            type="button"
            onClick={() => setActiveView("whatif")}
            className={`chat-action-btn ${activeView === "whatif" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            🎯 What-If
          </button>
          <button
            type="button"
            onClick={fetchPresentations}
            className={`chat-action-btn ${activeView === "presentations" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            📽️ Slides
          </button>
          <button
            type="button"
            onClick={fetchNotifications}
            className={`chat-action-btn ${activeView === "notifications" ? "active" : ""}`}
            style={{ fontSize: 11, padding: "5px 10px" }}
          >
            🔔 Inbox{unreadNotifCount > 0 ? ` (${unreadNotifCount})` : ""}
          </button>
          {currentUser?.role === "admin" && (
            <button
              type="button"
              onClick={fetchAdminData}
              className={`chat-action-btn ${activeView === "admin" ? "active" : ""}`}
              style={{ fontSize: 11, padding: "5px 10px" }}
            >
              🛡️ Admin
            </button>
          )}
        </div>

        <div className="results-content">
          {/* Welcome Command Center */}
          {activeView === "welcome" && !loading && (
            <div className="view-enter" style={{ maxWidth: 920, margin: "12px auto" }}>
              <div className="card" style={{ padding: 28, marginBottom: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent-light)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 6 }}>
                      AI Business Intelligence Command Center
                    </div>
                    <h3 style={{ fontSize: 24, fontWeight: 800, color: "#fff", margin: "0 0 8px 0", letterSpacing: "-0.4px" }}>
                      Welcome{currentUser?.name ? `, ${currentUser.name}` : " to INSLIGHT"}
                    </h3>
                    <p style={{ color: "var(--text-secondary)", fontSize: 13.5, lineHeight: 1.65, maxWidth: 600, margin: 0 }}>
                      {rowCount > 0
                        ? `Active dataset '${datasetName}' (${rowCount.toLocaleString()} records) is isolated and ready. Ask a broad strategic question or launch any analytical workspace below.`
                        : "Upload a CSV dataset in the AI Assistant panel to unlock natural-language analytics, ML forecasting, anomaly detection, and automated reporting."}
                    </p>
                  </div>
                  {rowCount === 0 && (
                    <button type="button" className="btn btn-primary" onClick={() => fileRef.current?.click()}>
                      📁 Upload CSV Dataset
                    </button>
                  )}
                </div>

                {/* One-Click Executive Prompts */}
                <div style={{ marginTop: 20 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 10 }}>
                    One-Click Executive AI Prompts
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 }}>
                    {[
                      "Analyze my business performance and identify the three biggest opportunities and risks.",
                      "Show total revenue by region.",
                      "Forecast revenue for next 30 days.",
                      "Identify underperforming regions.",
                    ].map((promptText, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleQuery(promptText)}
                        className="btn btn-ghost"
                        style={{
                          justifyContent: "flex-start",
                          textAlign: "left",
                          padding: "10px 12px",
                          lineHeight: 1.45,
                          whiteSpace: "normal",
                          height: "100%",
                        }}
                      >
                        <span style={{ color: "var(--accent-light)" }}>✨</span>
                        <span>{promptText}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quick Workspace Launchers */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
                {[
                  { icon: "🔬", title: "Root Cause Analysis", desc: "Decompose period variance & segment drivers", action: runRCA },
                  { icon: "📈", title: "ML Forecasting", desc: "Predict revenue with 95% confidence bands", action: () => runForecast(30, "auto") },
                  { icon: "📽️", title: "AI Slide Deck (.pptx)", desc: "Generate & edit executive PowerPoint decks", action: fetchPresentations },
                  { icon: "📄", title: "PDF & Excel Reports", desc: "Export boardroom reports & schedule Gmail", action: () => setActiveView("reports") },
                ].map((w, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={w.action}
                    className="kpi-card"
                    style={{ textAlign: "left", cursor: "pointer", border: "1px solid var(--border)" }}
                  >
                    <div style={{ fontSize: 22, marginBottom: 8 }}>{w.icon}</div>
                    <div style={{ fontSize: 13.5, fontWeight: 700, color: "#f8fafc", marginBottom: 4 }}>{w.title}</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.45 }}>{w.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="view-enter">
              <Loading
                text={
                  activeView === "rca"
                    ? "Conducting Root Cause Analysis across dimensions..."
                    : activeView === "forecast"
                    ? "Training time-series forecasting model..."
                    : activeView === "alerts"
                    ? "Evaluating rule-based threshold alerts..."
                    : activeView === "quality"
                    ? "Auditing dataset hygiene and quality..."
                    : activeView === "compare"
                    ? "Calculating period-over-period variance..."
                    : activeView === "studio"
                    ? "Synthesizing dynamic AI dashboard widgets..."
                    : activeView === "relationships"
                    ? "Validating multi-dataset candidate keys..."
                    : activeView === "presentations"
                    ? "Loading AI PowerPoint Studio..."
                    : activeView === "notifications"
                    ? "Loading Notification Center..."
                    : activeView === "admin"
                    ? "Loading Administration & Audit Logs..."
                    : "Synthesizing executive business insights..."
                }
              />
              <div style={{ marginTop: 14 }}>
                <SkeletonGrid />
              </div>
            </div>
          )}

          {/* Query Results */}
          {activeView === "query" && !loading && (
            <div>
              {queryData?.error ? (
                <div style={{ background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: 10, padding: "18px 20px", marginBottom: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 20 }}>⚠️</span>
                    <h4 style={{ color: "#f87171", margin: 0, fontSize: 15, fontWeight: 700 }}>Query Notice</h4>
                  </div>
                  <p style={{ color: "#e5e7eb", margin: "0 0 10px 0", fontSize: 13, lineHeight: 1.6 }}>{queryData.error}</p>
                  {queryData.available_columns && queryData.available_columns.length > 0 && (
                    <div style={{ fontSize: 12, color: "#9ca3af", background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: 6 }}>
                      <strong>Available dataset columns:</strong> {queryData.available_columns.slice(0, 10).join(", ")}
                    </div>
                  )}
                </div>
              ) : null}

              {!queryData && (
                <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-muted)" }}>
                  <div style={{ fontSize: 40, marginBottom: 12 }}>💬</div>
                  <h4 style={{ fontSize: 16, fontWeight: 700, color: "#f3f4f6", marginBottom: 6 }}>No Active Query Results</h4>
                  <p style={{ fontSize: 13, maxWidth: 420, margin: "0 auto" }}>
                    Ask a question in the chat panel (e.g. &quot;Analyze my business performance and identify the three biggest opportunities and risks&quot;) to view live results.
                  </p>
                </div>
              )}

              {queryData && !queryData.error && (
                <>
                  <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "12px" }}>
                    <button
                      type="button"
                      onClick={() => setShowExportModal(true)}
                      style={{
                        background: "#2563eb",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "6px",
                        padding: "6px 14px",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      📄 Export Report (PDF/Excel)
                    </button>
                  </div>

                  {queryData.kpi_cards?.length > 0 && <KPIGrid cards={queryData.kpi_cards} />}

                  {/* Top 3 Opportunities */}
                  {queryData.opportunities && queryData.opportunities.length > 0 && (
                    <div style={{ marginTop: 22, marginBottom: 20 }}>
                      <h4 style={{ fontSize: 15, fontWeight: 700, color: "#10b981", display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                        <span>🚀</span> Top Commercial Opportunities
                      </h4>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
                        {queryData.opportunities.map((opp: any, idx: number) => (
                          <div
                            key={idx}
                            style={{
                              background: "rgba(16, 185, 129, 0.05)",
                              border: "1px solid rgba(16, 185, 129, 0.25)",
                              borderRadius: 10,
                              padding: "14px 16px",
                              display: "flex",
                              flexDirection: "column",
                              justifyContent: "space-between"
                            }}
                          >
                            <div>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, gap: 6, flexWrap: "wrap" }}>
                                <span style={{ fontSize: 11, fontWeight: 700, color: "#10b981", background: "rgba(16, 185, 129, 0.15)", padding: "2px 8px", borderRadius: 12 }}>
                                  Opportunity #{opp.rank || idx + 1}
                                </span>
                                {opp.is_hypothesis && (
                                  <span style={{ fontSize: 10, fontWeight: 700, color: "#fbbf24", background: "rgba(251, 191, 36, 0.14)", padding: "2px 7px", borderRadius: 4, textTransform: "uppercase" }}>
                                    Hypothesis / Requires Validation
                                  </span>
                                )}
                              </div>
                              <h5 style={{ fontSize: 14, fontWeight: 700, color: "#f3f4f6", margin: "0 0 6px 0" }}>{opp.title}</h5>
                              <p style={{ fontSize: 12.5, color: "#9ca3af", margin: "0 0 8px 0", lineHeight: 1.5 }}>{opp.business_interpretation || opp.impact}</p>
                              {opp.supporting_metric && (
                                <div style={{ fontSize: 11.5, color: "#d1d5db", background: "rgba(0,0,0,0.22)", padding: "7px 9px", borderRadius: 6, marginBottom: 8, lineHeight: 1.45 }}>
                                  <div><strong>Metric:</strong> {opp.supporting_metric}</div>
                                  {opp.actual_value && <div><strong>Value:</strong> {opp.actual_value}</div>}
                                  {opp.evidence_source && <div style={{ color: "#9ca3af", fontSize: 11 }}><strong>Source:</strong> {opp.evidence_source}</div>}
                                </div>
                              )}
                            </div>
                            <div style={{ fontSize: 11.5, color: "#6ee7b7", background: "rgba(16, 185, 129, 0.1)", padding: "6px 10px", borderRadius: 6 }}>
                              💡 <strong>Action:</strong> {opp.recommendation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Top 3 Risks */}
                  {queryData.risks && queryData.risks.length > 0 && (
                    <div style={{ marginTop: 20, marginBottom: 22 }}>
                      <h4 style={{ fontSize: 15, fontWeight: 700, color: "#f87171", display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                        <span>⚠️</span> Critical Operational & Financial Risks
                      </h4>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
                        {queryData.risks.map((risk: any, idx: number) => (
                          <div
                            key={idx}
                            style={{
                              background: "rgba(239, 68, 68, 0.05)",
                              border: "1px solid rgba(239, 68, 68, 0.25)",
                              borderRadius: 10,
                              padding: "14px 16px",
                              display: "flex",
                              flexDirection: "column",
                              justifyContent: "space-between"
                            }}
                          >
                            <div>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                                <span style={{ fontSize: 11, fontWeight: 700, color: "#f87171", background: "rgba(239, 68, 68, 0.15)", padding: "2px 8px", borderRadius: 12 }}>
                                  Risk #{risk.rank || idx + 1}
                                </span>
                                <span
                                  style={{
                                    fontSize: 10,
                                    fontWeight: 700,
                                    textTransform: "uppercase",
                                    color: risk.severity === "critical" ? "#ef4444" : risk.severity === "warning" ? "#f59e0b" : "#3b82f6",
                                    background: "rgba(255,255,255,0.06)",
                                    padding: "2px 6px",
                                    borderRadius: 4
                                  }}
                                >
                                  {risk.severity || "warning"}
                                </span>
                              </div>
                              <h5 style={{ fontSize: 14, fontWeight: 700, color: "#f3f4f6", margin: "0 0 6px 0" }}>{risk.title}</h5>
                              <p style={{ fontSize: 12.5, color: "#9ca3af", margin: "0 0 8px 0", lineHeight: 1.5 }}>{risk.business_interpretation || risk.impact}</p>
                              {risk.supporting_metric && (
                                <div style={{ fontSize: 11.5, color: "#d1d5db", background: "rgba(0,0,0,0.22)", padding: "7px 9px", borderRadius: 6, marginBottom: 8, lineHeight: 1.45 }}>
                                  <div><strong>Metric:</strong> {risk.supporting_metric}</div>
                                  {risk.actual_value && <div><strong>Value:</strong> {risk.actual_value}</div>}
                                  {risk.evidence_source && <div style={{ color: "#9ca3af", fontSize: 11 }}><strong>Source:</strong> {risk.evidence_source}</div>}
                                </div>
                              )}
                            </div>
                            <div style={{ fontSize: 11.5, color: "#fca5a5", background: "rgba(239, 68, 68, 0.1)", padding: "6px 10px", borderRadius: 6 }}>
                              🛡️ <strong>Mitigation:</strong> {risk.mitigation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {queryData.narrative && (
                    <div className="narrative" style={{ lineHeight: 1.6, marginBottom: 18 }}>
                      <MarkdownRenderer content={queryData.narrative} />
                    </div>
                  )}

                  {(queryData.main_chart || queryData.secondary_chart) && (
                    <div className={`chart-grid ${!queryData.secondary_chart ? "single" : ""}`}>
                      {queryData.main_chart && <ChartRenderer config={queryData.main_chart} />}
                      {queryData.secondary_chart && <ChartRenderer config={queryData.secondary_chart} />}
                    </div>
                  )}

                  {queryData.supporting_table?.rows?.length ? (
                    <DataTable data={queryData.supporting_table.rows} title={queryData.supporting_table.title || "Supporting Financial Evidence"} />
                  ) : queryData.main_chart?.data?.length ? (
                    <DataTable data={queryData.main_chart.data} title="Query Records" />
                  ) : null}

                  {queryData.sql_query && (
                    <div style={{ marginTop: 14 }}>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => setShowSql(!showSql)}
                      >
                        {showSql ? "▾ Hide SQL Query" : "▸ Show Generated SQL"}
                      </button>
                      {showSql && <div className="sql-block">{queryData.sql_query}</div>}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Phase 3: Root Cause Analysis */}
          {activeView === "rca" && !loading && (
            <RootCausePanel data={rcaData} loading={loading} onRefresh={runRCA} />
          )}

          {/* Phase 3: Forecasting */}
          {activeView === "forecast" && !loading && (
            <ForecastingPanel data={forecastData} loading={loading} onRunForecast={runForecast} />
          )}

          {/* Phase 3: Alerts */}
          {activeView === "alerts" && !loading && (
            <AlertsPanel
              alerts={alerts}
              rules={alertRules}
              loading={loading}
              onScanAlerts={scanAlerts}
              onMarkRead={markAlertRead}
              onResolve={resolveAlert}
              onCreateRule={createAlertRule}
            />
          )}

          {/* Phase 3: Data Quality */}
          {activeView === "quality" && !loading && (
            <DataQualityPanel
              report={qualityReport}
              loading={loading}
              onRunAudit={runQualityAudit}
              onPreviewCleaned={previewCleaned}
              cleanedPreview={cleanedPreview}
            />
          )}

          {/* Phase 3: Comparative Analytics */}
          {activeView === "compare" && !loading && (
            <ComparisonPanel data={comparisonData} loading={loading} onRunComparison={runComparison} />
          )}

          {/* Phase 3: Dashboard Studio */}
          {activeView === "studio" && !loading && (
            <DashboardStudio
              currentDashboard={currentDashboard}
              savedDashboards={savedDashboards}
              loading={loading}
              onGenerateFromPrompt={generateDashboard}
              onSaveDashboard={saveDashboard}
              onOpenDashboard={(d) => setCurrentDashboard(JSON.parse(d.layout_config))}
              onDeleteDashboard={deleteDashboard}
            />
          )}

          {/* Phase 3: Multi-Dataset Relationships */}
          {activeView === "relationships" && !loading && (
            <RelationshipsPanel
              relationships={relationships}
              datasets={userDatasets}
              loading={loading}
              onRefresh={fetchRelationships}
              onDetectCandidates={detectRelationshipCandidates}
              onValidateRelationship={validateRelationship}
              onPreviewJoin={previewRelationshipJoin}
              onSaveRelationship={saveRelationship}
              onDeleteRelationship={deleteRelationship}
            />
          )}

          {/* Deep Dive */}
          {activeView === "deepdive" && !loading && (
            <DeepDiveView
              data={deepDiveData}
              highlightedSection={highlightedSection}
              onRefresh={() => runDeepDive(true)}
              onExportPdf={() => setShowExportModal(true)}
              onAskFollowUp={handleQuery}
            />
          )}

          {/* What-If */}
          {activeView === "whatif" && !loading && (
            <WhatIfPanel
              data={whatIfData}
              loading={loading}
              onRunSimulation={runWhatIfSimulation}
            />
          )}

          {/* Anomalies */}
          {activeView === "anomalies" && !loading && <AnomaliesPanel data={anomalyData} />}

          {/* Dataset Profile */}
          {activeView === "upload" && !loading && <DatasetProfileView profile={profileData} />}

          {/* Phase 4: Notifications */}
          {activeView === "notifications" && !loading && (
            <NotificationsPanel
              notifications={notifications}
              loading={loading}
              onRefresh={fetchNotifications}
              onMarkRead={markNotifRead}
              onMarkAllRead={markAllNotifsRead}
              onDelete={deleteNotif}
            />
          )}

          {/* Phase 4: AI PowerPoint Studio */}
          {activeView === "presentations" && !loading && (
            <PresentationStudio
              presentations={presentations}
              onRefresh={() => {
                fetchPresentations();
                refreshUnreadCount();
              }}
              onNotifyUser={(msg) => addAiMessage(msg)}
            />
          )}

          {/* Phase 4: Admin RBAC & Audit Logs */}
          {activeView === "admin" && !loading && (
            <AdminPanel
              currentUser={currentUser}
              users={adminUsers}
              auditLogs={adminAuditLogs}
              systemStatus={adminSystemStatus}
              onRefresh={fetchAdminData}
            />
          )}

          {/* Business Reports & Schedules */}
          {activeView === "reports" && !loading && <ReportsView />}

          {queryData?.sql_query && activeView === "query" && showSql && (
            <div style={{ marginTop: 8, display: "flex", justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  navigator.clipboard?.writeText(queryData.sql_query || "");
                  showToast("✓ SQL query copied to clipboard");
                }}
              >
                📋 Copy SQL
              </button>
            </div>
          )}

          {/* Export Query Result Modal */}
          <ReportModal
            isOpen={showExportModal}
            onClose={() => setShowExportModal(false)}
            title="Business Intelligence Query Export"
            customQueryData={{
              table_data: queryData?.main_chart?.data || [],
              kpi_cards: queryData?.kpi_cards || [],
              narrative: queryData?.narrative || "",
            }}
          />
        </div>
      </div>
      {toastMsg && <div className="toast-banner" role="status">{toastMsg}</div>}
    </div>
  );
}
