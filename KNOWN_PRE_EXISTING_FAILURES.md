# Known Pre-Existing Test Failures

**v1.1 — Post-R10 baseline (2026-05-20)**
Branch: main @ `4dae9ed` (R10 PR #106 merged)
Total pre-existing failures: **16 test cases, 9 files**
R10 unit tests: **566 passed / 0 failed** (55 test files in `tests/unit/chat-v2/`)

Prior baseline v1.0 captured pre-R7 (2026-05-19 @ `ccd2aed`) recorded 21 failures.
R7–R10 resolved the 5 Chat V2 stale tests (citation_rich_payload, sidebar_auto_title_refresh,
markdown_render_v2, panel_mode_toggle) — those are now GREEN.

Any failure in a post-R10 run that matches a file below is background noise.
Any failure in a file NOT listed here is a new regression requiring investigation.

---

## Current failing files (9 files, 16 test cases)

| # | File | Failure summary | Workstream | Disposition |
|---|------|----------------|------------|-------------|
| 1 | `src/lib/panchang/__tests__/ics_builder.test.ts` | ical-generator module resolution fails in CI (added by Phase 4C, post-merge env issue) | Phase 4C | Fix in Phase 4C follow-up |
| 2 | `tests/integration/test_query_panchanga_e2e.test.ts` | Requires live python-sidecar; skipped without `SIDECAR_URL` | Phase 4C | Gate behind env guard |
| 3 | `tests/component/chat-v2/r5/sidebar-background.test.tsx` | CSS class `bg-zinc-950` assertion stale vs R6+ sidebar layout | R5/R6 pre-existing | Delete stale test |
| 4 | `tests/consume/PostAnswerProvenance.test.tsx` (2 cases) | Component restructured post-R6; provenance pill counts mismatch | R6 pre-existing | Update or delete test |
| 5 | `src/components/performance/__tests__/KpiTile.test.tsx` (2 cases) | Arrow rendering assertion mismatch vs current KpiTile render | Phase O pre-existing | Fix KpiTile snapshot |
| 6 | `src/lib/components/aiops/__tests__/AuditRail.test.tsx` | AuditRail row action render fails — missing AIOps mock/provider | AIOps pre-existing | Fix test setup |
| 7 | `src/lib/components/aiops/__tests__/CostConfirmDialog.test.tsx` (2 cases) | Dialog render + confirm button — missing AIOps mock/provider | AIOps pre-existing | Fix test setup |
| 8 | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` (5 cases) | Button label `"Advanced params"` → `"▼ Advanced"` — stale assertion | AIOps pre-existing | Update getByText pattern |
| 9 | `src/scripts/etl/__tests__/msr_parser.test.ts` | MSR signals missing `source_file` — stale test vs updated schema | ETL pre-existing | Fix in MSR maintenance |

## Failure clusters

- **AIOps (9 failures):** ParamOverrideRow (5) + CostConfirmDialog (2) + AuditRail (1) = 8 test cases. Shared test setup issue (missing mock/provider) + stale label assertion.
- **Phase 4C (2 failures):** ics_builder env issue + E2E integration requiring live sidecar.
- **R5/R6 stale (3 failures):** sidebar-background + PostAnswerProvenance — component shape changed.
- **Observatory KpiTile (2 failures):** Arrow rendering snapshot stale.
- **ETL MSR parser (1 failure):** source_file field schema drift.

## v1.0 → v1.1 delta (what R7–R10 fixed)

Previously failing, now GREEN:
- `tests/unit/chat-v2/citation_rich_payload.test.ts` — R10 wired enrichedOnPin + citationRichMap
- `tests/unit/chat-v2/sidebar_auto_title_refresh.test.ts` — R10 added V2TitleTracker component
- `tests/unit/chat-v2/markdown_render_v2.test.ts` — R10 added `data-testid="v2-message-text"`
- `tests/unit/chat-v2/panel_mode_toggle.test.ts` — R10 added `data-testid="v2-composer-options"`

---

*v1.0 authored 2026-05-19 by merge-train conductor. v1.1 updated 2026-05-20 post-R10 merge.*
