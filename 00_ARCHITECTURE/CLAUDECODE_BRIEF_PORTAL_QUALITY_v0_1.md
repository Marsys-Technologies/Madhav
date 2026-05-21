---
artifact: CLAUDECODE_BRIEF_PORTAL_QUALITY_v0_1.md
version: 0.1
status: DRAFT
status_set_drafted_on: 2026-04-27
session_id: Madhav_PORTAL_QUALITY_v0_1
authored_by: Cowork (Claude Opus 4.7) on 2026-04-27
authored_during: Cowork conversation "Madhav — Consume staleness gap → adaptive design → portal quality pass"
governing_clause: CLAUDE.md §C item 0 — when this file is promoted to project root as CLAUDECODE_BRIEF.md and status is set to AUTHORED, it overrides items 1–11 reading sequence and any other scope guidance for the duration of the session.
target_executor: Claude Code (Google Anti-Gravity / VS Code extension), Sonnet 4.6
expected_session_class: Portal frontend quality pass — bug fixes + small serializer adjustments. Not M2 corpus execution. Not on the M2A-Exec sequence.
predecessor_session: Madhav_M2A_Exec_8 (must close first — B.4 phase final close gates this session because Exec_8 owns the active CLAUDECODE_BRIEF.md slot at root)
canonical_phase_pointer: "PORTAL_BUILD_TRACKER_PLAN_v0_1.md (frozen reference). This brief is a quality-pass amendment to the v0.1 portal, not a phase-plan execution."
scheduling_note: "Dispatch when (a) Exec_8 has closed, (b) the root CLAUDECODE_BRIEF.md slot is free, and (c) native has approved this brief's scope. No corpus state dependency — can run in parallel with B.5 work conceptually, but Claude Code single-session-at-a-time discipline says back-to-back."
governance_status: NOT YET ADOPTED — awaits native review. Once approved, copy to project root as `CLAUDECODE_BRIEF.md` with status `AUTHORED`.
---

# CLAUDECODE_BRIEF — PORTAL QUALITY PASS v0.1

## §1 — Why this session exists

The build tracker portal at `/build` and its sub-routes is the native's daily cockpit for project state. A Cowork audit on 2026-04-27 found ten quality issues spanning three bugs the native flagged directly (sidebar dot status, sub-phase ordering, overall-journey percentage) plus seven smaller findings across `/build/health`, `/build/parallel`, `/build/activity`, and the data freshness surface. Each issue is small in isolation; together they erode the trust the cockpit depends on.

This session ships all ten fixes in one focused pass. It does not change architecture, does not touch the corpus, does not touch the python-sidecar, and does not touch any L1–L6 layer file. Scope is bounded to the TypeScript portal under `platform/src/{app,components,lib}/build/**` plus a small set of changes to `platform/scripts/governance/serialize_build_state.py` for hardcoded workstreams and any verified data-flow gap in milestone status.

**Out of scope (explicitly).** No new portal features. No new pages. No design system overhaul. No re-skinning. No router changes. No auth changes. The Consume design discussed in `00_ARCHITECTURE/CONSUME_DESIGN_v0_1.md` is a separate future track and is not touched here.

## §2 — Active context (executor must re-verify at session open)

- **Macro phase:** M2 — Corpus Activation, active. This session does NOT touch corpus state.
- **Active phase-plan expansion:** `PHASE_B_PLAN_v1_0.md` v1.0.x — frozen for this session, read-only.
- **Predecessor session:** `Madhav_M2A_Exec_8` must be CLOSED at session open. Verify by reading `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` and confirming `last_closed_session_id` reads `Madhav_M2A_Exec_8` and `b4_full_close_pending` is `null`.
- **Red-team counter:** at session open, counter is 0 (reset post-Exec_8 cadence pass). This session does NOT increment the counter (not M2 execution).
- **Mirror discipline:** this session touches no MP.1–MP.5 mirror pair surface. MP.7 (SESSION_LOG) updates normally at close.
- **Cloud SQL:** not touched. No Auth Proxy required.
- **GCS:** read-only. Build-state JSON is fetched at runtime by `dataSource.ts`; no upload required unless serializer changes (AC.5) demand a re-emit, in which case run the serializer's `--upload-to-gcs` flag at session close.

