---
artifact: J6_BINDINGS_PREBUILD
version: "1.0"
status: BUILT_WAITING_ON_GATE
items: [J-6, J-6-n-flip, J-6l]
authority: KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A6_PREBUILD.md, D-40
---

# J6 authority bindings and evidence preparation

> **2026-10-20 SR-HEAD-POLICY-KEEP:** the four authority kinds are now **enabled** in
> `fleet/executor_ops.json`, only through this policy: the executor loads `head_operation.py`
> from the request's reviewed commit and refuses any request it refuses; `head_operation.py`
> is also the kinds' script. Both real kinds stay signed-only. Tests:
> `fleet/tests/test_j6_head_bindings.py` (gate), `tests/l3/gochara/test_j6_bindings_db.py` (entry point).

This change prepares code. All four authority kinds were **disabled** at prebuild time in
`fleet/executor_ops.json:20`. No request, production observation, decision,
J6R_REHEARSAL, J6L_LIVE or step-acceptance receipt is produced by this prebuild.
The J-6-n-flip decision residual remains open; its read-only consumer is prepared.

G6 and G8 remain the acceptance authority:
`KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md:46` and `:48`.
The campaign uses its existing handshake; per-job SESSION_OPEN is cut by
`KALAYANTRA_RELAUNCH_PLAN_v2_7.md:164`.

## Prepared operation contract

`fleet/head_operation.py:100` validates the canonical chart, full reviewed commit,
exact generation/manifest, complete expected authority row, change timestamp and
argument digest. `request_problem` (`:163`) consumes the latest governed D-FLIP
event and the actual hash-bound dry-run/publish receipts. It never authors a
decision. `flip_decision` (`:135`) follows the controller's last-event precedence
(`platform/scripts/governance/pravaha_tracker/state.py:75`): approved/refused are
final outcomes; deferred/insufficient_evidence remain open. Only approved permits
publish. A rollback consumes the retained row from its original committed publish
receipt; it does not depend on a later flip decision staying approved.

A request carries the existing executor fields plus:

- `head_change.expected_head`: exactly `{generation, flipped_at, flipped_by,
  evidence_ref}`, from an independent read of the stored authority row; UTC
  timestamps use ISO-8601 with `+00:00`. Missing fields are not filled in.
- `head_change.target`: `{generation, manifest_id}`; J-6 publishes only `5.0`.
- `head_change.change_at`: timezone-qualified, fixed in dry-run/execute scope.
- `args`: exactly `generation`, `manifest-id` (UUID or `none` for legacy rollback),
  `expected-head-sha256` (SHA-256 of sorted compact JSON of the complete old row).
- Publish: `decision_event_sha256`, the sorted compact JSON digest of the latest
  effective approved D-FLIP event from `run/EVENTS.jsonl`.
- Execute: `dry_run_receipt: {path, sha256}` under `run/ops/receipts`, for the same
  scope and reviewed commit. Dry run and execute need **distinct operation IDs
  and idempotency keys**. An already-receipted operation ID cannot be reused.
- Rollback: `rollback_of: {path, sha256}` for the original committed publish;
  `head_change.restore_head` equals its complete `before` row, and expected head
  equals its complete `after` row. For a governed previous head, supply its exact
  retained manifest as target too. There is no DELETE/default-v1 rollback.

The standalone adapter (`:260`) owns only its own transaction; it is not a layer
writer and changes no WriterBase contract. Execute requires an idle autocommit
connection. It acquires the existing chart lock, verifies the exact published,
non-test-slice manifest and matching seal, and compares-and-swaps all four
columns. All nine listed chart-scoped relation fingerprints (`:37`) must remain
equal. A dry run actually attempts this same switch, rolls its scope back and
reads the complete previous row back. A commit emits
`COMMITTED_AWAITING_READBACK`; the executor records `AWAITING_READBACK`.
Neither exit zero nor that output is acceptance. Production timing/qualification
of these full relation fingerprints still belongs to the real rehearsal gate.

(I) INTERPRETATION: descriptive G6 checklist keys (`:29`) are independent
pre-acceptance attestations bound to the complete request. They do not compute or
replace separate verification, seal approval, reader deployment, evaluation,
backup/restore or environment approval. Existing G8 lease, timestamp, reviewed
commit, credential isolation and production-fence checks remain in the executor.
Existing `operation_dryrun.py` metadata remains PREPARATION_ONLY; it is not the
new real transactional `publish_head_dryrun` / `rollback_head_dryrun`.

## Readback and receipt projection (offline commands only)

Commands below prepare or import evidence and print to stdout. They do not submit
an executor request or publish a canonical receipt. `REQUEST` and other file
arguments refer to actual independently checked evidence, not example approvals.

