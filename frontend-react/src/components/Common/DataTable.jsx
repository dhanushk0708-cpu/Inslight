import { fmt } from "../../utils/formatters";

export default function DataTable({ data, title = "Data" }) {
  if (!data?.length) {
    return null;
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column.replace(/_/g, " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, rowIndex) => (
              <tr key={`row-${rowIndex}`}>
                {columns.map((column) => (
                  <td key={`${rowIndex}-${column}`}>
                    {typeof row[column] === "number"
                      ? fmt(row[column])
                      : String(row[column] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
