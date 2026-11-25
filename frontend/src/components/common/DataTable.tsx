import React from "react";

function fmt(v: any, colName?: string): string {
  if (v == null || isNaN(v)) return "0";
  const n = Number(v);
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  const isCount = colName && /unit|qty|count|item|row|id/i.test(colName);
  const pfx = isCount ? "" : (colName && /revenue|sales|price|profit|cost|amount/i.test(colName)) ? "₹" : "";
  if (abs >= 1e7) return `${sign}${pfx}${(abs / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${sign}${pfx}${(abs / 1e5).toFixed(2)} L`;
  if (abs >= 1e3) return `${sign}${pfx}${(abs / 1e3).toFixed(1)} K`;
  return `${sign}${pfx}${abs % 1 === 0 ? abs.toLocaleString("en-IN") : abs.toFixed(1)}`;
}

interface DataTableProps {
  data: Array<Record<string, any>>;
  title?: string;
}

export const DataTable: React.FC<DataTableProps> = React.memo(({ data, title = "Data" }) => {
  if (!data?.length) return null;
  const cols = Object.keys(data[0]);

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c}>{c.replace(/_/g, " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, i) => (
              <tr key={i}>
                {cols.map((c) => (
                  <td key={c}>
                    {typeof row[c] === "number" ? fmt(row[c], c) : String(row[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});

DataTable.displayName = "DataTable";
