---
version: "1.1"
status: READY_FOR_COCKPIT_REVIEW
changelog: "2026-10-15: Amendment A2 D-21 — one percentage, wave lines, scope markers, closure classes and agent-hours per closure; 2026-10-14: initial read-only dashboard."
---

# Kāla project progress

A plain-language owner view of the live campaign. Python 3's standard library runs the server; the page contains its own CSS, JavaScript and SVG. It reads the existing tracker, completion events and job records. It does not alter campaign state, install anything or write a disk cache.

## Run

From this directory:

```sh
python3 -B server.py
```

Open <http://127.0.0.1:8768/>. `/api/summary` serves the computed summary, cached in memory for at most five seconds. The page refreshes every ten seconds without reloading. Stop the foreground server with Ctrl-C.

Only `/` and `/api/summary` are served. Unsupported routes return 404; mutations are not implemented. Binding is always `127.0.0.1`. No external scripts, fonts, images or analytics are loaded. Exceptions are displayed as source unavailability without returning paths, commands, credentials or raw error messages. Process command lines are examined in memory and never returned by the API.

| Environment variable | Default |
| --- | --- |
| `KY_PROGRESS_PORT` | `8768` |
| `KY_PROGRESS_TRACKER_URL` | `http://127.0.0.1:8767/api/state` |
| `KY_PROGRESS_EVENTS` | `/Users/Dev/kalayantra/run/EVENTS.jsonl` |
| `KY_PROGRESS_DIRECT_JOBS` | `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs` |
| `KY_PROGRESS_FLEET_JOBS` | `/Users/Dev/kalayantra/run/jobs` |

Tracker URLs must use HTTP on loopback without authentication. File and job-directory overrides are read-only inputs. No `.env` or credential file is loaded. `ps -axo pid=,command=` supplies process evidence.

## Source and calculation rules

The tracker response was inspected on 2026-10-14 and 2026-10-15. Its `tracks[].items[]` supplies the scope and current statuses; `generated_at` supplies the observation time. `native_queue` supplies owner waits. The response shapes are grounded in `platform/scripts/governance/pravaha_tracker/state.py:378`–`:390`. The tracker’s `overall.pct` is weighted partial progress (`state.py:378`), so this dashboard computes the requested percentage independently.

- Complete = `done + not_applicable`; percentage = complete / total × 100. The page displays this percentage once, with three complete / total count rows: Wave 4 (all `J-*`, including `J-W4-*` joins), everything else, and total. `V-J6` belongs to everything else under the job’s explicit ID rule. The competing done / total metric is removed.
- In progress includes `running` and `review`. Stuck includes `blocked` and `parked`, while the individual chips distinguish Stuck from Set aside.
- Deferred is its own bucket: a tracker row flagged `deferred: true` (triage class b, outside the acceptance closure, not finished; the 13 of SR-PARKED-OUT-OF-CAMPAIGN and the other deferrals) whose status is `blocked`, `parked` or `unknown` is counted in `metrics.deferred` and listed in `deferred`, never in `stuck`, `waiting` or `attention`. It is never counted as done; `total` and `percent` are unchanged.
- Closure counts and recent completions use the earliest recorded `kind=item, state=done` event for each item, filtered to items currently done in the tracker. A reopened item is removed from history, pace and recent completions. No inferred completion date is substituted. The chart also includes dated `not_applicable` events, so every completion line uses done + not applicable. Complete items without dates are disclosed, never backdated.
- Closure classes use tracker `completion_kind` (`platform/scripts/governance/pravaha_tracker/state.py:27`, `:312`): `V-*` checkpoints → verdict; `J-0*` → planning; other `code` → capability; other artifacts, joins, decisions and untyped items → planning. Each dated done item contributes once to exactly one class. Registry implementation declared `code` remains capability work.
- The chart has three cumulative completion lines, plus a dashed total-scope line. The exact 152 → 213 marker at 2026-10-14 19:04 UTC comes from `origin/kalayantra/velocity-a2:00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A2_VELOCITY.md:70`. Later changes are detected from consecutive successful tracker observations and labelled with observation times. Markers appear only once their time has passed. Additional observations are kept in memory, not persisted across restarts. No Wave 4 historical denominator is invented.
- Agent-hours sum each completed `X-*` job’s full elapsed duration from its UTC folder timestamp to `DONE` mtime; the rolling window contains the finish time. This includes unsuccessful jobs, reviews and fixes. Divide that sum by the recorded done closures in the same window. No closures gives null rather than zero or infinity. Missing or invalid timing gives null ratios without discarding closure counts. The supported source is the fast-lane direct-job folder; fleet jobs without this timing contract are outside the measure.
- Tracker requests allow 120 seconds because the live source can be slow; the page allows 130 seconds before showing a request failure.
- The event reader remembers inode and byte offset, processes only appended complete lines, retries an unfinished last line, and resets on replacement or truncation. A malformed complete record makes history unavailable; an unreadable source never becomes an empty history.
- Source availability is independent. A failed tracker gives null progress fields, not zero counts or cached progress. Failed history gives null historical metrics while preserving current tracker counts. Failed job/process coverage gives a null total agent count; independently observed agents may still be listed. Every unavailable source displays “data unavailable since” its first consecutive failed check, cleared on recovery.
- Age refers to the tracker’s observation time, not the dashboard’s response time. Above one minute the live indicator is amber; above five it is red. Delayed data is explicitly labelled as the last known figures. A tracker or dashboard request failure clears current progress and turns the indicator red.

