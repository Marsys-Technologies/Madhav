---
artifact: NIKASHA_TEST_CAMPAIGN_REPORT
canonical_id: NIKASHA_TEST_CAMPAIGN_REPORT
version: "1.0"
status: FINAL
campaign_id: nikasha-test
phase: 7 (report and handoff)
produced_on: 2026-09-27
branch: campaign/nikasha-test (from origin/l3/kala-layer-briefs)
phase_commits: {P0: c63ca0774, P1: 9495fb1a8, P2: [b02c7b62d, 871b4d4eb], P3: 55bd085e8, P4: 7c26bdea4, P5: d9772f295, P6: 1c4e729b1}
model_routing: K3_256 at LOW effort for the entire campaign, phases 0–7 (native instruction 2026-09-26; no model switch)
tested: >
  The Nikaṣa system — tier 1 `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md`,
  tier 2 `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`,
  tier 3 `briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`,
  tier 4 `briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md`,
  the inspector `platform/scripts/governance/asset_census.py`,
  the tracker `00_ARCHITECTURE/control/asset_elevation_tracker.py`,
  the ledgers `asset_gaps.jsonl` / `asset_certs.jsonl`,
  and the drift/fingerprint detectors `drift_detector.py`, `manifest_fingerprint.py`,
  `check_migration_ledger_vs_production.py` — exercised against all six layers L0–L5.
mode: >
  sandbox + production read-only. Every mutation ran against `nikasha_sandbox`
  (local PostgreSQL, port 54329, seeded read-only from production); every production
  read went through the read-only proxy (`source /Users/Dev/madhav-l3/dbenv.sh;
  export PGPORT=5433`; `default_transaction_read_only = on` verified at P0).
  Tiers 1–3 were never edited; every change they need is a register row.
register: NIKASHA_CHANGE_REGISTER_v2_0.md (214 rows, R01–R214; v1.0 retained, superseded)
companions: [nikasha_test/PHASE6_ANALYSIS.md, NIKASHA_IMPLEMENTATION_PLAN_v1_0.md, nikasha_test/DECISIONS_FOR_THE_NATIVE.md, nikasha_test/STATE.md, nikasha_test/EVENTS.jsonl]
verdict: NOT_READY_TO_FREEZE
---

# Nikaṣa test campaign — final report

**Verdict: NOT_READY_TO_FREEZE.** The freeze criterion — all five tests passing in production
tooling, every register row closed or explicitly deferred — fails on three of five tests: T2 (the
inspector invents verdicts: 60 hand-verify disagreements, all instances of R42/R43/R46), T3 (a fix
cannot close a row in the stock tooling: R57/R58 — proven FAIL in production tooling, proven PASS
only with the campaign's scratch closing copies), and T5 (22 open consistency findings including the
BLOCKS_FREEZE [TRANSFERS] contradiction R71 and the live tier-4 fingerprint drift R82). T1 is
PARTIAL (17/17 planted defects detected, but only in the sandbox and only against the stock
inspector's plantable checks; three checks are structurally unplantable) and T4 is PARTIAL (census
executes on four of five non-reference layers in production; L3 is NOT_RUNNABLE there — R40/R41).
The inspector itself is **NOT_READY**, tier 3 is **NOT_READY** (its §0.1 is unfillable on every
layer — the P-need/V-journey→layer mapping exists in no tier), and the closure loop — the thing the
whole system exists to do — is absent from the shipped tooling. The path to a sealable system is the
10-packet implementation plan (`NIKASHA_IMPLEMENTATION_PLAN_v1_0.md`, ≈365 h, every OPEN row
assigned), gated by the six rulings in `DECISIONS_FOR_THE_NATIVE.md`; the freeze decision should
rest on a second pass of this campaign after those packets land (§9 below), not on this one.

What is sound and worth saying first: the inspector's detection core is real — every one of 17
planted defects moved exactly the planted asset's verdict with zero cross-asset collateral, and a
mutation test proves the suite notices an inverted detector (T1 §1, §3). The closure loop, once
built as a ~70-line change, works end to end including regression — `bg_nakshatra_medical` went
GAPS_REGISTERED → ELEVATED (tracker 0/40 → 1/40, gates 0/360 → 9/360) and back (T3 §4–5). And the
largest defect cluster is not a bug but a missing artefact: no tier maps the product's needs to the
layers (C8, ~150 of 214 rows), which is a writing task, not a repair.

Verdicts vocabulary used throughout, exactly these spellings: `PASS` · `FAIL` · `PARTIAL` ·
`NO_DETECTOR` · `N/A` · `NOT_MEASURED` · `NOT_RUNNABLE`. Line numbers are each file's own at the
commit cited. Register row ids (R<nnn>) refer to `NIKASHA_CHANGE_REGISTER_v2_0.md`; the register's
214 rows are not restated here — only the headline findings are quoted in full (§7).

## Component inventory at baseline (Phase 0.4)

Population: every Nikaṣa component, instrumented by `sha256` (first 12 hex) and `git log -1
--format=%h`. Source: `nikasha_test/STATE.md` component table, reproduced at c63ca0774.

