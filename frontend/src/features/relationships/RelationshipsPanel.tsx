import React, { useState, useEffect } from "react";
import {
  DatasetRelationshipItem,
  Dataset,
  RelationshipCandidateItem,
  RelationshipValidationResult,
  RelationshipPreviewResult
} from "../../types";

interface RelationshipsPanelProps {
  relationships: DatasetRelationshipItem[];
  datasets?: Dataset[];
  loading: boolean;
  onRefresh?: () => void;
  onDetectCandidates: (srcId: string, tgtId: string) => Promise<RelationshipCandidateItem[]>;
  onValidateRelationship?: (
    srcId: string,
    tgtId: string,
    srcCol: string,
    tgtCol: string
  ) => Promise<RelationshipValidationResult>;
  onPreviewJoin?: (
    srcId: string,
    tgtId: string,
    srcCol: string,
    tgtCol: string,
    limit?: number
  ) => Promise<RelationshipPreviewResult>;
  onSaveRelationship: (
    srcId: string,
    tgtId: string,
    srcCol: string,
    tgtCol: string,
    relType: string
  ) => Promise<boolean | void>;
  onDeleteRelationship: (id: string) => Promise<void> | void;
}

export const RelationshipsPanel: React.FC<RelationshipsPanelProps> = ({
  relationships,
  datasets = [],
  loading,
  onRefresh,
  onDetectCandidates,
  onValidateRelationship,
  onPreviewJoin,
  onSaveRelationship,
  onDeleteRelationship
}) => {
  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

  // Form selections
  const [sourceDatasetId, setSourceDatasetId] = useState<string>("");
  const [targetDatasetId, setTargetDatasetId] = useState<string>("");
  const [sourceColumn, setSourceColumn] = useState<string>("");
  const [targetColumn, setTargetColumn] = useState<string>("");
  const [relationshipType, setRelationshipType] = useState<string>("N:1");

  // Dynamic candidate detection state
  const [candidates, setCandidates] = useState<RelationshipCandidateItem[]>([]);
  const [isDetectingCandidates, setIsDetectingCandidates] = useState(false);

  // Validation state
  const [validationResult, setValidationResult] = useState<RelationshipValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Preview state
  const [previewResult, setPreviewResult] = useState<RelationshipPreviewResult | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [activePreviewTitle, setActivePreviewTitle] = useState<string>("");

  // Saving state
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Initialize dataset defaults when modal opens
  useEffect(() => {
    if (isCreateModalOpen && datasets.length >= 2) {
      if (!sourceDatasetId) setSourceDatasetId(datasets[0].id);
      if (!targetDatasetId) setTargetDatasetId(datasets[1].id);
    }
  }, [isCreateModalOpen, datasets]);

  // Source & Target dataset objects
  const sourceDataset = datasets.find((d) => d.id === sourceDatasetId);
  const targetDataset = datasets.find((d) => d.id === targetDatasetId);

  // Extract columns for selected datasets
  const getDatasetColumns = (ds?: Dataset): string[] => {
    if (!ds) return [];
    if (ds.columns && ds.columns.length > 0) return ds.columns;
    if (ds.profile?.column_info) return ds.profile.column_info.map((c) => c.name);
    return [];
  };

  const sourceColumns = getDatasetColumns(sourceDataset);
  const targetColumns = getDatasetColumns(targetDataset);

  // When datasets change, reset columns, candidates, and validation
  const handleSourceDatasetChange = (id: string) => {
    setSourceDatasetId(id);
    setSourceColumn("");
    setCandidates([]);
    setValidationResult(null);
    setPreviewResult(null);
    setFormError(null);
  };

  const handleTargetDatasetChange = (id: string) => {
    setTargetDatasetId(id);
    setTargetColumn("");
    setCandidates([]);
    setValidationResult(null);
    setPreviewResult(null);
    setFormError(null);
  };

  // Auto-detect candidate join keys
  const handleAutoDetect = async () => {
    if (!sourceDatasetId || !targetDatasetId) {
      setFormError("Please select two different datasets first.");
      return;
    }
    if (sourceDatasetId === targetDatasetId) {
      setFormError("Source and Target datasets must be different.");
      return;
    }

    setIsDetectingCandidates(true);
    setFormError(null);
    try {
      const detected = await onDetectCandidates(sourceDatasetId, targetDatasetId);
      setCandidates(detected || []);
      if (detected && detected.length > 0) {
        // Automatically select the first candidate match
        setSourceColumn(detected[0].source_column);
        setTargetColumn(detected[0].target_column);
      }
    } catch (err: any) {
      setFormError(err.message || "Failed to detect candidate join keys.");
    } finally {
      setIsDetectingCandidates(false);
    }
  };

  // Trigger candidate detection automatically when both datasets are selected and distinct
  useEffect(() => {
    if (sourceDatasetId && targetDatasetId && sourceDatasetId !== targetDatasetId) {
      handleAutoDetect();
    }
  }, [sourceDatasetId, targetDatasetId]);

  // Validate relationship integrity
  const handleValidate = async () => {
    if (!sourceDatasetId || !targetDatasetId || !sourceColumn || !targetColumn) {
      setFormError("Please select both datasets and their matching join columns.");
      return;
    }
    if (!onValidateRelationship) return;

    setIsValidating(true);
    setFormError(null);
    try {
      const res = await onValidateRelationship(sourceDatasetId, targetDatasetId, sourceColumn, targetColumn);
      setValidationResult(res);
      // Auto-set suggested cardinality if detected
      if (res.cardinality) {
        if (res.cardinality === "many_to_one") setRelationshipType("N:1");
        else if (res.cardinality === "one_to_one") setRelationshipType("1:1");
        else if (res.cardinality === "one_to_many") setRelationshipType("1:N");
        else if (res.cardinality === "many_to_many") setRelationshipType("N:M");
      }
    } catch (err: any) {
      setFormError(err.message || "Failed to validate key integrity.");
    } finally {
      setIsValidating(false);
    }
  };

  // Preview joined records
  const handlePreview = async () => {
    if (!sourceDatasetId || !targetDatasetId || !sourceColumn || !targetColumn) {
      setFormError("Select matching datasets and columns to preview join.");
      return;
    }
    if (!onPreviewJoin) return;

    setIsPreviewing(true);
    setFormError(null);
    try {
      const res = await onPreviewJoin(sourceDatasetId, targetDatasetId, sourceColumn, targetColumn, 10);
      setPreviewResult(res);
    } catch (err: any) {
      setFormError(err.message || "Failed to execute join preview.");
    } finally {
      setIsPreviewing(false);
    }
  };

  // Open preview for an existing configured relationship
  const handleOpenExistingPreview = async (rel: DatasetRelationshipItem) => {
    if (!onPreviewJoin) return;
    const srcName = rel.source_dataset_name || rel.source_column;
    const tgtName = rel.target_dataset_name || rel.target_column;
    setActivePreviewTitle(`Join Preview: ${srcName} ➔ ${tgtName} (${rel.source_column} = ${rel.target_column})`);
    setIsPreviewing(true);
    setIsPreviewModalOpen(true);
    setPreviewResult(null);
    try {
      const res = await onPreviewJoin(rel.source_dataset_id, rel.target_dataset_id, rel.source_column, rel.target_column, 10);
      setPreviewResult(res);
    } catch (err: any) {
      setPreviewResult({
        status: "error",
        columns: [],
        records: [],
        total_preview_count: 0,
        message: err.message || "Failed to load join preview."
      });
    } finally {
      setIsPreviewing(false);
    }
  };

  // Save new relationship
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceDatasetId || !targetDatasetId) {
      setFormError("Both source and target datasets are required.");
      return;
    }
    if (sourceDatasetId === targetDatasetId) {
      setFormError("Source and target datasets must be different.");
      return;
    }
    if (!sourceColumn || !targetColumn) {
      setFormError("Please select both source and target join columns.");
      return;
    }

    setIsSaving(true);
    setFormError(null);
    try {
      await onSaveRelationship(sourceDatasetId, targetDatasetId, sourceColumn, targetColumn, relationshipType);
      setIsCreateModalOpen(false);
      // Reset form state
      setSourceColumn("");
      setTargetColumn("");
      setValidationResult(null);
      setPreviewResult(null);
      setCandidates([]);
      if (onRefresh) onRefresh();
    } catch (err: any) {
      setFormError(err.message || "Failed to save relationship.");
    } finally {
      setIsSaving(false);
    }
  };

  // Delete relationship
  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to remove this dataset relationship?")) return;
    setDeletingId(id);
    try {
      await onDeleteRelationship(id);
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  // Helper to format cardinality tag
  const renderCardinalityBadge = (type: string) => {
    const norm = type.toLowerCase().replace(/_/g, "");
    if (norm === "manytoone" || norm === "n:1") {
      return (
        <span
          style={{
            background: "rgba(56, 189, 248, 0.15)",
            color: "#38BDF8",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            padding: "2px 8px",
            borderRadius: 6,
            fontSize: 11,
            fontWeight: 700
          }}
        >
          N:1 (Many-to-One)
        </span>
      );
    }
    if (norm === "onetoone" || norm === "1:1") {
      return (
        <span
          style={{
            background: "rgba(16, 185, 129, 0.15)",
            color: "#10B981",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            padding: "2px 8px",
            borderRadius: 6,
            fontSize: 11,
            fontWeight: 700
          }}
        >
          1:1 (One-to-One)
        </span>
      );
    }
    if (norm === "onetomany" || norm === "1:n") {
      return (
        <span
          style={{
            background: "rgba(245, 158, 11, 0.15)",
            color: "#F59E0B",
            border: "1px solid rgba(245, 158, 11, 0.3)",
            padding: "2px 8px",
            borderRadius: 6,
            fontSize: 11,
            fontWeight: 700
          }}
        >
          1:N (One-to-Many)
        </span>
      );
    }
    return (
      <span
        style={{
          background: "rgba(244, 63, 94, 0.15)",
          color: "#F43F5E",
          border: "1px solid rgba(244, 63, 94, 0.3)",
          padding: "2px 8px",
          borderRadius: 6,
          fontSize: 11,
          fontWeight: 700
        }}
      >
        N:M (Many-to-Many)
      </span>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* ━━━ OVERVIEW & ACTION BANNER ━━━ */}
      <div
        style={{
          background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
          border: "1px solid #334155",
          borderRadius: 14,
          padding: "22px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.25)"
        }}
      >
        <div style={{ maxWidth: 640 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 22 }}>🔗</span>
            <span style={{ fontSize: 18, fontWeight: 700, color: "#F8FAFC", letterSpacing: "-0.01em" }}>
              Multi-Dataset Relational Intelligence
            </span>
            <span
              style={{
                fontSize: 10,
                background: "rgba(56, 189, 248, 0.15)",
                color: "#38BDF8",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                padding: "2px 8px",
                borderRadius: 12,
                fontWeight: 600,
                textTransform: "uppercase"
              }}
            >
              DuckDB OLAP Engine
            </span>
          </div>
          <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 6, lineHeight: 1.5, marginBottom: 0 }}>
            Connect disparate datasets (e.g. Sales Orders and Product Catalog) to execute cross-table analytics.
            Antigravity automatically verifies key integrity, prevents accidental Cartesian metric inflation, and enables unified reporting.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={loading}
              title="Refresh relationships and datasets"
              style={{
                background: "#1E293B",
                border: "1px solid #475569",
                color: "#E2E8F0",
                padding: "9px 14px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                transition: "all 0.15s ease"
              }}
            >
              🔄 Refresh
            </button>
          )}

          <button
            type="button"
            id="create-relationship-btn"
            onClick={() => {
              setFormError(null);
              setIsCreateModalOpen(true);
            }}
            style={{
              background: "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)",
              border: "1px solid #38BDF8",
              color: "#FFFFFF",
              padding: "9px 18px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: "0 2px 10px rgba(2, 132, 199, 0.35)",
              display: "flex",
              alignItems: "center",
              gap: 8,
              transition: "transform 0.15s ease"
            }}
          >
            <span>➕</span>
            <span>Create Relationship</span>
          </button>
        </div>
      </div>

      {/* ━━━ CONFIGURED RELATIONSHIPS LIST ━━━ */}
      <div
        style={{
          background: "#111827",
          border: "1px solid #1F2937",
          borderRadius: 12,
          padding: 20
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#F8FAFC" }}>
            Configured Dataset Relationships ({relationships.length})
          </div>
          <div style={{ fontSize: 12, color: "#64748B" }}>
            {datasets.length} available dataset{datasets.length === 1 ? "" : "s"} in workspace
          </div>
        </div>

        {relationships.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "48px 24px",
              background: "#0B0F19",
              border: "1px dashed #334155",
              borderRadius: 10
            }}
          >
            <div style={{ fontSize: 36, marginBottom: 12 }}>🔗</div>
            <div style={{ color: "#F1F5F9", fontSize: 16, fontWeight: 600 }}>No Relationships Defined Yet</div>
            <p style={{ fontSize: 13, color: "#94A3B8", maxWidth: 440, margin: "8px auto 20px auto", lineHeight: 1.5 }}>
              Link tables like <strong>inslight_sales_orders.csv</strong> and <strong>inslight_product_catalog.csv</strong> on <code>product_id</code> to unlock enriched multi-table queries.
            </p>
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(true)}
              style={{
                background: "#0284C7",
                border: "none",
                color: "#FFFFFF",
                padding: "8px 18px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer"
              }}
            >
              ➕ Create Relationship
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {relationships.map((rel) => {
              const srcLabel = rel.source_dataset_name || "Source Dataset";
              const tgtLabel = rel.target_dataset_name || "Target Dataset";

              return (
                <div
                  key={rel.id}
                  style={{
                    background: "#1E293B",
                    border: "1px solid #334155",
                    borderRadius: 10,
                    padding: "16px 18px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 14,
                    transition: "border-color 0.2s ease"
                  }}
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 260 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                      <span style={{ fontSize: 14, fontWeight: 700, color: "#F8FAFC" }}>
                        {srcLabel}
                      </span>
                      <span style={{ color: "#38BDF8", fontWeight: 700, fontSize: 13 }}>➔</span>
                      <span style={{ fontSize: 14, fontWeight: 700, color: "#F8FAFC" }}>
                        {tgtLabel}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", fontSize: 12 }}>
                      <span style={{ color: "#94A3B8" }}>
                        Join Key: <strong style={{ color: "#E2E8F0" }}>{rel.source_column}</strong> = <strong style={{ color: "#E2E8F0" }}>{rel.target_column}</strong>
                      </span>
                      <span style={{ color: "#475569" }}>•</span>
                      {renderCardinalityBadge(rel.relationship_type)}
                      <span style={{ color: "#475569" }}>•</span>
                      <span
                        style={{
                          background: "rgba(16, 185, 129, 0.12)",
                          color: "#10B981",
                          border: "1px solid rgba(16, 185, 129, 0.25)",
                          padding: "2px 7px",
                          borderRadius: 6,
                          fontSize: 10,
                          fontWeight: 700,
                          textTransform: "uppercase"
                        }}
                      >
                        ✓ {rel.cardinality_status || "VERIFIED"}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <button
                      type="button"
                      onClick={() => handleOpenExistingPreview(rel)}
                      style={{
                        background: "#0F172A",
                        border: "1px solid #475569",
                        color: "#38BDF8",
                        padding: "7px 12px",
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 6
                      }}
                    >
                      👁️ Preview Join
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDelete(rel.id)}
                      disabled={deletingId === rel.id}
                      style={{
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                        color: "#EF4444",
                        padding: "7px 12px",
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: deletingId === rel.id ? "not-allowed" : "pointer"
                      }}
                    >
                      {deletingId === rel.id ? "Deleting..." : "Delete ✕"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ━━━ MODAL: CREATE RELATIONSHIP ━━━ */}
      {isCreateModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 16
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsCreateModalOpen(false);
          }}
        >
          <div
            style={{
              background: "#0F172A",
              border: "1px solid #334155",
              borderRadius: 14,
              width: "100%",
              maxWidth: 720,
              maxHeight: "92vh",
              overflowY: "auto",
              padding: "24px 28px",
              boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
              color: "#F8FAFC"
            }}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1E293B", paddingBottom: 14 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#F8FAFC" }}>
                  Configure Dataset Relationship
                </div>
                <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                  Establish validated foreign key linkage and verify cardinality before persisting.
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#94A3B8",
                  fontSize: 20,
                  cursor: "pointer",
                  padding: "4px 8px"
                }}
              >
                ✕
              </button>
            </div>

            {formError && (
              <div
                style={{
                  marginTop: 14,
                  background: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid #EF4444",
                  borderRadius: 8,
                  padding: "10px 14px",
                  color: "#FCA5A5",
                  fontSize: 12
                }}
              >
                ⚠️ {formError}
              </div>
            )}

            {datasets.length < 2 && (
              <div
                style={{
                  marginTop: 14,
                  background: "rgba(245, 158, 11, 0.15)",
                  border: "1px solid #F59E0B",
                  borderRadius: 8,
                  padding: "10px 14px",
                  color: "#FDE68A",
                  fontSize: 12
                }}
              >
                ⚠️ You currently have only {datasets.length} dataset{datasets.length === 1 ? "" : "s"} uploaded. At least 2 datasets (e.g. Sales Orders and Product Catalog) are required to establish relationships.
              </div>
            )}

            <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 18 }}>
              {/* STEP 1: SELECT DATASETS */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8, display: "block" }}>
                  1. Select Datasets to Join
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div>
                    <label style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4, display: "block" }}>
                      Source Dataset (Primary / Fact Table)
                    </label>
                    <select
                      value={sourceDatasetId}
                      onChange={(e) => handleSourceDatasetChange(e.target.value)}
                      style={{
                        width: "100%",
                        background: "#1E293B",
                        border: "1px solid #475569",
                        color: "#F8FAFC",
                        padding: "9px 12px",
                        borderRadius: 8,
                        fontSize: 13
                      }}
                    >
                      <option value="">-- Select Source Dataset --</option>
                      {datasets.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.original_filename} ({d.row_count || d.profile?.rows || 0} rows)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4, display: "block" }}>
                      Target Dataset (Lookup / Dimension Table)
                    </label>
                    <select
                      value={targetDatasetId}
                      onChange={(e) => handleTargetDatasetChange(e.target.value)}
                      style={{
                        width: "100%",
                        background: "#1E293B",
                        border: "1px solid #475569",
                        color: "#F8FAFC",
                        padding: "9px 12px",
                        borderRadius: 8,
                        fontSize: 13
                      }}
                    >
                      <option value="">-- Select Target Dataset --</option>
                      {datasets
                        .filter((d) => d.id !== sourceDatasetId)
                        .map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.original_filename} ({d.row_count || d.profile?.rows || 0} rows)
                          </option>
                        ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* AUTO-DETECT CANDIDATE KEYS BUTTON & BADGES */}
              {sourceDatasetId && targetDatasetId && sourceDatasetId !== targetDatasetId && (
                <div style={{ background: "#1E293B", border: "1px solid #334155", borderRadius: 8, padding: "12px 14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: "#E2E8F0" }}>
                      ⚡ Compatible Join Candidates
                    </span>
                    <button
                      type="button"
                      onClick={handleAutoDetect}
                      disabled={isDetectingCandidates}
                      style={{
                        background: "#0F172A",
                        border: "1px solid #475569",
                        color: "#38BDF8",
                        padding: "4px 10px",
                        borderRadius: 6,
                        fontSize: 11,
                        cursor: "pointer"
                      }}
                    >
                      {isDetectingCandidates ? "Detecting..." : "Scan Common Keys"}
                    </button>
                  </div>

                  {candidates.length > 0 ? (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {candidates.map((cand, idx) => {
                        const isSelected = sourceColumn === cand.source_column && targetColumn === cand.target_column;
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setSourceColumn(cand.source_column);
                              setTargetColumn(cand.target_column);
                              setValidationResult(null);
                              setPreviewResult(null);
                            }}
                            style={{
                              background: isSelected ? "rgba(56, 189, 248, 0.2)" : "#0F172A",
                              border: isSelected ? "1px solid #38BDF8" : "1px solid #334155",
                              color: isSelected ? "#38BDF8" : "#94A3B8",
                              borderRadius: 6,
                              padding: "4px 10px",
                              fontSize: 12,
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: 6
                            }}
                          >
                            <span>✓</span>
                            <span>
                              <strong>{cand.source_column}</strong> ➔ <strong>{cand.target_column}</strong>
                            </span>
                            <span style={{ fontSize: 10, opacity: 0.7 }}>({cand.match_type})</span>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ fontSize: 11, color: "#64748B" }}>
                      {isDetectingCandidates ? "Scanning column schemas..." : "No automated matches found. Select columns manually below."}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 2: SELECT JOIN COLUMNS */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8, display: "block" }}>
                  2. Select Matching Columns
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div>
                    <label style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4, display: "block" }}>
                      Source Column ({sourceDataset?.original_filename || "Source"})
                    </label>
                    <select
                      value={sourceColumn}
                      onChange={(e) => {
                        setSourceColumn(e.target.value);
                        setValidationResult(null);
                        setPreviewResult(null);
                      }}
                      style={{
                        width: "100%",
                        background: "#1E293B",
                        border: "1px solid #475569",
                        color: "#F8FAFC",
                        padding: "9px 12px",
                        borderRadius: 8,
                        fontSize: 13
                      }}
                    >
                      <option value="">-- Select Source Column --</option>
                      {sourceColumns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4, display: "block" }}>
                      Target Column ({targetDataset?.original_filename || "Target"})
                    </label>
                    <select
                      value={targetColumn}
                      onChange={(e) => {
                        setTargetColumn(e.target.value);
                        setValidationResult(null);
                        setPreviewResult(null);
                      }}
                      style={{
                        width: "100%",
                        background: "#1E293B",
                        border: "1px solid #475569",
                        color: "#F8FAFC",
                        padding: "9px 12px",
                        borderRadius: 8,
                        fontSize: 13
                      }}
                    >
                      <option value="">-- Select Target Column --</option>
                      {targetColumns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* STEP 3: CARDINALITY SELECTION */}
              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8, display: "block" }}>
                  3. Relationship Cardinality
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                  {[
                    { key: "N:1", label: "Many-to-One (N:1)", desc: "Orders ➔ Catalog" },
                    { key: "1:1", label: "One-to-One (1:1)", desc: "Unique Entity" },
                    { key: "1:N", label: "One-to-Many (1:N)", desc: "Dimension ➔ Details" },
                    { key: "N:M", label: "Many-to-Many (N:M)", desc: "Cross Association" }
                  ].map((card) => {
                    const isSelected = relationshipType === card.key;
                    return (
                      <button
                        key={card.key}
                        type="button"
                        onClick={() => setRelationshipType(card.key)}
                        style={{
                          background: isSelected ? "rgba(2, 132, 199, 0.2)" : "#1E293B",
                          border: isSelected ? "1px solid #38BDF8" : "1px solid #334155",
                          borderRadius: 8,
                          padding: "10px 8px",
                          textAlign: "center",
                          cursor: "pointer",
                          color: isSelected ? "#38BDF8" : "#94A3B8"
                        }}
                      >
                        <div style={{ fontSize: 13, fontWeight: 700 }}>{card.key}</div>
                        <div style={{ fontSize: 10, color: isSelected ? "#E2E8F0" : "#64748B", marginTop: 2 }}>
                          {card.desc}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* STEP 4: VALIDATION ACTION & RESULTS */}
              <div style={{ display: "flex", gap: 10 }}>
                <button
                  type="button"
                  onClick={handleValidate}
                  disabled={isValidating || !sourceColumn || !targetColumn}
                  style={{
                    flex: 1,
                    background: "#1E293B",
                    border: "1px solid #475569",
                    color: "#38BDF8",
                    padding: "9px 14px",
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: !sourceColumn || !targetColumn ? "not-allowed" : "pointer"
                  }}
                >
                  {isValidating ? "Validating Key Integrity..." : "🔍 Validate Key Integrity"}
                </button>

                <button
                  type="button"
                  onClick={handlePreview}
                  disabled={isPreviewing || !sourceColumn || !targetColumn}
                  style={{
                    flex: 1,
                    background: "#1E293B",
                    border: "1px solid #475569",
                    color: "#10B981",
                    padding: "9px 14px",
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: !sourceColumn || !targetColumn ? "not-allowed" : "pointer"
                  }}
                >
                  {isPreviewing ? "Executing DuckDB Join..." : "👁️ Preview Joined Records"}
                </button>
              </div>

              {/* VALIDATION RESULTS CARD */}
              {validationResult && (
                <div
                  style={{
                    background: "#0B0F19",
                    border: "1px solid #1E293B",
                    borderRadius: 8,
                    padding: 14,
                    display: "flex",
                    flexDirection: "column",
                    gap: 10
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#F8FAFC" }}>
                      Key Integrity Report
                    </span>
                    <div style={{ display: "flex", gap: 8 }}>
                      <span
                        style={{
                          background: validationResult.is_valid ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                          color: validationResult.is_valid ? "#10B981" : "#EF4444",
                          border: `1px solid ${validationResult.is_valid ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                          padding: "2px 8px",
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 700
                        }}
                      >
                        {validationResult.is_valid ? "VALID KEY LINK" : "INTEGRITY WARNING"}
                      </span>
                      <span
                        style={{
                          background: validationResult.risk_level === "LOW" ? "rgba(56, 189, 248, 0.15)" : "rgba(245, 158, 11, 0.15)",
                          color: validationResult.risk_level === "LOW" ? "#38BDF8" : "#F59E0B",
                          border: "1px solid #334155",
                          padding: "2px 8px",
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 700
                        }}
                      >
                        RISK: {validationResult.risk_level}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 12 }}>
                    <div style={{ background: "#111827", padding: "8px 10px", borderRadius: 6 }}>
                      <div style={{ fontWeight: 600, color: "#94A3B8" }}>Source Table Stats</div>
                      <div style={{ color: "#E2E8F0", marginTop: 4 }}>
                        Rows: <strong>{validationResult.source_stats.total_rows}</strong> • Distinct: <strong>{validationResult.source_stats.distinct_keys}</strong>
                      </div>
                      <div style={{ color: "#94A3B8", marginTop: 2, fontSize: 11 }}>
                        Nulls: {validationResult.source_stats.null_keys} • Unique: {validationResult.source_stats.is_unique ? "Yes" : "No"}
                      </div>
                    </div>

                    <div style={{ background: "#111827", padding: "8px 10px", borderRadius: 6 }}>
                      <div style={{ fontWeight: 600, color: "#94A3B8" }}>Target Table Stats</div>
                      <div style={{ color: "#E2E8F0", marginTop: 4 }}>
                        Rows: <strong>{validationResult.target_stats.total_rows}</strong> • Distinct: <strong>{validationResult.target_stats.distinct_keys}</strong>
                      </div>
                      <div style={{ color: "#94A3B8", marginTop: 2, fontSize: 11 }}>
                        Nulls: {validationResult.target_stats.null_keys} • Unique: {validationResult.target_stats.is_unique ? "Yes" : "No"}
                      </div>
                    </div>
                  </div>

                  {validationResult.warnings && validationResult.warnings.length > 0 && (
                    <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.25)", borderRadius: 6, padding: "8px 10px" }}>
                      {validationResult.warnings.map((w, idx) => (
                        <div key={idx} style={{ color: "#FDE68A", fontSize: 11, marginTop: idx > 0 ? 4 : 0 }}>
                          ⚠️ {w}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* JOIN PREVIEW TABLE */}
              {previewResult && (
                <div style={{ background: "#0B0F19", border: "1px solid #1E293B", borderRadius: 8, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "#10B981" }}>
                      Preview: Joined DuckDB Records ({previewResult.records.length} sample rows)
                    </span>
                    <span style={{ fontSize: 11, color: "#64748B" }}>
                      {previewResult.columns.length} columns combined
                    </span>
                  </div>

                  {previewResult.status === "error" ? (
                    <div style={{ color: "#FCA5A5", fontSize: 12 }}>
                      ❌ {previewResult.message}
                    </div>
                  ) : previewResult.records.length === 0 ? (
                    <div style={{ color: "#94A3B8", fontSize: 12, textAlign: "center", padding: 12 }}>
                      No matching records found with INNER JOIN on {sourceColumn} = {targetColumn}.
                    </div>
                  ) : (
                    <div style={{ overflowX: "auto", maxHeight: 220 }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
                        <thead>
                          <tr style={{ background: "#1E293B", color: "#94A3B8" }}>
                            {previewResult.columns.slice(0, 8).map((col) => (
                              <th key={col} style={{ padding: "6px 8px", borderBottom: "1px solid #334155", whiteSpace: "nowrap" }}>
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewResult.records.map((row, rIdx) => (
                            <tr key={rIdx} style={{ borderBottom: "1px solid #1E293B" }}>
                              {previewResult.columns.slice(0, 8).map((col) => (
                                <td key={col} style={{ padding: "6px 8px", color: "#E2E8F0", whiteSpace: "nowrap" }}>
                                  {row[col] !== null && row[col] !== undefined ? String(row[col]) : "-"}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* FOOTER ACTIONS */}
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, borderTop: "1px solid #1E293B", paddingTop: 16 }}>
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  style={{
                    background: "transparent",
                    border: "1px solid #475569",
                    color: "#94A3B8",
                    padding: "9px 16px",
                    borderRadius: 8,
                    fontSize: 13,
                    cursor: "pointer"
                  }}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={isSaving || !sourceColumn || !targetColumn}
                  style={{
                    background: "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)",
                    border: "1px solid #38BDF8",
                    color: "#FFFFFF",
                    padding: "9px 20px",
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: isSaving || !sourceColumn || !targetColumn ? "not-allowed" : "pointer",
                    boxShadow: "0 2px 8px rgba(2, 132, 199, 0.4)"
                  }}
                >
                  {isSaving ? "Saving Relationship..." : "💾 Save Relationship"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ━━━ MODAL: VIEW EXISTING RELATIONSHIP PREVIEW ━━━ */}
      {isPreviewModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 16
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsPreviewModalOpen(false);
          }}
        >
          <div
            style={{
              background: "#0F172A",
              border: "1px solid #334155",
              borderRadius: 14,
              width: "100%",
              maxWidth: 840,
              maxHeight: "85vh",
              overflowY: "auto",
              padding: "24px 28px",
              boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
              color: "#F8FAFC"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1E293B", paddingBottom: 12 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 700, color: "#F8FAFC" }}>
                  {activePreviewTitle || "Cross-Dataset Join Preview"}
                </div>
                <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                  Live DuckDB query executing relational inner join across isolated database files.
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsPreviewModalOpen(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#94A3B8",
                  fontSize: 20,
                  cursor: "pointer"
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginTop: 16 }}>
              {isPreviewing ? (
                <div style={{ textAlign: "center", padding: "40px 0", color: "#38BDF8" }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>⚡</div>
                  <div>Querying joined DuckDB records...</div>
                </div>
              ) : previewResult && previewResult.status === "success" ? (
                <div>
                  <div style={{ fontSize: 12, color: "#94A3B8", marginBottom: 10 }}>
                    Displaying first {previewResult.records.length} joined records across {previewResult.columns.length} columns:
                  </div>
                  <div style={{ overflowX: "auto", maxHeight: 380, border: "1px solid #1E293B", borderRadius: 8 }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
                      <thead>
                        <tr style={{ background: "#1E293B", color: "#94A3B8" }}>
                          {previewResult.columns.map((col) => (
                            <th key={col} style={{ padding: "8px 10px", borderBottom: "1px solid #334155", whiteSpace: "nowrap" }}>
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {previewResult.records.map((row, rIdx) => (
                          <tr key={rIdx} style={{ borderBottom: "1px solid #1E293B" }}>
                            {previewResult.columns.map((col) => (
                              <td key={col} style={{ padding: "8px 10px", color: "#E2E8F0", whiteSpace: "nowrap" }}>
                                {row[col] !== null && row[col] !== undefined ? String(row[col]) : "-"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "30px 0", color: "#FCA5A5" }}>
                  {previewResult?.message || "No join records returned."}
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setIsPreviewModalOpen(false)}
                style={{
                  background: "#1E293B",
                  border: "1px solid #475569",
                  color: "#E2E8F0",
                  padding: "8px 16px",
                  borderRadius: 8,
                  fontSize: 13,
                  cursor: "pointer"
                }}
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
