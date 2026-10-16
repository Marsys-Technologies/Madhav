---
artifact: J5Q_PREPARATION
version: "1.0"
status: BUILT_WAITING_ON_GATE
date: 2026-10-16
items: [J-5q, J-5q-pr3091, J-5q-a57, J-5q-b54]
runtime_effect: none
changelog:
  - "1.0: offline qualification diagnostics, pinned-artifact report assembly, C35 seal/manifest refusal tests, and strict-tolerance merger repairs. No candidate evaluation or residual acceptance claimed."
---

# J5Q preparation — built, waiting on gate

This is preparation tooling, not `EVALUATION_RESULT_5_0_v1_0.md`, a measured
`J5Q_RESULT.json`, or an accepted A5.7/B5.4 residual. Actual generation measurements
and independently accepted receipts remain owed. No production operation, migration,
reader switch, publication, job enablement, or tracker completion is performed.

## Authority and source observations

- `CLAUDE.md:139` (§N.8): signals need detectors for their specific claims.
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md:46`
  (G6): run all endpoints and A5.7 gates on the exact independently sealed
  generation; record the results as they read. Scores are tuning baselines.
  Wrong, missing or unverifiable engineering results still prevent flip acceptance.
- The supplied protocol source is
  `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v2_3.md:168`
  (§6 endpoints), `:252` (§8 degeneracy), `:268` (§9 procedure), and `:292`
  (§10 attribution, ablations and honest limits).
- The supplied SI addendum is
  `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_5.md:13`
  (5.x `si := evidence_for`), `:17` (4.1 `si := raw_intensity`), `:32`
  (NULL is not zero), `:35` (unknown competitors), and `:54` (two freezes).
- The supplied campaign plan is
  `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.md:153`
  (A5.6/A5.7) and `:186` (B5.3/B5.4 dependencies). These protocol/addendum
  paths are absent from this pinned `origin/main`; the explicitly supplied
  readable source files were consulted instead. Source hashes are below.
- `platform/python-sidecar/services/gochara_eval/dump_extract.py:8` and `:42`
  explicitly refuse governed 5.x extraction. `services/gochara_eval/freeze.py:32`
  admits only 4.1 configuration freezes. This job does not quietly enable 5.x
  by widening those allowlists: a governed adapter and its bound freeze inputs
  remain required before any 5.0 scoring.
- PR #3091's local branch and remote-tracking branch both resolve to
  `74363d958688e5f30d4090f223b1a4e148e7f2af`. Its two files were already
  byte-identical on the job's base `349d12afbded4ccf99464841e9e7c932755fdef8`.
  Every inherited C35 assertion remains. Archived PR prose was unavailable in
  PORT_MANIFEST; it is advisory, and no missing review decision was inferred.

## Per-item delivery and remaining gates

| Item | Preparation built | Evidence deliberately left for the later operation/review |
|---|---|---|
| J-5q | JSON/Markdown assembly with all five endpoints for 3.0, 4.1 and 5.0, original values/statuses, hashes and independent scorer declarations | J-4f built generation; 5.x extraction/freezes; exact-generation scoring; independent acceptance; actual result artifact |
| J-5q-pr3091 | Existing C35 retained; snapshot alone and unknown snapshot digest cannot establish freshness; seal must identify a real matching chart/generation manifest | Separately dispatched exact-generation verification; exact-head independent child review and CI; controller-owned receipts and deployment containment |
| J-5q-a57 | Valence census, per-class/year plateau census, class/year computation coverage and pre-2020 availability diagnostics | A5.6; complete, independently verified generation readback; real solver/record evidence for fabricated instants; measured residual and independent acceptance |
| J-5q-b54 | 3.0/4.1/5.0 report sections with per-mechanism source attribution and P1–P6 ablation gaps explicitly disclosed | B5.3, A5.6, B4.3 and B4.4; baseline artifact readback, independent scoring, actual per-path ablation runs and accepted retrodiction residual |

The B4.4 dependency is retained. Surrogate answer 17 Q6 (`SURROGATE_ANSWER_17.md:25`)
requires actual historical baseline readback or the surrogate's explicit supersession
disposition; a code merge or an empty baseline section cannot satisfy it.

## Using the offline report assembler

Run from `platform/python-sidecar`, after constructing a local immutable input
bundle under the job folder. The command makes no database connection and never
runs the held-out scorer:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B -m services.gochara_eval.qualification_report \
  --inputs "$JOB_SCRATCH/qualification-inputs.json" \
  --output "$JOB_SCRATCH/qualification-preparation.json" \
  --markdown "$JOB_SCRATCH/qualification-preparation.md"
```

