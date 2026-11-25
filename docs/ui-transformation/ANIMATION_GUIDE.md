# INSLIGHT — Animation System

All animations are CSS/RAF-driven for zero extra bundle overhead and full `prefers-reduced-motion` compliance:

1. **Page / View Entrance (`pageEnter`):** `0.28s cubic-bezier(0.22, 1, 0.36, 1)` subtle `8px` vertical glide + opacity fade.
2. **KPI Count-Up (`AnimatedValue`):** `requestAnimationFrame` `420ms` cubic ease-out interpolation preserving `₹` currency, decimals, and unit suffixes.
3. **Charts & Cards (`chartRise`):** `0.32s ease-out` entrance animation.
4. **AI Thinking Identity (`aiPulse` + `ai-typing-dots`):** Soft indigo ring pulse on the AI `Sparkles` avatar alongside synchronized 3-dot bounce while computing insights.
5. **Skeleton Shimmer (`shimmer`):** `1.5s` linear gradient sweep on loading placeholders.
6. **Toast Feedback (`toastIn`):** `0.25s` slide-in confirmation banner (e.g., Copy SQL).
7. **Accessibility:** `@media (prefers-reduced-motion: reduce)` disables animations and smooth-scroll transitions globally.
