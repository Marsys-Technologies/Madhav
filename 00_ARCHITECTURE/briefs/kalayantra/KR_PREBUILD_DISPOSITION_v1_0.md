---
artifact: KR_PREBUILD_DISPOSITION
version: "1.0"
status: PARTIAL_PREPARATION — KR-1 and KR-2 are not complete
produced_on: 2026-10-16
base: 34c7e1acbd5e7c85dd200a0ed0f4924a835ab307
scope: A6 D-40; KR-1 and KR-2; branch preparation only
---

# Contract preparation and remaining inputs

This branch prepares independent KR-1 changes. It does **not** earn either
item's `built` outcome or authorize its landing. KR-1's complete contract phase
and KR-2's second-writer retirement remain unbuilt. K9-6 is still their landing
gate. No production operation, publication, migration, or activation is included.

Authority: `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:356`–`:363`, its §8.1,
`00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md:85`, and
`00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A6_PREBUILD.md:27` (§2, D-40).
The campaign charter's §1 delegates the session handshake/close to the campaign;
this job reports to that campaign through its result receipt.

## Prepared on this branch

* Grammar's local aspect table is removed. Its existing consumers import the
  kernel table, whose N-14 node entries are empty, including no seventh aspect
  (`platform/python-sidecar/services/gochara_kernel/convention.py:39`). Both
  point and whole-sign paths obey that convention. The grammar node locks in
  `brahmagyan/__tests__/test_aspects.py` are rewritten; the existing L0/L1 tests
  in that same file remain. The core sky parity test is rewritten from the
  pre-contract disagreement to the shared kernel table. No L0/L1 implementation changes.
* The second orb formula is named `cosine_orb_strength_score`. Saṅgam, trigger,
  and the Taraṅga service import/call that name. The ad-hoc scanner retains
  `orb_strength_score`; both existing formulas and multipliers are preserved
  and identified as their historical practice conventions. PLAN §3.1's
  intensity row (`KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:153`) distinguishes
  them, and §8 (`:362`) requires the rename.
* The unused `services/taranga_kernel` package is deleted. Its **44 passing**
  tests are archived unchanged, with original paths and SHA-256 values, in
  `99_ARCHIVE/kalayantra/kr1/README.md`. There was no external production
  importer. The replacement is K6-4's monthly field-integral projection,
  `platform/python-sidecar/pipeline/orchestrator/writers/ka_taranga.py:92`.
  Its ordinary dispatch remains inactive (`:99`); the branch's landing still
  waits for the campaign gate. The integral estimand is not represented as
  equivalent to the retired harmonic-mean or NBRY timing formulas.
* Kṣetra's internal `build_vedha_primitive` and `build_moorti_primitive` are
  removed. The existing importer `services/ka_kshetra/g1_inputs.py` now builds
  neutral mūrti testimony directly from upstream intervals and references,
  without calculating a tier-to-strength value. Its vedha path already reads
  `kala_vedha_gochara_interval`; its mūrti path uses the shared contested
  reader (`g1_inputs.py:116`). The former builder tests are rewritten against
  that interval consumer. S0/S1's continuous kinematic knot builders remain,
  per B8-6 (`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_RULING_SHEET_v1_0.md:233`).

The new `tests/l3/test_kr_contract_preparation.py` is discovered by the existing
sidecar CI test pattern (`.github/workflows/ci.yml:2438`). No CI path list changes
are necessary. The writer digest inventory is regenerated for the changed
transitive Python dependencies. The dependent capability-estate census is regenerated as well.

## Every remaining KR-1 family

Paths below are relative to `platform/python-sidecar/` unless specified.
A retained family is **not** claimed disposed by this branch.