## §3 — Inputs (already in project)

### Frontend code (read + edit per scope)

- `platform/src/components/build/PlanTree.tsx` — sidebar tree component. AC.1 + AC.2 target.
- `platform/src/components/build/PhaseGrid.tsx` — sub-phase card grid. AC.2 target.
- `platform/src/lib/build/derive.ts` — derived metrics (`macroCompletionPercent`, `phaseCompletionPercent`). AC.3 target.
- `platform/src/lib/build/format.ts` — formatters and helpers. AC.2 target (add `naturalSort`).
- `platform/src/lib/build/types.ts` — type definitions for `BuildState`, `MacroPhaseEntry`, `Milestone`. Read-only.
- `platform/src/lib/build/dataSource.ts` — GCS fetch path. Read-only this session.
- `platform/src/app/build/health/page.tsx` — Health page. AC.4 target.
- `platform/src/app/build/parallel/page.tsx` — Parallel workstreams page. AC.6 target.
- `platform/src/app/build/activity/page.tsx` — Activity feed page. AC.7 target.
- `platform/src/app/build/layout.tsx` (or equivalent shared layout) — AC.8 target (add freshness indicator).

### Serializer (read + small edit)

- `platform/scripts/governance/serialize_build_state.py` — emits `build-state.json`. Edits required for AC.5 (workstreams) and possibly AC.1 (verify milestone status flow).

### Reference (read-only)

