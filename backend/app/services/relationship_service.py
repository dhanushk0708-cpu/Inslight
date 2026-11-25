import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import duckdb
from app.models.user import User
from app.models.dataset import Dataset
from app.models.relationship import DatasetRelationship
from app.services.dataset_service import DatasetService
from app.core.logging import logger


class DatasetRelationshipService:
    """
    Multi-Dataset Relational Intelligence Service.
    Enables linking, validating, and querying related datasets (e.g. Sales + Products or Sales + Customers).
    Performs key integrity checks (nulls, duplicates) and protects against accidental many-to-many row explosion.
    """

    @classmethod
    def detect_candidate_join_keys(
        cls,
        conn_source: duckdb.DuckDBPyConnection,
        source_table: str,
        conn_target: duckdb.DuckDBPyConnection,
        target_table: str
    ) -> List[Dict[str, Any]]:
        """
        Identify matching candidate keys based on column names and compatible types.
        """
        source_cols = conn_source.execute(f"DESCRIBE {source_table}").df()
        target_cols = conn_target.execute(f"DESCRIBE {target_table}").df()

        src_names = {r["column_name"].lower(): r["column_name"] for _, r in source_cols.iterrows()}
        tgt_names = {r["column_name"].lower(): r["column_name"] for _, r in target_cols.iterrows()}

        candidate_keys = []
        for low_name, actual_src in src_names.items():
            if low_name in tgt_names:
                actual_tgt = tgt_names[low_name]
                candidate_keys.append({
                    "source_column": actual_src,
                    "target_column": actual_tgt,
                    "match_type": "Exact Name Match"
                })

        # Also check common foreign key naming patterns (e.g. id <-> product_id)
        for actual_src in src_names.values():
            for actual_tgt in tgt_names.values():
                if actual_src.lower() != actual_tgt.lower():
                    if (actual_src.lower().endswith("_id") and actual_tgt.lower() == "id") or \
                       (actual_tgt.lower().endswith("_id") and actual_src.lower() == "id"):
                        candidate_keys.append({
                            "source_column": actual_src,
                            "target_column": actual_tgt,
                            "match_type": "ID Foreign Key Match"
                        })

        return candidate_keys

    @classmethod
    def validate_relationship(
        cls,
        conn_source: duckdb.DuckDBPyConnection,
        source_table: str,
        conn_target: duckdb.DuckDBPyConnection,
        target_table: str,
        source_col: str,
        target_col: str
    ) -> Dict[str, Any]:
        """
        Validate join key integrity, check nulls and duplicates, and determine relationship cardinality.
        """
        # Source table stats
        src_total = conn_source.execute(f"SELECT COUNT(*) FROM {source_table}").fetchone()[0]
        src_nulls = conn_source.execute(f"SELECT COUNT(*) FROM {source_table} WHERE {source_col} IS NULL").fetchone()[0]
        src_distinct = conn_source.execute(f"SELECT COUNT(DISTINCT {source_col}) FROM {source_table}").fetchone()[0]

        # Target table stats
        tgt_total = conn_target.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
        tgt_nulls = conn_target.execute(f"SELECT COUNT(*) FROM {target_table} WHERE {target_col} IS NULL").fetchone()[0]
        tgt_distinct = conn_target.execute(f"SELECT COUNT(DISTINCT {target_col}) FROM {target_table}").fetchone()[0]

        # Cardinality Assessment
        src_has_duplicates = src_total > src_distinct
        tgt_has_duplicates = tgt_total > tgt_distinct

        if not src_has_duplicates and not tgt_has_duplicates:
            cardinality = "one_to_one"
            risk_level = "LOW"
            cardinality_warning = None
        elif src_has_duplicates and not tgt_has_duplicates:
            cardinality = "many_to_one"
            risk_level = "LOW"
            cardinality_warning = None
        elif not src_has_duplicates and tgt_has_duplicates:
            cardinality = "one_to_many"
            risk_level = "MEDIUM"
            cardinality_warning = "One-to-Many relationship may duplicate primary metrics during aggregations."
        else:
            cardinality = "many_to_many"
            risk_level = "HIGH"
            cardinality_warning = "Many-to-Many relationship detected! Cartesian join will multiply metric sums. Aggregation before join is strongly recommended."

        is_valid = True
        warnings = []
        if src_nulls > 0:
            warnings.append(f"Source key '{source_col}' has {src_nulls} null rows ({round(src_nulls/src_total*100, 1)}%). Unmatched records will be omitted in INNER JOIN.")
        if tgt_nulls > 0:
            warnings.append(f"Target key '{target_col}' has {tgt_nulls} null rows.")
        if cardinality_warning:
            warnings.append(cardinality_warning)

        return {
            "is_valid": is_valid,
            "source_column": source_col,
            "target_column": target_col,
            "cardinality": cardinality,
            "risk_level": risk_level,
            "warnings": warnings,
            "source_stats": {
                "total_rows": src_total,
                "null_keys": src_nulls,
                "distinct_keys": src_distinct,
                "is_unique": not src_has_duplicates
            },
            "target_stats": {
                "total_rows": tgt_total,
                "null_keys": tgt_nulls,
                "distinct_keys": tgt_distinct,
                "is_unique": not tgt_has_duplicates
            }
        }

    @classmethod
    def execute_joined_preview(
        cls,
        source_db_path: str,
        source_table: str,
        target_db_path: str,
        target_table: str,
        source_col: str,
        target_col: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Execute cross-dataset join in DuckDB attaching target database.
        """
        import os
        conn = duckdb.connect()
        try:
            source_p = os.path.abspath(source_db_path).replace("\\", "/")
            target_p = os.path.abspath(target_db_path).replace("\\", "/")
            conn.execute(f"ATTACH '{source_p}' AS db_src (READ_ONLY)")
            conn.execute(f"ATTACH '{target_p}' AS db_tgt (READ_ONLY)")

            query = f"""
                SELECT s.*, t.*
                FROM db_src.{source_table} s
                INNER JOIN db_tgt.{target_table} t
                  ON CAST(s.{source_col} AS VARCHAR) = CAST(t.{target_col} AS VARCHAR)
                LIMIT {limit}
            """
            df_join = conn.execute(query).df()
            records = json.loads(df_join.to_json(orient="records", default_handler=str))
            cols = list(df_join.columns)
            return {
                "status": "success",
                "columns": cols,
                "records": records,
                "total_preview_count": len(records)
            }
        except Exception as e:
            logger.error(f"Cross-dataset join failed: {e}")
            return {"status": "error", "message": f"Join execution failed: {str(e)}"}
        finally:
            conn.close()

    # ━━━━━━━━ RELATIONSHIP PERSISTENCE ━━━━━━━━

    @classmethod
    def create_relationship(
        cls,
        db: Session,
        user_id: str,
        source_dataset_id: str,
        target_dataset_id: str,
        source_col: str,
        target_col: str,
        relationship_type: str = "many_to_one"
    ) -> DatasetRelationship:
        """Save a confirmed relationship in PostgreSQL/SQLite."""
        type_mapping = {
            "1:1": "one_to_one",
            "1:N": "one_to_many",
            "N:1": "many_to_one",
            "N:M": "many_to_many",
            "ONE_TO_ONE": "one_to_one",
            "ONE_TO_MANY": "one_to_many",
            "MANY_TO_ONE": "many_to_one",
            "MANY_TO_MANY": "many_to_many",
        }
        normalized_type = type_mapping.get(relationship_type.strip().upper(), relationship_type.strip().lower())

        rel = DatasetRelationship(
            user_id=user_id,
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id,
            source_column=source_col,
            target_column=target_col,
            relationship_type=normalized_type,
            cardinality_status="verified"
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)
        return rel

    @classmethod
    def list_relationships(cls, db: Session, user_id: str) -> List[DatasetRelationship]:
        """List all dataset relationships defined by user."""
        return db.query(DatasetRelationship).filter(DatasetRelationship.user_id == user_id).all()

    @classmethod
    def delete_relationship(cls, db: Session, user_id: str, rel_id: str) -> bool:
        """Remove relationship."""
        rel = db.query(DatasetRelationship).filter(DatasetRelationship.id == rel_id, DatasetRelationship.user_id == user_id).first()
        if not rel:
            return False
        db.delete(rel)
        db.commit()
        return True
