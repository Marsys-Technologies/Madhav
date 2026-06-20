---
artifact: CLAUDECODE_BRIEF_ORCHESTRATOR_CONVERGENCE_v1_0.md
canonical_id: ORCHESTRATOR_CONVERGENCE_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous, but PHASE-GATED — see §0)
delivery_model: ONE arc, deployment-first, 5 internal phases, each its own PR; gated
goal: >
  Make the product "click Build" orchestrator drive L1 GA assets end-to-end (and become the FROZEN,
  metadata-driven foundation L2–L5 onboard to). Converge the GA writers into the orchestrator's
  WriterBase contract; add exactly ONE contract generalization (sub-steps); fix 3 deployment blockers;
  add the generic rebuild-on-probe-fail primitive. Build is self-reliant for L1 before any L2 work.
design_source: 00_ARCHITECTURE/ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md (the investigation — READ FIRST, it is authoritative for every design decision here)
decisions_locked: Option A (converge); freeze contract + sub-steps only; CI/IaC for the job image; finish before L2.
---

# Orchestrator Convergence — Execution Brief v1.0

## §0 — How to run this (phase-gated, deployment-first)

Read `ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md` IN FULL first — it is the authoritative design;
this brief sequences it. Five phases, each a separate PR, **in this exact order** (deployment-first, because
nothing can run via the job until the image contains the writers). A phase opens only after the prior is
merged + verified. Halt-and-report on any surprise. Read state from CURRENT_STATE + git (main `e8488ad4`),
not §F.

Governing principle: **build the orchestrator ONCE.** After this arc the orchestrator contract is FROZEN;
every future layer (L2–L5) onboards by conforming + registry metadata, never by changing orchestrator code.

## §1 — PHASE 1 — Deployment foundation (FIRST — fixes the 3 blockers)

Per investigation §2.F. Nothing downstream can run via the Cloud Run Job until these are fixed.

1. **Job name.** `jobInvoker.ts` defaults to `marsys-build-pipeline-job` which DOES NOT EXIST; the real job
   is `brahma-build-pipeline-job`. Fix the default + add `BUILD_JOB_NAME` to deploy.yml env (and confirm
   the running web service env). Verify with `gcloud run jobs list`.
2. **`ga_writers/` not in the job image (the big one).** `Dockerfile.pipeline` COPYs only `pipeline/`,
   `brahmagyan/`, `pyjhora_adapter/` — `python -m ga_writers.*` would `ModuleNotFoundError` in the job.
   **Add `ga_writers/` (and any shared deps it imports) to the image COPY.** Per the locked decision, also
   **bring the image build under CI/IaC** — the image is currently built out-of-band by hand (drift risk of
   exactly the class that bit this project repeatedly). Add a CI/deploy.yml job that builds + pushes
   `amjis/brahma-pipeline` from main on the relevant paths, so the job image can never silently diverge from
   the code again. Verify the new image contains `ga_writers/` (`docker run … python -c "import ga_writers"`).
3. **Watchdog heartbeat.** The watchdog reaps at 30-min orphan + 15-min stuck (no heartbeat) — it would kill
   a 40-min asset. Don't loosen the reaper (it protects against genuine hangs); instead this is solved by
   Phase 3's sub-step heartbeat (each sub-step updates `last_built_at`, keeping the asset visibly alive under
   both reapers). For Phase 1, just CONFIRM the reaper thresholds + that a per-sub-step heartbeat will satisfy
   them; note the exact thresholds the heartbeat must beat.

**Phase 1 AC [verify-against: prod]:** correct job name wired; job image rebuilt via CI/IaC and CONTAINS
`ga_writers/`; reaper thresholds documented. PR → merge-verify.

## §2 — PHASE 2 — Freeze the contract + add sub-steps (the ONE generalization)

Per investigation §2.B. The contract (`WriterBase.run(ctx: ContextSpec) -> WriterResult`) already handles
global + per-chart light writers. Add EXACTLY ONE thing — sub-steps — then freeze.