## Explicit interpretations and limitations

These choices fill details the task and plan do not specify; none changes campaign state:

1. **(I) INTERPRETATION — plain titles.** The `TITLES` and `TRACK_TEXT` presentation mappings condense the actual tracker titles and track descriptions into owner language. They identify the same tasks and describe work, never acceptance. Unknown IDs use the source title, shortened and with file references removed. Reasons keep the first recorded sentence, shortened to 220 characters; missing reasons say that none was recorded.
2. **(I) INTERPRETATION — date boundaries and projection.** Historical days use UTC. “Last 24 hours” and “last 7 days” are rolling windows. Pace is recorded, currently-done completions in seven days / 7. Projection adds `ceil(remaining / pace)` calendar days to today; zero or unavailable pace gives no date. Historical scope uses the known A2 change and changes observed during the current server run. Before the first known change the dashed line uses its recorded “before” size; other earlier changes remain unknown. With no known change, only current scope is known. Historical days use dated complete events; closure velocity uses done events only.
3. **(I) INTERPRETATION — incomplete historical coverage.** Currently-complete items without a completion event remain complete, but their date is unknown. The chart explicitly states the number of undated items; history, recent completions, rolling counts, pace and projection cover recorded events only. The 2026-10-15 live check had 60 dated complete items (58 done, two not needed) and ten undated complete items. This is an evidence gap, not a source read failure or a fabricated date.
4. **(I) INTERPRETATION — engine status.** The live health shape has `hold` and `engine_tick_age_s` (`platform/scripts/governance/pravaha_tracker/server.py:223`–`:227`), not an emergency flag. `hold=true` means Paused. `hold=false` and tick age below ten seconds means the tracker engine is Running, following its own detector (`server.py:382`). An explicit future `emergency_hold=true` is shown as Emergency hold. Otherwise status is unavailable; Running does not assert that campaign workers are active. No emergency status is inferred from age or error text.
5. **(I) INTERPRETATION — job lifecycle and liveness.** Direct Codex jobs require no `DONE` and a `codex exec` process whose argv contains the exact folder or a file below it. A sibling with a common prefix is excluded. Their heading supplies the label and item IDs only when explicitly present in the heading or a named Item/Items under review/Packet line. Finished direct job status comes from `result.json`. Fleet jobs recognise `live`, `running`, `terminating`, `prepared`, `ended` and `launch_failed`, grounded in `fleet/kyd_jobs.py:24` and `fleet/kyboot.py:2364`–`:2419`; a working engine process at the recorded PID is additionally required. Duplicate PIDs count once. This checks current process presence and engine, not the full launch identity or surviving process groups. Unrecognised lifecycle values or a recorded PID belonging to an unrecognised process make that source unavailable. Missing plain fleet labels remain honestly unavailable rather than inferred from a job-folder nickname.
6. **(I) INTERPRETATION — timing on review items.** “Work began” uses `started_at`, falling back to `updated_at`; it does not claim that the review itself began then. Agent duration comes from the direct folder timestamp or fleet `started_at`.

