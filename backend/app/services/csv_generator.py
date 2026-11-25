import io
import csv
from typing import List, Dict, Any
from app.services.excel_generator import sanitize_formula_injection


class CSVReportGenerator:
    @classmethod
    def generate(cls, table_data: List[Dict[str, Any]]) -> bytes:
        """
        Generate CSV bytes with formula injection sanitization.
        """
        if not table_data:
            return b"message\nNo data records available\n"

        output = io.StringIO()
        fieldnames = list(table_data[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for row in table_data:
            sanitized_row = {
                k: sanitize_formula_injection(v)
                for k, v in row.items()
            }
            writer.writerow(sanitized_row)

        return output.getvalue().encode("utf-8")
