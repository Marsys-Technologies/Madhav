```json
{"id":"K7-4","kind":"feature","wave":null,"build_tier":"opus","routing_reason":"Typed comparator / mapping.","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"§7–§12","sha256":"85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"§3.10","sha256":"ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_VALUE_REVIEW_v1_1.md","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"ka_tulana; F-L20","sha256":"57d528320b5ee1b514d442a129f699b3fae0a166bb4e4651cbb6325ccde483bc"},{"path":"00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"§2 R-6","sha256":"dcb854cb796f7b3d736a72e9c77f33639dff586194dac836c6ef6ca23d1eb5be"},{"path":"00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md","revision":"8482540d666f8ea930bf9e62214cf9002b25adec","section_range":"§0; §7","sha256":"f418ef9d9000a4c7e20dce78cefcd9210617f7b1fda91d107515290243ea7b24"}],"schema_receipt_id":null,"pw_mechanism_version":null,"release_pins":{"dash_build":null,"registry_revision":null},"packet_sha256":"4ffc9387d299220d1a1a2924c7c106c49cc45df8385379299eadb19b56877d13","original_failing_base":null,"test_commits":[],"expected_failing_assertion":null}
```
# K7-4 v1 - DRAFT
## 1. Pins, reads, prerequisites
Source pins above; citation macros:
P=00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md; C=spec_sources[0].path; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; Y=platform/python-sidecar; R=platform/src/lib/retrieval/registry/layers/L3_kala; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; T=S/engines/lane2/owner/OWNER_RULINGS_K7-4_TABLE.md; O=S/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md; U=/Users/Dev/kalayantra/wt/k2/Y/services/ka_sangam/jury/reader_contract.json; L=/Users/Dev/kalayantra/wt/k5/R/view_common.ts.
Read T:26-60/cited code+DDL, O:48-50,U:5-21,L:7-19,79-92,343-364,Owns. D-R6=approved; accepted K4-2b/K7-3 base containment (M:2594-2598,2633; P:330-337). Order: B-2->D-R6; K4-2aw->K4-2b; K7-2->K7-3->K7-4 (M:1358,2532,3298; C:453-460). Needs schema/slot/tests/templates and 00_ARCHITECTURE/briefs/kalayantra/fleet/FROZEN_PATHS.txt (P:367-369; S/engines/lane2/B4_RULINGS.md:5,13-14). Unbound/unpublished->unavailable (T:31,35; U:15-20); no extra approvals.
## 2. Owns
Files (expand prefixes):
- Y/services/ka_tulana/: ranker.py, writer.py, __init__.py
- Y/pipeline/orchestrator/: writers/ka_tulana.py, service_probes.py (Tulana only)
- Y/main.py (mount); Y/tests/: l3/test_ka_tulana.py, test_service_probes.py (Tulana only)
- R/: call_service_wrappers.ts, view_priority.ts, view_common.ts (PRIORITY only); view_common.test.ts, views_registry.integration.test.ts, __tests__/f131_priority_ranking_glossary.test.ts
- platform-mcp/src/tools/kala_views/: priority.ts, f171_disclosure_receipt_regression.test.ts
- platform/scripts/governance/asset_declarations.json (ka_* only; one landing)
- platform/src/generated/: nirmana-writer-digests.json, capability_estate_census.json
Allowed class: allocated platform/migrations/ SQL, ka_tulana health_probe only (P:338-342). cwd Y `python3 -B -m pipeline.orchestrator.provenance_inventory`; cwd platform `npm run codegen:capability-estate-census` (Y/pipeline/orchestrator/provenance_inventory.py:21,41-59; platform/package.json:30). Consumers disclosed (P:530-534).
## 3. Excerpt / reconciliation
ALGO:263, pinned above:
```excerpt
**Disposition.** Service, re-based; wiring into PRIORITY is the native's R-6.
```
Reconciliation: `00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md` uses T:30-58/O:48-50/T0. R-6 wiring; departure: execution evidence/default_applied:false (C:517).
## 4. Contract
T:26-35/58 mandatory: all mappings/tolerances/null/frame/relations/annotations; kala_field_windows (chart_id,window_id), snapshot-scoped. No weights/fallback/counting/averages. Delete I11_WEIGHTS/_composite/exports (Y/services/ka_tulana/ranker.py:38-43,218-237; __init__.py:10-25).
(I) INTERPRETATION I1: POST /api/compute/tulana_compare in ranker.py, mount/auth Y/main.py:90-108. Input {windows,date_from,date_to,question_frame?,preference?}; unique active-axis preference+remaining defaults; bad names/duplicates/H<1 error. Output T:35 + ordered/rejected. Registry->Python beside ranked_signals; facade forwards frame/preference, thesis uses comparison. Errors refuse. R/call_service_wrappers.ts:547-598,704-830; platform-mcp/src/tools/kala_views/priority.ts:229-240,290-311,372-393. Keep platform-mcp/src/tools/register_p1_aliases.ts:1028-1040 alias; legacy_scalar:true; full-front top_k with front_members_omitted (O:50).
(I) INTERPRETATION I2: T:51 inclusive DATE end->end+1 for relevance, H=90 horizon; stable <=/no extra tolerance; identity presentation ties only.
(I) INTERPRETATION I3: CERTIFICATION_MAPPING in __init__.py: seven L:7-19 views/URIs/sources/tier SELECT/density_contract/goldens/hashes, C:321 fields; platform/scripts/governance/asset_census.py:171-217 revisions/bindings/verdicts, NONE->NO_DETECTOR. TestMapping checks files/declarations/hashes/goldens; reuse matching hashes only (M:2637-2645; CLAUDE.md:141).
## 5. Migration metadata
health_probe UPDATE; 849 immutable (platform/migrations/849_nirmana_l3_w3_tulana_health_probe.sql:77-100). brief.op=null; brief.migration/migration_class/window_batch_id=null until cockpit stamps path/class/batch; then writes_data=true (platform/scripts/governance/pravaha_tracker/completion.py:37-49). T0 Q3: retain self-test interface/probe_type; replace weighted oracle independently (Y/pipeline/orchestrator/service_probes.py:918-944).
## 6. Acceptance - negatives first
T:41-55 vectors/exact results, row-order named cases: N1Tie,N2Win,OpenElapsed,DwTie,QualificationIgnored,NullNotZero,Unbound,RobustWin,WeakestIgnored,Stage9Null,RelevanceTie,DomainWin,UnknownFrame,ParetoWin,TradeoffFront. Direction/tolerance/imputation/winner mutants must fail.
Code negatives (M:2620-2630; T:35; C:354; CLAUDE.md:101,119-141):
- Swap: A/B mirrors, ties symmetric.
- Preference: tradeoff order changes; evidence deep-equal/relations unchanged.
- Quiet: unavailable/silent distinct in annotations/NOW arrival; no obstruction order (T overrides M:2623).
- Weights: import-closure scan + restored 0.40/0.25/0.20/0.15 fails tradeoff/preferences.
- Contest: only bound contest changes dissonance.
- Bypass: service opposes SQL; output/thesis follow service; frame forwarded.
- Compatibility: old goldens/flag/exact cut; absent column/mixed generation refuses.
- Fidelity: F131/F171 refs/values/labels/disclosures/density/gaps/empty_reason preserved; fabricated verification fails.
- FalseHealth: bad relation fails both checks/writer raises; no commit/close/asset_throughput.
- Mapping: seven registry/Vidhi/narration goldens; deleted entry/tier/test/hash/revision refuses step (C:321; fleet/cards/COVERAGE.md:87,101-104,169,178).
cwd=absolute worktree/directory; TESTS=Owns test paths newline-delimited (P:494-495):
Y: `python3 -B -m pytest tests/l3/test_ka_tulana.py tests/test_service_probes.py -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"`
platform: `npm test -- src/lib/retrieval/registry/layers/L3_kala`
platform-mcp: `npm test -- src/tools/kala_views/f171_disclosure_receipt_regression.test.ts`
repo: `KY_ITEM=K7-4 bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item`
Exit 0/all pass; scratch mutants fail named assertions; generators --check pass. Python/Node foreground; mocks no DB/network. Loopback DB phase: KALA_VIEW_DB_TESTS=1 platform command, docker/psql harness (R/views_registry.integration.test.ts:106-134); SQL/adapter/health_probe tests; no skips/network. Commit/base/digest/red bindings; green->independent assessment (P:544-551). BadCompletion refuses wrong head/open deps/missing CI/deploy; independent verdict+green CI+Kāla DB Tests+step+merge/deploy containment+squash readback required (P:380-389).
## 7. Evidence template
Frozen inspection.json/readback template (P:552-553; B4 Q13): head/hashes/tests/mutations/generators/schema/slot; credential-free squash health_probe readback.
## 8. PR template
One PR "Wire Tulana into PRIORITY"; frozen body contract/scope/tests/mapping/readback; [PROTECTED-WINDOW] if required. `ky review K7-4 --detail "PR #<n> @ <40-hex head>"`; Codex commit_message, no Git; new head->review (P:554-555).
## 9. Do not
No FROZEN/control/cross-campaign/applied-SQL/migrate.ts/deploy.yml/executor edits or production/credentials/ledger PR/rebase/force-push/private live promotion. DIRTY generated->REGEN; else launcher main merge (P:556-558).
