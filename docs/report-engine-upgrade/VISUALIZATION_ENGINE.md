# INSLIGHT BI Report Engine — Visualization Engine

## 1. Engine Specifications

The visualization subsystem is implemented in `backend/app/services/report_visualizer.py` using **Matplotlib 3.8+** with the non-interactive headless backend:
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

All charts are rendered directly into memory using `io.BytesIO()` streams, preventing file clutter, disk contention, or permission bottlenecks.

### Corporate Visual Styling
- **Color Palette:**
  - Primary Corporate Navy: `#1E3A8A`
  - Accent Electric Blue: `#3B82F6`
  - Secondary Slate Cyan: `#06B6D4`
  - Profit / Growth Emerald: `#10B981`
  - Alert / Outlier Coral: `#EF4444`
  - Neutral Background: `#F8FAFC`
- **Resolution:** 300 DPI for sharp vector-like print fidelity on PDF pages.
- **Spines:** Top and right spines removed for modern executive aesthetics.
- **Grid:** Subtle horizontal dotted gridlines (`#E2E8F0`, alpha 0.7).

---

## 2. Generated Visual Assets

| Chart ID | Method Name | Chart Type | Dimensions & Metrics Visualized |
|---|---|---|---|
| **Chart 1** | `generate_revenue_profit_trend()` | Dual-Line Chart | Monthly Revenue (`#1E3A8A`) and Monthly Gross Profit (`#10B981`) with peak month callout. |
| **Chart 2** | `generate_regional_breakdown()` | Horizontal Bar Chart | Territory revenue rankings with INR data labels and revenue share percentage. |
| **Chart 3** | `generate_product_performance()` | Horizontal Ranking Bar Chart | Top 7 Product SKUs ranked by revenue with auto-wrapped product names. |
| **Chart 4** | `generate_category_donut()` | Donut Chart with Center Callout | Market share breakdown across product categories with central total revenue stat. |
| **Chart 5** | `generate_category_comparison()` | Grouped Dual-Bar Chart | Side-by-side Revenue vs. Gross Profit comparison per business category. |

---

## 3. Fallback & Graceful Degradation

If a dataset lacks dates, regions, or categories:
- The visualizer gracefully detects absent data structures and returns `None`.
- `PDFReportGenerator` dynamically adjusts layout: if a chart is `None`, it substitutes an informative structured data table or callout box, preventing layout shifts or blank pages.
