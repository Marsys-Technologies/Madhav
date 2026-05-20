# RESIDUALS_LOG

Tracks execution of Chat V2 R7-R10 arc close-out residuals.

## Session metadata
- **Branch:** chat-v2/closeout-residuals
- **Base SHA (main):** 7c4e465 (Merge pull request #107 from amonty84/chat-v2/r7-r10-closeout)
- **Started:** 2026-05-20

---

## Phase 0 — Orient (COMPLETE)

| Check | Result |
|---|---|
| pwd | /Users/Dev/Vibe-Coding/Apps/Madhav ✓ |
| git sync | Already up to date with origin/main ✓ |
| gcloud | /opt/homebrew/bin/gcloud ✓ |
| psql | /opt/homebrew/bin/psql ✓ |
| cloud-sql-proxy | /opt/homebrew/bin/cloud-sql-proxy ✓ |
| npx | /Users/Dev/.nvm/versions/node/v24.14.0/bin/npx ✓ |
| GCP project | madhav-astrology ✓ |
| Branch created | chat-v2/closeout-residuals ✓ |

---

## Phase 1 — Backfill Run (COMPLETE)

| Metric | Value |
|---|---|
| Script bug found | `cm.content` column does not exist — fixed to `jsonb_array_elements(parts_json)` |
| BEFORE embeddings | 0 |
| Messages embeddable | 73 |
| AFTER embeddings | 73 |
| Errors | 0 |
| Duration | 53 seconds |
| Remaining un-embedded | 0 |
| BACKFILL_SCRIPT_NOT_FOUND.md | Updated to v2.0 RESOLVED |

---

## Phase 2 — Stale Test Triage (COMPLETE)

Final suite: **333 files pass / 0 fail / 22 skipped** (3405 test cases)

| # | File | Disposition | Fix |
|---|------|-------------|-----|
| 1 | `src/lib/panchang/__tests__/ics_builder.test.ts` | FIXED | npm install (ical-generator in package.json, not in node_modules) |
| 2 | `tests/integration/test_query_panchanga_e2e.test.ts` | FIXED | Added `INSTANCE_CONNECTION_NAME`/`DATABASE_URL` env guard in beforeAll |
| 3 | `tests/component/chat-v2/r5/sidebar-background.test.tsx` | DELETED | Stale R5 test; `v2-sidebar-expand` testid removed in R6+ |
| 4 | `tests/consume/PostAnswerProvenance.test.tsx` | FIXED | Click "Toggle provenance details" before asserting pill labels |
| 5 | `src/components/performance/__tests__/KpiTile.test.tsx` | FIXED | CSS class `emerald`/`rose` → CSS variable `status-success`/`status-halt` |
| 6 | `src/lib/components/aiops/__tests__/AuditRail.test.tsx` | FIXED | Raw action keys → ACTION_DISPLAY labels (`'Routing changed'`, `'Parameter reset'`) |
| 7 | `src/lib/components/aiops/__tests__/CostConfirmDialog.test.tsx` | FIXED | Heading role query; button text `"Set as default"` not `"Confirm switch"` |
| 8 | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | FIXED | Button regex + PARAM_DISPLAY labels (`'Temperature'` not `'temperature'`) |
| 9 | `src/scripts/etl/__tests__/msr_parser.test.ts` | FIXED | MSR version string `v3_0` → `v5_0` |

Also fixed: `platform/scripts/backfill_conversation_embeddings.ts` SQL column bug (`cm.content` → `jsonb_array_elements(parts_json)`).

---

## Phase 3 — Seal

_(to be populated)_
