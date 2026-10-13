```json
{"id":"J-4p","kind":"feature","wave":null,"build_tier":"opus","routing_reason":"kernel: P:569","needs_chart_data":true,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md","revision":"1.1","section_range":"444-465","sha256":"85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md","revision":"1.1","section_range":"449-459","sha256":"ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_VALUE_REVIEW_v1_1.md","revision":"1.1","section_range":"28-38","sha256":"57d528320b5ee1b514d442a129f699b3fae0a166bb4e4651cbb6325ccde483bc"},{"path":"00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md","revision":"1.0","section_range":"17-28","sha256":"dcb854cb796f7b3d736a72e9c77f33639dff586194dac836c6ef6ca23d1eb5be"},{"path":"00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md","revision":"1.0","section_range":"41-64","sha256":"f418ef9d9000a4c7e20dce78cefcd9210617f7b1fda91d107515290243ea7b24"},{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"509-580;720-726","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md","revision":"1.4","section_range":"487-513","sha256":"d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47"},{"path":"00_ARCHITECTURE/briefs/l3_families/contracts/DASHA_TABLE_CONTRACT_v1_0.md","revision":"1.1","section_range":"27-67","sha256":"93ddc1d9104421c4c989c4e73962631eaad56d3026259b108e3c77c1122d1a9a"},{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/FROZEN_PATHS.txt","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"1-9","sha256":"bed0ceb05255b28b3847b4f9f85fd9df1bc722104b96ce0412488e1261480ea7"}],"schema_receipt_id":null,"pw_mechanism_version":null,"release_pins":{"dash_build":null,"registry_revision":null},"packet_sha256":null,"original_failing_base":null,"test_commits":[],"expected_failing_assertion":null}
```
# J-4p DRAFT
A/E/V/R/X/P/S/D/F=spec_sources[0..8].path; sc/=platform/python-sidecar/; fl/=00_ARCHITECTURE/briefs/kalayantra/fleet/; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; SR=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json. k/r/c/t/u=sc/{services/gochara_kernel,services/gochara_rules,scripts/kala_gochara_cutover,tests/l3/gochara,tests/l3/gochara_rules} respectively. 1-based lines.

## 1 Pins
O=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md:44-46; T0=study:68-78.
Accepted install/pins/J-0m/K0-SV heads/verified squash mappings required. J-0c->J-0d->J-0->J-0m; J-4p after K0-SV/before consumers (P:720-726; A:444-465). Needs L1_SETTLED 2026-10-07T22:25Z, release ca17639b-f3cf-42c7-9866-0a61f3855802, live equality/no nonterminal chart build (M:5030-5036,5085; D:64,67); N8/9 need hashed rows/baseline in scratch DB (A:446).
(I) INTERPRETATION I1: O supersedes singleton; canonical pin/later REPIN (P:529). Unfilled pins await cockpit; missing inputs block.

## 2 Owns
Write ONLY:
k/dasha_read.py
k/inventory_verifier.py
r/permission.py
c/step06a_class_context.py
t/test_a53_dasha_read.py
t/test_a53_r16_amendments.py
t/test_a53_inventory.py
t/test_c48a_sealed_staleness.py
t/test_a25_v41_candidate_writer_pg.py (PG)
u/test_pp.py
u/test_am10_repin_75524b3e.py
platform/src/generated/nirmana-writer-digests.json
platform/src/generated/capability_estate_census.json
T0 Q1: verifier/cutover/tests; independent SQL; no new suite/CI edit (M:5083; P:530-534).
Read owns/callers, SR:2420-2442,3482-3493:
sc/services/gochara_grammar/dasha_data.py:97-263 (DD)
k/inventory_store.py:114-150 (IS)
k/record_store.py:1252-1267,1504-1511 (RS)
sc/pipeline/orchestrator/writers/ka_gochara_v5.py:918-946
c/step06b_windows_projection.py:555-601 (B)
platform/migrations/1206_gochara_search_inventory_completeness.sql:255-290 (SQL)
.github/workflows/ci.yml:475
t/test_a53_ci_db_list_guard.py:33-59 (CG)
F missing/unreadable/prohibited diff -> STOP/freeze path.

## 3 Excerpt
S:497-498:
```excerpt
  `[start_iso, end_iso)`; an instant `t = end_iso` belongs to the **next** row. Boundary
  instants are unambiguous by construction.
```
Reconciliation: `00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md` O/M:5085 replaces pin; retain S:496-507 and one-engine 5.0 snapshot/policy/independent verifier/2026-10-02 rulings (E:451-457).

