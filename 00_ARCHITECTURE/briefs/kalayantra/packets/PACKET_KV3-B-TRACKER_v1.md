```json
{"id":"KV3-B-TRACKER",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"platform/scripts/governance/** (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§0.4; §6; §8.5; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"KU-01","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"platform/scripts/governance/pravaha_tracker/audit.py",
"platform/scripts/governance/pravaha_tracker/completion.py",
"platform/scripts/governance/pravaha_tracker/state.py",
"platform/scripts/governance/pravaha_tracker/cli.py",
"platform/scripts/governance/pravaha_tracker/server.py",
"platform/scripts/governance/pravaha_tracker/events.py",
"platform/scripts/governance/pravaha_tracker/verdicts.py",
"platform/scripts/governance/pravaha_tracker/tests/test_kalayantra_control_plane.py"],
"acceptance":{
"command":"python3 -B -m pytest platform/scripts/governance/pravaha_tracker/tests/test_kalayantra_control_plane.py platform/scripts/governance/pravaha_tracker/tests/test_pravaha.py platform/scripts/governance/pravaha_tracker/tests/test_kimi_effort.py 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyreconcile.py -q -p no:cacheprovider",
"expected_result":"exit 0; test_kyreconcile.py unedited",
"negative_cases":[
"code-only completion without recorded deployment containment: guard refuses, audit reports",
"data-writing completion, post_deploy missing or at the wrong commit: guard refuses, audit reports",
"predicate False or not importable: no inheritance in guard or audit"]},
"packet_sha256":"85fc0a67adfea815e09b41cc51dc59223b3706afc6f13d7b097db74eae057c0b"}
```
**Pins** Plan v2.7 at e709f60d7; base = the job header's reviewed B-0c head.

**Owns** The eight `d1_paths`: seven tracker modules and the existing test file (new tests go there). The tracker is not FROZEN (precheck.sh step 9/9 names no tracker path). Read-only: plan model, staged actions, live EVENTS.jsonl. Prohibited: FROZEN paths (BS-05).

**Spec** (verbatim)
```excerpt plan §6
**Item declaration:** every retained executable item declares `completion_kind:
code | artifact | packet | operation`, its producer stream, reviewer identity rule,
detector and required step evidence (B-0 adds the fields).
```
```excerpt plan §6
**Inheritance predicate (one implementation, used by dispatcher and tracker):**
```
```excerpt plan §0.4
stage
   the owner-authorised `refused` decision to be published by the installation/model
   migration action (B-2), never by a test.
```
KU-01 (label `tracker-semantics`), verbatim:
```text
Audit and guarded completion shall share the same normalized, typed evidence requirements. Data-writing code requires ACCEPTED post_deploy evidence at the observed squash merge commit. Code-only completion requires verified successful deployment containment of its mapped merge commit, without inventing a post_deploy obligation. Artifact and operation completion retain their digest-bound acceptance requirements. Apply the shared reviewed-patch inheritance predicate wherever reviewed-head validity is evaluated.

Acceptance fixtures shall prove: valid code-only completion without post_deploy passes; missing deployment containment fails; data-writing completion with missing or wrong-commit post_deploy evidence fails; invalid inheritance fails. Reconcile remaining legacy claim/verdict findings explicitly before B-2 preflight acceptance. Do not fabricate verdicts, rewrite historical events or suppress unresolved findings.
```

**Contract** Rules 1–3 and 5–7 apply only to a model with `control_plane.declarations`; others as today.
1. `server.check_model` rejects: an executable item (not `done_by` decision/join) without `completion_kind` (one of four), `producer` (equal to `owner`), `reviewer_rule` (a key of `declarations.reviewer_rule`) or `detector`; `step_evidence` keys other than its `steps`; `done_by == "join"` disagreeing with `join is True`. The committed model passes.
2. New `completion.evidence_requirements(model, item)` is the ONE table, used by `completion.guarded_done_event` and `audit.audit`, keyed by `reviewer_rule`:
   - `v_exact_head_then_deploy_containment`: code; ACCEPTED pre_merge verdict valid for the reviewed head; recorded deployment containing the merge commit (`deploy.contains_merge is True`, `deployed_sha`, `run_id`); no post_deploy.
   - `v_exact_head_then_post_deploy_at_merge_commit`: code; that verdict and ACCEPTED post_deploy at `pr.mergeCommit.oid`.
   - `v_artifact_digest_reviewer_not_author`, `finalizer_independent_review_artifact_digest`: artifact verdict at the digest.
   - `v_pre_acceptance_then_receipt_readback_digest`: COMPLETED receipt for this item and operation id; artifact verdict at its digest.
   - `v_packet_verdict_bound_to_external_review`: packet, as today.
   The guard refuses a proof `type` other than the declared `completion_kind`. `completion.writes_data` normalises (empty, non-string/non-list and `NONE` are not data-writing; plan §8.5); a rule contradicting it is `declaration_conflict`: refused.
