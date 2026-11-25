# Deep Dive Response Schema (`DeepDiveResponse`)

Endpoint: `POST /api/v1/deep-dive?refresh=false`

## Top-Level Fields
- **Legacy Compatibility Fields:** `top_revenue_drivers`, `risk_areas`, `root_cause_analysis`, `recommendations`, `monthly_trend`, `revenue_by_category`, `error`
- **10-Section Research Fields:**
  - `dataset_metadata` (`filename`, `row_count`, `column_count`, `date_coverage`, `data_quality_score`, `available_analyses`, `limitations`)
  - `executive_summary` (`health_summary`, `kpi_cards`, `key_findings`, `warnings`)
  - `revenue_analysis`
  - `profitability_analysis` (`available: bool`, ...)
  - `product_analysis`
  - `category_analysis`
  - `regional_analysis`
  - `customer_analysis` (`available: bool`, ...)
  - `trend_and_forecast`
  - `anomalies_and_risks`
  - `opportunities`
  - `strategic_action_plan` (`short_term`, `medium_term`)
  - `charts` (dictionary of dynamic Recharts configurations)
  - `execution_stages` (list of actual completed analytical stages)
