---
artifact: NIKASHA_TEST_PHASE6_ANALYSIS
canonical_id: NIKASHA_TEST_PHASE6_ANALYSIS
version: "1.0"
status: FINAL
campaign_id: nikasha-test
phase: 6 (analysis)
produced_on: 2026-09-26
model_routing: K3_256 at LOW effort for the entire campaign including this analysis (native instruction 2026-09-26; the §5 Phase-5-end "switch to max effort" marker is cancelled)
register: NIKASHA_CHANGE_REGISTER_v2_0.md (214 rows, R01–R214)
---

# Nikaṣa test campaign — Phase 6 analysis

Population and instruments: all figures below come from (a) the campaign's own phase artefacts
under `00_ARCHITECTURE/briefs/nirmana/nikasha_test/` (paths cited per figure), or (b) the
nikasha-test P6 production read-only queries of 2026-09-26 (`source /Users/Dev/madhav-l3/dbenv.sh;
export PGPORT=5433`; verified `default_transaction_read_only = on` at P0), recorded in
`nikasha_test/EVENTS.jsonl` phase 6, event `P6_MEASUREMENTS`. Nothing was re-measured for this
document beyond that event; no figure is reasoned toward. Where no measurement exists the entry
says NOT_MEASURED.

## 6.1 · Readiness verdict per component

Verdicts use the campaign set: `READY` / `READY_WITH_CHANGES` / `NOT_READY`. "Deciding rows" are
the register rows whose closure would change the verdict.