Exit 0 means **report assembled**, including when measurements fail or are absent.
Exit 2 means invalid inputs; no successful measurement or acceptance is implied.
Input files cannot be used as output files. Missing generations are represented
explicitly; rejected or hash-mismatched sources are refused.

The input JSON schema is `ky.qualification_inputs/1`:

| Field | Required content |
|---|---|
| `chart_id` | Actual chart UUID, bound to every supplied extract |
| `generation_authors` | Non-empty complete list of generation-author identities, read from the build record |
| `sources` | Object keyed only by `3.0`, `4.1`, `5.0`; omit an unavailable generation |
| `sources[g].path`, `.sha256` | Relative local scorer-result path and measured SHA-256 |
| `sources[g].scorer_id` | Actual scorer identity, distinct from **every** listed author; compared case-insensitively after trimming |
| `sources[g].extract` | Object with relative `path` and measured `sha256` for that result's actual extract |
| `diagnostic_extract` | Optional pinned `{path, sha256}` for normalized governed 5.0 rows |
| `coverage_cells` | Optional pinned `{path, sha256}` for the 5.0 class/year census |

Every source path is relative to the input bundle and stays within it. The scorer's
measured extract digest, declared pin and match flag must agree with the supplied
extract bytes. Extract chart/generation identity must match the section. Historical
3.0/4.1 exact SQL predicates are recognized; normalized inputs instead carry explicit
`chart_id` and `generation` fields. Candidate source results require
`mode: MEASUREMENT` and `freeze.status: VERIFIED`. These are **transcribed source
claims**, not a re-execution of freeze verification. The independently dispatched
reviewer must inspect both freeze stages and actor provenance; the identity strings
and hashes are not authenticated independent-review receipts.

Normalized diagnostic rows use the existing candidate adapter's `event_class`,
`ws`, `we`, `pk` (IST civil dates), and `si` (finite non-negative number or explicit
NULL), plus the **stored** `outcome_valence_for_native`. Preserve its governed enum
`favourable | adverse | mixed | unqualified` (`platform/migrations/1156_gochara_eval_window.sql:296`).
Do not turn legacy `gain/loss` labels into native outcome valence. The future 5.x
extract adapter must derive these fields from the actual governed rows, use the
addendum's `evidence_for` mapping, identify all source rows and qualify unknowns.
This tool does not supply that adapter or authorize inspection before Stage 2.

Coverage input has `{chart_id, generation, cells}`. Each cell has `event_class`,
integer `year`, and boolean `computed`. Computed-empty is true only when the engine
actually completed that cell. An excluded, unsearched or missing cell cannot be
called computed. Duplicate cells, unknown classes, out-of-horizon years and untyped
booleans are refused. The future readback must prove the cells from real coverage
partitions, not infer them from admitted windows or this schema's existence.

The output schema is `ky.qualification_preparation/1`. Each endpoint/gate has
`status`, `measured` and `predicate`. Original scorer statuses stay in `measured`
and the complete `source_result`; no diagnostic rank median replaces a VOID result.
The display mapping is explicit: typed source `pass: true/false` maps to
`pass/fail`; VOID to `not_evaluable`; UNQUALIFIED, UNVERIFIABLE, RANK-UNPROVEN,
PARTIAL or absent evidence to `insufficient_evidence`. This does not rewrite the
source verdict. T-FP retains overall, adverse and gain blocks. Missing measurements
stay NULL, not zero. Attribution and ablations are non-gating source disclosures;
missing P1–P6 ablations are listed by path, with no fabricated deltas.

## (I) INTERPRETATION — preparation predicates and alternatives

