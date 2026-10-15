<!-- Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T211639Z-b4-define-k8-r26/DEFINE_K8-R26.md -->
<!-- Original sha256: 2fc2f0e6758380d41d478a21cd8a3f16c51e284d00777d363db7179f85a30701; date: 2026-10-14 -->
# DEFINE K8-R26 — acceptance study, not campaign acceptance

`KEY:line` means the expanded existing file and 1-based line. Relative paths resolve in the assembly. Prefixes: K=`00_ARCHITECTURE/briefs/kalayantra`; G=`platform/scripts/governance`; J=`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3`; W=`/Users/Dev/kalayantra/wt/k1/00_ARCHITECTURE/briefs/l3_families/measurements`; B=`/Users/Dev/worktrees.noindex/madhav/claude/census-run-rev30/platform/scripts/governance`. External evidence is not an admitted packet pin.

- M = `00_ARCHITECTURE/control/kalayantra/plan_model.json`
- P = `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md`
- R = `K/KALAYANTRA_RELAUNCH_PLAN_v2_7.md`
- C = `G/asset_census.py`
- C30 = `B/asset_census.py`
- N = `G/nikasha_certify.py`
- I = `J/jobs/J-20261012T164123Z-b4-packetplan/ITEMS.json`
- O = `J/jobs/J-20261012T164123Z-b4-packetplan/OPEN_POINTS.md`
- U = `J/engines/lane2/B4_RULINGS.md`
- D = `/Users/Dev/kalayantra/run/K8_GATE_TABLE_R26.md`
- T = `W/K8_GATE_TABLE_R26_v1_0.md`
- X = `W/test_k8_gate_table.py`
- V = `/Users/Dev/kalayantra/run/verdicts/K8-R26.5dfffece9d3ba339f5bfef5a21fdd7aca9dd9985.md`
- L = `/Users/Dev/kalayantra/run/LAUNCH_ACCEPTED.json`
- A = `00_ARCHITECTURE/briefs/l3_families/contracts/SUVARNA_ALIGNMENT_v1_0.md`
- H = `00_ARCHITECTURE/briefs/l3_families/contracts/DASHA_TABLE_CONTRACT_v1_0.md`
- HV = `/Users/Dev/kalayantra/run/verdicts/K0-SV.b66bfbd0a06ccda288843928f603a7aa0dc337ee.v1.cycle31.md`
- S = `00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json`
- F = `K/fleet/schemas/packet.json`
- Q = `K/fleet/kypacket.py`
- RT = `K/fleet/kyroute.py`
- BT = `G/__tests__/test_e5_7_build_completion_produced_set.py`
- CW = `G/__tests__/test_n233_build_history_cert_window.py`
- CF = `B/__tests__/test_n431_empty_slice_conditional.py`
- ROOT = `CLAUDE.md`

## 1. WHAT THE ITEM IS (five lines)
1. K reconciles the architecture plan's registry-25 nine-gate table to main: detector revisions, inputs and possible readings (M:4183–4202; P:299–317).
2. Owned outputs are `/Users/Dev/kalayantra/run/K8_GATE_TABLE_R26.md` and `00_ARCHITECTURE/briefs/l3_families/measurements/K8_GATE_TABLE_R26_v1_0.md` (M:4204–4206).
3. Consumers are subsequent K8 mappings and the native/implementers/Suvarṇa; this awards no asset certification (M:4186; P:25,321; T:26).
4. Dependencies: B-7 launch acceptance (nine bootstrap prerequisites) and K0-SV alignment, which depends on B-7 (M:4188–4191,1250–1259,1899–1901).
5. Model: code/K/`v_exact_head_then_deploy_containment`, `branch_merged` on `origin/kalayantra/k8-r26`; cockpit accepted artifact reconciliation, but fields remain stale (M:4193–4195,4215–4217; O:144–148; U:12).

## 2. DECIDED
Proposed checks; none built here. Representation/review boundary remain Q3.

