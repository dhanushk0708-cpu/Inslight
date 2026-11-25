# Multi-Dataset Relational Intelligence
## Automated Schema Linking, Cardinality Validation & Cross-Dataset Joins

---

### 1. Purpose & Overview
Real enterprise environments rarely store everything in a single table. Often data is separated into Transactions, Customers, Products, or Stores. Inslight's Relational Intelligence engine identifies candidate join keys, validates integrity, warns against dangerous cartesian explosions, and executes unified cross-dataset analytics.

---

### 2. Candidate Key Discovery & Scoring
When two datasets ($D_A$ and $D_B$) are selected, the engine computes column compatibility:
- **Column Name Similarity:** Normalized Levenshtein distance on column tokens (e.g. `customer_id` $\leftrightarrow$ `cust_id`, `id` $\leftrightarrow$ `user_id`).
- **Data Type Alignment:** Both columns must resolve to compatible types (integers, strings, UUIDs).
- **Value Overlap:** Intersection of distinct values over total distinct values:
$$\text{Overlap Score} = \frac{|V_A \cap V_B|}{|V_A \cup V_B|}$$

---

### 3. Relationship Validation & Cardinality
Candidate relationships are evaluated for data integrity:
- **Null Violations:** Flags primary keys containing null entries.
- **Uniqueness Check:** Calculates duplicate ratios on both sides.
- **Cardinality Assessment:**
  - **One-to-One ($1:1$):** Unique on both sides.
  - **One-to-Many ($1:N$):** Unique on source, repeated on target (standard foreign key).
  - **Many-to-Many ($N:M$):** Non-unique on both sides. Displays high-severity Cartesian explosion risk warning.

---

### 4. Cross-Dataset Query Execution
Inslight leverages DuckDB's in-memory multi-file query capabilities to perform safe ANSI SQL joins:
```sql
SELECT
  a.order_id,
  a.revenue,
  b.customer_name,
  b.region
FROM read_parquet('user_1_orders.parquet') AS a
INNER JOIN read_parquet('user_1_customers.parquet') AS b
  ON a.customer_id = b.customer_id
LIMIT 50;
```
Results are returned with execution latency, joined schema metadata, and row count indicators.