1. **Preparation, not residual completion.** Build offline helpers/runbook and
   retain `built_waiting_on_gate`; do not write the external result/residual paths.
   Alternative: emit placeholder residuals. Rejected because existence could be
   mistaken for measurement, and external writes exceed this job's box.
2. **Valence diagnostic.** Count all scored-horizon, non-anchor governed outcome
   labels; a fully known all-favourable census fails; any missing/unqualified label
   leaves it insufficient. Alternative: invent a required adverse percentage or
   promote occurrence evidence to native valence. Neither is specified.
3. **Peaks diagnostic.** Reuse the existing candidate admission merger, apply the strict representative tolerance, and report each
   populated scored class/year's adjacent-gap tie share at the protocol's strict
   `1e-9` tolerance; a share ≥50% fails that diagnostic, unknown representatives
   cannot establish pass. Alternative: an invented global peak-variance floor.
   This diagnostic does not replace the scorer's unknown-competitor enumeration.
4. **Coverage/pre-2020 diagnostic.** Use all 26 endpoint-eligible classes
   (`birth_anchor` excluded) and the 29 horizon years 1998–2026. Require a complete
   census before interpreting the ≥50% class coverage threshold. Pre-2020 availability
   requires all 572 class/year cells from 1998–2019 actually computed, including
   computed-empty. Fractions for incomplete censuses are observed lower bounds,
   not a claim that missing cells were uncomputed. Alternative: treat a missing
   class as absent from the denominator, or windows as proof of computation.
   Availability does not prove the serving reader answers a query.
5. **Exact-instant provenance.** The no-fabricated-instants gate stays
   `not_evaluable` with NULL measurement for date-only evidence. Alternative:
   infer correctness from a non-null peak or synthetic fixture seal. Rejected:
   real record/solver verification on the built generation is required.
6. **Inherited-source retrieval.** Use the already available exact source commit
   and verify both local refs rather than fetch. Alternative: write shared Git
   objects/refs outside the working copy. The job explicitly prohibits Git writes.
7. **Ablation completeness.** Enumerate P1–P6 because the campaign's B5 scope
   names those six paths; withheld/non-admitted paths need explicit qualified
   disclosures, not silent omission. Alternative: accept any non-empty ablation
   dictionary as complete. Both paths and original source data remain visible.

## Staleness compatibility and CI

`sealed_generation_staleness.py` retains fresh=0, stale=4, unable-to-check=3,
chart/generation scoping, existing database digest/census functions, and read-only
session enforcement. It now also requires a seal joined to its matching manifest
by manifest id **and** chart/generation. Migration 1153 deliberately has no seal
manifest FK (`platform/migrations/1153_gochara_sky_event_substrate.sql:892`).
An unsealed snapshot, dangling/cross-generation seal or missing stored digest is
an error, never fresh. No seal, manifest, reader or published-head row is changed.

All inherited PR #3091 tests remain. The new unit tests live in the automatically
collected sidecar `tests/` tree (`.github/workflows/ci.yml:2436`), whose shard plugin
assigns new files automatically (`platform/scripts/governance/pytest_plugins/sidecar_shard.py:16`).
New real-SQL tests are appended to the **already selected** C48a suite in the
required A5.3 DB job (`.github/workflows/ci.yml:553`); no workflow path list is changed.
That fixture's deliberately synthetic seals exercise SQL, not authentic
independent verification. No writer is modified, so writer aggregates require no regeneration. The
scorer's runtime `code_hashes()` measures both corrected merger files; future
freezes must use those new hashes. Old freeze artifacts are not edited.

## Later operation/review checklist (prepared, not executed)

1. Read back J-4f/A5.6's exact built generation, manifest and all original dependency
   artifacts. Have a separate dispatched verifier establish every included grain
   and the authentic seal. Preserve G8/protected-window controls.
2. Supply/review the governed 5.x extractor and generation-specific Stage-1/Stage-2
   freezes before inspection; bind the actual registry, controls, code, coverage,
   ephemeris and stored `evidence_for` mapping. Do not bypass the current refusal.
3. Use independent scorer(s), never a generation author, to run every co-primary
   endpoint and the real A5.7 engineering gates. Record weak scores unchanged.
   Obtain solver/record provenance rather than checking only date fields.
