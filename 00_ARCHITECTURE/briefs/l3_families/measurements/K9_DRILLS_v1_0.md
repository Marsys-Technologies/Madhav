---
artifact: K9_DRILLS
version: "1.0"
status: PREBUILD — local operation protocol qualified; production gates pending
produced_on: 2026-10-16
items: [K9-23, K9-4b]
changelog: "1.0: port inherited layer operations onto current main; require semantic checks and bind prepared readback bytes; keep activation disabled."
---

# Layer publication and rebuild drills

This is A6 D-40 / SR-A4-01 preparation. All five K9 executor entries remain
`enabled:false`. Gochara's `verification_job`, `publish_head`, and `rollback_head`
are separate operations and their declarations are preserved. No production
workload, request, acceptance marker, migration application or activation is
supplied by this preparation.

## Executable operations

The executor maps five distinct commands to
`platform/python-sidecar/services/kala_core/publication.py`, using module
`services.kala_core.publication` with cwd `platform/python-sidecar`:

| Executor kind | Command | Required named arguments |
|---|---|---|
| orchestrator_rebuild_dryrun | rebuild-dryrun | run-id, assets |
| orchestrator_rebuild | rebuild | run-id, assets |
| layer_verify | verify | run-id, generation, independently-derived-digest, semantic-source |
| layer_publish | publish | run-id, generation, expected-head, semantic-source |
| layer_rollback | rollback | generation, expected-head |

`assets` is the exact ordered, frozen plan, never a new workload assembled by
this script. The run must contain the complete replaceable roster and respect
K9-1's waves, including adapters and services. The delivery registrar and non-Kāla
writers refuse. The CLI is canonical-chart scoped. Rebuild delegates exactly
once to the existing `execute_run`, then reads the recorded run state and refuses
an absent, planned or failed result. It never invokes a writer directly.
The dispatcher must have prepared `action=rebuild, clear_before=false`
(PLAN §6.4); this wrapper creates no run and performs no clearing.

`rebuild-dryrun` is read-only inspection: `status=PLAN_ONLY`,
`executed_assets=[]`, `dry_run_passed=null`. It cannot qualify the executor's
execution dry-run gate. **(I) INTERPRETATION — dry-run:** preserve the inherited
plan-inspection interface because the actual orchestrator CLI has no dry-run
flag. Alternative: invent a frozen-runner flag or award execution qualification
to inspection; neither is supported.

**(I) INTERPRETATION — generation namespace:** `NONE` explicitly pins an absent
head in the publish CLI; real generations exclude `NONE`, `current`, whitespace
and empty values. Alternative: omit expected-head, losing the explicit absent
head compare-and-swap. Both initial and existing-head concurrent changes refuse.

**(I) INTERPRETATION — complete grains:**
`kala_layer_candidate.conventions.publication_grains` must map every frozen
writer/service to its nonempty, unique, writer-qualified grain keys. Missing,
unplanned, duplicate and failed grains refuse; `zero_rows` is a result. The
K9-1 preparation currently exposes materialized-stage grain plans, so complete
adapter/service and reused/skipped-grain bindings must be reconciled before
activation. Alternative: infer coverage from observed rows, hiding work that
never ran. No FROZEN writer interface is changed.

## Independent semantic verification

An independent input digest alone cannot earn layer verification or publication
(CLAUDE.md §N.8; PLAN §4.4). `publication_checks.py` requires a reviewed
`GoldenCheck` for each writer. Each checker reads candidate/source values through
a single-prepared-SELECT reader and returns an independently recomputed expected
value and observed value for **every** assigned grain. Missing/null comparisons,
unregistered writers and unequal values refuse before receipt insertion.

The immutable verifier receipt binds chart, generation, build id, frozen plan
digest, each writer's frozen code digest, exact grain/input-vector/result-state inventory,
checker ids, checker source SHA-256 and expected/observed value hashes.
Publication checks those bindings and complete comparisons, then uses the
existing manifest's independent-principal/input-digest guard and atomic head
compare-and-swap. Old input-only receipts refuse. Rollback can restore only the
published head's retained immediate predecessor and performs no payload deletion.

**(I) INTERPRETATION — oracle admission:** the production `CHECKS` registry is
empty and therefore refuses. Production writer owners must supply their reviewed
independent comparisons and narrow output/source SELECT grants; the request
cannot inject a module, expected values or a claimed PASS. The local tests use
explicit SQL-backed arithmetic fixture oracles for all 19 roster identities;
these prove protocol behavior, not those writers' Jyotish semantics. Alternative:
pretend fixture checks or an input digest independently verify real writer
outputs. The K9-4b operational per-writer acceptance is consequently **left out**
until these bindings and real K9-4a results exist.

**(I) INTERPRETATION — verifier capability:** use a distinct `layer_verifier`
capability instead of the alternative builder/owner channel, so absence refuses
without a credential fallback. The executor supplies
`KY_LAYER_VERIFIER_DATABASE_URL` as the child's sole `DATABASE_URL`, without a
builder/owner fallback. The child checks `current_user=verifier_principal`.
Centrally allocated migration **1390** adds column-scoped candidate/build-run
reads; existing 1330/1334 grants supply grain reads and receipt insertion.
1390 is protected alongside 1330 so routine deployment cannot apply its grants
before pending tables. It is new, idempotent, and was exercised only in guarded
local fixture databases. It does not grant head writes or broad schema access.
Actual production oracle SELECT grants remain a prerequisite.

## K9-4b request preparation and readback

