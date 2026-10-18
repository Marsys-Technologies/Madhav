```json
{"id":"KV3-B-EXECUTOR-TABLE",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§2; §5; §6 EXECUTE; §8.2; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/control/kalayantra/plan_model.json","revision":"7ee8f2af278e9b09868968a593db25ac835457e1","section_range":"items J-1a, J-3a, J-4b, J-4d, J-6m, J-6r, K9-23","sha256":"64c6b291670cea2226e322d804fbf238980ae2864d19f34e6a1a05229f231edf"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json",
"00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/executor.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_executor_table.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_executor_table.py 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/executor_cases.py -q -p no:cacheprovider",
"expected_result":"exit 0; executor_cases.py unedited; the enabled_by test is red on the base (K9-3 is not a model item)",
"negative_cases":[
"request for a disabled kind: validate() answers 'not enabled'",
"entry enabled in a copy but with a TO_BE_SET script: refused",
"requester outside the entry's requesters: refused",
"production request without a v1..v4 acceptance bound to its digest: refused",
"any executor.py code line changed other than the GIT assignment: boundary test fails"]},
"packet_sha256":"7a347319d4578285833c0b082e5a57f1acae1a09f61bdc4a9341e09692f7ca84"}
```
F = `00_ARCHITECTURE/briefs/kalayantra/fleet`.

**Pins** Plan v2.7 at e709f60d7; model at 7ee8f2af27; historical base = the reviewed B-0c head in the job header. `F/executor.py` at e709f60d7 has sha256 `8b9a164f52b307514d7b42f87019070689b1533f624b871a2e1d113408ebdcf7`.
Version 1.0; status: preparation; changelog: model pin refreshed; scope unchanged.

**Owns** `F/executor_ops.json`; in `F/executor.py` and `F/executor.sh` ONLY the git-handle path (`GIT`); `F/tests/test_executor_table.py` (new). Prohibited: every other line of executor.py; the running executor, `$KY_ROOT/exec`, `$KY_RUN/ops`, the installed trees; the plan model (read-only); FROZEN paths.

**Spec** (verbatim)
```excerpt plan §2
kept; re-pointed, extended and re-tested in B-1; executor authority boundary unchanged
```
```excerpt plan §14 B-1
executor table additions (incl. K9-23's)
```
```excerpt plan §5
Model `streams[].worktrees[]`, detector and
  executor paths migrate in B-0/B-1.
```
```excerpt plan §6 EXECUTE row
script (`executor.py`, authority boundary unchanged) | — | receipt in `run/ops/receipts/`; GitHub protected-window dispatch stays an owner-approved workflow action
```
```excerpt plan §8.2
Prohibited: `FROZEN_PATHS.txt`, cross-campaign files, and — for **campaign** builders —
   control-plane code
```

**Contract**
A. Table.
1. K9-23's additions: the five entries whose `enabled_by` is `K9-3` — an id no longer in the model (regrouped into K9-23) — `orchestrator_rebuild_dryrun`, `orchestrator_rebuild`, `layer_verify`, `layer_publish`, `layer_rollback`: `enabled_by` becomes `K9-23` and the placeholder `TO_BE_SET_BY_K9-3…` becomes `TO_BE_SET_BY_K9-23…`.
2. Nothing is enabled or disabled: the enabled kinds stay exactly `readback_sql`, `migration_readback`, `local_schema_seed`, `finalize`. No placeholder `script` is filled in (those scripts do not exist). `needs`, `requesters`, `production`, `fixed_args`, `allowed_args`, `required_rows`, `timeout_s` of every entry are unchanged. `local_schema_seed` stays script `F/local_db.sh`, `fixed_args ["seed"]` (KV3-B-LOCALDB keeps that command).
3. FORMAT RULE kept: `enabled` is the first key of every entry, because the model's detectors read it. `_doc` replaces enabling-by-item and setting-required_rows-by-item claims with: `enabled_by` names the item an entry serves; campaign builders never edit this file; later enablement follows Amendment A1 D-13, outside this item's scope.

