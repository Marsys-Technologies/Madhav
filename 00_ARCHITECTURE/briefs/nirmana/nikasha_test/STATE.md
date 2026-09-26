---
artifact: NIKASHA_TEST_CAMPAIGN_STATE
version: "0.4"
status: IN_PROGRESS
campaign_id: nikasha-test
you_are_here: Phase 5 CLOSED (T5 consistency: R63–R84). Next: Phase 6 analysis + register v2.0 (K3_256 LOW).
updated: 2026-09-26T22:22:00+05:30
---

# NIKAṢA TEST CAMPAIGN — STATE

## You are here
- Branch: `campaign/nikasha-test` (worktree `/Users/Dev/madhav-nikasha`, from `origin/l3/kala-layer-briefs`)
- HEAD: `45087f280` (P1 sandbox + P2 T2 progress committed and pushed).
- **Model routing: K3_256 at LOW effort for the ENTIRE campaign, phases 0–7. The 5→6 switch to
  K3 max effort is CANCELLED (native instruction 2026-09-26; brief §3 + frontmatter supersede the
  stale marker at §5 Phase 5 end).**
- Interpreter for governance scripts: `/opt/homebrew/opt/python@3.13/bin/python3.13` (system python3 lacks PyYAML).
- DB: production read-only via `source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433` (verified `on` at P0).
  Sandbox: **BUILT** — db `nikasha_sandbox`, socket dir `nikasha_test/.sandbox`, port 54329, user `sandbox`;
  `session_replication_role=replica` persisted; connect with `PGOPTIONS=` cleared (PGOPTIONS read-only leak
  was root-caused and is wrapped by `spsql` in the harness scripts).

## Phase ledger
| phase | state | commit | headline figure |
|---|---|---|---|
| 0 | CLOSED | c63ca0774 | census L0: 119 FAIL/90 PARTIAL; tracker 0/40, 0/360 gates |
| 1 | CLOSED | (this commit) | 183 tables, 0 COPY_FAIL, manifest written; fidelity diff L0: 3 diffs all sampling-induced, 0 UNEXPECTED → FIDELITY PASS (census/fidelity_L0.md); R47 registered (census output path overwrites prod artifact) |
| 2 | CLOSED (T2 hand-verified all 6 layers; T1 planted-defect suite done) | (this commit) | T2: 60 assets, 60 verdict-level disagreements, all instances of R42/R43/R46; L3 census on sandbox (2.5s) — R40/R41 the only prod blockers; handverify/T2_SUMMARY.md. T1: 17/17 plants detected, 0 cross-asset collateral, all restored; mutation test notices an inverted detector; differential 265 agree / 99 classed / 0 unclassified; new register rows R52–R56; harness/T1_RESULTS.md |
| 3 | CLOSED (T3 closure loop proven in sandbox) | (this commit) | Three gaps of three kinds fixed and closed BY MEASUREMENT: bg_ontology-Vocab.alias (79/79 dosha synonyms seeded), bg_nakshatra_medical-Build.registered (has_writer=true → cascaded a true new Build.exercised gap, closed by actually running the writer, run c0db4bc1), bg_doshas-Idem.pattern (seeder-following idem_scan). Headline: stock tooling CANNOT close rows (emit_gaps append-only-OPEN + tracker per-row state) — R57; scratch copies (harness/asset_census_closing.py, harness/tracker_sandbox.py) with last-row-per-gap_id + close/re-open emit make it work: 25+11 closures, tracker ELEVATED 0/40→1/40, gates 0/360→9/360. Regression proven (RE-OPENED → 1→0 → re-fix → 1). R33 CLOSED; new rows R57–R62; sandbox restored to baseline; harness/T3_CLOSURE_LOOP.md |
| 4 | CLOSED | (this commit) | 5 layer-instance skeletons + 10 asset briefs + 130 invention rows in derivations/ (L1 17, L2 30, L3 49, L4 17, L5 17). C-9/R09 confirmed all 5 layers; C-10 confirmed L1/L2/L3/L5, refuted L4. Universal top blocker: no P-need/V-journey→layer necessity mapping (tier-3 §0.1 unfillable). [TRANSFERS] contradiction tier-2 §1 vs tier-3 §5.4 test 4. |
| 5 | CLOSED | (this commit) | T5: 22 register rows R63–R84. 17 vocabulary disagreements (gate-count drift "eight"→nine ×5 surfaces; verdict spelling; L0 0/320 self-contradiction; [TRANSFERS] contradiction confirmed T2§1/§12.2 vs T3§5.4 t4; missing T1 review file; T2 miscounted review; "ten obligations" ×2; review-record naming ×4; pilots carry 8 gates; dual criterion strings) + 7 agreements + 11 ledger overlap pairs reconciled (namespace proposal, R28 scope) + drift HIGH confirmed (T4 fingerprint) / manifest MATCH 136 entries. consistency/T5_VOCABULARY.md, T5_LEDGER_DRIFT.md |
| 6 | NOT_STARTED | — | K3_256 low effort (switch cancelled) |
| 7 | NOT_STARTED | — | — |

