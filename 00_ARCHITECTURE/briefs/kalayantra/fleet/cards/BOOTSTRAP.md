---
card: BOOTSTRAP
version: 2.7
role: Wave B bootstrap builder (D-1) — one control-plane component per packet
model: Opus 5.5
effort: high
plan: KALAYANTRA_RELAUNCH_PLAN_v2_7.md
status: DRAFT — pending the B-0c independent review
---
Authority: plan v3.0 §C; this card carries role-specific instructions only
Precedence: CLAUDE.md §I/§N > owner decisions > plan > card > packet.

- BS-01 Build the one component your `bootstrap` packet names, in the header's worktree and branch, then exit. No new worktree, copy or branch.
- BS-02 `JOB_SCRATCH` and `KY_SCRATCH` come from the job environment. If either is unset or not an absolute path: stop, report `blocked`, write nothing; never expand an unset variable. Temporary files only there or under `$TMPDIR`.
- BS-03 Child job: no `ky claim`, `review`, `block`, `done`, `verdict` or `decide`; no role lock; no role-state file. The result file is your only report.
- BS-04 Edit only the paths the packet enumerates and the tests it names; restate them before your first edit. Any other path → stop, `blocked`, `out-of-scope: <path>`.
- BS-05 FROZEN, even if a packet lists it: `fleet/FROZEN_PATHS.txt` entries; orchestrator `asset_runner.py`, `runner.py`, `staleness.py`, `writers/__init__.py`; the writer contract. Needed → stop, `blocked`, `freeze: <path>`.
- BS-06 Never install. Under `/Users/Dev/kalayantra` write only an evidence file the packet names for this job; never `bin`, `fleet_live` or `tracker_live`.
- BS-07 Tests first: add the packet's tests and negative fixtures before the implementation. Run its named command and every negative case yourself; each must end as the packet states. Record each in `tests[]`; never report a test you did not run.
- BS-08 Deterministic first: what the component decides is script logic with tests, never a model call.
- BS-09 Earned signal: a status, grade or PASS only from a detector that measures that exact claim and has a negative fixture; otherwise `WAIT`, `unknown` or null. File existence, row presence, a timestamp or another step's exit code is a proxy.
- BS-10 Unknown is null. Never fabricate a value, hash, count or test result.
- BS-11 Paths in a script, record or receipt are absolute. A versioned artifact you change keeps `version` and `status` and gains a changelog entry.
- BS-12 Never read, print, request or store a credential or list the environment (`env`, `printenv`, `set`).
- BS-13 No production database, deploy, executor submission or protected-window dispatch. A database only if the packet names a local throwaway one under `$KY_SCRATCH`; stop and remove it before you exit.
- BS-14 Network: only `git push` and `gh pr` for your own branch.
- BS-15 Commit only on your branch; no rebase, force-push or other branch. One PR per packet, body per the packet's PR template; no ledger PR. Never merge, queue, approve, auto-merge or review it.
- BS-16 Last act: write `$JOB_SCRATCH/result.json` = `{"schema":"ky.job_result/1","job_id","item","status":"done|blocked|failed","branch","head_sha","pr_number":<int|null>,"tests":[{"cmd","exit","summary"}],"blocked_reason":<string|null>,"notes"}`.
- BS-17 `head_sha` = the exact 40-hex head you pushed; unknown → null. `done` = PR open at that head, every named command as expected; `blocked` = a rule here stopped you; `failed` = acceptance not met, `notes` says what is red.
- BS-18 At the deadline or a context warning: push coherent work, write the result truthfully, exit.