B. executor.py: `GIT` = `KY_SOURCE_REPO` from the environment, default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign` (plan §5 campaign checkout; as in kyctl.sh and kyveto.py), replacing `KY_ROOT/wt/campaign`; INTERPRETATION: the repository whose `origin/main` supplies table and scripts is thereby environment-selected, as `KY_ROOT` already made it. executor.sh: the same for its `GIT`. No other code line changes. `validate`, `execute`, `run_one`, `main`, `lease_live`, `request_digest`, `fence_quiescent`, `refresh_refusal_reason`, `handover_from_main`, `refresh_from_main_or_fail_closed`, `capabilities`, `run_group` and every constant (`CHILD_ENV_ALLOW`, `SAFE_*`, `APPROVAL_MAX_AGE_S`, `MAX_TIMEOUT`, `CANONICAL_CHART`) stay byte-identical: that is the authority boundary.

C. Unchanged interface other packets may assume (from executor.py):
- request `$KY_RUN/ops/requests/<operation_id>.json`: `{operation_id, kind, item_id, idempotency_key, requested_by, kyd, args, timeout_s?}`; a production kind adds `chart_id` (the canonical chart), `lease_id`, `reviewed_commit` (merged to main), `expires_at`, `acceptance_receipt` (a path under `run/ops/acceptance/`);
- acceptance `$KY_RUN/ops/acceptance/<operation_id>.json`: `{result: "ACCEPTED", operation_id, by: v1|v2|v3|v4, reviewed_commit, ts, request_sha256, rows, checks: {backup_taken, restore_verified, dry_run_passed}}`; `request_sha256` = sha256 of the request as sorted compact JSON without `acceptance_receipt`; at most 3 h old;
- receipt `$KY_RUN/ops/receipts/<operation_id>.json`: `{operation_id, kind, item_id, status: RUNNING|COMPLETED|FAILED|REFUSED|INTERRUPTED, reason, exit_code, request_sha256, reviewed_commit, output_file, output_sha256, ts}`;
- fence `$KY_RUN/ops/PRODUCTION_PENDING.json`, quiescence `…/acceptance/<operation_id>.quiescence.json` `{operation_id, request_sha256, result: "ACCEPTED", by, ts}`;
- table and scripts are read from `origin/main` only; an entry without `requesters` accepts `adhikarin` alone.

D. J-1a, J-4b, J-4d, J-6m, J-6r (ruling P10). Their entries, `smalltest_dispatch`, `verification_job`, `century_dispatch`, `publish_head`, `rollback_head`, are in the table DISABLED (all five are present at the base; one found absent is added with `enabled: false` first and `enabled_by` its item). Each item is K-owned, `completion_kind: code`, and its `file_contains` detector reads `"<kind>"\s*:\s*\{\s*"enabled"\s*:\s*true` in the campaign checkout's table, so it stays false and COMPLETE waits.
**Enablement authority.** KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md:44–54 settles later enablement by recorded surrogate decision after built/dry-run scripts. This packet enables nothing and edits no detector. J-3a/K9-23 retain their own detectors. Admission is not redispatch of installed work.

**Depends on** Wave 2. KV3-B-LOCALDB (wave 1) only for `local_db.sh seed` (unchanged call). KV3-B-KYDKINDS-OPS (wave 3) may assume C.

**Acceptance** Tests first. Must show: every `enabled_by` is an item id of `00_ARCHITECTURE/control/kalayantra/plan_model.json`; the enabled set is exactly the four kinds; every field of every entry equals the table at e709f60d7 except the five `enabled_by`/placeholder edits and `_doc`; the five P10 entries are present with `enabled: false`; `enabled` is each entry's first key; each of the five model patterns (read from the model, not retyped) does not match the table and does match a copy with that one entry flipped; executor.py at e709f60d7 (`git show`) has the pinned sha256 and differs from the working file only in the `GIT` assignment and comment or docstring lines naming that path; the listed functions hash equal to it. The negative cases run through `validate` on a temp KY_ROOT with `KY_SOURCE_REPO` = a temp repository, never the campaign checkout, never the network. An entry whose state the test cannot read is a failure, not a pass.

**Evidence** `result.json` (BS-16): each command, exit code, summary; skips named; pushed `head_sha`.

**Branch and PR** `kalayantra/kv3-b-executor-table`; one PR to main, "KĀLA-YANTRA v3 KV3-B-EXECUTOR-TABLE: executor table additions". Fleet merges under Amendment A1:26–33; job never merges.

**Do not** edit outside Owns (plan, cards, schemas, packets, model); enable an entry; start or stop the executor; write an operation request; fetch or touch the campaign checkout; rebase or force-push; read credentials, `executor.env` or pgenv; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
