---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md and execute it."
phase: Portal Redesign R4
phase_name: Consume polish — report gallery + trace drawer + tier picker + prediction-log
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: LOW
parallelizable_with: [R1, R2, R3, R5, R6]
must_complete_before: [R7]
depends_on: [R0]
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R4_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R4 — Consume polish

## Mission

The Consume tab is already at v3 quality (mature ChatShell, streaming, branches, command palette, model picker, share). R4 is polish, not rebuild. Land four refinements:

1. `<ReportGallery>` — re-render the flat `ReportLibrary` list as a card gallery with domain icons and freshness indicators.
2. `<TraceDrawer>` — collapse the always-visible `TracePanel` into a side drawer triggered from each answer's footer.
3. `<TierPicker>` — surface the audience-tier selector explicitly so super_admin can flip between client/admin/super_admin views to QA the same answer.
4. `<LogPredictionAction>` — when an answer contains a time-indexed claim, offer a button that writes to the LEL prediction subsection per `CLAUDE.md §E`.

Zero schema changes, zero migrations, zero sidecar changes, zero auth model changes.

## Pre-flight gate

Halt if any fail.

1. R0 closed. `<AppShell>` and `<ZoneRoot>` exist.
2. Vision exists; R4 row in TRACKER §3 reflects authored or earlier.
3. **`tracker.trace_fix_status` is `on_hold` or `merged`. If `in_flight`, halt** — collision per VISION §4.3.2 reapplies; serialize R4 against the trace fix.
4. Working tree clean. Branch `redesign/r4-consume-polish`.

## Scope declaration

```yaml
may_touch:
  - platform/src/components/consume/ReportLibrary.tsx                 # narrow edit: add view-mode prop
  - platform/src/components/consume/ReportGallery.tsx                 # NEW
  - platform/src/components/consume/TraceDrawer.tsx                   # NEW (wraps existing TracePanel content)
  - platform/src/components/consume/TierPicker.tsx                    # NEW
  - platform/src/components/consume/LogPredictionAction.tsx           # NEW
  - platform/src/components/consume/ConsumeChat.tsx                   # narrow edits: wire new components
  - platform/src/components/consume/AnswerView.tsx                    # narrow edit: footer slot
  - platform/src/components/consume/PanelAnswerView.tsx               # narrow edit: same footer slot
  - platform/src/components/trace/TracePanel.tsx                      # narrow edit: extract render-body into TracePanelContent
  - platform/src/lib/consume/prediction-detection.ts                  # NEW
  - platform/src/app/api/lel/route.ts                                 # may exist from R5; if not, minimal append-only endpoint
  - tests/e2e/portal/consume-polish.spec.ts                           # NEW
  - tests/components/ReportGallery.test.tsx                           # NEW
  - tests/components/TraceDrawer.test.tsx                             # NEW
  - tests/components/TierPicker.test.tsx                              # NEW
  - tests/components/LogPredictionAction.test.tsx                     # NEW
  - tests/lib/prediction-detection.test.ts                            # NEW
must_not_touch:
  - 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/app/api/                                             # except /api/lel if R5 didn't land it
  - platform/src/lib/db/types.ts
  - platform/src/lib/firebase/
  - platform/src/components/shared/AppShell.tsx
  - platform/src/components/dashboard/, build/, chat/                 # other-phase scope
  - platform/src/app/clients/[id]/page.tsx, build/                    # R2/R3 scope
  - platform/src/app/api/chat/consume/route.ts                        # NO API surface change
  - platform/src/lib/strategies/single_model_strategy.ts              # synthesis untouched
```

**Critical scope note on `TracePanel.tsx`.** R4 extracts the panel's render-body into `<TracePanelContent>` that `<TraceDrawer>` consumes. R4 does NOT modify the trace data model, the SSE stream consumption, or the `conversation_id` propagation logic. If trace-fix work resumes later, it merges into the trace endpoint and synthesis strategy — surfaces R4 doesn't touch.

## §1 — `<ReportGallery>`

Path: `platform/src/components/consume/ReportGallery.tsx`. Grid of report cards replacing the flat `ReportLibrary` list. Each card: domain icon (Lucide; consolidate into `DOMAIN_ICONS` map in `lib/consume/domain-icons.ts`); domain label (Source Serif 4 16px); title (Source Serif 4 14px, two-line clamp); freshness chip (relative time, color: green <14d, amber 14–60d, red >60d or known-stale); click → opens `<ReportReader>`.

Layout: 3-col desktop, 2-col tablet, 1-col mobile. `--card` token handles dark surface in ink zone.

