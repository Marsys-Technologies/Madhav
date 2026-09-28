---
artifact: PHASE0_2_P0_SAFETY_EVIDENCE
version: "1.0"
status: CURRENT
date: 2026-09-22
campaign: Kāla (L3) pre-elevation setup — Phase 0.2
worktree: /Users/Dev/madhav-l3/setup (branch l3/kala-setup-phase01)
does_not_authorize: >
  This artifact authorizes NOTHING beyond recording executed evidence. It does
  not authorize an expensive Kāla rebuild trial, a production write, a schema
  or migration change, a change to the FROZEN orchestrator contract, an
  elevation decision, or any edit under platform-mcp/src/tools/kala_views/.
  It records that two named P0 hazards were tested by execution and what the
  tests found. Proof tier (F24): computational correctness only — a passing
  test is not demonstrated product value.
---

# Phase 0.2 — P0 safety hazards: executed evidence

## §1 What the strategy requires

`00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`
line 222, §5 "Specific redesign candidates, in study order", row P0, verbatim:

> | P0 Kshetra planner and Bhavishya replacement | Kshetra planning deletes data
> before resume filtering. Bhavishya's empty-input early return follows deletion
> but precedes its outcome-preservation guard. | Make planning read-only; move
> replacement into the owned execution partition; preserve outcome identity
> independently of rebuildable projection, including empty results. | Zero
> planning/dry-run mutations; crash/resume and empty-generation tests; restore
> prior data/outcomes. Repair before any expensive rebuild trial. |

Both hazards APPEARED repaired on a prior read of the code. Per CLAUDE.md §N.8
(Earned-Signal Principle) a fix with no detector behind it is null, not green.
This phase makes the claim green with executed detectors, or reports it open.

Code under test (read in full):
- `platform/python-sidecar/services/ka_kshetra/writer.py` (2,629 lines) —
  `plan_substeps` at :277, `run_substep` at :489, `_run_prepare_replace` at :520,
  `_delete_prior_rows` at :2420, `_OWNED_TABLES` at :2474.
- `platform/python-sidecar/pipeline/orchestrator/writers/ka_kshetra.py` — the
  52-line `@register('ka_kshetra')` shim; all logic lives in `services/`.
- `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py`
  (594 lines) — outcome read + `FOR UPDATE` at :114-141, empty-input branch at
  :202-219, the pre-DELETE preservation assertion at :345, DELETE/UPDATE/INSERT
  at :396-431.
- `platform/python-sidecar/pipeline/orchestrator/db.py:46-70` — the build-session
  connection factory; documents the ~20-minute pure-CPU substep that
  `idle_in_transaction_session_timeout = 1800000` protects. The harness
  connection mirrors its `row_factory=dict_row` + `statement_timeout = 0`.
- FROZEN contract: root `CLAUDE.md` §N.2 and
  `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2 — writers run on
  `ctx.db_conn` and NEVER commit, roll back or close it.

## §2 The harness

### §2.1 How it was built

Bootstrap script, committed alongside this artifact:
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/phase0_2_harness_bootstrap.sh`

- Disposable PostgreSQL 15.17 (Homebrew) at `/tmp/kp0`, port 59510, `fsync=off`.
  Production is 15.18 — verified by `SHOW server_version` — so the harness is
  one patch release behind, same major.
- Production was READ-ONLY throughout: `pg_dump --schema-only`, `pg_get_functiondef`,
  and `\copy (SELECT …) TO`. No write statement was issued against production at
  any point. The production dbenv exports `PGOPTIONS=-c default_transaction_read_only=on`;
  this was independently confirmed when a harness command that inherited it was
  refused with `ERROR: cannot execute COPY FROM in a read-only transaction`. The
  harness `psql` wrapper and `tests/l3/_p0_harness.connect()` both explicitly
  clear every `PG*`/`DATABASE_URL` variable so a harness call can never reach
  production and vice versa.
- 44 tables dumped table-scoped; 86 non-extension `public` functions dumped
  separately; extensions `pgcrypto`, `pg_trgm`, `uuid-ossp` created locally.
  `vector` (pgvector 0.8.1 in production) is NOT available for postgresql@15 on
  this machine — confirmed none of the 44 carried tables has a `vector` column,
  so nothing under test depends on it.

