```json
{"id":"K4-2aw","kind":"artifact","wave":0,"build_tier":"opus","routing_reason":"Inherited head/squash assessment; no rebuild (plan §14).","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"420-424;509-563;720-726","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md","revision":"1.0","section_range":"17-60","sha256":"99c7156dd93a50febb45fd7d265d2fbef4b4ee733de1e94301a2b9e18b00216d"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"0a606fd0fa68efd7d197c2bacb75c1210a61e05f98db8db8bd81059a32823e75","semantic_acceptance":"Independent head acceptance, squash mapping, required CI, deployed containment, semantic schema/registry readback, ordered dependencies and preserved scope; admission is not completion.","negative_fixtures":["Ancestry without reviewed-patch proof.","REFUSED/empty/wrong-head readback; absent/skipped/red CI.","Fixture acceptance relabelled live, issued or certified."]}
```
# K4-2aw v1 — inherited acceptance
Version1.0; status: preparation; changelog: T0 work order.
Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2aw.956a250197e437e7a43d41bb6e5260bf9ab6cd82.md. Code: `git show M:<path>`.
## 1. Immutable pins / prerequisites
PR#3385; H=956a250197e437e7a43d41bb6e5260bf9ab6cd82; M=67afae086018d53abcd2248f54f08a15baf7aeb2; squash parent B=268d0273506161fd85c47095bff10ece7148e3db; V-head=956a250197e437e7a43d41bb6e5260bf9ab6cd82 (E:12361;12397;12546; V:1-5). Verify parent/effective H→M patch mapping; unproven difference needs review.
Release SUVARNA-L0L2-CLOSE-REV30-20261013, RUN/RELEASE_RECEIPT.json. SR(R:8-12) lacks1350/current slot: measured schema/ledger/registry/SQL slot required; missing blocks.
Dependencies K0a-4, K4-2a guarded-complete with head/squash/artifact proof. Wave0 order K4-2a→K4-2aw→K4-2b→K4-3 (P:722-725). Consumers K4-2b wait on completion.
## 2. Owns / allowed classes
Read PR diff/code/tests/DDL/inventories/evidence. Write only $JOB_SCRATCH/inspection.json/logs/caches/mutations. Reviewer≠author; F/FROZEN_PATHS.txt required. Findings→cockpit REWORK; no source/control/Git writes.
## 3. Spec excerpt / reconciliation
P revision2.7, hash in front matter, lines420-423:
```excerpt
**Inheritance predicate (one implementation, used by dispatcher and tracker):** bind old
head, new head, their exact base commits and a comparison of the reviewed patch;
ancestry alone is insufficient; any substantive resolution or unproven difference
requires review of the new head. Applied to every inherited Wave 0 head. After every
```
Reconciliation: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md` §8/§14: assess inherited work. A:26-45 removes owner-waits/veto/human-click; surrogate decides windows, fleet merges ACCEPTED/green CI; hard stops remain. PRs already merged.
## 4. Contract / COCKPIT RULING T0 (proposed by job)
1. (I) INTERPRETATION I1: artifact-kind assessment for existing code item; cockpit binds ARTIFACT role, retains code completion semantics; no invented red (P:544-550; F/schemas/packet.json semantic_acceptance).
2. V:3/E:12361,12397 bind ACCEPTED to H. H→M tree diff adds two K8_GATE_TABLE_R26 measurement files; reviewer must prove main inheritance/patch mapping, not waive it. Recheck latest verdict. V:10-17:164 passes/39SQL/18mutants plus isolated verifier-role/FIX5 repair.
3. (I) INTERPRETATION I2: accept only merged fixture/preparation scope; live bindings/qualification/issuance/retirement remain deferred (V; CLAUDE.md §N.5/7/8).
4. Completion needs acceptance/CI/squash/deploy/readback/dependencies. Claim-expiry audit is not acceptance (RUN/AUDIT_RECONCILIATION.json:145-178; P:420-424,544-555).
5. No owner-class decision here; doctrine/deletion/restore/FROZEN change→exact cockpit question (A:38-45).

Verify fixture writer only. `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` @ squash:1172-1196 retains default legacy delegation and class substeps; `services/ka_sangam/jury/candidate.py` under Y @ squash:188-204,229-261 binds ctx.build_id/chart/generation, requires building + conventions.fixture=true, rejects published head, validates before child-first class replacement, records acceptance_scope=fixture_only and separate null estimands. Uses ctx.db_conn, never commit/close/asset_throughput. Test harness role repair is evidence, not permission to grant production access. Live G-J bindings and publication remain unadmitted.
## 5. Migration / operation metadata
Inherited implementation: brief.migration=null; brief.op=null. Acceptance job writes_data=false; migration_class=null; window_batch_id=null. Runtime writer is data-writing, so consume independent post-deploy readback of its inherited 1350 prerequisite and registry; no new migration (E:12546).
1350 readback NOT PROVEN: RUN/ops/receipts/v3-c292-k4-2a-1350.json:2-13=REFUSED/v3/exit null (2026-10-13T11:38:38Z), SHA256=6717711d7f4b5033bf193a6c3f9ed9ae6c1d40d9de7d29b0755fe0cf590157fc. No completed1350 receipt found; other migrations do not count. Cockpit reconciles request, obtains authorised credential-free readback. Require request/id/item/M/receipt/output hashes, COMPLETED exit0, nonempty filename+SHA/applied_at ledger row, catalogue PK/FK/null constraints, registry/count_sql and legacy/published preservation; independent semantic review at M. Empty exit0 is not application proof.
## 6. Acceptance / negatives
Historical V SHA256=38338c40ae1aa40d2e8e73fa16eb61793b210427047fb651a41ce9192488cb64; retain base-red/mutations/scope. Preparation has not run implementation tests/CI.
Tests RUN/tests/K4-2aw.txt:1-2, SHA256=3a930e0fbede49fa8efe3c14e6c2c9a9b5ca21610ae97106dc3ceab293d128e2; Y expands above:
- Y/tests/l3/ka_sangam
- Y/tests/l3/kala_db/ka_sangam
Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2aw.txt`. Also Y/tests/test_fix_plan_proofs.py FIX5; retain full jury coverage.
`KY_ITEM=K4-2aw bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
Focus: Class substeps, idempotent resume/plan, wrong chart/build/generation/state/fixture/published refusal; child-first partition replacement; zero dry-run writes; legacy delegation/enrichment; transactional test roles leave no survivors.
Negatives: stale/rejected/wrong H/base/M, unproven patch, CI skip, absent/REFUSED readback, wrong chart/build/generation, fixture-as-live, fake qualification, unscoped deletion: refuse/named unavailable.
## 7. Evidence / deployment
inspection.json: item/job/reviewer, hashes/H/V-head/bases/M/patch/latest verdict/phase, dependencies/schema/slot, commands/logs/negatives/scope/deferred steps, CI run/H/results, deploy actual SHA/time/ancestry, request/receipt/output hashes/readback, before/after HEAD/status/tracked hashes, I1/I2/findings.
E:13985: K7-2 successful deploy run38311508214, actual SHA07230af11190b652ac29dcc4ff47f213cb85fca6, 2026-10-12T21:34:48Z. Job `GIT_OPTIONAL_LOCKS=0 git merge-base --is-ancestor M 07230af11190b652ac29dcc4ff47f213cb85fca6`: exit0. Later containment≠1350 application. Verifier rechecks; post_deploy verdict at M, not workflow head_sha (F/cards/PARIKSAKA.md PA-10).
## 8. Existing PR / controller handoff
Return PR#3385 @ H/evidence digest; controller registers/publishes verdicts/completion. U/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:75: tests_and_verdict for named steps; deferred stay open. Mismatch→cockpit, no ledger edit.
## 9. Do not
No rebuild/reallocate/reapply/production/credentials/computation/live fixture bypass/doctrine/deletion/FROZEN/control/generated/Git writes/own acceptance/duplicate request/DONE from merge. Global HOLD stops. RUN/HANDOVER_STATE_20261013T0526Z.md:1-12 is historical v2; A governs now.
Notes: (I) INTERPRETATION: fixtures/SQL/readback; no chart MCP (this packet:25,29,32,35-40).
