---
artifact: J6MR_PREBUILD.md
version: 1.0
status: BUILT_WAITING_ON_GATE
produced_on: 2026-10-16
changelog:
  - '1.0: disabled authority adapters, source-bound operational step acceptance and measured soak detector.'
---

# J-6m / J-6r preparation

This prepares code under A6 D-40 / SR-A4-01. No production operation, enablement,
protected application, effective ruling or J6R acceptance is asserted. The cockpit
still earns the real item steps in dependency order.

The serving admission replacement is already migration 1379; 1382 closes its
TRUNCATE bypass. Both are protected-listed. This change preserves 1236, 1379 and
1382 byte-for-byte and needs no new migration number. Local admission tests use
those actual migrations; synthetic seal metadata in their fixtures never proves
independent verification or computed chart data.

## Authority request and execution

The table now binds `publish_head`, `publish_head_dryrun`, `rollback_head` and
`rollback_head_dryrun` to the module
`scripts.kala_gochara_cutover.authority_operation` in `platform/python-sidecar`.
All four remain **disabled**, require `builder`, have a 120-second executor
budget, and carry checklist rows 2/3/7/9/11. The child also bounds connection,
lock and statement time. Existing G8 lease, source containment, request-bound
pre-acceptance, backup/verified restore, production fence and quiescence checks
remain in the executor. The no-effect `operation_dryrun.py` preview cannot earn
`dry_run_passed`; the two new transactional kinds execute the actual CAS and
retention checks and roll back.

The accepted `KY_OPERATION_REQUEST` includes the executor's usual fields plus a
safe `request_id`. Its `args` must exactly equal the transported CLI args:

| Operation | Required args |
| --- | --- |
| publish and its dry run | `generation=5.0`, `manifest-id=<exact sealed published UUID>`, `expected-head=<SHA-256>` |
| rollback and its dry run | `generation=<measured retained generation>`, `expected-head=<SHA-256>`, `source-operation=<successful publish operation ID>`, `source-sha256=<full publish output digest>` |

**(I) INTERPRETATION I1:** `expected-head` hashes sorted compact UTF-8 JSON of the
complete observed head: `generation`, `flipped_at` (UTC ISO timestamp or null),
`flipped_by`, `evidence_ref`. The alternative, a generation-only token, would miss
concurrent audit-row changes. The chart lock and full-row SQL CAS both apply.
There is no absent-row fallback or upsert. Publication requires the exact
published non-test-slice manifest and matching seal; the deployed SQL remains
the admission authority.

Execution additionally requires top-level `dryrun_operation` and
`dryrun_output_sha256`. Under `$KY_ROOT/run/ops`, the child reads
`receipts/<dryrun_operation>.json`, its `.output.txt`, and
`acceptance/<dryrun_operation>.json`. It verifies successful rollback-confirmed
output, matching args/chart/head/reviewed commit, the receipt's request/output
digests and an independent v1–v4 ACCEPTED receipt carrying the same operation,
commit, request digest and `output_sha256`. A boolean dry-run attestation alone
cannot satisfy this child.

**(I) INTERPRETATION I2:** restore the full retained authority row from the actual
successful publication output, bound to its executor receipt and the request's
`source-sha256`. The alternative, caller-supplied replacement audit fields or
DELETE-to-v1, would lose the measured previous head. Rollback restores metadata
as well as generation, and never calls ledger rollback or deletes generation
content. Before and after, the nine chart-scoped relations listed in
`j6r_rehearsal._RETAINED_TABLES` must have identical counts and row-byte hashes.
This is a declared retention set, not a whole-database backup.

Before execution's first UPDATE the child exclusively creates and fsyncs
`run/ops/authority-intents/<operation_id>.json` with the complete preimage,
replacement and request digest. An existing intent refuses execution. An intent
remains `PREPARED` even after success: it records what was prepared, not what
committed. A lost connection, interrupted commit or missing output requires
independent request-bound readback and reconciliation; never delete the intent
or retry to infer an outcome. Final output is emitted only after the transaction
context confirms commit or rollback. Operation receipts and independent
post-operation readbacks are still separate requirements.

## Operational step and soak evidence