| component | verdict | evidence | deciding register rows |
|---|---|---|---|
| Tier 1 — `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md` | **READY_WITH_CHANGES** | T5 found one cosmetic row-order issue and one broken pointer (its `review_record` file does not exist anywhere; V10/R72). No derivability invention names a tier-1 clause as the failed provider. Evidence: `nikasha_test/consistency/T5_VOCABULARY.md` V1–V17; `nikasha_test/derivations/L1..L5_INVENTIONS.md` | R01 (COSMETIC), R72, R76 |
| Tier 2 — `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` | **READY_WITH_CHANGES** (one BLOCKS_FREEZE contradiction) | The [TRANSFERS] contradiction (T2 §1/§12.2 vs T3 §5.4 test 4) hit three layers in P4 (R94/R119/R140/R185); the multi-producer shared-table gap (R06) confirmed on L1/L2/L3/L5, refuted L4; most P4 primary rows (R85, R89, R90, R91, R109, …) land on tier-2 clauses. Evidence: T5_VOCABULARY.md V9; register §2.2, §2.8 | **R06, R71**, plus R73, R75, and the P4 primaries assigned to T2 |
| Tier 3 — `briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` | **NOT_READY** | §0.1 is unfillable on every layer (no P-need/V-journey→layer necessity mapping exists — the universal P4 blocker, 130 rows); C-9 (per-asset carriage check unassignable, R09) confirmed on all five non-reference layers (R92, R112, R144, R190, R204, and 6th in R159/R174); the §5.2/§5.4 gate-count and verdict-spelling drift (R65, R67, R68); §5.4 test 4 contradicts T2 (R71). Evidence: register §2.8 per-layer confirmations; `derivations/L*_INSTANCE_SKELETON.md` | **R08, R09, R71**, R65, R67, R68, R74, and the P/V-mapping row R85 |
| Tier 4 — `briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` | **READY_WITH_CHANGES** | R12/R13 landed during the campaign's predecessors; what remains is service/edge-kind shape (R14 and its P4 extensions R97/R125/R165–R177/R211/R212), the "eight gates"/"six checks" text drift (R63, R64), the stale `0/320`-class figures it cites (R69/R70-adjacent), and its manifest fingerprint (R82). Its own figures drifted against production (776 runs vs measured 762; 21 skip_no_delta vs measured 17 — R84). Evidence: T5_VOCABULARY.md V1/V2/V6; P6 queries (R84 row text) | R14, R63, R64, R68(T4), R82; R16 pending R09 |
| Inspector — `platform/scripts/governance/asset_census.py` | **NOT_READY** | T1: 17/17 planted defects detected with zero cross-asset collateral and a mutation test that notices an inverted detector (`harness/T1_RESULTS.md`) — the detection core is sound. But: one check inverts on data destruction (R52/T1-FN1), one FAIL branch is dead code (R53), 57 assets get no `Count.floor`/`Build.completion` verdict at all while the differential finds real breaches they hide (R56/T1-F1: ga_vargas 0 < 22 092; bo_laksana 7 409 < 60 000; ph_sankrama 630 < 2 510), no per-check fault isolation kills whole layers (R41 — L3 and `--layer all` abort), `Vocab.identity` cannot scale to kala_field (R40), and the closure path does not exist (R57). T2: 60 verdict disagreements over 60 hand-verified assets, all R42/R43/R46 instances (`handverify/T2_SUMMARY.md`). Three checks (Complete.width, Carr.detector, Reach.fields) are NOT_MEASURED by planting — constant verdicts, nothing to plant (T1_RESULTS.md §5) | **R40, R41, R42, R52, R56, R57** (BLOCKS_FREEZE/BLOCKS_LAYER), then R20, R22, R43–R46, R48–R51, R53–R55, R60 |
| Delta ledger — `00_ARCHITECTURE/control/asset_gaps.jsonl` | **READY_WITH_CHANGES** | Schema and vocabulary agree with T4/tracker (T5 agreements A3/A4). Defects: hand-written rows carry no deterministic id or detector binding and can never close by measurement (R58); 11 hand↔census duplicate-in-substance pairs measured (`consistency/T5_LEDGER_DRIFT.md` §A; R78–R81 scope); sandbox runs pollute it with prod-scale floor rows (R62). Baseline: 262 data rows (243 gap / 19 opportunity; 261 OPEN, 1 IN_PROGRESS) — STATE.md P0.5 | R58, R62, R78–R81, R15, R29 |
| Certification ledger — `00_ARCHITECTURE/control/asset_certs.jsonl` | **READY_WITH_CHANGES** | Record shape agrees across T3 §5.3, T4 §7 and the `_schema` line (T5 A7). It holds one data row and has never been written by a production run; the only full write cycle exists in the sandbox (9 certs, `harness/T3_CLOSURE_LOOP.md` §4). Its correctness therefore rides on the R57 port, not on any defect of its own. NOT_MEASURED: nothing — the ledger is simply unexercised in production | R57 (indirect), R32 DONE |
| Tracker — `00_ARCHITECTURE/control/asset_elevation_tracker.py` | **READY_WITH_CHANGES** | Correctly reported 0/40 ELEVATED, 0/360 gates at baseline (STATE.md P0.5) and moved 0→1/40, 0/360→9/360 in the sandbox once last-wins-per-gap_id existed (T3_CLOSURE_LOOP.md §4–5). Stock version cannot see closure (per-row state, R57b), reads ledgers but not the census JSON (R30), duplicates the SHAPE list with T4 §2 (R31 — currently in agreement, A1), carries a stale "Eight, not thirty-three" comment (R66) | R57(b), R30, R31, R66 |
| `drift_detector.py` | **READY_WITH_CHANGES** | Caught the one real drift present (ASSET_ELEVATION_TEMPLATE fingerprint HIGH, R82) and nothing false at HIGH+; the two LOW `schema_db_unreachable` findings are an unreachable instrument reporting noise (R83). Evidence: `consistency/T5_LEDGER_DRIFT.md` §B1 verbatim run, exit 2 | R82 (content), R83 (instrument hygiene) |
| `manifest_fingerprint.py` | **READY** | `--check` MATCH at P0 baseline and at P5 re-run: 136 entries, declared == observed `7794567b405a9207` (STATE.md P0.5; T5_LEDGER_DRIFT.md §B2). No campaign finding names it | — |
| `check_migration_ledger_vs_production.py` | **READY (unexercised)** | Inventoried at P0 (STATE.md component table); no campaign phase injected a fault against it, so its failure modes are NOT_MEASURED. No findings surfaced against it in any phase | — |

## 6.2 · The register at v2.0

`NIKASHA_CHANGE_REGISTER_v2_0.md` exists (this branch, superseding v1.0, nothing deleted). Index
counts (register §0.1–§0.3):

