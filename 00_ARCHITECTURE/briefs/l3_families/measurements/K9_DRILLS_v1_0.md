---
artifact: K9_DRILLS
version: "1.0"
status: PREBUILD — local manifest protocol proven; full-layer drills pending
produced_on: 2026-10-16
item: K9-23
changelog: "1.0: separately bound disabled layer operations, local failure/rollback proofs and full-drill protocol."
---

# Layer publication and rebuild drills

The three layer operations are distinct from Gochara's `verification_job`,
`publish_head`, and `rollback_head`. They operate only the `kala_layer_*` manifest
and call the existing APIs. They neither switch Gochara authority nor delete
candidate, published, issued-forecast or production rows. SR-A4-01 keeps all five
K9 executor entries disabled; preparation is not activation evidence.

## Prepared interface

Run from `platform/python-sidecar` as the principal allocated by the executor:

```text
python -m services.kala_core.publication rebuild-dryrun --run-id RUN_UUID --assets ORDERED_COMMA_LIST
python -m services.kala_core.publication rebuild --run-id RUN_UUID --assets ORDERED_COMMA_LIST
python -m services.kala_core.publication verify --run-id RUN_UUID --generation GENERATION --independently-derived-digest SHA256
python -m services.kala_core.publication publish --run-id RUN_UUID --generation GENERATION --expected-head PREVIOUS_GENERATION_OR_NONE
python -m services.kala_core.publication rollback --generation RETAINED_PREVIOUS_GENERATION --expected-head CURRENT_GENERATION
```

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

The rollback test publishes A, opens and publishes B against A, then CAS-restores
A against B. It compares the retained head row's actual serialized bytes
(including its stored timestamp) and all candidate-grain row bytes before and
after rollback. The separate previous-head test refuses a jump from C to A when
C pins B as its predecessor. Candidates and grain payloads remain retained.
The existing multi-connection lifecycle suite remains selected alongside these
new tests. These are manifest-protocol proofs, not a production served-payload
or full-layer semantic qualification.

Executor tests prove the five bindings remain disabled, select distinct commands,
and pass only the operation's one connection. Required Governance Tool Tests
runs those binding tests and now depends on Kāla DB Tests. The CI gate's own
negative cases execute its shell predicate with failed, cancelled and skipped DB
results; only an intentional docs-only skip is permitted.

## Full-layer drills still owed before enablement

| Drill | Raw evidence to retain | Current result |
|---|---|---|
| Baseline full candidate | run id, frozen plan/digest, every candidate grain, independent checks, qualified consumer bytes | null — K9-1 execution pending |
| Attachment-only upstream change | exact before/after upstream values; actual runner `asset.skip_no_delta` and `asset.substep` events; completed/repeated grains | null — no real invalidation run |
| Interpretation change | same evidence, with geometry reuse distinguished from writer invocation | null — no real invalidation run |
| Convention change | convention pins and actual rerun events, never a predicted rerun list | null — no real invalidation run |
| Kill/resume | monotonic start/kill times, durable-grain snapshot at kill, resumed completed/repeated keys and CPU/wall loss | null — no real killed-substep run |
| Publish/rollback | full served projection bytes at A, retained A bytes, head CAS A→B→A, bytes compared after rollback | local manifest bytes proven; full served projection null |
| Backup and restore | qualified named backup, scratch-target restore, exact row/hash comparison and capability readback | null — J-1a qualification pending |

For each real drill preserve what the runner actually did. Do not infer reruns
from the dependency graph or from `build_run_assets.state='complete'`:
`skip_no_delta` also finishes complete
(`pipeline/orchestrator/asset_runner.py:931`). Use emitted events and the
content-bound progress ledger, and distinguish a writer probe, a writer call,
a skipped grain and a repeated grain. Restart loss is elapsed abandoned work
since the last durable boundary, measured at the kill, with repeated-work time
reported separately. No restart-loss number is claimed by this pre-build.

The backup entries still name J-1a placeholders in `fleet/executor_ops.json`.
Their declared capability is `gcloud`; neither script binding is qualified.
`platform/scripts/backup/export_irreplaceable_tables.sh:7` is a narrower logical
export of two table sets using `DATABASE_URL` and optional GCS; it is not a
whole-layer Cloud SQL backup/restore proof. Keep both backup operations disabled
until J-1a supplies the real scripts and confirms their capabilities. Do not
reuse that narrow export as a canonical rebuild backup.

D-R9 remains in force: the century materializer stays held and its data retained
until the successor proves coverage and refinement semantics (surrogate charter
§5 KYD-4; KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §12 R-9). Neither a local
publication test nor the prepared bindings release that hold.
