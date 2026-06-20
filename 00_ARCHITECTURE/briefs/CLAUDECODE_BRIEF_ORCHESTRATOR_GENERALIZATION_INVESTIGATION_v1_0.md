---
artifact: CLAUDECODE_BRIEF_ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md
canonical_id: ORCHESTRATOR_GENERALIZATION_INVESTIGATION_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE
delivery_model: INVESTIGATION ONLY — produce a findings doc + recommendation; change NO code, apply NO migrations
goal: >
  Determine how to make the product "click Build" orchestrator drive every layer's assets
  (L0 global + L1–L5 per-chart) from ONE frozen writer contract + registry metadata — so the
  orchestrator is written once and each future phase just onboards conforming writers. NOT a
  per-layer extension.
---

# Orchestrator Generalization — Investigation Brief v1.0

## §0 — The framing (read this first — it shapes every answer)

The native builds layer-by-layer: finalize a phase's briefs → code → confirmed assets, THEN align the
orchestrator to that phase. **That cadence is correct — keep it.** The refinement this investigation
serves: instead of *extending* the orchestrator per layer (accumulating L1/L2/L3… special cases), design
it so the **orchestrator contract is FROZEN once** and each phase merely makes its writers *conform* to
that contract + sets the right registry metadata. Goal end-state: by L5, the orchestrator code was
written once; every layer was just "conform + register." This is **onboarding to a fixed contract**, not
per-layer extension.

**The native's build model the contract must express (as METADATA, not orchestrator branches):**
- **L0 = global, permanent.** One copy, no chart_id. NOT rebuilt per client. BUT: a few per-asset health
  checks run; **if a check fails, ONLY that failing L0 asset regenerates.** (Verify-then-conditionally-rebuild.)
- **L1–L5 = per-chart.** Built fresh for every client profile, in dependency order.
So when a new client profile is created and Build is clicked, the orchestrator walks the registry and,
per asset, does the right thing FROM METADATA: global+health-checked → probe, skip-if-green, regen-if-failed;
per_chart → build for this chart_id. One loop. No "if layer == L1" branches.

## §1 — What already exists (confirmed 2026-06-10 — build on this, don't reinvent)

The orchestrator is REAL and already more general than "L0-only":
- Chain: `PlanModal → POST /api/cockpit/runs → jobInvoker → Cloud Run Job → pipeline/orchestrator/main.py
  → execute_run → run_asset` (per asset, dependency-ordered via `asset_registry.depends_on` closure; emits
  SSE; pause/resume/stop; updates `asset_throughput` + `build_run_assets`).
- **The writer contract is already generic:** `WriterBase.run(ctx: ContextSpec) -> WriterResult`.
  `ContextSpec` = {asset_id, build_id, db_conn, config (chart_id for per_chart), dry_run}. `WriterResult`
  = {rows_inserted, rows_updated, rows_skipped, duration_seconds, notes}. **This already expresses a
  per-chart writer** — it is NOT L0-specific.
