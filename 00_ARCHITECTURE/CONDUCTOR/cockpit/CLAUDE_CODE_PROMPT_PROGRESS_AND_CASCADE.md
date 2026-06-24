---
artifact: CLAUDE_CODE_PROMPT_PROGRESS_AND_CASCADE.md
canonical_id: CLAUDE_CODE_PROMPT_PROGRESS_AND_CASCADE
version: 1.0
status: READY — implementation brief: real-time stage-based progress bar (Framer Motion) + universal DAG cascade-rebuild + retire direct runners. NO SEAL.
authored_by: Cowork 2026-06-22
native_decisions: "(1) Progress = STAGE-based (queued→running→substeps→committing→lit), Framer Motion UX. (2) Cascade = auto-cascade, staged-for-confirm preview, for ANY asset, permanently. (3) RETIRE the run_*_prod.py direct runners — all builds via orchestrator."
source_investigation: "subagent a9166f2d wiring map — both mechanisms mostly built; specific breaks identified."
---

# Implementation Brief — Real-Time Progress + Universal Cascade + Retire Direct Runners

> Paste §PROMPT to Claude Code in Antigravity. Establishes BOTH permanently (not one-off). **DO NOT SEAL.**
> This is platform infrastructure — it does NOT gate the L4 seal but should land before L5.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Implement three linked fixes the
native ratified. A read-only wiring investigation is done — work from the change-points below; both
mechanisms are MOSTLY ALREADY BUILT, the failures are specific. **DO NOT seal anything.** Establish these
as PERMANENT behaviors for every asset, not one-off fixes.

**Rails:** Frozen orchestrator contract (the orchestrator stays the sole build-state writer); anti-drift;
Gemini/DeepSeek only; localhost code-plane / prod data-plane; verify against the live cockpit. Use
`next dev --webpack` locally (Turbopack CPU bug). dd-MMM-yyyy dates via the central formatter.

### THE ROOT CAUSE (fix this first — it unblocks both mechanisms)
The 10 `platform/python-sidecar/run_*_prod.py` direct-runner scripts write rows + `conn.commit()` but touch
ZERO of `asset_throughput` / `build_run_assets` / `emit_event`. So any build via them is INVISIBLE to the
cockpit (no progress) AND skips the orchestrator's topo-walk (no cascade). **Native decision: RETIRE them —
all builds go through the orchestrator.**

### PART 0 — Retire the direct runners (the keystone)
1. **Verify the orchestrator can do everything the scripts were used for FIRST** (or retiring them breaks
   heavy/one-off builds):
   - Single-asset build: `plan.ts` already supports `scope='asset'` + `action='rebuild'` (includes
     downstream). Confirm `runs/route.ts` → `invokeRunJob` dispatches a single-asset run end-to-end.
   - **HEAVY builds (the real risk):** the `ka_sangam` lifetime tier runs 1–3 hours. Check the Cloud Run
     Job `brahma-build-pipeline-job` **task timeout** (`gcloud run jobs describe brahma-build-pipeline-job
     --region=asia-south1 --format='value(spec.template.spec.template.spec.timeoutSeconds)'`). If it's
     shorter than the heaviest asset's wall-clock, RAISE it (Cloud Run Jobs max 24h) — this is WHY people
     fell back to unbounded local scripts. Fix the friction or the retirement won't stick.
   - Confirm a CLI/orchestrator entrypoint exists for an operator to kick a single-asset build without the
     UI (for ops parity with the old scripts).
2. **Then delete the 10 `run_*_prod.py`** (git rm). Grep for any caller/cron/doc referencing them and
   repoint to the orchestrator path. If any is genuinely still needed as an emergency tool, instrument it
   (write `asset_throughput` state + `build_run_assets` + `emit_event` mirroring `asset_runner.py`) rather
   than leave it blind — but prefer deletion.
3. Record in CF.L3.8 / the orchestrator-convergence doc that direct runners are RETIRED; the click-Build /
   `runs` route is the ONLY build path.

### PART 1 — Stage-based progress bar (queued → running → substeps → committing → lit) + Framer Motion
The orchestrator already EMITS the signals (`asset_runner.py` emits `asset.state_change` building→lit,
`asset.substep {index,total,rows_written,substep_label}`, `asset.progress`); `sse/route.ts` already streams
them; `DataAssetsView.tsx` already subscribes via `useCockpitSSE` and builds `substepOverlay`/`sseOverlay`.
The BREAKS are all on the render side — fix these:
1. **Define the stage model.** Map orchestrator states/events → 5 stages: `queued` (in plan, not started),
   `running` (state=building, before first substep), `substeps` (substep events arriving; show `i/total`),
   `committing` (last substep done, state not yet lit), `lit` (state=lit). Drive the bar fill by stage
   (e.g. 5%/25%/25→90% across substeps/95%/100%), NOT by `actual_rows/target_floor`.
