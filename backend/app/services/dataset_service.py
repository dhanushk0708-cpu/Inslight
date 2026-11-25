import os
import re
import json
import uuid
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.utils.csv_reader import read_csv_safe


class DatasetService:
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize columns, parse dates and convert numeric strings."""
        df = df.copy()

        # Normalize column names
        df.columns = [
            re.sub(r"[^\w]", "_", str(c).strip().lower()).strip("_")
            for c in df.columns
        ]

        # Remove fully empty and duplicate columns
        df = df.dropna(axis=1, how="all")
        df = df.loc[:, ~df.columns.duplicated()]

        # Parse date columns
        for col in df.columns:
            if any(kw in col.lower() for kw in ["date", "datetime", "timestamp"]):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

        # Force numeric on likely numeric columns
        numeric_hints = [
            "price", "cost", "revenue", "amount", "total", "quantity",
            "units", "sold", "profit", "discount", "rating", "review",
            "count", "score", "margin", "tax", "fee", "salary"
        ]
        for col in df.columns:
            if any(hint in col.lower() for hint in numeric_hints) and df[col].dtype == "object":
                try:
                    cleaned = (
                        df[col]
                        .astype(str)
                        .str.replace(r"[$,₹€£\s]", "", regex=True)
                        .str.replace(",", "", regex=False)
                    )
                    df[col] = pd.to_numeric(cleaned, errors="coerce")
                except Exception:
                    pass

        # Derive missing business columns
        if "total_revenue" not in df.columns:
            if "price" in df.columns and "quantity_sold" in df.columns:
                df["total_revenue"] = df["price"] * df["quantity_sold"]
            elif "price" in df.columns and "quantity" in df.columns:
                df["total_revenue"] = df["price"] * df["quantity"]

        if "discount_amount" not in df.columns:
            if "price" in df.columns and "discounted_price" in df.columns:
                df["discount_amount"] = df["price"] - df["discounted_price"]
            elif "price" in df.columns and "discount_price" in df.columns:
                df["discount_amount"] = df["price"] - df["discount_price"]

        if "discount_pct" not in df.columns and "price" in df.columns and "discount_amount" in df.columns:
            df["discount_pct"] = (df["discount_amount"] / df["price"] * 100).round(1)

        return df

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Compute dataset statistics, null values, and sample previews."""
        column_info = []
        missing = {}
        for col in df.columns:
            info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "unique_count": int(df[col].nunique()),
                "sample_values": [str(v) for v in df[col].dropna().unique()[:5]],
                "null_count": int(df[col].isnull().sum()),
            }
            if "date" in col.lower():
                info["semantic_type"] = "date"
            elif "id" in col.lower() and "sl" not in col.lower():
                info["semantic_type"] = "identifier"
            elif pd.api.types.is_numeric_dtype(df[col]):
                info["semantic_type"] = "numeric"
                s = df[col].dropna()
                if len(s) > 0:
                    info["stats"] = {
                        "mean": round(float(s.mean()), 2),
                        "min": round(float(s.min()), 2),
                        "max": round(float(s.max()), 2),
                    }
            else:
                info["semantic_type"] = "categorical"

            column_info.append(info)
            if df[col].isnull().sum() > 0:
                missing[col] = int(df[col].isnull().sum())

        total_cells = df.shape[0] * df.shape[1]
        quality = round((1 - sum(missing.values()) / total_cells) * 100, 1) if total_cells else 100.0

        suggested_questions = [
            f"What is the total revenue by category?",
            f"Show monthly trend over time",
            f"What are the top 5 products by sales?"
        ]

        return {
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_info": column_info,
            "data_quality_score": quality,
            "missing_values": missing,
            "suggested_questions": suggested_questions,
            "preview": json.loads(df.head(5).to_json(orient="records", default_handler=str)),
        }

    @classmethod
    def get_duckdb_path(cls, user_id: str, dataset_id: str) -> str:
        """Get the isolated DuckDB storage path for a given user and dataset."""
        return os.path.join(settings.DATASET_STORAGE_DIR, user_id, f"{dataset_id}.duckdb")

    @classmethod
    def save_and_register_dataset(
        cls,
        db: Session,
        user_id: str,
        file_bytes: bytes,
        filename: str
    ) -> Tuple[Dataset, Dict[str, Any]]:
        """
        Parses CSV, saves to an isolated DuckDB file under user's directory,
        and registers dataset in PostgreSQL/SQLite.
        """
        # Read CSV safely
        df_raw = read_csv_safe(file_bytes, is_bytes=True)
        df = cls.normalize_dataframe(df_raw)

        dataset_id = str(uuid.uuid4())
        user_storage_dir = os.path.join(settings.DATASET_STORAGE_DIR, user_id)
        os.makedirs(user_storage_dir, exist_ok=True)

        storage_path = os.path.join(user_storage_dir, f"{dataset_id}.duckdb")
        table_name = "sales_data"  # Standardized internal table name per isolated DuckDB file

        # Write to isolated DuckDB file
        conn = duckdb.connect(storage_path)
        conn.register("df_temp", df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_temp")
        conn.close()

        # Generate profile and schema metadata
        profile = cls.profile_dataframe(df, filename)
        profile["id"] = dataset_id

        # Register in database repository
        dataset = DatasetRepository.create(
            db=db,
            user_id=user_id,
            original_filename=filename,
            table_name=table_name,
            storage_path=storage_path,
            row_count=len(df),
            column_count=len(df.columns),
            schema_metadata=json.dumps(profile)
        )

        return dataset, profile

    @classmethod
    def load_seed_for_user(cls, db: Session, user_id: str) -> Optional[Tuple[Dataset, Dict[str, Any]]]:
        """Loads default sample_sales.csv for new users if requested."""
        seed_paths = [
            "data/sample_sales.csv",
            "backend/data/sample_sales.csv",
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_sales.csv")
        ]
        seed_file = next((p for p in seed_paths if os.path.exists(p)), None)
        if not seed_file:
            return None

        with open(seed_file, "rb") as f:
            content = f.read()
        return cls.save_and_register_dataset(db, user_id, content, "sample_sales.csv")

    @staticmethod
    def get_duckdb_connection(storage_path: str, read_only: bool = True):
        """Get DuckDB connection for query execution."""
        return duckdb.connect(storage_path, read_only=read_only)
