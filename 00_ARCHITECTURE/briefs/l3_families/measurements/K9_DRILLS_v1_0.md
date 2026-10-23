---
artifact: K9_DRILLS
version: "1.2"
status: ENABLED BINDINGS — local manifest protocol proven; full-layer drills pending
produced_on: 2026-10-20
item: K9-23
changelog: "1.2 (W5W6-READINESS WP2): the cancel kinds are enabled and the section 'Cancel, stop and teardown of a rebuild' states what a cancel does to a running rebuild, proven by test_w56_k9_cancel_teardown.py; the rebuild run no longer publishes to Pub/Sub; teardown covers the resonance writer's candidate tables and names the chart-scoped gochara_resonance_map. 1.1: all eight layer/rebuild kinds are enabled (SR-PREBUILD-ALL, #3746) and described as bound; each drill names the runner record it must retain; backup bindings confirmed from the declaration; every full-layer result stays null; the Gochara separation statement follows the declaration (publish_head / rollback_head enabled by #3786; verification_job enabled by J-4b through its own script fleet/verification_launch.py, on the kind-batch). 1.0: separately bound disabled layer operations, local failure/rollback proofs and full-drill protocol."
---

# Layer publication and rebuild drills

The three layer operations are distinct from Gochara's `verification_job`,
`publish_head`, and `rollback_head`. They operate only the `kala_layer_*` manifest
and call the existing APIs. They neither switch Gochara authority nor delete
candidate, published, issued-forecast or production rows. In the declaration
`verification_job` is `enabled:true` (J-4b) and runs its own script `fleet/verification_launch.py`, while `publish_head` and `rollback_head` are enabled
only through the reviewed head policy (J-6m / J-6r, #3786) and run `fleet/head_operation.py`;
no Gochara kind shares a script with a layer kind. All eight layer and rebuild kinds below are enabled in
`fleet/executor_ops.json` (SR-PREBUILD-ALL, #3746): `orchestrator_rebuild_dryrun`,
`orchestrator_rebuild`, `layer_verify_dryrun`, `layer_verify`, `layer_publish_dryrun`,
`layer_publish`, `layer_rollback_dryrun` and `layer_rollback`. Enablement says the
refusals below are in place; it is not evidence that a full layer has been rebuilt,
published or rolled back.

## Bound interface

Run from `platform/python-sidecar` as the principal allocated by the executor. The
three real layer operations are `services.kala_core.publication` itself; the rebuild
kinds and every `*_dryrun` sibling go through `services.kala_core.publication_admission`,
which delegates the real work to it:

```text
python -m services.kala_core.publication_admission rebuild-dryrun --run-id RUN_UUID --assets ORDERED_COMMA_LIST --phase pre|post
python -m services.kala_core.publication_admission rebuild --run-id RUN_UUID --assets ORDERED_COMMA_LIST --phase pre|post
python -m services.kala_core.publication verify --run-id RUN_UUID --generation GENERATION --independently-derived-digest SHA256
python -m services.kala_core.publication publish --run-id RUN_UUID --generation GENERATION --expected-head PREVIOUS_GENERATION_OR_NONE
python -m services.kala_core.publication rollback --generation RETAINED_PREVIOUS_GENERATION --expected-head CURRENT_GENERATION
python -m services.kala_core.publication_admission verify-dryrun | publish-dryrun | rollback-dryrun   (same arguments as the real operation)
```

A layer dry run executes the real operation in a transaction it rolls back and reads
back; `dry_run_passed` is true only when the rollback was confirmed and a write was
observed inside the transaction. The rebuild dry run is plan inspection only
(K9_BENCHMARKS_v1_0.md, Execution boundary) and never earns `dry_run_passed`.

**(I) INTERPRETATION:** the required initial-publication expected-head token is
`NONE`, since executor argument validation does not transport an empty value.
Alternative: omit the expected-head argument and lose the explicit absent-head
pin. For subsequent publications
it is the exact generation string. All CLI operations are canonical-chart
scoped. Rebuild consumes an already accepted frozen run, never creates one,
never invokes a writer directly, and delegates transaction ownership to the
orchestrator. Its asset list must equal the ordered frozen plan. Non-Kāla assets
and the delivery registrar are refused. Preparing a run with
`action=rebuild, clear_before=false` remains the dispatcher's responsibility
(PLAN §6.4); this wrapper performs no clearing.

**(I) INTERPRETATION:** K9-1 supplies the complete writer/grain inventory in
`kala_layer_candidate.conventions.publication_grains`, a map of each included
writer id to a nonempty list of grain keys. Keys equal their writer id or begin
with `writer_id:`. This extends existing convention metadata without changing
the FROZEN writer contract. Missing metadata, a writer absent from the frozen
plan, duplicate/wrong-owner keys, extra or absent grain rows and failed grains
all refuse. Alternative: infer completeness from observed rows, which cannot
find a writer that never ran. The K9-1 builder must reconcile this metadata
before activation; legacy candidates intentionally fail closed.

**(I) INTERPRETATION:** digest re-derivation uses the existing separately
supplied `verify_candidate(... independently_derived_digest=...)` contract
(`services/kala_core/verify/__init__.py:37`). Coverage and input identity are
checked here, independently implemented writer-specific semantic/golden-value
checks remain an upstream verification requirement. Alternative: derive the
“independent” digest from stored grain inputs, which is circular. The operation
reports `INPUT_VERIFICATION_RECORDED` and `semantic_verification=null`; it does
not manufacture a semantic PASS. This null is an activation gate, not semantic
verification evidence. An accepted input receipt alone cannot qualify the
full-layer semantic rehearsal for the executor's pre-acceptance.

**(I) INTERPRETATION:** a new `layer_verifier` executor capability selects only
`KY_LAYER_VERIFIER_DATABASE_URL` into the child's `DATABASE_URL`. It never
falls back to builder/owner credentials. Alternative: bind the verifier to the
builder capability, which cannot establish the separate-principal boundary. The child checks `current_user` is
`verifier_principal`. Migration 1390 grants column-scoped candidate/build-run
reads only, in addition to the existing grain-read and receipt-insert grants.
No schema creation privilege or head write is granted. Migration 1390 is centrally allocated to K9-23 by
`/Users/Dev/kalayantra/run/MIGRATION_ALLOCATION.json`
(R-2026-10-16-01); 1386 is allocated to L0-M. No migration was applied to production.

## Local database oracles

The tests in
`platform/python-sidecar/tests/l3/kala_db/manifest/test_publication_ops.py`
run on the suite's guarded throwaway PostgreSQL database. They prove absent
candidate, incomplete inventory, failed/missing/stale/wrong-principal verification,
stale expected head and changed live head are refused without a head mutation.
A published zero-row grain is an explicit result, never an absent result.

The rollback oracle, `test_rollback_restores_retained_head_and_payload_bytes`, publishes A, opens and publishes B against A, then CAS-restores
A against B. It compares the retained head row's actual serialized bytes
(including its stored timestamp) and all candidate-grain row bytes before and
after rollback. The separate previous-head test refuses a jump from C to A when
C pins B as its predecessor. Candidates and grain payloads remain retained.
The existing multi-connection lifecycle suite remains selected alongside these
new tests. These are manifest-protocol proofs, not a production served-payload
or full-layer semantic qualification.

Executor tests prove the eight bindings are enabled with the declared module, subcommand and
capability, select distinct commands, pass only the operation's one connection, and
never let `NIRMANA_FORCE_EXECUTE` reach a child. Required Governance Tool Tests
runs those binding tests and now depends on Kāla DB Tests. The CI gate's own
negative cases execute its shell predicate with failed, cancelled and skipped DB
results; only an intentional docs-only skip is permitted.

## Cancel, stop and teardown of a rebuild

`orchestrator_rebuild_cancel` and its dry run `orchestrator_rebuild_cancel_dryrun` run `publication_admission cancel` / `cancel-dryrun`
(`rebuild_control.cancel`). The executor admits a cancel only for the run-id of an `orchestrator_rebuild` that is in flight (SR-CANCEL-LANE),
signed-only, on its own worker so it never waits behind the rebuild it stops. The teardown kinds `orchestrator_rebuild_teardown` and
`orchestrator_rebuild_teardown_dryrun` run the same module's `teardown` / `teardown-dryrun`; whether they are enabled is the declaration's
(`fleet/executor_ops.json`, surrogate ruling S-1), and a teardown is never mechanical and needs the signer's backup and dry-run attestations.

**What a cancel does to a run that is executing.** It acts only between assets; it never interrupts one.

1. The cancel sets `build_runs.stop_requested_at` (a first request keeps its time) and nothing else for a `running` or `paused` run; a `planned`
   run is marked `stopped` at once. The returned `state_after` is what the database says, never a presumed terminal state.
2. The rebuild is ONE in-process run: the executor child `publication_admission rebuild` calls `execute_run`. Its scheduler
   (`runner.execute_dag`) reads the request at the top of each scheduling round: after every asset that finishes, and at most every
   `_POLL_INTERVAL` (5 s) while assets are in flight.
3. On a stop request it starts no further asset. An asset already dispatched runs to the end of its own work (the runner cannot interrupt a writer;
   only the writer's own `writer_timeout_seconds` abandons one), and is counted completed if it finishes.
4. `execute_run` then writes the run `stopped` with `ended_at` and returns. The child reads the final state, finds it is not `completed`, prints
   `{"reason": "orchestrator did not complete the build", "status": "REFUSED"}` and exits 2: the receipt of a cancelled rebuild is a refusal, never a pass.
5. A cancel therefore does not shorten the asset in progress: for a long single writer (the Gochara century writer runs for hours) the run ends only after that
   writer ends. Cancelling does not tear anything down; the candidate and the asset states the run wrote stay until a teardown.

Proven against the database fixture by `test_w56_k9_cancel_teardown.py`: `test_c5a` (a stub plan of three assets, cancel after the first: the other two never
start, the run reads `stopped`), `test_c5b` (a cancel that arrives while an asset is working: that asset finishes, nothing further starts) and `test_c5c` (the
rebuild child of a cancelled run exits REFUSED, exit 2).

**What a teardown covers.** The candidate of a terminal run, every table that references it (read from the catalog), the unlinked candidate-keyed tables
of the plan's writers (`kala_activation_predicates` from `ka_yojaka`; `kala_f1_relationship` and `kala_f1_target_object` from the resonance writer's candidate
path, migration 1342), and, for a failed run, the asset states it wrote. `gochara_resonance_map` is different: it has no generation column and the resonance writer's
legacy path deletes and re-inserts the whole chart (`services/ka_gochara_resonance/writer.py`), so a teardown cannot tell a run's rows from the previous build's. It is
never deleted; the teardown result names it under `chart_scoped_writes_left_alone` with its row count, and a rebuild whose plan includes `ka_gochara_resonance` has
already replaced that table's rows for the chart. Giving that table a candidate generation needs a migration and is not done here.

The rebuild run keeps its orchestrator events off Pub/Sub (`PUBSUB_DISABLED` is set for the run by `publication_admission`), so the `[event]` lines reach stderr and
the stall and re-projection gates have their log source.

## Full-layer drills still owed

The bindings are enabled; these drills are the evidence a full layer is owed before its
first real use. Each row names the runner record that must be preserved, because the
dependency graph and `build_run_assets.state='complete'` cannot say what ran.

| Drill | Runner record to retain | Raw evidence to retain | Current result |
|---|---|---|---|
| Baseline full candidate | every `asset.substep` event and the frozen plan digest | run id, every candidate grain, independent checks, qualified consumer bytes | null — K9-1 execution pending |
| Attachment-only upstream change | `asset.skip_no_delta` and `asset.substep` events per writer, plus the content-bound progress ledger | exact before/after upstream values; completed and repeated grains | null — no real invalidation run |
| Interpretation change | `asset.skip_no_delta` and `asset.substep` events, geometry reuse distinguished from writer invocation | same evidence as above | null — no real invalidation run |
| Convention change | `asset.skip_no_delta` and `asset.substep` events for the actual rerun, never a predicted list | convention pins before and after | null — no real invalidation run |
| Kill/resume | `asset.substep` events up to the kill and after the resume, with monotonic timestamps | durable-grain snapshot at the kill, resumed completed and repeated keys, CPU and wall loss | null — no real killed-substep run |
| Publish/rollback | none from the runner; the head rows and grain bytes are database state | full served projection bytes at A, retained A bytes, head CAS A→B→A, bytes compared after rollback | local manifest bytes proven; full served projection null |
| Backup and restore | none from the runner; the backup receipts and the scratch-restore receipt | qualified named backup, scratch-target restore, exact row/hash comparison, capability readback | null — J-1a qualification pending |

For each real drill preserve what the runner actually did. Do not infer reruns
from the dependency graph or from `build_run_assets.state='complete'`:
`skip_no_delta` also finishes complete
(`pipeline/orchestrator/asset_runner.py:931`). Use emitted events and the
content-bound progress ledger, and distinguish a writer probe, a writer call,
a skipped grain and a repeated grain. Restart loss is elapsed abandoned work
since the last durable boundary, measured at the kill, with repeated-work time
reported separately. No restart-loss number is claimed by this pre-build.

Backup operations, confirmed from the declaration (`fleet/executor_ops.json`, enabled_by J-1a)
and not re-qualified here:

- `backup_snapshot` is enabled, capability `owner`, script `platform/scripts/backup_v5_small_test_job.py`, arguments `label` and `scope`.
- `backup_restore_verify` is enabled, capability `owner`, script `platform/scripts/backup_v5_small_test_job.py`, arguments `label` and `scope`.

The script exists in the tree, so these are no longer placeholders. It is a pg_dump
capture with a measured scratch restore, full or `--scope small_test`; the scratch restore
proves the archive, not a production restore. Qualified backup/restore evidence for a
rebuilt layer is J-1a's and stays null in the table above.
`platform/scripts/backup/export_irreplaceable_tables.sh:7` is a narrower logical export of
two table sets using `DATABASE_URL` and optional GCS; it is not a whole-layer backup/restore
proof. Do not reuse it as a canonical rebuild backup.

D-R9 remains in force: the century materializer stays held and its data retained
until the successor proves coverage and refinement semantics (surrogate charter
§5 KYD-4; KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §12 R-9). Neither a local
publication test nor the enabled bindings release that hold.
