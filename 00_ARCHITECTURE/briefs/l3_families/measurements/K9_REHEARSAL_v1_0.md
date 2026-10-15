---
artifact: K9_REHEARSAL_v1_0.md
version: "1.0"
status: PREBUILD_ONLY — operational rehearsal NOT_RUN
item: K9-1
authority: SR-A4-01 and SR-A4-05; code preparation only
changelog:
  - "1.0: passive request preparation, guarded read-only evidence audit, and real disposable-DB regression tests; no activation."
---

# K9-1 rehearsal preparation

This is code preparation, not a full-layer build result. No lane build, canonical-chart
rebuild, independently dispatched semantic verification, production publication,
benchmark, rollback drill, or certification is claimed. The campaign-level handshake
remains open (`briefs/kalayantra/sessions/SESSION_OPEN_kalayantra.yaml`, notes).

The binding item is `00_ARCHITECTURE/control/kalayantra/plan_model.json:20068`.
The rebuild contract is `KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:293`, the
stage/grain table is at line 186, and candidate → verification → publication is
at line 238. The cockpit runs request shape is implemented at
`platform/src/app/api/cockpit/runs/route.ts:46`; frozen manifest validation is at
`platform/python-sidecar/pipeline/orchestrator/runner.py:234`.

## Prepared code

`platform/python-sidecar/services/kala_core/rehearsal.py` provides two passive APIs:

- `prepare_rehearsal(...)` requires explicit lane, chart/build/generation identity,
  expected previous head, model/rule/convention pins, and every materialized asset's
  actual grain keys. It produces an **unsubmitted** `asset_set` request with
  `action=rebuild, clear_before=false`, the ordered 19-asset roster, and null
  operational/publication-path signals. It neither opens a candidate nor dispatches.
- `audit_rehearsal(conn, prepared)` accepts an idle local lane connection, starts
  one repeatable-read, read-only snapshot, and inspects committed evidence. It checks
  the frozen run manifest, actual completion times across stages, candidate binding
  and pins, every writer's current detector, chart/global execution scope, current
  code/config/upstream/partition/output lineage, data freshness, every planned grain
  including `zero_rows`, current verifier input digest, and the published head.
  Missing/false/null detectors fail. A detector that attempts persistent mutation
  fails inside a savepoint; inspection continues and reports the failure.

The command-line surface only prepares a file, without any DSN or database connection:

```sh
# From platform/python-sidecar; both file paths are operator-selected job artifacts.
python3 -m services.kala_core.rehearsal --prepare "$JOB_SCRATCH/pins.json" \
  --output "$JOB_SCRATCH/K9_REHEARSAL.prepared.json"
```

`pins.json` supplies exactly `lane`, `chart_id`, `generation`, `build_id`,
`expected_head_generation`, `model_digest`, `rule_registry_version`, `conventions`,
and `grains_by_asset`. There are deliberately no invented production example pins
or grain keys. The latter mapping must cover Yojaka, Avadhi, judge, negative space,
jury, forecaster and the four read models; keys must come from the upstream planners.

The audit's states are `incomplete`, `awaiting_verification`, `awaiting_publication`,
and `published`. Guarded throwaway databases require explicit `allow_fixture=True`
and can only finish as `fixture_passed`. `operational_rehearsal_passed`,
`publication_path_verified`, and `clear_before_verified` stay null: table readback
cannot establish historical dispatch options or which function executed a head write.

Existing lifecycle APIs retain mutation authority:
`services/kala_core/manifest/__init__.py:32` opens a candidate,
line 133 validates and publishes it, and line 177 calls the head CAS. The separate
verifier principal check is in `services/kala_core/verify/__init__.py:41`.
There is no new writer, orchestrator contract, migration, executor capability,
serving change, or production activation.

## Interpretations and upstream assumptions

1. **(I) INTERPRETATION — pre-build is passive preparation and audit code.** SR-A4-01
   and SR-A4-05 permit code ahead of dependency bookkeeping; they do not establish
   real-writer output readiness. Alternative: execute the operational K9 build now.
   The latter is outside this job's code-only authority.
2. **(I) INTERPRETATION — F1 before Avadhi.** PLAN §4.1 places Avadhi early but says
   it reads F1; §6.4 explicitly puts Yojaka before Avadhi. Preparation follows that
   dependency. Alternative: follow the table's printed numeric order literally.
3. **(I) INTERPRETATION — sky grains belong to the judge.** PLAN §4.1 declares no
   separate sky registry id and includes five adapters before judge consumption.
   The roster includes those adapters and the four services, excludes the delivery
   registrar and legacy writers, and does not invent a sky asset. Alternative:
   manufacture a registry id or rebuild the delivery registrar as replaceable data.
4. **(I) INTERPRETATION — upstream supplies globally unique grain attestations.**
   Migration `platform/migrations/1330_kala_layer_manifest_candidates.sql:25` keys
   grains by chart/generation/grain, not asset. The caller must supply actual unique
   keys, and upstream writers must persist them using the existing contract.
   Alternative: guess keys, infer completion from row counts, or silently namespace
   keys the writers never wrote. Missing upstream attestations remain a refusal.
5. **(I) INTERPRETATION — lifecycle evidence has a narrower meaning than certification.**
   A matching verifier receipt is reported as stored acceptance; it does not prove
   an independently dispatched semantic re-derivation ran. The existing Dasha proxy
   probe's declared scope is retained in detector detail. Alternative: promote receipt
   presence or a proxy GREEN into a whole-layer correctness claim.
6. **(I) INTERPRETATION — external rehearsal evidence remains untouched.** The owns
   list names `/Users/Dev/kalayantra/run/K9_REHEARSAL.json`, outside this job's write
   box. The job folder holds the pre-build receipt; the cockpit may install real
   operational evidence only after execution. Alternative: overwrite the run file
   with fixture/preparation evidence.

## Verification and activation gates

The focused suite is `tests/l3/kala_db/rehearsal/test_rehearsal.py`. Its disposable
tables use migration 1330's actual candidate/head schema. It executes stored detector
SQL and migration 1377's real Tulana probe, accepts honest zero-row grains, catches
missing/stale/false evidence and ordering violations, and observes the real
`publish_candidate → publish_head` CAS while confirming inspection never moves a head.
Its synthetic accepted receipt tests lifecycle admission only, not verifier independence;
the existing separately dispatched verifier suite remains part of validation.

The mandatory Kāla DB job discovers the new directory at `.github/workflows/ci.yml:345`,
retaining all existing test selections. The governance CI coverage test also names
the new file. Fail-on-revert copies, exact commands/exits, and logs are retained under
`JOB_SCRATCH/revert-proofs/` and indexed by `JOB_SCRATCH/result.json`.

Before operational use: complete the item's real dependencies, apply the reviewed
upstream schemas/declarations through their proper windows, obtain actual candidate
and grain pins, inspect the accepted frozen plan, and run the existing orchestrator
on the lane database with one build slot. Open the candidate before its stages; retain
the old head while building; separately dispatch the actual semantic verifier; publish
only through the existing manifest/CAS path. Then install the measured lane report and
lineage at the canonical external evidence path. K9-23 owns cost/drill preparation;
K9-4 owns production operations. No cost, speed, coverage, or completion number is
inferred from these fixture tests.