### §2.2 The trigger-function trap, measured

The trap is real and was reproduced before it was fixed. A table-scoped dump
carries `CREATE TRIGGER` but not the functions:

```
$ grep -c '^CREATE TABLE'   schema_tables.sql   → 39
$ grep -c 'CREATE TRIGGER'  schema_tables.sql   → 14
$ grep -c 'CREATE FUNCTION' schema_tables.sql   → 0
```

Restoring that dump alone produced **20 errors, 14 of them exactly this**:

```
psql:schema_tables.sql:3474: ERROR:  function public.l2_data_plane_reject_immutable_change() does not exist
psql:schema_tables.sql:3481: ERROR:  function public.l2_data_plane_capture_row() does not exist
psql:schema_tables.sql:3495: ERROR:  function public.l2_data_plane_guard_generation_change() does not exist
psql:schema_tables.sql:3502: ERROR:  function public.l2_data_plane_guard_active_mutation() does not exist
psql:schema_tables.sql:3537: ERROR:  function public.l2_data_plane_guard_completed_run_rows() does not exist
psql:schema_tables.sql:3551: ERROR:  function public.nirmana_invalidate_chart_receipts() does not exist
psql:schema_tables.sql:3558: ERROR:  function public.phala_anchors_set_identity() does not exist
psql:schema_tables.sql:3565: ERROR:  function public.reject_build_run_manifest_mutation() does not exist
```
(the other 6 errors were FK targets for 5 tables not yet in the dump —
`asset_registry`, `brahma_event_ontology`, `profiles`, `bg_transit_rules`,
`chart_grants` — which were then added, bringing the dump to 44 tables /
15 triggers.)

### §2.3 Which functions were carried, and how presence was verified

Functions were loaded FIRST, under `SET check_function_bodies = false` (their
bodies reference tables the table dump creates afterwards). **11 functions
matter** — 8 referenced directly by a `CREATE TRIGGER`, plus 3 helpers those
bodies call:

| # | function | role |
|---|---|---|
| 1 | `l2_data_plane_capture_row` | trigger fn — L2 governed capture (`bodha_pratijna`, `bodha_msr_signals`) |
| 2 | `l2_data_plane_guard_active_mutation` | trigger fn — L2 protected-table mutation guard |
| 3 | `l2_data_plane_guard_completed_run_rows` | trigger fn — run-rows immutability |
| 4 | `l2_data_plane_guard_generation_change` | trigger fn — generation immutability |
| 5 | `l2_data_plane_reject_immutable_change` | trigger fn — 5 immutable data-plane tables |
| 6 | `nirmana_invalidate_chart_receipts` | trigger fn — `charts` → `asset_freshness` invalidation |
| 7 | `phala_anchors_set_identity` | trigger fn — computes `phala_anchors.anchor_id` |
| 8 | `reject_build_run_manifest_mutation` | trigger fn — `build_runs` manifest immutability |
| 9 | `l2_data_plane_strip_volatile` | helper called by #1 |
| 10 | `l2_data_plane_jsonb_has_nonfinite` | helper called by #1 |
| 11 | `phala_anchor_identity` | helper called by #7 |

(A 9th trigger function, `nirmana_invalidate_registry_receipts`, arrived with
`asset_registry` and is also present — 15 triggers / 9 distinct functions total.)

**Presence** — after the functions-first load, `schema_tables.sql` restored with
**0 errors** and all 15 triggers exist:

