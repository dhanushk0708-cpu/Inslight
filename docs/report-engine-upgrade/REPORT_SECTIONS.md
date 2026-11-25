# INSLIGHT BI Report Engine — Report Sections Specification

## 1. PDF Boardroom Report Structure (10-Page Blueprint)

| Page # | Section Title | Contents & Visual Artifacts |
|:---:|---|---|
| **1** | **Executive Cover Page** | INSLIGHT branding, Corporate report title, metadata audit block (dataset name, row/column counts, currency: INR, generation timestamp, classification badge), and full document Table of Contents with section descriptions. |
| **2** | **Executive Summary & Narrative** | Key Executive Takeaways, Data-Grounded Executive Narrative synthesized by Groq LLM, High-level KPI Scorecard Table with formatted INR metrics. |
| **3** | **Executive KPI Dashboard** | 6-Card Executive Metric Grid (Total Revenue, Gross Profit, Blended Margin, Total Volume, AOV, ASP), Period-over-Period Performance Highlights. |
| **4** | **Revenue & Profitability Trends** | Monthly trend narrative, **Embedded Matplotlib Chart 1** (Dual-Line Revenue & Profit Trend), Monthly Performance breakdown data table with MoM growth rates. |
| **5** | **Regional Market Performance** | Geographic sales asymmetry narrative, **Embedded Matplotlib Chart 2** (Horizontal Regional Bar Chart), Regional Ranking table with total revenue, profit, and revenue share %. |
| **6** | **Product Portfolio & SKU Rankings** | Product concentration analysis, **Embedded Matplotlib Chart 3** (Top SKU Ranking Chart), Top 10 Product performance table. |
| **7** | **Category & Channel Analysis** | Category market share analysis, **Embedded Matplotlib Chart 4** (Category Donut Chart) and **Chart 5** (Category Revenue vs. Profit Comparison), Comprehensive Category contribution table. |
| **8** | **Profitability & Cost Ratios** | Margin health diagnosis, Margin spread analysis, Financial Health Matrix table (Gross Margin, Cost-to-Revenue Ratio, Best Margin Category). |
| **9** | **Operational Anomaly Audit** | Outlier detection summary, Risk mitigation procedures, Detailed Anomaly Audit Log table with Severity Badges (HIGH, MEDIUM, LOW) and recommended audit checks. |
| **10** | **Strategic Recommendations & Appendix** | Strategic Action Plan (Prioritized High/Medium/Low actions with expected business impact), Data Quality & Governance Audit Table, Metric Definitions & Glossary. |

---

## 2. Multi-Sheet Excel Workbook Structure (9 Worksheets)

The Excel engine (`backend/app/services/excel_generator.py`) produces an enterprise-grade multi-tab `.xlsx` workbook:

1. **`Executive Summary`** — Report metadata, generation timestamp, high-level commentary, and primary executive scorecard.
2. **`KPI Dashboard`** — Comprehensive financial and operational KPI metrics with formatted values and status ratings.
3. **`Revenue Trends`** — Month-by-month temporal data table with Revenue, Profit, Volume, and MoM Growth calculations.
4. **`Regional Performance`** — Geographic sales breakdown, total revenue, profit contribution, and territory market share %.
5. **`Product Performance`** — SKU rankings, units sold, gross sales, and average selling price.
6. **`Category Breakdown`** — Division/Category metrics, gross profit, and category profit margins.
7. **`Anomaly Audit`** — Detected statistical outliers with severity ratings, affected columns, and recommended analyst action.
8. **`Analyst Insights & Strategy`** — 4-part data analyst findings and prioritized executive recommendations.
9. **`Source Data Partition`** — Sanitized sample partition of underlying raw data rows (up to 500 rows) with active freeze panes and auto-fit columns.
