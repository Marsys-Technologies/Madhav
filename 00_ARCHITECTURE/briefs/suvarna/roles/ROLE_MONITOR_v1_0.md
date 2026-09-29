---
artifact: SUVARNA_ROLE_MONITOR
canonical_id: SUVARNA_ROLE_MONITOR
version: "1.1"
status: "DRAFT — for native review (N-1, with the v1.3 plan set)"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.1 (2026-09-29, L.12 sweep to the v1.3 set): eight checks, including credential_readonly (D6: the login is suvarna_reader with no write path by effective privilege); builder_scope added by E7.3 (D1). Credential semantics match monitor.py: missing blocks; group/world-readable or a backup beside it warns; a changed file is not detectable by stat. Power: warn on battery at 50% or more, block below; a build treats a power warn as a failed precondition. Stalls and spend belong to the Conductor (arch §12.8), not the Monitor. New: the Conductor watchdog (D5, charter G15; alerting from L.15, relaunch from L.14). Whole-item blocked events are the Conductor's (arch §12.1); the Monitor's only blocked event is the watchdog's. Stale 'ROLE_COMMON open question 9' references replaced by arch §12.8 and §12.1. Sources: REVIEW_PASS1_DISPOSITION_v1_0.md (C15, C16, C34, C43; S16, S27 residuals); D5, D6."
  - "1.0 (2026-09-29): first draft, from arch §3.1, §5.4, §8, §11.3, charter G15, R10, §10 and platform/scripts/governance/suvarna_tracker/monitor.py."
---

# Role · Monitor

Read `ROLE_COMMON_v1_0.md` first. It holds the shared rules; this file does not repeat them.

## Who you are

The Monitor is a script, not a model (arch §3.1: "no model — a script"). It checks the environment the swarm runs in,
repairs what it is allowed to, watches the Conductors' heartbeats, and writes what it sees to the event log. This file
is for whoever starts it (the native at launch, runbook §2; a Conductor if it finds it not running) and for every role
that reads its output. Always on, one instance, serving both execution sessions.

## Inputs

- `platform/scripts/governance/suvarna_tracker/monitor.py`. Environment: `SUVARNA_HOME=/Users/Dev/suvarna`; the
  credential path defaults to `~/.config/suvarna/pgenv.sh`, which the `credential` check only `stat`s and never opens.
  The `credential_readonly` check runs one read-only catalog query through that file, in a subprocess, and never prints
  it.

## What it does

1. **Start it once**, detached, if it is not already running:
   `PYTHONPATH=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna python3 -m suvarna_tracker.monitor --watch 300 --emit --repair`
2. **Eight checks** every 300 seconds, each `ok`, `warn` or `block` (arch §8); overall exit 0 / 1 / 2:
   - `db_proxy`: the database proxy listening on 5433;
   - `credential`: the file exists (missing blocks); owner-only (group- or world-readable warns); no
     `pgenv*.bak*`, `pgenv.previous*` or `.pgenv.*.tmp` beside it (warns). It cannot see whether the contents changed;
   - `credential_readonly` (D6): session and current user both `suvarna_reader`, its role default read-only, and no
     write path by effective privilege (tables, columns, sequences, CREATE, memberships, ownership, SECURITY DEFINER
     functions) and no exposure of withheld columns. Any write path or exposure blocks. **Until the native applies D6
     this check blocks, which is correct**: nothing is dispatched on the old app login;
   - `power`: AC ok; on battery at 50% or more warns; below 50% blocks. A production build treats a `power` warn as a
     failed precondition (charter §6.7);
   - `sleep_prevented`: `caffeinate` or an active assertion;
   - `hold`: `run/SUVARNA_HOLD` present blocks;
   - `disk`: below 20 GB warns, below 5 GB blocks;
   - `tracker`: `/api/health` answers.
   A check that cannot measure reports `warn`, never `ok`. **E7.3 adds a ninth, `builder_scope`** (D1): the builder
   account is `guest` and `active` and its grants are exactly `{(482012f1, 'build')}`; anything else blocks.
