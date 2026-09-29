---
artifact: PRAVAHA_EXECUTION_ARCHITECTURE
canonical_id: PRAVAHA_EXECUTION_ARCHITECTURE
version: "1.0"
status: ACTIVE
date: 2026-09-29
companion_to: PRAVAHA_CAMPAIGN_PLAN_v1_0.md
---

# Pravāha — execution architecture: the real-time tracker and the stream protocol

The native's first requirement for this campaign is a tracker that is **fully real-time, robust and resilient**.
The design answer is not to make a better report, but to make the tracker the thing the work runs *through*: the
streams take their next item from it, claim it, report each step to it and close it with evidence. A dashboard fed
that way cannot lag the work, because the work cannot proceed without writing to it.

## 1. Pieces

| Piece | Where | Role |
|---|---|---|
| Plan model | `00_ARCHITECTURE/control/pravaha/plan_model.json` | streams, phases, tracks, 68 items, 19 decisions; owners; dependencies; detectors. Edited only by the steward (or the native), always together with the plan document |
| Event log | `/Users/Dev/pravaha/run/EVENTS.jsonl` | append-only, one JSON line per state change, the single source of truth |
| Detectors | `platform/scripts/governance/pravaha_tracker/detectors.py` | check real sources — PR state and CI (`gh`), branch contents and merges (`git`), files on disk, production rows (read-only), the tracker's own health |
| Server | `pravaha_tracker/server.py` on `127.0.0.1:8766` | pure function of model + log + detectors + git activity, pushed to the page over Server-Sent Events |
| CLI | `/Users/Dev/pravaha/bin/pravaha` | the only way anyone reads or moves the campaign |
| Supervisor | launchd agent `com.madhav.pravaha.tracker` | starts at login, restarts on any exit |
| Tests | `pravaha_tracker/tests/test_pravaha.py` | 21 tests, including an end-to-end latency test through a real server |

## 2. What "done" means — earned signals (CLAUDE.md §N.8)

1. Where a detector exists, **the detector decides**. An event that claims done while the detector disagrees shows
   as a *conflict*, never done. A detector that cannot measure shows *unmeasured*, never done.
2. A decision item is done only when the native's ruling is recorded, with what was ruled.
3. A join is done only when everything it joins is done — no event can claim it.
4. An event-closed item is done only with evidence (refused at write time otherwise).
5. The CLI refuses, at write time: an unknown item or decision ID; one stream moving the other stream's item; a
   blocked/parked/failed state without a reason; a decision "decided" by anyone but the native or the steward quoting
   the native.

## 3. Real time — measured

| Path | Measured 2026-09-29 |
|---|---|
| `pravaha` command → event visible in `/api/state` | 0.93 s (most of it Python start-up; the engine ticks every 1 s) |
| Event → open browser | pushed on the next tick over SSE; a visible "alive" message every 5 s when nothing changes |
| An item event touching a detected item | that detector is re-measured on the same tick, not at its TTL |
| Stream git activity (last commit, branch, uncommitted files) | every 20 s, independent of emits |
| Detector TTLs | GitHub 2 min · git 1 min · files 15 s · database 1 min · http 10 s |

## 4. Resilience — tested

| Failure | Behaviour |
|---|---|
| Tracker process killed | launchd restarts it; measured back and serving in **0.3 s** after `kill -9` |
| Machine reboot / logout | launchd `RunAtLoad` starts it at login |
| Browser loses the stream | page falls back to polling every 5 s and says so in amber |
| Server unreachable | page says so in red with the age of the data it still shows |
| Server down when a stream emits | the event is still written to the log (the log is the truth); the tracker replays it on start; `pravaha next` reads the last saved snapshot and warns |
| Event log cannot be written | the CLI exits 3 and tells the stream to **stop work** and tell the native — invisible work must not continue |
| Two streams write at the same instant | one atomic `O_APPEND` write + `fsync` per line; tested with 400 concurrent lines, 0 malformed |
| Corrupt line in the log | skipped, counted, shown in the health strip |
| Log replaced or truncated | reader detects the new inode/size and re-reads |
| Bad edit to the plan model (syntax, dangling dependency, cycle, unknown owner/decision) | rejected; the last good model stays up; the error is shown |
| A detector crashes or its source is missing | that item shows *unmeasured*; everything else carries on |
| Database checks without credentials | shown as *unmeasured* until D-T1; never as done |
| Loss of the log file | a copy is taken every 10 minutes to `run/backup/EVENTS-<date>.jsonl` (14 kept) |
| A stream goes quiet with work running | marked *stale* after 15 min and *silent* after 45 min without a heartbeat; its commits still show |