| Fully decided obligation | Authority | Exact measurement | Real input / fixture |
|---|---|---|---|
| Nine core gates: revisions, inputs, attainable readings. | M:4186; P:305–317; C:129–142 | Extend X:test_exactly_nine_gates_and_all_25_core_criteria: AST-compare criterion multiset, gate, revision, binding. Independently source-review input/reading statements. | P §7; T gate rows; pinned C/C30; X:23–31,54–65. |
| Every row cites the census line actually read. | M:4209 | Parse every criterion locator; compare to the AST dict-call lineno at the declared immutable commit; reject missing/wrong locators and duplicate/omitted criteria. | T:38–46; X:55–65; C:171–216 or selected C30 registry. |
| Every difference lists its introducing revision: produced sets, history, density, source kinds, carriage included. | M:4210 | Compare P §7 with current applicability AND historical code/tests. Extend X:test_difference_table_covers_changed_plan_criteria_and_required_topics with introduction expectations; mutate an introduction to a later revision. | T:48–62; BT:227–229 (produced sets rev4); CW:1–7,165; C:196,197,212–214. |
| Preserve detector ceilings; no invented PASS. | ROOT:135–143; P:305,321 | Reject D2 PASS with binding NONE; distinguish checked N/A; source-review promised releases. Mutate required evidence/verdicts. | C:213; C30:226; X:68–76; N:7–30 (refusal evidence, not ledger-write authority). |
| No runtime changes; writer impacts become NEW ITEM reports; ADHIKĀRIN records supersession KYD. | M:4212–4213 | `git diff --name-only <base> <head>` against ruled scope; review writer-impact/report references and actual KYD binding/order (Q4). | M:4204–4206 outputs; T:133–138; future review/KYD evidence. |
| N-152 dropped the certificate ledger. | M:4202; R:556; A:40 | No ledger output/edit; distinguish legacy refusal semantics from current declarations/builds. | T:28–34; N:2–35; A:40. |
| Artifact acceptance/negative fixtures, no invented feature-red; independent reviewer. | U:12; O:144–148; R:378,382,549–551; F:151–158 | Check fields, negative results, author≠reviewer and accepted digest through typed completion. | Future packet/review receipt; R:385. Model correction pending Q1. |

### Observed evidence and limitations

- Assembly global **27** (C:470); C30 global **30**, provisional, four changed criteria (C30:495,208,212,215–216). Offline byte comparison confirms C30 equals cached `origin/main` source at `1c0b5f154204dcc8a78d33d4c8e52723fdefd991`. No fetch/current-remote claim.
- D points to T v1.2/global29/PR3272, head `86cb61a244db3500a24260b5170486f13b5bc1d1`, open/review due (D:3–14). T/X exist externally; owned tracked table absent here. Cockpit mirroring need not block drafting (U:19).
- X: **59 passed**, against fixed snapshot `3d39fe7ccad5b41c6c2f900d3134d5a5f6eb3ed4`/global29 (X:16,24,46–51). C30 comparison finds stale Vocab.alias 9→10, Narr.checkable 7→8, Null.schema_default/Null.blank_rows 10→11 (T:41–45; C30:208,212,215–216). Snapshot consistency ≠ current reconciliation/acceptance.
- T:61 attributes produced sets to Build.completion rev6; BT:1–7,227–229 dates introduction to **rev4**, service rev5/latest-attempt rev6/unread-log rev7. X:79–90 checks topics/current revisions, not introduction history: M:4210 remains incompletely measured.
- V:5,10–12 rejected snapshot-consistent prose after main's Carr rules changed within the same global revision. Global revision/hash consistency alone cannot establish freshness.

## 3. UNDECIDED — cockpit questions

1. **Which typed completion replaces the code detector, and how is PR3272 disposed?** Artifact treatment is ruled (U:12; O:144–148), but M:4193–4195,4215–4217 still requires merge/deployment; R:726 says refresh-or-close. Options: (a) artifact/digest acceptance, refresh PR solely for documents/oracle; (b) artifact acceptance, close old PR; (c) retain code after explicit scope reconciliation. Recommend **(a)**. Cost: MODEL/receipt wiring and PR disposition; risk: carrying old review forward.

2. **When must the table equal main, and what later change invalidates it?** M:4186/R:519 gives no recheck timing; X:16,46–51 freezes29, C30:495 is30, V:10–12 proves same-version drift. Options: (a) immutable admission-selected main pin, review-time comparison/refusal on semantic changes; (b) approved historical-only29; (c) latest main at every check. Recommend **(a)** using cockpit-confirmed30 or newer. Cost: four updates/conditional-release description (CF:1–9), possible rework; risk: offline cached main needs cockpit confirmation. **(I) INTERPRETATION I1:** admission pin/review invalidation is a proposed conservative policy.

