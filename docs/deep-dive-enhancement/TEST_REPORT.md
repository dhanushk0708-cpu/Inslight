# Deep Dive Enhancement — Test Report

## Automated Backend Tests (`backend/tests/test_deep_dive_enhanced.py`)
1. `test_deep_dive_comprehensive_on_sample_sales`:
   - Verified 96 rows in `sample_sales.csv`, KPI cards, `profitability_analysis.available == True`, `product_analysis.available == True`, `regional_analysis.available == True`, `customer_analysis.available == False` (no fabricated customer metrics), dynamic charts (`revenue_trend`, `revenue_by_category`, `top_products`, `regional_performance`), 3 opportunities, 3 risks, and execution stages.
2. `test_deep_dive_adapts_dynamically_to_alternate_schema`:
   - Uploaded `customers.csv` (`date,region,customer_id,order_id,revenue` — no profit/cost or product columns).
   - Verified `profitability_analysis.available == False`, `customer_analysis.available == True` (`unique_customers == 4`), `customer_concentration` chart generated, and `profit_trend` omitted.