`<ReportLibrary>` gains `view: 'list' | 'gallery'` prop (default `'gallery'`). Persist user preference to `localStorage` (`marsys.consume.reportView`).

## §2 — `<TraceDrawer>`

Path: `platform/src/components/consume/TraceDrawer.tsx`. Uses shadcn `<Sheet>` (already in `components/ui/sheet.tsx`). Triggered from a "Trace" button in each answer's footer. Slides from right on desktop, full-screen on mobile.

Drawer contents: existing `<TracePanel>` body, refactored as `<TracePanelContent>` so the drawer and (now-deprecated) always-on panel share render code. Always-on usage in `<ConsumeChat>` is removed; drawer is the only entry post-R4.

`<AnswerView>` gets a `traceId` prop and renders the Trace button conditionally (only when a trace exists for that query).

## §3 — `<TierPicker>`

Path: `platform/src/components/consume/TierPicker.tsx`. Small segmented control in the Consume chat header next to the model picker. Three options: `client | admin | super_admin`. Visible to super_admin only.

Behavior: changing tier reloads the current conversation with the new tier passed to the API as a request parameter. Existing `audienceTier` prop on `<ConsumeChat>` becomes user-settable. Previous messages retain their original tier and gain a small "rendered as: super_admin" badge for clarity. State persists to URL query (`?tier=admin`).

Closes a finding from `EXEC_BRIEF_PHASE_11A_DEBUG_v1_0.md` — super_admin previously had no way to QA "what does this answer look like for a `client`?" without logging out.

## §4 — `<LogPredictionAction>`

Path: `platform/src/components/consume/LogPredictionAction.tsx`. Rendered in `<AnswerView>` and `<PanelAnswerView>` footer alongside the Trace button — but only when `detectPrediction(answerText)` returns true.

`detectPrediction` heuristic in `lib/consume/prediction-detection.ts`: regex-based detection of time-indexed claims. Patterns: "by {date|month|year}", "in the next {N} {days|weeks|months}", "before {date}", "during {dasha period}", "Mars dasha will...", "in {year}". Returns `{ detected: boolean; horizon?: string; confidence?: number }`. False positives acceptable — user has final say.

Button opens `<LogPredictionDialog>` (NEW in R4 — distinct from R5's if R5 already authored one; share via `lib/lel/` if so):
- Pre-fills horizon from detector.
- Prompts for explicit falsifier (the "what observation would refute this" field, per `MACRO_PLAN_v2_0.md` Learning Layer discipline rule #4 "held-out prospective data is sacrosanct").
- Prompts for confidence (slider 0–1).
- Submit calls `POST /api/lel` with prediction payload (same endpoint R5 lands; if R5 hasn't, this brief includes minimal version).

After submit: toast "Prediction logged · PRED.{id}", action button flips to checkmark indicator.

Per `CLAUDE.md §E`: until `06_LEARNING_LAYER/` is scaffolded, predictions stored in LEL prediction subsection. Action writes there. When learning layer lands, storage moves with no UI change.

## §5 — Tests

`tests/e2e/portal/consume-polish.spec.ts`: super_admin opens consume; sees Tier picker; flips to client view, verifies render change; opens an answer, clicks Trace → drawer opens; closes; clicks Log Prediction → dialog opens, fills falsifier + confidence, submits, asserts checkmark indicator.

Unit tests for each new component. Unit tests for `prediction-detection.ts` covering regex patterns + edge cases.

Visual regression on consume route. Governance scripts exit 0.

## §6 — Closure report

`00_ARCHITECTURE/PORTAL_REDESIGN_R4_REPORT_v1_0.md` with `status: COMPLETE`. Update TRACKER §3 R4 row to closed.

If `trace_fix_status` flipped from on_hold → in_flight DURING R4 execution, closure report MUST surface this in `follow_ups` so trace-fix work picks up against R4's `<TraceDrawer>`.

## §7 — Out of scope

- Do NOT modify the consume route's API contract.
- Do NOT change synthesis strategies.
- Do NOT modify the trace SSE endpoint or its data model.
- Do NOT modify `audienceTier` parameter's downstream behavior in synthesis — only its UI selectability.
- Do NOT introduce a separate prediction-storage model; route via LEL (or future Learning Layer when it lands).
- Do NOT delete `<TracePanel>` itself; only retire its always-on usage.

## §8 — One-line summary

Take the Consume tab from "good v3" to "polished v3.1" with a gallery, a drawer, a tier flip, and a prediction-log shortcut — all additive, all on top of the existing mature shell.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R4_CONSUME_POLISH_v1_0.md (AUTHORED, re-authored 2026-04-30 after surgical-fix data loss).*
