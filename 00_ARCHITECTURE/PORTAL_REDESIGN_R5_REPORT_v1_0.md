---
artifact: PORTAL_REDESIGN_R5_REPORT_v1_0
artifact_id: PORTAL_REDESIGN_R5_REPORT
version: 1.0.0
status: COMPLETE
authored_by: Claude Code (Sonnet 4.6)
authored_at: 2026-04-30
session_id: redesign-r5-timeline-2026-04-30
phase_id: R5
exec_brief: EXEC_BRIEF_PORTAL_REDESIGN_R5_TIMELINE_v1_0.md
branch: redesign/r5-timeline
worktree: ~/Vibe-Coding/Apps/Madhav-r5
---

# Portal Redesign R5 — Closure Report (Timeline / LEL Surface)

## §1 — Phase summary

R5 landed `/clients/[id]/timeline` — the UI home for LEL events and prospective predictions. The route reads directly from `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` via a robust two-pass YAML parser and ships an append-only writer with in-process mutex protection. No DB schema changes. No changes to existing LEL entries.

## §2 — Deliverables status

| Deliverable | Status | Path |
|---|---|---|
| LEL parser (`parseLEL`, `parseLELMarkdown`) | ✓ LANDED | `platform/src/lib/lel/parser.ts` |
| LEL writer (`appendEvent`, `appendPrediction`, `markPredictionOutcome`) | ✓ LANDED | `platform/src/lib/lel/writer.ts` |
| `/api/lel` POST endpoint (append_event / append_prediction / mark_outcome) | ✓ LANDED | `platform/src/app/api/lel/route.ts` |
| `/clients/[id]/timeline` page (server component) | ✓ LANDED | `platform/src/app/clients/[id]/timeline/page.tsx` |
| Timeline layout (`<AppShell>` breadcrumb) | ✓ LANDED | `platform/src/app/clients/[id]/timeline/layout.tsx` |
| `<TimelineView>` (Events + Predictions tabs, URL state) | ✓ LANDED | `platform/src/components/timeline/TimelineView.tsx` |
| `<EventCard>` (timeline spine, category pill, dasha state) | ✓ LANDED | `platform/src/components/timeline/EventCard.tsx` |
| `<PredictionTable>` (sortable, status badges) | ✓ LANDED | `platform/src/components/timeline/PredictionTable.tsx` |
| `<LogEventDialog>` (super_admin modal) | ✓ LANDED | `platform/src/components/timeline/LogEventDialog.tsx` |
| `<LogPredictionDialog>` (confidence slider modal) | ✓ LANDED | `platform/src/components/timeline/LogPredictionDialog.tsx` |
| Feature flag `PORTAL_REDESIGN_R5_ENABLED` | ✓ LANDED | `platform/src/lib/config/feature_flags.ts` |
| Parser unit tests (7 tests) | ✓ PASSING | `platform/tests/lib/lel-parser.test.ts` |
| Writer unit tests (4 tests) | ✓ PASSING | `platform/tests/lib/lel-writer.test.ts` |
| Playwright E2E scaffolding | ✓ LANDED | `platform/tests/e2e/portal/timeline.spec.ts` |

All 11 unit tests pass. E2E tests require running dev server with `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID`.

## §3 — Parser design decisions

The LEL file (`LIFE_EVENT_LOG_v1_2.md`) contains 36 real events plus PATTERN/PERIOD/GAP blocks and a schema template entry (`EVT.YYYY.MM.DD.XX`). Approximately 18 event blocks contain unquoted strings with colons in YAML values (e.g. `description: First contract: a major milestone`) which break strict YAML parsing.

**Two-pass strategy adopted:**
1. Try `js-yaml.load()` strictly — if it yields objects with EVT./PRED. keys, use them.
2. If strict parse fails or yields no recognized keys, fall back to per-field regex extraction (`regexExtractEntry()`).

**Additional normalization applied:**
- `toDateStr()` handles js-yaml's automatic Date object coercion for bare ISO dates (e.g. `date: 2024-07-15` becomes a JS Date — normalized back to `"2024-07-15"` string).
- `EVT.YYYY.MM.DD.XX` schema template filtered at both parse paths via `id.includes('YYYY')`.
- PATTERN/PERIOD/GAP/CHAPTER blocks silently skipped (no EVT./PRED. key prefix).

Parse result on the real LEL file: **36 events, 0 hard errors**.

## §4 — Writer design decisions

**Append-only invariant**: `appendEvent` and `appendPrediction` insert before `## §4 — CHRONIC PATTERNS`, never modifying existing entries.