- **`run_asset` already branches on `storage_type='service'`** and runs `_run_service_health_probe`
  (GREEN/degraded/down). So the health-check primitive for L0 EXISTS — but it currently only MARKS status;
  it does NOT auto-regenerate on failure (see §3.C — that's the one genuinely-new orchestrator behavior).
- **The gap:** `run_asset` resolves writers via `get_writer(asset_id)` from `writers/__init__.py`, populated
  only by `@register('bg_*')` WriterBase subclasses. The 9 GA writers (`ga_writers/`) use a different
  pattern (module functions `build_ga_*(...)`, their own `_idempotency.py` + `_telemetry.py`, per-ayanamsha
  loops) and are NOT registered → `get_writer('ga_dashas')` returns None → Build can't run them. L1 only
  built because `ga_writers/build_runner.py` was hand-invoked on the sidecar.

## §2 — The investigation questions

### §2.A — The conformance gap (the core)
Read `writers/__init__.py` (WriterBase, ContextSpec, WriterResult, @register, _auto_discover) and 2–3 GA
writers + `ga_writers/build_runner.py` + `_idempotency.py` + `_telemetry.py`. Produce a concrete diff: what
exactly must a GA writer do to satisfy `WriterBase.run(ctx) -> WriterResult`? (entry signature, where it
gets chart_id/build_id/db_conn, who owns the transaction — note ContextSpec says "caller-owned; writer
doesn't close or commit", does that conflict with how GA writers manage txns + savepoints?, how rows are
reported, how `_telemetry` reconciles with run_asset's own asset_throughput UPDATE — TWO build-state
writers today, must converge to one).

### §2.B — Does the FROZEN contract stretch to all of L1–L5? (the decisive question)
The contract was proven on small L0 global writers. Test it against the hardest L1 case and report
whether it needs a ONE-TIME generalization now (so it never changes again) or already suffices:
1. **Per-chart:** ContextSpec.config carries chart_id — confirm a per_chart writer has everything it needs.
2. **Heavy writers / runtime:** `ga_dashas` writes ~2.5–3M rows over ~40 min. Does run_asset's
   single-`run(ctx)`-call-per-asset model + the Cloud Run Job wall-clock + the SSE cadence accommodate a
   40-min single call? **Decide the design here** (native's open question): should a heavy asset run as
   ONE long orchestrator step (job stays alive, coarse progress), or should the contract support an asset
   declaring **sub-steps** (e.g. per-ayanamsha / per-dasha-system) so the orchestrator drives chunks with
   granular SSE + mid-asset resume on failure? Recommend, with the Cloud Run Job timeout as the constraint.
   If sub-steps are needed, that is the ONE generalization to bake into the frozen contract NOW.
3. **Idempotency:** GA writers already replace-not-accrete via `_idempotency.py`. Under the contract, who
   calls it — the writer (keep) or the orchestrator (centralize)? Recommend so L2–L5 inherit one pattern.
4. **Multi-ayanamsha:** GA writers loop 5 ayanamshas internally. Does that stay inside the writer, or does
   the contract express it? (Relates to sub-steps.)

### §2.C — The L0 verify-then-conditionally-regenerate behavior (the one new orchestrator primitive)
Today `_run_service_health_probe` marks GREEN/degraded/down but does NOT regenerate. The native's L0 model
needs: **global asset's check fails → regenerate ONLY that asset.** Investigate the cleanest way to add this
as GENERIC, metadata-driven logic (not L0-special): e.g. a registry field like `rebuild_on_probe_fail` +
the asset's own writer registered so the orchestrator can re-run it. Confirm L0 data assets (not just
services) can carry a health check too (the native said "a couple of checks at L0" — are these service
probes, or data-asset integrity checks like FORENSIC/row-count? design for both). Recommend the metadata
shape + the orchestrator addition. This should be the ONLY genuinely-new orchestrator code.

### §2.D — Registry metadata completeness for metadata-driven dispatch
The orchestrator must decide everything per-asset FROM the registry. Audit whether `asset_registry` carries
enough: `scope` (global/per_chart ✓), `storage_type` (service/postgres_table ✓), `depends_on` ✓, plus
what's MISSING for the model — a build-trigger/health-check declaration, `rebuild_on_probe_fail`, sub-step
declaration (if §2.B.2 needs it), and how a writer is located (today `get_writer_git_hash` hardcodes
`writers/{asset_id}.py` — breaks for ga_ writers elsewhere; propose how the registry or registry+convention
locates any writer). List the exact columns/metadata to add so dispatch is 100% metadata-driven.

### §2.E — Two options, but framed against the frozen-contract goal
- **Option A — converge (recommended-by-default unless evidence says otherwise):** make each GA writer a
  registered WriterBase subclass (thin adapter wrapping `build_ga_*`), conforming to run(ctx)→WriterResult.
  Orchestrator code stays ~fixed; L2–L5 writers register the same way from day one. The clean frozen-contract path.
- **Option B — adapter dispatch:** teach run_asset a fallback to invoke `ga_writers.build_runner` when no
  WriterBase is registered. Less writer refactor, but leaves TWO writer patterns + two telemetry paths
  permanently, and L2 must pick one — risks perpetuating the fork. Note what's lost.
Recommend A or B **explicitly**, with effort (files, risk), AND state which sets the cleaner foundation
for L2 Bodha to register into from day one (the native builds L2 next, into whatever this establishes).

### §2.F — Deployment reality checks
1. **Job name:** `jobInvoker.ts` says `marsys-build-pipeline-job`; `main.py` docstring + older memory say
   `brahma-build-pipeline-job`. Run `gcloud run jobs list` — confirm which exists, which is wired in
   deploy.yml + jobInvoker env, and reconcile.
2. **Image contents:** does the deployed Cloud Run Job's image even CONTAIN `ga_writers/`? If not, that's a
   prerequisite (the job can't run GA writers it doesn't ship). Verify.
3. **Watchdog/reaper:** confirm the existing watchdog (`/api/cockpit/watchdog`, build reaper) handles a
   40-min asset without reaping it as stuck.

## §3 — Deliverable

Write `00_ARCHITECTURE/ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md` containing:
1. The conformance diff (§2.A).
2. **The frozen-contract verdict (§2.B): does the contract already stretch to L0–L5, or what ONE-TIME
   generalization (sub-steps? heavy-writer model?) must be baked in now so it never changes again.**
3. The L0 verify-then-regenerate design (§2.C) — the one new orchestrator primitive.
4. The exact registry metadata to add (§2.D) for fully metadata-driven dispatch.
5. **A-vs-B recommendation (§2.E)** with effort + which sets the L2 foundation.
6. Deployment fixes (§2.F).
7. **The end-to-end test plan:** how to prove `POST /api/cockpit/runs` scope=layer/ganita for `482012f1`
   runs all 9 GA assets in dependency order, flips `asset_throughput` lit per asset VIA THE ORCHESTRATOR
   (not _telemetry), streams SSE, with no hand-invoking — AND a global-build test proving L0 assets
   health-check + regenerate-only-on-failure.
8. A short "L2-readiness" statement: with this in place, what an L2 Bodha writer must do to be
   orchestrator-native from day one (the conformance checklist L2 briefs will include).

**Make NO code changes, apply NO migrations. Read-only investigation. Rails: investigation only.**

---

*End. Goal: write the orchestrator ONCE (frozen contract + metadata-driven dispatch covering global/per_chart
+ health-check-regenerate + heavy writers), so every future layer onboards by conforming, not by extending.*
