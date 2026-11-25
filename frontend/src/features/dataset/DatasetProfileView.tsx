import React from "react";
import { DatasetProfile } from "../../types";
import { DataTable } from "../../components/common/DataTable";

interface DatasetProfileViewProps {
  profile: DatasetProfile | null;
}

export const DatasetProfileView: React.FC<DatasetProfileViewProps> = ({ profile }) => {
  if (!profile) return null;

  return (
    <div>
      <div className="card">
        <div className="card-title">Dataset Profile & Data Quality</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          <div style={{ padding: 16, background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)", textAlign: "center", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 26, fontWeight: 800, color: "var(--accent-light)" }}>{profile.rows.toLocaleString()}</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", marginTop: 4, fontWeight: 600 }}>Rows</div>
          </div>
          <div style={{ padding: 16, background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)", textAlign: "center", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 26, fontWeight: 800, color: "var(--accent-light)" }}>{profile.columns}</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", marginTop: 4, fontWeight: 600 }}>Columns</div>
          </div>
          <div style={{ padding: 16, background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)", textAlign: "center", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 26, fontWeight: 800, color: "var(--green)" }}>{profile.data_quality_score}%</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", marginTop: 4, fontWeight: 600 }}>Quality Score</div>
          </div>
        </div>
      </div>

      {profile.column_info?.length > 0 && (
        <DataTable
          data={profile.column_info.map((c) => ({
            Column: c.name,
            Type: c.semantic_type,
            Unique: c.unique_count,
            Nulls: c.null_count,
            Samples: c.sample_values?.slice(0, 3).join(", ")
          }))}
          title="Dataset Schema"
        />
      )}

      {profile.preview?.length > 0 && (
        <DataTable data={profile.preview} title="Data Preview (First 5 Rows)" />
      )}
    </div>
  );
};