| Family | Retained code / importer | Required replacement and remaining work |
|---|---|---|
| Saṅgam compatibility shim / engine | `pipeline/orchestrator/writers/ka_sangam.py:25` imports the legacy engine; its default dispatch still runs it | Admit live jury producers and stage-to-reader identity/field mappings, then migrate default writer and all readers. `services/ka_sangam/jury/reader_contract.json:34` leaves convergence/signal/peak/issuance identities unadmitted; `:39` explicitly defers retirement. A fixture candidate is not that replacement. |
| `taranga_service.py` | `routers/taranga.py:23` still imports its public API | Repoint the HTTP reader to the admitted projection/serving interface before deleting the service and rewriting/archiving its route tests. The private candidate writer currently supplies no replacement HTTP interface. |
| `kala_permission` | Historical admission harness `scripts/kala_admission/currents.py:86` still imports its constants | Retire or archive the old admission harness with its tests, then delete permission code and archive its formula tests. The judge's per-instant permission is the replacement. Repointing that historical experiment to a different model would change what it measured. |
| `kala_trigger` / `compose_with_ka_sangam` | `pipeline/orchestrator/writers/ka_sangam.py:45` still imports both | First remove the live legacy writer's score composition. The replacement negative-space boundary reports `trigger_survivor_roster_and_doctrine_unadmitted` (`services/kala_trigger/negative_space.py:17`); the survivor roster and doctrine admission are missing inputs. No detector is selected by inference here. |
| Grammar read models | `services/kala_core/promise/relationships.py:15` still imports grammar's derived points, alongside active legacy grammar users | Move each promised read model into core promise/clocks/ontology/rules and migrate its importers. Only the node table is contracted here; the directory is not retired. |
| `gochara_intensity` and v3 mechanisms | Active v1/v3, sweep, and W2G callers remain, including `services/w2g/materialize.py:61` | Retire with v1/v3. Preserve `enrich_targets`/`compute_x_t` only with an actual judge rule-path citation, per PLAN `:357`. The current jury does not provide that admission. |
| `w2g` | Writer `pipeline/orchestrator/writers/ka_gochara.py:105` still imports its fingerprint | Move arcs/crossings/solver to core sky and `class_fingerprint` to core manifest, preserving fingerprint bytes and per-class invalidation. No W2G file is claimed retired. The Pravāha kernel is unchanged. |
| `ka_temporal/date_resolver` | `pipeline/orchestrator/writers/ka_kalasutra.py:117` and `ka_vighnakara.py:541` still call the legacy resolver without `as_of_date` | Delegate through core clocks with explicit as-of and L1 build/tier pins, migrate every caller and rewrite clock tests. Core `clocks/__init__.py:157` requires those pins, while the legacy loader `date_resolver.py:328` lacks them. This branch does not silently choose a build/tier or preserve wall-clock fallback as if delegated. |
| `pipeline/transit_search.py` | Retained ad-hoc service, also still called by legacy stage code | The duplicate name is resolved here. Geometry cutover still requires retiring/migrating those legacy stage callers; the service itself remains per PLAN `:362`. |
| Kṣetra S4 vocabulary | Existing `moorti_at_ingress` covariate reader in `services/ka_kshetra/stage4_field.py:632` | The internal builders are removed; this reader vocabulary is not another mūrti computation and is left intact. New candidate testimony is neutral and uses `moorti_testimony`. No continuous-knot or field-model redesign is included. |

## KR-2 is left out

The default D-KR disposition is already specified as approved
(`00_ARCHITECTURE/control/kalayantra/plan_model.json:1817`). No new D-KR ruling
is requested or inferred. What is missing is the admitted live read mapping
and its published-head equivalence fixture.

The importer `brahmagyan/mimamsa/l5_event_chart_state_index.py:62` reads the
hardcoded `SIGNAL_ANCHORS`. At `:81` it requests `MALEFIC_CLUSTERS`, but the
source module actually declares `MALEFIC_DASHA_WINDOWS`
(`brahmagyan/kala/l3_obstruction.py:183`), so that import currently falls back
to an empty obstruction list. Its old output must be captured honestly; a
repoint that simply starts returning new obstruction records would not prove
unchanged output. The live jury contract also leaves its reader identities
unadmitted (`services/ka_sangam/jury/reader_contract.json:34`).

Consequently no second-writer deletion or L5 read change is included. The
hazards remain visible: `brahmagyan/kala/convergence.py:525` deletes chart rows
before inserting, and `brahmagyan/kala/obstruction.py:543` still writes
`kala_obstruction`. KR-2 requires a future patch with the actual admitted
published-stage mapping and canonical-chart index comparison. This is a
reported campaign gap, not an achieved retirement or an owner refusal.

## Interpretations and alternatives

1. **(I) INTERPRETATION:** pre-build the independent contract changes while
   reporting both parent items incomplete. Alternative: leave the entire
   packet unchanged until every replacement is admitted. No parent-item
   completion signal is earned by the partial changes.
2. **(I) INTERPRETATION:** “second orb formula” means Saṅgam's cosine formula,
   in the order PLAN `:153` lists them. Alternative: rename the ad-hoc linear
   function. The scanner's existing public API is retained.
3. **(I) INTERPRETATION:** retire the unused Taraṅga kernel independently of
   the still-imported HTTP service. Alternative: retain both until HTTP
   cutover. The archive and direct import-retirement detector make the split
   explicit; the whole Taraṅga family is not called retired.
4. **(I) INTERPRETATION:** neutral mūrti testimony uses a zero envelope and
   preserves both upstream edges; no unadmitted tier-to-strength mapping is
   evaluated. Alternative: construct the old scalar envelope and then mark
   it neutral. The existing upstream reader already declares that a numeric
   bridge is not admitted (`services/ka_kshetra/g1_inputs.py:5`).


## Verification limits of this job

The affected database tests use the guarded existing cluster on
`127.0.0.1:55433`. The old broad migration-test helper
`platform/python-sidecar/tests/pg_disposable.py:70` instead runs `initdb` and
starts another server on a random port. Initial broad runs reached those
fixtures; their server starts failed because the permitted scratch path is
longer than PostgreSQL's Unix-socket limit. Those failures are not evidence
against the contract changes, and are not a successful database test.

Subsequent broad verification loads a **job-only** audit guard before test
collection. It rejects server creation/start/stop commands before execution;
unsupported fixtures remain explicit setup errors. The guard also records
individual test outcomes. It neither substitutes fake data nor repoints an
unguarded legacy fixture at the shared cluster. No repository fixture or L0
implementation is changed. Exact results and retained logs are in the job
receipt, not a claim that the whole suite passed.

On macOS, the default 256-file process limit also fails the existing S4
forced-spill tests. All 13 bounded-memory hash cases pass after raising only
the test process's soft file limit to 4,096; the S4 hashing source is unchanged.
The final guarded run uses that limit. Test dependencies and all transient
test paths are confined to the job folder; the pinned ephemeris remains the
owner-provided read-only corpus.