```sh
python -B 00_ARCHITECTURE/briefs/kalayantra/fleet/head_operation.py decision --events "$EVENTS"
python -B 00_ARCHITECTURE/briefs/kalayantra/fleet/head_operation.py readback-sql --request "$REQUEST"
python -B 00_ARCHITECTURE/briefs/kalayantra/fleet/head_operation.py complete \
  --request "$REQUEST" --commit-receipt "$COMMIT_RECEIPT" \
  --readback-request "$READBACK_REQUEST" --readback-receipt "$READBACK_RECEIPT" \
  --readback-output "$READBACK_OUTPUT" --acceptance "$ACCEPTANCE"
```

The future independent lane writes the generated SQL under `run/ops/sql` and
requests existing `readback_sql` with `args.sql_file` and `args.sql_sha256` (the
exact SQL bytes' digest). `fleet/readback_sql.sh:32` checks that digest before
connecting. Its existing read-only driver, single prepared statement and resolved
path confinement remain. The query measures the head and exact manifest/seal;
it binds the **recorded operation ID and request digest**, rather than inventing
a build-run column absent from the authority schema. The independent acceptance
also binds both the commit-receipt and readback-receipt SHA-256 values. The
completion projection (`head_operation.py:385`) rejects another query, requester,
operation, head, manifest, output digest or acceptance. It does not release the
production fence or author controller step verdicts. The controller still owes
the nominated `/Users/Dev/kalayantra/run/ops/receipts/J-6.json` binding and its
independent accepted evidence digest (`00_ARCHITECTURE/control/kalayantra/plan_model.json:19881`).

(I) INTERPRETATION: these proposed child-output/readback schemas add precise
bindings without asserting an observed operation. The previous executor receipt
stays immutable; completion is a separately accepted projection for the canonical
item path. The alternative of treating child success as COMPLETED is rejected.

## Live response and soak tooling

`fleet/j6_live_readback.py:83` accepts a transport callable. The CLI imports
previously captured HTTP status, final URL, observation time and exact body bytes;
it never opens a network connection. Capture retains the original bytes in
base64 and their digest. It requires the exact `gochara_v5_windows/1` identity,
published matching seal, complete class coverage, and no refusal or test slice.

Its proposed `ky.j6_deployment_observation/1` input identifies the actual endpoint,
immutable deployed image digest/commit, observation time and full deployed
migration filename/hash set. A separate `ky.j6_consumer_path/1` receipt, ACCEPTED
by an independent verifier, must bind that deployment digest, URL and exact flip
binding: `{operation_id, request_sha256, receipt_sha256,
readback_receipt_sha256, chart_id, generation, manifest_id}`. This path receipt
must come from actual consumer-route verification. `mode: authority` is not
self-attestation by the capture producer. Named-generation URLs and the existing
explicit-generation route do not establish the consumer switch.

```sh
python -B 00_ARCHITECTURE/briefs/kalayantra/fleet/j6_live_readback.py capture \
  --binding "$BINDING" --deployment "$DEPLOYMENT" --consumer-path "$CONSUMER_PATH" \
  --http-observation "$HTTP_OBSERVATION" --body "$HTTP_BODY"
python -B 00_ARCHITECTURE/briefs/kalayantra/fleet/j6_live_readback.py soak \
  --binding "$BINDING" --observations "$CAPTURE_ARRAY" --owner-rule "$OWNER_RULE"
```

`record_soak` (`:127`) revalidates every captured payload/digest and deployment,
requires chronological samples of the same operation/deployment, records their
measured span and hashes the owner rule's exact bytes. Successful samples do not
prove health between samples. The owner rule and required outage/gap/other metric
observations, and their independent evaluation, remain later inputs. With no
owner rule, omit `--owner-rule`: the missing rule is explicit. All capture/soak
`acceptance` fields remain null; there is no default duration or computed PASS.

(I) INTERPRETATION: opaque owner-rule evidence is recorded rather than designing
a new soak threshold. This follows the explicit open rule at
`00_ARCHITECTURE/control/kalayantra/plan_model.json:347` and J-6l-a61 (`:26279`).
No canonical J6L_LIVE receipt is written by preparation/import alone.

## Gate work deliberately left out

The cockpit still owes effective governed D-FLIP and all original dependencies;
independently dispatched production verification/seal and exact-manifest approval;
actual deployment/constraint/migration/image evidence; live lease, backup with
verified restore, reviewed CI head, accepted real dry run, pre-acceptance, one
slot and protected-environment approval where applicable; real consumer flip and
rollback acceptance; owner-defined measured soak exit rule, actual observations,
and independent post-readback/soak acceptance. None is inferred absent/present in
production by these local tests. Do not enable or dispatch from this prebuild.

Tests use guarded disposable admission-metadata fixtures on the suite's own
cluster; synthetic seal setup is deliberately **not** verification/seal evidence
(`platform/python-sidecar/tests/l3/gochara/test_j6r_rehearsal_db.py:1`). No sky
stand-in or computation was introduced. No migration, frozen writer, L0–L2 asset,
generated aggregate or implementation-digest input changed. CI discovers the new suites through the matching DB integration and
J6-BINDINGS governance profiles in `platform/scripts/governance/ci_test_suites.json`.
