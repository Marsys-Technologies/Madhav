```json
{"id":"K4-2b","kind":"artifact","wave":0,"build_tier":"opus","routing_reason":"Inherited head/squash assessment; no rebuild (plan §14).","needs_chart_data":false,"max_loops":3,"plan_version":"2.7","spec_sources":[{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"2.7","section_range":"420-424;509-563;720-726","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md","revision":"1.0","section_range":"17-60","sha256":"99c7156dd93a50febb45fd7d265d2fbef4b4ee733de1e94301a2b9e18b00216d"}],"schema_receipt_id":"SR-20261009T200542Z-a9d843652016","pw_mechanism_version":"1.0","release_pins":{"dash_build":"ca17639b-f3cf-42c7-9866-0a61f3855802","registry_revision":30},"packet_sha256":"2b7ee21424528e823a0a5e869842196fd7c87f044542aacd163d3f4fdf5544a3","semantic_acceptance":"Independent head acceptance, squash mapping, required CI, deployed containment, semantic schema/registry readback, ordered dependencies and preserved scope; admission is not completion.","negative_fixtures":["Ancestry without reviewed-patch proof.","REFUSED/empty/wrong-head readback; absent/skipped/red CI.","Fixture acceptance relabelled live, issued or certified."]}
```
# K4-2b v1 — inherited acceptance
Version1.0; status: preparation; changelog: T0 work order.
Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2b.c3c16d1c4cadbe882f973abf7f3f4ed1d72715d0.md. Code: `git show M:<path>`.
## 1. Immutable pins / prerequisites
PR#3390; H=c3c16d1c4cadbe882f973abf7f3f4ed1d72715d0; M=4a7bd85ef22b5271fa318eb18feab30cd2e439b1; squash parent B=0ea26647d11d562117f8b2aeacf87540b4f17f68; V-head=c3c16d1c4cadbe882f973abf7f3f4ed1d72715d0 (E:12428;12665;13073; V:1-5). Verify parent/effective H→M patch mapping; unproven difference needs review.
Release SUVARNA-L0L2-CLOSE-REV30-20261013, RUN/RELEASE_RECEIPT.json. SR(R:8-12) lacks1350/current slot: measured schema/ledger/registry/SQL slot required; missing blocks.
Dependencies K4-2aw guarded-complete with head/squash/artifact proof. Wave0 order K4-2a→K4-2aw→K4-2b→K4-3 (P:722-725). Consumers K4-3 and K7-4 wait on completion.
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
2. V:1-9/E:12665 bind ACCEPTED to H:440 tests/62SQL plus2 declaration pins. H→M whole trees differ on50 paths: independently prove main inheritance/scoped patch mapping; no waiver. E:13073 refuses completion on K4-2aw, not reader rebuild. Recheck latest verdict.
3. (I) INTERPRETATION I2: accept only merged fixture/preparation scope; live bindings/qualification/issuance/retirement remain deferred (V; CLAUDE.md §N.5/7/8).
4. Completion needs acceptance/CI/squash/deploy/readback/dependencies. Claim-expiry audit is not acceptance (RUN/AUDIT_RECONCILIATION.json:145-178; P:420-424,544-555).
5. No owner-class decision here; doctrine/deletion/restore/FROZEN change→exact cockpit question (A:38-45).

Verify preparation readers, retaining signed D(W), witness signature and separate null estimands. `services/ka_sangam/jury/reader.py` under Y @ squash:18-21,24-84,100-139 binds SELECT by chart/generation/build, defaults to kala_convergence, never unions/falls back, requires private fixture and refuses published head. convergence_id/signal_id/peak_date/issuance_identity stay null with stage_to_reader_mapping_unadmitted; preparation returns zero writes. V:13-15 explicitly defers live admission/mapping, mode retirement/deletion and K9-4b cutover. Those are not closed by acceptance of the inherited preparation implementation.
## 5. Migration / operation metadata
Inherited implementation and acceptance job: brief.migration=null; brief.op=null; writes_data=false; migration_class=null; window_batch_id=null (E:13073). Consume K4-2a verified 1350 schema and K4-2aw post-deploy evidence; do not manufacture an own migration request.
1350 readback NOT PROVEN: RUN/ops/receipts/v3-c292-k4-2a-1350.json:2-13=REFUSED/v3/exit null (2026-10-13T11:38:38Z), SHA256=6717711d7f4b5033bf193a6c3f9ed9ae6c1d40d9de7d29b0755fe0cf590157fc. No completed1350 receipt found; other migrations do not count. Cockpit reconciles request, obtains authorised credential-free readback. Require request/id/item/M/receipt/output hashes, COMPLETED exit0, nonempty filename+SHA/applied_at ledger row, catalogue PK/FK/null constraints, registry/count_sql and legacy/published preservation; independent semantic review at M. Empty exit0 is not application proof.
## 6. Acceptance / negatives
Historical V SHA256=2faf1c0ae9156f79e68a2e2680f87322b638b0724f25fb85ba5da9bf57d0d9fc; retain base-red/mutations/scope. Preparation has not run implementation tests/CI.
Tests RUN/tests/K4-2b.txt:1-14, SHA256=e150a54359e33732acef759f2196e15f82ccb57c8dd2a1991bd7deb4b327886a; Y expands above:
Execute all 14 exact entries from that pinned newline list, including two named declaration-pin node IDs; expand no globs. Check every entry against H before running.
Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2b.txt`. 
`KY_ITEM=K4-2b bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
Focus: Legacy default byte/value equality; negative chart/generation SQL-filter mutations; missing/forged identities, wrong null estimand, nonfinite D(W), duplicate witness, published/live refusal; planning/reprobe issues zero rows and performs no DELETE.
Negatives: stale/rejected/wrong H/base/M, unproven patch, CI skip, absent/REFUSED readback, wrong chart/build/generation, fixture-as-live, fake qualification, unscoped deletion: refuse/named unavailable.
## 7. Evidence / deployment
inspection.json: item/job/reviewer, hashes/H/V-head/bases/M/patch/latest verdict/phase, dependencies/schema/slot, commands/logs/negatives/scope/deferred steps, CI run/H/results, deploy actual SHA/time/ancestry, request/receipt/output hashes/readback, before/after HEAD/status/tracked hashes, I1/I2/findings.
E:13985: K7-2 successful deploy run38311508214, actual SHA07230af11190b652ac29dcc4ff47f213cb85fca6, 2026-10-12T21:34:48Z. Job `GIT_OPTIONAL_LOCKS=0 git merge-base --is-ancestor M 07230af11190b652ac29dcc4ff47f213cb85fca6`: exit0. Later containment≠1350 application. Verifier rechecks; post_deploy verdict at M, not workflow head_sha (F/cards/PARIKSAKA.md PA-10).
## 8. Existing PR / controller handoff
Return PR#3390 @ H/evidence digest; controller registers/publishes verdicts/completion. U/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:75: tests_and_verdict for named steps; deferred stay open. Mismatch→cockpit, no ledger edit.
## 9. Do not
No rebuild/reallocate/reapply/production/credentials/computation/live fixture bypass/doctrine/deletion/FROZEN/control/generated/Git writes/own acceptance/duplicate request/DONE from merge. Global HOLD stops. RUN/HANDOVER_STATE_20261013T0526Z.md:1-12 is historical v2; A governs now.
Notes: (I) INTERPRETATION: fixtures/SQL/readback; no chart MCP (this packet:25,29,32,35-40).
