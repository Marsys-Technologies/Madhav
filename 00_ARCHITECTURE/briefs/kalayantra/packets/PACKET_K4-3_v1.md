```json
{"id":"K4-3","kind":"artifact","wave":0,"build_tier":"opus","routing_reason":"Inherited head/squash assessment; no rebuild (plan §14).","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"420-424;509-563;720-726","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md","revision":"1.0","section_range":"17-60","sha256":"99c7156dd93a50febb45fd7d265d2fbef4b4ee733de1e94301a2b9e18b00216d"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"5c5705f3b52dc61d3f3c103bdd53826a63ccdbb558775629552c9b3af302ad9c","semantic_acceptance":"Independent head acceptance, squash mapping, required CI, deployed containment, semantic schema/registry readback, ordered dependencies and preserved scope; admission is not completion.","negative_fixtures":["Ancestry without reviewed-patch proof.","REFUSED/empty/wrong-head readback; absent/skipped/red CI.","Fixture acceptance relabelled live, issued or certified."]}
```
# K4-3 v1 — inherited acceptance
Version1.0; status: preparation; changelog: T0 work order.
Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-3.912efb617ffe9b7e33af5a3a3c22045a74bbd2be.md. Code: `git show M:<path>`.
## 1. Immutable pins / prerequisites
PR#3393; H=ee773b5383850067a5658ccafa42fd2488e6f344; M=4e34e2a1f6d660ce17b43a3fb3ad29519d378a60; squash parent B=4a7bd85ef22b5271fa318eb18feab30cd2e439b1; V-head=912efb617ffe9b7e33af5a3a3c22045a74bbd2be (E:12389;12853; V:1-5). Verify parent/effective H→M patch mapping; unproven difference needs review.
Release SUVARNA-L0L2-CLOSE-REV30-20261013, RUN/RELEASE_RECEIPT.json. SR(R:8-12) lacks1350/current slot: measured schema/ledger/registry/SQL slot required; missing blocks.
Dependencies K4-2b guarded-complete with head/squash/artifact proof. Wave0 order K4-2a→K4-2aw→K4-2b→K4-3 (P:722-725). Consumers V-K4, K5-G1a, K6-5a, K6-123, K8-REG wait on completion.
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
2. Shared predicate returned inherits=false/reason=patch_differs, derived old_base=09be23702659752b3bc5c5309701df0e68fd29f2 and new_base=the squash parent above. V:3 records its original stacked base b52697e4e23bbfcb8bdee39bc490b8aefe93b72f. Fresh independent review at registered head required; E:12853 itself retracts earlier acceptance retention. Historical V:11-17 retains 192 tests/22 SQL and 3 attachment mutants; 11 stale mapping-pin mutants detected.
3. (I) INTERPRETATION I2: accept only merged fixture/preparation scope; live bindings/qualification/issuance/retirement remain deferred (V; CLAUDE.md §N.5/7/8).
4. Completion needs acceptance/CI/squash/deploy/readback/dependencies. Claim-expiry audit is not acceptance (RUN/AUDIT_RECONCILIATION.json:145-178; P:420-424,544-555).
5. No owner-class decision here; doctrine/deletion/restore/FROZEN change→exact cockpit question (A:38-45).

Verify canonical reading attachment without changing agreement or issuing forecasts. `services/kala_core/assertion/attachment.py` under Y @ squash:1-5,21-41 defines class/phase/affected_person/episode identity and explicit F1-supplied refs; `services/ka_sangam/jury/candidate.py` @ squash:193-202,257-261 stores attachment report separately from measured agreement. Duplicate signals/assertions/events credit once; conflicts refuse; unmatched/nonobservable reading claims retain reasons. Certification mapping/declaration must match independently measured registry pins; historical rev29 fixture mapping is not rev30/live certification (V:7-15; release pin). No silent relabelling or production certificate.
## 5. Migration / operation metadata
Inherited implementation: brief.migration=null; brief.op=null; migration_class=null; window_batch_id=null. Acceptance job writes_data=false. Candidate attachment persistence depends on independently verified 1350 schema and writer readback; no allocation or publication.
1350 readback NOT PROVEN: RUN/ops/receipts/v3-c292-k4-2a-1350.json:2-13=REFUSED/v3/exit null (2026-10-13T11:38:38Z), SHA256=6717711d7f4b5033bf193a6c3f9ed9ae6c1d40d9de7d29b0755fe0cf590157fc. No completed1350 receipt found; other migrations do not count. Cockpit reconciles request, obtains authorised credential-free readback. Require request/id/item/M/receipt/output hashes, COMPLETED exit0, nonempty filename+SHA/applied_at ledger row, catalogue PK/FK/null constraints, registry/count_sql and legacy/published preservation; independent semantic review at M. Empty exit0 is not application proof.
## 6. Acceptance / negatives
Historical V SHA256=4743ed0120f0812c67851f64ae0aa3499b82aed3a765fb1b618fa4f586610a40; retain base-red/mutations/scope. Preparation has not run implementation tests/CI.
Tests RUN/tests/K4-3.txt:1-2, SHA256=9057008b0aed7674cb179821da799a5da3ac507a21c50d6df282fed2976519b8; Y expands above:
- Y/tests/l3/ka_sangam
- Y/tests/l3/kala_db/ka_sangam/test_jury_candidate_end_to_end.py
Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-3.txt`. 
`KY_ITEM=K4-3 bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
Focus: Canonical class/phase/person/episode identity, duplicates once, conflict rejection and unmatched reasons; attachment leaves D(W) byte/value unchanged; mapping AST/pin mutants and readback roundtrip; inherited verifier-role fixture; only ka_sangam declaration changed.
Negatives: stale/rejected/wrong H/base/M, unproven patch, CI skip, absent/REFUSED readback, wrong chart/build/generation, fixture-as-live, fake qualification, unscoped deletion: refuse/named unavailable.
## 7. Evidence / deployment
inspection.json: item/job/reviewer, hashes/H/V-head/bases/M/patch/latest verdict/phase, dependencies/schema/slot, commands/logs/negatives/scope/deferred steps, CI run/H/results, deploy actual SHA/time/ancestry, request/receipt/output hashes/readback, before/after HEAD/status/tracked hashes, I1/I2/findings.
E:13985: K7-2 successful deploy run38311508214, actual SHA07230af11190b652ac29dcc4ff47f213cb85fca6, 2026-10-12T21:34:48Z. Job `GIT_OPTIONAL_LOCKS=0 git merge-base --is-ancestor M 07230af11190b652ac29dcc4ff47f213cb85fca6`: exit0. Later containment≠1350 application. Verifier rechecks; post_deploy verdict at M, not workflow head_sha (F/cards/PARIKSAKA.md PA-10).
## 8. Existing PR / controller handoff
Return PR#3393 @ H/evidence digest; controller registers/publishes verdicts/completion. U/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:75: tests_and_verdict for named steps; deferred stay open. Mismatch→cockpit, no ledger edit.
## 9. Do not
No rebuild/reallocate/reapply/production/credentials/computation/live fixture bypass/doctrine/deletion/FROZEN/control/generated/Git writes/own acceptance/duplicate request/DONE from merge. Global HOLD stops. RUN/HANDOVER_STATE_20261013T0526Z.md:1-12 is historical v2; A governs now.
Notes: (I) INTERPRETATION: fixtures/SQL/readback; no chart MCP (this packet:25,29,32,35-40).