`fleet/k9_readback.py` prepares inert JSON from an existing typed executor
request plus a recorded run/generation. It supports stages `per-writer` and
`publication`. It neither submits requests nor writes under the live run root.
The generated SQL reads the recorded run's frozen source plan, its candidate,
complete grain rows, actual build_run_assets and asset_provenance_receipts rows,
and verification detail; publication readback also reads
that run's chart head. Missing evidence stays null; no query manufactures PASS.

At preparation the exact single-SELECT JSONB query is wrapped as:

```sql
SELECT evidence::text AS evidence FROM (<readback_sql>) AS t
```

The helper adds `args["sql-sha256"]`; the existing executor request digest thus
binds the exact SQL bytes. Admission refuses a K9-4b readback without that hash.
`readback_sql.sh` checks the digest before connecting, then executes the same
bytes with the prepared extended-query protocol in a read-only transaction.
The returned format is tab-separated CSV with a header: parse CSV before
parsing its one `evidence` JSON text field. The real-shell test exercises this
wrapper and refuses a changed SQL file. **(I) INTERPRETATION — identity:** use
the executor's existing operation_id and request digest; the cockpit retains its
acceptance-record request_id mapping. Alternative: invent a required new executor
request identity field; the current typed request does not define one.

The future guarded sequence remains:

| K9-4b step | Required evidence; none emitted here |
|---|---|
| per_writer_readback_accepted | independent readback for K9-4a's recorded run; every writer's own semantic/golden evidence and source/build/grain lineage |
| verification_passed | separate-principal layer_verify receipt plus independent readback of its immutable semantic detail |
| published | layer_publish request with explicit expected-head; executor receipt and independent observation of the same run/head |
| publication_readback_accepted | readback_sql receipt/output digest, recorded run/generation and retained predecessor; independent whole-file acceptance |

Every future production request still owes live coordination lease, verified
backup restore, a real dry-run proof, one build slot and request-bound independent
pre-acceptance (CHARTER §10 / G8). Postconditions come from executor readback,
not exit zero. Do not write MET markers or completion receipts from this runbook.

## Local proofs and remaining drills

`tests/l3/kala_db/manifest/` is already discovered by Kāla DB Tests. The required
Governance Tool Tests aggregate now also requires that DB job. The new binding
and CI-gate tests are discovered by existing governance shards; no explicit
new test path is added to ci.yml. Tests cover absent/incomplete candidates,
input-only/rejected/stale/wrong-principal receipts, semantic mismatch, wrong
build/code/grain pins, both head CAS cases, role separation, planned-run
delegation and incomplete outcomes, and byte-equal retained head plus unchanged
grain payloads on rollback. Job-local mutation/revert copies retain distinguishing
negative runs. The N2 delegation regression is delivered; its separately governed
child and historical custody note remain for independent cockpit reconciliation.

| Full-layer drill | Required raw measurement | Result |
|---|---|---|
| Baseline candidate | actual full frozen run, every independent writer oracle, complete consumer bytes | null — upstream golden bindings and K9-1/K9-4a execution pending |
| Attachment-only lineage change | actual runner skip/substep events and completed/repeated grains | null — not run |
| Interpretation change | actual runner events; geometry reuse distinguished from invocation | null — not run |
| Convention change | changed pins and actual rerun events | null — not run |
| Killed-substep resume | monotonic kill time, last durable boundary, abandoned-work seconds, repeated-work time and keys | null — not run |
| Publish/rollback | full served projection A bytes, A→B→A head transition and compared bytes | local manifest/head/grain bytes proven; full served projection pending |
| Backup/restore | named source backup, isolated restore equality, capability and principal readback | inherited J-1a scripts bound and dry-run interface checked; no fresh capture/restore executed |

Record what the runner actually reran; neither dependency edges nor a completed
writer row prove an invocation (`asset.skip_no_delta` also completes). Restart
loss is measured abandoned work since the last durable boundary, with repeated
work reported separately. These measurements cannot be invented from protocol
fixtures. The benchmark contract records them as null until that real drill.

Backup declarations on starting main are already enabled J-1a owner-capability
bindings to `platform/scripts/backup_v5_small_test_job.py`, with distinct snapshot
and restore-verify modes. They are preserved, not re-enabled by K923B. Their dry
runs report `planned`, `backup_taken=null`, `restore_verified=null`; no local
interface check substitutes for the required actual backup/restore receipt.

D-R9 remains held until coverage/refinement semantics are independently proven
(PLAN §12 R-9). Neither fixture verification nor these prepared operations
release it. FROZEN paths, L0–L2 assets, generated outputs and production remain
untouched; existing caller/CI declarations were changed only where needed.


Source anchors (working implementation):

- Frozen roster/waves: `platform/python-sidecar/services/kala_core/rehearsal.py:29`;
  run/candidate guards: `platform/python-sidecar/services/kala_core/publication.py:23`.
- Golden source/receipt binding:
  `platform/python-sidecar/services/kala_core/publication_checks.py:34` and
  `platform/python-sidecar/services/kala_core/publication_checks.py:63`.
- Separate verification, publication and rollback:
  `platform/python-sidecar/services/kala_core/publication.py:88`,
  `platform/python-sidecar/services/kala_core/publication.py:111`, and
  `platform/python-sidecar/services/kala_core/publication.py:127`.
- Request preparation: `00_ARCHITECTURE/briefs/kalayantra/fleet/k9_readback.py:24`;
  SQL-byte check: `00_ARCHITECTURE/briefs/kalayantra/fleet/readback_sql.sh:32`;
  admission: `00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py:360`.
- Delegation/incomplete outcomes:
  `platform/python-sidecar/tests/l3/kala_db/manifest/test_publication_ops.py:268`;
  actual-shell wrapper/digest proof:
  `platform/python-sidecar/tests/l3/kala_db/manifest/test_k94b_readback.py:51`.
