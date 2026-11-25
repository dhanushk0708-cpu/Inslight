import DataTable from "../Common/DataTable";

export default function UploadProfile({ viewData }) {
  return (
    <div className="slide-up">
      <div className="card">
        <div className="card-title">Dataset Profile</div>
        <div className="profile-grid">
          <div className="profile-stat">
            <div className="profile-stat-value">
              {viewData.rows?.toLocaleString()}
            </div>
            <div className="profile-stat-label">Rows</div>
          </div>
          <div className="profile-stat">
            <div className="profile-stat-value">{viewData.columns}</div>
            <div className="profile-stat-label">Columns</div>
          </div>
          <div className="profile-stat">
            <div className="profile-stat-value">{viewData.data_quality_score}%</div>
            <div className="profile-stat-label">Quality</div>
          </div>
        </div>
      </div>

      {viewData.column_info && (
        <DataTable
          data={viewData.column_info.map((column) => ({
            Column: column.name,
            Type: column.semantic_type,
            Unique: column.unique_count,
            Nulls: column.null_count,
            Samples: column.sample_values?.slice(0, 3).join(", "),
          }))}
          title="Columns"
        />
      )}
    </div>
  );
}