3. **Which semantics must the offline checker prove, and which require independent source review?** M:4186,4210 defines no representation; X:71–107 mostly checks tokens/current revisions. Options: (a) Markdown with source-backed rule/introduction records, negative fixtures and full prose review; (b) new JSON matrix contract; (c) execute census mechanisms on DB. Recommend **(a)**: nine gates/25 criteria, stage/read-model/registrar/service conditionals (P:309–317), introduction evidence, digest-bound review. Cost: ~25 criterion cases plus boundary mutations and source review; risk: lexical checks mislabeled semantic acceptance. **(I) INTERPRETATION I2:** grammar/proof boundary needs ruling; future per-asset certification mappings remain separate (P:321).

4. **Are supersession KYD/writer-impact reports required before acceptance or downstream use?** M:4213/T:137 gives no order, receipt schema or detector. Options: (a) KYD bound to accepted table/source digest and impact disposition before completion; (b) accept first, block downstream use. Recommend **(a)**. Cost: ruling/reports only for real writer impacts; risk: serial delay. **(I) INTERPRETATION I3:** ordering/binding is proposed; cockpit supplies record mechanism/IDs.

## 4. BLOCKED BY

- **Final admission/run:** `/Users/Dev/kalayantra/run/RELEASE_RECEIPT.json` checked absent. R:587–599/F:119–126 requires bound release/final Wave B evidence; U:14 allows drafts. S:7–15 is dated schema, not release. Historical B-7 is dated 2026-10-07/four workers (L:5,22), versus one-worker release (M:1248,1282): no proof of current v3 B-7/final-bundle acceptance (R:595–599). Cockpit supplies typed current completion/release evidence.
- **Admission:** Q1 model/ownership reconciliation and cockpit wave stamping (U:5,12; O:145–146); routing reads model owns (RT:402–407), not a prose override.
- **Final source pins, not drafting:** chosen registry/nikasha and T/X must be integrated/mirrored by cockpit (U:19); Q:379–392 checks local/pinned bytes, Q:245–251 rejects external paths. Sources exist; no DB/L1 rebuild required by this read-only scope (M:4212–4213).
- **K0-SV exists:** A/H acknowledged (H:4,90), historical post-deploy acceptance HV:3–13; squash is cached-main ancestor (check exit0). Revalidate typed prerequisite (R:367–369; M:1920–1929); no missing-agreement or v3-admission claim.

## 5. BUILD SHAPE — if the recommendations are ruled

**(I) INTERPRETATION I4 — proposed scope/size:** extend/mirror X (116 lines); add `fleet/accept/k8_gate_table.py` (~200–350), `fleet/tests/test_accept_k8_gate_table.py` (~250–400), `fleet/tests/fixtures/accept_k8_r26/` snapshot/table (~100–200), relative to K. Proposed additions require owns extension; no existing interface claimed. Keep R26 names, record actual revision (T:21–25).

AST/source-byte checks, no census import/run. Mutations: omission/duplication, wrong locator/revision/binding/introduction, missing rule evidence, same-version stale snapshot, D2 PASS, wrong digest/reviewer, runtime path. Semantic fixtures/source review replace keyword claims (ROOT:135–143; X:71–107; BT:227–229); CF:1–9 supplies offline conditional boundaries, CW:6–7 separates pure/DB checks.

Sandbox: bounded read-only Git for blob/ref/diff evidence (X:19–24; Q:228–243); no DB, network, ephemeris or production. Reuse Wave B **kypacket.py** admission and **kyroute.py** scope routing (Q:2–12,372–392; RT:4–9,395–428), using independently reviewed installed heads (R:714–715). Neither replaces semantic review; future packet scopes precheck (R:549–551).

## 6. READINESS
**BLOCKED** for admission/run: release/current B-7 evidence, typed model/wave reconciliation, final source integration; draft can proceed after Q1–Q4 (U:5,12,14,19). Study completion does not complete K8-R26.