**In-process mutex** (`withLock()`): Promise-chain-based soft lock prevents concurrent writes within a single Next.js process. Errors in one write detach from the lock chain so they do not block subsequent writes.

**Round-trip validation**: Every write runs `parseLELMarkdown()` on the new content before calling `writeFile`. If the newly appended entry is not found in the parse result, the write aborts with an error — the file is never corrupted.

**`chart_state_pending: true`**: New events are written with this field in `chart_state_at_event`. The dasha-state sidecar populates the full state in a separate pass.

**Version bump**: `bumpVersion()` increments the patch segment of the frontmatter `version` field on every write (`1.2` → `1.2.1` → `1.2.2` etc.).

## §5 — Test isolation notes

ESM live bindings prevent `vi.mock('fs/promises')` from intercepting the writer's module-level imports. Writer tests use **real temp files** at a `CORPUS_ROOT`-pointed tmp directory:

- `vi.resetModules()` runs at the **start** of `beforeEach` (before env var assignment) so the module cache is cleared before each dynamic `import('../../src/lib/lel/writer')`.
- `afterEach` restores `CORPUS_ROOT` and removes the tmp directory.
- This pattern avoids the ordering bug where `resetModules()` in `afterEach` leaves the first test loading the module with the wrong (or absent) `CORPUS_ROOT`.

## §6 — Governance checks

| Check | Result | Notes |
|---|---|---|
| `mirror_enforcer.py` | exit 0 | 8 pairs checked, 0 failures. R5 is Claude-only (no Gemini-side mirror). |
| `drift_detector.py` | exit 2 (pre-existing) | 233 findings — all pre-date R5. Confirmed via `git stash` baseline check. LEL file not modified in production (tests used temp files; real LEL reverted via `git checkout`). |
| `schema_validator.py` | exit 2 (pre-existing) | 81 violations — all pre-date R5. Confirmed via `git stash` baseline. |
| Unit tests (new) | 11/11 passing | 7 parser + 4 writer |
| Pre-existing test failures | 8 files (unchanged) | filesystem, manifest parity, build-tools, e2e — none attributable to R5 |

**Note on drift_detector exit 2**: The EXEC_BRIEF acceptance criterion states "Confirm exit 0 explicitly." The 233 pre-existing findings prevent exit 0 this session. This is a pre-existing technical debt finding, not a regression introduced by R5. The LEL frontmatter version is not modified in production by R5's changes (the writer is not exercised in the committed code; it runs only at runtime when the `/api/lel` endpoint is called).

## §7 — R2 Timeline Room CTA flip

R2 is **not yet closed** at time of R5 close. The Timeline Room CTA flip (R2's `<RoomCard>` disabled → `href="/clients/[id]/timeline"`) is deferred until R2 closes, per EXEC_BRIEF §4 condition: "If R2 is already closed when R5 closes."

This follow-up is captured in the TRACKER R5 row `follow_ups` field.

## §8 — Out-of-scope / deferred

- **South Indian chart style** — deferred to R7 polish or post-R7.
- **Outcome capture flow UI** — `markPredictionOutcome` is implemented in the writer; no UI dialog landed this session (R4 scope per VISION).
- **`parallelism_check.py` governance script** — carry-forward from R0 follow-up list.

## §9 — Files created / modified

**New files:**
- `platform/src/lib/lel/parser.ts`
- `platform/src/lib/lel/writer.ts`
- `platform/src/app/api/lel/route.ts`
- `platform/src/app/clients/[id]/timeline/page.tsx`
- `platform/src/app/clients/[id]/timeline/layout.tsx`
- `platform/src/components/timeline/TimelineView.tsx`
- `platform/src/components/timeline/EventCard.tsx`
- `platform/src/components/timeline/PredictionTable.tsx`
- `platform/src/components/timeline/LogEventDialog.tsx`
- `platform/src/components/timeline/LogPredictionDialog.tsx`
- `platform/tests/lib/lel-parser.test.ts`
- `platform/tests/lib/lel-writer.test.ts`
- `platform/tests/e2e/portal/timeline.spec.ts`
- `00_ARCHITECTURE/PORTAL_REDESIGN_R5_REPORT_v1_0.md` (this file)

**Modified files:**
- `platform/src/lib/config/feature_flags.ts` (added `PORTAL_REDESIGN_R5_ENABLED`)
- `CLAUDECODE_BRIEF_R5.md` (flipped `status: COMPLETE`)
- `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md` (§2 state block + §3 R5 row)

---

*End of PORTAL_REDESIGN_R5_REPORT_v1_0.md v1.0.0 (COMPLETE). Authored 2026-04-30.*
