---
artifact: ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
canonical_id: ORCHESTRATOR_CONVERGENCE_CLOSE
version: 1.1
status: CURRENT
authored_by: Claude Code (Antigravity IDE) 2026-06-12
seals: CLAUDECODE_BRIEF_ORCHESTRATOR_CONVERGENCE_v1_0.md
design_source: ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md
goal: >
  Sealing record for the Orchestrator Convergence arc: the "click Build" orchestrator now
  drives L1 Gaṇita assets end-to-end via a FROZEN, metadata-driven, sub-step-capable writer
  contract. Records the frozen contract, the per-phase deliverables, and the L2-readiness
  conformance checklist every future-layer writer brief embeds.
changelog: >
  v1.1 (2026-07-29, SATYA-DĪPA): added §7, the freeze's first authorized, dated exception —
  the no-op-completion promotion predicate in asset_runner.py (`_run_data_writer`) now verifies
  substep-plan completeness (has_substeps=true writers only) before reclassifying a 0-rows
  'dormant' result to 'lit'. See SATYA_DIPA_REPORT_v1_0.md for full detail. The freeze itself
  (§2) is otherwise untouched — no writer contract, WriterBase signature, or control-flow change.
---

# Orchestrator Convergence — Close v1.0

## §1 — Verdict

The orchestrator was **built once** and is now **FROZEN**. Every future layer (L2 Bodha →
L5) onboards by (a) writing a `@register('<asset_id>')` `WriterBase` subclass that conforms
to the frozen contract and (b) declaring registry metadata — **never** by changing
orchestrator code. The 9 L1 Gaṇita writers are the first cohort to conform; they are also
now **per-chart general** (any chart, not just the native).

## §2 — The FROZEN contract (the architectural seal)

`pipeline/orchestrator/writers/__init__.py` — final shape, do not extend:

- `ContextSpec{ asset_id, build_id, db_conn (caller-owned; writer never commits/closes),
  config{chart_id, birth_params}, dry_run }`
- `WriterResult{ asset_id, rows_inserted, rows_updated, rows_skipped, duration_seconds, notes }`
- `SubStep{ key, label }` — one savepoint-isolated, heartbeated unit; `key` is the writer's
  idempotency scope.
- `WriterBase`:
  - **light writer** → implements `run(ctx) -> WriterResult` (whole asset in one unit);
  - **heavy writer** → overrides `plan_substeps(ctx) -> list[SubStep]` + `run_substep(ctx, step)
    -> WriterResult`; gets a working `run()` for free (drives its own sub-steps for CLI);
  - `has_substeps` advisory flag mirrors `asset_registry.has_substeps`.

If a future layer appears to need a contract change, **STOP and raise with the native** — the
freeze was a deliberate architectural decision, not a routine edit.

## §3 — Per-phase deliverables (all merged to main)

| Phase | PR | Merge | What |
|---|---|---|---|
| 1 — Deployment foundation | #254 | `38f842ff` | job-name fix (`brahma-build-pipeline-job` + `BUILD_JOB_NAME` env); `ga_writers/` added to `Dockerfile.pipeline`; `brahma-pipeline` image brought under CI (`deploy-pipeline-job` builds+pushes+re-points + `import ga_writers` smoke); reaper thresholds documented. |
| 2 — Freeze contract + sub-steps | #255 | `65ad201d` | `SubStep` + `plan_substeps`/`run_substep` added and the contract FROZEN; `_drive_substeps` drives each sub-step in its own `SAVEPOINT` + `last_built_at` heartbeat + commit + `asset.substep` SSE; mid-asset resume via `completed_keys`. |
| 3 — Converge 9 GA writers | #256 | `3129f3e3` | transaction-ownership inverted (writers run on `ctx.db_conn`, never commit, no `_telemetry` on the conformed path); 9 `@register` adapters (`get_writer` resolves all 9); heavy `ga_dashas` (36 sub-steps) + `ga_vargas` (5); `get_writer_git_hash` generalized via `source_paths`. |
| 3B — Per-chart generalization (native-added) | #257 | `38ef773e` | `birth_params.py` provider (native→`NATIVE_BIRTH`, non-native fetched from `public.charts` with tz from IANA `timezone_id`, missing-data→loud halt); birth threaded into `ga_dashas`/`ga_tajaka`; every native-anchored FORENSIC assertion (incl. 3 buried `ga_dashas` asserts) guarded to fire only for the native. Non-native builds no longer halt; native regression guard intact. |
| 4 — rebuild-on-probe-fail + DAG | #258 | `20ed5a01` | the one new primitive — metadata-driven verify-then-conditionally-regenerate (`_probe_asset`/`_mark_probe_green`/`_run_data_writer`); migration 223 adds `rebuild_on_probe_fail` / `integrity_check_sql` / `has_substeps` + backfills the real GA `depends_on` DAG + `estimated_seconds`; seed parity. |