- `00_ARCHITECTURE/PORTAL_BUILD_TRACKER_PLAN_v0_1.md` — original portal plan. Read sections D.1–D.5 for design intent context.
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — verify Exec_8 close before proceeding.
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` — read-only, for FILE_REGISTRY row context.

## §4 — Scope declarations

### `may_touch` (globs)

```
platform/src/components/build/PlanTree.tsx
platform/src/components/build/PhaseGrid.tsx
platform/src/lib/build/derive.ts
platform/src/lib/build/format.ts
platform/src/app/build/health/page.tsx
platform/src/app/build/parallel/page.tsx
platform/src/app/build/activity/page.tsx
platform/src/app/build/layout.tsx                                          # for global freshness indicator (AC.8)
platform/src/components/build/FreshnessIndicator.tsx                       # NEW component (AC.8) — small footer/header chip
platform/scripts/governance/serialize_build_state.py                       # AC.5 (workstreams derivation) + AC.1 verification
verification_artifacts/PORTAL/portal_quality_v0_1_visual_check.md          # NEW — manual visual-check report at close
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                                       # state pointer update at close
00_ARCHITECTURE/SESSION_LOG.md                                              # atomic append at close
00_ARCHITECTURE/FILE_REGISTRY_v1_9.md                                       # superseded banner if any new file registers
00_ARCHITECTURE/FILE_REGISTRY_v1_10.md                                      # NEW version with portal-quality deliverables (FreshnessIndicator + verification artifact)
00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md                                    # amendment log entry
CLAUDECODE_BRIEF.md                                                         # status:COMPLETE at close
```

### `must_not_touch` (globs)

```
01_FACTS_LAYER/**                                                           # L1 immutable
025_HOLISTIC_SYNTHESIS/**                                                   # L2.5 frozen
03_DOMAIN_REPORTS/**                                                        # L3 read-only
035_DISCOVERY_LAYER/**                                                      # L3.5 active in B.5
04_REMEDIAL_CODEX/**                                                        # L4 frozen
05_TEMPORAL_ENGINES/**                                                      # L5 frozen
06_LEARNING_LAYER/**                                                        # L6 active substrate
00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md                                        # frozen
00_ARCHITECTURE/MACRO_PLAN_v2_0.md                                          # frozen
00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md                                # frozen
00_ARCHITECTURE/PORTAL_BUILD_TRACKER_PLAN_v0_1.md                            # original plan; read-only reference
00_ARCHITECTURE/CONSUME_DESIGN_v0_1.md                                       # separate track; read-only
00_ARCHITECTURE/GOVERNANCE_BASELINE_v1_0.md
00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md
00_ARCHITECTURE/STEP_LEDGER_v1_0.md                                          # GOVERNANCE_CLOSED
00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md                       # only edit if a NEW ND opens (none expected)
00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md
00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md                               # only edit if a NEW DIS opens (none expected)
00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md                                 # read-only this session (FILE_REGISTRY changes don't require canonical-artifacts changes)
platform/python-sidecar/**                                                   # entire python-sidecar — NOT in scope
platform/supabase/migrations/**                                              # DB schema — NOT in scope
platform/scripts/governance/**                                               # except serialize_build_state.py per AC.5/AC.1
.geminirules                                                                  # MP.1 — no Gemini-side change this session
.gemini/**                                                                    # MP.2/3/4 — no Gemini-side change this session
035_DISCOVERY_LAYER/PROMPTS/**                                                # B.4/B.5 territory
035_DISCOVERY_LAYER/REGISTERS/**                                              # B.5 territory
06_LEARNING_LAYER/LEDGER/**                                                   # B.4/B.5 ledger; not touched
06_LEARNING_LAYER/PREDICTION_LEDGER/**                                        # not touched
verification_artifacts/RAG/**                                                  # B.4 deliverables; read-only
```

## §5 — Acceptance criteria (each AC is a discrete, testable deliverable)

**AC.1 — Sidebar dot color reflects status (Bug 1).**
- Edit `PlanTree.tsx` `statusDot()` (lines 14–19): replace `bg-foreground` for completed with explicit `bg-emerald-500`. Keep `bg-amber-500` for in_progress/active. Keep `bg-muted-foreground/30` for pending. Add a fourth case for unknown/missing status returning `bg-muted-foreground/15` (more muted than pending).
- Verify the milestone status flow: read `serialize_build_state.py` lines 644–667 and confirm `m2_milestones[].status` is set to `"completed"` for B.0–B.5 and B.10. If the upstream `phase_b_plan` data isn't carrying status, fix the population path so it does. Add a smoke check: serializer emits `build-state.json` with `macro_arc[1].milestones[i].status === "completed"` for each completed sub-phase.
- **Verification:** manual visual check on `/build/plan` with M2 expanded: completed sub-phases show emerald dots; pending B.6–B.9 show muted gray; in-progress (none today) would show amber. Capture screenshot in `verification_artifacts/PORTAL/portal_quality_v0_1_visual_check.md`.

**AC.2 — Natural sort on sub-phase IDs (Bug 2).**
- Add `naturalSort(a: string, b: string): number` helper to `platform/src/lib/build/format.ts`. Implementation mirrors `_phase_id_sort_key()` in `serialize_build_state.py` lines 430–435: tokenize the ID into segments split by `.`, parse numeric segments as integers, compare segment-by-segment, fall back to string compare for non-numeric. Test cases (in a colocated test file or doc-comment): `B.3.5` sorts between `B.3` and `B.4`; `B.10` sorts after `B.9`; `M.10` sorts after `M.9`.
- Apply in `PhaseGrid.tsx` line 31: `const sorted = subPhases.slice().sort((a, b) => naturalSort(a.phase_id, b.phase_id))` then map over `sorted`.
- Apply in `PlanTree.tsx` line 73: `const sortedMilestones = milestones.slice().sort((a, b) => naturalSort(a.id, b.id))` then map over `sortedMilestones`.
- **Verification:** unit test `format.test.ts` with three cases above. Visual check on `/build/plan`: B.0 first, B.10 last, B.3.5 between B.3 and B.4, in both sidebar and card grid.

**AC.3 — Overall journey percent weights partial active macro progress (Bug 3).**
- Edit `derive.ts` `macroCompletionPercent()` lines 65–70. New logic: count fully-closed macros, plus add the active macro's `phaseCompletionPercent / 100` as a fractional contribution. Formula: `Math.round(((closedMacros + activeMacroFraction) / arc.length) * 100)`.
- The active macro is the entry where `status === 'active'` (or equivalently, `state.macro_phase.id === entry.id`). The active macro's fraction is the existing `phaseCompletionPercent(state)` divided by 100.
- **Verification:** with M1 closed (1 macro complete) and M2 at 8/12 sub-phases complete (`phaseCompletionPercent = 67`), `macroCompletionPercent` returns 17 (rounded from 16.7). Add a unit test case to confirm. Visual check: the gauge on `/build/plan` reads 17%, not 10%.

**AC.4 — Health page distinguishes "unknown" from "healthy" (sub-page sweep #1).**
- Edit `platform/src/app/build/health/page.tsx` line 16. Current logic: `lastDrift === 0 && lastSchema === 0 && lastMirror === 0`. New logic: introduce three states — `healthy` (all three === 0), `unhealthy` (any non-zero numeric), `unknown` (any null/undefined). Render distinct visual treatment for unknown (gray badge, "No recent run") vs healthy (emerald badge, "All clear") vs unhealthy (amber/red badge, "N findings").
- **Verification:** manually set one of the three exit codes to `null` in the local JSON and confirm "unknown" badge renders. Reset and confirm "healthy" badge renders.

**AC.5 — Parallel workstreams derived from source (sub-page sweep #2).**
- Edit `serialize_build_state.py` lines 1415–1424. Replace hardcoded LEL/PPL/BUILD_TRACKER/GOVERNANCE_HYGIENE entries with derived data:
  - LEL: read `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` frontmatter; emit `event_count` from the actual events array length and `last_activity` from the file's mtime or frontmatter date.
  - PPL: read `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl`; emit `prediction_count` from line count and `last_activity` from file mtime. If the file is empty, status is "scaffold-only"; if non-empty, status is "active".
  - BUILD_TRACKER: derive from this very serializer's run state (status="active", last_activity=`generated_at`).
  - GOVERNANCE_HYGIENE: derive from `verification_artifacts/{drift,schema,mirror}/` latest run timestamps.
- Emit a stable schema; document field meanings in a comment block at the new derivation site.
- **Verification:** add an event to LEL (don't actually mutate LEL — just simulate by changing the count in a test fixture), re-run serializer, confirm parallel page reflects the change. Real verification: re-run serializer at session close, manually open `/build/parallel`, confirm displayed counts match source files.

**AC.6 — Cowork ledger order (sub-page sweep #3).**
- Edit `platform/src/app/build/parallel/page.tsx` line 62. Remove the `.reverse()` call. Document in a comment that the serializer emits cowork ledger newest-first; the frontend renders as-emitted.
- Verify in `serialize_build_state.py` that cowork ledger is emitted newest-first; if it isn't, fix the serializer instead.
- **Verification:** `/build/parallel` shows cowork ledger threads with the most recently closed thread at top.

**AC.7 — Activity page filter dropdowns use natural sort (sub-page sweep #4).**
- Edit `platform/src/app/build/activity/page.tsx` lines 11–12. Apply `naturalSort` (from AC.2) to the deduplicated class and phase arrays before passing to the filter dropdown.
- **Verification:** dropdowns show B.0, B.1, B.2, ..., B.9, B.10 in numerical order, not B.0, B.1, B.10, B.2, ..., B.9.

**AC.8 — Build-state freshness indicator on every page (sub-page sweep #5).**
- Create new component `platform/src/components/build/FreshnessIndicator.tsx`. Reads `state.generated_at` (ISO 8601), renders a small chip showing "Generated · {relative time}" with a tooltip showing the absolute timestamp. Style: subtle, footer-positioned, `bt-label` typography.
- Render `<FreshnessIndicator />` in `platform/src/app/build/layout.tsx` (or whichever shared layout wraps all `/build/*` pages) as a footer or top-right header element.
- Optional: add a "Refresh" button that triggers `router.refresh()` to re-fetch the JSON. Decision: include the button for v0.1.
- **Verification:** every `/build/*` page renders the freshness indicator. Click refresh, confirm fresh fetch from GCS (Network tab shows `cache: 'no-store'` request).

**AC.9 — Style consistency for status badges/dots.**
- After AC.1 + AC.4 land, audit visual treatment of status across all `/build/*` pages. Document the canonical mapping in a brief comment block at the top of `format.ts` or a new `statusVisual.ts` helper:
  - `completed` → emerald
  - `active`/`in_progress` → amber
  - `pending` → muted-foreground/30
  - `unknown` → muted-foreground/15
  - `unhealthy` → red (only on health page)
- **Verification:** visual grep across `/build/cockpit`, `/build/plan`, `/build/health`, `/build/parallel`, `/build/registry`, `/build/sessions`, `/build/interventions`, `/build/activity` — every status indicator uses the mapping above.

**AC.10 — Quality gates pass.**
- `npm run lint` exits 0.
- `npm run typecheck` (or equivalent) exits 0.
- `npm run test -- format` (the new naturalSort test) passes.
- If a portal smoke test exists, it passes.
- **Verification:** capture each command's exit status in the verification artifact.

## §6 — Hard constraints

- **Do not change architecture.** This is a quality pass, not a redesign. The portal's IA, routing, auth gating, and data flow shape are unchanged.
- **Do not pre-build for B.6/B.7.** This brief does not anticipate the Consume design (`CONSUME_DESIGN_v0_1.md`). That work lands when ND.2 is authored and B.6's brief expands.
- **No corpus state changes.** No edits to L1–L6 layer files, no DB writes, no GCS writes other than re-emitting `build-state.json` if AC.5's serializer change demands it.
- **No mirror-pair touches.** This session does not touch `.geminirules`, `.gemini/project_state.md`, or any MP.1–MP.5 surface.
- **One PR/commit per AC if possible.** Aids reviewability. If multiple ACs land in one commit, the commit message must enumerate them.

## §7 — Verification deliverable

At session close, write `verification_artifacts/PORTAL/portal_quality_v0_1_visual_check.md` containing:
- Screenshot or text-described visual confirmation of AC.1, AC.2, AC.3, AC.4, AC.6, AC.7, AC.8 on a running local dev server.
- Output of `npm run lint`, `npm run typecheck`, and the new test (AC.10).
- A summary table: AC.1 ✓, AC.2 ✓, ..., AC.10 ✓.

## §8 — Close-checklist additions (beyond standard SESSION_CLOSE_TEMPLATE)

- `CURRENT_STATE.last_closed_session_id` → `Madhav_PORTAL_QUALITY_v0_1`.
- `CURRENT_STATE.next_session_objective` → next M2 phase per arc (likely B.6 or B.5 continuation, depending on B.5 multi-session schedule).
- `FILE_REGISTRY` bump to v1.10 if `FreshnessIndicator.tsx` and the verification artifact register.
- `GOVERNANCE_STACK` amendment log entry: "Portal Quality Pass v0.1 closed — 10 quality issues fixed across `/build/*` routes."
- `SESSION_LOG` atomic append.
- `CLAUDECODE_BRIEF.md` (this file at root, post-promotion) → `status: COMPLETE`.
- Manifest, mirror, drift checks: run as standard.

## §9 — Out-of-band notes for the executor

- The native flagged the three primary bugs (AC.1, AC.2, AC.3) directly during a Cowork conversation on 2026-04-27. The wider sweep (AC.4–AC.9) emerged from a portal audit during the same conversation. AC.10 is standard quality-gate hygiene.
- AC.5 may surface the largest scope creep — derivation of workstreams from source files is non-trivial. If the derivation logic for any one workstream takes more than 30 min of executor time, document the partial implementation in the file's docstring + add a row to `STALENESS_REGISTER.md` and proceed. Full derivation can be a v0.2 follow-up.
- AC.8's optional refresh button: include it. The marginal cost is small and the trust value is high.
- If during AC.1's data-flow verification the executor finds that `phase_b_plan` data has stale or wrong status values for B.0–B.5, the fix may require touching the serializer's phase-plan parsing logic. That's in scope (it's the same file as AC.5). Document the discovery in §9 of the close-checklist.

---

*End of CLAUDECODE_BRIEF_PORTAL_QUALITY_v0_1.md (DRAFT, 2026-04-27). Promote to project root as `CLAUDECODE_BRIEF.md` with status `AUTHORED` when ready to dispatch — after Exec_8 closes and native approves scope.*
