```json
{"id":"KA-3a","kind":"feature","wave":1,"build_tier":"opus","routing_reason":"Protected migration; plan §9.","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"§8;§9;§14 Wave 1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md","revision":"1.1","section_range":"281-295","sha256":"ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569"},{"path":"platform/migrations/1341_k1_2_avadhi_candidate_dossiers.sql","revision":"1341","section_range":"6-31;36-77","sha256":"968029179cb77433e1d0c49c460335de2174f1305685fd5aeaca3aa07b07d239"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"fb7d650850d147208f9cce269c75f97ea7e6fc1d80a6e0766da142b700613143","original_failing_base":"6f925d1fe7fe67d9032d7fa078730ae7e3b57f2d","test_commits":[{"sha":"fedc5ae504fb76e2da042142e87743223fb1bab7","digest":"f6c82172ebed2bd0267dcea977950652865cd573790f4c1116c25137c9fa3492","path":"platform/python-sidecar/tests/l3/gochara/test_vedha_interval_relation.py"}],"expected_failing_assertion":"AttributeError: no build_obstruction_intervals (legacy replay; §6)."}
```
# KA-3a v1
Version1.0; status: preparation; changelog: T0 contract.
Y=platform/python-sidecar; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; SR=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; C=Y/services/kala_core; D=Y/services/gochara_rules/vedha_derive.py; SQL=/Users/Dev/kalayantra/run/schema/prod_schema.sql. Lines1-based.
## 1. Pins
Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json. Wave1 preparation. Require activation/J-0m ownership/K0a-4/KA-1w/KA-2 heads+squashes/inherited landing (M:2734-2738,2771). SR historical: fresh schema/slot before BUILD, approved window/readback before consumers.
## 2. Owns
Y/services/{kala_core/overlays,ka_vedha_gochara}/**; Y/pipeline/orchestrator/writers/ka_vedha_gochara.py; Y/tests/l3/ka_vedha_gochara/**; platform/migrations/<allocated>_ka_3a_vedha_candidate_intervals.sql; platform/scripts/kala_protected_migrations.txt; platform/src/generated/{nirmana-writer-digests,capability_estate_census}.json. Shared: C/idempotency/__init__.py literal whitelist additions only. Cockpit registers additions/tests/shared before BUILD; disclose direct consumers. No manifest/assertion/sky/judge/TS edits.
## 3. Excerpt
1341:26-27:
```excerpt
-- Retain the old natural key within the immutable legacy partition. F2's
-- exact instants distinguish sub-periods which begin on the same civil date.
```
Reconciliation: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md` §8: protected list replaces M:2768 workflow edits; separate tables preserve old keys (1341).
## 4. Contract
COCKPIT RULING T0 (proposed by job)
1. (I) INTERPRETATION I1: schema in KA-3a, no new ID (M:2764,2786-2787;plan:530-540).
2. (I) INTERPRETATION I2: two NEW tables below; DATE rows/key unchanged (SR:4496-4517; SQL:16457-16483,25298;1341:26-31).
3. I2: coverage header survives zero intervals; precise half-open UTC children (D:207-220,258-277; C/sky/coverage.py:42-76).
4. I2: candidate FK/guarded replacement/no legacy linkage/publication (C/manifest/__init__.py:32-86;C/idempotency/__init__.py:51-101).
5. (I) INTERPRETATION I3: provider here; live binding next (S/engines/surrogate/SURROGATE_ANSWERS_01-02.md:63; SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:84).

Existing kala_vedha_gochara SR:4496-4517 adds nullable method_qualification text,coverage jsonb,upstream_fingerprint jsonb; no defaults/backfill/rekey/candidate writes. Legacy readers unchanged.
I2 NEW schema:
- kala_vedha_gochara_candidate: chart_id uuid; generation,ayanamsha_id,vedha_kind text; PK(four); FK(chart_id,generation)→kala_layer_candidate (SQL:25169-25170). janma_reference_fact_id,formula_version text; natal_build_id uuid; coverage,upstream_fingerprint,payload jsonb; nullable method_qualification,null_reason text. Others NOT NULL. Generation nonempty/!=legacy/no default. Header/family even zero; build via FK.
- kala_vedha_gochara_interval: parent four; graha,state,classical_citation,source_qualification text; t_in,t_out timestamptz; reasons,obstructors,unknown_obstructors text[]; detail jsonb; nullable unqualified_reason,moon_scope text. Others NOT NULL. PK(parent,graha,t_in); FK(parent)→header. Finite t_in<t_out/no overlaps per parent/graha. House detail primary_house/vedha_house integers1-12; lattā source/target refs. No score/JSON segments/cascade; children first.
CHECK kind house_vedha/sarvatobhadra/latta; method_qualification qualified/method_contested/uncited_extension or NULL+reason. House state active/inactive/unqualified; reason iff unqualified; reasons/lists/scopes/precedence match D. Source vocabulary retained/flags measured.
I2 typed payload v1: SkyCoverage requested/source/covered JD/backend/convention/complete+exact gaps/search_state searched|partial|unsearched; header disclosures/enrichment/null reasons. Accepted sky horizon; outside unsearched/holes unavailable/empty≠clean. Validate JD/UTC; no guessed origin/Assertion period_anchor (C/assertion/__init__.py:136-165).
Fingerprint natal IDs/build/sky content/coverage/L0 pairs/lattā/locators/conventions/version (D:90-95); input change→stale. chart_facts refs match chart/build/ayanamsha; contradiction halts/absence typed gap/external-computation spec.
candidate_generation(ctx), chart/build/mutable-state locks/guards BEFORE deletion. Reject legacy/current/published/retained; unbound main no-op. Two helper literal entries; caller guards immutability. Empty clears intervals/retains header+grain. ctx.db_conn only; no commit/close/asset_throughput/serving/count_sql switch.
Independent adapter/D verifier (:40); both exceptions/stored Moon excluded/inactive scope except Mercury/per-instant offsets. No viparīta+no-served-source disclosure; SBC information_unavailable/no approximation; lattā verse_cited/Ketu gap. S/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md:52,54: obstructor_residence_unknown,node_obstruction_undecided,node_residence_unknown; verbatim XXVI47-48+locator/applied_to_computation=false; no concurrent_latta_count/numbers. Missing passage unavailable.
## 5. Metadata
brief.migration=additive; brief.op=null; writes_data=true; migration_class=NEEDS-PROTECTED-WINDOW; window_batch_id=null pending approval. One migration/list entry/no GRANT. KV3-SCHEMA-2 §4=preservation precedent only.
## 6. Acceptance
(I) INTERPRETATION I4: LEGACY test replay/original logic/current fingerprint import; not full-base/candidate proof. AttributeError: LEGACY_RED.json. Already-green→independent assessment (plan:544-549). Candidate tests FIRST; cockpit pins committed red before BUILD; legacy green≠done.
Owned tests: literal tests/l3/gochara_rules/fixtures/l0_vedha_rows_2026_10_02.json→partition/equality vs D+oracle; exceptions/nodes/gaps/precedence/reasons/scope/century offsets/no viparīta/SBC unavailable/sourced lattā-enrichment/Ketu gap. Kill endpoint/exception/node/gap/constant-offset/coverage/fake cancellation-grid-quote-qualification mutants.
Disposable PostgreSQL: schema before/after; retained IDs/values/key/readers byte-equal; two generations coexist; duplicates/overlaps/reversed/nonfinite/wrong parent-chart-build-natal rejected; migration/replacement twice equal keys/content/counts; zero retains coverage; other partitions unchanged; published/retained overwrite/concurrent-publication/DB errors refuse.
Y: python3 -B -m pytest tests/l3/ka_vedha_gochara tests/l3/gochara_rules/test_am18_vedha.py tests/l3/gochara/test_vedha_interval_relation.py tests/l3/kala_core/ayanamsha/test_ayanamsha.py -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"
Y: python3 -B -m pipeline.orchestrator.provenance_inventory; then --check. Platform: npm run codegen:capability-estate-census; then :check. Inventory hash equality. KY_ITEM=KA-3a bash "$KY_FLEET/precheck.sh" --item. Exit0/no skips; CI/Kāla DB Tests/review. Five steps M:2742-2746: tests+verdict (answer05:75).
## 7. Evidence
inspection.json: head/base/tests/deps/schema/slot/negatives/preservation/facts/coverage/fingerprint/I1-I4. Readback ledger/catalogue/retained rows/registry/squash+verdict.
## 8. PR
[PROTECTED-WINDOW] Candidate vedha intervals. Body T0/schema/owns/red limits/compat/tests/readback. ky review KA-3a --detail "PR #<n> @ <40-hex head>". Independent verifier; cockpit writes Git.
## 9. Do not
No production/credentials/control/FROZEN/judge edits, legacy rekey/delete/new ID/fabrication/publication/rebase/force-push/ledger PR. DIRTY generated→REGEN, else launcher. Missing gates block BUILD.