For an operational step with `evidence_sha256`, the independent review's unique
matching step must contain that digest, `request_id`, `operation_id` and
`evidence_path`. The controller hashes the actual evidence bytes. That evidence
must contain matching request/operation IDs and `sources.request`,
`sources.receipt`, `sources.readback`, each `{path, sha256}`. Relative source paths
resolve beside the evidence; the review's relative evidence path resolves beside
its result. The source request's compact sorted digest (excluding only
`acceptance_receipt`) must equal the executor receipt and independent readback
`request_sha256`. The successful executor receipt and ACCEPTED v1–v4 readback
must name the same operation; readback also names the request and the actual
`executor_receipt_sha256`.

**(I) INTERPRETATION I3:** make that explicit source chain mandatory instead of
trusting equal strings in two markers. Legacy non-operational artifact/review
forms retain their existing behavior. Operational reviews without source bytes
must be re-earned; they are not silently grandfathered.

`J-6l-a61.owner_soak_rule_and_live_readback` specifically requires
`schema=ky.served_soak/1`. Its evidence contains `rule: {path, sha256}` and
`samples`. The independent matching review step additionally pins
`soak_rule_sha256` and `effective_soak_decision`. The rule (`ky.soak_rule/1`)
provides `decision_id`, `approved_at`, UTC `start`/`end`, positive `cadence_s`,
`max_lateness_s`, positive `max_latency_ms`, distinct `required_classes`, canonical
`chart_id`, `generation=5.0`, exact `manifest_id`, and `deployment` with commit,
image digest and migration-set digest. The accepted source readback must agree
on chart/generation/manifest/deployment. The source publication request must
agree on the generation and exact manifest.

**(I) INTERPRETATION I4:** use an inclusive start/end schedule with a whole number
of cadence intervals. The alternative is inferring an end or silently reducing
the sample denominator. The rule must be approved before the first sample;
future, late, missing or duplicate samples refuse. No duration or latency is
chosen here, and this validator does not make a decision effective.

Each sample records `scheduled_at`, `observed_at`, `latency_ms`, `http_status`,
`transport=authority_selected_http`, immutable `deployment`, exact
`response_base64` and `response_sha256`. The detector decodes and hashes the bytes,
then measures HTTP success, absence of domain refusal, published manifest and
matching seal/chart/generation provenance, and `complete_within_scope` for every
required class. Rollback invalidates the window. Explicit-generation HTTP,
in-process fixture results and elapsed time alone cannot qualify. Acceptance
still requires independent capture/review of actual serving and integrity
readbacks; this validator is not a serving-probe implementation.

## Remaining gate work

- Independently review the exact merged adapter source and CI, then enable only
  through the approved gate/installation path. This branch enables nothing.
- Verify the protected migrations actually applied and read the CHECK/ALWAYS
  trigger definitions from the target database. No production readback was run.
- Supply the real sealed/verified generation, deployed image/migration identity,
  effective D-FLIP and measured soak rule, accepted dry runs and G8 prerequisites.
- Bind an actual authority-selected deployed serving probe and legacy transport.
  `routers/gochara_v5.py` currently requires an explicit generation and calls
  `read_v5`; substituting that endpoint cannot prove authority selection.
- Run the real lane/deployed-reader flip → response → rollback → byte-equal
  response and retention rehearsal. Only then may an independent verifier accept
  `/Users/Dev/kalayantra/run/J6R_REHEARSAL.json`. That path is outside this job's
  writable box and was not created. Component tests preserve the real reader's
  honest `stale_binding` with synthetic admission metadata and explicitly do not
  claim G6 qualification or a completed soak.

## Source anchors

- `CLAUDE.md:114` (§N.4 applied migration immutability), `:139` (§N.8 earned signals).
- `KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:108` (phase 11) and
  `KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md:46` (G6), `:48` (G8), beside the
  campaign brief directory.
- `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:246`
  (publication retention) and `:247` (rollback CAS).
- `platform/migrations/1379_gochara_sealed_authority.sql:24` (admission predicate),
  `:115` (replacement CHECK); `1382_gochara_authority_no_truncate.sql:27`.
- `platform/python-sidecar/services/gochara_kernel/serving_reader.py:608`
  (authority dispatch); `platform/python-sidecar/routers/gochara_v5.py:35`, `:93`
  (explicit-generation route).

The new tests live in three already mandatory CI suites:
`fleet/tests/test_operation_adapters.py`,
`pravaha_tracker/tests/test_step_receipt_binding.py`, and
`tests/l3/gochara/test_j6r_rehearsal_db.py`. No explicit workflow test paths,
CI-generated outputs, writer sources, frozen paths or digest locks were changed.
