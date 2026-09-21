# Domain C — Orchestrator and build path

Packet owner: Domain C subagent, Kāla Readiness Audit, cycle work under
`l3/kala-readiness-audit`. Read-only investigation + one throwaway local Postgres 15 instance
(started and fully torn down in this session) + the project's own orchestrator unit-test suite
(mock-cursor based, no real DB). No production data was read, mutated, or built. No build was
dispatched.

Primary source: `platform/python-sidecar/pipeline/orchestrator/{asset_runner.py, runner.py,
locks.py, writers/__init__.py}`. Contract source: `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`
(v1.2).

---

## 1. Per-chart advisory lock mechanism

**Code:** `platform/python-sidecar/pipeline/orchestrator/locks.py`

```python
def acquire_chart_lock(cur, chart_id: str) -> bool:
    cur.execute("SELECT pg_try_advisory_lock(hashtext(%s)) AS got", (str(chart_id),))
    return bool(cur.fetchone()["got"])

def release_chart_lock(cur, chart_id: str) -> None:
    cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (str(chart_id),))
```

This is a Postgres **session-level advisory lock** keyed on `hashtext(chart_id)` (int32 hash of
the chart UUID string). It is non-blocking (`pg_try_advisory_lock`, not `pg_advisory_lock`):
a caller either gets it immediately or gets `false` back and must defer. Session-level advisory
locks are automatically released if the holding connection ends, which is the failure-safety
property the orchestrator depends on for a crashed run (see §3).

**Called from** `runner.py:1092`, right after the fleet-cap check and before `claim_runnable_run`:

```python
if not acquire_chart_lock(cur, chart_id):
    logger.warning("[orchestrator] chart %s locked by another run — deferring", chart_id)
    conn.close()
    sys.exit(3)
conn.commit()
```

Exit code `3` is the documented "defer, try again later" signal (see `runner.py`'s own
docstring: `3 — chart locked by another run (defer)`). There is also a **separate global lock**
for scope=`global` assets (`_GLOBAL_ASSETS_LOCK_KEY = "nirmana-global-assets"`,
`acquire_global_assets_lock`/`release_global_assets_lock`), acquired only when the frozen plan
contains at least one global-scope asset, released before the chart lock on every exit path
(`runner.py:1099-1108, 1115-1117, 1213-1214`).

**What prevents two concurrent builds on the same chart:** the non-blocking `pg_try_advisory_lock`
call itself — a second orchestrator process for the same `chart_id` gets `got=false` and exits
`3` without touching any state. This is a real Postgres primitive, not an application-level mutex,
so it survives process crashes: if a build process dies without calling `release_chart_lock`, the
underlying Postgres session/connection close still releases the lock (verified live below).

**Live proof (throwaway local Postgres 15, not production):**

```
$ /opt/homebrew/opt/postgresql@15/bin/initdb -D "$DATADIR" -U testuser --auth=trust
$ /opt/homebrew/opt/postgresql@15/bin/pg_ctl -D "$DATADIR" -o "-p 59321 -k $DATADIR" -l /tmp/kala_audit_pg.log start

# Session A: acquire lock on canonical chart_id, hold connection open 4s
$ psql ... -c "SELECT pg_try_advisory_lock(hashtext('482012f1-710e-4a25-994a-93821f5871aa')) AS session_a_got_lock; SELECT pg_sleep(4);" &

# Session B: try SAME chart lock while A holds it
$ psql ... -c "SELECT pg_try_advisory_lock(hashtext('482012f1-710e-4a25-994a-93821f5871aa')) AS session_b_got_same_chart_lock;"
→ f                      # BLOCKED — proves mutual exclusion, matches runner.py's exit(3) defer path

# Session C: try a DIFFERENT chart_id's lock while A still holds chart A's lock
$ psql ... -c "SELECT pg_try_advisory_lock(hashtext('11111111-1111-1111-1111-111111111111')) AS session_c_got_other_chart_lock;"
→ t                      # SUCCEEDED — proves the lock is per-chart, not a single global mutex

# wait for Session A's psql to exit (pg_sleep(4) ends, connection closes)

# Session D: try chart A's lock again now that A's connection has closed
$ psql ... -c "SELECT pg_try_advisory_lock(hashtext('482012f1-710e-4a25-994a-93821f5871aa')) AS session_d_got_lock_after_a_released;"
→ t                      # SUCCEEDED — proves session-scoped auto-release on disconnect
                          # (the exact property a crashed build process relies on)
```

