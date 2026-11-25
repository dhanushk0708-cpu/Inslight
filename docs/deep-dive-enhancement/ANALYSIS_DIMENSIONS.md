# Deep Dive Analysis Dimensions & Guards

1. **Executive Overview:** Total revenue, profit/margin (only when cost/profit columns exist), units/orders (only when order IDs exist, otherwise per-record averages), key findings, and data limitations.
2. **Revenue Performance:** Monthly/quarterly trends, MoM & QoQ growth, category/product/region contribution, and concentration checks.
3. **Profitability:** Computed strictly from `profit` or `revenue - cost`; clearly marks `available: false` when absent.
4. **Product Intelligence:** Top & bottom products, contribution %, high-volume/low-revenue items, and explicit distinction between low sales velocity and inventory accumulation.
5. **Regional Intelligence:** Regional ranking, revenue/profit, and performance gaps without presenting hypothetical gains as guaranteed.
6. **Customer Intelligence:** Enabled only when customer identifiers exist; otherwise reports `available: false`.
7. **Trends & Forecasts:** Reuses `ForecastingService` with 30-period horizon and insufficient-data guards.
8. **Risks & Anomalies:** Reuses `AdvancedAnomalyService` and `StrategicAnalysisService` risks with severity and evidence.
9. **Opportunities:** Transparently separates measured findings from `[Hypothesis]` scenarios.
10. **Strategic Action Plan:** Short-term and medium-term prioritized actions with metrics to monitor.
