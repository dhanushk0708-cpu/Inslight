import json
from typing import List, Dict, Any, Optional
from app.models.dataset import Dataset
from app.core.logging import logger


class RAGService:
    @staticmethod
    def build_dataset_context(dataset: Dataset) -> Dict[str, Any]:
        """
        Builds structured metadata catalog for the user's dataset.
        Extracts column names, semantic types, sample values, and summary statistics.
        """
        if not dataset.schema_metadata:
            return {
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "columns": [],
                "formatted_schema": f"Table: {dataset.table_name} ({dataset.row_count} rows)"
            }

        try:
            meta = json.loads(dataset.schema_metadata)
            columns = [c["name"] for c in meta.get("column_info", [])]

            schema_lines = [
                f"Table Name: {dataset.table_name}",
                f"Total Records: {dataset.row_count}",
                "Columns and Types:"
            ]
            for col in meta.get("column_info", []):
                name = col.get("name")
                dtype = col.get("dtype")
                semantic = col.get("semantic_type", "general")
                samples = ", ".join(str(s) for s in col.get("sample_values", [])[:4])
                schema_lines.append(f"  - [{name}] ({dtype}, {semantic}) | Examples: {samples}")

            return {
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "columns": columns,
                "formatted_schema": "\n".join(schema_lines),
                "data_quality_score": meta.get("data_quality_score", 100.0)
            }
        except Exception as e:
            logger.error(f"Error parsing dataset schema metadata: {e}")
            return {
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "columns": [],
                "formatted_schema": f"Table: {dataset.table_name} ({dataset.row_count} rows)"
            }

    @staticmethod
    def retrieve_relevant_columns(question: str, all_columns: List[str]) -> List[str]:
        """
        Identifies relevant columns for the query to prune unnecessary prompt tokens.
        """
        q = question.lower()
        matched = []
        for col in all_columns:
            clean = col.lower().replace("_", " ")
            if clean in q or any(term in q for term in clean.split()):
                matched.append(col)

        # Always include at least categorical/date/metric candidates if few matches
        return matched if matched else all_columns[:15]
