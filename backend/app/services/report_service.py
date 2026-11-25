import os
import json
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import duckdb
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.models.report import Report
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.report_repository import ReportRepository
from app.services.pdf_generator import PDFReportGenerator
from app.services.excel_generator import ExcelReportGenerator
from app.services.csv_generator import CSVReportGenerator
from app.services.report_analytics_service import ReportAnalyticsService
from app.analytics.anomaly_detection import AnomalyDetector
from app.services.dataset_service import DatasetService


class ReportService:
    @classmethod
    async def generate_report(
        cls,
        db: Session,
        user: User,
        title: str,
        report_format: str = "pdf",
        dataset_id: Optional[str] = None,
        report_type: str = "executive",
        include_anomalies: bool = True,
        custom_query_data: Optional[Dict[str, Any]] = None
    ) -> Report:
        """
        Orchestrate complete report generation using actual analytics data.
        """
        # 1. Resolve dataset with ownership check
        dataset = None
        if dataset_id:
            dataset = DatasetRepository.get_by_id(db, dataset_id=dataset_id, user_id=user.id)
            if not dataset:
                raise ValueError(f"Dataset '{dataset_id}' not found or access denied.")
        else:
            dataset = DatasetRepository.get_latest_for_user(db, user_id=user.id)

        if not dataset:
            seed = DatasetService.load_seed_for_user(db, user_id=user.id)
            if seed:
                dataset, _ = seed
            else:
                raise ValueError("No dataset found. Please upload a dataset first.")

        dataset_name = dataset.original_filename
        fmt = report_format.lower()
        now = datetime.now(timezone.utc)

        # 2. If custom query data was passed (e.g. user exported active table from Studio)
        kpis_count = 0
        anomalies_count = 0

        if custom_query_data and custom_query_data.get("table_data"):
            table_data = custom_query_data.get("table_data", [])
            kpi_cards = custom_query_data.get("kpi_cards", [])
            narrative = custom_query_data.get("narrative", "")
            profile = json.loads(dataset.schema_metadata) if dataset.schema_metadata else {}
            kpis_count = len(kpi_cards)

            if fmt == "pdf":
                file_bytes = PDFReportGenerator.generate(
                    title=title,
                    dataset_name=dataset_name,
                    kpi_cards=kpi_cards,
                    narrative=narrative,
                    table_data=table_data,
                    data_quality=profile,
                    generated_at=now
                )
                ext = "pdf"
            elif fmt == "excel":
                file_bytes = ExcelReportGenerator.generate(
                    title=title,
                    dataset_name=dataset_name,
                    kpi_cards=kpi_cards,
                    narrative=narrative,
                    table_data=table_data,
                    data_quality=profile,
                    generated_at=now
                )
                ext = "xlsx"
            elif fmt == "csv":
                file_bytes = CSVReportGenerator.generate(table_data=table_data)
                ext = "csv"
            else:
                raise ValueError(f"Unsupported report format: {fmt}")
        else:
            # 3. Comprehensive Centralized Analytics Engine
            analytics = await ReportAnalyticsService.analyze_dataset_for_report(
                dataset=dataset,
                include_anomalies=include_anomalies,
                report_type=report_type
            )
            kpis_count = len(analytics.get("kpis", {}).get("cards", []))
            anomalies_count = len(analytics.get("anomalies", []))

            # Sample raw partition data for tables / exports
            conn = duckdb.connect(dataset.storage_path, read_only=True)
            df_sample = conn.execute(f"SELECT * FROM {dataset.table_name} LIMIT 100").df()
            table_data = json.loads(df_sample.to_json(orient="records", default_handler=str))
            conn.close()

            if fmt == "pdf":
                file_bytes = PDFReportGenerator.generate_comprehensive_report(
                    analytics=analytics,
                    title=title
                )
                ext = "pdf"
            elif fmt == "excel":
                file_bytes = ExcelReportGenerator.generate_comprehensive_workbook(
                    analytics=analytics,
                    raw_table_data=table_data
                )
                ext = "xlsx"
            elif fmt == "csv":
                file_bytes = CSVReportGenerator.generate(table_data=table_data)
                ext = "csv"
            else:
                raise ValueError(f"Unsupported report format: {fmt}")

        # 4. Save file under isolated user directory
        report_id = str(uuid.uuid4())
        user_dir = os.path.join(settings.REPORT_STORAGE_DIR, user.id)
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, f"{report_id}.{ext}")

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)

        # 5. Persist record in database
        report = ReportRepository.create_report(
            db=db,
            user_id=user.id,
            name=title,
            report_format=fmt,
            file_path=file_path,
            file_size=file_size,
            dataset_id=dataset.id,
            parameters_json=json.dumps({
                "dataset_name": dataset_name,
                "row_count": len(table_data),
                "kpis_count": kpis_count,
                "anomalies_count": anomalies_count,
                "report_type": report_type
            }),
            status="generated"
        )
        return report
