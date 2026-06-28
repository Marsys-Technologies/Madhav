---
artifact: ORCHESTRATOR_WAVE_PARALLEL_SCHEDULER_v1_0.md
canonical_id: ORCHESTRATOR_WAVE_PARALLEL_SCHEDULER
version: 1.0
status: CURRENT
authored_by: Claude Code (Cowork) 2026-06-29
amends: ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
native_approval: >
  Native (Abhisek Mohanty) explicitly approved changing the orchestrator scheduler from
  serial to wave-parallel, "with version bump", on 2026-06-29 (AskUserQuestion: "FROZEN
  approval" = "Approve, with version bump").
goal: >
  Record the orchestrator scheduler change from a strictly-serial plan walk to a width-limited
  wave-parallel DAG executor, the DAG-correctness prerequisites that made it safe, and the
  affirmation that the FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE §2) is
  UNCHANGED. Scope: pipeline/orchestrator/{runner.py, asset_runner.py}.
---

# Orchestrator — Wave-Parallel Scheduler (Amendment to the Convergence Close)

## §1 — What changed

`runner.py` previously walked the build plan **strictly serially** — `for asset_id in plan:
run_asset(...)`, one asset fully completing before the next began, on a single shared
connection. The DAG is genuinely wide (peak ~8 independent assets in L1), so the long pole
(ga_dashas / ka_sangam) blocked everything behind it for no reason.

It now runs a **width-limited wave-parallel DAG executor** (`runner.execute_dag`, driven by
`_schedule_parallel`):

- An asset is dispatched **only when every declared dependency is committed-complete** and
  **no dependency failed/blocked** — identical in meaning to the old inline upstream-success
  gate. Two assets run concurrently **only if neither (transitively) depends on the other**.
- Failure is transitive: a failed asset blocks its downstream subtree (no "empty but
  complete" rows on incomplete upstream data).
- Width = `ORCHESTRATOR_WORKER_LIMIT` (default **4**; `1` = dependency-ordered serial, a safe
  fallback). Each concurrently-executing asset runs on its **own** DB connection.

## §2 — What did NOT change — the FROZEN contract holds

`ORCHESTRATOR_CONVERGENCE_CLOSE §2` (the `WriterBase` contract) is **untouched**. Verified
clause by clause under parallelism:

| Frozen clause | Under wave-parallel |
|---|---|
| `ContextSpec.db_conn` is caller-owned; writer never commits/closes | Each worker owns ONE connection and passes it as `ctx.db_conn`; the writer still never commits/closes it — the orchestrator's `_drive_substeps` commits, on that worker's connection. |
| `run(ctx)` light / `plan_substeps`+`run_substep` heavy | Unchanged — `run_asset` invokes writers exactly as before. |
| `SubStep` savepoint-isolated + heartbeat + per-substep commit | Unchanged — runs on the worker's connection. |
| Orchestrator is the sole `asset_throughput` writer | Unchanged. |

The change is **how many caller-owned connections exist at once** (one per concurrent writer
instead of one shared) and **the order of dispatch** — both orchestrator-internal scheduler
concerns, not writer-contract concerns. No writer needs any change.

## §3 — Why it is safe: the correctness prerequisites (defense in depth)

Parallelism is only safe on a CORRECT DAG. The old serial build masked DAG defects via
sort-order luck; these were closed FIRST, in order:

1. **Edge completeness (migrations 365 + 366).** A 5-layer audit (independently source-verified)
   found ~40% of data assets declared `depends_on` that did not match their actual reads. 365
   makes `depends_on` a true superset of each writer's reads (adds-only; verified acyclic; 211
   edges). 366 adds the `ph_muhurta → ka_sangam` edge introduced by a bug fix.
2. **CI edge-completeness guard** (`pipeline/orchestrator/dag_edge_guard.py` +
   `tests/test_dag_edge_guard.py`). Automated reads-vs-declared check; fails when a writer adds
   an undeclared cross-asset read. Live registry passes with zero hard violations.
3. **Writer-entry dependency assertion** (`asset_runner.deps_unsatisfied`, called at the top of
   `run_asset`). Before running, asserts every declared dep is actually `lit` (services: not
   `error`) at the correct scope. `ORCHESTRATOR_DEP_ASSERT=enforce|warn|off` (default enforce).
   This is the backstop that fails LOUD instead of silently building on missing data — the
   class of bug that previously hid behind SAVEPOINT/`_table_exists` guards.

## §4 — Connection budget (the binding constraint)

Cloud SQL `max_connections=50`; ~33 available to the orchestrator. Per run: 1 MAIN connection
(advisory lock + run-state + signals) plus up to `WORKER_LIMIT` worker connections. The product
is bounded:

    ORCHESTRATOR_MAX_CONCURRENT_RUNS × (1 + ORCHESTRATOR_WORKER_LIMIT) ≤ ~33

Defaults rebudgeted to **6 × (1 + 4) = 30**. (Was 10 × 1 = 10 under the serial model.) The MAIN
connection commits/rolls back between scheduler rounds so a stop/pause committed by the API
server is visible (the serial loop got this for free via per-asset commits).

## §5 — Verification

- `tests/test_wave_scheduler.py` (7): dependency ordering, real concurrency on independent
  assets, transitive blocking, `worker_limit=1` serial-equivalence, out-of-plan dep seeding,
  missing-upstream → blocked-not-hung, stop halts dispatch.
- `tests/test_orchestrator_gate.py` updated: the upstream-success gate still holds end-to-end;
  the strict-serial-order assertion relaxed to topological-order (parallelism is intentional).
- `tests/test_dag_edge_guard.py` (4), full sidecar suite green.

## §6 — Residual / follow-up

- Register this artifact in `CAPABILITY_MANIFEST.json` (formal manifest step; tracked alongside
  the existing R6-1 orchestrator-arc registration residual).
- First true wall-clock validation happens at the **L4 Phala build campaign** (L2–L5 have never
  built end-to-end). `ph_muhurta` gochara transit scoring remains an honest gap until then.