```
$ hp -Atc "SELECT c.relname||' | '||t.tgname||' | '||p.proname||' | enabled='||t.tgenabled::text AS r
           FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_proc p ON p.oid=t.tgfoid
           JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE NOT t.tgisinternal AND n.nspname='public' ORDER BY r;"
asset_registry | nirmana_registry_receipt_invalidation | nirmana_invalidate_registry_receipts | enabled=O
bodha_msr_signals | l2_data_plane_capture | l2_data_plane_capture_row | enabled=O
bodha_msr_signals | l2_data_plane_mutation_guard | l2_data_plane_guard_active_mutation | enabled=O
bodha_pratijna | l2_data_plane_capture | l2_data_plane_capture_row | enabled=O
bodha_pratijna | l2_data_plane_mutation_guard | l2_data_plane_guard_active_mutation | enabled=O
build_runs | trg_build_runs_manifest_immutable | reject_build_run_manifest_mutation | enabled=O
charts | nirmana_chart_receipt_invalidation | nirmana_invalidate_chart_receipts | enabled=O
data_plane_l2_producer_generations | l2_data_plane_generation_immutable | l2_data_plane_guard_generation_change | enabled=O
l2_data_plane_asset_outputs | l2_data_plane_outputs_immutable | l2_data_plane_reject_immutable_change | enabled=O
l2_data_plane_input_bind_receipts | l2_data_plane_bind_receipts_immutable | l2_data_plane_reject_immutable_change | enabled=O
l2_data_plane_partition_contexts | l2_data_plane_partition_contexts_immutable | l2_data_plane_reject_immutable_change | enabled=O
l2_data_plane_row_snapshots | l2_data_plane_snapshots_immutable | l2_data_plane_reject_immutable_change | enabled=O
l2_data_plane_run_intents | l2_data_plane_run_intents_immutable | l2_data_plane_reject_immutable_change | enabled=O
l2_data_plane_run_rows | l2_data_plane_run_rows_immutable | l2_data_plane_guard_completed_run_rows | enabled=O
phala_anchors | phala_anchors_identity_biu | phala_anchors_set_identity | enabled=O
```

**Firing** — presence is not execution (§N.8). Four live proofs:

*A / B — the L2 mutation guard executes and raises (`bodha_pratijna`, `bodha_msr_signals`):*
```
$ hp -Atc "INSERT INTO bodha_pratijna (chart_id) VALUES ('482012f1-…');"
ERROR:  protected L2 INSERT requires direct data_plane_builder authentication
CONTEXT:  PL/pgSQL function l2_data_plane_guard_active_mutation() line 16 at RAISE
$ hp -Atc "INSERT INTO bodha_msr_signals (chart_id) VALUES ('482012f1-…');"
ERROR:  protected L2 INSERT requires direct data_plane_builder authentication
CONTEXT:  PL/pgSQL function l2_data_plane_guard_active_mutation() line 16 at RAISE
```

*C — FK/constraint layer intact:*
```
ERROR:  insert or update on table "l2_data_plane_run_intents" violates foreign key
        constraint "l2_data_plane_run_intents_chart_id_asset_id_generation_id__fkey"
```

*D — the `charts` AFTER-UPDATE trigger executes and writes through to `asset_freshness`:*
```
BEGIN; INSERT INTO asset_freshness (…,'fresh','[]'::jsonb,'v1');
 BEFORE: fresh reasons=[]
UPDATE charts SET birth_time = birth_time + interval '1 second' WHERE id='482012f1-…';
 AFTER : stale reasons=["chart_inputs_changed"]
ROLLBACK;
```

*E — the `phala_anchors` BEFORE-INSERT identity trigger executes:* an INSERT that
supplied NO `anchor_id` was rejected on a DIFFERENT column, and the rejection's
`DETAIL` shows the trigger had already computed the identity:
```
ERROR:  null value in column "derivation_ledger_jsonb" … violates not-null constraint
DETAIL:  Failing row contains (a51fa0a3-2c49-57d1-84b1-540fea623e52, 482012f1-…, harness, …)
                               ^^^^^^^^ anchor_id, computed by phala_anchors_set_identity
```

Seeding note, stated rather than hidden: `bodha_pratijna` and
`bodha_msr_signals` rows were seeded with `ALTER TABLE … DISABLE TRIGGER USER`
around the `\copy`/INSERT and `ENABLE` immediately after, because the production
guard refuses any write not authenticated as `data_plane_builder` inside an
admitted L2 generation. The guards are **enabled for every writer call the tests
make** — and both writers only ever READ those tables.

Honest gaps in harness fidelity:
- 9 of the 86 dumped functions failed to load — all `planner_managed_prashna_jobs`
  / `planner_inquiry_lifecycles` / `chart_dashas` row-typed functions whose tables
  were deliberately not carried. None is a trigger function and none is reachable
  from either writer.
