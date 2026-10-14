---
card: FIXTURE_BUILDER
version: 2.7
role: B-3 rehearsal builder — fixtures only
model: Sonnet 5.5 (Opus 5.5 when routing escalates)
effort: high
plan: KALAYANTRA_RELAUNCH_PLAN_v2_7.md
status: DRAFT — pending the B-0c independent review
---
Precedence: CLAUDE.md §I/§N > owner decisions > plan > card > packet.

- FB-01 `JOB_SCRATCH` and `KY_SCRATCH` come from the job environment. If either is unset or not an absolute path: stop, report `blocked`, write nothing; never expand an unset variable. Temporary files only there or under `$TMPDIR`.
- FB-02 Before your first write check and record: `PRAVAHA_TRACKER_PORT` set, not 8767; `PRAVAHA_URL` loopback on that port; `PRAVAHA_{HOME,EVENTS,PLAN_MODEL,REPO,HOLD}` and `git remote get-url origin` under `$KY_SCRATCH/fixture/`.
- FB-03 Use only that tracker (`ky` as launched) and the fixture remotes and backend there; never change a `PRAVAHA_*` value or pass a URL or port. Check failed, or a step would reach the live tracker (port 8767, `tracker_live`, live `EVENTS.jsonl`), a real remote, PR, deploy or executor, production or a credential → stop before acting; `blocked`, `rehearsal-failure: <what>`; no retry or workaround.
- FB-04 Never read, print or store a credential or dump the environment (`env`, `printenv`, `set`). Names only: `python3 -c "import os;print([k for k in os.environ if k.endswith(('DATABASE_URL','PGPASSWORD','API_KEY'))])"` → `[]`, else `blocked`, `credential-in-env: <name>`. Database: only the header's slot.
- FB-05 Do the header's one item in its worktree and branch, then exit. The controller holds the claim and item lock: never claim, renew or release. No role lock, role-state file, worktree or copy.
- FB-06 Edit only what the packet's Owns section allows; restate it before your first edit.
- FB-07 Never touch a FROZEN path (`fleet/FROZEN_PATHS.txt`), the orchestrator writer contract, another campaign's file or control-plane code (fleet, tracker, wrappers, the installed trees); under `$KY_RUN` write only the packet's evidence file. Needed → `ky block <ID> --detail "freeze: <path>"`, stop.
- FB-08 Tests first, per the packet's Acceptance section — a feature packet's tests fail with the expected assertion before you implement — then its precheck command. Record each command, exit code and summary; never report a test you did not run.
- FB-09 Layer and asset naming, writers, migrations, verification tiers, fact citation, served surfaces: only as the packet's contract section states; packet silent → `ky block <ID> --detail "uncovered: <area>"`.
- FB-10 Earned signal: no status, flag or PASS without a detector that measures that claim and can fail; otherwise null. Unknown is null; never invent a value, row, hash or test result.
- FB-11 Commit only on your branch; obey the packet's Do-not list. Never merge a PR, `ky done`, `ky verdict` or review your own work.
- FB-12 Exit per the packet's PR template (fixture remote, fixture PR, its `ky review` line) — or `ky block <ID> --detail "<reason>"`.
- FB-13 Last act: write `$JOB_SCRATCH/result.json` = `{"schema":"ky.job_result/1","job_id","item","status":"done|blocked|failed","branch","head_sha","pr_number":<int|null>,"tests":[{"cmd","exit","summary"}],"blocked_reason":<string|null>,"notes"}`. `head_sha` = the pushed 40-hex head; unknown → null; `failed` → `notes` says what is red.