## Component inventory (Phase 0.4)
| component | version | status | sha256(12) | last commit |
|---|---|---|---|---|
| MADHAV_PRODUCT_DEFINITION_FINAL.md (tier 1) | FINAL | SEALED | b9c098cd390d | 62b9c34ce 2026-09-25 |
| MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md (tier 2) | FINAL | SEALED | a7eaf821bf65 | 090bd9aaa 2026-09-26 |
| LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (tier 3) | FINAL | SEALED | 137ba6b9a415 | 090bd9aaa 2026-09-26 |
| ASSET_ELEVATION_TEMPLATE_v2_0.md (tier 4) | 2.0 | DRAFT_PENDING_REVIEW | 244e87dff30a | b598c3b63 2026-09-26 |
| MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md (L0 instance) | 3.0 | DRAFT_PENDING_ACCEPTANCE | 2233d00ad48d | 090bd9aaa 2026-09-26 |
| l0_assets/BG_EPHEMERIS_ELEVATION_BRIEF_v1_0.md | 1.0 | PILOT_DRAFT | c5aa73091609 | 73b280c62 2026-09-26 |
| l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md | 1.0 | PILOT_DRAFT | f40d42a80f67 | e88b56c5a 2026-09-26 |
| l0_assets/BG_PANCHANGA_ELEVATION_BRIEF_v1_0.md | 1.0 | PILOT_DRAFT | f6064958c012 | 73b280c62 2026-09-26 |
| l0_assets/BG_RULES_ELEVATION_BRIEF_v1_0.md | 1.0 | PILOT_DRAFT | fb411d880223 | 73b280c62 2026-09-26 |
| l0_assets/BG_SARVATOBHADRA_GRID_ELEVATION_BRIEF_v1_0.md | 1.0 | PILOT_DRAFT | 09422060bae3 | 73b280c62 2026-09-26 |
| platform/scripts/governance/asset_census.py (inspector) | — | — | 1158bc8543ec | b598c3b63 2026-09-26 |
| 00_ARCHITECTURE/control/asset_elevation_tracker.py | — | — | 607b1fcbd790 | 090bd9aaa 2026-09-26 |
| 00_ARCHITECTURE/control/asset_gaps.jsonl | — | 262 data rows | 0bc05eacd6c0 | abe4bc1d8 2026-09-26 |
| 00_ARCHITECTURE/control/asset_certs.jsonl | — | 1 data row | 4d45d8a3a513 | 5973d0132 2026-09-26 |
| platform/scripts/governance/drift_detector.py | — | — | 0f37efd64dfc | ffe2e12d0 2026-09-25 |
| platform/scripts/governance/manifest_fingerprint.py | — | — | 4e33035b7a84 | 6ef745576 2026-09-25 |
| platform/scripts/governance/check_migration_ledger_vs_production.py | — | — | 87b8c0f866a6 | 6ef745576 2026-09-25 |
| NIKASHA_CHANGE_REGISTER_v1_0.md | 1.0 | LIVING | 112d29d3680f | a184d2288 2026-09-26 |
| NATIVE_DECISIONS_2026-09-25_v1_0.md | 1.8 | RULED | 9cd273cb478b | 090bd9aaa 2026-09-26 |
| BUILD_FAILURE_TRIAGE_2026-09-26_v1_0.md | 1.0 | MEASURED | f7d6d28d63d9 | abe4bc1d8 2026-09-26 |
| REVIEW_DATA_PLANE_FINAL_v1_0.md | — | — | d06271564327 | 6ef745576 2026-09-25 |
| REVIEW_L0_STRATEGY_v2_0.md | — | — | d6e471178e4c | 629b88693 2026-09-25 |


