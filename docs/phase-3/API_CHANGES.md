# Phase 3 API Changes & New Endpoints
## Complete Reference for Phase 3 REST APIs

---

### 1. New Endpoints Summary (Phase 3)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/agent/query` | Autonomous BI Agent multi-step reasoning query | Yes |
| `POST` | `/api/v1/analytics/rca` | Dimensional & Price-Volume Root Cause Analysis | Yes |
| `POST` | `/api/v1/analytics/forecast` | ML & statistical time series forecasting (7/30/90 days) | Yes |
| `POST` | `/api/v1/analytics/advanced-anomalies` | Multi-algorithmic anomaly detection & opportunity tagging | Yes |
| `GET` | `/api/v1/alerts` | List triggered business alerts for current user | Yes |
| `POST` | `/api/v1/alerts/scan` | Trigger rule evaluation against active dataset | Yes |
| `PATCH` | `/api/v1/alerts/{id}/read` | Mark alert as read | Yes |
| `PATCH` | `/api/v1/alerts/{id}/resolve` | Mark alert as resolved | Yes |
| `GET` | `/api/v1/alerts/rules` | List user's alert rules | Yes |
| `POST` | `/api/v1/alerts/rules` | Create custom alert rule | Yes |
| `DELETE` | `/api/v1/alerts/rules/{id}` | Delete custom alert rule | Yes |
| `POST` | `/api/v1/datasets/{id}/quality` | Run data quality audit & compute health score | Yes |
| `GET` | `/api/v1/datasets/{id}/quality/preview` | Non-destructive before-and-after cleaned preview | Yes |
| `POST` | `/api/v1/analytics/compare` | Period-over-period or segment-over-segment comparison | Yes |
| `POST` | `/api/v1/dashboards/generate` | AI-assisted dashboard generation from prompt | Yes |
| `GET` | `/api/v1/dashboards` | List user's saved dashboards | Yes |
| `POST` | `/api/v1/dashboards` | Save a new dashboard configuration | Yes |
| `GET` | `/api/v1/dashboards/{id}` | Retrieve dashboard with live widget queries | Yes |
| `PUT` | `/api/v1/dashboards/{id}` | Update existing dashboard | Yes |
| `DELETE` | `/api/v1/dashboards/{id}` | Delete saved dashboard | Yes |
| `POST` | `/api/v1/dashboards/{id}/duplicate` | Clone saved dashboard | Yes |
| `GET` | `/api/v1/relationships/candidates` | Detect foreign key candidates between two datasets | Yes |
| `POST` | `/api/v1/relationships/validate` | Validate integrity & determine cardinality ($1:1, 1:N, N:M$) | Yes |
| `POST` | `/api/v1/relationships/preview` | Execute cross-dataset DuckDB join preview | Yes |
| `GET` | `/api/v1/relationships` | List saved relationships | Yes |
| `POST` | `/api/v1/relationships` | Save relationship | Yes |
| `DELETE` | `/api/v1/relationships/{id}` | Delete relationship | Yes |

---

### 2. Error Response Standards
All endpoints consistently follow RFC 7807 problem details:
```json
{
  "detail": "Descriptive error message explaining the failure or data insufficiency."
}
```
Standard status codes used:
- `200 OK`: Successful synchronous retrieval or calculation.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Invalid parameters, insufficient data points, or malformed schema.
- `401 Unauthorized`: Missing or invalid JWT Bearer token.
- `404 Not Found`: Dataset or entity not found or belonging to another tenant.
- `500 Internal Server Error`: Server-side processing failure.
