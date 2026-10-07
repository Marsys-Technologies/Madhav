VERDICT: REJECT

The manifest construction is compatible with the current runner and writer. The production admission checks and transaction reporting are incomplete.

Reviewed `5d9e7127…884d5ea8` without modifying files or accessing any database or network.

1. **P1 — Sealed/published generation 5.0 is never checked. Must fix before production: YES.**  
   [dispatch_v5_small_test_job.py:337](platform/scripts/dispatch_v5_small_test_job.py#L337) proceeds directly through activation, throughput reset and run insertion without querying publication or seal state. An otherwise conforming registry row with an existing published/sealed 5.0 therefore permits a committed dispatch and changes its build metadata. Later writer guards protect generation contents, but do not undo staging: see `services/gochara_kernel/ledger.py:549` and `record_store.py:588`. Check both conditions within the staging transaction using the existing publication/seal locking protocol.

2. **P1 — Admission does not establish that existing v5 state belongs to an eligible test candidate. Must fix before production: YES.**  
   [dispatch_v5_small_test_job.py:147](platform/scripts/dispatch_v5_small_test_job.py#L147) omits `catalog_status` and existing runtime evidence. An inactive retired row, a non-test run, or an orphaned provenance receipt can pass these checks while violating the monitor predicate at `platform/src/lib/nirmana-elevation/definitions.ts:210` and `:289`. More seriously, an existing unsealed **non-test** 5.0 candidate can subsequently be replaced: `ka_gochara_v5.py:837` deletes the entire generation’s output chain, not just the requested class. Require the monitor’s complete eligibility conditions and establish ownership of any existing candidate before staging.

3. **P2 — Reversing activation does not reverse its freshness side effects. Must fix before production: YES.**  
   Both updates at [dispatch_v5_small_test_job.py:337](platform/scripts/dispatch_v5_small_test_job.py#L337) and `:371` fire migration 596’s invalidation trigger. Its update filters only by `asset_id`, marking existing v5 freshness rows **across every chart and partition** stale (`596_nirmana_provenance_receipts.sql:61–80`). Those changes commit even though `is_active` returns to false. A v5 freshness row belonging to another chart is therefore modified by this supposedly single-chart operation. Read and validate the inactive candidate directly; activation is only needed by the reused helper’s query, not by the worker.

4. **P2 — Registry validation is not protected against concurrent changes. Must fix before production: YES.**  
   The SELECT at [dispatch_v5_small_test_job.py:149](platform/scripts/dispatch_v5_small_test_job.py#L149) takes no row lock. Another transaction can activate or alter the row after validation; this dispatch then performs unconditional updates and finally forces it inactive. For example, a concurrent legitimate activation can be silently reversed. Lock the registry row before validating it and retain that lock through staging. The active-run unique index protects a different invariant.

5. **P2 — Setting throughput dormant does not guarantee execution of the requested slice. Must fix before production: YES.**  
   [dispatch_v5_small_test_job.py:345](platform/scripts/dispatch_v5_small_test_job.py#L345) claims to force a genuine build, but `asset_runner.py:1144` can still take the delta-skip path. Its receipt comparison receives chart/birth configuration, not the slice marker, and reads neither throughput nor freshness state (`provenance.py:389–433`). **If a matching proven receipt exists**, changing from `all_classes_1y` to `one_class_full` can skip the writer and reattribute the previous output receipt to the new run (`asset_runner.py:1058`). I reproduced that predicate with an in-memory receipt; I did not establish that such a receipt exists in production. Enforce a clean-receipt prerequisite or ensure the separately launched execution uses the existing force mechanism.

6. **P2 — A reporting failure after successful commit is reported as “nothing committed.” Must fix before production: YES.**  
   [dispatch_v5_small_test_job.py:395](platform/scripts/dispatch_v5_small_test_job.py#L395) closes and prints outside the transaction exception handler. A broken stdout pipe after `commit()` reaches `_safe_failure`, whose default at `:429` says **“No COMMIT was sent … it committed nothing.”** I reproduced one successful mock commit followed by precisely that message and exit 1. Preserve the confirmed committed state and run ID through connection cleanup and output failures. Also, the suggested dry-run recovery does not actually look up the original run.

7. **P2 — The new CI step does not provision its writer dependencies in the selected Python runtime. Must fix before production: NO, by itself; fix before relying on this CI step.**  
   [ci.yml:1003](.github/workflows/ci.yml#L1003) imports the real writer during test collection. The job switches to Python 3.11 at `:850`, then installs only database drivers, PyYAML and pytest at `:855`. Earlier `requirements-ci.txt` installations precede that interpreter selection. A clean selected interpreter lacks dependencies such as SciPy, imported by `services/gochara_kernel/arcs.py:31`. Install the writer test requirements after selecting Python.

The remaining requested checks:

| Check | Result |
|---|---|
| **Manifest and digest** | Both documented invocations passed the actual `validate_frozen_run_manifest`, writer validator and local writer-code digest check. Dispatch canonicalisation matches `runner.py:228` and the TypeScript canonicaliser at `definitions.ts:1535` for both generated manifests. |
| **Atomic marker insertion** | Correct: the marker is added before hashing (`dispatch:238`), and manifest plus digest are inserted together (`:357`). Migration 595 makes the persisted manifest immutable. |
| **Activation and crashes** | The true→false updates occur within one transaction. Other sessions cannot see committed activation; a crash between statements rolls back the transaction. Even an ambiguous COMMIT follows the restoring update. The freshness side effect remains finding 3. |
| **Worker execution** | The script starts nothing. The operator must launch the printed Cloud Run command. `pipeline/orchestrator/main.py:53` requires that exact run ID; `runner.py:1180` loads its frozen plan. The worker does **not** require v5 to remain active. |
| **Scope and dependencies** | The accepted plan contains only v5 for the pinned chart. `asset_set` does not expand dependencies during execution: `runner.py:844` checks out-of-plan prerequisites; unavailable dependencies block v5 rather than being rebuilt. The writer itself also writes its shared rule/substrate tables. |
| **Concurrent normal build/dispatch** | With migration 595 applied, its unique index at `:30` prevents concurrent planned/running/paused runs for the chart. A conflicting insert rolls back this transaction’s earlier changes. Missing an explicit active-run SELECT is therefore **not** itself a concurrency defect. |
| **Dry run** | Same staging statements, followed by rollback, with zero commit calls. Its digest is reproducible for unchanged inputs; the generated run UUID is outside the manifest. PostgreSQL audit identity sequences may still advance on rolled-back trigger inserts. |
| **Operator controls** | The pinned chart, three required execution flags, mutually exclusive modes and environment-only DSN are implemented. Tested connection-error paths suppress credential-bearing exception text. A 90-day retention deadline is printed. However, the watchdog fails undispatched planned runs after **10 minutes** (`watchdog/route.ts:429`); staging cannot wait indefinitely for later approval. |

**Verification:** all **62 new tests passed** locally. Their writer-oracle checks are useful, but the recording database fake cannot prove triggers, uniqueness, locking, privileges or rollback effects. A production-shaped PostgreSQL suite is needed for those guarantees.

**Not verified:** live schema or data, applied migrations, database roles, deployed worker image, actual crash/concurrency behavior, Cloud Run execution, or CI execution. Migration `1304_ka_gochara_v5_registry_row_small_test.sql`, the cited teardown script and its runbook are **absent from this checkout**. The test at `test_dispatch_v5_small_test.py:141` silently skips checking migration 1304 when absent; these production prerequisites remain unqualified.

