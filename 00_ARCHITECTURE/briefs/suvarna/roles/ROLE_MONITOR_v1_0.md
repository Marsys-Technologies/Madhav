---
artifact: SUVARNA_ROLE_MONITOR
canonical_id: SUVARNA_ROLE_MONITOR
version: "1.0"
status: "DRAFT — for native review"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.0 (2026-09-29): first draft, from arch §3.1, §5.4, §8, §11.3, charter G15, R10, §10 and platform/scripts/governance/suvarna_tracker/monitor.py."
---

# Role · Monitor

Read `ROLE_COMMON_v1_0.md` first. It holds the shared rules; this file does not repeat them.

## Who you are

The Monitor is a script, not a model (arch §3.1: "no model — a script"). It checks the environment the swarm runs in,
repairs what it is allowed to, and writes what it sees to the event log. This file is for the agent that starts it
(the Conductor, at session open) and for every role that reads its output. Always on, one instance, serving both
execution sessions (charter §1 binds both).

## Inputs

- `platform/scripts/governance/suvarna_tracker/monitor.py`. Environment: `SUVARNA_HOME=/Users/Dev/suvarna`; the
  credential path defaults to `~/.config/suvarna/pgenv.sh`, which the script only `stat`s and never opens.

## What it does

1. **Start it once**, detached, if it is not already running:
   `PYTHONPATH=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna python3 -m suvarna_tracker.monitor --watch 300 --emit --repair`
2. **Seven checks** every 300 seconds, each `ok`, `warn` or `block` (arch §8): database proxy on port 5433; credential
   file present and owner-only; power (battery below 50% blocks); sleep prevented; hold switch absent; disk (below
   5 GB blocks, below 20 GB warns); tracker `/api/health`. A check that cannot measure reports `warn`, never `ok`.
3. **Repairs** (`--repair`, G15), only when the process is verifiably not running: restart the database proxy on 5433
   (never a proxy on another workstream's port), the tracker supervisor (`run_tracker.sh`), and `caffeinate`. With the
   hold switch on, it repairs nothing.
4. **Never touches** the credential, the hold switch, disk or power (G15, R10). Those are reported, and the Steward
   parks them. A missing or changed credential file is never recreated (charter §10).

## Pausing dispatch

- The Monitor does not stop other agents itself. **Before each dispatch the Conductor runs**
  `python3 -m suvarna_tracker.monitor --once` (same environment) **and dispatches nothing on exit 2 (block)** (arch §8).
- On a block the Conductor emits the pause, and the resume, as `note` events (ROLE_CONDUCTOR step 2). Items already
  running finish.
- **Stalls** (no progress for 10 minutes, charter §10) and the **spend meter** (arch §9) are assigned to the Monitor but
  `monitor.py` does not measure them today (ROLE_COMMON open question 9). Do not improvise them.

## Outputs and where they go

- `$SUVARNA_HOME/run/monitor_state.json` (the last non-ok set); `$SUVARNA_HOME/run/proxy.log` for a proxy it started.
- Events in `$SUVARNA_HOME/run/EVENTS.jsonl` (below).

## Report as it happens

With `--emit` the script writes, as actor `monitor`:
- a `heartbeat` every pass (`ok: 7/7`, or `WARN: …` / `BLOCK: …` listing the non-ok checks);
- a `note` when the set of non-ok checks changes, including when it clears;
- a `note` per repair taken (`repair: …`).
It does not emit `blocked` item events (arch §11.3 assigns them; ROLE_COMMON open question 9).
If the monitor's own emit fails, its output shows `emit errors`: treat that as the log being unwritable (P12) and stop
dispatch until it is fixed.

## Authority

- **Acts under:** G15 (repair the database proxy, the tracker supervisor and sleep prevention).
- **Park through the Steward:** credential missing or changed (R10); hold on, disk low, power on battery.
- **Refuse:** P1 (it never reads the credential), P2.

## Stop conditions

The watch loop ends only on SIGTERM or interrupt. If it is not running, the Conductor starts it again (step 1). The
Conductor's own `--once` check before each dispatch does not depend on the watch loop being up.

## Done means

Always on: a `monitor` heartbeat no older than about 300 seconds on the tracker, a note for every change of state, and
a note for every repair.
