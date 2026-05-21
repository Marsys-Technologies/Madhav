---
artifact: PORTAL_REDESIGN_R4_REPORT_v1_0
artifact_id: PORTAL_REDESIGN_R4_REPORT
version: 1.0
status: COMPLETE
phase: R4
phase_name: Consume polish — report gallery + trace drawer + tier picker + prediction-log
authored_by: Claude Code (Sonnet 4.6)
authored_at: 2026-04-30
session_id: redesign-r4-consume-polish-2026-04-30
exec_brief: EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
worktree: ~/Vibe-Coding/Apps/Madhav-r4
branch: redesign/r4-consume-polish
risk_classification: LOW
---

# Portal Redesign R4 — Closure Report

## §1 — Pre-flight gate result

All pre-flight checks passed at session open:

| Check | Result |
|---|---|
| R0 closed | ✅ TRACKER §3 R0 row: `status: closed` |
| `trace_fix_status` | ✅ `on_hold` — no collision |
| Working tree clean | ✅ Branch `redesign/r4-consume-polish` in worktree |
| No in-flight parallel collision | ✅ No other phase `in_flight` |

## §2 — Deliverables landed

### §2.1 — `<ReportGallery>` (EXEC_BRIEF §1)

**New file:** `platform/src/components/consume/ReportGallery.tsx`

Grid of report cards (3-col desktop, 2-col tablet, 1-col mobile) replacing the flat list.
Each card: domain icon + domain label + title (2-line clamp) + freshness chip.

Freshness chip colors: green `<14d`, amber `14–60d`, red `>60d`.

**New file:** `platform/src/lib/consume/domain-icons.ts`

Extracted `DOMAIN_ICONS` map and `domainIcon()` helper from `ReportLibrary.tsx` into shared lib.
Added `freshnessColor()` helper for the three-tier chip logic.

**Modified:** `platform/src/components/consume/ReportLibrary.tsx`

Added `view: 'list' | 'gallery'` prop (default `'gallery'`). In gallery mode renders `<ReportGallery>`; in list mode preserves the original flat list. Consumes domain icon from shared `lib/consume/domain-icons.ts`.

**Modified:** `platform/src/components/consume/ConsumeChat.tsx`

Added `reportView` state (default `'gallery'`) persisted to `localStorage` at key `marsys.consume.reportView`. `<ReportLibrary>` receives `view={reportView}`. Command palette gains gallery/list toggle commands.

### §2.2 — `<TraceDrawer>` (EXEC_BRIEF §2)

**New file:** `platform/src/components/consume/TraceDrawer.tsx`

Uses shadcn `<Sheet side="right">` (base-ui backed, already in `components/ui/sheet.tsx`). Contains `<TracePanelContent>` as its body. Full-width on mobile via Sheet's responsive classes.

**Modified:** `platform/src/components/trace/TracePanel.tsx`

Extracted the stateful body (tabs, live/history, step selection, context inspector, timeline bar) into `TracePanelContent` — a new named export. `<TracePanel>` now wraps `TracePanelContent` with the legacy fixed-position backdrop + header for backward compatibility. Both consumers (TraceDrawer + TracePanel) share the same render body.

**Modified:** `platform/src/components/consume/AnswerView.tsx`

Added `traceId?: string` and `queryId?: string` props. When `traceId` is present, renders a footer containing a Trace button (opens local `TraceDrawer` state) and `<LogPredictionAction>`.

**Modified:** `platform/src/components/consume/ConsumeChat.tsx`

Removed `tracePanelOpen` state and the `<TracePanel>` always-on usage. Added `traceDrawerOpen` state. The Trace button in the toolbar now opens `<TraceDrawer>` with `session.currentQueryId`. `<TracePanel>` is no longer imported.

### §2.3 — `<TierPicker>` (EXEC_BRIEF §3)

**New file:** `platform/src/components/consume/TierPicker.tsx`

Segmented control (3 buttons: Client | Admin | Super) with `role="group"` accessibility. Active tier styled with `--brand-gold` background.

**Modified:** `platform/src/components/consume/ConsumeChat.tsx`

Added `activeTier` state (initialized from `?tier=` URL param or `initialAudienceTier` prop). `<TierPicker>` rendered in the toolbar area, visible to `super_admin` only. `handleTierChange` updates state + URL query via `history.replaceState` (no re-mount). Previous messages retain their original rendered tier — the new tier applies to the next query.

### §2.4 — `<LogPredictionAction>` (EXEC_BRIEF §4)

