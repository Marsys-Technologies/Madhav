---
version: "1.0"
status: READY_FOR_COCKPIT_REVIEW
changelog: "2026-10-14: initial read-only owner progress dashboard."
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

The tracker response was inspected on 2026-10-14. Its `tracks[].items[]` supplies the scope and current statuses; `generated_at` supplies the observation time. `native_queue` supplies owner waits. The response shapes are grounded in `platform/scripts/governance/pravaha_tracker/state.py:378`–`:390`. The tracker’s `overall.pct` is weighted partial progress (`state.py:378`), so this dashboard computes the requested percentage independently.

- Complete = `done + not_applicable`; percentage = complete / total × 100. The headline separately reports actual done / total and how many items were not needed.
- In progress includes `running` and `review`. Stuck includes `blocked` and `parked`, while the individual chips distinguish Stuck from Set aside.
- Completion history uses the first `kind=item, state=done` event encountered for each item, filtered to items currently done in the tracker. A reopened item is removed from history, pace and recent completions. No inferred completion date is substituted.
- The event reader remembers inode and byte offset, processes only appended complete lines, retries an unfinished last line, and resets on replacement or truncation. A malformed complete record makes history unavailable; an unreadable source never becomes an empty history.
- Source availability is independent. A failed tracker gives null progress fields, not zero counts or cached progress. Failed history gives null historical metrics while preserving current tracker counts. Failed job/process coverage gives a null total agent count; independently observed agents may still be listed. Every unavailable source displays “data unavailable since” its first consecutive failed check, cleared on recovery.
- Age refers to the tracker’s observation time, not the dashboard’s response time. Above one minute the live indicator is amber; above five it is red. Delayed data is explicitly labelled as the last known figures. A tracker or dashboard request failure clears current progress and turns the indicator red.

## Explicit interpretations and limitations

These choices fill details the task and plan do not specify; none changes campaign state:

1. **(I) INTERPRETATION — plain titles.** The `TITLES` and `TRACK_TEXT` presentation mappings condense the actual tracker titles and track descriptions into owner language. They identify the same tasks and describe work, never acceptance. Unknown IDs use the source title, shortened and with file references removed. Reasons keep the first recorded sentence, shortened to 220 characters; missing reasons say that none was recorded.
2. **(I) INTERPRETATION — date boundaries and projection.** Historical days use UTC. “Last 24 hours” and “last 7 days” are rolling windows. Pace is recorded, currently-done completions in seven days / 7. Projection adds `ceil(remaining / pace)` calendar days to today; zero or unavailable pace gives no date. The total chart line shows today's scope because historical scope totals are not supplied. Items marked not needed count as complete but are outside the done-event chart.
3. **(I) INTERPRETATION — incomplete historical coverage.** Currently-done items without a done event remain complete, but their date is unknown. The chart explicitly states the number of undated items; history, recent completions, rolling counts, pace and projection cover recorded events only. The inspected live snapshot had 44 dated done items and nine undated done items. This is an evidence gap, not a source read failure or a fabricated date.
4. **(I) INTERPRETATION — engine status.** The live health shape has `hold` and `engine_tick_age_s` (`platform/scripts/governance/pravaha_tracker/server.py:223`–`:227`), not an emergency flag. `hold=true` means Paused. `hold=false` and tick age below ten seconds means the tracker engine is Running, following its own detector (`server.py:382`). An explicit future `emergency_hold=true` is shown as Emergency hold. Otherwise status is unavailable; Running does not assert that campaign workers are active. No emergency status is inferred from age or error text.
5. **(I) INTERPRETATION — job lifecycle and liveness.** Direct Codex jobs require no `DONE` and a `codex exec` process whose argv contains the exact folder or a file below it. A sibling with a common prefix is excluded. Their heading supplies the label and item IDs only when explicitly present in the heading or a named Item/Items under review/Packet line. Finished direct job status comes from `result.json`. Fleet jobs recognise `live`, `running`, `terminating`, `prepared`, `ended` and `launch_failed`, grounded in `fleet/kyd_jobs.py:24` and `fleet/kyboot.py:2364`–`:2419`; a working engine process at the recorded PID is additionally required. Duplicate PIDs count once. This checks current process presence and engine, not the full launch identity or surviving process groups. Unrecognised lifecycle values or a recorded PID belonging to an unrecognised process make that source unavailable. Missing plain fleet labels remain honestly unavailable rather than inferred from a job-folder nickname.
6. **(I) INTERPRETATION — timing on review items.** “Work began” uses `started_at`, falling back to `updated_at`; it does not claim that the review itself began then. Agent duration comes from the direct folder timestamp or fleet `started_at`.

The earned-signal requirement is `CLAUDE.md:139`–`:142` (§N.8). Missing-source/coverage-as-unknown is also explicit in `KALAYANTRA_RELAUNCH_PLAN_v2_7.md:666`–`:677`. The owner’s installation rule is `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md:81`–`:84` (D-9). This dashboard does not alter any of those controls or independently certify the campaign.

Open questions for the cockpit: should the tracker expose an explicit emergency-hold state? Should undated decision/join completions gain their own canonical completion events? Should fleet jobs publish a plain work label and full process-identity evidence? The page handles each gap today without inventing it.

## Tests

Pytest is only a test-runner dependency, not a server dependency. Run from the working-copy root, with a job-local absolute `JOB_SCRATCH`:

```sh
python3 -B -m pytest -p no:cacheprovider \
  --basetemp "$JOB_SCRATCH/pytest" \
  00_ARCHITECTURE/briefs/kalayantra/progress/test_progress.py
```

Fixtures cover completion percentage, track counts, rolling windows, pace and projected date, burn-up values, reopened items, missing dates, incremental appends and partial lines, log replacement, malformed events, source outages, failure recovery, bounded caching, direct job result states, process/path matching, fleet terminal/unknown states, and earned engine status. All temporary fixtures belong under the job folder.

## Launchd template

`com.madhav.kalayantra.progress.plist.template` is a template only. The cockpit must substitute the absolute reviewed Python executable, installed progress directory and approved log directory for the three `__…__` placeholders before validating and installing it. It uses `-B`, port 8768 and a loopback-only server, with launchd restart throttling. The dashboard server writes no files; launchd owns any redirected stdout/stderr. No launchd command was run by this job.
