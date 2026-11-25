# Root Cause Analysis (RCA) Engine
## Mathematical Foundations & Dimensional Decomposition

---

### 1. Purpose & Motivation
When key business metrics change (such as a drop in monthly revenue or a surge in shipping costs), business leaders need to know **why** it happened and **where** the variance originated. The Inslight RCA Engine decomposes aggregated metric variances into dimensional components and mathematical drivers.

---

### 2. Analytical Methodologies

#### A. Period-over-Period Variance Analysis
Calculates baseline period metrics ($M_0$) versus comparison period metrics ($M_1$):
$$\Delta M = M_1 - M_0$$
$$\% \Delta M = \frac{M_1 - M_0}{M_0} \times 100$$
Safe division rules prevent zero-division errors when $M_0 = 0$.

#### B. Dimensional Contribution Breakdown
For any dimension $D$ (e.g., `Category`, `Region`, `Sales_Rep`), the total variance $\Delta M$ is decomposed into individual segment contributions:
$$\Delta M = \sum_{d \in D} \Delta M_d$$
$$\text{Contribution Share}_d = \frac{\Delta M_d}{|\Delta M|} \times 100$$
Each segment is classified as a:
- **Major Negative Driver:** Segments driving greater than 20% of negative variance.
- **Major Positive Driver:** Segments mitigating negative variance or driving positive growth.
- **Neutral / Minor:** Low-impact fluctuations.

#### C. Price vs. Volume Decomposition
For revenue ($R = P \times Q$), total revenue change is decomposed into Price Effect and Volume Effect:
$$\Delta R = \text{Price Effect} + \text{Volume Effect}$$
$$\text{Price Effect} = (P_1 - P_0) \times Q_1$$
$$\text{Volume Effect} = (Q_1 - Q_0) \times P_0$$

This isolates whether a revenue drop was caused by price discounting or reduced sales volume.

---

### 3. API Contract
- **Endpoint:** `POST /api/v1/analytics/rca`
- **Request Body:**
  ```json
  {
    "dataset_id": "optional-uuid",
    "metric_column": "revenue",
    "dimension_column": "category",
    "date_column": "order_date",
    "baseline_period": "2024-10",
    "comparison_period": "2024-11"
  }
  ```
