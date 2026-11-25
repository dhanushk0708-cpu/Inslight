# INSLIGHT — Deep Dive Research Workspace Architecture

## Overview
The Deep Dive Business Intelligence Workspace pairs a spacious, multiline AI Analyst panel on the left with a 10-section interactive Business Intelligence Research Report on the right.

## Backend Pipeline (`DeepDiveResearchService`)
1. **Schema & Capability Inference:** Dynamically inspects DuckDB columns (`DESCRIBE`) to identify revenue, profit/cost, units, dates, categories, products, regions, customers, order IDs, and inventory columns.
2. **Deterministic Analytics First:** Executes DuckDB aggregations, `DataQualityService`, `StrategicAnalysisService`, `ForecastingService`, and `AdvancedAnomalyService`.
3. **LLM Grounded Synthesis:** Passes only verified aggregate facts to `AIService.generate_text` (with deterministic fallback if unavailable) so the LLM never invents statistics.
4. **Dataset-Specific Caching:** Uses a bounded LRU cache keyed by `(user_id, dataset_id, row_count)` with `?refresh=true` bypass support.
5. **Backward Compatibility:** `DeepDiveEngine` delegates to `DeepDiveResearchService` and `DeepDiveResponse` preserves all legacy fields alongside the 10-section payload.