## 4 Contract
Contract N1-N9; dasha_read.py:78-148 load_pinned_vimshottari(conn,chart_id)->(rows,contract); make_period_rows_for(conn,chart_id)->(callable,contract); assert_single_pinned_build(conn,chart_id)->list[str]. chart_dashas SR:2420-2442; TWO_PASS_VERIFIED/levels1-3; all-tier/level guard first (D:64-65).
(I) INTERPRETATION I2: add contract state/reason, rows=[]: absent=not_built; no two-pass=not_verified; two-pass only deeper=deeper_levels_only; mixed/NULL first. MD_ROWS/AD_ROWS/PD_ROWS/permission output keep 75524b3e (O). IS/SQL:278-290 bind IDs/content; no column.

## 5 Tools
brief.migration/op=null; writes_data=false; migration_class/window batch=null (P:541-543). Python/pytest/npm/process tools, scratch guarded loopback PostgreSQL/ephemeris/teardown; no external network (test_a53_inventory.py:221-233; t/conftest.py:22-68). Supply PG:71-76 guarded DSN/cluster-id inputs.

## 6 Tests
Tests FIRST; cockpit pins observed red base/assertion/blobs (P:544-551). Green independently assessed; kill mutants; exit0/no CI/DB/sky skips.
N1 old_pin: both sides accept ca17639b, refuse old/wrong canonical; accept two other-chart UUIDs (O; dasha_read.py:29-115).
N2 hidden_second: foreign any-tier/level4 build/reversal -> dasha_builds_mixed both sides/cutover (dasha_read.py:84-94; inventory_verifier.py:737-751; step06a_class_context.py:242-248).
N3 null_only: NULL-only/valid+NULL refuse both chart classes/sides (D:33).
N4 predicate: wrong chart/system/Lahiri/build/tier excluded; merged IDs=independent eligible SQL; no promotion (DD:217-256).
N5 unavailable_as_none: canonical 482012f1-710e-4a25-994a-93821f5871aa empty/unverified DashaReadConflict, wrong sole dasha_build_not_pinned; others dasha_context_unavailable/I2 reason; RS unknown/unrestricted, never none/false (O; RS).
N6 digest: build/tier/bounds/deletion-replacement IDs change digest, dasha/input same=false; computed_at-only equal (SQL:278-290; test_c48a_sealed_staleness.py:67-108,43-56 drift-only).
N7 boundary: next at boundary, wrong parent/level excluded; duplicate IDs retained/conflicts raise, reversed too (S:496-507; DD:97-168).
N8 history: old label retained; O-PP-1/2/3 loader/real ca rows at test_pp.py:14-21: Me-Ke-Me/Me-Mo-Ve/Me-Ra-Ve, licences/Ma->Ra boundary; assert/state measured delta (O).
N9 same_rows (PG:409,619 fixture follows live pin): bound same-row lords/bounds/licences/IDs, make_period_rows_for/B.frozen_c5_permission_context=baseline. (I) INTERPRETATION I3: only build/basis differs; no equal-rebuild claim (T0 Q6; DIGEST_A.md:87-88).
N10 CI: CG passes/coverage (M:5083). N11 stale_generated: corruption fails checks; census writer_digest_inventory hash=SHA256(inventory bytes) (platform/scripts/generate_capability_estate_census.ts:834).
N12 side_effect: spy rejects recomputation/promotion/conn commit-close/asset_throughput writes; no detectorless PASS (CLAUDE.md:101,115,119,141).
TESTS=seven owned tests+CG; newline paths relative to sc/. sc/, bash:
```sh
GOCHARA_A53_REQUIRE_DB=1 GOCHARA_SE1_REQUIRE=1 python3 -B -m pytest $TESTS -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"
python3 -B -m pipeline.orchestrator.provenance_inventory
python3 -B -m pipeline.orchestrator.provenance_inventory --check
```
platform/: npm run codegen:capability-estate-census; npm run codegen:capability-estate-census:check. Exit0 (sc/pipeline/orchestrator/provenance_inventory.py:41-59; platform/package.json:30-31). KY_ITEM=J-4p bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item (P:494-495,551).

## 7 Proof
Needs inspection.json template (B4_RULINGS.md:13); exits/red/hashes/negatives, no invented keys (P:552-553). No readback/steps (M:5045-5093).
N13 wrong_head: independent reviewer; absent head/deps/lease/CI-DB/squash-containment refuses; origin/kalayantra/j-4p retained (M:5056-5058,5087-5089; P:381-385; fl/cards/PARIKSAKA.md:13-16,21,27).

## 8 PR
PR J-4p: settled dasha. Body Contract/Owns/Red/Compat-events/Hashes/Review-deploy. ky review J-4p --detail "PR #<n> @ <40-hex head>" each head; hold blocks main merge (owner decisions:78-85).

## 9 Stops
One PR; no ledger/control/FROZEN/cross-campaign/Git writes, credentials/production, rebase/force-push/fabrication. Codex result to launcher; DIRTY generated->REGEN, else origin/main merge (P:556-558; fl/cards/KARAKA.md:17).