7. **(I) INTERPRETATION — closure classes.** The tracker’s code/artifact declarations determine capability vs planning, with the explicit `V-*` and `J-0*` rules above taking precedence. Untyped joins and decisions count as planning rather than claiming code delivery; no title-based guess reclassifies registration code.
8. **(I) INTERPRETATION — agent effort.** A2’s campaign-wide 45 hours / eight closures (`00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A2_VELOCITY.md:21`–`:22`, `:72`, on `origin/kalayantra/velocity-a2`) is interpreted as all completed direct-job time divided by recorded closures, not only jobs attributable to already-closed items. Multi-item review jobs and packet IDs do not provide a reliable per-item allocation. Whole durations enter the finish-time window; overlapping agents add their hours. This is elapsed job time, not CPU time. A late `DONE` marker increases the estimate, and missing historical job folders can lower it. Active jobs and fleet jobs without `DONE` are excluded. Cockpit question: should a future canonical effort source supply execution-end times and per-item attribution?


The earned-signal requirement is `CLAUDE.md:139`–`:142` (§N.8). Missing-source/coverage-as-unknown is also explicit in `KALAYANTRA_RELAUNCH_PLAN_v2_7.md:666`–`:677`. The owner’s installation rule is `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md:81`–`:84` (D-9). This dashboard does not alter any of those controls or independently certify the campaign.

Open questions for the cockpit: should the tracker expose an explicit emergency-hold state? Should undated decision/join completions gain their own canonical completion events? Should fleet jobs publish a plain work label and full process-identity evidence? The page handles each gap today without inventing it. Should the tracker retain scope snapshots across dashboard restarts and expose historical per-wave membership?


## Tests

Pytest is only a test-runner dependency, not a server dependency. Run from the working-copy root, with a job-local absolute `JOB_SCRATCH`:

```sh
python3 -B -m pytest -p no:cacheprovider \
  --basetemp "$JOB_SCRATCH/pytest" \
  00_ARCHITECTURE/briefs/kalayantra/progress/test_progress.py
```

Fixtures cover D-21 wave partition and complete counts, exact-time scope markers and later observed changes, dated not-needed completions, closure classes and rolling boundaries, job durations, zero closures and unavailable timing, the actual inline page render (via the macOS system JavaScriptCore framework, skipped on other systems), completion percentage, track counts, rolling windows, pace and projected date, burn-up values, reopened items, missing dates, incremental appends and partial lines, log replacement, malformed events, source outages, failure recovery, bounded caching, direct job result states, process/path matching, fleet terminal/unknown states, and earned engine status. All temporary fixtures belong under the job folder.

## Live check (2026-10-15)

A foreground server on `127.0.0.1:8878` returned HTTP 200 for the page and `/api/summary`, reading the live tracker, events and jobs. It was stopped after the check. Observation: `2026-10-15T09:15:32Z`.

```text
Complete: 70 / 213 = 32.9% (68 done + 2 not needed)
Wave 4: 6 / 96; everything else: 64 / 117; total: 70 / 213
Closures in 24 h: 3 capability, 4 verdict, 1 planning = 8
Closures in 7 d: 20 capability, 4 verdict, 2 planning = 26
Agent-hours per closure: 14.57 (24 h), 6.25 (7 d)
Scope marker: 152 → 213 at 2026-10-14 19:04 UTC
History coverage: 60 dated complete; 10 complete without usable dates
All six source checks available
```

The 24-hour numerator is 116.58 elapsed job-hours. Several overnight jobs received their `DONE` markers together around 07:38:55 UTC, producing 10–12-hour elapsed durations. The dashboard follows the requested folder-to-`DONE` calculation and discloses this limitation rather than substituting the amendment’s older approximate 45-hour figure.

## Launchd template

`com.madhav.kalayantra.progress.plist.template` is a template only. The cockpit must substitute the absolute reviewed Python executable, installed progress directory and approved log directory for the three `__…__` placeholders before validating and installing it. It uses `-B`, port 8768 and a loopback-only server, with launchd restart throttling. The dashboard server writes no files; launchd owns any redirected stdout/stderr. No launchd command was run by this job.