Full transcript captured during the run; instance was `pg_ctl stop -m fast` + `rm -rf` on the
temp data dir immediately after — confirmed no leftover process or temp file
(`ps aux | grep kala_audit` → none; `ls /tmp | grep kala_audit` → none). Note: the harmless
`WARNING: you don't own a lock of type ExclusiveLock` seen when unlocking chart C/D from a
*different* psql invocation than the one that acquired it is an artifact of this throwaway test
script issuing the unlock from a fresh connection — the real `release_chart_lock` in `locks.py`
always runs on the same cursor/connection that called `acquire_chart_lock`, so this does not
reflect a defect in the orchestrator's own code.

**Note on distinction from `test_s7lock_guc_hardening.py`:** that suite covers a different lock —
`lock_timeout` GUC hardening on the DB connection itself (S7), not the chart advisory lock. Not to
be confused with the chart-level `pg_try_advisory_lock` mechanism above.

---

## 2. Fleet cap (concurrent build limit across charts)

**Code:** `runner.py:95` —

```python
_MAX_CONCURRENT_RUNS = int(os.environ.get("ORCHESTRATOR_MAX_CONCURRENT_RUNS", "6"))
```

Default **6** concurrent runs, overridable via env var. The comment above it documents the budget
math: Cloud SQL `max_connections=50`, ~33 available to the orchestrator; one run holds 1 main
connection + up to `_WORKER_LIMIT` (default 4, `ORCHESTRATOR_WORKER_LIMIT`) worker connections
(one per concurrently-executing DAG-parallel asset within that run), so worst case per run =
1+4=5; `6 × 5 = 30 ≤ ~33`.

**Enforcement** — `runner.py:429-435` + `1082-1090`:

```python
def count_other_running_runs(cur, run_id: str) -> int:
    """Apply the fleet cap without making a crashed run block its own retry."""
    cur.execute(
        "SELECT count(*) AS active FROM build_runs WHERE state='running' AND id<>%s",
        (run_id,),
    )
    return int(cur.fetchone()["active"])
...
active_count = count_other_running_runs(cur, run_id)
if active_count >= _MAX_CONCURRENT_RUNS:
    logger.warning(...)
    conn.close()
    sys.exit(3)
```

This runs **before** the chart advisory lock is acquired, so a run that would exceed the fleet
cap never touches the lock or any asset state — it exits `3` (defer) cleanly. The `id<>%s`
exclusion is deliberate: a crashed/retried run does not count itself, so a legitimate retry of
the same `run_id` is never blocked by its own prior (already-terminal or orphaned) attempt.

**Live DB check** (read-only, aggregates only, canonical instance):
```
$ source dbenv.sh; psql -Atq -c "SELECT state, count(*) FROM build_runs GROUP BY state ORDER BY 2 DESC;"
failed|429
completed|369
stopped|19
```
No `running`/`planned`/`paused` rows exist at time of audit — the fleet cap is currently slack
(0/6 active). This confirms `build_runs.state` really does reach `failed`/`completed`/`stopped`
in production, not merely in test fixtures.

**Unit proof:** `pipeline/orchestrator/tests/test_run_claim_and_global_lock.py::
test_concurrency_cap_does_not_count_the_retrying_run_itself` — PASSED (see §7 below for the run).

---

## 3. `build_runs` lifecycle

**Table:** `build_runs` (migration `platform/supabase/migrations/171_build_runs.sql`, confirmed
live via information_schema on the read-only replica):