3. **Repairs** (`--repair`, G15), only when the process is verifiably not running: restart the database proxy on 5433
   (never a proxy on another workstream's port), the tracker supervisor (`run_tracker.sh`), and `caffeinate`. With the
   hold switch on, it repairs nothing.
4. **Conductor watchdog** (D5, arch §5.5, G15). A Conductor whose last heartbeat is older than three loop intervals is
   stalled.
   - **Interim, to G2 (built by L.15):** alerting only: emit `blocked` on the session's Conductor, write
     `$SUVARNA_HOME/run/CONDUCTOR_STALLED`, and wait for the native (runbook §6).
   - **Durable (built by L.14):** relaunch one headless pass (`claude -p` with the Conductor prompt,
     `--permission-mode dontAsk`, in the hq worktree). At most three relaunches an hour per session; then set the hold,
     emit why, and park. A usage-limit pause reads as a stall: read the CLI's error and wait it out; never restart-loop.
   - Until L.15 lands the watchdog in `monitor.py`, it does not exist: do not improvise it.
5. **Never touches** the credentials, the hold switch (other than setting it after the third relaunch), disk or power
   (G15, R10). Those are reported, and the Steward parks them. A missing credential file, or one that fails
   `credential_readonly` or `builder_scope`, is never recreated or changed (charter §10).

## Pausing dispatch

- The Monitor does not stop other agents itself. **Before each dispatch the Conductor runs**
  `python3 -m suvarna_tracker.monitor --once` **and dispatches nothing on exit 2 (block)** (arch §8, §12.8).
- On a block the Conductor emits the pause, and the resume, as `note` events (ROLE_CONDUCTOR step 2). Items already
  running finish.
- **Agent stalls and the spend meter belong to the Conductor** (arch §12.8). The Monitor does not measure them.
- The tracker's `monitor_check_ok` detector runs `monitor --once --json` itself (arch §11.7); `run/monitor_state.json`
  keeps only the non-ok set.

## Outputs and where they go

- `$SUVARNA_HOME/run/monitor_state.json` (the last non-ok set); `$SUVARNA_HOME/run/proxy.log` for a proxy it started;
  `$SUVARNA_HOME/run/CONDUCTOR_STALLED` when the watchdog fires.
- Events in `$SUVARNA_HOME/run/EVENTS.jsonl` (below).

## Report as it happens

With `--emit` the script writes, as actor `monitor`:
- a `heartbeat` every pass (`ok: 8/8`, or `WARN: …` / `BLOCK: …` listing the non-ok checks);
- a `note` when the set of non-ok checks changes, including when it clears;
- a `note` per repair taken (`repair: …`) and per Conductor relaunch;
- the watchdog's `blocked` on a stalled Conductor. Every other whole-item `blocked` on a plan item is the Conductor's
  (arch §11.3, §12.1).
If the monitor's own emit fails, its output shows `emit errors`: treat that as the log being unwritable (P12) and stop
dispatch until it is fixed.

## Authority

- **Acts under:** G15 (repair the database proxy, the tracker supervisor and sleep prevention; relaunch a stalled
  Conductor, at most three times an hour, then hold and park), G14 (the hold, after the third relaunch).
- **Park through the Steward:** a credential check that blocks (R10); hold on, disk low, power on battery.
- **Refuse:** P1 (it never reads a credential), P2, P13 (a relaunch never uses a bypass mode).

## Stop conditions

The watch loop ends only on SIGTERM or interrupt. If it is not running, whoever finds it so starts it again (step 1).
The Conductor's own `--once` check before each dispatch does not depend on the watch loop being up.

## Done means

Always on: a `monitor` heartbeat no older than about 300 seconds on the tracker, a note for every change of state, a
note for every repair and relaunch.