Unit coverage: full `platform/python-sidecar` suite **1563 passed, 0 regressions** at Phase 4.

## §4 — Phase 5 — End-to-end self-reliance test (OPERATOR runbook)

The live E2E proof requires super-admin web auth + a fresh client + the localhost cockpit —
operator-executed. Preconditions (Phases 1–4) are all deployed.

**Test 1 — Per-chart L1 on a fresh NON-native chart** (never `482012f1`, never `362f9f17`):
1. Create a fresh client profile (real birth data incl. a valid IANA `timezone_id`) → `chart_id = C`.
   Confirm `asset_throughput` has no `lit` GA rows for `C`.
2. `POST /api/cockpit/runs { chart_id: C, scope: 'layer', scope_target: 'ganita', action: 'build' }`
   → expect `201 { run_id, plan, asset_count }`. **Assert `plan` is dependency-ordered**
   (`ga_positions` before `ga_strength`/`ga_vargas`/`ga_dashas`/...; `ga_structural` after them;
   `ga_sade_sati` after `ga_structural`) — now real via the migration-223 DAG.
3. Assert the Cloud Run Job started: `gcloud run jobs executions list --job brahma-build-pipeline-job`.
4. Subscribe to `GET /api/cockpit/sse`: per-asset `building→lit`; for `ga_dashas`, ≥35
   `asset.substep` events with `last_built_at` advancing (heartbeat proof).
5. Single-writer proof: `built_against_writer_hash` + `built_against_upstream_hash` non-NULL on
   `(C, ga_*)` rows (only the orchestrator sets these; `_telemetry` never did). Grep job logs for
   `[telemetry]` — must be ABSENT on the conformed path.
6. On completion: all GA `(C, ga_*)` rows `lit`; `build_runs.state='completed'`; no FORENSIC
   halt (the chart is non-native → native anchors not asserted).
7. Idempotency/resume: re-run `action='rebuild'` scope=asset `ga_dashas`; row count identical;
   kill at sub-step ~20 and re-run → resumes without doubling.
8. Reaper non-interference: confirm the watchdog ran ≥1 cycle during `ga_dashas` and did NOT flip
   the run `failed` or the asset `error`.

**Test 2 — Global L0 verify-then-regenerate** (once an L0 asset opts in):
1. Set `rebuild_on_probe_fail=true` + a registered writer + a check (`health_probe` or
   `integrity_check_sql`) on an L0 asset.
2. Green path: healthy → `POST /api/cockpit/runs scope=global` → probe GREEN → `lit`,
   `rows_written=0`, writer NOT run (`asset.probe status=green action=skipped`).
3. Failure path: break the asset → re-run → `asset.probe failed→regenerating` → writer runs →
   re-probe GREEN → `lit`; assert **no other L0 asset rebuilt**.
4. No-policy path: `rebuild_on_probe_fail=false` + failing probe → `error`, NOT regenerated.

## §5 — L2-readiness conformance checklist (embed verbatim in every L2–L5 writer brief)

A writer is orchestrator-native iff **all** hold:

- [ ] **Is a class**, `@register('<asset_id>')`, subclassing `WriterBase`; `asset_id` matches the registry.
- [ ] **Discoverable** — imported by `_auto_discover()` (lives under `pipeline/orchestrator/writers/`
      or is a thin adapter that does) **and ships in the `brahma-pipeline` job image**.
