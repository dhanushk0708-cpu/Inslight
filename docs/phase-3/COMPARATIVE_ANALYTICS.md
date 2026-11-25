# Comparative Business Analytics
## Period-over-Period & Segment-over-Segment Benchmarking

---

### 1. Purpose & Overview
Comparative analytics provides structured benchmarking across temporal periods (Month-over-Month [MoM], Quarter-over-Quarter [QoQ], Year-over-Year [YoY]) or cross-sectional segments (Region A vs. Region B, Category X vs. Category Y).

---

### 2. Computational Logic & Variance Decomposition

#### A. Period-over-Period (MoM / QoQ)
Aggregates metric values by temporal bucket:
$$\text{Absolute Variance} = \text{Value}_{\text{Current}} - \text{Value}_{\text{Previous}}$$
$$\text{Percentage Change} = \frac{\text{Value}_{\text{Current}} - \text{Value}_{\text{Previous}}}{\text{Value}_{\text{Previous}}} \times 100$$
Zero-denominator handling ensures that if $\text{Value}_{\text{Previous}} = 0$, percentage change safely evaluates to `0.0%` (or `+100.0%` if current $>0$) without raising unhandled runtime errors.

#### B. Segment-over-Segment
Compares two categorical slices of the dataset across multiple target metrics (Revenue, Units Sold, Average Order Value):
- Ratio Comparison: $\frac{\text{Metric}_A}{\text{Metric}_B}$
- Metric Share: $\frac{\text{Metric}_A}{\text{Metric}_A + \text{Metric}_B} \times 100$

---

### 3. API Contract
- **Endpoint:** `POST /api/v1/analytics/compare`
- **Request Body (Period):**
  ```json
  {
    "dataset_id": "optional-uuid",
    "comparison_type": "period",
    "metric_column": "revenue",
    "date_column": "order_date",
    "period_granularity": "monthly"
  }
  ```
- **Request Body (Segment):**
  ```json
  {
    "dataset_id": "optional-uuid",
    "comparison_type": "segment",
    "metric_column": "revenue",
    "dimension_column": "region",
    "segment_a": "North",
    "segment_b": "South"
  }
  ```
