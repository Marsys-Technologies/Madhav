```json
{"id":"KA-3b","kind":"artifact","wave":1,"build_tier":"opus","routing_reason":"Scope/ownership reconciliation; independent wiring; parent join.","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"509-560;728-730","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/control/kalayantra/plan_model.json","revision":"snapshot","section_range":"1696-1699;2819-2879;4444-4467","sha256":"64c6b291670cea2226e322d804fbf238980ae2864d19f34e6a1a05229f231edf"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md","revision":"1.1","section_range":"169;173;207","sha256":"85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md","revision":"1.1","section_range":"281-356","sha256":"ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569"},{"path":"platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py","revision":"snapshot","section_range":"120-124;1255-1278","sha256":"0b5a5433fdb755c3599c28ddee274b2d152bb3334c6042ad87f3c749420fafa5"},{"path":"platform/python-sidecar/services/gochara_rules/vedha_derive.py","revision":"snapshot","section_range":"207-277;298-363","sha256":"68efc2243a5805d6c65456a74eeb8b9232986957e56e941324867c916b2fe720"},{"path":"platform/python-sidecar/services/gochara_kernel/window_sweep.py","revision":"snapshot","section_range":"286-294","sha256":"e7b9113ca7d52272e347f08485f93247e1a9a269c37ba231d6ff0bfa5cefcc22"},{"path":"platform/python-sidecar/services/gochara_kernel/window_verifier.py","revision":"snapshot","section_range":"62-68","sha256":"edee01df55ee32bfd27d46c8360ba7157c03657aeb4e745c030169b3852857b3"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"c8833225358fd4caeeb53f86758f42248bfff5795eab1b0f98dd27cefeaf23fd","semantic_acceptance":"Unclaimable join retains four families and wiring; all required independently accepted children DONE; complete obligation/ownership correspondence.","negative_fixtures":["missing family/wiring","lost edge","overlap/cycle","unreviewed child","premature join","flag-only wiring","legacy mutation"]}
```
# KA-3b v1 · READY FOR ADMISSION
v1.0; status: preparation; changelog: initial ruling/join.
## 1. Immutable pins / gates
P/M/C/A/W/D/B/V=spec_sources[0..7].path; Y=platform/python-sidecar; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md; R=S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md. Lines 1-based.
Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,18; revision 30 from cockpit. Wave 1=P:728-730 preparation. Historical SR v2.2; children need current schema/accepted heads/squash mappings. Keep D-R8/J-0m/KA-3a (M:2824-2828).
COCKPIT RULING T0 (proposed by job):
1. Keep KA-3b's four families/downstream ID and mandatory preclaim split/join (M:2822,2868).
2. R:84's “KA-3b (judge wiring)” prioritises a wiring child after KA-3a; it does not replace the four-adapter parent (U:63; study:79,98).
3. S registers actual children/waits; reuse J-0m's exact-scope judge child if present, else S allocates; no ID allocated here (M:4447-4467).
4. Production consumes KA-3a through overlays; D remains independent semantic verification (C:169,173,207; W:124,1259).
5. Missing/unqualified inputs stay unavailable; publication stays legacy; all children must earn completion (B:286-294; U:63; M:2865,2868; CLAUDE.md:119,132-141).
(I) INTERPRETATION I1: add wiring dependency; artifact kind describes aggregate evidence. S replaces obsolete branch_merged/code with join=true/done_by=join (M:1696-1699). Never claim/BUILD/manual-done parent; admission grants no registration authority.
DEFINE_KA-3b.md absent. study=S/jobs/J-20261012T184241Z-b4-define-ka-3a/DEFINE_KA-3a.md.
## 2. Owns / allowed classes
Parent: scratch inspection only. S registers declarations under its governed scope; original downstream KA-3b edges stay.
Child floor M:2839-2858: f=moorti_nirnaya|kota_chakra|tithi_pravesha|sudarshana_varsha; Y/services/ka_f/**, Y/pipeline/orchestrator/writers/ka_f.py, Y/tests/l3/ka_adapters/**. One family per child; separate schema/protocol from runtime qualification (M:2868). S allocates exact tests/migrations and serialized generated inventory/census custody.
Wiring floor: W; Y/services/gochara_kernel/{window_sweep,record_store,window_verifier}.py; Y/tests/l3/gochara/**. Steward/J paths, no K grant (M:1655-1656). KA-3a provider read-only; S registers bounded export/generated custody and J-0d waits. No control/FROZEN/foreign edit.
## 3. Excerpt / reconciliation
C:207:
```excerpt
Adapters (`ka_vedha_gochara`, `ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`) keep their writers and tables at level 1 (as today) and gain `method_qualification`, `coverage` and `upstream_fingerprint` columns where missing; the judge consumes them through `kala_core.overlays`.
```
Reconciliation: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md` §8/§14: bounded children/receipts/compatibility; R:84 prioritises wiring without losing families/widening K custody.
## 4. Contract
M:2870 existing columns; children bind exact candidate schema/keys/types, never infer from legacy DATE/JSON.
A:305-356: mūrti moorti_nakshatra_27/uncited_legacy, same-instant ingress/Moon, testimony only; kota uncited_extension ring occupancy/shared nature/null direction; tithi moon_longitude_return/uncited_legacy, no uncited phase variant, NOW/AHEAD same coverage; sudarshana adapter frames/conventions, no tri_lagna_convergence judgment or judge enrichment.
W:124/1259 unbound; B:286-294 scalar. D:298-363: factor/applicable/results/boundaries/scopes; results state/value/reasons/qualification/scope/obstructors/unknown_obstructors/t_in/t_out. Wire interior edges/metadata/persistent judge records; flag-only binding fails (V:62-68).
(I) INTERPRETATION I2: KA-3a provider retains structured result; scalar bridge extracts declared value at t, retains metadata/edges. Support/chart/generation/frame/fingerprint/factor ref agree; wrong identity refuses, gaps reasoned null. Verifier never imports production semantics. No provider signature/table invented.
## 5. Metadata
brief.migration=null; brief.op=null; writes_data=false; migration_class=null; window_batch_id=null. Child metadata follows scope; routine columns≠table/re-key permission (M:2871). Protected SQL uses platform/scripts/kala_protected_migrations.txt; no migrate.ts/deploy.yml edit (P:535-540).
## 6. Acceptance
Crosswalk covers four families/wiring/all original obligations. Every required child DONE with exact-head ACCEPTED/merge mapping/required readback; skips do not count. Existing join semantics (M:750,1696-1699), no new detector/parent red. Child packets pin observed red/base/tests (P:544-551).
Registration checker platform/scripts/governance/pravaha_tracker/server.py:269-315: check_model(candidate_model)==[]; reviewer checks correspondence. KY_ITEM=KA-3b bash "$KY_FLEET/precheck.sh" --item checks descriptor, never launches join.
Reject: missing/duplicate family or wiring; lost original edge; overlap/cycle; unreviewed head; premature join; flag-only wiring; legacy mutation.
Wiring: active=0/inactive=1+Moon scope/unqualified=null; reasons obstructor_residence_unknown/node_obstruction_undecided/node_residence_unknown (D:263-273); cited precedence; half-open edges/interior island; ref/support/coverage/fingerprint/persistent evidence. Wrong chart/generation, missing provider/edges and shared-verifier mutants fail. K3 keeps judge_vedha_rows_absent until eligible rows (U:63); fixture≠live wiring.
Families prove A:305-356/M:2859-2864 oracles, overlays-only consumers, candidate idempotency/legacy byte preservation. Disclose mūrti epoch correction, never false equality. Child packets pin commands/fixtures; CI/Kāla DB Tests/mutants required.
## 7. Evidence
Accepted inspection.json template: crosswalk/actual child IDs/head/receipt/digest/review refs; model diff; negatives/gaps; I1/I2. No new parent artifact/production request; report never substitutes for children.
## 8. Review / PR
No parent PR. Child PR: scope/contract/compatibility/red/mutants/schema/deploy; ky review <actual-child-id> --detail "PR #<n> @ <40-hex head>". S registers reviewed split; author≠reviewer.
## 9. Do not
No invented ID/interface/chart/doctrine, scope loss, numeric testimony/serving flip, credentials/network/production/Git/control/FROZEN writes, rebase/force-push. Children pin/read fleet/FROZEN_PATHS.txt; missing contract/custody blocks. Admission≠acceptance. Worktree/evidence retained.
