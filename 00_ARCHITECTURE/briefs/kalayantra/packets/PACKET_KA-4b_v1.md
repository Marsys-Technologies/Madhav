```json
{"id":"KA-4b","kind":"feature","wave":null,"build_tier":"opus","routing_reason":"Opus: governance path (P:574).","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md","revision":"1.1","section_range":"242-259;448-476","sha256":"85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md","revision":"1.1","section_range":"362-391","sha256":"ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_VALUE_REVIEW_v1_1.md","revision":"1.1","section_range":"28-42","sha256":"57d528320b5ee1b514d442a129f699b3fae0a166bb4e4651cbb6325ccde483bc"},{"path":"00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md","revision":"1.0","section_range":"17-28","sha256":"dcb854cb796f7b3d736a72e9c77f33639dff586194dac836c6ef6ca23d1eb5be"},{"path":"00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md","revision":"1.0","section_range":"78;118;136-140","sha256":"f418ef9d9000a4c7e20dce78cefcd9210617f7b1fda91d107515290243ea7b24"}],"schema_receipt_id":null,"pw_mechanism_version":null,"release_pins":{"dash_build":null,"registry_revision":null},"packet_sha256":"57c188bdc7e28813a9a14248b56314a51f7dd6087e92d2426e49cb89c3bf11aa","original_failing_base":null,"test_commits":[],"expected_failing_assertion":null}
```
# KA-4b — DRAFT
Path keys/physical lines:
L/A=spec_sources[0..1].path; J=platform/scripts/governance/pravaha_tracker/completion.py; P=00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md; C=CLAUDE.md; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet;
S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; O=S/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md;
R=platform/src/lib/retrieval/registry/layers/L3_kala; B=platform/src/lib/retrieval/registry/layers/L0_brahmagyan; E=platform-mcp/src/tools/kala_views; H=platform-mcp/src/lib; W=/Users/Dev/kalayantra/wt/k7.

## 1. Pins
Read U:19-25/O:56-60/C:119-144, Owns/imports/tests; inherited W/R/{view_elect.ts:1-8,view_common.ts:15,54-61,195-277,338-364,views_registry.integration.test.ts:70-188}.
K0a→K7; KA-4→evaluator; L0-M/evaluator parallel→KA-4b last (L:450,453,461; U:13,25). Needs accepted K7-1b/KA-4/new L0-M/evaluator heads/verified squashes in base, fixtures, rules/reseal/schema, slot/install, F/FROZEN_PATHS.txt/frozen templates (P:330-337,367-369; U:23-25; S/engines/lane2/B4_RULINGS.md:13-14). Cockpit adds evaluator dependency/detaches K8-KA; REPIN after Gaṇita rebuild (P:529).

## 2. Owns
R/: view_elect.ts, view_elect.test.ts, view_common.ts (ELECT only), index.ts (ELECT only), views_registry.integration.test.ts.
E/: elect.ts, elect.test.ts, __tests__/elect_ledger_alias_f122.test.ts, __tests__/elect_budget_trim_f122.test.ts, __tests__/elect_sections_coverage.test.ts.
H/: kala_lattice_query.ts, kala_lattice_query.test.ts, muhurta_undertakings.ts.
platform-mcp/src/tools/: muhurta_finder.ts, muhurta_finder.test.ts (upanayana only).
B/: query_parihara_graph.ts, __tests__/query_parihara_graph.test.ts (counts/narration).
platform/scripts/governance/asset_declarations.json (ka_* only, one landing).
platform/src/generated/: capability_estate_census.json, capability_knowledge.snapshot.json, muhurta_undertakings.generated.ts (regenerate).
Consumers disclosed; RITUAL preserved (M:2945-2957; P:530-534; U:25). Generator prerequisite: W/platform/scripts/generate_muhurta_undertakings.ts:1-23.

## 3. Excerpt
A:383, revision/hash above:
```excerpt
7. **No composite.** A candidate carries: interval, factors present (cited), doṣas, parihāras applied (cited, scoped), residual doṣas or `cancellation_unassessed`, personal layer, uncited factors in their own list.
```
Reconciliation: `00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md` U:19-25 service, splits/ledger/factors queued, mapping detached; O:60 legacy flag.

## 4. Contract
U:19-25: POST /api/compute/parihara_evaluate; ruled request/response/grammar/states; project envelope/terms/facts/citations/by_rules unchanged, no TS predicates/key-match. Transport R/call_service_wrappers.ts:126-152. Location: caller or disclosed lattice_reference_location (U:19).
elect_read+kala_elect_get; undertaking≠event_class (W/R/view_common.ts:15,54-61,79-90). Upanayana enum; marriage→marriage+general; upanayana→upanayana+general; others→general only; finder PG82 v.46 only (O:58; A:381).
O:60 new fields/no composites/min_score; old shape+legacy_composite:true; U:25 vivaha_chapter_dosas:not_detected. Clean note “no cited doṣa overlaps; uncited convention spans listed separately”; partial assessment≠clearance. Live scope counts replace ZERO/UNCANCELLED (B/query_parihara_graph.ts:137-194; H/kala_lattice_query.ts:292-399). Existing columns B/query_parihara_graph.ts:138-140; U:23 additions require receipt (P:538-540).

