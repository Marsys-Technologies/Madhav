---
artifact: ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md
canonical_id: ORCHESTRATOR_GENERALIZATION_INVESTIGATION
version: 1.0
status: CURRENT
authored_by: Claude Code (Antigravity IDE) 2026-06-12
authored_for: native (Abhisek Mohanty)
delivery_model: INVESTIGATION ONLY — findings + recommendation. No code changed, no migrations applied, no prod touched.
investigates: CLAUDECODE_BRIEF_ORCHESTRATOR_GENERALIZATION_INVESTIGATION_v1_0.md
read_state_from: CURRENT_STATE_v1_0.md (v5.72) + git main HEAD e8488ad4
goal: >
  Determine the ONE frozen writer-contract + registry-metadata shape that lets the "click Build"
  orchestrator drive every layer's assets (L0 global + L1–L5 per-chart) from a single loop, so each
  future phase onboards conforming writers rather than extending the orchestrator.
---

# Orchestrator Generalization — Investigation Findings v1.0

## §0 — Executive summary (the verdict in five sentences)

1. **The contract is 90% there and should be FROZEN now with exactly ONE addition: sub-steps.** `WriterBase.run(ctx: ContextSpec) -> WriterResult` already expresses global *and* per-chart writers; the only thing it cannot survive is a 40-minute single call (`ga_dashas`), and the fix — letting a heavy asset declare sub-steps the orchestrator drives — is the one generalization to bake in permanently.
2. **The GA writers do not conform on three load-bearing axes:** they open their **own** DB connection and **commit internally** (defeating the orchestrator's savepoint), they write `asset_throughput` **themselves** via `_telemetry` (a second build-state writer that must be deleted), and they are **not registered** in the `WriterBase` registry (so `get_writer('ga_dashas')` returns `None` and Build marks them `error`).
3. **Recommend Option A (converge to registered `WriterBase` subclasses), decisively.** Option B (teach `run_asset` a fallback into `ga_writers.build_runner`) permanently forks the writer pattern, the telemetry path, *and* the transaction model — and forces L2 Bodha to inherit the fork on day one.
4. **The only genuinely-new orchestrator code is the L0 verify-then-conditionally-regenerate primitive** — a generic, metadata-driven `rebuild_on_probe_fail` path that works for both service probes and data-asset integrity checks. Everything else is conformance + metadata.
5. **Three deployment facts block a green Build today:** the invoker defaults to a job name that does not exist (`marsys-build-pipeline-job` vs the real `brahma-build-pipeline-job`); the deployed job image (`amjis/brahma-pipeline`, built out-of-band) **does not contain `ga_writers/`**; and the watchdog would reap a 40-minute asset. All three must be fixed regardless of A-vs-B.

---

## §1 — What exists (confirmed against main HEAD e8488ad4)

The chain, end to end (all confirmed by reading source, not memory):

```
PlanModal
  └─ POST /api/cockpit/runs        platform/src/app/api/cockpit/runs/route.ts
        ├─ requireSuperAdmin()
        ├─ 409 gate: block if build_runs already (planned|running|paused) for chart   (route.ts:32-41)
        ├─ resolveBuildPlan({scope, scope_target, action, registry, throughput})       lib/build/plan.ts:114
        │     • assetsInScope: global=all | layer=filter(layer==target) | asset=[target]  (plan.ts:57-66)
        │     • action filter: build=dormant-only | rebuild=scope (or target+downstream) | update | cascade
        │     • topoSort(candidates) by depends_on  → DEPENDENCY-ORDERED plan            (plan.ts:32-55,157)
        ├─ INSERT build_runs (state='planned', plan=jsonb[])                            (route.ts:63-68)
        ├─ INSERT build_run_assets (state='queued', position=i)                         (route.ts:72-80)
        └─ invokeRunJob(runId)  → Cloud Run Job (non-blocking; failure non-fatal)       (route.ts:84)
              └─ jobInvoker.ts → job `${BUILD_JOB_NAME ?? 'marsys-build-pipeline-job'}` (jobInvoker.ts:58)
                    └─ python -m pipeline.orchestrator.main --run-id <uuid>             (main.py:31-68)
                          └─ execute_run(run_id)                                        (runner.py:80)
                                ├─ discover_all()  (import every writers/ module)       (runner.py:90-91)
                                ├─ acquire_chart_lock(chart_id)  (advisory; exit 3 if held)
                                ├─ for asset_id in plan:
                                │     ├─ check_signals (pause/stop)                      (runner.py:118-126)
                                │     ├─ is_asset_complete → skip if 'lit'               (runner.py:128-130)
                                │     └─ run_asset(conn, cur, run_id, chart_id, asset_id, position)
                                └─ mark_run_state('completed')
```

`run_asset` (asset_runner.py:162) per asset:
- ensures `asset_throughput` row (global vs per-chart `ON CONFLICT` split, migration 184) → `state='building'`;
- ensures `build_run_assets` row → `building`; sets `build_runs.current_asset_id`; commits; emits SSE;
- branches on `asset_registry.asset_type == 'service'` → `_run_service_health_probe` (GREEN/degraded/down) and **returns** (asset_runner.py:229-233);
- else `get_writer(asset_id)`; if `None` → `mark_asset_error("no writer registered")` and return (asset_runner.py:237-239);
- else **inside `SAVEPOINT writer_exec`**: build `ContextSpec(asset_id, build_id=run_id, db_conn=conn, config={'chart_id': chart_id})`, call `writer_cls().run(ctx)`, read `rows_inserted + rows_updated` (asset_runner.py:244-260);
- **orchestrator owns the state write**: `UPDATE asset_throughput SET state='lit', rows_written, built_against_upstream_hash, built_against_writer_hash, last_error=NULL` (asset_runner.py:266-276), `build_run_assets='complete'`, commit, emit SSE, mark transitive downstream `stale`.

The contract objects (writers/__init__.py):
- `ContextSpec = {asset_id, build_id, db_conn (caller-owned; writer doesn't close or commit), config (chart_id for per_chart), dry_run}`.
- `WriterResult = {asset_id, rows_inserted, rows_updated, rows_skipped, duration_seconds, notes}`.
- `WriterBase.run(ctx) -> WriterResult`; **MUST NOT** `commit()/rollback()/close()`; registered via `@register('bg_*')`; auto-discovered by `_auto_discover()`.

**This already expresses a per-chart writer** (`config['chart_id']`). The L0 service health primitive already exists. The gap is purely (a) GA writers don't conform and aren't registered, and (b) no heavy-writer / verify-then-regenerate support.

---

## §2.A — The conformance diff (concrete)

A GA writer today is a **module function**, not a class:

```python
# ga_writers/ga_dashas_writer.py
def build_ga_dashas(chart_id=CANONICAL_CHART_ID, build_id=None, *, systems=None, ayanamshas=None, skip_db=False) -> dict
def build_system(system_id, ayanamsha_id, chart_id=CANONICAL_CHART_ID, build_id=None, *, skip_db=False) -> dict
```

Inside, it opens its **own** connection and **commits on it**:

```python
# build_system (ga_dashas_writer.py:2297-2300)
with _conn() as conn:                 # psycopg.connect(_db_url())  — a SECOND connection
    rows_written = _upsert_rows(conn, rows, system_id, ayanamsha_id)   # ...which COMMITs (line 2163)
    _update_asset_throughput(conn, chart_id, build_id, "ga_dashas", rows_written, "in_progress")  # writes asset_throughput itself
```

The required end-state is a registered class:

```python
@register('ga_dashas')
class GaDashasWriter(WriterBase):
    asset_id = 'ga_dashas'
    def run(self, ctx: ContextSpec) -> WriterResult: ...
```

| Axis | GA writer today | `WriterBase` contract | Conflict? | What the adapter must do |
|---|---|---|---|---|
| **Entry shape** | module fn `build_ga_*(chart_id, build_id, ...)` | `run(self, ctx) -> WriterResult` | mechanical | wrap fn in a class method |
| **chart_id** | kwarg, defaults to `CANONICAL_CHART_ID` (`482012f1…`) | `ctx.config['chart_id']` | **yes** — hard-coded native default must die; per-chart Build passes a real chart_id | read `ctx.config['chart_id']`; never default to the native |
| **build_id** | kwarg, auto-`uuid4()` if None | `ctx.build_id` (= `run_id`) | mechanical | read `ctx.build_id` |
| **DB connection** | opens own `_conn()` = `psycopg.connect()`; uses `with` (closes it) | `ctx.db_conn` (caller-owned; **don't close**) | **YES — load-bearing** | use `ctx.db_conn` throughout; delete every `with _conn()` in the write path |
| **Transaction** | `conn.commit()` per system (`_upsert_rows`:2163; positions:597) | writer **MUST NOT commit/rollback**; orchestrator wraps in `SAVEPOINT writer_exec` and commits once | **YES — load-bearing** | remove all `commit()`; let the orchestrator's savepoint + commit own atomicity |
| **Idempotency** | `replace_prior_*` (`_idempotency.py`) called by writer, same txn | unspecified — see §2.B.3 | OK if it uses `ctx.db_conn` | **keep in writer**, but on `ctx.db_conn` so it lives inside the savepoint |
| **Rows reporting** | returns ad-hoc summary dict (`rows_written`, `total_rows_written`, `total_chart_facts_rows`, per-step) | `WriterResult(rows_inserted, rows_updated, rows_skipped, …)` | mechanical | map the writer's counts → `WriterResult` |
| **Telemetry** | writes `asset_throughput` itself (`_telemetry.update_asset_throughput`, `_update_asset_throughput`) | **orchestrator** writes `asset_throughput` (asset_runner.py:266-276) | **YES — double write** | **delete the `_telemetry` call from the conformed path**; orchestrator is the single state writer |
| **Multi-ayanamsha** | internal loop (5 ayanamshas) | not expressed | OK for light writers; see §2.B.4 | keep internal for light writers; becomes a sub-step axis for `ga_dashas` |
| **Registration** | none → `get_writer` returns `None` | `@register('ga_*')` + auto-discovered | **YES — why Build can't run them** | add `@register`; ship the module where `_auto_discover` can import it |

### The transaction-ownership conflict, spelled out (this is the dangerous one)

`run_asset` runs the writer inside `SAVEPOINT writer_exec` on connection `conn`, expecting a crash to `ROLLBACK TO SAVEPOINT writer_exec` and undo *only* the writer's rows (asset_runner.py:244-259). The GA writers defeat this two ways:

1. **Different connection.** `build_system` opens a *second* psycopg connection via `_conn()`. The orchestrator's savepoint is on `conn`; the GA writes land on a different socket. `ROLLBACK TO SAVEPOINT` on `conn` cannot undo them.
2. **Internal commits.** Even on one connection, `_upsert_rows` calls `conn.commit()` (line 2163), which **releases the savepoint and ends the transaction**. After that, the orchestrator's `ROLLBACK TO SAVEPOINT writer_exec` would raise (savepoint gone), and partial multi-system writes are already durable.

> **Conformance therefore is not "wrap the function." It is "invert connection + transaction ownership."** The adapter must thread `ctx.db_conn` into `build_ga_*` / `build_system` / `_upsert_rows` / `replace_prior_*` and strip every `commit()` and every `with _conn()`. This is the real work of Option A (§2.E), and it is exactly what makes the writer savepoint-safe and resumable.

### Two build-state writers → one

Today, for a conformed-but-not-cleaned writer, **both** of these fire for `ga_dashas`:
- GA's `_telemetry.update_asset_throughput(... state='lit'/'in_progress', rows_written=<GA's count>)`, and
- the orchestrator's `UPDATE asset_throughput SET state='lit', rows_written=<result.rows_inserted+rows_updated>, built_against_*_hash` (asset_runner.py:266-276).

They race and can disagree on `rows_written` and `state`. **Resolution: the orchestrator is the sole `asset_throughput` writer.** Delete `_telemetry`'s write from the conformed path. (`_telemetry.py` stays in the repo for the legacy standalone `build_runner` CLI until that CLI is retired, but a registered writer never calls it.) The orchestrator already records `built_against_upstream_hash` / `built_against_writer_hash`, which the GA telemetry never did — another reason to centralize.

---

## §2.B — Does the FROZEN contract stretch to L0–L5? (the decisive question)

**Verdict: YES for L0 + per-chart light writers with zero change; NO for heavy writers without ONE addition — sub-steps. Bake sub-steps in now; freeze the rest.**

### B.1 Per-chart — already sufficient
`ContextSpec.config` carries `chart_id` (asset_runner.py:250). A per-chart writer has chart_id, build_id, a caller-owned connection, and dry_run. Nothing missing. The 9 GA assets are all `scope='per_chart'` (confirmed in seed + migration 195). ✓

### B.2 Heavy writers / runtime — the decision (sub-steps REQUIRED, not optional)

`ga_dashas` = **7 systems × 5 ayanamshas = 35 independent chunks**, ~2.5–3M rows, ~40 min. Test the single-`run(ctx)` model against the deployed envelope (from §2.F):

| Constraint | Value | A 40-min single `run(ctx)` call? |
|---|---|---|
| Cloud Run Job task timeout | **3600 s (60 min)**, `maxRetries: 0` | survives only if the asset is the *only* heavy step; no headroom for the rest of the plan |
| Watchdog orphan-run reaper | fails `build_runs` after **30 min** running with no asset completing in the last 10 min (watchdog/route.ts:34-46) | **REAPED at 30 min** — a 40-min single asset completes nothing for 40 min → the parent run is marked `failed` mid-write |
| Watchdog stuck-asset reaper | flips `building→error` when `last_built_at < now()-15min` (watchdog/route.ts:48-56); **no heartbeat** — `last_built_at` is only written on completion | on a **rebuild**, `last_built_at` holds the prior completion (>15 min old) → asset flipped to `error` at the next 5-min tick, ~15 min in |

A single 40-minute `run(ctx)` is **not viable** on the deployed platform. It trips the 30-minute orphan reaper, risks the 60-minute job cap, and is reaped at ~15 minutes on any rebuild.

**Decision: the frozen contract supports an asset declaring SUB-STEPS, and the orchestrator drives them.** The natural grain already exists in code: `build_system(system_id, ayanamsha_id, chart_id, build_id)` is exactly one chunk and is already "context-decay-safe / call this per-system" (ga_dashas_writer.py:2215). Concretely, freeze this one extension into `WriterBase`:

```python
class WriterBase:
    asset_id: str = ''
    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Default: a single sub-step (the whole asset). Heavy writers override."""
        return [SubStep(key=self.asset_id, label=self.asset_id)]
    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult: ...
    # run(ctx) keeps working: default run() = run_substep over plan_substeps(); light writers just implement run().
```

The orchestrator's per-asset block becomes: `for step in writer.plan_substeps(ctx): run_substep(...)`, and **after each sub-step it touches `asset_throughput.last_built_at = NOW()`** (the heartbeat) and emits an `asset.substep` SSE event. Effects:
- **Heartbeat** — each sub-step (≈1–2 min, ≪15 min) refreshes `last_built_at`, so neither reaper fires; the asset never looks stuck.
- **Granular SSE** — "ga_dashas: vimshottari × lahiri (12/35)" instead of one 40-min silence.
- **Mid-asset resume** — a sub-step is the savepoint unit; a crash at chunk 20 resumes from chunk 20 (the writer's `replace_prior_*` makes each sub-step replace-not-accrete, so re-running a completed chunk is safe).
- **Still one job** — sub-steps run inside the same `--run-id` process; the 3600 s budget is spent in short, observable increments, and a partially-complete heavy asset can be continued by a follow-up run rather than restarted.

> This is the **one and only** generalization to bake into the frozen contract now. After it, L2–L5 never change the contract: a light writer implements `run()` (or trivially gets the 1-substep default); a heavy writer overrides `plan_substeps` + `run_substep`. Freeze here.

(Job-timeout note: even with sub-steps, a 40-min asset plus the rest of an L1 plan can exceed 3600 s in one task. Pair the sub-step heartbeat with **raising the Cloud Run Job `timeoutSeconds`** and/or letting the run resume across task invocations — see §2.F.3. Sub-steps make resume cheap; the timeout bump buys a single task enough wall-clock.)

### B.3 Idempotency — writer-owned, on the orchestrator's connection
`replace_prior_*` (`_idempotency.py`) is **natural-key-scoped** — it deletes only the `(chart_id, ayanamsha_id, fact_category/system_id/varga)` scope the writer is about to rewrite, so writers never clobber each other and a per-ayanamsha insert never wipes a sibling. That knowledge lives in the writer; the orchestrator cannot reproduce it generically. **Recommendation: keep idempotency in the writer**, called immediately before INSERT **on `ctx.db_conn`** (inside the orchestrator's savepoint). With sub-steps, `replace_prior_*` is scoped to the sub-step's keys → safe re-run of any chunk. Centralizing in the orchestrator would require it to know every table's natural key; that re-introduces per-asset branching — the opposite of the goal. (The registry already carries a coarser `clear_tables text[]` for whole-table assets like `ganita_positions`; the orchestrator MAY honor that for `scope`-wide truncation, but per-key replace stays in the writer.) L2–L5 inherit one rule: **"your writer replaces its own scope before it inserts, using `ctx.db_conn`."**

### B.4 Multi-ayanamsha — inside the writer, except as the heavy sub-step axis
The 5-ayanamsha loop stays **inside** light writers (it's fast and the contract needn't know). For `ga_dashas` it becomes one half of the `(system × ayanamsha)` sub-step grid. So: the contract does **not** express ayanamsha; it expresses sub-steps, and heavy writers choose ayanamsha as a sub-step axis. No registry column for ayanamsha.

---

## §2.C — The L0 verify-then-conditionally-regenerate primitive (the one new orchestrator behavior)

Today `_run_service_health_probe` (asset_runner.py:109-157) runs the probe and **only marks** GREEN→`lit` / else→`error`. The native's L0 model needs: **check fails → regenerate ONLY that asset → re-check.** Design it generic and metadata-driven, never `if layer == 'L0'`:

**Metadata (see §2.D):** add `rebuild_on_probe_fail boolean DEFAULT false` to `asset_registry`. Generalize the health check to data assets too: today `health_probe jsonb` is populated only on the 3 `service` rows; allow a **data** asset to carry a check (either reuse `health_probe` with a `probe_type: 'row_count' | 'forensic' | 'integrity_sql'`, or the existing `count_sql` vs `target_floor` as the cheapest integrity probe). The native said "a couple of checks at L0" — design for **both** service probes *and* data-asset integrity checks.

**Orchestrator addition (the only genuinely-new code):**

```python
def run_asset_with_healthcheck(...):
    has_check = is_service or registry_row.get('health_probe') or registry_row.get('integrity_check')
    if has_check:
        status = run_probe(asset_id, registry_row)          # GREEN | degraded | down/FAIL
        if status == 'GREEN':
            mark_lit(rows_written=0); emit('probe.green'); return          # skip-if-green
        if registry_row.get('rebuild_on_probe_fail') and get_writer(asset_id) is not None:
            emit('probe.failed→regenerating')
            run_writer(asset_id)                            # regenerate ONLY this asset (its registered writer)
            status2 = run_probe(asset_id, registry_row)     # re-verify
            mark_lit() if status2 == 'GREEN' else mark_error(f'regen-then-probe still {status2}')
            return
        mark_error(f'probe {status}; no rebuild policy/writer'); return    # today's behavior, unchanged
    # ... existing data-writer path unchanged ...
```

This is **one** branch added to the existing service path; it is metadata-driven (any asset, any layer, that sets `rebuild_on_probe_fail=true` and registers a writer participates). It requires that the failing L0 asset **also have a registered writer** (so it can be regenerated) — another reason Option A (everything is a registered `WriterBase`) is the clean foundation: a service asset that wants self-heal simply registers its regeneration writer. This should be the **only** new orchestrator primitive in the whole generalization.

---

## §2.D — Registry metadata to add (so dispatch is 100% metadata-driven)

**Already present and sufficient** (confirmed by migration audit): `scope` (global/per_chart, 167:23), `storage_type` + `asset_type` (service/data, 167:14 / 202:13), `depends_on text[]` (167:22), `target_table`, `count_sql`, `size_sql`, `target_floor`, `sort_order`, `layer`, `is_active`, `catalog_status`, `clear_tables text[]` (181:9), `health_probe jsonb` (202:17), `provides_apis jsonb`. `asset_throughput` carries `state` (CHECK: dormant/building/lit/stale/error), `rows_written`, `last_built_at`, `last_measured_build_id`, `built_against_upstream_hash`, `built_against_writer_hash`, plus the two partial uniques (`(chart_id,asset_id) WHERE chart_id IS NOT NULL`; `(asset_id) WHERE chart_id IS NULL`).

**ABSENT — add these (one migration):**

| # | Column / change | Table | Type / default | Why |
|---|---|---|---|---|
| 1 | **Writer locator** | — | (see note) | The single biggest blocker. `get_writer` keys on `asset_id` from a registry populated only by `bg_*` modules; `get_writer_git_hash` hard-codes `writers/{asset_id}.py` (asset_runner.py:64), which **breaks for any writer outside `writers/`**. **Recommended (Option A): no column — convention.** Every writer is `@register('<asset_id>')` and auto-discovered; locator = `asset_id`. Fix `get_writer_git_hash` to resolve the path from the registered class's module (`inspect.getfile(cls)`) instead of a hard-coded path. (If Option B were chosen, you'd instead need `writer_module text` — an argument *against* B.) |
| 2 | `rebuild_on_probe_fail` | `asset_registry` | `boolean DEFAULT false` | §2.C self-heal policy, metadata-driven |
| 3 | Data-asset health check | `asset_registry` | extend `health_probe jsonb` usage (add `probe_type`) **or** add `integrity_check_sql text` | §2.C — let a *data* asset (not just a service) declare a check; none do today |
| 4 | `has_substeps` (hint only) | `asset_registry` | `boolean DEFAULT false` | lets the cockpit/orchestrator know an asset is chunked **before** invoking; the *actual* sub-step list comes from `writer.plan_substeps(ctx)` (code-derived, not static), so no `sub_steps jsonb` column is needed |
| 5 | `max_task_seconds` / `estimated_seconds` populate | `asset_registry` | int | `estimated_seconds` already exists but GA rows leave it NULL; populate so the planner can warn on long assets and choose job timeout |
| 6 | **Populate intra-GA `depends_on`** | `asset_registry` data | — | Not a schema change — a data fix. All 9 GA rows currently declare `depends_on=[]` (only `ga_sensitive→bg_reference`). The plan is correct today only because `sort_order` 1–9 happens to match the real order. For `topoSort` (plan.ts) + `compute_downstream_closure` (stale propagation) to be *real*, populate the true edges (e.g. `ga_structural`/`ga_strength`/`ga_sade_sati` depend on `ga_positions`). |

Heartbeat support (§2.B.2) needs **no new column** — it reuses `asset_throughput.last_built_at`, written per sub-step.

> Net: **2 genuinely-new columns** (`rebuild_on_probe_fail`, and one of `integrity_check_sql`/`probe_type`), **1 optional hint** (`has_substeps`), **1 code fix** (`get_writer_git_hash` path resolution), **1 data backfill** (`depends_on` + `estimated_seconds`). Dispatch is then fully metadata-driven with no `if layer == …` anywhere.

---

## §2.E — Option A vs Option B

**Recommendation: Option A — converge to registered `WriterBase` subclasses. Decisively.**

### Option A — converge (RECOMMENDED)
Each GA writer becomes a thin `@register('ga_*')` `WriterBase` subclass whose `run()` / `run_substep()` calls the existing `build_ga_*` / `build_system` logic, **refactored to**: (a) use `ctx.db_conn` (delete `with _conn()`), (b) never `commit()`, (c) read `chart_id`/`build_id` from `ctx`, (d) **not** call `_telemetry`, (e) for `ga_dashas`, expose `plan_substeps` over the 35 `(system × ayanamsha)` chunks.

- **Effort:** 9 adapter classes (small). The real work is the **connection/transaction-ownership refactor** in each writer's DB-write path (`_upsert_rows`, the `build_ga_*` `with _conn()` blocks, `replace_prior_*` call sites) — this is where the risk lives, because it touches every GA writer's durability path.
- **Risk:** medium, well-contained. Mitigated by the sub-step grain (each chunk = one savepoint), by keeping `replace_prior_*` (replace-not-accrete makes re-runs safe), and by a side-by-side test against the existing `build_runner` row counts (chart_facts/chart_dashas totals are known: 536,471 dashas, 21,635 divisionals, etc., per CURRENT_STATE v5.72).
- **Payoff:** orchestrator code stays frozen; ONE telemetry path (orchestrator); ONE transaction model (savepoint-isolated); savepoint isolation actually works; self-heal (§2.C) is available because every asset has a registered writer. **L2 Bodha registers `@register('bo_*')` subclasses from day one into the same machine.**

### Option B — adapter dispatch (NOT recommended)
Teach `run_asset` a fallback: when `get_writer(asset_id) is None`, shell into `ga_writers.build_runner`. Less GA refactor up front, but:
- **Permanently forks three things:** two writer patterns (class vs module-fn), two telemetry paths (`_telemetry` vs orchestrator — the double-write is never resolved), two transaction models (own-connection-commit vs caller-owned-savepoint). Savepoint isolation, `built_against_*_hash`, and SSE granularity are all **lost** for GA assets.
- **Sub-steps + self-heal don't compose** — `build_runner` is a monolithic "run all 9 steps in one process" CLI; the orchestrator can't drive its chunks or regenerate one asset.
- **L2 inherits the fork:** Bodha briefs would have to pick a side, and "the fork already exists" is the path of least resistance → the generalization never actually lands. This is the failure mode §0 of the brief warns against (per-layer extension by accretion).

**Which sets the cleaner L2 foundation:** A, unambiguously. L2 writers are *new code* — there is zero cost to writing them as `WriterBase` subclasses from the start, and every reason to (one registry, one telemetry, one txn model, sub-step + self-heal for free). B would make L2's first decision "which of our two incompatible writer patterns do we use," which is exactly the wrong question to inherit.

---

## §2.F — Deployment reality checks

### F.1 Job name — MISMATCH (must fix)
- Real, existing job (gcloud, project `madhav-astrology`, region `asia-south1`): **`brahma-build-pipeline-job`** (last run 2026-06-08; `timeoutSeconds: 3600`, `maxRetries: 0`). Also `brahma-foundation-bootstrap`.
- `jobInvoker.ts:58` defaults to **`marsys-build-pipeline-job`** via `get('BUILD_JOB_NAME', 'marsys-build-pipeline-job')`. `BUILD_JOB_NAME` is **not set in `deploy.yml`** → runtime falls back to the non-existent name. `cloud_run/jobs.ts:5` also hard-codes the stale `marsys-build-pipeline-job`. `infra/iam/main.tf:128` correctly says `brahma-build-pipeline-job`.
- **Fix:** set `BUILD_JOB_NAME=brahma-build-pipeline-job` in `deploy.yml` (amjis-web env) **or** change the `jobInvoker.ts` default; reconcile `cloud_run/jobs.ts` and tests. (Note: if a live Cloud Run env-var already overrides this on amjis-web, Build may work today despite the repo default — but it is not reproducible from the repo, which is its own hygiene problem.)

### F.2 Image contents — `ga_writers/` is NOT in the deployed job image (prerequisite)
- The job runs image **`asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline@sha256:eedd16a9…`**, built from **`platform/python-sidecar/Dockerfile.pipeline`** (entrypoint `python -m pipeline.orchestrator.main`). Its `COPY` lines bring in `pipeline/`, `brahmagyan/`, `pyjhora_adapter/`, and 3 CGM JSONs — **there is no `COPY … ga_writers/`**. So `python -m ga_writers.build_runner` would `ModuleNotFoundError` inside the deployed job today, and a registered GA `WriterBase` would not be importable either.
- The `amjis-sidecar` **service** image (`platform/python-sidecar/Dockerfile`, `COPY . .`) *does* contain `ga_writers/` — but that is a different image from the job. (This is why L1 built via a *separate* `l1-ganita-build-482012f1` Cloud Run Job, per CURRENT_STATE v5.71, not via `brahma-build-pipeline-job`.)
- The `brahma-pipeline` image is **built out-of-band** — no workflow or IaC builds/pushes it (CREATED BY the operator's account). The production SHA is not reproducible from the repo.
- **Prerequisite for Option A:** (a) add `COPY platform/python-sidecar/ga_writers/ ./platform/python-sidecar/ga_writers/` to `Dockerfile.pipeline`; (b) ensure `_auto_discover` can import GA writers (either move/register them under `pipeline/orchestrator/writers/` as thin adapters that import from `ga_writers`, **or** extend discovery to the `ga_writers` package); (c) bring the `brahma-pipeline` image build into CI/IaC so the deployed SHA is reproducible.

### F.3 Watchdog / job timeout — would reap a 40-min asset (fix with sub-steps + timeout bump)
- Active reaper: `platform/src/app/api/cockpit/watchdog/route.ts` (Cloud Scheduler, ~5 min). `build/reap/route.ts` is deprecated (410).
- **Orphan-run: 30 min** — `build_runs` `running` with no `asset_throughput.last_built_at` in the last 10 min → `failed` (route.ts:34-46). A 40-min single asset completes nothing for 40 min → run failed at 30 min.
- **Stuck-asset: 15 min** — `state='building' AND last_built_at < now()-15min → error` (route.ts:48-56). **No heartbeat** (`last_built_at` only written on completion/error; no DEFAULT). First build dodges it by NULL accident; rebuilds get reaped ~15 min in.
- **Cloud Run Job task timeout: 3600 s (60 min) hard**, `maxRetries: 0`, not managed by deploy.yml.
- **Fix:** the §2.B.2 sub-step **heartbeat** (touch `last_built_at` per sub-step) keeps a chunked heavy asset under both reaper thresholds. Additionally, **raise the Job `timeoutSeconds`** (or enable cross-task resume) so a full L1 plan containing a 40-min asset fits one task, and bring the job's timeout under IaC so it's not a console-only setting.

---

## §3.7 — End-to-end test plan

### Test 1 — Per-chart L1 (the GA convergence proof)
**Goal:** prove `POST /api/cockpit/runs scope=layer scope_target=ganita` for a chart runs all 9 GA assets in dependency order, flips `asset_throughput` `lit` **via the orchestrator** (not `_telemetry`), streams SSE, with **no hand-invoking**.

Preconditions: §2.F.1 (job name), §2.F.2 (`ga_writers/` in `brahma-pipeline` image + registered + discoverable), §2.F.3 (sub-step heartbeat or raised timeout) all done. Use a **fresh non-native chart** (NOT `482012f1` — the native is the contamination control; a fresh chart proves chart_id is read from `ctx.config`, not the `CANONICAL_CHART_ID` default).

1. Create a fresh client profile → `chart_id = C`. Confirm `asset_throughput` has no `lit` GA rows for `C`.
2. `POST /api/cockpit/runs` `{ chart_id: C, scope: 'layer', scope_target: 'ganita', action: 'build' }`. Expect `201 { run_id, plan, asset_count: 9 }`. **Assert `plan` is dependency-ordered** — `ga_positions` before `ga_structural`/`ga_strength`/`ga_sade_sati` (requires §2.D.6 `depends_on` backfill; otherwise it's only `sort_order`-correct).
3. **Assert the Cloud Run Job actually started** (`gcloud run jobs executions list --job brahma-build-pipeline-job`) — proves `invokeRunJob` hit a real job (F.1).
4. Subscribe to `GET /api/cockpit/sse`. Assert event stream: per asset `asset.state_change building→lit`; for `ga_dashas`, multiple `asset.substep`/`asset.progress` events (≥35) with `last_built_at` advancing between them (heartbeat proof).
5. **Single-writer proof:** during `ga_dashas`, assert `asset_throughput.rows_written` for `(C, ga_dashas)` is written by the orchestrator's UPDATE — instrument by confirming `built_against_writer_hash` and `built_against_upstream_hash` are non-NULL (only the orchestrator sets these; `_telemetry` never did). If those columns are populated, the orchestrator is the writer.
6. On completion: all 9 `(C, ga_*)` rows `state='lit'`; counts match known L1 totals (chart_dashas 536,471; chart_divisionals 21,635; ganita_positions 50; etc., scaled to chart C). `build_runs.state='completed'`. **No row written by `_telemetry`** (grep job logs for `[telemetry]` — must be absent on the conformed path).
7. **Idempotency / resume proof:** re-run `action='rebuild'` scope=asset `ga_dashas`. Assert final row count is identical (replace-not-accrete), and that killing the job at sub-step ~20 then re-running resumes without doubling rows.
8. **Reaper non-interference:** confirm the watchdog ran ≥1 cycle during the 40-min `ga_dashas` and did **not** flip the run to `failed` or the asset to `error` (heartbeat working).

### Test 2 — Global L0 (verify-then-regenerate proof)
**Goal:** prove L0 assets health-check and regenerate **only on failure**.

1. Pick an L0 asset with `rebuild_on_probe_fail=true`, a registered writer, and a health/integrity check (service probe or data `count_sql`/`integrity_check_sql`).
2. **Green path:** with the asset healthy, `POST /api/cockpit/runs scope=global action=update` (or the `--global-build` path). Assert the asset's probe runs, returns GREEN, asset is marked `lit` with `rows_written=0`, and **its writer did NOT run** (no INSERTs, writer git-hash unchanged, SSE shows `probe.green`/skip — not `building`).
3. **Failure path:** deliberately invalidate that asset (e.g. truncate its table / break the smoke condition in a scratch DB). Re-run global build. Assert: probe → FAIL → SSE `probe.failed→regenerating` → the asset's **writer runs** (rows inserted) → **re-probe GREEN** → `lit`. Assert **no other L0 asset rebuilt** (regenerate-only-the-failing-asset).
4. **No-policy path:** for an asset with `rebuild_on_probe_fail=false` whose probe fails, assert it is marked `error` and **not** regenerated (today's behavior preserved).

---

## §3.8 — L2-readiness conformance checklist (what an L2 Bodha writer must do to be orchestrator-native from day one)

Drop this verbatim into every L2 (and L3–L5) writer brief. A writer is orchestrator-native iff **all** hold:

- [ ] **Is a class**, `@register('<asset_id>')`, subclassing `WriterBase`; `asset_id` class attr matches `asset_registry.asset_id`.
- [ ] **Discoverable** — the module is imported by `_auto_discover()` (lives under `writers/`, or the discovery path is extended to its package) **and ships in the `brahma-pipeline` job image** (`Dockerfile.pipeline` COPY).
- [ ] **`run(ctx) -> WriterResult`** (light) **or** `plan_substeps(ctx)` + `run_substep(ctx, step) -> WriterResult` (heavy, > ~10 min or > a few hundred k rows).
- [ ] **Connection:** uses `ctx.db_conn` exclusively. **Never** opens its own connection. **Never** calls `commit()`/`rollback()`/`close()` — the orchestrator owns the transaction + savepoint.
- [ ] **chart_id / build_id:** read from `ctx.config['chart_id']` and `ctx.build_id`. **No hard-coded `CANONICAL_CHART_ID` default.**
- [ ] **Idempotency:** calls its own `replace_prior_*` (natural-key-scoped, replace-not-accrete) on `ctx.db_conn` immediately before INSERT; safe to re-run any sub-step.
- [ ] **Telemetry:** writes **nothing** to `asset_throughput`. The orchestrator is the sole state writer. Returns counts in `WriterResult`.
- [ ] **dry_run:** honors `ctx.dry_run` (reports what it *would* write; no INSERT/UPDATE).
- [ ] **Determinism:** same inputs → same rows + same content hashes; INSERT … ON CONFLICT for idempotency where applicable.
- [ ] **Registry row exists** with correct `scope`, `asset_type`, `layer`, **populated `depends_on`** (real upstream edges, not `[]`), `count_sql` + `target_floor` (completeness), `sort_order`, and — if self-healing — `rebuild_on_probe_fail=true` + a `health_probe`/`integrity_check_sql`. Set `has_substeps=true` if heavy.
- [ ] **No orchestrator change required** — if onboarding the writer needs a new `if` branch in `run_asset`/`runner.py`, the contract was violated; fix the writer, not the orchestrator.

> When this checklist passes for every L2 writer with zero orchestrator edits, the frozen-contract goal is proven: the orchestrator was written once; L2 just conformed + registered.

---

## §4 — What to do next (sequenced; none done here — investigation only)

1. **Deploy prerequisites (independent of A/B, do first):** F.1 job-name reconcile; F.2 add `ga_writers/` to `Dockerfile.pipeline` + bring the `brahma-pipeline` image into CI/IaC; F.3 raise Job `timeoutSeconds` under IaC.
2. **Freeze the contract:** add `plan_substeps`/`run_substep` + `SubStep` to `WriterBase`; add the sub-step heartbeat + `asset.substep` SSE to `run_asset`. (One-time; never again.)
3. **One migration:** `rebuild_on_probe_fail`, data-asset `integrity_check_sql`/`probe_type`, optional `has_substeps`; backfill GA `depends_on` + `estimated_seconds`; fix `get_writer_git_hash` path resolution.
4. **Option A conversion:** 9 GA `WriterBase` adapters; refactor connection/transaction ownership (delete `with _conn()` + `commit()` from the write path); drop `_telemetry` from the conformed path; `ga_dashas.plan_substeps` over 35 chunks.
5. **The one new primitive:** `_run_service_health_probe` → generic verify-then-regenerate (§2.C).
6. **Prove it:** run Test 1 + Test 2 (§3.7).
7. **L2 onboards by conforming** (§3.8) — no orchestrator change.

---

*End. Frozen-contract verdict: freeze `WriterBase.run(ctx)->WriterResult` as-is for global + per-chart light writers; bake in exactly ONE addition — declarable sub-steps with an `asset_throughput.last_built_at` heartbeat — to carry heavy writers (`ga_dashas`, and any L2–L5 equivalent) under the deployed reaper/timeout envelope. Add the verify-then-regenerate branch as the only new orchestrator code. Everything else is conformance (Option A) + ~2 metadata columns. Read-only investigation; no code changed, no migrations applied, no prod touched.*
