---
artifact: NIKASHA_TEST_CAMPAIGN_STATE
version: "0.1"
status: IN_PROGRESS
campaign_id: nikasha-test
you_are_here: Phase 1 — sandbox built (110+49 tables); fidelity diff in progress; Phase 2 T2 prod sweep + hand-verify L0/L1/L2/L4/L5 done
updated: 2026-09-26T19:05:00+05:30
---

# NIKAṢA TEST CAMPAIGN — STATE

## You are here
- Branch: `campaign/nikasha-test` (worktree `/Users/Dev/madhav-nikasha`, from `origin/l3/kala-layer-briefs`)
- Phase: **0 — CLOSED** (fingerprint baseline, inventory, L0 baselines, dispositions all recorded).
  Next: Phase 1 sandbox.
- Interpreter for governance scripts: `/opt/homebrew/opt/python@3.13/bin/python3.13` (system python3 lacks PyYAML).
- DB: production read-only via `source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433` (verified `on`).
  Sandbox: not yet built (Phase 1).

## Phase ledger
| phase | state | commit | headline figure |
|---|---|---|---|
| 0 | CLOSED | (this commit) | census L0: 119 FAIL/90 PARTIAL; tracker 0/40, 0/360 gates |
| 1 | NOT_STARTED | — | — |
| 2 | NOT_STARTED | — | — |
| 3 | NOT_STARTED | — | — |
| 4 | NOT_STARTED | — | — |
| 5 | NOT_STARTED | — | — |
| 6 | NOT_STARTED | — | (model switch: K3 max effort at 5→6 boundary) |
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
  "Per-entry check" = drift_detector's per-artifact fingerprint findings (manifest_fingerprint has no
  per-entry mode; recorded as interpretation decision).
- drift_detector: **3 findings, exit=2** — 1 HIGH: ASSET_ELEVATION_TEMPLATE fingerprint drift
  (CANONICAL_ARTIFACTS declares bb341cc1…, file is 244e87dff3…; v1.1→v2.0 edit never rotated);
  2 LOW environmental (drift detector psql lacks password when env not sourced). Report:
  00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T112959Z.{json,md}.
- Census L0 (production, read-only, runtime 65.1s): 40 assets · 36 registered ids vs 34 has_writer=true;
  67 global runs, 0 touched L0; never-exercised-with-writer: bg_sign_medical.
  FAIL 119 · PARTIAL/NO_DETECTOR 90 · measured 40. Per-check FAIL counts: Build.completion 10,
  Build.exercised 1, Build.registered 2, Cost.baseline 40, Count.floor 1 (bg_parihara_rules),
  Dens.served 24, Earn.build_record 40, Vocab.alias 1 (bg_ontology).
  Artifact: nikasha_test/census/L0_prod_baseline_20260926.json.
- Tracker L0 (production): 40 assets, GAPS_REGISTERED=40, ELEVATED 0/40, open gaps 239,
  open opportunities 18, gates certified 0/360.
- Ledgers: asset_gaps.jsonl 262 data rows (243 gap / 19 opportunity; 261 OPEN, 1 IN_PROGRESS);
  asset_certs.jsonl 1 data row.
- Note: tracker open-gap count (239, L0) vs ledger total (243 all layers) — scope difference, reconciled Phase 5.


## Register dispositions (Phase 0.6)
25 OPEN rows dispositioned (one EVENTS row each): test=R06 R08 R09 R10 R14 R15 R16 R22 R24 R28 R30 R31 R33;
fix=R20 (inspector, if blocking); fix-as-harness=R25 (harness/plant.py, inspector untouched);
verify-in-6.7=R34 R35 R36 R37; carry-to-plan=R01 R21 R23 R29 R38 R39.
Binding rulings absorbed: #9 signature authority, #10 medical exclusions stay removed, #11 ten obligations
(Dom→Carr), #13 tiers 1-3 sealed, #16 composite identity key, #17 Build ninth gate 9×129 + boundary rule.
Inspector read in full (662 lines): noted for later phases — emit_gaps emits NO_DETECTOR rows as gaps
(Carr.detector × N assets), dead `missing` var in Build.dag, int(rw) crash surface on non-numeric
rows_written, Complete.width/Carr.detector/Reach.fields constant NOT_GENERIC/NO_DET.

## Blockers
None.