- **Total 214 rows** — R01–R84 carried from v1.0; R85–R214 added from the P4 derivability pass.
- By state: OPEN 197 · DONE 15 · CLOSED 1 (R33, closed by the T3 sandbox proof) · MEASURED in P6 1 (R84).
- By severity: BLOCKS_FREEZE 12 · BLOCKS_LAYER 107 · DEGRADES 83 · COSMETIC 12.
- Distribution: tiers R01–R16; inspector R17–R26 + R40–R62; T5 consistency R63–R84; ledgers/tracker R27–R33; build system R34–R39; P4 inventions R85–R214 (L1 15 · L2 30 · L3 49 · L4 18 · L5 18 = 130 — the campaign brief's per-layer split 17/30/49/17/17 is wrong in the parts and right in the total; register §5 records the reconciliation).
- Source-count note: L1's own footer claims 17 inventions while listing 15 (INV-L1-09/-15 folded); no source line was dropped (register §5).

## 6.3 · Root-cause clustering

The L0 run's shape — three findings behind most rows — repeats. Eight clusters cover all 197 OPEN
rows:

| # | cluster (named cause) | rows | count |
|---|---|---|---|
| C1 | **Completion/counting logic (R42/R52-class)** — `Build.completion` is a rows_written↔live consistency test that inverts on data destruction and self-compares on multi-table assets; views and empty-by-design have no honest verdict | R42, R46, R52, R53, R99, R126 | 6 |
| C2 | **Grep/registration limits (R43-class)** — literal-grep/AST blind spots: `@register(CONSTANT)` indirection, package-directory writers, a citation-column list that misses the singular form | R43, R60 | 2 |
| C3 | **Latest-row selection (R44/R49-class)** — `asset_throughput` / `build_run_assets` reads quote non-latest rows; stale-only dependencies read "all lit" | R44, R45, R49 | 3 |
| C4 | **Silent coverage + no fault isolation (R56-class)** — checks absent without an N/A row on parameterized/multi-table count_sql and whole layers on one timeout; real floor breaches hidden | R40, R41, R48, R56, R128 | 5 |
| C5 | **Closure absence (R57/R58-class)** — the ledger is append-only-OPEN, the tracker reads per-row state, hand rows have no detector binding; nothing can ever close by measurement | R57, R58, R62, R30, R15, R29, R80 | 7 |
| C6 | **Ledger namespace split (R78-class)** — one defect, two row idioms; 11 measured duplicate pairs | R78, R79, R81 | 3 |
| C7 | **Documentation drift after ruling 17 (R63–R77-class)** — the ninth gate and the Dom→Carr rename landed in code and ledger vocabularies but not in the sealed prose; self-contradicting counts; a missing review file; the [TRANSFERS] contradiction | R63–R77, R82 (R83 is instrument hygiene, carried in C4's family) | 16 |
| C8 | **Derivability absence (P/V-mapping and its siblings)** — no tier maps P-needs/V-journeys, obligations, entity classes, presentation rows, contracts, switch behaviour, or carriage checks *to layers*; no ablation harness exists; shared tables have no multi-producer expression (R06/R10-class folds in here). The 130 P4 rows collapse onto ~20 primary rows (R85, R86, R87, R88, R89, R90, R91, R93, R06, R09, R22, R71, R101, R105, R106, R109, R117, R122, R124, R133, R142, R161, R194 + small singletons R97, R120, R121, R133, R163, R194, R213, R214); the rest are `depends_on` transcription rows | R06, R08–R10, R14, R16, R21–R23, R85–R214 minus rows counted in C1–C4 | ~150 |

Plus unclustered singletons: R01 (cosmetic order), R50 (off-by-one), R51 (Dens attribution), R54
(verdict saturation), R55 (Earn≡Cost single detector), R59 (Ashtanga Hridayam admission), R61
(cascade fact), and the build-system section R34–R39 (clustered by §2.7 itself, analysed in §6.7).

Reading: two inspector clusters (C1+C4) produce every one of the 60 T2 verdict disagreements and
all three known hidden floor breaches; one tooling cluster (C5) makes the entire closure loop
impossible; one documentation cluster (C7) is the price of reopening sealed documents by ruling
without a re-render pass; and the largest cluster (C8) is a single architectural omission — the
tiers define products and layers but never the *mapping between them*.

## 6.5 · The freeze criterion, evaluated

Freeze criterion (register §1): all five tests pass **in production tooling**, and every register
row closed or explicitly deferred. Status per test, per layer:

| test | L0 | L1 | L2 | L3 | L4 | L5 | verdict |
|---|---|---|---|---|---|---|---|
| T1 finds what is there | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | PASS (sandbox) | **PARTIAL** — proven only in the sandbox and only against the stock inspector's plantable checks; 3 checks unplantable (NOT_MEASURED); must re-run against the ported inspector |
| T2 does not invent what isn't | PASS (0 disagreements / ~120 cells) | FAIL (12+R44-class) | FAIL (8) | NOT_RUNNABLE on production — sandbox-measured (R40/R41) | FAIL (9) | FAIL (4) | **FAIL** — 60 disagreements, all R42/R43/R46; fix and re-run |
| T3 a fix closes a row | FAIL stock / PASS with scratch port (sandbox) | untested | untested | untested | untested | untested | **FAIL in production tooling** (R57/R58); the fix exists and is proven (`harness/asset_census_closing.py`, `tracker_sandbox.py`; 25+11 closures, regression both ways) |
| T4 works on a layer it wasn't built against | reference layer | RUN | RUN | NOT_RUNNABLE on production (R40/R41; 180s timeout on kala_field, 10.3M rows; ground truth dups=0 in 47s by hand) | RUN | RUN | **PARTIAL** — census executed L1/L2/L4/L5 production (80s/81s/44s/27s) and L3 sandbox (2.5s); C-10 refuted on L4, confirmed elsewhere |
| T5 the pieces agree | — (cross-cutting) | — | — | — | — | — | **FAIL** — 22 open findings R63–R84 including one BLOCKS_FREEZE contradiction (R71) and one live fingerprint drift (R82) |

**What remains before Nikaṣa can be sealed and the real run started at L0**, in order:

1. Port the closure loop (R57/R58 + R47/R62/R30) into the production tools and re-prove T3 against
   production ledgers (read path) — packet P3 of the implementation plan.
2. Fix the C1/C4 inspector defects (R40–R56 family) and re-run T2 on all six layers to zero
   disagreements; re-run the T1 suite against the ported inspector, including a re-plant of the
   TRUNCATE case which must then FAIL.
3. Run the L3 census on production (unblocked by R40/R41).
4. Land the C7 documentation alignment and the sealed-tier reopens (R08/R09/R71 at minimum) by
   native ruling; rotate the T4 fingerprint (R82).
5. Resolve the ledger namespace (C6) so hand and census rows share one id space before new rows
   accumulate.
6. Instrument the builder (R34/R35) and remove the run-killer (R36) — before any from-scratch run.
7. Then the freeze question reduces to the C8 mapping work (R85 et al.) plus R39 — the system can
   be *sealed* only when a fresh reader can derive L1–L5 without inventing content.

## 6.6 · What the campaign could not test, and why

| # | not tested | why | what would be needed |
|---|---|---|---|
| 1 | `Complete.width`, `Carr.detector`, `Reach.fields` sensitivity (T1 planting) | Constant verdicts with no per-asset input to mutate — nothing to plant (T1_RESULTS.md §5) | Real per-asset inputs: declared universes in the registry (R22), per-asset Carr assignments (R09), the R23 field-level census — then plants become expressible |
| 2 | `Earn.build_record` / `Cost.baseline` in the defect direction | Constant-FAIL at baseline because `rows_per_second` is NULL in 268/268 `asset_throughput` rows (P6 query); only the sensitivity direction was plantable (T1-FN4/R55) | R34 instrumentation landing, then a real build with a recorded rate |
| 3 | L3 census on production | `Vocab.identity`'s `count(DISTINCT (chart_id,event_class,segment_index))` over kala_field (10.3M rows) exceeds the hardcoded 180s psql timeout (`asset_census.py:95`) and one check's failure aborts the layer (R40/R41). Ground truth measured by hand: duplicates = 0 in 47s (`/tmp/kala_field_dupcount.txt`, recorded in STATE.md P2) | R40 (sample-aware/indexed duplicate count + configurable timeout) and R41 (per-check fault isolation), then re-run |
| 4 | Closure against production ledgers | Production is read-only (campaign constraint §2.1); writing CLOSED rows to `00_ARCHITECTURE/control/` production ledgers is a write the campaign may not do | The R57 port landed + one supervised production closure run |
| 5 | Hand-written gap rows closing by measurement | They carry no deterministic id and no detector binding (R58) — unclosable by construction, not by tooling | R58 (deterministic ids + detector bindings for hand rows) |
| 6 | The `[TRANSFERS]` obligations' real home | The retrieval and conversation planes are not built (T2 §1); presentation parity cannot be exercised at all | Those planes' artefacts existing; until then R71's rewording makes the debt explicit |
| 7 | Tier 1's review fold ("11 MAJOR + 14 MINOR, all folded") | The referenced file `briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md` does not exist anywhere in the repository (T5 V10/R72; `find` over the worktree) | Locate/restore the file or correct the pointer |
| 8 | Synergy terms (T3-template §1.5) | No ablation harness exists for any layer (R105/R206); the tier itself forbids inventing the fraction | A seam-by-seam ablation harness per chart-product layer (R105, 16h) |
| 9 | Deployed-vs-current-code baseline | The census reads registry + run history only; no code-head comparison exists (R87) | A git-head/schema-fingerprint read added to the census (R87, 6h) |
| 10 | `check_migration_ledger_vs_production.py` under fault | Inventoried but never fault-injected (no phase required it) | A planted migration-ledger mismatch in the sandbox |

## 6.7 · The build system, re-verified at analysis time

All figures: nikasha-test P6 production read-only queries, 2026-09-26 (EVENTS.jsonl `P6_MEASUREMENTS`;
proxy on PGPORT=5433). Queries named per figure.

| figure | value | reproduction |
|---|---|---|
| Assets in registry | **129** (brahmagyan 40 · bodha 23 · ganita 19 · kala 23 · mimamsa 15 · phala 9) — confirms T3's "9 × 129" scope | `SELECT layer, count(*) FROM asset_registry GROUP BY layer` |
| Build runs | **762** total — T4 §4.2 says 776 (**drifted**); states: completed 328 · failed 419 · stopped 15 | `SELECT state, count(*) FROM build_runs GROUP BY state` |
| Build run ↔ asset rows | **6 823** rows over **124** distinct assets | `SELECT count(*), count(DISTINCT asset_id) FROM build_run_assets` |
| L0 never run | **5/40** (confirms T4) | `build_run_assets ⋈ asset_registry` anti-join on layer L0 |
| L0 errored-or-aborted | **13/40** (confirms T4) | same join, state ∈ (error, aborted) |
| skip_no_delta | **17 assets / 61 rows** — T4 says 21 (**drifted**) | `build_run_assets` disposition = 'skip_no_delta' |
| Rate baseline | `asset_throughput.rows_per_second` NULL in **268/268** rows — **no rate baseline exists anywhere** (R34 re-verified) | `SELECT count(*) FROM asset_throughput WHERE rows_per_second IS NULL` |
| Silent failures | **288/419** failed runs carry no error text (R35 re-verified) | `build_runs` state='failed' AND error text null/empty |
| Failure-class noise | orphan-watchdog 49 rows; guardian restarts present; frozen-manifest validation 6 (R36/R37 re-verified) | `build_run_assets`/event text classed by source |
| Run-killer | Registry change mid-run aborts every asset in the run — the R36 evidence stands: 18 assets across 8 runs, including a 10-asset L0 run aborted in full on 2026-09-04 (BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md; consistent with the 419-failure population above) | triage document + `build_runs` failure join |
| Sole DRAFT asset | `bg_vidhi_floors` is the only `catalog_status=DRAFT` L0 asset (confirmed) | `SELECT asset_id FROM asset_registry WHERE catalog_status='DRAFT'` |

**Reading for the plan (register §2.7 sequencing rule, confirmed by these numbers):** instrument
the builder first (R34 — without a rate there is no cost baseline to judge any elevation against;
R35 — 69% of failed runs are undiagnosable), remove the run-killer (R36 — it would abort the
elevation campaign's own runs), fix stability and cascade reporting alongside layer elevation
(R37/R38 — every `Build.history` verdict is read against orphan/guardian noise until it falls),
and freeze the builder's own elevation plan last (R39 — "seamless" is defined by the asset
contract, which must stop moving first). The orchestrator's `WriterBase` contract stays frozen
throughout; all of R34–R38 are engine behaviour, not contract shape.

## 6.4 · The implementation plan

Produced as a separate artefact per the campaign brief §7:
`00_ARCHITECTURE/briefs/nirmana/NIKASHA_IMPLEMENTATION_PLAN_v1_0.md`, with native-only decisions in
`00_ARCHITECTURE/briefs/nirmana/nikasha_test/DECISIONS_FOR_THE_NATIVE.md`. Packet order: instrument
(R34/R35) → run-killer (R36) → closure port (R57/R58) → inspector detectors (R40–R56 family) →
documentation alignment (R63–R77) → ledger namespace (R78–R81) → fingerprint rotation (R82) →
layer-instance blockers (P/V mapping, C8) → builder's own plan (R39) last.