- [ ] **`run(ctx)`** (light) **or** `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy: > ~10 min
      or > a few hundred k rows).
- [ ] **Connection:** uses `ctx.db_conn` exclusively; **never** opens its own, **never**
      `commit()/rollback()/close()`.
- [ ] **chart_id / birth:** reads `ctx.config['chart_id']` and `ctx.config['birth_params']`
      (None → its verified default); `ctx.build_id`. **No hard-coded native default in the build path.**
- [ ] **Idempotency:** its own natural-key-scoped `replace_prior_*` on `ctx.db_conn` immediately
      before INSERT, scoped to the sub-step key; any sub-step safe to re-run.
- [ ] **Telemetry:** writes **nothing** to `asset_throughput`; returns counts in `WriterResult`.
- [ ] **FORENSIC:** any native-anchored assertion is guarded `if chart_id == CANONICAL_CHART_ID`;
      structural invariants stay unconditional.
- [ ] **dry_run:** honors `ctx.dry_run`.
- [ ] **Registry row** with correct `scope`, `asset_type`, `layer`, **populated `depends_on`**
      (real edges, not `[]`), `count_sql` + `target_floor`, `sort_order`; `has_substeps=true` if heavy;
      `rebuild_on_probe_fail=true` + a `health_probe`/`integrity_check_sql` if self-healing.
- [ ] **No orchestrator change required** — if onboarding needs a new `if` in `run_asset`/`runner.py`,
      the contract was violated; fix the writer, not the orchestrator.

## §6 — Residuals (non-blocking)

- **R4-1:** No GA asset sets `rebuild_on_probe_fail=true` yet — the primitive is wired + unit-proven,
  ready for the first L0 opt-in (Phase 5 Test 2 runs then).
- **R3B-1:** `ga_tajaka` stores a cosmetic `+05:30` tz suffix on the annual-instant ISO (display
  metadata only; the compute uses the bare instant) — not correctness-affecting.
- **R5-1:** Phase 5 live E2E is operator-executed (super-admin web auth + fresh client); the runbook
  above is authoritative.
- **R6-1:** Manifest registration of the 3 arc docs (`ORCHESTRATOR_GENERALIZATION_INVESTIGATION`,
  `ORCHESTRATOR_CONVERGENCE_BRIEF`, `ORCHESTRATOR_CONVERGENCE_CLOSE`) in `CAPABILITY_MANIFEST.json`
  is **booked for the next `manifest:build` / quarterly governance pass** (§H). Hand-editing the
  fingerprinted manifest now is avoided (gate risk); regenerating now would pull in ~12 unrelated
  untracked session briefs in the working tree. `drift_detector` + `schema_validator` were run at
  close — both at the project's established exit-3 known-residual baseline, no NEW arc-induced
  hard failure. This booking matches the drift-detector's existing "registration/fingerprint
  pending → quarterly pass" pattern.

## §7 — Authorized freeze exceptions (dated log)

The freeze (§2) is absolute except where explicitly, narrowly authorized and logged here. Any
orchestrator change NOT logged in this section is a freeze violation, full stop.

### 7.1 — SATYA-DĪPA no-op-completion completeness check (2026-07-29)

**Authorization:** `SATYA_DIPA_BRIEF_v1_0.md` §9.1, one narrow freeze exception: "the promotion
predicate in `asset_runner.py:596–630` and nothing else in the orchestrator."

**Defect:** the D-1.6 no-op-completion rescue (`_run_data_writer`, added to fix run 71b260c7 —
see §6 residual history and `tests/test_d16_state_write_defect.py`) reclassified a 0-rows-this-run
'dormant' result to 'lit' whenever the asset's target table had ANY rows present, without checking
whether the writer's substep plan had actually finished. A resumable writer legitimately reporting
0 rows because everything was already committed (the true D-1.6 shape) and a resumable writer
genuinely mid-build with substeps still remaining were indistinguishable to the rescue — both have
"rows present, 0 rows this run." The latter is the same "unearned lit" defect class as D-1.6 itself,
capable of silently unblocking downstream dependents on an incomplete build.

**Fix (asset_runner.py:596–630 only):** for `asset_registry.has_substeps = true` writers, before
promoting, the rescue now re-invokes the writer's own `plan_substeps(ctx)` (SAVEPOINT-isolated,
same pattern as `_data_rows_present`) and requires it to report zero remaining substeps. Writers
with `has_substeps` false/NULL (light writers, no real substep plan) are unaffected — the check is
skipped entirely, preserving prior behavior exactly (`SATYA_DIPA_BRIEF_v1_0.md` §4.1: "An asset
with no substep plan defined behaves as before"). When the plan is genuinely incomplete, the asset
is marked **`incomplete`** (migration 474: new value in `asset_throughput_state_check`) — not
`lit` (would falsely satisfy `runner.py`'s and `staleness.py`'s `state IN ('lit','service_ok')`
dependency-satisfied allowlists) and not `dormant` (data is not absent). A distinct event,
`asset.noop_completion_rejected`, is emitted alongside the existing `asset.noop_completion`.

**Contract impact:** none. `WriterBase`, `plan_substeps`/`run_substep`, `ctx`, `WriterResult`, and
`_drive_substeps`'s signature are all unchanged. `plan_substeps(ctx)` is a read-only planning call
by contract; re-invoking it once, immediately after the same round's `_drive_substeps` call
completed (same fingerprint, no intervening state change), is safe and does not double-execute any
`run_substep`.

**Regression proof:** `tests/test_d16_state_write_defect.py` — `test_satyadipa_d16_preserved_through_completeness_check`
(D-1.6's exact shape, run THROUGH the new check, still promotes to 'lit') and
`test_satyadipa_partial_substep_plan_with_rows_present_not_lit` (new: genuinely-incomplete plan
with data present → 'incomplete', not 'lit'; proven to fail against pre-fix code, pass against
fixed code) and `test_satyadipa_light_writer_no_substep_plan_behaves_as_before` (has_substeps=false
→ unchanged). Full detail: `SATYA_DIPA_REPORT_v1_0.md`.
