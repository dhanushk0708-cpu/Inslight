# INSLIGHT — Technical Audit: Next.js Frontend
**Document ID:** `AUDIT-DOC-02`
**Target:** `frontend/` (Next.js Application)
**Date of Audit:** November 2026
**Auditor:** Senior Full-Stack Engineer & Frontend Architect

---

## 1. Architectural Inspection

The primary frontend is located in `frontend/` and was created with Next.js 14 utilizing the App Router pattern.

```
frontend/
├── package.json
├── package-lock.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.local
└── src/
    └── app/
        ├── globals.css
        ├── layout.tsx
        └── page.tsx
```

### Key Architectural Findings:
1. **Extreme Monolithic Consolidation:**
   - The entire frontend application resides in a single file: `frontend/src/app/page.tsx` (1,082 lines, 54.5 KB).
   - This file bundles the root application shell, layout management, view routing, chat interface, message history, file upload handlers, scenario simulation sliders, tabular data grids, and three distinct SVG chart rendering engines.
2. **Missing Component Hierarchy:**
   - No `components/`, `hooks/`, `services/`, `types/`, or `utils/` directories exist within `frontend/src/`.
   - In contrast, the legacy `frontend-react/` repository had a structured multi-component architecture (`Charts/`, `Chat/`, `Common/`, `Dashboard/`, `Header/`, `Sidebar/`, `hooks/`, `services/`). During the migration to Next.js, all components were flattened and pasted into `page.tsx`.
3. **Runtime CSS Injection (`injectStyles` Anti-Pattern):**
   - Lines 9–525 of `frontend/src/app/page.tsx` define an `injectStyles()` function that injects a 516-line raw CSS string directly into `document.head` via `document.createElement("style")`.
   - This bypasses Next.js CSS Modules, Tailwind CSS compilation, and critical CSS extraction, leading to Flash of Unstyled Content (FOUC), layout shifts, and cache invalidation issues.

---

## 2. State Management & Re-rendering Analysis

The component `App` in `frontend/src/app/page.tsx` declares 13 pieces of top-level state:
```typescript
const [health, setHealth] = useState(null);
const [messages, setMessages] = useState([]);
const [input, setInput] = useState("");
const [loading, setLoading] = useState(false);
const [activeView, setActiveView] = useState("welcome");
const [viewData, setViewData] = useState(null);
const [showSql, setShowSql] = useState(false);
const [history, setHistory] = useState([]);
const [wiPrice, setWiPrice] = useState(0);
const [wiDiscount, setWiDiscount] = useState(0);
const [wiUnits, setWiUnits] = useState(0);
```

### Performance & Re-render Deficiencies:
- **Input Typing Lag:** `input` state updates on every keystroke (`onChange={e => setInput(e.target.value)}`). Because `input` is located at the root of `App`, every single keystroke triggers a complete re-render of:
  - The chat history message list.
  - The active results panel.
  - All SVG charts (`BarChart`, `LineChart`, `PieChart`), recomputing coordinate geometry and path strings.
  - The active data table.
- **Slider Dragging Overhead:** In the What-If view, dragging the Price, Discount, or Volume range slider updates `wiPrice`, `wiDiscount`, or `wiUnits` on every mouse tick, re-rendering the entire page and chat panel.
- **Absence of Memoization:** Neither `BarChart`, `LineChart`, `PieChart`, nor `DataTable` are wrapped in `React.memo()`. No computed geometry is cached using `useMemo()`.

---

## 3. UI, Visualizations, and Unused Dependencies

1. **Unused Dependencies in `package.json`:**
   - `"recharts": "2.10.3"`: Installed in `node_modules` (over 10 MB bundle impact), but never imported or referenced in `src/app/page.tsx`.
   - `"lucide-react": "0.303.0"`: Installed, but icons are rendered using emoji glyphs (e.g., `⚡`, `👤`, `✨`, `📁`, `🔬`, `🎯`, `🔍`).
   - `"react-dropzone": "14.2.3"`: Installed, but CSV uploads use a hidden `<input type="file" ref={fileRef} />` triggered via DOM click.
2. **Hand-Rolled SVG Engines:**
   - `BarChart` (lines 558–573): Normalizes data heights manually using percentage calculations.
   - `LineChart` (lines 575–598): Manually constructs SVG path strings (`pathD`, `areaD`), calculates bounding boxes (`w = 700, h = 230`), and maps ticks. Contains no responsive SVG scaling or tooltip support.
   - `PieChart` (lines 600–622): Manually computes trigonometric arcs (`Math.cos`, `Math.sin`) and SVG path arcs (`M cx cy L ... A r r ... Z`). Does not handle label overlaps or responsive reflows.