- One production profile row was replaced with a synthetic `profiles` row
  (`id` only, `role='guest'`) to satisfy `charts.client_id` — no production PII
  was copied to the harness.

### §2.4 Teardown proof

Executed and recorded at §6 "Teardown proof" below: server stopped, `pg_isready`
returns `no response` (exit 2), nothing listening on 59510, no postgres process
for the data dir, and `/tmp/kp0` removed.

## §3 Kshetra planning read-only

### §3.1 The test

`platform/python-sidecar/tests/l3/test_ka_kshetra_p0_planning_readonly.py`
(helpers in `platform/python-sidecar/tests/l3/_p0_harness.py`), following the
existing `tests/l3/` convention (env-var DSN, skip when unreachable).

It calls the REAL `KaKshetraWriter().plan_substeps(ctx)` on a real connection.
Three independent detectors:

- **D1 — `txid_current_if_assigned()` stays NULL.** Postgres assigns a
  transaction id lazily, only when a tuple is first modified; an INSERT later
  rolled back still assigns one. `txid_current()` is deliberately NOT used — it
  would assign an xid and destroy the measurement.
- **D2 — the same call inside `SET TRANSACTION READ ONLY`.** Any write statement
  raises `25006` regardless of how many rows it would have matched.
- **D3 — per-chart row-count + `md5` content digest of every writer-owned table**,
  read from the writer's own `_OWNED_TABLES` declaration (so a table added to the
  writer's replacement set is covered automatically), plus `build_substep_progress`
  and `bodha_pratijna`.

**Measured limits, recorded rather than assumed.** D1 and D3 are BLIND to a write
statement that modifies zero rows — Postgres assigns no xid for a no-op DELETE and
the digest does not move either. Every D1/D3 test therefore seeds a committed
sentinel row first. D2 has no such blind spot and is the strongest of the three.
This was found by running the negative fixture, not by reasoning about it.

### §3.2 The run

```
$ cd /Users/Dev/madhav-l3/setup/platform/python-sidecar
$ python3 -m pytest tests/l3/test_ka_kshetra_p0_planning_readonly.py -p no:randomly -v
test_planning_assigns_no_transaction_id_and_changes_no_content               PASSED
test_planning_succeeds_inside_a_read_only_transaction                        PASSED
test_read_only_transaction_detector_is_not_vacuous                           PASSED
test_dry_run_planning_and_dry_run_prepare_mutate_nothing                     PASSED
test_negative_fixture_detectors_catch_a_planted_planning_mutation            PASSED
test_resume_planning_filters_completed_substeps_and_preserves_committed_rows PASSED
test_prepare_replace_fails_closed_on_a_populated_slice_without_deleting      PASSED
============================== 7 passed in 0.56s ===============================
```

What each proves, against the strategy's wording:

- *"Make planning read-only"* — `plan_substeps` produced 346 substeps for the
  canonical chart with `txid_current_if_assigned() = NULL` before and after, an
  unchanged content digest across 17 watched tables, and it also succeeds
  verbatim inside `SET TRANSACTION READ ONLY`.
- *"Move replacement into the owned execution partition"* — `steps[0].key ==
  'prepare:replace'`, an EXECUTION substep the orchestrator wraps in its own
  savepoint (`writer.py:520 _run_prepare_replace` → `:2420 _delete_prior_rows`).
  Planning emits it; planning does not perform it.
- *"Zero planning/dry-run mutations"* — covered for BOTH: `ctx.dry_run=True`
  planning assigns no xid, and the dry-run `prepare:replace` substep returns
  `rows_inserted=0, notes='dry-run: replacement preparation not executed'` with
  the digest unchanged.
- *"crash/resume"* — a first attempt commits `prepare:replace` plus a real row
  and a `stage0:Sun` receipt; a fresh writer object on a fresh transaction then
  re-plans. Re-planning assigns no xid, the committed row survives
  byte-identical, both completed keys are filtered out, and the resumed plan is
  exactly `n_first - 2` — bounded.
