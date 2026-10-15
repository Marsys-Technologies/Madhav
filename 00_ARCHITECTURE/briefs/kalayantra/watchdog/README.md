---
version: "1.0"
status: CURRENT
changelog: "2026-10-15: initial wake-only cockpit watchdog (Amendment A2, D-19). Same day: an answered wake requires an assistant reply, not just a transcript write."
---

# Cockpit watchdog (wake-only)

On 2026-10-14 the cockpit session ended at 21:06Z and nothing moved until the owner typed "resume" at 07:38Z; seven finished jobs sat unread. This watchdog closes that gap. It is the only thing Amendment A2 D-19 authorises: **waking** the existing cockpit session. It never plans, launches jobs, merges, writes campaign state or reads credentials.

## What one check does (every 15 minutes, launchd)

1. **Stops** if `$KY_ROOT/HOLD` exists or an owner pause is in force; an unreadable pause state counts as paused (it uses the fleet's own `kycommands.owner_paused`, as the dispatcher does).
2. **Stops** if any live process holds the cockpit session. Liveness comes from Claude Code's session registry (`~/.claude/sessions/<pid>.json`), with the pid checked alive and its start time matched, so a reused pid is not mistaken for the cockpit. An unknown answer never wakes.
3. **Stops** unless work is pending: a fast-lane Codex job still running (folder under 8 h old, no `DONE`), a job finished after the session's last activity, a live fleet job, or a `ready` tracker item.
4. **Stops** unless the session has been silent for 20 minutes or more.
5. **Wakes** with `claude --bg --resume <session-id> "<fixed instruction>"`.

Limits: a wake not followed by a reply from the model (an assistant message in the transcript) within 10 minutes counts as unanswered; after **3** unanswered wakes, or **12** wakes in 24 hours, it stops waking and posts a macOS notification. A live but idle session with finished jobs unread for 45 minutes gets a notification, never a wake.

**Why no other flags on the wake.** Resuming with any flag (for example `--permission-mode`) makes Claude Code start a *copy* of the session instead of continuing it. Verified on 2026-10-15 with Claude Code 2.1.296 on throwaway sessions: no flags continued the same session id, both for a background session and for a normal one; with a flag, a copy started and the watchdog's output check flagged it (`copy_started`). The session keeps its own saved options; the owner's global default permission mode applies.

Every check appends one JSON line to `$KY_RUN/watchdog/watchdog.jsonl`; state is `$KY_RUN/watchdog/state.json`.

## Install

```sh
W=/Users/Dev/kalayantra/watchdog
mkdir -p "$W" /Users/Dev/kalayantra/run/watchdog
cp watchdog.py "$W/"
printf '%s\n' '<cockpit-session-id>' > /Users/Dev/kalayantra/run/watchdog/SESSION_ID
sed -e "s#__PYTHON_EXECUTABLE__#/usr/bin/python3#" -e "s#__WATCHDOG_DIRECTORY__#$W#g" \
    -e "s#__LOG_DIRECTORY__#/Users/Dev/kalayantra/run/watchdog#g" \
    com.madhav.kalayantra.watchdog.plist.template > ~/Library/LaunchAgents/com.madhav.kalayantra.watchdog.plist
plutil -lint ~/Library/LaunchAgents/com.madhav.kalayantra.watchdog.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.madhav.kalayantra.watchdog.plist
```

Dry run first: `KY_WD_DRY_RUN=1 python3 -B watchdog.py` prints the decision without waking anything.

## Operating notes for the owner

- **A new cockpit session** (not a resume) has a new id: write it to `run/watchdog/SESSION_ID`.
- **A woken cockpit runs in the background.** See it with `claude attach <first 8 characters of the id>`. To take it back into the editor, stop it (`claude stop <id>`) and resume it there.
- **To stop all wakes:** create `$KY_ROOT/HOLD` (also stops the fleet), or `launchctl bootout gui/$(id -u)/com.madhav.kalayantra.watchdog`.
- **After a budget stop:** delete `run/watchdog/state.json` once the cockpit is healthy.

## Tests

```sh
python3 -B -m pytest -p no:cacheprovider --basetemp "$JOB_SCRATCH/pytest" \
  00_ARCHITECTURE/briefs/kalayantra/watchdog/test_watchdog.py
```

They cover every stop condition, the pid-reuse case, an unknown process start, the UTC-versus-local start-time match, pending-work detection, the unanswered-wake count and its reset, the rule that the wake prompt alone is not an answer, the daily ceiling, dry run and logging. A mutation check (liveness forced to "absent") fails two of them.