4. Read back accepted 3.0 and 4.1 baselines or the explicit surrogate disposition
   for a missing historical baseline; preserve B5.4's dependency. Run and disclose
   actual mechanism attribution and per-path ablations, including unavailable paths.
5. Assemble and review the hash-bound report; separately publish the real evaluation
   result and A5.7/B5.4 residuals only within the cockpit's authorized operation.
   Independent acceptance binds evidence digests and original prerequisites.
6. Review the exact final child head and run CI plus ported/mutation oracles.
   The controller alone derives per-child envelopes/step receipts. This builder
   writes no MET receipt, deployment claim, or production operation request.

## Supplied source hashes observed during preparation

| Source (relative to the supplied Pravāha brief root) | SHA-256 |
|---|---|
| `measurement/EVALUATION_PROTOCOL_v2_3.md` | `a8353dc48563e08710f1fc6815ace2f15b7e9db5eec5d4ebea1e6dde1120514e` |
| `measurement/EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_5.md` | `f9e3fb5685fe81b8c2c3a4761bea2b4d020798458b1259b22e216fbb8ae953bb` |
| `PRAVAHA_CAMPAIGN_PLAN_v1_0.md` | `54ecf3f2ffb20d229a042867818976ac6e0b53b862cee73f59a60ca45429d3a7` |

## Preparation verification

The scoped sidecar run passed **401 tests**, with no skips, against the guarded
local cluster at `127.0.0.1:55433` and the configured pinned local ephemeris path.
It included the entire `tests/l3/gochara_eval` suite, C35, and C48a. Three existing
pytest class-fixture deprecation warnings remain in inherited tests. The pinned
3.0 baseline oracle retained every recorded figure. A real historical-baseline
CLI demonstration, with explicitly synthetic demo identity and no candidate
scoring, also assembled successfully under the job folder.

**45 semantic mutations** failed their selected tests and passed with the behavior
restored. Separate copies with the inherited script restored prove both fixed
staleness defects fail on revert: snapshot-without-seal and unknown stored digest.
The scratch `verify_mutations.py`, `mutation-proofs.json`, `findings-fixed.json`
and per-case logs preserve the exact mutation operators, tests and exit codes.
The shared mutation copy is reused sequentially; the three finding-revert copies
remain reverted for review, including the diagnostic maximum-member correction. This is builder evidence, not independent review.

Local collection through `sidecar_shard` partitioned all four touched test files
without an explicit workflow edit. The required DB job already selects C48a.
The writer provenance inventory check and Git diff/whitespace checks passed. No exact-head CI run, independent child verdict,
production deployment or deployed-source containment is asserted by these results.
The cockpit must retain the working copy and job evidence until review/landing,
then perform its normal worktree and scratch cleanup. Fixture databases are
created/dropped by their guarded suites; this job neither starts nor stops the
shared test cluster.

### Exact-tolerance merger correction

The new census regression uses abutting January rows at SI 0 and SI `1e-9`,
a March candidate at 0, and a May candidate at 1. The January maximum is `1e-9`;
its strict-tolerance separation from March gives three distinct groups, not a
2/3 plateau. The shared mergers now select the distinct higher member at the exact tolerance
boundary inside the existing admission groups before counting ties (protocol §4.2/§8.3). Both shared evaluation mergers now
use `difference >= tau` for a distinct higher member and `abs(difference) < tau`
for a tie. A saved reverted copy proves the boundary regressions fail without
these comparisons. Unknown-member admission groups remain unqualified.

The canonical candidate and fully-known extract mergers are both corrected;
there is no diagnostic-only workaround. Separate mutants restore each of their
four former comparisons and must fail. The entire pinned 3.0 reproduction still
passes without changing any figure. Fresh candidate freeze hashes are required
before measurement; the reporter continues to preserve source results verbatim.

8. **(I) INTERPRETATION — shared merger repair.** Correct the two shared
   evaluation helpers as the minimal required footprint for consistent diagnostic
   and scorer behavior. Alternative: keep a diagnostic-only workaround and leave
   the canonical scorer's exact-tolerance boundary wrong. The FROZEN orchestrator
   contract is not changed; existing freeze documents are not rewritten.