- *"restore prior data/outcomes"* — `prepare:replace` against a POPULATED
  writer-owned slice raises `KshetraReplacementHeld` and deletes nothing
  (DP-SD-017 W0 holds replacement until W7 supplies immutable
  candidate/publication); after rollback the digest is identical to the prior one.

### §3.3 The negative fixture (F28)

A detector that has never reported false is not a detector. A scratch-only pytest
plugin (`plant_kshetra_mutation.py`, never committed, never in the repo) replaces
`services.ka_kshetra.stage0_kinematics.plan_substeps` — one of the lane planners
`plan_substeps` folds in via `_optional_stage_plugins` — with a planner that
DELETEs first, i.e. the original hazard shape. The UNMODIFIED tests then fail:

```
$ PYTHONPATH=<scratch> python3 -m pytest tests/l3/test_ka_kshetra_p0_planning_readonly.py \
      -p no:randomly -p plant_kshetra_mutation -q

E  AssertionError: D1 FAILED: plan_substeps assigned a transaction id, which Postgres
   does only for a transaction that has written. Planning is not read-only.
E  assert 1712 is None
E  psycopg.errors.ReadOnlySqlTransaction: cannot execute DELETE in a read-only transaction
E  ERROR services.ka_kshetra.writer:writer.py:481 ka_kshetra:
   services.ka_kshetra.stage0_kinematics.plan_substeps failed: cannot execute DELETE in a
   read-only transaction
E  AssertionError: D1 FAILED for dry-run planning
E  assert 1717 is None
E  AssertionError: RESUME HAZARD: re-planning wrote. This is the P0 defect — planning
   mutating before resume filtering.
E  assert 1723 is None
E  Failed: DID NOT RAISE <class 'services.ka_kshetra.writer.KshetraReplacementHeld'>

FAILED test_planning_assigns_no_transaction_id_and_changes_no_content
FAILED test_planning_succeeds_inside_a_read_only_transaction
FAILED test_dry_run_planning_and_dry_run_prepare_mutate_nothing
FAILED test_resume_planning_filters_completed_substeps_and_preserves_committed_rows
FAILED test_prepare_replace_fails_closed_on_a_populated_slice_without_deleting
5 failed, 2 passed in 0.29s
```

The 2 that still pass are the negative fixture itself (it plants its own mutation
and expects the detectors to fire) and D2's own control.

### §3.4 Verdict

**REPAIRED-AND-PROVEN.** `ka_kshetra.plan_substeps` is read-only by execution on
three independent detectors, replacement lives in the `prepare:replace` execution
substep, dry-run writes nothing, resume is bounded and non-destructive, and the
detectors are demonstrably able to report false.

## §4 Bhavishya empty-generation + crash/resume + restore

### §4.1 The test

`platform/python-sidecar/tests/l3/test_bhavishya_p0_empty_generation_db.py`.

`tests/l3/test_bhavishya_p0_safety.py` already covers this shape against a
hand-written `_StrictConnection` fake (67 tests pass, 1 skipped — that skip is
its live-DSN partition-lock test). A fake cannot catch a CHECK/FK/trigger
disagreement and is not what the strategy asks for; this module runs the real
`KaBhavishyaLekhaWriter.run(ctx)` against the live harness.

**A detector correction worth recording.** The obvious detector — `xid` — is
WRONG for this writer, and the first run of these tests failed because of it.
`ka_bhavishya_lekha` deliberately takes `SELECT … FOR UPDATE` on the chart's
existing projections BEFORE deciding anything (`:114-141`), to serialize its
read/plan/write window. Measured on the harness:

```
xid_before=NULL           ctr_before          ins/upd/del = 0/0/0
SELECT … FOR UPDATE   →   xid=1808            ctr ins/upd/del = 0/0/0
DELETE (1 row)        →                       ctr ins/upd/del = 0/0/1
```

A row lock assigns an xid without modifying a tuple. So the detector here is
`pg_stat_get_xact_tuples_inserted/updated/deleted` per relation
(`_p0_harness.xact_tuple_counters`), backed by the content digest and by the
domain-level outcome map (`id → (outcome_recorded, outcome_notes)`).

### §4.2 The run

