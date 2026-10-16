```json
{"id":"KA-3b","kind":"artifact","wave":1,"build_tier":"opus","routing_reason":"Scope/ownership reconciliation; independent wiring; parent join.","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"509-560;728-730","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/control/kalayantra/plan_model.json","revision":"snapshot","section_range":"986;2077-2080;3484-3539;5515-5538","sha256":"2743c5a0c70022c5de90ac8acc1984df4a242e364673b742964d8dc79cfabd3b"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md","revision":"1.1","section_range":"169;173;207","sha256":"85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef"},{"path":"00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md","revision":"1.1","section_range":"281-356","sha256":"d39d4eb02c62dbde2e639f0329fddea9da2c3968704279cd1273d6dea7a14e91"},{"path":"platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py","revision":"snapshot","section_range":"126-130;1535-1557","sha256":"07367ebba21b2bfa3ff08d9b849955dd31f3292f1689a68f6d31bfbfc78eb7d4"},{"path":"platform/python-sidecar/services/gochara_rules/vedha_derive.py","revision":"snapshot","section_range":"207-277;298-363","sha256":"68efc2243a5805d6c65456a74eeb8b9232986957e56e941324867c916b2fe720"},{"path":"platform/python-sidecar/services/gochara_kernel/window_sweep.py","revision":"snapshot","section_range":"286-294","sha256":"e7b9113ca7d52272e347f08485f93247e1a9a269c37ba231d6ff0bfa5cefcc22"},{"path":"platform/python-sidecar/services/gochara_kernel/window_verifier.py","revision":"snapshot","section_range":"62-68","sha256":"edee01df55ee32bfd27d46c8360ba7157c03657aeb4e745c030169b3852857b3"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"90a302975f9875098dce10a7a8340c6d2fde772268544a17f4b2ac03176a8aaf","semantic_acceptance":"Unclaimable join retains four families and wiring; all required independently accepted children DONE; complete obligation/ownership correspondence.","negative_fixtures":["missing family/wiring","lost edge","overlap/cycle","unreviewed child","premature join","flag-only wiring","legacy mutation"]}
```
# KA-3b v1 · PREPARATION
v1.2; status: preparation; changelog: repin current sources/citations (PBKNB-N1).
## 1. Immutable pins / gates
P/M/C/A/W/D/B/V=spec_sources[0..7].path; Y=platform/python-sidecar; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md; R=S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md. 1-based lines.
Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,18; revision 30 from cockpit. Wave 1=P:728-730 preparation. Children repin schema/accepted heads/squash mappings. Keep D-R8/J-0m/KA-3a (M:3489-3493).
T0 (proposed):
1. Keep KA-3b's four families/downstream ID and mandatory preclaim split/join (M:3487,3533).
2. R:84's “KA-3b (judge wiring)” prioritises a wiring child after KA-3a; it does not replace the four-adapter parent (U:63; study:79,98).
3. S registers actual children/waits; reuse J-0m's exact-scope judge child if present, else S allocates; no ID allocated here (M:5515-5538).
4. Production consumes KA-3a through overlays; D remains independent semantic verification (C:169,173,207; W:130,1538).
5. Missing/unqualified inputs unavailable; publication stays legacy; children earn completion (B:286-294; U:63; M:3532-3533; CLAUDE.md:119,132-141).
(I) INTERPRETATION I1: add wiring dependency; artifact kind describes aggregate evidence. S replaces obsolete branch_merged/code with join=true/done_by=join (M:2077-2080). Never claim/BUILD/manual-done parent; admission grants no registration authority.
study=S/jobs/J-20261012T184241Z-b4-define-ka-3a/DEFINE_KA-3a.md.
## 2. Owns / allowed classes
Parent: inspection only; S registers within scope; retain downstream edges.
Child floor M:3506-3525: f=moorti_nirnaya|kota_chakra|tithi_pravesha|sudarshana_varsha; Y/services/ka_f/**, Y/pipeline/orchestrator/writers/ka_f.py, Y/tests/l3/ka_adapters/**. One family/child; separate schema/protocol from runtime qualification (M:3533). S allocates tests/migrations and serialized inventory/census custody.
Wiring floor: W; Y/services/gochara_kernel/{window_sweep,record_store,window_verifier}.py; Y/tests/l3/gochara/**. Steward/J custody; no K grant. KA-3a provider read-only; S registers bounded export/generated custody and J-0d waits. No control/FROZEN/foreign edit.
## 3. Excerpt / reconciliation
C:207:
```excerpt
Adapters (`ka_vedha_gochara`, `ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`, `ka_sudarshana_varsha`) keep their writers and tables at level 1 (as today) and gain `method_qualification`, `coverage` and `upstream_fingerprint` columns where missing; the judge consumes them through `kala_core.overlays`.
```
Reconciliation: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md` §8/§14: bounded children/receipts/compatibility; R:84 prioritises wiring without losing families/widening K custody.
## 4. Contract
M:3534 existing columns; children bind exact candidate schema/keys/types, never infer from legacy DATE/JSON.
A:305-356: mūrti moorti_nakshatra_27/uncited_legacy, same-instant ingress/Moon, testimony only; kota uncited_extension ring occupancy/shared nature/null direction; tithi moon_longitude_return/uncited_legacy, no uncited phase variant, NOW/AHEAD same coverage; sudarshana adapter frames/conventions, no tri_lagna_convergence judgment or judge enrichment.
W:130/1538 unbound; B:286-294 scalar. D:298-363: factor/applicable/results/boundaries/scopes; results state/value/reasons/qualification/scope/obstructors/unknown_obstructors/t_in/t_out. Wire interior edges/metadata/persistent judge records; flag-only binding fails (V:62-68).
(I) INTERPRETATION I2: KA-3a provider retains structured result; scalar bridge extracts declared value at t, retains metadata/edges. Support/chart/generation/frame/fingerprint/factor ref agree; wrong identity refuses, gaps reasoned null. Verifier never imports production semantics.
## 5. Metadata
brief.migration=null; brief.op=null; writes_data=false; migration_class=null; window_batch_id=null. Child metadata follows scope; routine columns≠table/re-key permission (M:3535). Protected SQL uses platform/scripts/kala_protected_migrations.txt; no migrate.ts/deploy.yml edit (P:535-540).
## 6. Acceptance
Crosswalk covers four families/wiring/all original obligations. Every required child DONE with exact-head ACCEPTED/merge mapping/required readback; skips do not count. Existing join semantics (M:986,2077-2080), no new detector/parent red. Child packets pin red/base/tests (P:544-551).
Checker platform/scripts/governance/pravaha_tracker/server.py:374: check_model(candidate_model)==[]; reviewer checks correspondence. KY_ITEM=KA-3b bash "$KY_FLEET/precheck.sh" --item checks descriptor, never launches join.
Reject: missing/duplicate family or wiring; lost original edge; overlap/cycle; unreviewed head; premature join; flag-only wiring; legacy mutation.
Wiring: active=0/inactive=1+Moon scope/unqualified=null; reasons obstructor_residence_unknown/node_obstruction_undecided/node_residence_unknown (D:263-273); cited precedence; half-open edges/interior island; ref/support/coverage/fingerprint/persistent evidence. Wrong chart/generation, missing provider/edges and shared-verifier mutants fail. K3 keeps judge_vedha_rows_absent until eligible rows (U:63); fixture≠live wiring.
Families prove A:305-356/M:3524-3529 oracles, overlays-only consumers, candidate idempotency/legacy byte preservation. Disclose mūrti epoch correction, never false equality. Child packets pin commands/fixtures; CI/Kāla DB Tests/mutants required.
## 7. Evidence
[KN-B bundle](../evidence/KN_B_PREBUILD_v1.json) sha256=8863f23030e0b51d68b80d67a20e1f51cb8bbc9e0227e4878100cc19f3988952; pins paths/digests. Original result/interpretations/receipts absent; 8 review mutants≠builder/exhaustive proof. [Reconciliation](../evidence/KN_B_PREBUILD_v1.md) retains crosswalk/IDs/heads/review+merge/readback/digests/gaps/I1/I2 and five-child/edge/join gates; no parent/live completion.
## 8. Review/PR
No parent PR. Child: scope/contract/compatibility/red/mutants/schema/deploy; ky review <actual-child-id> --detail "PR #<n> @ <40-hex head>". S registers split; author≠reviewer.
## 9. Do not
No invented ID/interface/chart/doctrine, scope loss, numeric testimony/serving flip, credential/network/production/Git/control/FROZEN writes, rebase/force-push. Children pin/read fleet/FROZEN_PATHS.txt; missing contract/custody refuses. Admission≠acceptance. Retain evidence/worktree.