## Baseline figures (Phase 0.5)
- manifest_fingerprint --check: **MATCH** (136 entries, declared==observed 7794567b405a9207).
- drift_detector: **3 findings, exit=2** — 1 HIGH: ASSET_ELEVATION_TEMPLATE fingerprint drift
  (bb341cc1… declared vs 244e87dff3… on disk; v1.1→v2.0 edit never rotated);
  2 LOW environmental. Report: 00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T112959Z.{json,md}.
- Census L0 (production, read-only, runtime 65.1s): 40 assets · 36 registered ids vs 34 has_writer=true;
  67 global runs, 0 touched L0; never-exercised-with-writer: bg_sign_medical.
  FAIL 119 · PARTIAL/NO_DETECTOR 90 · measured 40. Artifact: nikasha_test/census/L0_prod_baseline_20260926.json.
- Tracker L0 (production): 40 assets, GAPS_REGISTERED=40, ELEVATED 0/40, open gaps 239,
  open opportunities 18, gates certified 0/360.
- Ledgers: asset_gaps.jsonl 262 data rows (243 gap / 19 opportunity; 261 OPEN, 1 IN_PROGRESS);
  asset_certs.jsonl 1 data row.
- Note: tracker open-gap count (239, L0) vs ledger total (243 all layers) — scope difference, reconciled Phase 5.

## Register dispositions (Phase 0.6)
25 OPEN rows dispositioned: test=R06 R08 R09 R10 R14 R15 R16 R22 R24 R28 R30 R31 R33;
fix=R20; fix-as-harness=R25; verify-in-6.7=R34 R35 R36 R37; carry-to-plan=R01 R21 R23 R29 R38 R39.
Binding rulings absorbed: #9, #10, #11, #13, #16, #17 (details in pre-rewrite STATE / EVENTS phase 0).

## Phase 1 findings so far (harness root causes — all recorded in EVENTS)
- macOS bash 3.2 lacks mapfile → while-read loop in build_sandbox.sh.
- dbenv.sh PGOPTIONS read-only leaks into sandbox connections → spsql wrapper clears PGOPTIONS.
- pgvector 0.8.6 compiled+installed for postgresql@15 (brew build covered pg17/18 only); uuid-ossp created.
- FK copy-ordering failures → session_replication_role=replica on sandbox (constraints defined, not enforced).
- Generated columns (bg_sky_calendar, ephemeris_daily) need explicit non-generated COPY column lists.
- extend_sandbox.sh pass 1: regex extraction of referenced tables picked up CTE/alias names
  (b, c, baseline, computed…) → 73 real tables copied ok, 92 junk-name failures.
  extend_sandbox_fix.sh written: validates candidate names against production pg_class before copying.