```
$ python3 -m pytest tests/l3/test_bhavishya_p0_empty_generation_db.py -p no:randomly -v
test_empty_input_with_a_recorded_outcome_refuses_and_mutates_nothing             PASSED
test_empty_input_with_no_existing_rows_is_an_honest_empty                        PASSED
test_empty_input_with_unrecorded_rows_still_refuses_rather_than_silently_emptying PASSED
test_rebuild_with_matching_candidate_preserves_outcome_and_row_identity          PASSED
test_negative_fixture_legacy_delete_then_early_return_loses_the_outcome          PASSED
test_crash_mid_run_restores_prior_data_and_resume_is_bounded                     PASSED
test_dry_run_contract_is_absent_and_that_is_reported_not_assumed                 PASSED
============================== 7 passed in 0.11s ===============================
```

Against the strategy's wording:

- *"preserve outcome identity … including empty results"* — a `kala_bhavishya`
  row carrying `outcome_recorded=true, outcome_notes='observed: promotion 2027-02'`
  meets an EMPTY candidate plan (no `kala_darshana` rows). The writer raises
  `"candidate plan is empty while 1 existing projection row(s) remain … no rows
  were mutated"`, the transaction tuple counters do not move on any of
  `kala_bhavishya / kala_darshana / kala_convergence / phala_anchors`, and the
  outcome map is byte-identical after rollback.
- *Honest empty* — with nothing seeded at all, the writer returns
  `rows_inserted=0` / `"No future darshana windows and no existing projections"`,
  assigns no xid, and moves no counter. An honest empty, not a silent one.
- *Stale rows with NO recorded outcome also refuse* — rather than reporting a
  successful empty rebuild while stale rows stay servable (§N.8).
- *L3-U10 / F17 / F19, "candidate regeneration does not reset a delivered
  forecast"* — a NON-empty rebuild whose regenerated claim is identical (seeded
  from the writer's own `_assign_tier` / `_build_falsifiability` /
  `_build_projection_narrative`, not hand-typed literals) yields
  `rows_inserted=0, rows_skipped=1`, the same row `id`, and the outcome intact.
  Row identity matters independently: `phala_anchors.bhavishya_id` is
  `ON DELETE SET NULL`, so delete/reinsert would sever accepted downstream
  provenance even inside a successful transaction.
- *"crash/resume"* — the light writer exposes exactly ONE substep
  (`len(plan_substeps(ctx)) == 1`), so the honest statement is: a crash rolls
  back that one savepoint. Under `SAVEPOINT substep` the run really inserts
  (`rows_inserted == 1`, table goes 1 → 2 rows); `ROLLBACK TO SAVEPOINT substep`
  restores the digest byte-for-byte and the recorded outcome survives; the
  resumed run replays exactly the lost work (`rows_inserted == 1,
  rows_skipped == 1`) and still preserves the observation. The writer accretes
  no partial state a resume would have to reconcile.
- *"restore prior data/outcomes"* — proven twice: by the savepoint rollback above,
  and by the refusal paths, where a full `content_digest` comparison after
  rollback equals the pre-run digest.

**One honest gap, asserted rather than papered over.**
`ka_bhavishya_lekha.run()` has NO `ctx.dry_run` branch — a dry-run invocation
would write. Its planning is the inherited default `plan_substeps`, which touches
no DB at all (asserted), so the strategy's "zero planning/dry-run mutations" is
satisfied on the planning half and NOT on the run half. This is captured as a
test (`test_dry_run_contract_is_absent_and_that_is_reported_not_assumed`) that
asserts the CURRENT absence, so it turns red the day someone adds the branch and
this section must be corrected. It is a Phase 1 candidate, not a P0 blocker:
nothing in the live path invokes this writer with `dry_run=True` (§5).

### §4.3 The negative fixture (F28)

Two forms.

*(a) In-repo, permanent.* `test_negative_fixture_legacy_delete_then_early_return_loses_the_outcome`
defines a test-local `_LegacyOrderWriter` reproducing the pre-repair ordering —
DELETE the chart's projections, THEN early-return on empty input — and asserts
that the SAME `_assert_outcomes_preserved` helper the positive tests use reports
failure:

```
with pytest.raises(AssertionError, match="OUTCOME LOSS"):
    _assert_outcomes_preserved(before, after)
```

