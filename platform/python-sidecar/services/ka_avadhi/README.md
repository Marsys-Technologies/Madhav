# K-AVADHI-C integrity preparation

Version: 1.0. Status: PREPARATION, NOT INSTALLED. Changelog: initial read-only
candidate inspector and guarded PostgreSQL regression fixtures.

`inspect_candidate(conn, chart_id, build_id)` measures the explicitly dispatched
building candidate. It compares its complete period row set with the pinned F2
input and resolves lord-condition ids, subjects, keys, roles and inherited values
against the pinned natal chart/build/ayanamsha/tier. Sign and Yogini identities
use the shared vocabulary. A `missing_fact` null requires actual absence in that
pinned input; `method_inapplicable` requires a sign lord. Partial L1 nulls inherit
their ids and values. Mechanism effective states must match their pinned source.
The caller owns the connection, transaction and stable inspection snapshot.

This is a preparation API, not a writer hook, serving route, registry check,
legacy-health detector, prose verifier or layer-acceptance signal. Every report
retains the certification HOLD and warning. Its `passed` field applies only to
the candidate obligations described above. No registry, legacy, published or
serving rows are changed. The existing served warning/exclusion must remain;
this module does not install or claim a new product warning.

The tests execute the complete existing registry SQL produced by migration 1341
and independently execute the complete retained migration-1023 SQL scoped to
legacy exactly as 1341 scopes it. The empty-reference legacy fixture is
**synthetic**: both checks remain false while candidate inspection passes.
It is not a capture or reproduction of today's canonical-chart failure.
Other cases prove grounding rejection, typed-null discipline, chart/build
isolation, repeatability and byte-preservation of immutable rows and registry.
The existing `kala-db-tests` CI job discovers this suite and requires the DB.

Binding sources:

- `00_ARCHITECTURE/control/kalayantra/plan_model.json:20728` onward: original
  K-AVADHI-C brief and compatibility boundary (fix the demonstrated wrong side).
- `00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md:110`–120:
  ALGO 3.2, L1 ids and values, typed nulls, no quality/score.
- `platform/migrations/1341_k1_2_avadhi_candidate_dossiers.sql:34`–71:
  retained legacy SQL AND candidate obligations.
- `platform/migrations/1023_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql:133`–187:
  real lord grounding, resolvable references and retained legacy attribution.
- `platform/python-sidecar/pipeline/orchestrator/writers/ka_avadhi.py:272`–286:
  dispatched candidate binding and immutable legacy/published partitions.
- `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:819`–833:
  registry SQL is executed without chart/build parameters; no new runner
  interface is assumed or implemented here.
- Triage `X-20261015T084536Z-parked-triage/TRIAGE.md:88`–96 and its result's
  K-AVADHI-C entry; KYD-151/153 (`run/DECISIONS.jsonl:147,149`); surrogate
  `SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:51,58`: preparation is permitted,
  canonical readbacks and independent acceptance still gate the eventual port.

(I) INTERPRETATION: without the authorized immutable canonical capture/current
registry SQL hash, migration-1341 ledger and generation/reference readbacks,
the buildable deliverable is this read-only preparation, not an installed
replacement. The inspector deliberately requires the writer's deterministic
full condition/ref shape and ordering; it does not admit a weaker minimum-ref
or arbitrary-null contract.

Cockpit follow-up: obtain that evidence, admit the concrete candidate/legacy
serving and dispatch-binding contract, then independently review full-SQL,
ref/null/mutant results at the final head. Only after the evidence proves the
check is the wrong side should a new registry-only migration be allocated
(1380 is reserved by an open PR; use 1381+ after rechecking origin/main).
No applied migration, writer, orchestrator contract, tail exclusion or HOLD is
changed by this preparation. Deployment/readback acceptance remains separate.
