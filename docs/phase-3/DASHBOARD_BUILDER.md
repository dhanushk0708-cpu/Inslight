# AI Dashboard Builder & Dashboard Studio
## Natural Language Synthesis & Interactive Widgets

---

### 1. Purpose & Overview
The Dashboard Studio allows business users to generate full interactive dashboards either through natural language requests ("Build a sales executive overview with monthly revenue, regional breakdown, and top categories") or by customizing widget arrangements.

---

### 2. Architecture & Widget Models

#### A. Widget Layout & Types
Dashboards are composed of modular JSON widget configurations:
- `kpi`: Single high-impact metric card (Total Revenue, Average Order Value, Unit Volume).
- `line_chart`: Time-series revenue and volume trends.
- `bar_chart`: Categorical dimensional comparisons (Revenue by Category, Sales by Rep).
- `donut_chart`: Proportional market share or channel contribution.

#### B. Dynamic Execution Engine
Widgets do not store static mock data; each widget stores its aggregation specification. When loaded, DuckDB executes optimized aggregations against the active dataset to populate live charts.

#### C. Saved Dashboard Entity (`SavedDashboard`)
- `id`: Unique identifier (UUID).
- `user_id`: Tenant owner.
- `title`: User-friendly title.
- `description`: Contextual explanation.
- `is_favorite`: Quick access flag.
- `widgets`: Structured JSON array containing widget layout and analytical parameters.

---

### 3. API Contract
- `POST /api/v1/dashboards/generate`: Generate dashboard from natural language prompt.
- `GET /api/v1/dashboards`: List all saved dashboards for authenticated user.
- `GET /api/v1/dashboards/{id}`: Retrieve specific dashboard with live query results.
- `POST /api/v1/dashboards`: Save a newly designed dashboard.
- `PUT /api/v1/dashboards/{id}`: Update an existing dashboard.
- `DELETE /api/v1/dashboards/{id}`: Delete dashboard.
- `POST /api/v1/dashboards/{id}/duplicate`: Clone existing dashboard layout.
