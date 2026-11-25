# INSLIGHT — Responsive Design & Accessibility

## Breakpoints (`frontend/src/app/globals.css`)
- **Desktop (`> 1100px`):** Side-by-side `410px` AI Assistant sidebar + fluid Results Command Center; 2-column `.chart-grid`; auto-fit `190px+` `.kpi-grid`.
- **Laptop / Small Desktop (`<= 1100px`):** AI sidebar narrows to `350px`; `.chart-grid` collapses cleanly to `1fr` to prevent cramped charts.
- **Tablet (`<= 820px`):** `.app` switches to vertical stack; `.chat-panel` becomes collapsible via the topbar `☰ AI Chat` toggle (`height: 62vh` when open, `0` when collapsed); `.kpi-grid` uses 2 columns.
- **Mobile (`<= 520px`):** `.kpi-grid` collapses to `1fr`; zero horizontal overflow (`overflow-x: hidden`).

## Accessibility
- Keyboard-visible focus rings (`*:focus-visible { outline: 2px solid var(--accent-light); outline-offset: 2px; }`).
- Semantic `aria-label` attributes on icon buttons, language selector, and upload inputs.
- High-contrast text (`#f3f5fa` on `#050811` / `#0f1524`).
