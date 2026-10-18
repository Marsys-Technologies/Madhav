```json
{"id":"J-4p","kind":"feature","wave":0,"build_tier":"opus","routing_reason":"kernel: P:569","needs_chart_data":true,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"509-580;720-726","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md","revision":"1.4","section_range":"487-513","sha256":"d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47"},{"path":"00_ARCHITECTURE/briefs/l3_families/contracts/DASHA_TABLE_CONTRACT_v1_0.md","revision":"1.1","section_range":"27-67","sha256":"93ddc1d9104421c4c989c4e73962631eaad56d3026259b108e3c77c1122d1a9a"},{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md","revision":"1.0","section_range":"26-45","sha256":"99c7156dd93a50febb45fd7d265d2fbef4b4ee733de1e94301a2b9e18b00216d"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"2f89e593b9bc1b158d9faceb682af8e4cbc0f6200c1b02b014d236299f66de70","original_failing_base":"e44f9fe2d4b21ce4e7b1a925a180f618d37b9a73","test_commits":[{"sha":"d0fcce3b2f76afb83cc2ac5a6afbd70f7bf9c65c","digest":"7f515716e140268f8a0fa0666176bd89332f99c1fef82459788bd27a7e166357","path":"platform/python-sidecar/tests/l3/gochara_rules/test_am10_repin_75524b3e.py"}],"expected_failing_assertion":"test_am10_repin_75524b3e.py:27,31 AssertionError: old 1f89fd4c != expected 75524b3e (historical replay, section 6)."}
```
# J-4p v1
Version1.1; status:preparation; changelog: J4P-B1 settlement; v1.0 T0.
Repo paths; source lines. P/S/D/A=spec_sources[0..3].path; Y=platform/python-sidecar/; K=Y/services/gochara_kernel/; R=Y/services/gochara_rules/; C=Y/scripts/kala_gochara_cutover/; T=Y/tests/l3/gochara/; U=Y/tests/l3/gochara_rules/; M/SR=00_ARCHITECTURE/control/kalayantra/{plan_model.json,SCHEMA_RECEIPT_v2_2.json}; F=00_ARCHITECTURE/briefs/kalayantra/fleet/; E=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; O=E/OWNER_RULINGS_DIGEST_A.md; DD=Y/services/gochara_grammar/dasha_data.py; IS=K/inventory_store.py; B=C/step06b_windows_projection.py; SQL=platform/migrations/1206_gochara_search_inventory_completeness.sql.
(I) Run evidence: controller supplies.
## 1. Pins
Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,13-19; registry30(job). Wave0 before J-1a/J-4d (P:720-726); accepted install/J-0m/K0-SV heads+squashes required.
SR:5,8-15 historical; /Users/Dev/kalayantra/run/schema/prod_schema.sql:5573-5595,14274-14290 columns confirmed; seeded2026-10-12T07:15:26Z; SHA256=f82aa93c60c397eb3e44c5317a1721bfa75db6a9fd32c551b5c5f89796804120. Schema/ledger≠SR:16-25. Measured current receipt/rebind before BUILD (E/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:83). PW1.0=00_ARCHITECTURE/briefs/kalayantra/KALA_PROTECTED_WINDOW_v1_0.md:3.
## 2. Owns
K/dasha_read.py; K/dasha_settlement.json; K/inventory_verifier.py; K/implementation_digest.lock.json; K/input_vector.py; K/input_vector_verifier.py; R/permission.py; C/step06a_class_context.py;
T/test_a53_dasha_read.py; T/test_a58_honest_tier_readers.py; T/test_j4p_dasha_settlement.py; T/test_step06b_per_instant_permission.py; T/test_a53_moon_scope_domain.py; T/test_a53_verification_job.py; T/test_a53_r16_amendments.py; T/test_a53_inventory.py; T/test_c48a_sealed_staleness.py; T/test_a25_v41_candidate_writer_pg.py;
U/test_pp.py; U/test_am10_repin_75524b3e.py;
platform/src/generated/nirmana-writer-digests.json; platform/src/generated/capability_estate_census.json.
Scope/CI list (M:5083; P:530-534). F/FROZEN_PATHS.txt missing/prohibited -> STOP.
## 3. Excerpt
S:497-498; revision/hash above:
```excerpt
  `[start_iso, end_iso)`; an instant `t = end_iso` belongs to the **next** row. Boundary
  instants are unambiguous by construction.
```
Reconciliation: `00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md` ca replaces historical runtime pin (M:5085; D:64,67; O:46-48); other semantics retained.
## 4. Proposed COCKPIT RULING T0
1. (I) INTERPRETATION I1: direct verifier/cutover/tests; independent SQL (P:530-534).
2. J4P-B1: K/dasha_settlement.json carries L1_SETTLED, source 2051951aaa3f4e1b6a55d728f703bc074daf11ef:CAMPAIGN_COORDINATION.md:9205-9211 and release SUVARNA-L0L2-CLOSE-REV30-20261013. Changes require a reviewed PR; reader/verifier load/reparse independently; bytes enter both implementation digests.
3. (I) INTERPRETATION I3: consumed IDs/content bind build; deletion drifts (IS:126-150; SQL:278-290).
4. Both paths refuse settlement_missing, settlement_malformed, settled_build_absent, settled_build_ambiguous, chart_not_settled; retain NULL guard. No singleton/other-chart fallback. (I) INTERPRETATION I7: match the full run UUID, not a colliding eight-hex prefix; all multi-build states refuse.
5. MD_ROWS/AD_ROWS/PD_ROWS+permission() retain75524b3e label apart from runtime DASHA_READ_CONTRACT ca; no relabelling/served oracle use (O:48; R/permission.py:11-85,169-200; CLAUDE.md:134-145).
6. (I) INTERPRETATION I5: same-row lords/bounds/licences/IDs/function outputs; only build/basis metadata excluded; no equal-rebuild claim (M:5080,5085; D:22,67; O:48).
Signatures retained: load_pinned_vimshottari(conn,chart_id)->(rows,contract); make_period_rows_for(conn,chart_id)->(callable,contract); assert_single_pinned_build(conn,chart_id)->list[str]. Columns SR:2420-2437/dump §1. TWO_PASS_VERIFIED/levels1-3; no computation/promotion.
## 5. Metadata/tools
brief.migration/op=null; writes_data=false; migration_class/window_batch_id=null. Python/pytest/npm; ephemeris; DB deferred to CI (cockpit job ruling).
## 6. Acceptance
(I) INTERPRETATION I6: historical AM-10 replay, not ca proof: LEGACY_RED.json lines27,31 fail1f89fd4c vs75524b3e(exit1); post-repin green. Errors≠red. Precedent PACKET_KA-3a_v1.md:38. Install idempotently; already-green -> independent assessment. Current tests FIRST/cockpit pins committed red before implementation (P:544-551).
N1 both sides/cutover accept ca, refuse old/wrong canonical; unnamed chart refuses; no fallback.
N2 foreign build any tier/level4/reversed -> mixed both sides; N3 NULL-only/valid+NULL refuse both chart classes; N4 exact chart/system/Lahiri/build/tier/levels eligible IDs=independent SQL, no promotion (D:64; DD:217-256).
N5 absent/unverified/level4-only refuses settled_build_absent; unnamed charts chart_not_settled; no served empty-context licence-none/false (O:46; K/record_store.py:1252-1267,1504-1511).
N6 build/tier/bounds/delete-replace IDs -> digest drift/stale; computed_at-only equal; T/test_c48a_sealed_staleness.py:43-108 drift-only (SQL:278-290).
N7 boundary next row/parent/level filtering; equal duplicates retain all source IDs; conflicting/reversed overlaps fail (S:496-507; DD:97-168).
N8 old labels/bounds preserved; O-PP-1/2/3 via real ca rows:2013-12-11 Me-Ke-Me,2018-11-28 Me-Mo-Ve,2022-01-03 Me-Ra-Ve; Ma->Ra boundary delta measured/asserted (O:48; U/test_pp.py:14-57).
N9 hash-bound live-row baseline; make_period_rows_for/B.frozen_c5_permission_context equal under I5; missing export blocks BUILD (T/test_a25_v41_candidate_writer_pg.py:409,619).
N10 T/test_a53_ci_db_list_guard.py passes; N11 corrupted outputs fail checks/census hash=SHA256(inventory bytes); N12 spies reject computation/promotion/commit-close/asset_throughput/detectorless PASS (CLAUDE.md:101,119,141-145).
TESTS=seven owned tests+T/test_a53_ci_db_list_guard.py; launcher supplies newline Y-relative paths. In Y:
```sh
GOCHARA_A53_REQUIRE_DB=1 GOCHARA_SE1_REQUIRE=1 python3 -B -m pytest $TESTS -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"
python3 -B -m pipeline.orchestrator.provenance_inventory
python3 -B -m pipeline.orchestrator.provenance_inventory --check
```
Platform: npm run codegen:capability-estate-census; then :check. Exit0/no skips. KY_ITEM=J-4p bash "$KY_FLEET/precheck.sh" --item. Independent rerun/mutants+CI/Kāla DB Tests at reviewed head.
## 7. Evidence
inspection.json=cockpit pilot template (E/B4_RULINGS.md:15); head/base/tests/red/green/deps/schema/slot/settlement/guard/compat/mutants/hashes proposed. No readback/steps; missing head/lease/deps/CI/squash refuses (F/cards/PARIKSAKA.md:13-16,21,27).
## 8. PR
PR J-4p: settled reader/verifier; Contract/Owns/Red/Compat/Hashes/Review. ky review J-4p --detail "PR #<n> @ <40-hex head>". origin/kalayantra/j-4p (M:5056-5058). ACCEPTED head+green CI -> fleet merge (A:26-33); hold obsolete. Cockpit records T0/scope; Git launcher-owned.
## 9. Stops
One PR; no ledger/control/FROZEN/foreign/CI edits, credentials/production, rebase/force-push/fabrication. DIRTY generated->REGEN, else launcher merges origin/main (P:556-558). Admission only checker success; missing execution gates block BUILD.
