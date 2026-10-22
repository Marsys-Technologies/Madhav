# Dispatch chain (A11 items 5 and 7) — TR pass to seal hand-off, automatic and detector-gated

Where it lives: this folder (`fleet/dispatch_chain.py`, tests `fleet/tests/test_dispatch_chain.py`, CI suite `governance-tool-tests-shard-5-0`). It is the sibling of the seal controller
(`SEAL_CONTROLLER_SC1.md`): one poll per run, stdlib only, nothing connects to a database, no credential is read. The cockpit installs the launchd wrapper (below); this folder carries no plist.

Every stage re-evaluates from evidence on every poll, in order, and stops at the first detector that does not read true (root CLAUDE.md §N.8). Markers (`$OUT/markers/`) only make the
EMISSIONS exactly-once per (generation, trial head) — they are never evidence that a stage passed.

## The chain

| Stage | Detector (reads false when…) | Action it takes when true |
|---|---|---|
| S0 `TRIAL_READY` | `trial_ready.json` is not `TRIAL_READY/1` at H, lacks one of T01..T25, any value is not `true` (recounted; the file's `ready` is cross-checked, never trusted), a true check names no evidence | A0 arm the 12-class TR: write the harness command (never run) |
| S1 `TR_PASS_MERGE` | `tr_verdict.json` (`ky.tr_verdict/1`) is not at H, does not cite the digest of THIS trial_ready, is DIAGNOSTIC, lacks 12 classes, any of G-1..G-7 is not `true`, or the verdict disagrees with the recount; RV-INT part 2 result is not an ACCEPTED reviewer verdict at H with a patch id, claims and no blocking finding; PR head ≠ H, base ≠ main, draft, closed | A1 `gh pr merge N --auto --squash --match-head-commit H` (+ remove a hold label); waits for MERGED |
| S2 `MAIN_EQUIVALENCE` | merge commit M not reachable from main; a required main workflow not green AT M; no NEW `deploy.yml` dispatch run beyond those that predate the dispatch, or it did not succeed; the deployed pipeline image (executor `cloudrun_job_readback` receipt) does not carry M; the main EQUIVALENCE_RECORD is not of M; the decision is not EQUAL (category table named in the hold), not bound to both record digests, or contradicts its own categories | A2 deploy `deploy.yml` with `force_all_services=true` (after CI green only); image readback request; `equivalence_record.py record` / `compare` |
| S3 `REBIND_ADMIT_DISPATCH` | executor `CAPABILITIES.json` not ACTIVE at M / stale / production slot busy; the v1.7 rebind record not at M, staged files changed since its digest, a staged production pin ≠ M; the admission rehearsal not of M, with flags, a control that admitted its planted defect, or a dispatch-path template not admitted | A3 rebind command (written); `admission_rehearsal.py`; the pack's century template queued byte-for-byte |
| S4 `BUILD_VERIFY_LAUNCH` | dispatch receipt not COMPLETED/0 at M or without a `LAUNCHED` `ky.century_launch/1` record; execution readback not for that execution / run id / M image, FAILED or RUNNING | A4 every sharded `verification_job` template queued in the SAME poll; fresh read-only build readbacks while it runs |
| S5 `AGGREGATE_HANDOFF` | a verification receipt not COMPLETED/0 at M; `seal_controller.check_aggregate` (the reviewed SC-1 detector) does not read PASSED | A5 the adopted-generation file for SC-1 (which then pages the surrogate for the brief and approval) |

## Hold and page rules

Any detector that reads false or null is a HOLD with a named code (`S2_CI_RED`, `S3_STALE_PINS`, …) in `CHAIN_STATUS.json`, paged ONCE per (stage, code, reason) as `PAGE CHAIN-HOLD`.
A SOFT hold (the producer is known to be in flight: CI running, receipt not back, auto-merge queued) carries the same status but is paged (`PAGE CHAIN-STALL`, once) only after the stage has waited
`stall_s` (config; default 7200 s; `stall_s_by_stage` per stage). A non-idempotent action (the deploy dispatch) leaves an INTENT marker first and is never repeated by this program.

## Modes

* default (EMIT): `gh` READS run (two fixed shapes, repo-pinned); nothing is mutated; each action is written under `$OUT/actions/` or `$OUT/requests/` for the cockpit.
* `--apply`: additionally performs the allow-listed actions marked `chain --apply` (`python3 dispatch_chain.py --list-actions` prints every action, its kind, who performs it and its authority).
  Requests then go to `--requests-dir` (default `<ops>/requests`, the executor queue — the executor, not this program, admits or refuses them).
* `--dry-run`: writes NOTHING and prints the would-do sequence (all six stages with PASS / HOLD / NOT_REACHED and each action's state).

## Config (`ky.dispatch_chain_config/1`, written by the cockpit; default `/Users/Dev/kalayantra/run/DISPATCH_CHAIN.json`)

`chart_id`, `generation`, `repo` (checkout holding the merged main objects), `evidence_dir`, `trial {head, arm {where cloud|mac, argv}}`, `pr {number, repo, hold_labels, merge_method}`, `ci {required [workflow names]}`,
`main {pinned_inputs_file}`, `dispatch {pack_version "1.7", staged_dir, century_template, rebind_argv, sql_dir, sandbox_root, capabilities}`, `verification {templates [...]}`,
`seal {aggregate_file, expected_classes [26], adopted_file, out, verification_operation_id?, …}`, optional `stall_s`, `readback_every_s` (300), `capabilities_max_age_s` (900), `capabilities_file`, `evidence {name: path}`.
Evidence files (under `evidence_dir`): `trial_ready.json`, `tr_verdict.json`, `trial_record.json`, `rvint_part2.result.json`, `main_record.json`, `equivalence_decision.json`, `pack_rebind.json`, `rehearsal/<M12>/REHEARSAL.json`.

launchd (cockpit's own label): `ProgramArguments` `/opt/homebrew/bin/python3 <checkout of main>/00_ARCHITECTURE/briefs/kalayantra/fleet/dispatch_chain.py --out "$OUT" --pages-log fast/PAGES.log --apply`, `StartInterval` 60, `RunAtLoad`.

## Interpretations (I) — alternatives in result.json

1. `ky.tr_verdict/1`, `ky.pack_rebind/1` and the RV-INT part-2 file (a reviewer `ky.job_result/1`, item matching `RV-INT … part 2`) have no producer on main yet: the shapes are defined here and each detector is strict about them. A different shape needs one edit in the reader.
2. "Merged on main" = PR MERGED + the GitHub compare API says M is `identical`/`behind` main; "main CI green" = the newest run of each `ci.required` workflow at M concluded success; "forced image deploy" = a NEW `deploy.yml` workflow_dispatch run (not in the prior-id set recorded at dispatch) that succeeded AND the deployed image carries M.
3. "v1.7 rebind" = the pack's repin tool, run by the cockpit (`dispatch.rebind_argv` written, never run); the chain checks its result. "Century dispatch request (orchestrator_rebuild … per the pack)" = whichever of `century_dispatch` / `orchestrator_rebuild` the pack's `dispatch.century_template` is; the chain never edits a template.
4. Sharded verification = the pack's list of `verification_job` templates; the executor kind only takes `generation`, so the shard split lives in the pack, not here. All are queued in one poll.
5. A multi-shard seal hand-off names the first template's operation as SC-1's `verification_operation_id` (override: `seal.verification_operation_id`); this program additionally requires every shard's receipt.
