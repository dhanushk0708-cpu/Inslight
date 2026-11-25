# INSLIGHT BI Report Engine — Analytics Methodology

## 1. Semantic Schema Detection

The engine accepts arbitrary structured tabular CSV uploads. Upon ingestion, DuckDB queries inspect column data types and execute semantic string matching to classify fields into dimensional categories:

- **Measures (Aggregatable Numerics):**
  - Revenue: `revenue`, `sales`, `turnover`, `total_amount`, `amount`
  - Profit: `profit`, `margin`, `net_amount`, `gross_profit`
  - Cost: `cost`, `cogs`, `expense`, `spend`
  - Volume: `quantity`, `units`, `volume`, `orders`, `count`
  - Price: `price`, `unit_price`, `selling_price`, `rate`
  - Discount: `discount`, `rebate`, `markdown`
- **Dimensions (Categorical & Temporal Attributes):**
  - Date / Period: `date`, `order_date`, `created_at`, `timestamp`, `month`
  - Region / Territory: `region`, `territory`, `zone`, `state`, `country`, `market`
  - Category / Division: `category`, `department`, `line`, `family`, `type`
  - Product / SKU: `product`, `item`, `sku`, `title`, `name`
  - Segment / Channel: `segment`, `channel`, `customer_type`, `tier`

---

## 2. Metric Computation & Consistency Guarantee

To ensure numbers displayed on the PDF Cover Page match the Excel KPI sheet and the narrative text, metrics are computed **once** inside DuckDB and serialized into a consolidated analytics state dictionary:

### Executive KPIs
- **Gross Revenue:** $\sum \text{Revenue}$
- **Gross Profit:** $\sum \text{Profit}$ (or $\sum (\text{Revenue} - \text{Cost})$ when profit is absent)
- **Gross Margin Percentage:** $(\text{Gross Profit} / \text{Gross Revenue}) \times 100\%$
- **Average Order Value (AOV):** $\text{Gross Revenue} / \text{Total Orders}$
- **Average Selling Price (ASP):** $\text{Gross Revenue} / \text{Total Units Sold}$

### Indian Rupee Currency Formatting Rules
All financial figures are formatted strictly in Indian Rupees (`₹`):
- Values $\ge 10,000,000$ (1 Crore) $\rightarrow$ `₹ X.XX Cr`
- Values $\ge 100,000$ (1 Lakh) $\rightarrow$ `₹ X.XX L`
- Values $< 100,000$ $\rightarrow$ Standard Indian comma grouping: `₹ ##,##,##0.00`
- Dollars (`$`) are strictly stripped and rejected across all reporting outputs.

---

## 3. Data-Grounded Executive Narrative

To eliminate AI hallucinations in executive summaries:
1. `ReportAnalyticsService` queries exact values for gross revenue, gross profit, margin, lead region, top category, peak month, and anomaly count.
2. These hard facts are injected into a constrained system prompt sent to Groq (`llama-3.3-70b-versatile`).
3. If Groq is unreachable or fails, a deterministic template-based narrative fallback is generated instantly, guaranteeing uninterrupted report generation.
