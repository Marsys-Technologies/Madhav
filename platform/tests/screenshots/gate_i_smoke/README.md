# Gate I — Performance Command Center Visual Smoke Screenshots

Captured: 2026-05-13 (CROSS_GATE_VISUAL_SMOKE session)
Playwright run: 3/3 PASS

## Screenshots

| File | Content | Reviewer checklist |
|---|---|---|
| `performance_full.png` | Full /performance page at 1440×900 | Heading, KPI grid, query log section, time-window picker all visible |
| `kpi_tiles.png` | KPI tile grid | "Performance health" and "Retrieval health" tiles rendered with headline values |
| `query_log_header.png` | Query log table header row | Column headers visible |
| `time_window_picker.png` | Time-window picker controls | 7d/30d/24h/90d buttons or similar present |
| `eval_runs.png` | Full /performance/eval-runs page | Eval runs table or empty-state message visible |
| `eval_table.png` | Eval runs table | Table structure rendered |

## Re-run Command

```
# Write a fresh session cookie to /tmp/smoke_session_cookie.txt, then:
npx playwright test tests/e2e/gate_i_performance_smoke.spec.ts --reporter=list --workers=1
```

## Notes

- Page uses React Query (TanStack Query v5) for client-side data fetching
- No `data-testid` attributes on performance components; selectors use text content
- KPI tiles and query log will show empty/— values when no queries are logged yet
- The /performance route is super-admin gated; auth via Firebase session cookie