---

## 4. Code Quality & TypeScript Configuration

1. **Suppressed Type Checking (`tsconfig.json`):**
   ```json
   {
     "compilerOptions": {
       "strict": false,
       "allowJs": true,
       "skipLibCheck": true,
       "noEmit": true
     }
   }
   ```
   - TypeScript is configured in loose mode (`"strict": false`).
   - In `page.tsx`, component props and helper functions have zero type definitions:
     - `function BarChart({ data, xKey, yKey, title })` — implicit `any`.
     - `function fmt(v)` — implicit `any`.
     - `function kpiIcon(label)` — implicit `any`.
     - `const doUpload = async (file)` — implicit `any`.
2. **Network Resilience & Error Handling:**
   - API endpoint is derived from:
     ```typescript
     const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
     ```
   - All network calls use bare `fetch()` without timeout handlers, retry policies, or `AbortController` cancellation signals.
   - If a user rapidly enters multiple queries or clicks actions while a request is pending, race conditions can occur where a slower earlier request overrides a newer request.

---

## 5. Accessibility (a11y) & UX Deficiencies

1. **Missing Keyboard Controls & Focus Management:**
   - Action buttons and slider controls lack appropriate ARIA live regions (`aria-live="polite"`).
   - Chat suggestions lack keyboard arrow navigation.
2. **Color Contrast & Dynamic Theming:**
   - Color values (`--text-dim: #3a4058`, `--text-muted: #505872`) against dark backgrounds (`--bg-primary: #06080d`) fail WCAG AA contrast ratio standards (4.5:1 for normal text).
3. **Missing Form Validation:**
   - Chat input only checks `!input.trim()`. No length restrictions or sanitization are performed prior to dispatching network payloads.

---

## 6. Proposed Modular Next.js Architecture

To achieve enterprise-grade maintainability, performance, and scalability, the frontend must be restructured into a modular, domain-driven structure:

```
frontend/src/
├── app/
│   ├── layout.tsx                 # Root layout with font optimization & theme provider
│   ├── page.tsx                   # Clean page composer importing feature containers
│   └── globals.css                # Pure Tailwind CSS directives & theme variables
│
├── components/
│   ├── ui/                        # Reusable atomic UI primitives
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── slider.tsx
│   │   ├── badge.tsx
│   │   ├── spinner.tsx
│   │   └── modal.tsx
│   ├── charts/                    # Production Recharts wrappers
│   │   ├── bar-chart-view.tsx
│   │   ├── line-chart-view.tsx
│   │   ├── pie-chart-view.tsx
│   │   └── chart-container.tsx
│   └── common/
│       ├── data-table.tsx
│       └── error-boundary.tsx
│
├── features/                      # Domain-specific modules
│   ├── chat/
│   │   ├── components/
│   │   │   ├── chat-panel.tsx
│   │   │   ├── chat-header.tsx
│   │   │   ├── chat-messages.tsx
│   │   │   ├── chat-input.tsx
│   │   │   └── suggestion-chips.tsx
│   │   └── hooks/
│   │       └── use-chat.ts
│   │
│   ├── analytics/
│   │   ├── components/
│   │   │   ├── results-panel.tsx
│   │   │   ├── kpi-grid.tsx
│   │   │   ├── executive-narrative.tsx
│   │   │   └── sql-viewer.tsx
│   │   └── hooks/
│   │       └── use-query-execution.ts
│   │
│   ├── what-if/
│   │   ├── components/
│   │   │   ├── what-if-panel.tsx
│   │   │   └── scenario-slider.tsx
│   │   └── hooks/
│   │       └── use-what-if.ts
│   │
│   ├── anomalies/
│   │   └── components/
│   │       └── anomaly-feed.tsx
│   │
│   └── dataset/
│       ├── components/
│       │   ├── upload-dropzone.tsx
│       │   └── dataset-profile-view.tsx
│       └── hooks/
│           └── use-dataset-upload.ts
│
├── lib/
│   ├── api-client.ts              # Typed fetch client with interceptors & timeouts
│   ├── formatters.ts              # Currency, number, percentage formatting
│   └── constants.ts               # Theme tokens and app configuration
│
└── types/
    ├── api.ts                     # Backend request and response DTO interfaces
    ├── chat.ts                    # Message and conversation types
    └── dataset.ts                 # Profiling and metadata types
```