- Extend the contract so a writer MAY declare sub-steps: `plan_substeps(ctx) -> list[SubStepSpec]` and
  `run_substep(ctx, substep) -> WriterResult`. A writer with no sub-steps keeps the plain `run(ctx)` path
  (L0 + light L1 unchanged). The orchestrator, for an asset with `has_substeps`, calls `plan_substeps` then
  drives each `run_substep` as its own gated unit with **a `last_built_at` heartbeat per sub-step** (satisfies
  the reaper, gives granular SSE, enables mid-asset resume — a re-run skips completed sub-steps via the
  writer's idempotency).
- Sub-step granularity for the heavy writers = the **35 `(system × ayanamsha)` chunks that already exist as
  `build_system` calls** in ga_dashas (and the analogous per-ayanamsha chunks for ga_vargas). Do NOT invent
  new chunking — expose the structure already there.
- **Idempotency stays writer-owned** (on `ctx.db_conn`, via the existing `_idempotency.py` helpers), scoped
  per sub-step so a resumed run replaces only its chunk. Multi-ayanamsha stays internal except as the
  heavy-writer sub-step axis.
- **FREEZE.** Document in the contract module that this is the final contract shape; future layers conform,
  they do not extend. This is the architectural seal.

**Phase 2 AC:** contract supports optional sub-steps + per-sub-step heartbeat; light writers unaffected;
contract documented as frozen; unit tests for the sub-step driver (plan→run-each→resume-skips-completed). PR → merge-verify.

## §3 — PHASE 3 — Converge the 9 GA writers (the delicate part: transaction inversion)

Per investigation §2.A. This is the load-bearing change — do it carefully; it touches the idempotency +
atomicity guarantees.

- **Invert connection + transaction ownership.** Today GA writers open their OWN connection (`with _conn()`)
  and commit internally (`_upsert_rows → conn.commit()`), which defeats the orchestrator's
  `SAVEPOINT writer_exec` / `ROLLBACK TO SAVEPOINT`. Refactor every GA writer to **use `ctx.db_conn`** (the
  orchestrator-owned connection) and **NOT commit** (the orchestrator owns the transaction + savepoint
  lifecycle, per ContextSpec's "caller-owned; writer doesn't close or commit"). This is the heart of
  conformance — verify a failed sub-step `ROLLBACK TO SAVEPOINT` cleanly undoes that sub-step's writes.
- **One build-state writer.** Delete the `_telemetry.py` asset_throughput writes from the conformed path —
  `run_asset` is the sole build-state writer now (asset_runner.py:266-276). No double-write.
- **Register each writer.** Wrap each `build_ga_*` as a `WriterBase` subclass with `@register('ga_...')`
  (heavy ones implement `plan_substeps`/`run_substep`; light ones implement `run`). Locate them so
  `discover_all` imports them and `get_writer('ga_dashas')` resolves.
- **Fix `get_writer_git_hash`** — it hardcodes `writers/{asset_id}.py`; generalize so it locates a writer
  wherever it lives (ga_writers/) — via the registry or a path-resolution convention.
- Keep `ga_writers/build_runner.py` working as a thin CLI shim over the conformed writers for now (so manual
  invocation still works), but the canonical path is the orchestrator.

**Phase 3 AC [verify-against: prod, on a NON-native test chart first]:** `get_writer` resolves all 9 GA
assets; a writer runs on `ctx.db_conn` with no internal commit; a forced sub-step failure rolls back that
sub-step only (savepoint proven); only `run_asset` writes asset_throughput; idempotency double-run still
yields one set. PR → merge-verify.

## §4 — PHASE 4 — rebuild-on-probe-fail primitive + depends_on backfill

Per investigation §2.C + §2.D. The ONE new orchestrator behavior + the metadata to make dispatch fully
registry-driven.

- **Generic `rebuild_on_probe_fail`.** Add the registry column(s) (`rebuild_on_probe_fail bool`,
  `integrity_check_sql`/`probe_type`). Extend the orchestrator's check path: probe/integrity-check →
  GREEN: skip; FAIL: regenerate ONLY that asset → re-probe. Design for BOTH service probes (L0 services) AND
  data-asset integrity checks (L0 data assets — e.g. FORENSIC/row-count). This is the native's L0
  "verify-then-conditionally-regenerate" model, generic + metadata-driven (no L0-special branch).
- **Backfill `depends_on`.** GA `depends_on` is all `[]` today — order is correct only by `sort_order` luck.
  Set the real edges (per the L1 DAG: GA8 structural depends on GA3–GA7; GA9 on GA3/4/6/7/8; etc.) so the
  orchestrator's dependency-closure runs them in the correct order. Migration + seed patch.
- Add `has_substeps` hint + any other metadata the investigation §2.D listed.

**Phase 4 AC [verify-against: prod]:** rebuild_on_probe_fail works for a deliberately-failed L0 check
(regenerates only that asset, re-probes green); GA depends_on reflects the real DAG; dispatch is 100%
metadata-driven. PR → merge-verify.

## §5 — PHASE 5 — End-to-end self-reliance test (the proof)

Per investigation §3.7. Prove the Build button drives L1 with NO hand-invocation.

1. **Per-chart L1 convergence** (on a fresh NON-native test chart, so we don't disturb 482012f1):
   `POST /api/cockpit/runs` scope=layer/ganita → the Cloud Run Job runs all 9 GA assets **in dependency
   order**, each `asset_throughput` flips lit **via the orchestrator** (not _telemetry), SSE streams
   per-asset + per-sub-step progress, heavy assets heartbeat and are NOT reaped. Confirm final row counts
   match a known-good build.
2. **Global L0 verify-then-regenerate:** trigger a global build; confirm green L0 assets skip, and a
   deliberately-broken L0 asset regenerates only itself and re-probes green.
3. Confirm the cockpit (localhost) reflects the whole thing live: bars fill, dots lit, via the orchestrator path.

**Phase 5 AC:** both tests pass; Build is self-reliant for L1; no hand-invoked build_runner needed.

## §6 — Close + L2 readiness

- Update governance: register `ORCHESTRATOR_GENERALIZATION_INVESTIGATION` + this brief in
  `CAPABILITY_MANIFEST.json`, run drift/schema validators (the governance follow-up the investigation flagged).
- Seal: a short `ORCHESTRATOR_CONVERGENCE_CLOSE.md` recording the frozen contract + the L2-readiness
  conformance checklist (investigation §3.8) that every L2 Bodha brief will embed, so L2 writers are
  orchestrator-native from day one.

## §7 — Rails

Phase-gated (don't open a phase before the prior merges + verifies); deployment-first; surgical migrations
only (no deploy.yml-auto / bulk runner for DB migrations); test transaction-inversion on a non-native chart
before touching 482012f1; only real chart ids, never `362f9f17`; merge-verify every PR
(`gh pr view N --json mergeCommit,state`); halt-and-report on transaction-rollback failure, reaper conflict,
image-still-missing-ga_writers, or any ambiguity. The contract is FROZEN at Phase 2 — if a later phase seems
to need a contract change, STOP and report (it means the freeze was wrong, a native decision).

---

*End. Converge GA writers into a frozen, metadata-driven, sub-step-capable orchestrator; fix the deployment
foundation with CI/IaC; add generic rebuild-on-probe-fail. Build becomes self-reliant for L1 — the foundation
L2–L5 onboard to by conforming, never by extending.*
