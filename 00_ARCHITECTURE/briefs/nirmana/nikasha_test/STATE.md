---
artifact: NIKASHA_TEST_CAMPAIGN_STATE
version: "0.2"
status: IN_PROGRESS
campaign_id: nikasha-test
you_are_here: Phase 1 — sandbox built (110+73 tables); fidelity re-diff pending after extension pass 2. Phase 2 — T2 prod sweep done for L0/L1/L2/L4/L5; L3 blocked by inspector timeout, will census on sandbox; hand-verify done except L3.
updated: 2026-09-26T20:40:00+05:30
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
| 1 | IN_PROGRESS (sandbox built; fidelity re-diff pending) | 45087f280 | 110 core tables, 0 COPY_FAIL, manifest written; ext pass 1: +73 ok / 92 junk-name failures (extraction defect, fix script ready) |
| 2 | IN_PROGRESS (T2 sweep + hand-verify 5/6 layers; L3 pending; T1 not started) | 45087f280 | runtimes L1 80s, L2 81s, L4 44s, L5 27s; L3/all FAILED on 180s inspector timeout; kala_field dup ground truth = 0 (47s manual) |
| 3 | NOT_STARTED | — | closure loop — campaign's most important untested path |
| 4 | NOT_STARTED | — | tier1/tier2 structured summary ready at derivations/_tier1_tier2_summary.md |
| 5 | NOT_STARTED | — | — |
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

## Open threads (carried forward)
1. Run extend_sandbox_fix.sh → merge copy_report_ext*.tsv → re-run make_manifest.py → re-run L0 sandbox
   census → fidelity diff vs prod (write census/fidelity_L0.md) → close Phase 1.
2. L3 census on the SANDBOX (kala_field sampled ~515k, query completes) + T2 hand-verify L3 → close Phase 2 T2.
3. T1 planted defects (harness/plant.py) — NOT STARTED, sandbox only.
4. Phase 3 closure loop — NOT STARTED, campaign's most important untested path.
5. Register rows: write now for the 5 systemic inspector defects + 2 timeout defects (then P6 batch).

## Blockers
None. (L3 production census blocked by inspector timeout → routed to sandbox; §2.3 fix proposed, not yet applied.)