3. `audit.audit` gains `repo=None`; its code block and end-of-log recheck use rule 2. New codes `missing_deployment_containment`, `completion_kind_mismatch`, `declaration_conflict`; `missing_post_deploy_verdict` only where rule 2 requires it. `cli.cmd_audit` passes the repo as `cli.cmd_guarded_done` does. Unchanged: lines `FAIL <code> <ref>: <detail>` and `AUDIT PASS|FAIL: <n> findings`; exit 0, 1 findings, 2 unavailable. Nothing is filtered.
4. `verdicts.accepted_verdict` (signature unchanged) calls the shared predicate in its inheritance branch; `verdicts.merge_only_between` is deleted.
5. `events.validate_against_model`, verdict branch: the actor carries a slot (`stream-V:<slot>`) different from the slot of every actor that recorded a `review` event for the item.
6. New `cli.cmd_step` (plan §6 STEP): exit 2, nothing written, unless the step is declared, its `step_evidence` detector is non-null, the live tracker verifies it done and `--evidence` is an existing file; the event records the absolute path and `evidence_sha256`. `server` `do_GET`: `/api/verify?id=<ID>&step=<step>` verifies that detector (404 when null).
7. `state.build_snapshot`: item rows also carry `completion_kind`, `producer`, `reviewer_rule`, `step_evidence` (shown by `ky next --json`); existing keys and values unchanged for the same inputs. Staging: a decision whose item has `triage.class == "retire_decision"` and no final outcome carries `staged: true` and is absent from `native_queue`; the package never writes a decision event itself. B-2 publishes with `ky decide <D-id> --outcome refused --as steward --delegated --detail "<text>"` (the form of kyveto.py `run_ky`); the retired item then reads `not_applicable`.
8. Unchanged, test-pinned (kyloop.py `poll_inboxes`): `ky inbox --stream S|--steward --json` exits 0 with a JSON list carrying `msg_id`, 1 when empty.

INTERPRETATION: the table in 2; the step guard acts at the write path only (old step events are not re-judged); `staged: true` and the queue exclusion; the join rule in 1 (from retired B-CLAIM-RECOVERY); `build_snapshot` stays pure, no git.

**Depends on** Wave 2. KV3-B-KYVERDICTS (same wave; tests use a stub module), ruling P4: top-level module `kyverdicts` on `sys.path` (the `ky` wrapper and the tracker service add `<root>/fleet_live`); `kyverdicts.inherits(repo, old_head, new_head) -> bool`, fail-closed: import error, exception or non-True = not inherited.

**Acceptance** Tests first: the four KU-01 fixtures, each on BOTH `guarded_done_event` and `audit` for the same events; audit reports a completion exactly when the guard refuses it; a refusing test per rule; EVENTS bytes unchanged by model load, tick and audit. `test_verdict_survives_merge_only_push_but_not_a_new_commit` is rewritten for the predicate, not deleted. What the tracker cannot verify is refused, never recorded.

**Evidence** `result.json` (BS-16): each command, exit code, summary; skips named; pushed `head_sha`.

**Branch and PR** `kalayantra/kv3-b-tracker`; one PR to main, "KĀLA-YANTRA v3 KV3-B-TRACKER: tracker semantic changes"; never merged by the job.

**Do not** edit outside Owns (plan, cards, schemas, packets, model); write a tracker event outside a temp EVENTS file; run `ky` or the tracker service; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
