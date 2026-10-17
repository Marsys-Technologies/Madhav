---
artifact: MECHANICAL_ACCEPTANCE
version: "1.0"
status: REVIEW_CANDIDATE
produced_on: 2026-10-17
authority: owner direction A7 D-44 (DECISIONS_SURROGATE.jsonl id D-44)
changelog:
  - "1.0: executor-written post-acceptance for read-only kinds, mechanical quiescence for a fenced production op (new read-only kind `quiescence_check`), PGAPPNAME session marker."
---

# Mechanical acceptance and quiescence (A7 D-44)

Read-only readbacks need no reviewer; writing operations keep exactly ONE V-lane (v1..v4) pre-acceptance; post-acceptance and quiescence are measured by the executor.

## 1. Post-acceptance of a read-only kind

Kinds carrying `"read_only": true` in `executor_ops.json` (`readback_sql`, `migration_readback`, `cloudrun_job_readback`, `quiescence_check`). When such a request ends `COMPLETED` with exit 0 and is archived to `done/`, the executor writes `acceptance/<op>.post.json`:
`schema ky.mechanical_acceptance/1`, `by: executor-mechanical`, `result: ACCEPTED`, `operation_id`, `request_sha256`, `reviewed_commit`, `exit_code`, `output_sha256`, `receipt_sha256`, `checks`, `ts`. It is written only if all `checks` hold: receipt COMPLETED exit 0; receipt names this operation; the archived `done/` request digest equals the receipt's `request_sha256`; the output file digest equals the receipt's `output_sha256`; `reviewed_commit` is present, equals the receipt's and is an ancestor of `origin/main`; the kind is `read_only` and not production in the table read now; not a lane rehearsal. Anything else writes nothing (the reason is in `logs/executor.log`). An existing file is never replaced. **It judges nothing about the readback's content** (e.g. "absence counts are all zero" stays with the consumer).

## 2. Mechanical quiescence

Request the read-only kind `quiescence_check` with `args.operation = <fenced production operation id>` (dispatch operations also `args.execution_readback = <operation id of an ACCEPTED cloudrun_job_readback naming the launched execution>`). `quiescence_sessions.sh` lists the live sessions whose `application_name` equals the operation's marker. The executor then writes `acceptance/<operation>.quiescence.json` (`ky.mechanical_quiescence/1`, `by: executor-mechanical`) only if every check holds: the check itself completed (identity checks above); target is a production, non-lane, non-teardown operation; its receipt is terminal (COMPLETED / FAILED / AWAITING_ABSENCE); the fence names the target and its request digest; no `inflight/` entry is the target (an unreadable entry counts against); the session readback is bound to the target's marker (the target's receipt carries `session_marker`), could see every role's sessions (`sees_all_sessions`, i.e. pg_read_all_stats or superuser), was measured after the target's receipt, and lists no session; for a dispatch, the launched execution is `SUCCEEDED` or `FAILED` per the accepted readback. `fence_quiescent()` accepts `executor-mechanical` only for a record with that schema and every check true.

**The marker.** Before this change no operation set one. The executor now sets `PGAPPNAME=ky-op-<sha256(operation_id)[:16]>` in every non-lane child and records it in the receipt (`session_marker`); libpq applies it to every connection that does not set its own. Receipts made before this change have no `session_marker`, so their quiescence is unmeasurable (check `session_readback_bound_to_the_target_marker` fails; use a V lane). Sessions of a remote Cloud Run execution do not carry the marker: they are covered by the execution readback.

**Not mechanical:** `smalltest_teardown` / `measuring_teardown` (release needs the consumer-judged absence evidence, `absence_receipt` / `absence_acceptance`, which `fence_quiescent` demands regardless of signer).

## 3. Admission

`validate()` is unchanged: a writing operation's pre-acceptance must be `by` v1..v4. `executor-mechanical` is refused there (tested).