## 5. Metadata
brief.migration=null; brief.op=null; migration_class=null; window_batch_id=null; writes_data=false (J:37-49).
Node/Python; units offline; SQL needs loopback PostgreSQL+docker/psql, supplied ephemeris; no external network/production (W/R/views_registry.integration.test.ts:104-116).

## 6. Acceptance
First write R/view_elect.test.ts/E/elect.test.ts/Owns tests, U:19 fixtures; mutants fail; verifier repeats (P:544-561):
N1 scope_leak: debilitated kartarī marriage→cancelled/v.88 locator; business→unassessed; scope/locator mutant fails (A:374,389).
N2 unknown_residual: missing/partial/U:19 reasons never residual/clear (A:379).
N3 keymatch: false conjunct/natal/wrong time-candidate cannot cancel; v.68 no vedha cancellation; v.89 strength_undefined; v.91 no subtraction (A:373-378; U:19-21).
N4 recompute: poisoned old adjudicator never called; registry/alias interval/state/terms equal evaluator; midpoint change→predicate_changes_within_candidate (U:19,25).
N5 fact_drift: fact_id/value→served/prose equal; dangling/altered cannot earn verification (C:119,132-141).
N6 composite_leak: new no composite/min_score; old golden shape+flag; no education/initiation inference/upanayana invented lists (O:58-60).
N7 budget_alias: budget preserves cancellation/locator; catalogs/conventions separate; bookkeeping cannot empty candidate (C:125-128; E/elect.ts:926-941).
N8 scope_drift: forbidden diff/non-ka_* edit/stale generated bytes fail before-after/codegen (M:2948-2951).
N9 false_green: base red/head green; already-green→assessment; missing/skipped/failed CI/DB insufficient (P:146-150,544-551).
N10 stale_receipt: scratch test_ka4b_receipts.py→completion.unmet_evidence; wrong head/missing deploy/contains_merge:false/author verdict refuse (J:94-146; P:381-385).
N11 private_head: unqualified/test-slice refused; out-of-range→no_matching_rows; rollback bytes restored; chart 482012f1-710e-4a25-994a-93821f5871aa sentinel→registry/Vidhi; seven-name regression (L:246-257,476; W/R/views_registry.integration.test.ts:5-188).

Commands: 0/pass; mutants nonzero. Cwd platform:
`ky_rt=src/lib/retrieval/registry/layers; npm test -- "$ky_rt/L3_kala/" "$ky_rt/L0_brahmagyan/__tests__/query_parihara_graph.test.ts"`
Repeat KALA_VIEW_DB_TESTS=1/KY_LANE; DB cases execute. Cwd platform-mcp:
`npm test -- src/tools/kala_views/elect src/tools/kala_views/__tests__/elect_ src/lib/kala_lattice_query src/tools/muhurta_finder`
Root `KY_ITEM=KA-4b bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item`; TESTS newline-delimited platform paths per F/precheck.sh:94-103; MCP separately.
Cwd sidecar: `KALA_REQUIRE_DB=1 python3 -B -m pytest tests/l3/kala_db -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"`; guarded KALA_ADMIN_DSN, skips fail.
Root: `python3 -B -m pytest "$JOB_SCRATCH/test_ka4b_receipts.py" -p no:cacheprovider --basetemp="$JOB_SCRATCH/receipts"`.
Cwd platform: `npm run codegen:capability-estate-census`; `npm run codegen:capability-knowledge -- --generated-at=<reviewed ISO timestamp>`; their `:check` commands exit 0 (platform/package.json:28-31). `npx --no-install tsx scripts/generate_muhurta_undertakings.ts`, repeat `--check` (generator:3,17-22). Real outputs required (L:446).

## 7. Evidence
Frozen template (P:552-553; B4 Q13): base/head/deps/red/digests/tests/mutants/DB/projection/diff. No invented keys.
(I) INTERPRETATION I1: exact-head independent review+successful deployed squash containment still owed; mapping no STEP (P:381-389; M:2966-2968; U:25).

## 8. PR
One “KA-4b: scoped cancellation”; frozen body; controller `ky review KA-4b --detail "PR #<n> @ <40-hex head>"` (P:554-558). Launcher Git; Codex commit_message.

## 9. Do not
No control/FROZEN/executor/schema/evaluator/mapping edits, credentials/production/rebase/force-push. Freeze→STOP; DIRTY generated→REGEN, else launcher main merge (P:530-534,556-558). No BUILD.