**Known limits.** Local only (`127.0.0.1`); viewing from another device needs a decision on safe exposure. The plan
model is hand-kept; the steward checks it matches the plan document at every change. Database detectors need D-T1.

## 5. The stream protocol — every Kimi Code session follows it exactly

```
P=/Users/Dev/pravaha/bin/pravaha         # use the absolute path
export PRAVAHA_STREAM=A                   # or B — set once at session start
```

1. **Open.** `cd` into your stream's worktree, then `$P preflight`. If it fails (exit 4), fix what it says or stop.
   It checks the tracker is live, you are in your worktree, on an allowed branch, and the hold switch is off.
2. **Choose.** `$P next`. Work only on an item listed as READY (or one already RUNNING for you). Never start a
   WAITING item: its dependencies are not done.
3. **Claim before you work.** `$P start <ID> --detail "<what you are about to do>"`.
4. **Report as you go.** For items with steps: `$P step <ID> <step_name> --evidence "<commit|file|test>"` the moment
   each step is finished. For long work: `$P progress <ID> 0.4 --detail "..."`. Heartbeat at least every 10 minutes
   while working and after every long-running command: `$P heartbeat --detail "<what you are doing now>"`.
5. **Ask for review** when an item is a gate or needs an independent reviewer: `$P review <ID> --detail "..."`.
6. **Close with evidence**: `$P done <ID> --evidence "<PR #, commit, file path, test output>"`. For items with a
   detector, the detector must agree — if the dashboard shows *conflict*, your evidence and the detector disagree:
   investigate, do not argue with it.
7. **Blocked?** `$P block <ID> --detail "<exact reason and what would unblock it>"` immediately — then go back to step 2
   and take the next READY item. Never sit idle on a block.
8. **Need the native?** Write the decision's page into the decision packet (Stream B) or your escalation file
   (Stream A), then `$P request <D-ID> --detail "<path to the page>"`. Continue with other READY work.
9. **Measurements** (benchmarks, root counts, retrodiction scores): `$P metric <name> <value> --detail "<how measured>"`.
10. **Never** edit the plan model, never emit for the other stream's items, never mark a join or a decision item done.
    If the plan is wrong, write a note (`$P note --detail "..."`) and tell the native.
11. **If `pravaha` exits 3** (cannot write the event log): stop all work and tell the native.

## 6. Roles

| Role | Who | Writes |
|---|---|---|
| Stream A | Kimi Code session in A's worktree | A's items; heartbeats; metrics; decision requests |
| Stream B | Kimi Code session in B's worktree | B's items; heartbeats; metrics; decision requests |
| Native | you | decisions (`pravaha decide`); your own items (the #2731 merge is detected automatically) |
| Steward | the strategic Claude session | plan-model changes (with the plan document), notes, decisions recorded in your words (`--as steward`) |
| Tracker | the server | nothing — it only reads |

## 7. For the native — operating the tracker

| Want to | Do |
|---|---|
| See the campaign | open **http://127.0.0.1:8766** |
| Terminal summary | `/Users/Dev/pravaha/bin/pravaha status` |
| Record a ruling | `/Users/Dev/pravaha/bin/pravaha decide D-41 --detail "yes — as recommended"` |
| Pause all new work | `touch /Users/Dev/pravaha/run/PRAVAHA_HOLD` (preflight then refuses); resume: `rm` it |
| Restart the tracker | `launchctl kickstart -k gui/$(id -u)/com.madhav.pravaha.tracker` |
| Enable database checks (D-T1) | create a chmod-600 read-only env file, then `PRAVAHA_PGENV=<path> bash platform/scripts/governance/pravaha_tracker/install_launchd.sh` |
| Uninstall | `bash platform/scripts/governance/pravaha_tracker/install_launchd.sh --uninstall` |
| Logs | `/Users/Dev/pravaha/run/tracker.log`; events `/Users/Dev/pravaha/run/EVENTS.jsonl` |
| Run the tests | `cd platform/scripts/governance && python3 -m unittest pravaha_tracker.tests.test_pravaha` |