2. **Feed live SSE into the bar.** `AssetRow.tsx:~184` currently passes only polled `actualRows` to
   `AssetProgressBar`. Pass the live stage + `substep {index,total}` from `substepOverlay`/`sseOverlay` so
   the bar advances on events, not just on stats re-poll.
3. **Rewrite `AssetProgressBar.tsx` fill logic** (`~lines 26-28`): fill from the stage model + substep
   `index/total` while building; show the rows ratio only in the lit/complete state. Kill the
   "actualRows/target_floor → sits at ~0% then snaps to 100" behavior.
4. **Framer Motion UX:** animate the bar width with a spring (`motion.div` `animate={{width}}` +
   `transition={{type:'spring', stiffness, damping}}`), a subtle pulse on the active-stage segment, and a
   smooth stage-label cross-fade. Confirm framer-motion is already a dep (the rail elevation used it). Keep
   it tasteful — spring fill + active-stage shimmer + label fade; respect prefers-reduced-motion.
5. **Stats payload parity (fallback path):** add `rows_written` to the SELECT + the `AssetStats` interface
   in `stats/route.ts` so the polled fallback also reflects writer progress when SSE drops.
6. **Substep denominator (optional polish):** if feasible, have `plan_substeps` expose an expected-rows
   estimate so `asset.substep` can carry a true %; otherwise the `index/total` stage fill is sufficient
   (you chose stage-based, so this is polish not required).
**Acceptance:** trigger a real build (e.g. ph_muhurta) via the orchestrator and WATCH the bar advance
through the 5 stages live, with spring animation, no manual refresh — on localhost AND prod.

### PART 2 — Universal DAG cascade-rebuild with confirm-preview
The cascade ALREADY EXISTS: `plan.ts` (`transitiveDownstream`/`computeDownstreamClosure`/`topoSort`) +
`asset_runner.py:26-41` (recursive-CTE downstream closure). **`plan.ts:141-149`: rebuild asset X already
queues X + all transitive dependents in topo order.** Close the narrow gaps so it's universal + safe:
1. **Rebuild-cascade confirm preview (parity with clear).** Today single-asset rebuild's `PlanModal` shows
   the resolved plan but doesn't reuse the rich `CascadePreviewModal`/`ClearConfirmModal` "+N downstream
   will rebuild" preview. Wire a confirm-preview before any rebuild dispatch that shows the transitive
   dependents (data is already in `resolveBuildPlan`'s output `plan` + `includes_upstream_count`). Staged-
   for-confirm, one-click proceed (the native's chosen behavior).
2. **Clear/delete should cascade-rebuild at ANY scope, not just global.** `clear/execute/route.ts` marks
   downstream `stale` but only GLOBAL clear chains a rebuild (`CockpitShell.tsx:88-99`). Generalize: after
   an asset- or layer-scoped clear/delete, offer "and rebuild dependents" → POST `runs` with
   `action='cascade'` (or `rebuild`) for the affected + downstream set in topo order, behind the same
   confirm-preview. (Deleting raw data with no rebuild is what leaves the DAG inconsistent — the principle
   the native wants enforced.)
3. **Make it a documented standing principle, not ad-hoc.** Add to the cockpit/orchestrator docs: "any
   delete or rebuild of an asset auto-computes its transitive downstream dependents from the DAG and stages
   them for cascade-rebuild in dependency order, with a confirm preview." This is the permanent behavior.
**Acceptance:** rebuilding `ka_vighnakara` (or any asset) shows a preview listing ALL transitive dependents
(incl. ph_pratikara) and, on confirm, rebuilds them in dependency order via the orchestrator — with the
PART 1 progress bar advancing per asset. Deleting an asset offers the same cascade.

### PART 3 — Verify end-to-end (the two original symptoms gone)
1. Rebuild `ka_sangam` (the convergence fix) THROUGH THE ORCHESTRATOR (not a script) → the bar progresses
   live through stages → on completion, the cascade preview offers to rebuild `kala_obstruction` →
   `ph_pratikara` (its real DAG dependents) → confirm → they rebuild in order, bars advancing.
2. Confirm `asset_throughput` reflects true state/rows for every asset built this way (no more
   rows_written=0 caused by direct-runner bypass).
3. CI green (no net-new failures); commit + push (auto-deploys); verify on the live prod cockpit.

### REPORT — NO SEAL
Report: Part 0 (timeout check result + raised value if needed; scripts deleted + any callers repointed);
Part 1 (the stage model + the bar advancing live, with a screenshot/GIF if possible); Part 2 (the cascade
preview working for rebuild + delete at asset/layer scope); Part 3 (the ka_sangam→obstruction→pratikara
cascade running through the orchestrator with live bars). Note anything still open. **DO NOT seal.** STOP.

---
*End. Retire the direct runners (the keystone — unblocks both), wire the stage-based progress bar with
Framer Motion to the SSE events the orchestrator already emits, and close the narrow gaps so DAG cascade-
rebuild (already mostly built) is universal + confirm-previewed for any asset. Verify on the live cockpit.
Platform infra — does not gate L4 seal, but land before L5. NO SEAL.*
