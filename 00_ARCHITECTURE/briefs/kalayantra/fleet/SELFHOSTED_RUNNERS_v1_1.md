# madhav-db self-hosted runners — runbook v1.1

version: 1.1 · status: ACTIVE · supersedes: the v1.0 runner README of #3736 (cockpit folder `/Users/Dev/scratch.noindex/claude/madhav/20261019-selfhosted-runners/README.md`), step 6 only
authority: OWNER-SELFHOSTED-SPLIT-20261018; SR-RUNNER-PROBE-NOSECRET (owner surrogate, 2026-10-19)

Changelog
- v1.1 (2026-10-19): the `db-runner-probe` job no longer uses a token or asks GitHub for the runner list. It reads a heartbeat
  timestamp in the repository variable `MADHAV_DB_ONLINE`. `MADHAV_RUNNER_PROBE_TOKEN` and `MADHAV_DB_MIN_ONLINE` are retired.
  Every other v1.0 step (fork-approval setting, runner group, image, one trial lane, measurement, known limits) is unchanged.

## How DB jobs choose a machine
The DB-heavy jobs (Kāla DB tests, the DB Integration shards, the Gochara A5.5f / C37 / C38 DB jobs) run on
`["self-hosted","madhav-db"]` or on `ubuntu-latest`. The choice is made by the `db-runner-probe` job in
`.github/workflows/ci.yml`, which itself always runs on a GitHub-hosted runner:

1. `MADHAV_DB_ENABLED=false` → `ubuntu-latest` (kill switch).
2. `MADHAV_DB_ONLINE` unset or empty → `ubuntu-latest`.
3. Value is not `YYYY-MM-DDTHH:MM:SSZ` (UTC, trailing `Z`) or is not a real date → `ubuntu-latest`.
4. Value is more than **60 s in the future** of the probe job's own clock (skew allowance) → `ubuntu-latest`.
5. Value is more than **180 s old** → `ubuntu-latest`.
6. Otherwise (between 180 s old and 60 s ahead) → `["self-hosted","madhav-db"]`.

Same job, same check name: no check is renamed, skipped or duplicated. The step always exits 0, so a broken probe cannot fail
or skip a DB job. The comparison uses only the probe's clock and the stored text; nothing is fetched from GitHub's runner API.

## Heartbeat design (owner's Mac)
- A launchd agent runs every **60 s**. Each run first checks that at least one `madhav-db` runner is online **and idle-capable**
  (a registered runner container is up and can take a job). If so it writes the current UTC time:
  `gh variable set MADHAV_DB_ONLINE --repo Marsys-Technologies/Madhav --body "$(date -u +%Y-%m-%dT%H:%M:%SZ)"`.
  If not, it **writes nothing** — it never writes an "offline" value and never deletes the variable; the old timestamp simply
  ages past 180 s and the DB jobs fall back to `ubuntu-latest` by themselves.
- Why 180 s: three missed beats. A Mac that sleeps, loses network or stops its runners stops beating; within 3 minutes new runs
  stop being routed to it. A job already queued to `madhav-db` when the runner dies waits — flip `MADHAV_DB_ENABLED=false` and re-run it.
- Credentials: none are created. The cockpit's existing `gh` login (already able to manage repository variables) does the write.
  There is no repository secret for this.
- Concurrency: the write is idempotent and last-writer-wins; one agent per Mac is enough.
- Clock: the Mac and GitHub's runners both use network time; the 60 s future allowance absorbs normal drift.

## Operation
1. One-time setup, in order: v1.0 steps 1–5 (fork-approval setting, runner group, image, VM ceiling, start ONE lane).
2. Install the launchd heartbeat (above). Check: `gh variable list --repo Marsys-Technologies/Madhav | grep MADHAV_DB_ONLINE`
   shows a timestamp that advances each minute while the lane is up.
3. DB jobs move to the Mac automatically while the heartbeat is fresh. No secret or PR is needed to turn this on or off.
4. **Kill switch** (no PR): set the repository variable `MADHAV_DB_ENABLED=false` — takes effect on the next workflow run.
   Setting it back to anything else (or deleting it) re-enables routing. Stopping the heartbeat achieves the same within 3 minutes.
5. Measurement and teardown: v1.0 steps 7–8, unchanged.

## What did not change (fork fence)
Fork pull requests never reach a self-hosted label: each DB job's `runs-on` keeps the exact fence
`(github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository) && … || 'ubuntu-latest'`,
enforced by `platform/scripts/governance/check_selfhosted_fork_guard.py`. No workflow uses `pull_request_target` on a self-hosted
label, and no job that can run self-hosted mounts a host path. A fork author cannot influence the heartbeat variable, and even a
fresh heartbeat cannot route a fork PR to the Mac.

## Tests
`platform/scripts/governance/__tests__/test_selfhosted_fork_guard.py` runs the probe step's real script under bash with a fresh,
stale (> 180 s), future-dated (> 60 s), missing, malformed and kill-switch heartbeat; and pins that the probe has no secret and
no `gh api` runner call. The fork-fence tests are unchanged.