*(b) Scratch-only, against the real production class.* A plugin
(`plant_bhavishya_hazard.py`, never committed) monkeypatches
`KaBhavishyaLekhaWriter.run` back to the legacy ordering. The UNMODIFIED tests
then fail:

```
$ PYTHONPATH=<scratch> python3 -m pytest tests/l3/test_bhavishya_p0_empty_generation_db.py \
      -p no:randomly -p plant_bhavishya_hazard -q

E  Failed: DID NOT RAISE <class 'RuntimeError'>
E  Failed: DID NOT RAISE <class 'RuntimeError'>
E  AssertionError: OUTCOME LOSS: recorded observation(s) destroyed by the rebuild:
   {45: (True, 'observed: promotion 2027-02')}
E  AssertionError: the run must have made a real change to restore from
   assert 2 == 1  where 2 = WriterResult(…, rows_inserted=2, …)

FAILED test_empty_input_with_a_recorded_outcome_refuses_and_mutates_nothing
FAILED test_empty_input_with_unrecorded_rows_still_refuses_rather_than_silently_emptying
FAILED test_rebuild_with_matching_candidate_preserves_outcome_and_row_identity
FAILED test_crash_mid_run_restores_prior_data_and_resume_is_bounded
4 failed, 3 passed in 0.15s
```

`OUTCOME LOSS: recorded observation(s) destroyed by the rebuild` is the P0 hazard
reproduced live, and it is the detector reporting false on demand.

### §4.4 Verdict

**REPAIRED-AND-PROVEN**, with one narrow, named, non-blocking gap (no `dry_run`
branch in `run()` — §4.2, carried to Phase 1).

## §5 Live-path status

Both assets are live, not dormant. Evidence:

- Production `asset_registry` (read-only query):
  ```
  ka_bhavishya_lekha | layer=kala | has_writer=true | catalog_status=CURRENT | scope=per_chart | has_substeps=false
  ka_kshetra         | layer=kala | has_writer=true | catalog_status=CURRENT | scope=per_chart | has_substeps=true
  ```
- Production `asset_throughput` shows real per-chart build attempts:
  `ka_bhavishya_lekha` — 1 chart `error`, 2 `stale`; `ka_kshetra` — 2 `error`, 1 `stale`.
- `discover_all()` registers both:
  `ka_kshetra -> KaKshetraWriter (heavy)`, `ka_bhavishya_lekha -> KaBhavishyaLekhaWriter (light)`.

**Hazard 1 (Kshetra planning).** A live caller reaches it, at TWO call sites:
- `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:740` —
  `substeps = writer.plan_substeps(ctx)`, the ordinary build dispatch, reached
  from `runner.py:687 run_asset` and ultimately from the container entrypoint
  `platform/python-sidecar/Dockerfile.pipeline:68` →
  `python -m pipeline.orchestrator.main`.
- `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1133` — the
  SATYA-DĪPA no-op-completion re-probe calls `writer.plan_substeps(ctx)` AGAIN,
  after the build, inside `SAVEPOINT noop_completeness_probe`, and only for
  `has_substeps=true` assets — which `ka_kshetra` is. This second site makes the
  read-only property more load-bearing than the first: a mutating planner there
  would corrupt a build that had already succeeded.

**Hazard 2 (Bhavishya empty-input).** A live caller reaches it, via the same
`asset_runner` dispatch: a light writer gets one default substep whose
`run_substep` calls `run(ctx)`. One production dependent asset declares
`ka_bhavishya_lekha` in its `depends_on`, so the asset also participates in
cascade rebuilds.

Web/cockpit surface: `platform/src/app/api/build/` (rebuild, rebuild-all,
cascade, start, continue) and `platform/src/app/api/cockpit/` (plan, refresh,
clear) are the operator-facing build entrypoints; they drive the same
orchestrator. I did **not** trace a single HTTP handler line-for-line to
`run_asset`, so, precisely: *no evidence found within the scope I searched —
`platform/python-sidecar/pipeline/orchestrator/**`, `platform/src/app/api/**`,
`platform/src/lib/**`, `platform-mcp/src/**` — that either hazard is unreachable;
both are reached from the Python orchestrator dispatch, which is the path every
"click Build" ultimately takes.*

