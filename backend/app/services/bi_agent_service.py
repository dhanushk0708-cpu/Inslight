import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.services.business_guard import BusinessContextGuard, GUARD_REJECTION_MESSAGE, NO_DATASET_MESSAGE
from app.services.query_service import QueryService
from app.services.root_cause_service import RootCauseService
from app.services.forecasting_service import ForecastingService
from app.services.advanced_anomaly_service import AdvancedAnomalyService
from app.services.comparison_service import ComparisonService
from app.services.data_quality_service import DataQualityService
from app.services.strategic_analysis_service import StrategicAnalysisService
from app.services.ai_service import ai_service
from app.core.logging import logger


class BIAgentService:
    """
    AI Business Intelligence Agent Orchestrator.
    Understands high-level business inquiries and selects appropriate validated analytical tools
    (Root Cause Analysis, Forecasting, Anomaly Detection, Comparative Analytics, or SQL).
    Synthesizes evidence-backed conclusions and explains reasoning step-by-step.
    """

    @classmethod
    async def process_business_inquiry(
        cls,
        db: Session,
        user: User,
        dataset: Dataset,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-step business analysis based on user intent.
        """
        # 1. Business Context Guard Check
        is_valid, reject_msg = await BusinessContextGuard.validate_query(
            question=question,
            has_dataset=bool(dataset)
        )
        if not is_valid:
            return {
                "status": "rejected",
                "answer": reject_msg or GUARD_REJECTION_MESSAGE,
                "reasoning_steps": ["Inquiry screened by Business Context Guard."],
                "tool_used": "business_guard",
                "evidence": None,
                "suggested_follow_ups": [
                    "What was our total revenue last quarter?",
                    "Which product category has the highest sales?",
                    "Why did sales drop in November?"
                ]
            }

        q_lower = question.lower()
        reasoning_steps = [
            f"1. Interpreted business question: '{question}'.",
            f"2. Validated against active dataset '{dataset.original_filename}' ({dataset.row_count:,} records)."
        ]

        conn = DatasetService.get_duckdb_connection(dataset.storage_path, read_only=True)
        try:
            # 2. Tool Intent Classification
            # Tool A: Strategic Business Performance & Opportunities/Risks Analysis
            if any(k in q_lower for k in [
                "opportunity", "opportunities", "risk", "risks",
                "business performance", "performance overview", "complete business overview",
                "business overview", "executive overview", "company overview",
                "top-performing", "top performing", "top product", "top products", "best product",
                "highest revenue product", "highest sales product",
                "underperforming", "underperforming regions", "underperforming products", "weak regions", "lagging",
                "what is driving my revenue", "revenue drivers", "key drivers", "driving my sales",
                "where am i losing money", "losing money", "unprofitable", "lowest margin",
                "business trends", "important business trends", "growth trends",
                "what should management focus on", "management focus", "strategic recommendations"
            ]):
                strat_res = StrategicAnalysisService.analyze_business_performance(
                    conn=conn,
                    table_name=dataset.table_name,
                    question=question,
                    dataset_name=dataset.original_filename
                )
                return strat_res

            # Tool B: Root Cause Analysis ("why did", "cause", "drop", "decline", "fell", "reason for")
            elif any(k in q_lower for k in ["why did", "why has", "root cause", "reason for", "why revenue", "why sales", "why profit", "decline", "dropped"]):
                reasoning_steps.append("3. Detected diagnostic intent: User seeking explanation for metric variation.")
                reasoning_steps.append("4. Invoked Root Cause Analysis Engine (Dimensional contribution & Price-Volume decomposition).")
                rca_result = RootCauseService.analyze_root_cause(conn, dataset.table_name)

                # Synthesize explanation
                synthesis = await cls._synthesize_agent_response(
                    question=question,
                    tool_name="Root Cause Analysis",
                    findings=rca_result
                )
                reasoning_steps.append("5. Synthesized evidence-backed root cause explanation.")

                return {
                    "status": "success",
                    "tool_used": "root_cause_analysis",
                    "answer": synthesis,
                    "summary": synthesis[:200],
                    "reasoning_steps": reasoning_steps,
                    "analytical_steps": reasoning_steps,
                    "data": rca_result,
                    "evidence": {
                        "primary_driver": rca_result.get("price_volume_decomposition", {}).get("primary_driver") if rca_result.get("price_volume_decomposition") else "Segment Variance",
                        "top_contributor": rca_result.get("top_contributors", [{}])[0].get("segment", "General") if rca_result.get("top_contributors") else "General",
                        "absolute_change": rca_result.get("formatted_change")
                    },
                    "suggested_follow_ups": [
                        "Would you like to forecast revenue for the next period?",
                        "Should we inspect regional anomaly patterns?",
                        "Run a detailed period-over-period comparison?"
                    ]
                }

            # Tool B: Predictive Forecasting ("forecast", "predict", "next month", "future", "projection")
            elif any(k in q_lower for k in ["forecast", "predict", "future", "projection", "next 30 days", "next month", "trend forecast"]):
                reasoning_steps.append("3. Detected predictive intent: User seeking time-series projection.")
                reasoning_steps.append("4. Invoked Forecasting Service (Historical backtest with prediction intervals).")
                fc_result = ForecastingService.generate_forecast(conn, dataset.table_name, horizon=30)

                synthesis = await cls._synthesize_agent_response(
                    question=question,
                    tool_name="Predictive Forecasting",
                    findings=fc_result
                )
                reasoning_steps.append("5. Evaluated model accuracy (MAE, RMSE, MAPE) and formed projection summary.")

                return {
                    "status": "success",
                    "tool_used": "forecasting",
                    "answer": synthesis,
                    "reasoning_steps": reasoning_steps,
                    "data": fc_result,
                    "evidence": {
                        "projected_total": fc_result.get("formatted_forecast_total"),
                        "trend_direction": fc_result.get("trend_direction"),
                        "model": fc_result.get("method_used")
                    },
                    "suggested_follow_ups": [
                        "What factors could accelerate this projected trend?",
                        "Can we compare this forecast to previous seasonal peaks?",
                        "Generate a boardroom report with this forecast."
                    ]
                }

            # Tool C: Anomaly Detection ("anomaly", "unusual", "outlier", "risk", "spike", "drop")
            elif any(k in q_lower for k in ["anomaly", "anomalies", "outlier", "unusual", "irregular", "spike"]):
                reasoning_steps.append("3. Detected anomaly audit intent: User inspecting unusual transactions.")
                reasoning_steps.append("4. Executed multi-method anomaly detection (Z-score, IQR, and Isolation Forest).")
                anom_result = AdvancedAnomalyService.detect_anomalies(conn, dataset.table_name)

                synthesis = await cls._synthesize_agent_response(
                    question=question,
                    tool_name="Advanced Anomaly Detection",
                    findings=anom_result
                )
                reasoning_steps.append("5. Filtered positive opportunities vs negative operational risks.")

                return {
                    "status": "success",
                    "tool_used": "anomaly_detection",
                    "answer": synthesis,
                    "reasoning_steps": reasoning_steps,
                    "data": anom_result,
                    "evidence": {
                        "anomalies_count": anom_result.get("anomalies_detected_count"),
                        "risks": anom_result.get("risks_count"),
                        "opportunities": anom_result.get("opportunities_count")
                    },
                    "suggested_follow_ups": [
                        "Should we configure an automated alert for these outliers?",
                        "What is the root cause behind the highest deviation transaction?",
                        "Review data quality of these flagged rows."
                    ]
                }

            # Tool D: Comparative Analysis ("compare", "vs", "versus", "difference between", "better than")
            elif any(k in q_lower for k in ["compare", " versus ", " vs ", "difference between", "benchmark"]):
                reasoning_steps.append("3. Detected comparative benchmark intent.")
                reasoning_steps.append("4. Invoked Comparative Analytics Engine (MoM / Segment delta & share).")
                comp_result = ComparisonService.compare_periods_or_segments(conn, dataset.table_name)

                synthesis = await cls._synthesize_agent_response(
                    question=question,
                    tool_name="Comparative Analytics",
                    findings=comp_result
                )
                reasoning_steps.append("5. Formulated comparative delta summary.")

                return {
                    "status": "success",
                    "tool_used": "comparative_analytics",
                    "answer": synthesis,
                    "reasoning_steps": reasoning_steps,
                    "data": comp_result,
                    "evidence": comp_result.get("latest_comparison") or comp_result.get("segment_a"),
                    "suggested_follow_ups": [
                        "Why did the trailing segment underperform?",
                        "Create a comparative dashboard widget.",
                        "Inspect underlying data quality."
                    ]
                }

            # Tool F: Standard SQL Analytics Gateway (Fallback for specific ad-hoc aggregation)
            else:
                reasoning_steps.append("3. Evaluating question via structured SQL analytics pipeline.")
                query_res = await QueryService.process_user_query(
                    db=db,
                    user=user,
                    question=question,
                    dataset_id=dataset.id if dataset else None,
                    conversation_history=conversation_history
                )

                # If SQL translation was unable to confidently generate a query, automatically upgrade to Strategic Analysis
                if query_res.get("error"):
                    logger.info("Ad-hoc SQL query unconfident for inquiry; upgrading to Strategic Analysis Engine.")
                    strat_res = StrategicAnalysisService.analyze_business_performance(
                        conn=conn,
                        table_name=dataset.table_name,
                        question=question,
                        dataset_name=dataset.original_filename
                    )
                    strat_res["reasoning_steps"].insert(2, "3. Query required multi-dimensional analysis beyond single SQL SELECT; activated Strategic Business Intelligence Engine.")
                    return strat_res

                reasoning_steps.append("4. Executed validated DuckDB aggregation query.")
                reasoning_steps.append("5. Generated visualization cards and executive narrative.")
                answer_text = query_res.get("narrative") or "Query executed successfully."
                return {
                    "status": "success",
                    "tool_used": "sql_query",
                    "answer": answer_text,
                    "summary": answer_text[:200],
                    "reasoning_steps": reasoning_steps,
                    "analytical_steps": reasoning_steps,
                    "data": query_res,
                    "kpi_results": query_res.get("kpi_cards", []),
                    "charts": {
                        "main_chart": query_res.get("main_chart"),
                        "secondary_chart": query_res.get("secondary_chart")
                    },
                    "supporting_table": {
                        "columns": query_res.get("available_columns", []),
                        "rows": query_res.get("main_chart", {}).get("data", []) if query_res.get("main_chart") else []
                    },
                    "evidence": query_res.get("kpi_cards"),
                    "suggested_follow_ups": query_res.get("suggested_followups") or []
                }

        finally:
            conn.close()

    @classmethod
    async def _synthesize_agent_response(cls, question: str, tool_name: str, findings: Dict[str, Any]) -> str:
        """Construct grounded analyst narrative from computed tool facts."""
        prompt = f"""You are INSLIGHT Senior AI Business Intelligence Agent.
The user asked: "{question}"
You invoked the analytical tool: {tool_name}
The tool returned the following verified data facts:
{json.dumps(findings, default=str)[:1500]}

Write a concise, professional, evidence-backed answer (2-4 sentences).
Rules:
1. State the key finding with exact numbers from the data.
2. Clearly distinguish correlation from causation (e.g. use "contributing factor" or "correlated pattern" unless proven).
3. Express all monetary figures in Indian Rupees (₹, Lakhs, Crores). Never use US dollars ($).
4. Provide a concrete operational recommendation.
"""
        try:
            return await ai_service.generate_text(prompt)
        except Exception as e:
            logger.warning(f"AI response synthesis failed: {e}")
            if "Root Cause" in tool_name:
                return f"Root Cause Analysis indicates that {findings.get('period_label', 'recent period')} experienced an absolute change of {findings.get('formatted_change')}. The primary contributing driver is identified as {findings.get('price_volume_decomposition', {}).get('primary_driver', 'segment shift')}."
            elif "Forecasting" in tool_name:
                return f"Based on historical data backtested with {findings.get('method_used', 'time-series analysis')}, the projected total for the {findings.get('horizon_label', 'next period')} is {findings.get('formatted_forecast_total')} indicating a {findings.get('trend_direction', 'steady')} trend."
            elif "Anomaly" in tool_name:
                return f"Scan identified {findings.get('anomalies_detected_count', 0)} statistical outliers ({findings.get('risks_count', 0)} risks and {findings.get('opportunities_count', 0)} positive opportunities). Top anomalies warrant operational audit."
            else:
                return f"Comparative analysis completed successfully across target metrics."
