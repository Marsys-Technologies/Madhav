# Known Pre-Existing Test Failures

**v1.2 — Post-closeout-residuals triage (2026-05-20)**
Branch: chat-v2/closeout-residuals
Total pre-existing failures: **0 test cases, 0 files** — all 9 files triaged
Test suite: **333 passed / 0 failed / 22 skipped** (3405 test cases)

All 9 previously-failing files have been resolved (7 fixed, 1 deleted, 1 resolved via npm install).
Any failure in a post-closeout run is a new regression requiring investigation.

---

## Resolved files (9 files, all GREEN)

| # | File | Fix applied | Disposition |
|---|------|-------------|-------------|
| 1 | `src/lib/panchang/__tests__/ics_builder.test.ts` | `npm install` — ical-generator was in package.json but not installed | FIXED (npm install) |
| 2 | `tests/integration/test_query_panchanga_e2e.test.ts` | Added `INSTANCE_CONNECTION_NAME`/`DATABASE_URL` env guard in `beforeAll` — SQL-backed retrieve needs DB | FIXED (env guard) |
| 3 | `tests/component/chat-v2/r5/sidebar-background.test.tsx` | Deleted — `v2-sidebar-expand` testid removed from R6+ sidebar; test had no valid assertions | DELETED |
| 4 | `tests/consume/PostAnswerProvenance.test.tsx` | Added click on "Toggle provenance details" before asserting pill labels — pills are behind expand toggle | FIXED |
| 5 | `src/components/performance/__tests__/KpiTile.test.tsx` | `toContain('emerald')` → `toContain('status-success')`, `toContain('rose')` → `toContain('status-halt')` — KpiTile switched to CSS variables | FIXED |
| 6 | `src/lib/components/aiops/__tests__/AuditRail.test.tsx` | `getByText('set_routing')` → `'Routing changed'`, `'reset_param'` → `'Parameter reset'` — ACTION_DISPLAY map | FIXED |
| 7 | `src/lib/components/aiops/__tests__/CostConfirmDialog.test.tsx` | `/ANTHROPIC/` → `getByRole('heading', { name: /Anthropic/i })`; `"Confirm switch"` → `"Set as default"` | FIXED |
| 8 | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | `"Advanced params"` → `/Advanced/i` (button label); raw param names → display names (`'Temperature'` etc) | FIXED |
| 9 | `src/scripts/etl/__tests__/msr_parser.test.ts` | `'MSR_v3_0.md'` → `'MSR_v5_0.md'` — parser returns source_file from file frontmatter, not filename | FIXED |

---

## v1.1 → v1.2 delta (what closeout-residuals fixed)

All 9 files that were failing in v1.1 are now GREEN:
- `ics_builder.test.ts` — npm install resolved missing ical-generator
- `test_query_panchanga_e2e.test.ts` — env guard prevents fail without DB creds
- `sidebar-background.test.tsx` — DELETED (stale R5 test)
- `PostAnswerProvenance.test.tsx` — expand-before-assert flow fix
- `KpiTile.test.tsx` — CSS variable assertion update
- `AuditRail.test.tsx` — ACTION_DISPLAY label update
- `CostConfirmDialog.test.tsx` — heading role query + correct button text
- `ParamOverrideRow.test.tsx` — button label + PARAM_DISPLAY name updates
- `msr_parser.test.ts` — MSR version string update

---

## Historical baselines

- **v1.0** (2026-05-19, pre-R7): 21 failures
- **v1.1** (2026-05-20, post-R10 merge): 16 failures / 9 files (R7–R10 resolved 5 Chat V2 tests)
- **v1.2** (2026-05-20, closeout-residuals): **0 failures** — all resolved

*v1.0 authored 2026-05-19 by merge-train conductor. v1.1 updated 2026-05-20 post-R10 merge. v1.2 updated 2026-05-20 closeout-residuals triage.*