For `dry_run=True` specifically (the §4.2 gap): I found **no live caller that
constructs a `ContextSpec` with `dry_run=True` within the scope I searched**
(`platform/python-sidecar/pipeline/orchestrator/**`). That is why the missing
dry-run branch in `ka_bhavishya_lekha.run()` is a Phase 1 item and not a P0
blocker.

## §6 Verdict

| item | verdict | reason |
|---|---|---|
| **P0 hazard 1 — Kshetra planner mutation** | **REPAIRED-AND-PROVEN** | Real `plan_substeps` executed against a live trigger-carrying Postgres: no xid assigned, succeeds under `SET TRANSACTION READ ONLY`, digest unchanged across 17 tables; replacement is the `prepare:replace` execution substep; dry-run writes nothing; resume filters completed keys and preserves committed rows; a planted planning mutation makes 5 of 7 tests fail. |
| **P0 hazard 2 — Bhavishya empty-input deletion** | **REPAIRED-AND-PROVEN** | Real `run()` executed against the live harness: an empty candidate plan against a retained outcome refuses with zero tuple modifications and a byte-identical digest; honest empty on a truly empty chart; matched rebuild preserves outcome AND row id; savepoint crash restores and the resumed run replays exactly the lost work; planting the legacy delete-then-early-return ordering yields `OUTCOME LOSS: recorded observation(s) destroyed by the rebuild`. |
| **Sub-item — `ka_bhavishya_lekha.run()` has no `dry_run` branch** | **STILL OPEN → Phase 1 item** | A `dry_run=True` invocation would write. Asserted as current behaviour by a test so it cannot drift silently. No live caller passes `dry_run=True` within the scope searched, so it is not a P0 blocker. |
| **Detector fidelity — `xid` on a row-locking writer** | **RESOLVED, recorded** | Measured: `FOR UPDATE` assigns an xid but moves no tuple counter. `xid` is exact for Kshetra planning (no locks) and wrong for Bhavishya; the latter uses `pg_stat_get_xact_tuples_*`. |
| **Whether repair is sufficient for an expensive rebuild trial** | **COULD NOT VERIFY** | Out of scope here. These tests prove the two named safety properties on a seeded harness; they do not exercise a full `ka_kshetra` stage-0→8 build, nor production data volumes. F24: computational correctness only. |
| **Production behaviour under concurrency** | **COULD NOT VERIFY** | The advisory-lock/partition-lock serialization was not exercised with two concurrent connections here; `tests/l3/test_bhavishya_p0_safety.py`'s existing two-connection test skips without a DSN. Phase 1 candidate. |

### Teardown proof

```
$ pg_ctl -D /tmp/kp0/data stop
waiting for server to shut down.... done
server stopped

$ pg_isready -h /tmp/kp0 -p 59510
/tmp/kp0:59510 - no response
exit=2

$ lsof -nP -iTCP:59510
exit=1                      (no process listening on 59510)

$ pgrep -fl 'kp0/data'
exit=1                      (no postgres process for this data dir)

$ rm -rf /tmp/kp0 ; ls -d /tmp/kp0
ls: /tmp/kp0: No such file or directory

$ ls /tmp | grep -c '^kp0$'
0
```
The concurrent agent's instance (`/tmp/kx`, port 59500) was never touched.

### Files produced

- `platform/python-sidecar/tests/l3/_p0_harness.py` — shared detectors + connection
- `platform/python-sidecar/tests/l3/test_ka_kshetra_p0_planning_readonly.py` — 7 tests
- `platform/python-sidecar/tests/l3/test_bhavishya_p0_empty_generation_db.py` — 7 tests
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/phase0_2_harness_bootstrap.sh`
- this artifact

Nothing was committed or pushed. The full `tests/l3/` suite runs
**1 failed, 1538 passed, 41 skipped, 2 xfailed**; the single failure is
`test_transit_search_cache.py::test_cached_call_matches_direct_swe_calc_ut`
(`assert 275.33943157413626 == 275.33942000832093`), a pre-existing Swiss
Ephemeris float-precision failure in a memoization test last touched by PR #606,
untouched by this phase.
