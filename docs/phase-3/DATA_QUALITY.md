# Data Quality Assistant & Diagnostic Auditor
## Automated Profiling, Health Scoring & Clean Previews

---

### 1. Purpose & Overview
Data quality directly impacts the reliability of business intelligence. The Data Quality Assistant audits uploaded tabular data for common anomalies, calculates a standardized 0–100 Data Health Score, and provides a non-destructive cleaned preview.

---

### 2. Diagnostic Dimensions & Checks

| Check | Failure Condition | Remediation Strategy |
|---|---|---|
| **Missing Values (Nulls)** | Column null percentage $> 0\%$ | Imputation via median/mean for numeric columns, modal string for categorical. |
| **Duplicate Rows** | Exact row matches across all columns | Deduplication retaining first occurrence. |
| **Inconsistent Casing** | Categorical columns containing identical values with differing case (e.g. `Tech`, `tech`, `TECH`) | Normalization to title-case or lower-case. |
| **Negative Measure Violations** | Strictly positive business measures (Units, Quantity, Unit Price) $< 0$ | Clipping at zero or flagging as invalid refund entries. |
| **Type Discrepancies** | Mixed types or dates formatted as irregular text | Type casting and standard ISO 8601 parsing. |

---

### 3. Data Health Score Calculation
The health score is computed on a 100-point scale with weighted penalties:
$$\text{Health Score} = \max\left(0, 100 - (P_{\text{null}} \times 30 + P_{\text{duplicates}} \times 25 + P_{\text{casing}} \times 20 + P_{\text{negative}} \times 25)\right)$$
- **Score $\ge 90$:** Excellent Quality (Ready for predictive modeling).
- **Score $70 - 89$:** Moderate Quality (Minor anomalies detected).
- **Score $< 70$:** Poor Quality (High risk of distorted analytics).

---

### 4. Non-Destructive Cleaned Preview
The clean preview runs strictly in-memory via DuckDB/Pandas:
- **Zero In-Place Overwrites:** The original raw dataset file remains completely unchanged on disk.
- **Preview Payload:** Returns sample rows showing before-and-after normalization with side-by-side diff markers.