## Phase 2 findings so far (T2)
- Census sweep (production): L1 80s, L2 81s, L4 44s, L5 27s JSONs in census/*_prod_20260926.json.
- **L3 and `--layer all` FAILED**: asset_census.py hardcodes 180s psql timeout (line 95);
  Vocab.identity's count(DISTINCT(chart_id,event_class,segment_index)) over kala_field (10.3M rows)
  exceeds it; the exception aborts the ENTIRE layer census (no per-check fault isolation).
  Ground truth: kala_field duplicates = 0, measured manually in 47s (/tmp/kala_field_dupcount.txt).
  Register rows to write: unscalable duplicate-count query; no per-check fault isolation.
- Hand-verification done L0/L1/L2/L4/L5 — handverify/{L0,L1,L2,L4,L5}_T2.md, protocol harness/T2_PROTOCOL.md.
  L0: 0 disagreements over ~120 cells (1 wrong rationale string, bg_text_index Idem.pattern).
  Systemic inspector defects (register rows to write NOW, per resume instruction):
  (a) Build.completion N/A "no count_sql" despite non-null count_sql layer-wide; self-comparison on
      multi-table assets (mi_kula count_sql 15 vs live 11 scored PASS);
  (b) Build.registered misses @register(ASSET_ID) constant indirection (mi_bhara, mi_sankalpa) and
      package-directory writers (ph_rectification); layer registered counts wrong (L4 8 vs 9; L5 12 vs 14);
  (c) Earn.build_record/Cost.baseline quote non-latest asset_throughput rows;
  (d) Build.dep_liveness "all lit" ignores stale-only dependencies (L2);
  (e) bo_samvada view asset scored against stub count_sql SELECT 0 (live_rows 0 vs real 15).

## Phase 2 findings so far (T1)
- T1 planted-defect suite (sandbox only): 17 plants across 15 of 18 inspector checks, all detected
  for the planted asset and no other (collateral=[] on all), all restored clean
  (harness/plant.py, harness/T1_RESULTS.json, census/plants/*.json).
- Mutation test: inverted Vocab.identity in harness/asset_census_mutant.py; control FAIL vs mutant
  PASS on the same planted duplicate → suite_notices=true (harness/T1_MUTATION.json).
- Differential test (harness/differential.py, harness/T1_DIFFERENTIAL.md): independent
  reimplementation of Vocab.identity / Build.registered / Count.floor over all 6 layers:
  265 agreements, 99 disagreements ALL classed (9×R46, 19×R48, 13×R43, 57×new R56, 1 methodology),
  0 unclassified.
- New register rows R52–R56 (NIKASHA_CHANGE_REGISTER): Build.completion inverted FAIL→PASS on
  data destruction (sharpens R42); Build.target FAIL branch dead under asset_kind CHECK;
  Vocab.alias severity verdict-invisible (FAIL saturation); Earn.build_record ≡ Cost.baseline
  single constant-FAIL detector; Count.floor/Build.completion silently absent on 57 assets with
  parameterized/multi-table count_sql (real floor breaches hidden: ga_vargas 0<22092,
  bo_laksana 7409<60000, ph_sankrama 630<2510).
- R25 CLOSED (plant mode built).
- NOT_MEASURED: Complete.width, Carr.detector, Reach.fields (constant verdicts, no per-asset
  input to plant).

## Open threads (carried forward)
1. ~~Phase 1~~ CLOSED (9495fb1a8).
2. ~~T2 including L3~~ CLOSED. Register rows R40–R51 written.
3. ~~T1 planted defects + mutation + differential~~ CLOSED (this commit). R52–R56 written; R25 closed.
4. ~~Phase 3 closure loop~~ CLOSED (this commit). R33 closed; R57–R62 written; sandbox restored to baseline.
5. Phases 4–7 as per brief. Next: Phase 4 derivability — L1–L5 layer-instance skeletons.

## Phase 3 findings (T3)
- Three gaps of three kinds (data / registry / detector) fixed in sandbox and observed closing by
  measurement; full narrative in harness/T3_CLOSURE_LOOP.md.
- **Headline finding R57**: stock inspector never closes a row (emit_gaps appends OPEN only, skips
  existing ids) and stock tracker reads state per row — closure is structurally impossible in the
  shipped tooling. Scratch copies with (a) last-row-per-gap_id state, (b) close/re-open emission,
  (c) NIKASHA_CONTROL_DIR ledger redirect prove the fix; ~70 lines to port to production.
- Regression leg works: flipping has_writer true→false produced exactly 1 RE-OPENED row and dropped
  ELEVATED 1→0 (CERTIFIED_GAPS_OPEN); re-fix re-closed and restored 1/40.
- Registry fixes cascade (R61): registering the writer surfaced a true new Build.exercised gap,
  closed by actually running BgMedicalMappingsWriter in the sandbox (60 rows, real throughput).
- Carr.D1 per-asset detector honestly failed first ('ashtanga hridayam' cited 27×, not in the text
  registry → R59); passed 27/27 after the text row was admitted.
- Ledger hygiene gaps found: hand-written rows never auto-close (R58); Ldgr list misses singular
  `classical_citation` (R60); sandbox sampling emits prod-scale Count.floor rows (R62).
- Sandbox verified restored to baseline post-run; platform/ and 00_ARCHITECTURE/control/ git-clean.

## Blockers
None. (L3 production census blocked by inspector timeout → routed to sandbox; §2.3 fix proposed, not yet applied.)