```
$ source dbenv.sh
$ psql -Atq -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='build_runs' ORDER BY ordinal_position;"
id|uuid  chart_id|uuid  scope|text  scope_target|text  action|text  state|text  plan|jsonb
current_asset_id|text  triggered_by|text  created_at|timestamptz  started_at|timestamptz
ended_at|timestamptz  pause_requested_at|timestamptz  stop_requested_at|timestamptz
last_error|text  plan_manifest|jsonb  plan_manifest_digest|text

$ psql -Atq -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='build_runs'::regclass AND contype='c';"
build_runs_action_check       CHECK (action = ANY (ARRAY['build','update','rebuild','cascade']))
build_runs_state_check        CHECK (state = ANY (ARRAY['planned','running','paused','completed','stopped','failed']))
build_runs_plan_manifest_pair_check  CHECK ((plan_manifest IS NULL) = (plan_manifest_digest IS NULL))
build_runs_plan_manifest_digest_check CHECK (plan_manifest_digest IS NULL OR plan_manifest_digest ~ '^[0-9a-f]{64}$')
build_runs_plan_manifest_object_check CHECK (plan_manifest IS NULL OR jsonb_typeof(plan_manifest)='object')
build_runs_scope_check        CHECK (scope = ANY (ARRAY['global','layer','asset','asset_set']))
```

**States:** `planned → running → {completed | stopped | failed}`, with `paused` as an
intermediate pause state. Transitions found in `runner.py`:

| Transition | Where | Trigger |
|---|---|---|
| `planned` → `running` | `claim_runnable_run` (`runner.py:415-426`), atomic CAS `UPDATE ... WHERE state IN ('planned','running') RETURNING id` | dispatcher creates row `planned`; orchestrator process claims it after locks acquired |
| `running`/`planned`/`paused` → `failed` | `_terminalize_preflight_failure` (`runner.py:325-340`) | frozen-manifest validation fails (`_verify_registry_still_matches_manifest` / `_verify_sidecar_code_matches_manifest`, or tamper) — also cascades `build_run_assets` rows still `queued` → `aborted` in the same statement (CTE) |
| running → `completed` | `mark_run_state(..., 'completed', ...)` (`runner.py:136,146`) | all planned assets reached a terminal accepted state |
| running → `failed` | `mark_run_state(..., 'failed', ...)` | any asset lands in `error` (or, per the rollup tests, `incomplete` treated as failure — see §7) |
| running → `stopped` | operator-requested stop (`stop_requested_at` column + poll loop) | graceful stop signal honored between assets/sub-steps |