**New file:** `platform/src/lib/consume/prediction-detection.ts`

`detectPrediction(text)` — regex heuristic covering seven pattern classes:
- `by {month} {year}` / `by {year}` / `by next {period}`
- `in the next N {days|weeks|months}`
- `before {month} {year}` / `before the end of this year`
- `during {name} dasha`
- `{name} dasha will`
- `in {year}` (20xx)
- `within the next N {months|years}`

Returns `{ detected, horizon?, confidence? }`. False positives acceptable per brief.

**New file:** `platform/src/components/consume/LogPredictionAction.tsx`

Rendered in `<AnswerView>` footer (and thereby in `<PanelAnswerView>` which uses AnswerView). Self-hides when `detectPrediction` returns `false`. Button opens `<LogPredictionDialog>` (inline in same file) which:
- Pre-fills horizon from detector
- Requires falsifier (Learning Layer rule #4 sacrosanct invariant)
- Confidence slider 0–1 (default 0.7)
- POSTs to `POST /api/lel`
- On success: toast `Prediction logged · PRED.{id}`, button flips to checkmark

**New file:** `platform/src/app/api/lel/route.ts`

Minimal `POST` endpoint. Validates required fields, calls `logPrediction()` from `lib/prediction/writer.ts` (already existed), returns `{ id }` with HTTP 201. Input validation mirrors writer's own validation for defense-in-depth. R5 will enhance or replace this endpoint when the full Timeline surface lands.

## §3 — Tests

| File | Type | Coverage |
|---|---|---|
| `tests/components/ReportGallery.test.tsx` | unit | card count, empty state, freshness chip colors, onSelect callback |
| `tests/components/TraceDrawer.test.tsx` | unit | open/closed states, queryId passthrough, title rendering |
| `tests/components/TierPicker.test.tsx` | unit | 3 buttons, active highlighting, onChange callbacks, a11y group |
| `tests/components/LogPredictionAction.test.tsx` | unit | no-render when undetected, dialog open, falsifier required error, POST call |
| `tests/unit/prediction-detection.test.ts` | unit | 10 positive patterns, 3 negative patterns, confidence shape |
| `tests/e2e/portal/consume-polish.spec.ts` | E2E | gallery render, tier picker visibility + URL persistence, trace drawer open/close |

E2E tests require `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` (same env contract as `cutover:stage1-smoke`); they self-skip in CI without those env vars.

## §4 — Scope compliance

All changes are within `may_touch` globs. No `must_not_touch` paths were modified.

Narrow edits confirmed:
- `TracePanel.tsx`: render-body extracted into `TracePanelContent`; trace data model, SSE stream, `conversation_id` propagation untouched.
- `ConsumeChat.tsx`: `<TracePanel>` import removed; `<TraceDrawer>` wired in; `<TierPicker>` added to toolbar; `view` prop threaded to `<ReportLibrary>`. API surface unchanged.
- `AnswerView.tsx`: two new optional props added; no breaking change to existing callers.
- `PanelAnswerView.tsx`: one new optional prop `traceId` added; no breaking change.

## §5 — Governance scripts

| Script | Exit code | Notes |
|---|---|---|
| `drift_detector.py` | 2 (233 findings) | Pre-existing — identical count on `main` before R4 changes; R4 introduced zero new drift violations |
| `schema_validator.py` | 2 (81 violations) | Pre-existing — same baseline |
| `mirror_enforcer.py` | **0** | 8 pairs checked, 8 passed; redesign is Claude-only (no Gemini-side mirror) |

Pre-existing drift and schema violations are tracked in `ONGOING_HYGIENE_POLICIES_v1_0.md §I` known_residuals.

## §6 — Follow-ups

- E2E tests require a dev server + auth cookie to run; run `npm run dev` then `npx playwright test tests/e2e/portal/consume-polish.spec.ts` with `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` set.
- `<TierPicker>` currently shows 3 options; `acharya_reviewer` tier is omitted per brief (super_admin, admin, client only). Can be expanded when that tier requires QA.
- R5 may introduce a richer `/api/lel` endpoint; when it does, `route.ts` in this R4 should be reviewed for consolidation.
- `trace_fix_status` remained `on_hold` throughout R4 execution. If trace-fix work resumes, it should rebuild against `<TraceDrawer>` rather than the retired always-on `<TracePanel>` usage.

---

*End of PORTAL_REDESIGN_R4_REPORT_v1_0.md (COMPLETE, 2026-04-30).*