| component | version | status | sha256(12) | last commit |
|---|---|---|---|---|
| MADHAV_PRODUCT_DEFINITION_FINAL.md (tier 1) | FINAL | SEALED | b9c098cd390d | 62b9c34ce 2026-09-25 |
| MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md (tier 2) | FINAL | SEALED | a7eaf821bf65 | 090bd9aaa 2026-09-26 |
| LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (tier 3) | FINAL | SEALED | 137ba6b9a415 | 090bd9aaa 2026-09-26 |
| ASSET_ELEVATION_TEMPLATE_v2_0.md (tier 4) | 2.0 | DRAFT_PENDING_REVIEW | 244e87dff30a | b598c3b63 2026-09-26 |
| MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md (L0 instance) | 3.0 | DRAFT_PENDING_ACCEPTANCE | 2233d00ad48d | 090bd9aaa 2026-09-26 |
| l0_assets/*.md (five pilot briefs) | 1.0 | PILOT_DRAFT | (per-file, STATE.md) | 2026-09-26 |
| platform/scripts/governance/asset_census.py (inspector) | — | — | 1158bc8543ec | b598c3b63 2026-09-26 |
| 00_ARCHITECTURE/control/asset_elevation_tracker.py (tracker) | — | — | 607b1fcbd790 | 090bd9aaa 2026-09-26 |
| 00_ARCHITECTURE/control/asset_gaps.jsonl | — | 262 data rows | 0bc05eacd6c0 | abe4bc1d8 2026-09-26 |
| 00_ARCHITECTURE/control/asset_certs.jsonl | — | 1 data row | 4d45d8a3a513 | 5973d0132 2026-09-26 |
| platform/scripts/governance/drift_detector.py | — | — | 0f37efd64dfc | ffe2e12d0 2026-09-25 |
| platform/scripts/governance/manifest_fingerprint.py | — | — | 4e33035b7a84 | 6ef745576 2026-09-25 |
| platform/scripts/governance/check_migration_ledger_vs_production.py | — | — | 87b8c0f866a6 | 6ef745576 2026-09-25 |

Interpreter for all governance scripts: `/opt/homebrew/opt/python@3.13/bin/python3.13` (system
python3 lacks PyYAML — EVENTS phase 0, `ENVIRONMENT_REPAIR`).

## 0 · Phase 0 — orientation and baseline (commit c63ca0774)

Tests: read-only posture verification; fingerprint/drift baseline; L0 inspector and tracker
baseline; disposition of the 25 then-OPEN register rows.

| figure | value | reproduction |
|---|---|---|
| Read-only posture | `default_transaction_read_only = on` | `source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433; SELECT current_setting('default_transaction_read_only')` — EVENTS P0 |
| Manifest fingerprint | **MATCH** — 136 entries, declared == observed `7794567b405a9207` | `python3.13 platform/scripts/governance/manifest_fingerprint.py --check` |
| Drift detector | **3 findings, exit 2** — 1 HIGH (`ASSET_ELEVATION_TEMPLATE` fingerprint: declared `bb341cc1…` vs on-disk `244e87dff3…`, the v1.1→v2.0 edit never rotated → R82), 2 LOW environmental (`schema_db_unreachable`) | `python3.13 platform/scripts/governance/drift_detector.py`; `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T112959Z.{json,md}` |
| Census L0 (production, 65.1 s) | 40 assets; 36 registered ids vs 34 `has_writer=true`; 67 global runs, 0 touching L0; never-exercised-with-writer: `bg_sign_medical`; **FAIL 119 · PARTIAL/NO_DETECTOR 90** | `asset_census.py --layer L0`; `nikasha_test/census/L0_prod_baseline_20260926.json` |
| Tracker L0 | 40 assets GAPS_REGISTERED, ELEVATED 0/40, open gaps 239, open opportunities 18, gates certified **0/360** | `00_ARCHITECTURE/control/asset_elevation_tracker.py` run at P0; STATE.md P0.5 |
| Ledgers | `asset_gaps.jsonl` 262 data rows (243 gap / 19 opportunity; 261 OPEN, 1 IN_PROGRESS); `asset_certs.jsonl` 1 data row | `python3 -c` Counter over parsed JSONL; STATE.md P0.5 |

All 25 OPEN rows dispositioned (test / fix / fix-as-harness / verify / carry) as one EVENTS line
each; rulings #9–#17 of `NATIVE_DECISIONS_2026-09-25_v1_0.md` absorbed as binding.

## 1 · Phase 1 — the sandbox (commit 9495fb1a8)

Built `nikasha_sandbox` (local PostgreSQL, socket `nikasha_test/.sandbox`, port 54329, user
`sandbox`) from read-only extraction of production; `session_replication_role=replica` persisted.

| figure | value | reproduction |
|---|---|---|
| Tables copied | **183 tables, 0 COPY_FAIL** | `harness/build_sandbox.sh` + `extend_sandbox_fix.sh` logs; `harness/SANDBOX_MANIFEST.json` (per-table prod rows vs sandbox rows, sampling rule, DDL sha256) |
| Fidelity check (itself a test) | L0 census sandbox vs production: **3 diffs, all sampling-induced, 0 unexpected → FIDELITY PASS** | `harness/census_diff.py` over `census/L0_prod_baseline_20260926.json` vs `census/L0_sandbox_20260926.json`; `census/fidelity_L0.md` |

Harness root causes recorded for re-use (EVENTS phase 1): macOS bash 3.2 lacks `mapfile`;
`dbenv.sh` PGOPTIONS read-only leaks into sandbox connections (wrapped by the `spsql` helper);
pgvector 0.8.6 compiled for postgresql@15; FK copy ordering solved by `session_replication_role`;
generated columns need explicit COPY column lists. **R47 registered here**: the census `--out` path
default overwrites a production artefact — a census pointed at the sandbox must not write where a
production read expects its own file.

## 2 · Phase 2 — T1 and T2, every layer (commits b02c7b62d, 871b4d4eb)

### T2 — does the inspector invent what isn't there? (production read-only; L3 via sandbox)

Census sweep runtimes: L1 80 s, L2 81 s, L4 44 s, L5 27 s (JSONs `census/{L1,L2,L4,L5}_prod_20260926.json`);
L0 65.1 s at P0. **L3 and `--layer all` FAIL to run on production**: `asset_census.py:95` hardcodes a
180 s psql timeout and `Vocab.identity`'s `count(DISTINCT (chart_id,event_class,segment_index))` over
`kala_field` (10.3M rows) exceeds it; one check's exception aborts the entire layer census (R40, R41).
Ground truth measured by hand: `kala_field` duplicates = 0 in 47 s (`/tmp/kala_field_dupcount.txt`,
STATE.md P2). L3 was therefore censused on the sandbox (2.5 s, `census/L3_sandbox_20260926.json`).

Hand verification: 60 assets, stratified across every asset kind present (L0 8, L1 12, L2 8, L3 11,
L4 9, L5 12), every census verdict cell re-derived by independent query or grep against production
(protocol `harness/T2_PROTOCOL.md`; per-layer reports `handverify/L{0..5}_T2.md`).

| check | L0 | L1 | L2 | L3 | L4 | L5 | total | register row |
|---|---|---|---|---|---|---|---|---|
| Build.completion | 0 | 12 | 8 | 8 | 9 | 4 | **41** | R42 |
| Build.registered | 0 | 0 | 0 | 4 | 1 | 2 | **7** | R43 |
| Build.contract (N/A cascade) | 0 | 0 | 0 | 4 | 1 | 2 | **7** | R43-derived |
| Idem.pattern | 0 | 0 | 1 | 1 | 1 | 2 | **5** | R43-derived / R46 |
| all other 14 checks | 0 | 0 | 0 | 0 | 0 | 0 | **0** | — |

**Total verdict disagreements: 60 over 60 hand-verified assets — every one an instance of an
already-registered defect (R42, R43, R46). No new false-positive pattern.** L0 itself: 0
disagreements over ~120 cells (one wrong rationale string, `bg_text_index` Idem.pattern). Evidence
rows also logged: R44 (non-latest `asset_throughput` rows quoted by Earn.build_record /
Cost.baseline), R45 ("all lit" false under stale-only deps), R49 (stale error text), a
Build.exercised off-by-one (ga_dashas 108 vs 107) and Dens.served module-attribution errors (L4).
Source: `handverify/T2_SUMMARY.md`. Layer-level `registered_ids` counts wrong wherever R43 fires
(L4 8 vs 9; L5 12 vs 14) — same root cause.

### T1 — does the inspector find what is there? (sandbox only)

Harness: `harness/plant.py` (17 plants), `harness/mutation_test.py` + `asset_census_mutant.py`,
`harness/differential.py`. Raw: `harness/T1_RESULTS.json`, `T1_MUTATION.json`; per-plant censuses
`census/plants/*.json`. Run pattern per plant: `PGHOST=…/.sandbox PGPORT=54329 PGUSER=sandbox
PGDATABASE=nikasha_sandbox PGOPTIONS= python3.13 platform/scripts/governance/asset_census.py
--layer L<n> --out census/plants/<plant>.json`.

- **Planted suite: 17 plants across 15 of 18 inspector checks — 17/17 detected for the planted
  asset and no other (`collateral=[]` on all 17), all restored clean.** Full table:
  `harness/T1_RESULTS.md` §1.
- **Mutation test**: inverting `Vocab.identity`'s comparison flips the planted-duplicate verdict
  PASS↔FAIL; `suite_notices=true` — the harness can fail (T1_RESULTS.md §3).
- **Differential test**: independent reimplementation of `Vocab.identity` / `Build.registered` /
  `Count.floor` over all six layers: **265 agreements, 99 disagreements all classed, 0
  unclassified** (9×R46, 19×R48, 13×R43, 57×R56, 1 methodology) — `harness/T1_DIFFERENTIAL.md`.
- **False-negative findings (new rows R52–R56)**: T1-FN1 `Build.completion` inverts on data
  destruction (planted TRUNCATE of `bg_muhurta_lattice` read FAIL→**PASS**, "live=0 and
  rows_written=0 — consistent") — sharpens R42; T1-FN2 `Build.target`'s FAIL branch is dead code
  under the `asset_kind` CHECK; T1-FN3 `Vocab.alias` severity is verdict-invisible (FAIL
  saturation, 79/741 → 741/741 empty with no verdict movement); T1-FN4 `Earn.build_record ≡
  Cost.baseline` is one detector, constant-FAIL (`rows_per_second` NULL everywhere); T1-F1 → **R56**:
  `Count.floor`/`Build.completion` silently absent on 57 assets with parameterized/multi-table
  `count_sql`, hiding real floor breaches the differential reports (ga_vargas 0 < 22 092; bo_laksana
  7 409 < 60 000; ph_sankrama 630 < 2 510).
- **NOT_MEASURED by planting**: `Complete.width`, `Carr.detector`, `Reach.fields` — constant
  verdicts, no per-asset input to mutate (T1_RESULTS.md §5). R25 CLOSED (plant mode built).

## 3 · Phase 3 — T3, the closure loop, never run before (commit 55bd085e8)

Question (R33): can a gap row be **closed by measurement** — census → CLOSED → cert record →
tracker increment — and re-open when the defect returns? Full narrative with quoted ledger rows:
`harness/T3_CLOSURE_LOOP.md`.

Three gaps of three kinds fixed in the sandbox exactly as production would: `bg_ontology-Vocab.alias`
(data: `harness/t3_seed_dosha_aliases.py`, 79/79 dosha synonyms seeded), `bg_nakshatra_medical-
Build.registered` (registry: `has_writer=true`), `bg_doshas-Idem.pattern` (detector:
seeder-following `idem_scan` in `harness/asset_census_closing.py`).

**Result: FAIL in stock tooling, PASS with the scratch port.** Stock `emit_gaps`
(`asset_census.py:576`) appends OPEN rows and skips existing ids — there is no closure path at all;
the stock tracker (`asset_elevation_tracker.py:200`) reads gap state per row, so even an appended
CLOSED row would not close the earlier OPEN one. Together = **R57, the campaign's headline
finding**. The scratch copies (`harness/asset_census_closing.py` with append-only CLOSED/RE-OPENED
rows keyed by deterministic gap_id, `harness/tracker_sandbox.py` with last-wins-per-gap_id and
`NIKASHA_CONTROL_DIR` redirection) make it work:

| figure | value | reproduction |
|---|---|---|
| Closures, run 1 (data+registry+detector fixes) | **25 rows closed by measurement**, incl. all three chosen rows; 4 appended; 184 already present | closing census over `harness/sandbox_control/`; `census/t3_after_fixes.json` |
| Cascade (R61) | the registry fix opened a true new gap `bg_nakshatra_medical-Build.exercised` — closed by actually running `BgMedicalMappingsWriter` (run `c0db4bc1`, 60 rows, real throughput) | `harness/t3_run_writer.py`; `census/t3_after_all_fixes.json` |
| Closures, run 2 | 11 more; `bg_nakshatra_medical` all 7 rows CLOSED | same |
| Certification | 9 cert records (one per gate) written to the sandbox `asset_certs.jsonl` copy | `harness/sandbox_control/` |
| Tracker movement | ELEVATED **0/40 → 1/40**; gates certified **0/360 → 9/360**; open gaps 239 → 207 | `harness/tracker_sandbox.py` before/after |
| Regression | `has_writer` true→false → exactly **1 RE-OPENED** row, ELEVATED 1→0 (CERTIFIED_GAPS_OPEN); re-fix re-closed → 1/40 | `census/t3_regressed.json`, `census/t3_reclosed.json` |
| Hygiene side-findings | R58 (hand rows have no detector binding — unclosable by construction), R59 (`ashtanga hridayam` cited 27×, not admitted — the first real D1 detector honestly failed first, then passed 27/27), R60 (Ldgr misses singular `classical_citation`), R62 (sandbox census emits prod-scale Count.floor rows) | T3_CLOSURE_LOOP.md §8 |

Sandbox verified restored to baseline; `platform/` and `00_ARCHITECTURE/control/` git-clean;
production ledgers untouched (263/1 lines throughout). **R33 CLOSED.** What had to be built (~70
lines total to port): ledger redirection, closure semantics in emit_gaps, last-wins gap resolution
in the tracker, seeder-following idem_scan, a per-asset Carr detector convention, a harness
orchestrator pass, a deterministic alias seeder — T3_CLOSURE_LOOP.md §7; this list is the core of
plan packet P3.

## 4 · Phase 4 — document derivability by a fresh reader (commit 7c26bdea4)

Derived five layer-instance skeletons (tier 3 + tiers 1–2 + the layer's census only) and ten test
asset briefs (two per layer: one ordinary writer-backed, one edge kind). Artefacts:
`derivations/L{1..5}_INSTANCE_SKELETON.md` (marked TEST ARTEFACT — NOT AN INSTANCE),
`derivations/L{1..5}_INVENTIONS.md`, `derivations/{GA_PRASHNA,GA_TAJAKA,BO_DRISHTI,BO_SAMVADA,
KA_DASHA_KALA,KA_KALASUTRA,PH_MUHURTA,PH_RECTIFICATION,MI_BHARA,MI_KULA}_BRIEF_TEST.md`.

| figure | value | reproduction |
|---|---|---|
| Inventions registered | **130 rows (R85–R214)** — L1 15 · L2 30 · L3 49 · L4 18 · L5 18 (L1's own footer claims 17 while listing 15; two folded, no source line dropped — register §5) | per-layer `L<n>_INVENTIONS.md`; register §2.8 |
| Universal blocker | tier-3 §0.1 is **unfillable on every layer** — no P-need/V-journey→layer necessity mapping exists in any tier | every skeleton; register §2.8 primaries R85 et al. |
| C-9 (per-asset carriage check unassignable, R09) | **confirmed on all five non-reference layers** (R92, R112, R144, R190, R204; sixth instance R159/R174) | skeletons, row-13 fill attempts |
| C-10 (multi-producer shared tables, R06) | confirmed L1/L2/L3/L5; **refuted on L4** | skeletons |
| [TRANSFERS] contradiction (R71) | hit on three layers (R94, R119, R140, R185) — see §7 headline findings | skeleton derivations vs T2 §1/§12.2 vs T3 §5.4 test 4 |

The 130 P4 rows collapse onto ~20 primary rows; the rest are `depends_on` transcription rows
(PHASE6_ANALYSIS.md §6.3, cluster C8).

## 5 · Phase 5 — T5, do the pieces agree (commit d9772f295)

Surfaces checked: the four tiers, the L0 instance, the five pilots, the inspector, the tracker, both
ledgers, the manifest — gate keys and count, verdict vocabulary, ledger states, `kind`, SHAPE
markers, criterion strings, "ten obligations", [TRANSFERS], version/status vs manifest, the
"review record" names, and every count one document states about another. Reports:
`consistency/T5_VOCABULARY.md`, `consistency/T5_LEDGER_DRIFT.md`. **22 register rows (R63–R84).**

- **17 vocabulary disagreements (V1–V17)**: the gate count drift ("the eight gates" on five
  surfaces where the set is nine — V1/V2/V3/V5, plus the tracker's stale "Eight, not thirty-three"
  comment V4 → R66); verdict-spelling drift (`NO DETECTOR` ×2 in T3, bare `NA` in T4 — V6); the L0
  instance's self-contradicting denominators (0/320 in four places vs its own 360 — V7) and
  no-longer-reproducing status figures (V8); the [TRANSFERS] contradiction (V9 → R71); tier 1's
  `review_record` pointing at a file that exists nowhere (`REVIEW_PRODUCT_DEFINITION_v3_1.md` —
  V10 → R72, its "11 MAJOR + 14 MINOR, all folded" claim unverifiable); tier 2's miscounted review
  summary (V11) and changelog (V13); "ten obligations" without its reason at T3 (V12); two
  criterion strings for one check (V15); three artefacts named "review record" (V16); five pilots
  carrying eight gates against a nine-gate tracker (V17).
- **7 agreements (A1–A7)**: SHAPE markers, verdict closed set, ledger states, `kind`, gate keys and
  the Dom→Carr rename, cross-document counts verified against census JSON and manifest
  fingerprints, cert record shape.
- **Ledger reconciliation**: 262 data rows = 209 census rows + 53 hand-written; **11
  duplicate-in-substance hand↔census pairs** measured (both rows of each pair quoted verbatim in
  T5_LEDGER_DRIFT.md §A); the reliable discriminator is `owner == "asset_census"`; single-namespace
  proposal recorded (R28 scope, R78–R81).
- **Governance detector runs**: `drift_detector.py` — 3 findings, exit 2; the expected HIGH
  (ASSET_ELEVATION_TEMPLATE fingerprint) confirmed verbatim; the two LOW `schema_db_unreachable`
  are an unreachable instrument reporting noise (R83). Report verbatim:
  `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T172934Z.{json,md}`. Command:
  `python3.13 platform/scripts/governance/drift_detector.py`.
  `manifest_fingerprint.py --check` — **MATCH, 136 entries, `7794567b405a9207`**, exit 0.

## 6 · Phase 6 — analysis (commit 1c4e729b1)

Register extended to v2.0 (214 rows, nothing deleted; R85–R214 added): OPEN 197 · DONE 15 ·
CLOSED 1 (R33, by the T3 sandbox proof) · MEASURED 1 (R84); severity BLOCKS_FREEZE 12 ·
BLOCKS_LAYER 107 · DEGRADES 83 · COSMETIC 12; every row carries severity, `depends_on`, effort.
Root-cause clustering: eight clusters cover all 197 OPEN rows — C1 completion/counting logic (6),
C2 grep/registration limits (2), C3 latest-row selection (3), C4 silent coverage + no fault
isolation (5), C5 closure absence (7), C6 ledger namespace split (3), C7 documentation drift after
ruling 17 (16), C8 derivability absence (~150) — plus unclustered singletons and the build-system
section R34–R39. Two inspector clusters (C1+C4) produce all 60 T2 disagreements and all three known
hidden floor breaches; one tooling cluster (C5) makes the entire closure loop impossible; C7 is the
price of reopening sealed documents without a re-render pass; C8 is a single architectural omission
— the tiers define products and layers but never the mapping between them. Deliverables:
`PHASE6_ANALYSIS.md`, `NIKASHA_IMPLEMENTATION_PLAN_v1_0.md` (10 packets, ≈365 h), and
`DECISIONS_FOR_THE_NATIVE.md` (six native-only decisions, each with recommendation and option
costs — referenced here, not duplicated).

### Readiness verdicts per component

| component | verdict | deciding rows |
|---|---|---|
| Tier 1 (product definition) | READY_WITH_CHANGES | R01, R72, R76 |
| Tier 2 (data plane) | READY_WITH_CHANGES (one BLOCKS_FREEZE contradiction) | **R06, R71**, R73, R75 |
| Tier 3 (layer template) | **NOT_READY** | **R08, R09, R71**, R65, R67, R68, R74, R85 |
| Tier 4 (asset template) | READY_WITH_CHANGES | R14, R63, R64, R68, R82 |
| Inspector (`asset_census.py`) | **NOT_READY** | **R40, R41, R42, R52, R56, R57**, then R20, R22, R43–R46, R48–R51, R53–R55, R60 |
| Delta ledger (`asset_gaps.jsonl`) | READY_WITH_CHANGES | R58, R62, R78–R81, R15, R29 |
| Certification ledger (`asset_certs.jsonl`) | READY_WITH_CHANGES (unexercised in production: 1 data row, never written by a production run) | R57 (indirect) |
| Tracker | READY_WITH_CHANGES | R57(b), R30, R31, R66 |
| `drift_detector.py` | READY_WITH_CHANGES | R82 (content), R83 (instrument hygiene) |
| `manifest_fingerprint.py` | READY | — |
| `check_migration_ledger_vs_production.py` | READY (unexercised — never fault-injected; failure modes NOT_MEASURED) | — |

### Freeze criterion, evaluated (per test, per layer)

| test | L0 | L1 | L2 | L3 | L4 | L5 | verdict |
|---|---|---|---|---|---|---|---|
| T1 finds what is there | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | **PARTIAL** — sandbox only, stock inspector's plantable checks only; 3 checks NOT_MEASURED |
| T2 does not invent what isn't | PASS (0 / ~120 cells) | FAIL (12 + R44-class) | FAIL (8) | NOT_RUNNABLE on production (R40/R41); sandbox-measured | FAIL (9) | FAIL (4) | **FAIL** — 60 disagreements, all R42/R43/R46 |
| T3 a fix closes a row | FAIL stock / PASS with scratch port (sandbox) | untested | untested | untested | untested | untested | **FAIL in production tooling** (R57/R58); fix proven: 25+11 closures, regression both ways |
| T4 works on a layer it wasn't built against | reference layer | RUN | RUN | NOT_RUNNABLE on production (R40/R41: 180 s timeout on kala_field, 10.3M rows; ground truth dups=0 in 47 s by hand) | RUN | RUN | **PARTIAL** — production runtimes 80 s/81 s/44 s/27 s; L3 sandbox 2.5 s; C-10 refuted on L4, confirmed elsewhere |
| T5 the pieces agree | — (cross-cutting) | — | — | — | — | — | **FAIL** — 22 open findings R63–R84, incl. BLOCKS_FREEZE R71 and live fingerprint drift R82 |

### What the campaign could not test (abridged; full table PHASE6_ANALYSIS.md §6.6)

`Complete.width`/`Carr.detector`/`Reach.fields` sensitivity (nothing to plant); `Earn.build_record`/
`Cost.baseline` in the defect direction (constant-FAIL at baseline — `rows_per_second` NULL in
268/268 `asset_throughput` rows); the L3 census on production (R40/R41); closure against production
ledgers (read-only constraint §2.1 — needs the R57 port plus one supervised production closure run);
hand-written rows closing by measurement (R58, unclosable by construction); the [TRANSFERS]
obligations' real home (the retrieval/conversation planes are not built); tier 1's review fold
(its `review_record` file does not exist); synergy terms (no ablation harness exists, R105);
deployed-vs-current-code baseline (R87); `check_migration_ledger_vs_production.py` under fault.

### Build system, re-verified at analysis time (P6 production read-only queries, EVENTS `P6_MEASUREMENTS`)

| figure | value | reproduction |
|---|---|---|
| Assets in registry | **129** (brahmagyan 40 · bodha 23 · ganita 19 · kala 23 · mimamsa 15 · phala 9) | `SELECT layer, count(*) FROM asset_registry GROUP BY layer` |
| Build runs | **762** — tier 4 §4.2 says 776 (**drifted**); completed 328 · failed 419 · stopped 15 | `SELECT state, count(*) FROM build_runs GROUP BY state` |
| Run↔asset rows | **6 823** over **124** distinct assets | `SELECT count(*), count(DISTINCT asset_id) FROM build_run_assets` |
| L0 never run / errored-or-aborted | **5/40** · **13/40** (confirm tier 4) | `build_run_assets ⋈ asset_registry` anti-join / state join |
| skip_no_delta | **17 assets / 61 rows** — tier 4 says 21 (**drifted**) | `build_run_assets` disposition = 'skip_no_delta' |
| Rate baseline | `rows_per_second` NULL in **268/268** rows — no rate baseline exists anywhere (R34 re-verified) | `SELECT count(*) FROM asset_throughput WHERE rows_per_second IS NULL` |
| Silent failures | **288/419** failed runs carry no error text (R35 re-verified) | `build_runs` state='failed' AND error text null/empty |
| Run-killer | registry change mid-run aborts every asset in the run — 18 assets across 8 runs, incl. a 10-asset L0 run aborted in full 2026-09-04 (R36 evidence stands) | `BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md` + `build_runs` failure join |
| Sole DRAFT asset | `bg_vidhi_floors` | `SELECT asset_id FROM asset_registry WHERE catalog_status='DRAFT'` |

## 7 · Headline findings (quoted, with replacement text)

The register's 214 rows are not restated; these six carry the verdict. Proposed replacement text
is the register's own.

**R57 — the closure loop is impossible in the stock tooling** (BLOCKS_FREEZE; the campaign's
headline finding). `emit_gaps` (`asset_census.py:576`) "appends rows with deterministic id
`<asset>-<criterion>`, **skipping ids already present**; `owner="asset_census"`, `change=""`,
`state="OPEN"`" — no CLOSED path exists; and the tracker (`asset_elevation_tracker.py:200`) "reads
gap state **per row**, so even an appended CLOSED row would not close the earlier OPEN one".
Replacement (proven in sandbox): append-only CLOSED/RE-OPENED rows keyed by deterministic gap_id;
last-wins-per-gap_id in the tracker; `NIKASHA_CONTROL_DIR` redirection of the hardcoded
`00_ARCHITECTURE/control/` path. ~70 lines, ported from `harness/asset_census_closing.py` and
`harness/tracker_sandbox.py`.

**R42 / R52 — `Build.completion` is unreliable in both directions** (BLOCKS_FREEZE). R42:
"`Build.completion` emits `N/A "no count_sql"` although `count_sql` is non-null layer-wide, and on
multi-table assets it compares the registry `count_sql` result against itself (mi_kula: count_sql
15 vs live 11 scored PASS)". R52 sharpens it from the plant suite: "emptying a table whose build
record agrees with the emptiness flips the check FAIL→**PASS** (planted TRUNCATE of
bg_muhurta_lattice read 'live=0 and rows_written=0 — consistent'). It is a rows_written↔live
consistency test, not a non-emptiness test — destroying data makes the asset look healthy."
Replacement: split the check — non-emptiness against the declared floor and population rule (with
an honest verdict for views and empty-by-design assets) separately from rows_written↔live
consistency; the TRUNCATE re-plant must FAIL after the fix.

**R56 — silent coverage** (BLOCKS_FREEZE). "`Count.floor`/`Build.completion` silently absent (no
verdict emitted) on assets whose `count_sql` is parameterized or multi-table — 57 assets on
L1/L2/L4/L5. The differential reimplementation finds real breaches the inspector never reports
(ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510)." Replacement: every
check emits a verdict row for every asset — an explicit `N/A` with its reason where the check
cannot run, never silence; parameterized `count_sql` gets a declared-universe fallback
(`count(*)` of `target_table`, as `harness/differential.py` does).

**R40 / R41 — the L3 census cannot run on production** (R41 BLOCKS_FREEZE, R40 BLOCKS_LAYER).
R40: "`Vocab.identity`'s `count(DISTINCT (chart_id,event_class,segment_index))` does not scale to
the estate's largest table (kala_field, 10.3M rows) and exceeds the hardcoded 180s psql timeout
(line 95), making the L3 and `--layer all` census unrunnable on production. Ground truth measured
by hand: duplicates = 0 in 47s." R41: "No per-check fault isolation: one check raising (timeout,
missing relation) aborts the ENTIRE layer census instead of degrading that check's verdict to
UNKNOWN for that asset." Replacement: sample-aware/indexed duplicate count plus a configurable
timeout; per-check exception capture recorded as measured-but-errored.

**R71 — the [TRANSFERS] contradiction** (BLOCKS_FREEZE). Tier 2 §1 (`:83-85`): "a layer plan does
not inherit it as its own work"; tier 2 §12.2 (`:614`) marks Presentation parity [TRANSFERS];
tier 3 §5.4 test 4 (`:628`) requires of the layer instance: "Presentation parity holds for the
layer's served surface." P4 confirmed three layers hit this (R94, R119, R140, R185). Replacement
(P4's proposal, recommended in DECISIONS_FOR_THE_NATIVE D3): reword tier-3 §5.4 test 4 — "run
where the surface exists; where the owning plane is not built, record [TRANSFERS]-pending — never
a pass, never a block."

**R82 — live fingerprint drift on tier 4** (DEGRADES, caught by `drift_detector.py` at HIGH).
"CANONICAL_ARTIFACTS row for ASSET_ELEVATION_TEMPLATE: rotate fingerprint_sha256 to
244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f and update last_verified_*" —
declared `bb341cc1a696…` vs on-disk `244e87dff30a…`; the v1.1→v2.0 edit was never restamped in the
session that made it. Note the detector worked; the content defect it guards is what remains.

## 8 · Per-layer results

| measure | L0 | L1 | L2 | L3 | L4 | L5 | reproduction |
|---|---|---|---|---|---|---|---|
| Assets in registry | 40 | 19 | 23 | 23 | 9 | 15 | `SELECT layer, count(*) FROM asset_registry GROUP BY layer` (P6) |
| Census executed on production | yes (65.1 s) | yes (80 s) | yes (81 s) | **no — R40/R41** | yes (44 s) | yes (27 s) | `census/*_prod_20260926.json`, `census/runtime_sweep_20260926.tsv` |
| Census on sandbox | yes | yes | yes | yes (2.5 s) | yes | yes | `census/*_sandbox_20260926.json` |
| Hand-verify sample size | 8 | 12 | 8 | 11 | 9 | 12 | `handverify/T2_SUMMARY.md` |
| Hand-verify verdict disagreements | 0 | 12+ | 8 | 8 | 9 | 4 (60 total, all R42/R43/R46) | `handverify/L{0..5}_T2.md` |
| Planted-defect detection | 17 plants over 6 layers, 17/17 detected, 0 collateral | — (suite spans layers) | — | — | — | — | `harness/T1_RESULTS.json`, `census/plants/*.json` |
| T1 differential disagreements (classed) | 10 (9×R46 + 1 methodology) | 18 (T1-F1) | 23 (T1-F1) | 32 (19×R48 + 13×R43) | 7 (T1-F1) | 9 (T1-F1 + R43) | `harness/T1_DIFFERENTIAL.md` per-layer tables |
| P4 derivation inventions | reference layer (skeleton pre-exists) | 15 | 30 | 49 | 18 | 18 (130 total) | `derivations/L{1..5}_INVENTIONS.md` |
| C-9 carriage check unassignable | (reference) | confirmed | confirmed | confirmed | confirmed | confirmed | skeletons; R92/R112/R144/R190/R204 |
| C-10 multi-producer shared tables | — | confirmed | confirmed | confirmed | **refuted** | confirmed | skeletons; R06 |

## 9 · How to re-run this campaign

The freeze decision should rest on a second pass, run after the implementation plan's packets land.
Everything below is scripted under `00_ARCHITECTURE/briefs/nirmana/nikasha_test/` and resumable
from `STATE.md` + `EVENTS.jsonl`.

**Fix first, or the second pass cannot run cleanly:**

1. **R40/R41** — the L3 production census and `--layer all` abort on the 180 s hardcoded timeout
   and the missing per-check fault isolation. Until then, L3 is measured on the sandbox only and T4
   stays PARTIAL.
2. **R47** — the census `--out` path overwrites a production artefact by default; a re-run pointed
   at production must write to a distinct path first.
3. **NIKASHA_CONTROL_DIR port (part of R57)** — the scratch closing tooling reads ledgers from an
   env-directed directory; the production tools hardcode `00_ARCHITECTURE/control/`. The port must
   land before T3 can be re-proven against production ledgers (read path).
4. Plus the six rulings in `DECISIONS_FOR_THE_NATIVE.md` (orchestrator edits authorization, sealed-
   tier reopens, [TRANSFERS] resolution, …) — the plan continues around each, but the re-run's T5
   and derivability legs assume the documentation-alignment packets have landed.

**Second-pass procedure (same five tests, same order):**

1. **Environment** — worktree on the campaign branch; interpreter
   `/opt/homebrew/opt/python@3.13/bin/python3.13`; production reads via
   `source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433` after verifying
   `SELECT current_setting('default_transaction_read_only')` = `on`.
2. **Baseline (P0)** — `manifest_fingerprint.py --check`; `drift_detector.py`; census + tracker on
   L0; ledger row counts. Compare against this report's §0 figures.
3. **Sandbox (P1)** — rebuild with `harness/build_sandbox.sh`, then `extend_sandbox_fix.sh`;
   regenerate `harness/SANDBOX_MANIFEST.json` via `make_manifest.py`; re-run the fidelity diff with
   `harness/census_diff.py` (expect: only sampling-induced diffs).
4. **T2 (P2)** — `harness/census_sweep_prod.sh` for all six layers (L3 must now run on
   production); hand-verify per `harness/T2_PROTOCOL.md`, stratified ≥8 assets per layer covering
   every asset kind; success = **0 verdict disagreements per layer** (this pass: 60, all
   R42/R43/R46 — those rows closed means zero).
5. **T1 (P2, sandbox)** — `harness/plant.py` (17 plants), then `harness/mutation_test.py` against
   `asset_census_mutant.py`, then `harness/differential.py`. Re-plant the TRUNCATE case (R52): it
   must now read FAIL. Success = 17/17 detected, 0 collateral, `suite_notices=true`, 0 unclassified
   differential disagreements — and R56-class silence gone (an explicit N/A row where a check
   cannot run).
6. **T3 (P3)** — with the R57/R58 port landed, re-run the closure loop **against the ported
   production tools** in the sandbox: fix the same three kinds of gap, observe CLOSED rows, cert
   records, tracker increment, then regress one fix and observe RE-OPENED and the count falling.
   The scratch copies under `harness/` (`asset_census_closing.py`, `tracker_sandbox.py`,
   `t3_seed_dosha_aliases.py`, `t3_run_writer.py`) remain as the reference behaviour. Then one
   supervised production closure run (the single write the first pass could not do).
7. **T4/derivability (P4)** — re-derive the five layer skeletons from the re-rendered tiers;
   success = tier-3 §0.1 fillable without invention and the P4 primary rows (R85 et al.) closed.
8. **T5 (P5)** — re-run the vocabulary cross-checks, the ledger overlap census (expect the 11
   duplicate pairs folded into one namespace), `drift_detector.py` (expect: no HIGH), and
   `manifest_fingerprint.py --check` (expect: MATCH).
9. **Freeze evaluation (P6)** — re-score the five tests per layer against the register's §1
   criterion; the freeze question reduces to C8 (the P-need/V-journey→layer mapping) plus R39 once
   packets 1–7 have landed.

---

## Application / handoff record

- **Register**: `NIKASHA_CHANGE_REGISTER_v2_0.md` — 214 rows, v1.0 retained and superseded; nothing
  deleted.
- **Plan**: `NIKASHA_IMPLEMENTATION_PLAN_v1_0.md` — 10 packets, ≈365 h, every OPEN row assigned.
- **Native decisions**: `nikasha_test/DECISIONS_FOR_THE_NATIVE.md` — six rulings, referenced not
  duplicated.
- **Campaign log**: `nikasha_test/STATE.md` (phase ledger, all phases closed) and
  `nikasha_test/EVENTS.jsonl` (append-only, 61 events). Phase commits: P0 c63ca0774 · P1 9495fb1a8 ·
  P2 b02c7b62d + 871b4d4eb · P3 55bd085e8 · P4 7c26bdea4 · P5 d9772f295 · P6 1c4e729b1.
- **Constraints honoured**: production read-only throughout (every mutation in `nikasha_sandbox`);
  tiers 1–3 never edited; orchestrator and `WriterBase` untouched; nothing placed at the repository
  root; no secret in any artefact. Tier 4 and the inspector were not edited either — every
  blocking defect was proven in scratch copies and registered instead (R57 marked fixed-during-
  campaign in scratch only).
- **Deliberately not done**: no re-measurement beyond the P6 `P6_MEASUREMENTS` event (all figures
  herein are reproduced from the phase artefacts and that event, not recomputed); the tier-1
  missing review file (R72) was not hunted beyond a `find` over the worktree — locating it is a
  native/plan task; `check_migration_ledger_vs_production.py` was never fault-injected
  (NOT_MEASURED).