`build_run_assets` (per-asset row inside a run) has its own `state` column: `queued → building →
{complete | error | aborted}`, with `disposition` (`'build'`) and `output_changed` (bool, whether
this asset's output digest actually changed vs the prior receipt) recorded per asset —
`asset_runner.py:1203-1208, 1249-1252`.

`asset_throughput` (per-chart, per-asset persistent state, independent of any one run) has states
`dormant, building, lit, stale, error, incomplete` (`asset_throughput_state_check`, confirmed live
— see §4/§7). `service_ok` also appears as an allowed dependency-satisfied state in `runner.py:707`
(`state IN ('lit','service_ok')`) for service-kind assets, though it is not in the CHECK constraint
list returned above — worth flagging as a possible drift point for the DAG-guard packet, not
something this packet re-verified further (out of Domain C's direct scope; noted for Domain H/the
final synthesis).

**What marks success/failure/partial:**
- **Success (asset-level):** `asset_throughput.state='lit'`, gated by (a) the writer completing
  without exception, (b) the registry's declared `integrity_check_sql` (if any) passing
  post-write, and — for `has_substeps=true` writers reporting 0 rows this run — (c) the
  SATYA-DĪPA completeness re-probe (§7).
- **Partial:** `asset_throughput.state='incomplete'` — a `has_substeps=true` writer reported 0
  rows this run, data is present from earlier partial progress, but its own `plan_substeps(ctx)`
  still reports remaining substeps. This state deliberately does NOT satisfy the
  `state IN ('lit','service_ok')` dependency-satisfied allowlist, so downstream assets stay
  blocked (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1; migration 474 added the value to
  `asset_throughput_state_check`).
- **Failure (asset-level):** `asset_throughput.state='error'` via `mark_asset_error` — sets
  `last_error`, updates `build_run_assets.state='error'`, commits, emits
  `asset.state_change` event.
- **Failure (run-level):** `build_runs.state='failed'` — either a preflight rejection
  (`_terminalize_preflight_failure`) before any asset runs, or a rollup decision after the DAG
  walk that treats any `error`/`incomplete` asset as a failed run (see the rollup test names in
  §7, e.g. `test_run_reported_failed_when_a_writer_landed_incomplete`).

---

## 4. `_verify_registry_still_matches_manifest`

**Code:** `runner.py:343-373`. Runs during run start, immediately after `validate_frozen_run_manifest(run)`
and before `_verify_sidecar_code_matches_manifest`, before any lock is acquired and before any
asset state is touched (`runner.py:1038-1040`).

**What it checks:** for every `asset_id` in the frozen plan, re-reads the **live**
`asset_registry` row (`scope`, `depends_on`, `natural_key_partition`, and a derived
`has_cowriters` flag — whether another active writer shares the same `target_table`) and compares
it against the values captured in the **frozen manifest at dispatch time**
(`frozen.asset_scopes`, `frozen.asset_deps`, `frozen.asset_partitions`,
`frozen.asset_has_cowriters`). `depends_on` is compared **unordered** (both sides sorted) because
dependency ORDER was never a real invariant — only membership. Any mismatch, or the asset no
longer being registered at all, raises `ValueError`.

**When it runs:** every single run start, unconditionally, before `claim_runnable_run`.

**On mismatch:** the `ValueError` is caught by the caller (`runner.py:1041-1049`), which calls
`_terminalize_preflight_failure(cur, run_id=run_id, message=...)` — this marks the run `failed`
(and cascades any still-`queued` `build_run_assets` rows to `aborted`) and the process exits `1`.
No writer runs, no lock is acquired, no state is mutated beyond the terminal failure record. This
is the "fail closed if mutable registry config changed after dispatch, before work starts"
behavior documented in the function's own docstring — it exists specifically to prevent a run
dispatched against one DAG shape from silently executing against a since-mutated
`asset_registry`.

---

## 5. `_verify_sidecar_code_matches_manifest`

**Code:** `runner.py:376-392`. Runs immediately after `_verify_registry_still_matches_manifest`,
same preflight block, same failure path.

**What it checks:** for every `asset_id` in the frozen plan, computes the **actual, currently
running** code's digest — `get_writer_source_hash(asset_id)` for a registered `@register`'d
writer, or a shared `get_probe_source_hash()` for assets with no writer (probe-only /
verify-then-regenerate path) — and compares it against `frozen.expected_code_digests[asset_id]`,
the digest that was captured and pinned into the manifest **at dispatch time** (presumably by the
web/API layer that created the `build_runs` row). Mismatch raises `ValueError`.

**Purpose (from the function's docstring):** "Reject web/job image skew before any asset state or
output is mutated." This is exactly the deploy-lag hazard named in the charter's F6 finding — if
the `brahma-pipeline` job image is stale relative to what dispatched the run, this check is the
mechanism that refuses to silently run stale code under a fresh-looking manifest.

**On mismatch:** identical failure path to §4 — `_terminalize_preflight_failure`, run marked
`failed`, exit `1`, no writer executes, no state mutated.

**Regression coverage confirmed live:** `pipeline/orchestrator/tests/test_frozen_run_manifest.py`
includes `test_tampered_manifest_is_rejected_before_any_writer_can_run`,
`test_registry_dependency_drift_fails_closed_instead_of_replanning_the_run`, and
`test_registry_dependency_reorder_alone_does_not_fail_preflight` (the sort-both-sides case) — all
PASSED in this session's run (§7).

---

## 6. Writer registration (`@register('<asset_id>')`)

**Code:** `pipeline/orchestrator/writers/__init__.py:160-251`.

- `_REGISTRY: dict[str, type[WriterBase]] = {}` — module-level dict, `asset_id → writer class`.
- `register(asset_id)` is a decorator factory: on class decoration it validates
  `issubclass(cls, WriterBase)`, then inserts into `_REGISTRY`. A **duplicate** registration for
  the same `asset_id` is tolerated only when it is genuinely the same class re-importing
  (benign dual-import/test-collection case, matched by identity or by
  `__name__`+trailing-module-segment equality) — a **different** class claiming the same
  `asset_id` raises `ValueError('duplicate writer registration for asset_id=...')`. This preserves
  the one-writer-per-`asset_id` invariant even under CI's sometimes-dual-path module collection.
- **Discovery:** `_auto_discover()` (guarded by a `threading.Lock` so concurrent worker threads
  calling `get_writer()` during parallel DAG execution cannot race a duplicate-registration
  error) walks `pkgutil.iter_modules(pkg.__path__)` over the `writers/` package — i.e. every
  `.py` file directly under `pipeline/orchestrator/writers/` except ones starting with `_` or the
  `tests` subpackage — and `importlib.import_module()`s each one. Because each writer module
  calls `@register(...)` at import time (module-level class decoration), importing the module is
  sufficient to populate `_REGISTRY`; there is no separate manual registration list.
  **Hard-fails on import error** — "registration gap is not silently OK" (function's own comment).
- Triggered lazily on first `get_writer()` call, or explicitly via `discover_all()` — which
  `runner.py`'s `main()` calls unconditionally at the top of every run
  (`runner.py:1008-1009`, comment: `"D1: ensure all writer modules are imported"`).
- `get_writer(asset_id)` calls `_auto_discover()` then returns `_REGISTRY.get(asset_id)`.

**Live proof (this session, no DB needed — pure import):**
```
$ python3 -c "
from pipeline.orchestrator.writers import discover_all, list_writers
discover_all()
w = list_writers()
print('total writers registered:', len(w))
print('ka_* writers registered:', len([k for k in w if k.startswith('ka_')]))
"
total writers registered: 123
ka_* writers registered: 22
```
The 22 registered `ka_*` writers are exactly: `ka_avadhi, ka_bhavishya_lekha, ka_dasha_kala,
ka_gochara, ka_gochara_resonance, ka_gochara_v3_century_materialize, ka_graha_sancara,
ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_kota_chakra, ka_kshetra, ka_moorti_nirnaya,
ka_muhurta_seva, ka_sangam, ka_sudarshana_varsha, ka_taranga, ka_tithi_pravesha, ka_tulana,
ka_vedha_gochara, ka_vighnakara, ka_yojaka`. This is exactly 22, matching CLAUDE.md §E's "22
active `ka_*` identities" claim. `ka_gochara_sweep.py` exists as a file under `writers/` but does
**not** appear in the registered set — consistent with CLAUDE.md's "`ka_gochara_sweep` is retired,
protected history... never rebuilt" (the file presumably has no `@register` call, or is excluded
some other way; this packet did not open `ka_gochara_sweep.py` itself to confirm which — flagged
as a one-line follow-up for whoever owns F3/the DAG reconciliation, not re-derived here to avoid
scope creep into that packet's territory).

**Unit proof:** `writers/__tests__/test_writer_registry.py` (register/get_writer/run_asset
transitions) and `writers/__tests__/test_frozen_contract_stability.py` (register decorator
idempotency + genuine-conflict rejection + the frozen `ContextSpec`/`WriterResult`/`SubStep`
shapes) — both suites PASSED in this session (§7).

---

## 7. Substep plans (`plan_substeps` / `run_substep`) and the SATYA-DĪPA no-op-completion fix

**Contract (`writers/__init__.py`):** a "heavy" writer overrides `plan_substeps(ctx) ->
list[SubStep]` and `run_substep(ctx, step) -> WriterResult`; the base class then gives it a
working `run()` for free (drives its own substeps serially). `has_substeps` on the class /
`asset_registry.has_substeps` is an advisory flag that mirrors this.

**Driver:** `_drive_substeps` (`asset_runner.py:707-`), the actual orchestrator-side driver used
during a real run (as opposed to a writer's own free `run()` fallback used e.g. by CLI callers):
- calls `writer.plan_substeps(ctx)` once to get the full chunk list;
- for each substep not already in `completed_keys` (resume set): runs inside
  `SAVEPOINT writer_exec`; on exception, `ROLLBACK TO SAVEPOINT writer_exec` and re-raise (caller
  marks the whole asset `error`; prior committed substeps stay durable); on success, `RELEASE
  SAVEPOINT`, accumulate `rows_inserted`/`rows_updated`, **update
  `asset_throughput.last_built_at` + cumulative `rows_written` as a heartbeat**, commit (unless
  `defer_commits=True`, used when a post-write integrity check must gate the whole batch
  atomically), and emit an `asset.substep` SSE event.
- Already-completed keys (from a resumed run) are skipped with a `skipped: true` substep event,
  not re-executed — this is the "mid-asset resume via `completed_keys`" mechanism named in
  `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §3 Phase 2.

**Live DB check:** `asset_registry.has_substeps = true` for **26** rows (`SELECT count(*) FROM
asset_registry WHERE has_substeps = true` on the read-only replica) — the heavy-writer population
across all layers, of which the 9 GA + several `ka_*`/`bo_*`/`mi_*` writers are members (this
packet did not further break this count down by layer; that is Domain-A/T1 territory).

**The SATYA-DĪPA no-op-completion fix, verified in the actual code (`asset_runner.py:1100-1186`):**

This is the authorized freeze exception §7.1 in `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`. Before
this fix, `_run_data_writer` would reclassify ANY 0-rows-this-run "dormant" result to "lit"
whenever the target table had any rows present at all — with no check that the writer's own
substep plan had actually finished. The current code:

```python
if final_state == 'dormant':
    present = _data_rows_present(conn, cur, asset_id, chart_id)
    if present is not None and present > 0:
        # rows present is necessary but not sufficient — check has_substeps
        cur.execute("SELECT has_substeps FROM asset_registry WHERE asset_id = %s", (asset_id,))
        has_substeps = bool(...)
        plan_complete = True
        if has_substeps:
            cur.execute("SAVEPOINT noop_completeness_probe")
            try:
                remaining = writer.plan_substeps(ctx)          # ← re-invokes the writer's OWN plan
                remaining_count = len(remaining)
                plan_complete = remaining_count == 0
                cur.execute("RELEASE SAVEPOINT noop_completeness_probe")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT noop_completeness_probe")
                plan_complete = False   # conservatively incomplete on error

        if plan_complete:
            final_state = 'lit'          # genuinely nothing left — promote
            emit_event({"type": "asset.noop_completion", ...})
        else:
            final_state = 'incomplete'   # something left — hold, do NOT unblock downstream
            emit_event({"type": "asset.noop_completion_rejected", ...})
```

This exactly matches CLAUDE.md §N.8's own description: "the orchestrator no-op-completion
promotion predicate asserted substep-plan completeness while only ever checking row presence."
The fix re-invokes `plan_substeps(ctx)` (a read-only planning call by contract) inside its own
savepoint immediately after the round's own `_drive_substeps` call, and only promotes to `'lit'`
if the writer's own plan agrees nothing remains — otherwise it lands `'incomplete'` (a state that
deliberately does not satisfy the `state IN ('lit','service_ok')` dependency-satisfied check
elsewhere in the orchestrator, so downstream assets correctly stay blocked). `has_substeps=false`
(light writers) skip the check entirely, preserving prior behavior unchanged.

**Relationship to CLAUDE.md §N.8 item 4** ("a verification flag must have a real detector behind
it, or be null"): this is precisely that principle applied one layer down in the build system's
own success signal — the fix replaces a proxy check ("rows present") with the actual claim being
asserted ("substep plan finished"), which is the general pattern §N.8 generalizes from the
narration-layer version in §N.7 item 4.

---

## 8. Prove end-to-end — test suite run (real command, real output)

Ran the exact test files named in this packet's brief plus their closest siblings
(`test_d16_state_write_defect.py` — the direct SATYA-DĪPA regression suite —
`test_run_claim_and_global_lock.py`, `test_frozen_run_manifest.py`, `test_s7lock_guc_hardening.py`,
`writers/__tests__/test_writer_registry.py`, `writers/__tests__/test_frozen_contract_stability.py`),
using the project's own venv interpreter, against the **checked-out worktree's actual code**
(no DB required for these — all use `FakeConn`/`FakeCursor`/`Cursor`/`Connection` mock harnesses
that simulate SQL call sequences and assert on them, i.e. these are true unit tests of the
orchestrator's control-flow logic, not integration tests against a real Postgres):

```
$ cd platform/python-sidecar
$ /Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3 -m pytest \
    tests/test_orchestrator_substeps.py \
    tests/test_orchestrator_rebuild_probe.py \
    tests/test_orchestrator_run_state_rollup.py \
    tests/test_asset_runner_provenance_hashes.py \
    tests/test_asset_runner_zero_rows.py \
    tests/test_ga_orchestrator_conformance.py \
    tests/test_orchestrator_gate.py \
    tests/test_d16_state_write_defect.py \
    -v
...
============================= 105 passed in 1.23s ==============================
```

```
$ /Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3 -m pytest \
    pipeline/orchestrator/tests/test_run_claim_and_global_lock.py \
    pipeline/orchestrator/tests/test_frozen_run_manifest.py \
    pipeline/orchestrator/tests/test_s7lock_guc_hardening.py \
    pipeline/orchestrator/writers/__tests__/test_writer_registry.py \
    pipeline/orchestrator/writers/__tests__/test_frozen_contract_stability.py \
    -v
...
============================== 36 passed in 0.37s ==============================
```

**Total: 141/141 passed, 0 failures, 0 skips**, covering (by name, all individually confirmed
PASSED above): substep drive/resume/heartbeat/integrity-defer, probe green/down/regenerate
dispatch paths, run-state rollup (failed-asset → failed-run, incomplete → failed-run, dormant-only
→ completed-run), upstream-hash provenance including the D-NATIVE-07 service-dependency
accommodation, zero-rows dormant/lit classification, all 9 GA writers' orchestrator-conformance
(resolve, has_substeps flags, injected-conn threading, birth-params handling), DAG-gate
transitive-failure blocking, the fleet-cap self-exclusion test, frozen-manifest tamper/drift
rejection (both of §4 and §5's functions), the S7 lock-timeout GUC hardening, writer registration
+ frozen-contract shape stability, and the full SATYA-DĪPA D-1.6 regression suite (§7 above) —
including the two tests explicitly designed to fail against pre-fix code and pass against fixed
code (`test_satyadipa_d16_preserved_through_completeness_check`,
`test_satyadipa_partial_substep_plan_with_rows_present_not_lit`).

**Because these are mock-cursor unit tests, not a real-Postgres integration proof, this packet
additionally ran a real, disposable, local Postgres 15 instance** specifically to exercise the one
mechanism whose correctness genuinely depends on real Postgres session/lock semantics and cannot
be meaningfully asserted with a fake cursor: the advisory lock in §1. That proof (mutual exclusion
on the same chart_id, non-exclusion across different chart_ids, and auto-release on session close)
is reproduced in full in §1 above. The instance was started, used for ~10 seconds of queries, and
fully torn down (`pg_ctl stop -m fast` + `rm -rf` on the temp data directory) before this report
was written — confirmed no leftover process (`ps aux | grep kala_audit` → none) or file (`ls /tmp |
grep kala_audit` → none).

---

## Verdict: READY

**Scope of this verdict:** the orchestrator/build-path mechanics named in this packet — chart
advisory locking, fleet cap, `build_runs`/`build_run_assets`/`asset_throughput` lifecycle, the two
preflight verify functions, writer registration/discovery, and substep-plan partial-completion
tracking including the SATYA-DĪPA fix — are real, load-bearing, and behave as documented. This is
NOT a verdict on data completeness, DAG correctness (F3), privilege coverage (F4), or any other
packet's territory.

**What would have made this NOT READY (and did not happen):**
- The advisory-lock proof failing to block Session B, or Session C also blocking (would mean the
  lock is accidentally global rather than per-chart) — did not happen; f/t/t/t exactly as
  predicted.
- Any of the 141 named orchestrator unit tests failing, especially
  `test_satyadipa_partial_substep_plan_with_rows_present_not_lit` (which is specifically
  documented to fail against pre-fix code) — all 141 passed.
- `_verify_registry_still_matches_manifest` or `_verify_sidecar_code_matches_manifest` not
  actually being wired into the run-start path, or catching their `ValueError` silently instead of
  terminalizing the run — confirmed both are called unconditionally at `runner.py:1039-1040`
  inside a `try` whose `except ValueError` path calls `_terminalize_preflight_failure` and exits
  non-zero; not a no-op.
- The 22 `ka_*` writer count not matching CLAUDE.md's stated campaign denominator, or
  `discover_all()` silently swallowing an import failure — `_auto_discover()` explicitly
  re-raises on any import exception ("registration gap is not silently OK"); live count came back
  exactly 22.
- `build_runs.state` in the live read-only replica showing values outside the CHECK constraint's
  six-state vocabulary, or zero real rows ever reaching `completed`/`failed` (i.e. the lifecycle
  being untested in anger) — live query showed 429 `failed` + 369 `completed` + 19 `stopped`, real
  production history exercising every terminal state.

**One item flagged and resolved (minor, non-blocking):** `runner.py:707`, `staleness.py:83,138`
all check the dependency-satisfied allowlist `state IN ('lit','service_ok')`, and
`asset_runner.py:105-108`'s comment claims service assets are "surfaced as `state='service_ok'`."
Traced this fully:

```
$ grep -rn "'service_ok'" pipeline/ --include='*.py' | grep -v tests
runner.py:707       ... state IN ('lit','service_ok') LIMIT 1   [READ]
staleness.py:83     (docstring) "The UPDATE matches state IN ('lit', 'service_ok')"  [READ]
staleness.py:138    ... AND state IN ('lit', 'service_ok')       [READ]
asset_runner.py:105 # surfaced as state='service_ok' (comment only, no write)
asset_runner.py:108 # 'service_ok' is what "lit" means for a service. (comment only)

$ source dbenv.sh; psql -Atq -c "SELECT state, count(*) FROM asset_throughput GROUP BY state ORDER BY 2 DESC;"
lit|163  stale|73  error|28  dormant|3  incomplete|1
```

`'service_ok'` is **read-checked in three places but never written anywhere** — the actual
service-health-probe write path (`_run_service_health_probe`, §3/§1's `_run_service_health_probe`
region, `asset_runner.py:634-681`) sets `state='lit'` on a GREEN probe, not `'service_ok'`. This
is confirmed both by grep (no `SET ... state = 'service_ok'` or equivalent anywhere in
non-test code) and by the live replica (zero rows in any state outside the six values in
`asset_throughput_state_check`, which itself does not list `'service_ok'` as valid). Migration
`377_ka_dasha_kala_target_floor.sql`'s own comment calls this `READY_STATES = ['lit','service_ok']`
and explains the actual production workaround: `ka_dasha_kala` (a per-chart service writer) is
given `target_floor=0` specifically so the ordinary zero-rows-is-complete logic promotes it to
`'lit'` rather than relying on a `'service_ok'` value that the codebase never produces. **Net
effect: harmless today** (every real service asset reaches `'lit'` through the `zero_rows_is_complete`
path, and the allowlist checks are a superset that includes an unused member, not a subset that
excludes a used one) but it is vestigial/dead code across three files and a stale comment — a
one-line cleanup for whoever owns the DAG/staleness surfaces, not a readiness blocker for this
packet.
