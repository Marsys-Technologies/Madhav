```json
{"id":"K8-REG","kind":"operation","wave":1,"build_tier":"opus","routing_reason":"Migration (§9).","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"§8;§14","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/control/kalayantra/plan_model.json","revision":"snapshot","section_range":"4223-4272;1367","sha256":"64c6b291670cea2226e322d804fbf238980ae2864d19f34e6a1a05229f231edf"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md","revision":"1.1","section_range":"300-327;332-336","sha256":"85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef"},{"path":"platform/scripts/governance/asset_census.py","revision":"snapshot","section_range":"2085;2649;3118-3162;472;11951;17435","sha256":"43bd2552c08cdedecd397fe0067a2d1fb15b372d9ef805d67bfc7c12ff9dd64c"},{"path":"platform/scripts/governance/fingerprint_declarations.py","revision":"snapshot","section_range":"10-31;61-103;1006-1015;1124-1130","sha256":"93c56d9de13ff021b15f4e2a21da6b981d2c58f5674e13b9e202fd194ad3a07e"},{"path":"platform/scripts/governance/nikasha_stale_certs.py","revision":"snapshot","section_range":"236-267;351-452","sha256":"80b32c73b2deaaae26931ea4271206558bcdf925cc4e20077f9913be8d035726"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"0511d81ec84d59c9619aca9c863c4b16308d916d1ea5938f8e76797f29b3a126","semantic_acceptance":"Twice-applied ka_* correction preserves IDs/data; independent source-bound tests/head/squash readback prove registry truth.","negative_fixtures":["foreign/deleted/new ID","bad edge/count/generation/integrity","retirement/reseed revival","bad fingerprint","missing deps/wrong head/stale bytes"]}
```
# K8-REG v1 · READY FOR ADMISSION
Version1.0; status: preparation; changelog: initial T0.
P/M/A/E/F/N=spec_sources[0..5].path; Y=platform/python-sidecar; G=platform/scripts/governance; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3. 1-based citations.
## 1. Pins / gates
Release SUVARNA-L0L2-CLOSE-REV30-20261013 (/Users/Dev/kalayantra/run/RELEASE_RECEIPT.json); Wave1 preparation (P:728-730; S/engines/lane2/B4_RULINGS.md:5).
Needs accepted install/schema/slot, K0a-4/K2-2/K3-2/K4-3/K5-G1b/K6-5/K7-4/KA-4b heads/squashes (M:4228-4236) and separate fingerprint PR. Cockpit registers prerequisite; no invented ID.
00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json:444-488 is historical (:8-12); authenticate actual schema/ledger/registry.
origin/main:00_ARCHITECTURE/control/census/EVIDENCE_rev30/README.md:26-29 pins tool7e63cc872/registry30/declarations1.77.0, L0-L2 only; :76 records37 missing fingerprints. Working E:470 is rev27: reconcile released main. Criterion hash E:472-479 ≠ content hash N:351-412.
## 2. Owns
One allocated platform/migrations/*.sql: UPDATE existing ka_* registry rows only.
platform/scripts/seed/asset_registry_seed.ts (ka_* only; below SE)
G/asset_declarations.json (ka_* only)
platform/src/generated/nirmana-writer-digests.json
platform/src/generated/capability_estate_census.json
platform/scripts/__tests__/asset_registry_seed_dag_parity.test.ts
G/__tests__/test_e6_gh_declared_service_and_reads_match.py
G/__tests__/test_e5_7_build_completion_produced_set.py
Expand G; scoped tests. Read-only writers/readers; no consumer/fleet edits.
## 3. Excerpt / reconciliation
A:321:
```excerpt
Where a detector is `NONE`, the mapping says `NO_DETECTOR` and names the engine-branch revision that would change it — a dependency, never a claimed PASS.
```
Reconciliation: `00_ARCHITECTURE/control/kalayantra/plan_model.json`:4256 requires fingerprints; E:2649-2663/3160-3162 rejects unknown fields, F:64-65 is L0/global. S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:55,85 orders separate additive extension/custodian review, then K8-REG.
## 4. Contract
COCKPIT RULING T0 (proposed by job)
1. Separate PR extends G/asset_census.py/G/fingerprint_declarations.py, tests/field description; Suvarna reviews (answer05:55,85; E:3160-3162).
2. (I) INTERPRETATION I1 (lines2-4): optional ka_* `fingerprint` uses F:89-103 shapes, scope=chart/groups=[]/definition=nikasha_stale_certs.table_fingerprint/1; absent/null=unknown. Proposed API.
3. ALL retained chart rows; real generation/snapshot/ayanamsha natural keys; no selector. Map name/key/exclude→N:236-267 VOLATILE; N:417-452 binds chart; F:1124-1130 composes.
4. Retain IDs/build/generation/qualification/ledger; exclude only evidenced non-key wall-clock stamps. F:25-31 validation; no_table/shared_table/no_plain_natural_key=undeclared; partial≠full/current/PASS.
5. Bind schema/registry/code/declaration digests/computation; preserve L0 APIs/census (main README:26-29,76; CLAUDE.md:141). Seal consumed-row identity unchanged (M:5036).
Prerequisite: G/__tests__/test_e5_7_fingerprint_declarations.py/validator tests prove E.validate_declarations AND adapter→N.table_fingerprint read-only. Two charts/two generations: permutation/stamp-only equal; semantic/key/generation/delete/new-column moves hash; foreign-chart change doesn't. Bad key/table/column/evidence/scope/exclusion/read/service/full/PASS refuse. Absent field changes no cell/criterion hash; L0 hashes equal. Shared partition unproved→undeclared; no ledger/serving changes.
(I) INTERPRETATION I2: implemented ka_* + evidenced lifecycle (A:303,321; M:4252). Crosswalk writer/head/reads/writes/generation/key/count/integrity/produced/lifecycle/revision/gaps; cockpit adds prerequisites; unresolved unchanged/disclosed.
Counts match published-head/legacy reader. Candidate proof binds Y/services/kala_core/manifest/__init__.py:76-86 candidate_generation(ctx). E:2085-2101 literal filters supply no runtime selector: wrong retained-generation SUM is gap, required completion waits for consumer. Services keep NULL counts (SE:2408,2424,2440).
Nonconstant/chart-scoped count_sql; engine integrity unparameterised/read-only, truthy first column after completion, false on corruption (A:317; E.integrity_sql_problem:11951). Reads match known active producers/full acyclic graph; incomplete parse disclosed (E._measure_dag:17435). has_writer/has_substeps/target_table/clear_tables/natural_key_partition match writers/constraints; produced_tables in declarations (M:4265); seed parity.
Lifecycle requires accepted cutover; century hold through K9-3 (M:1403; A:332-336). Prove reseed durability via ka_* literals (SE:3560-3573 RETIRED guard); ambiguous successor retains tuple/gap. Tulana refusal requires typed D-R6/cockpit dependency reconciliation (M:1367); no local skip.
## 5. Metadata
(I) INTERPRETATION I3: operation=registry-data correction; code completion/PR retained (M:4268-4270), runtime extension separate; no invented red/executor permission. brief.migration=allocated UPDATE; brief.op=null; writes_data=true; migration_class=ROUTINE-OK; window_batch_id=null. No widening.
## 6. Acceptance
Tests first; disposable PostgreSQL: migration twice+seed; IDs/non-ka_* rows/retained data unchanged. Real SQL/chart A/B/mode counts; insert/delete moves count, corruption flips integrity. Generation/loss/retirement/reseed/edge/shape mutants fail; no DB skips.
Repo: G=platform/scripts/governance; python3 -B -m pytest "$G/__tests__/test_e6_gh_declared_service_and_reads_match.py" "$G/__tests__/test_e5_7_build_completion_produced_set.py" -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"
platform: npx --no-install vitest run scripts/__tests__/asset_registry_seed_dag_parity.test.ts
Y: python3 -B -m pipeline.orchestrator.provenance_inventory; repeat --check
platform: npm run codegen:capability-estate-census; npm run codegen:capability-estate-census:check
Bytes equal generators; census inventory hash=inventory bytes (platform/scripts/generate_capability_estate_census.ts:834).
KY_ITEM=K8-REG bash "$KY_FLEET/precheck.sh" --item. Exit0/negatives/CI/Kala DB Tests. Independent head verdict + deployed-squash containment/readback (P:380-389), never branch alone.
## 7. Evidence
inspection.json: author/head/pins/schema/slot/prerequisite verdicts/crosswalk/rows/SQL/tests/mutants/reseed/generators/T0/I1-I3/gaps. Installed readback: ledger/registry/count/integrity/retained data/deployed SHA-image; independent squash verdict.
## 8. PR
PR "Correct Kala registry truth": owns/T0/deps/crosswalk/tests/preservation/metadata/readback/gaps. ky review K8-REG --detail "PR #<n> @ <40-hex head>"; new head→review. Cockpit commits; admission≠execution.
## 9. Do not
No new IDs/DELETE/early cutover/fabrication/foreign/shared-consumer/control/FROZEN/applied-SQL/credentials/production/network/ledger PR/Git writes/rebase/force-push. DIRTY generated→REGEN, otherwise launcher reconciles main. Campaign handshake.
