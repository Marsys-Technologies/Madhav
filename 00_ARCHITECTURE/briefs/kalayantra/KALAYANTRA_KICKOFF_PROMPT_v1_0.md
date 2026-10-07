---
artifact: KALAYANTRA_KICKOFF_PROMPT
version: "1.3"
status: ACTIVE — the owner opens Codex on /Users/Dev/kalayantra/wt/campaign with full access and pastes the one-line kickoff; Codex reads this file and does everything below the header, including starting the executor. No terminal step for the owner. (Filename keeps v1_0 by repository convention; the frontmatter version is authoritative.)
date: 2026-10-07
what_this_session_does: 'the LAUNCH only — verify, start the executor and the fleet, confirm both run, report, end. All building, including the bootstrap items B-1b … B-7, is done by the supervised fleet in resumable cycles (charter §3.2, §5).'
owner_steps: |
  1. Open Codex (app or terminal) on the folder /Users/Dev/kalayantra/wt/campaign, with full access (approvals never; the launch starts background processes, Docker and the tracker service).
  2. Paste: "Read /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_KICKOFF_PROMPT_v1_0.md and carry out everything below its header block exactly, beginning with Step 0."
  The two production connections are already in ~/.config/kalayantra/executor.env (filled 2026-10-07 from Secret Manager, mode 600).
to_stop_everything: 'touch /Users/Dev/kalayantra/HOLD   (pauses every lane and the executor at their next boundary; remove the file to resume)'
changelog:
  - "1.3 (2026-10-07): launch pool remains zero until the reviewed B-7p/B-7 gate releases four builders; kickoff itself still releases none."
  - "1.2 (2026-10-07): owner direction — the launch is one pasted prompt, no terminal steps. This session now starts the executor itself, in a child process that sources executor.env; the session's own environment never holds the connections and never prints them."
  - "1.1 (2026-10-06): after Astra's review of the execution design. The kickoff is a short launch; explicit working directory, PATH and stream; specification hash check first; tracker installed from the campaign's copy; no implementation worker before launch acceptance."
  - "1.0 (2026-10-06): first version."
---

You are launching **KĀLA-YANTRA**, the fully autonomous campaign that builds the Kāla layer of the Madhav project as one engine and absorbs the Gochara 5.0 work to its flip. **This session does the launch only: verify, start, confirm, report, end.** The fleet you start does all the building, in supervised cycles, with no human in the loop. Do not ask questions, do not wait for approval, do not pause for confirmation, and do not begin any implementation work yourself.

**Working root:** `/Users/Dev/kalayantra/wt/campaign` (a git worktree of the Madhav repository on branch `campaign/kalayantra`). Never work inside `/Users/Dev/Vibe-Coding/Apps/Madhav` or `/Users/Dev/madhav-l3/*`.

## Step 0 — shell setup (every later command assumes it)

```bash
export KY_ROOT=/Users/Dev/kalayantra
cd "$KY_ROOT/wt/campaign"
export PATH="$KY_ROOT/bin:$PATH"
export KY_STREAM=S
F=00_ARCHITECTURE/briefs/kalayantra/fleet
for v in DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL PGPASSWORD; do
  [ -n "$(printenv "$v")" ] && echo "SET: $v"
done
echo "secret check done"
```

If any name prints as `SET`, run `unset <name>` for each before continuing (never print a value). This session must hold no credential; the fleet refuses to start otherwise.

## Step 1 — read (nothing else)

`00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` — §0, §1, §3, §4.1, §5, §8, §12, §15. That is all this session needs.

## Step 2 — verify, in this order (each command is idempotent; fix only what the step names)

