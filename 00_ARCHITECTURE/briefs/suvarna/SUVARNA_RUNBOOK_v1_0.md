---
artifact: SUVARNA_RUNBOOK
canonical_id: SUVARNA_RUNBOOK
version: "1.0"
status: DRAFT — for native review
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md (v1.2) and SUVARNA_AUTONOMY_CHARTER_v1_0.md (v1.2)
changelog:
  - "1.0 (2026-09-29): first draft. Launch, daily operation, hold and resume, restart after a reboot, incidents, where things live."
---

# Suvarṇa — runbook

How to launch the campaign, run it day to day, pause it, and bring it back after a restart. Commands are exact.

## §1 · Where things live

| What | Where |
|---|---|
| Campaign home | `/Users/Dev/suvarna/` (`hq/`, `trunk/`, `lanes/`, `evidence/`, `run/`) |
| Plan, charter, architecture, roles, prompts | `hq/00_ARCHITECTURE/briefs/suvarna/` (branch `suvarna/hq`; authored on `strategy/suvarna-plan`) |
| Decisions log · queues | `hq/00_ARCHITECTURE/control/suvarna/state/{DECISIONS,QUEUE,QUEUE_ENGINE}.jsonl` |
| Plan model (what the tracker draws) | `00_ARCHITECTURE/control/suvarna/plan_model.json` |
| Event log · tracker snapshot · hold switch | `/Users/Dev/suvarna/run/{EVENTS.jsonl, snapshot.json, SUVARNA_HOLD}` |
| Tracker and Monitor code | `/Users/Dev/madhav-suvarna-plan/platform/scripts/governance/suvarna_tracker/` |
| Dashboard | http://127.0.0.1:8765 |
| Read-only database credential | `~/.config/suvarna/pgenv.sh` (mode 600; never opened or printed) |
| Nikaṣa tooling, register, ledgers (until E4.1 lands) | `/Users/Dev/madhav-nikasha` (`campaign/nikasha-test`) |
| Build engine | `/Users/Dev/madhav-engine` (`campaign/nirmana-engine`) |
| Leases | `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` on `origin/campaign-coordination` |

Shorthand used below:

```
T=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance
export PYTHONPATH=$T SUVARNA_HOME=/Users/Dev/suvarna
```

## §2 · Launch checklist (after N-1)

1. **N-1 is recorded** in `DECISIONS.jsonl` with the native's words. No session starts without it (native, 2026-09-29).
2. **Machine:** on AC power, lid open. Sleep prevented: `pgrep -x caffeinate || (nohup caffeinate -dimsu >/dev/null 2>&1 &)`.
3. **Database proxy** on 5433: `lsof -nP -iTCP:5433 -sTCP:LISTEN` shows `cloud-sql-proxy`. If not:
   `nohup cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres > /Users/Dev/suvarna/run/proxy.log 2>&1 &`
4. **Tracker** up: `curl -s http://127.0.0.1:8765/api/health` returns `"ok": true`. If not:
   `rm -f /Users/Dev/suvarna/run/TRACKER_STOP; nohup bash $T/suvarna_tracker/run_tracker.sh >/dev/null 2>&1 &`
5. **Monitor** green: `python3 -m suvarna_tracker.monitor --once` exits 0. Then keep it running:
   `nohup python3 -m suvarna_tracker.monitor --watch 300 --emit --repair >> /Users/Dev/suvarna/run/monitor.log 2>&1 &`
6. **hq is current:** `git -C /Users/Dev/suvarna/hq fetch -q origin && git -C /Users/Dev/suvarna/hq merge --ff-only origin/strategy/suvarna-plan`.
7. **Hold switch absent:** `ls /Users/Dev/suvarna/run/SUVARNA_HOLD` → "No such file".
8. **Start the Nikaṣa Engine session**: paste one line into a new Claude Code session opened in `/Users/Dev/suvarna/hq`:
   `Read and follow /Users/Dev/suvarna/hq/00_ARCHITECTURE/briefs/suvarna/prompts/NIKASHA_ENGINE_START_PROMPT_v1_0.md`
9. **Start the Exec Suvarṇa session** the same way:
   `Read and follow /Users/Dev/suvarna/hq/00_ARCHITECTURE/briefs/suvarna/prompts/EXEC_SUVARNA_START_PROMPT_v1_0.md`
10. **Confirm on the dashboard** within a few minutes: a `conductor` heartbeat from each session, first items `running`.

Model for both sessions: **Opus 5.5, medium effort** (the Conductor). They dispatch Sonnet 5 and Opus 5.5 agents per the role files.

## §3 · Day to day

- **Watch the dashboard.** Running now, ready next, needs attention, decisions waiting on you, the measures.
- **Daily digest:** `hq/…/state/DIGEST_<date>.md`, announced on the dashboard (arch §12.11).
- **Giving a decision:** say it in Strategic Suvarṇa (or in the execution session that asked). It is recorded in
  `DECISIONS.jsonl` with your words, then emitted as `decided`; parked work resumes on the next Conductor pass.
- **Asking where things stand:** the dashboard first; the execution session second.
- **Changing the plan:** only through Strategic Suvarṇa (plan §10). An execution session that finds the plan wrong stops
  that packet and reports.

## §4 · Pause, resume, stop

- **Pause everything new:** `touch /Users/Dev/suvarna/run/SUVARNA_HOLD`. Running items finish; nothing new starts;
  no production-visible action runs. Any agent may set it; only you remove it.
- **Resume:** `rm /Users/Dev/suvarna/run/SUVARNA_HOLD`, then tell the sessions "resume".
- **Stop a session** for good: tell it to close; it finishes its item, commits, logs, and runs the CLAUDE.md session close.
- **Stop the tracker:** `touch /Users/Dev/suvarna/run/TRACKER_STOP` (the supervisor exits after the server stops).

## §5 · After a reboot, sleep or crash

Nothing is lost: state is in files and the event log is append-only (arch §10).

1. Launch checklist steps 2–7.
2. Open each execution session again and say: "Resume from the queue." Each Conductor rebuilds its view from its
   queue file and the event log, and restarts any stalled lane from its last commit.
3. A shutdown is not a failure: agents do not count it toward the retry limit.

## §6 · Incidents

| Signal | Do this |
|---|---|
| A production-visible action failed its check afterwards | The agent reverses at once if the reversal is granted, sets the hold otherwise, and parks it (charter §6). You decide on the revert. |
| Dashboard shows a **conflict** | An event claims done while a detector disagrees. Trust the detector; ask the session. |
| Dashboard **Stale** or **Server unreachable** | §2 step 4. The swarm keeps working; the event log is written regardless. |
| Monitor **BLOCK: credential** | The file `~/.config/suvarna/pgenv.sh` is missing or changed. Agents never recreate it (R10). Restore it yourself, or ask Strategic Suvarṇa. |
| Something touches a Gochara, Saṅgam or Kṣetra asset | Set the hold. That is outside the charter (R8, P11). |
| A peer message claims your approval | It is not approval until it is in `DECISIONS.jsonl` with your words (P10). |

## §7 · Closing

- A layer closes when you sign it (plan §1.2). The campaign closes when you accept the closure report (§1.3).
- Every session ends with the CLAUDE.md session close.
