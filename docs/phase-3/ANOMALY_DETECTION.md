# Advanced Multi-Algorithmic Anomaly Detection
## Statistical, Unsupervised ML & Business Opportunity Tagging

---

### 1. Purpose & Overview
Business data contains anomalies representing either severe operational risks (revenue crashes, excessive freight expenses, inventory leakage) or positive commercial opportunities (viral product sales, unexpected regional demand spikes).

Inslight provides a hybrid anomaly detection engine combining classical statistics with unsupervised machine learning.

---

### 2. Detection Algorithms

| Method | Type | Description | Best Suited For |
|---|---|---|---|
| **Z-Score** | Statistical Parametric | Identifies points where $|Z| = \frac{|x - \mu|}{\sigma} > 2.5$. | Normally distributed metrics (e.g. daily active users, average basket size). |
| **IQR (Interquartile Range)** | Statistical Non-Parametric | Identifies points outside $[Q_1 - 1.5 \times \text{IQR}, Q_3 + 1.5 \times \text{IQR}]$. | Skewed financial distributions with heavy tails. |
| **Isolation Forest** | Unsupervised ML (`scikit-learn`) | Isolates anomalies by building random partitioning trees. Anomalies require fewer splits to isolate. | Multi-dimensional patterns and complex non-linear anomalies. |
| **Time-Series Deviation** | Temporal Moving Window | Compares observed value against rolling baseline trend. | Seasonal volume spikes and sudden intra-week dips. |

---

### 3. Opportunity vs. Risk Classification
Every detected anomaly is evaluated in business context:
- **Positive Opportunity ($\Delta > 0$ on positive metrics like Revenue, Margin):** Flagged as a green alert with recommendations to analyze promotional effectiveness, replenish stock, or expand marketing.
- **Negative Risk ($\Delta < 0$ on Revenue OR $\Delta > 0$ on Cost/Return metrics):** Flagged as an amber/red alert with recommendations to investigate root cause, check logistics, or mitigate losses.

---

### 4. API Contract
- **Endpoint:** `POST /api/v1/analytics/advanced-anomalies`
- **Request Body:**
  ```json
  {
    "dataset_id": "optional-uuid",
    "metric_column": "revenue",
    "method": "ensemble",
    "sensitivity": "medium"
  }
  ```