1. **Specifications.** `bash $F/verify_specs.sh` must end with `SPEC HASHES OK`. A mismatch is the one failure that stops the launch: report the table and end.
2. **Branch.** `git status -sb | head -3` shows `campaign/kalayantra`, not behind `origin/campaign/kalayantra`, with no uncommitted change. If it is behind: `git pull --ff-only`. If there are uncommitted changes: report them and end (do not commit, stash or discard anything).
3. **Environment and a real agent start.** `bash $F/preflight.sh bootstrap` must end with `BOOTSTRAP PREFLIGHT OK` and must show `LANE SMOKE PASS` — that is a real start of the worker and reviewer models under the exact lane environment (profile, login, models, tools, no credential-like variable). A ✗ on the venv, the ephemeris files, node modules or docker: run the command again once (it repairs those itself). A ✗ in the lane smoke, or any ✗ that remains: report the line and end — do not launch.
4. **Tracker.** Always run `bash $F/install_tracker.sh --gov "$KY_ROOT/wt/campaign/platform/scripts/governance"` — it must print `ACCEPTED`, and `run/TRACKER_INSTALL_RECEIPT.json` must name this package directory and this campaign's model. A healthy web endpoint alone never substitutes for this installation. Then `curl -fs -m 5 http://127.0.0.1:8767/api/health` shows `"ok": true` with no model error, and `ky status` shows 145 items. (`audit_available: false` in the receipt is expected until bootstrap item B-2.)
5. **Rehearsal databases.** `for l in k1 k2 k3 k4 k5 k6 v1 v2 sutradhara adhikarin; do bash $F/local_db.sh db $l; done` — every line must read `READY` (assertions run in this invocation; a receipt is written). A `FAILED` line: report it and end. This session never takes the schema seed itself (that reads production settings).
6. **Lane worktrees.** `for l in sutradhara adhikarin v1 v2 k1 k2 k3 k4 k5 k6; do test -d "$KY_ROOT/wt/$l/platform/node_modules" && echo "$l ok" || echo "$l MISSING"; done` — a `MISSING` lane: `git -C "$KY_ROOT/wt/campaign" worktree add "$KY_ROOT/wt/$l" --detach origin/main` if the folder is absent, then `(cd "$KY_ROOT/wt/$l/platform" && npm ci) && (cd "$KY_ROOT/wt/$l/platform-mcp" && npm ci)`.
7. **Executor — start it, then check it.** This session starts it, in a child process, so the connections never enter this session's environment and are never shown:
   ```bash
   bash -c 'source "$HOME/.config/kalayantra/executor.env" && bash /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/kalayantra/fleet/executor.sh up' >/dev/null 2>&1
   sleep 5; cat "$KY_ROOT/run/ops/CAPABILITIES.json"
   ```
   The file must show a fresh `ts`, `"pgenv": true`, `"builder": true`, `"owner": true`. `ops_table_on_main: false` is expected before the bootstrap PR merges. If `pgenv`, `builder` or `owner` is false, first check the database tunnel: `lsof -nP -iTCP:5433 -sTCP:LISTEN` must show `cloud-sql-proxy`; if it does not, start it with `nohup cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres >/dev/null 2>&1 &`, wait ten seconds, run `bash $F/executor.sh down`, wait until no `exec/executor.py` process remains, and start the executor again as above. Still false or no file: report `NOT LAUNCHED (executor)` with the CAPABILITIES content and end. Never open, print, copy or `cat` `executor.env`; never `source` it in this session's own shell.
8. **Hold switch.** `test -f "$KY_ROOT/HOLD" && echo HOLD-PRESENT`. If present, a human put it there: report and end without launching.

## Step 3 — launch

```bash
echo 0 > "$KY_ROOT/run/KY_WORKERS"      # initial four builders are released only by reviewed B-7p/B-7 gate
echo 1 > "$KY_ROOT/run/KY_VERIFIERS"    # one verifier until atomic claims are installed (item B-2)
source "$HOME/.config/kalayantra/fleet.env"
bash $F/kalayantra_fleet.sh up
```

The script refuses (exit 78) if a credential is in the environment — go back to Step 0. It starts every lane loop detached; with the two files above, only `sutradhara`, `adhikarin` and `v1` run cycles for now.

## Step 4 — confirm that the fleet really runs (at most fifteen minutes)

Check once a minute, no faster:

```bash
bash $F/kalayantra_fleet.sh status
tail -5 "$KY_ROOT/logs/supervisor.log"
ls -la "$KY_ROOT/logs/" | grep -E 'sutradhara\.1\.log|adhikarin\.1\.log|v1\.1\.log'
```

The launch is **confirmed** when `supervisor.log` shows `cycle 1 start` for `sutradhara`, `adhikarin` and `v1`, each lane's first log file exists and is growing, and its first lines show the model working rather than an error. If a lane's first cycle ends within a minute with an authentication, profile-not-found or model-not-found error: `bash $F/kalayantra_fleet.sh down`, quote the exact error line in the report, and end — the launch failed and nothing is left running.

Do not wait for a cycle to finish, and do not do any bootstrap item yourself: the conductor lane works B-4, B-1b and the rest in its own cycles, under the charter's pre-B-2 bootstrap protocol (§4.1).

## Step 5 — report and end

Print, in this order:

1. `LAUNCHED` or `NOT LAUNCHED (<reason>)`.
2. Worktree `/Users/Dev/kalayantra/wt/campaign`, branch `campaign/kalayantra`, its head (`git rev-parse --short HEAD`).
3. Tracker: `http://127.0.0.1:8767` and the first line of `ky status`.
4. Lanes running, and the pool gates (`cat $KY_ROOT/run/KY_WORKERS $KY_ROOT/run/KY_VERIFIERS`).
5. Executor capabilities as read in Step 2.7 (which of `builder`, `owner` are false, and that the items needing them will wait).
6. How to pause everything: `touch /Users/Dev/kalayantra/HOLD`. How to look: `bash /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/kalayantra/fleet/kalayantra_fleet.sh status`. The morning check (available once item B-2 is done): `KY_STREAM=S /Users/Dev/kalayantra/bin/ky audit --since kickoff`.

Then end the session. The fleet continues by itself.

## Hard rules for this session

No implementation, no pull request, no merge, no commit, no push, no stash, no rebase. No reading, printing or handling of a credential: `~/.config/kalayantra/executor.env` is only ever sourced inside the one child-process command of Step 2.7, and `~/.config/pravaha/pgenv.sh` is never opened. The executor is started only by that command (and restarted only as Step 2.7 says). No change to anything outside `/Users/Dev/kalayantra/run/`. No work in another campaign's worktree. If a step fails in a way this prompt does not cover: report exactly what you ran and what it printed, and end — never improvise a repair.

Begin with Step 0.
