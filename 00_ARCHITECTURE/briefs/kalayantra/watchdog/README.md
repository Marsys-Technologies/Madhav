---
version: "1.0"
status: CURRENT
changelog: "2026-10-20: page the owner surrogate when the cockpit has had no turn for 45 min with work pending (line three). 2026-10-20: a live but idle cockpit with work waiting gets a nudge file (SR-IDLE-NUDGE). 2026-10-15: initial wake-only cockpit watchdog (Amendment A2, D-19). Same day: an answered wake requires an assistant reply, not just a transcript write."
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

**Nudge for a live, idle cockpit (SR-IDLE-NUDGE, 2026-10-20).** Root cause of the 20:49Z-23:47Z stall on 2026-10-19: the cockpit was live but idle with 15 finished jobs unread, and the watchdog (which only resumes a dead session) did nothing. Now, when the session is **live**, its registry status is `idle`, it has been silent for 20 minutes or more (`KY_WD_NUDGE_IDLE_MIN`), and there are unread finished jobs or a non-empty `fast/BACKLOG.txt` or `fast/ARM_ORDER.txt` (non-blank lines that do not start with `#`; directory `KY_WD_FAST_DIR`, default the parent of the fast jobs folder), the watchdog leaves one nudge, at most every 30 minutes (`KY_WD_NUDGE_EVERY_MIN`): `<N> finished jobs unread; backlog <M>; arm-order <K>; act`. It logs action `nudge`. **Channel:** there is no script-callable way to send a message into a running session (the `SendMessage` tool belongs to the model; resuming a live session with a prompt starts a copy), so the nudge is written to `$KY_RUN/watchdog/NUDGE.txt` (one line, timestamped, overwritten); the cockpit's loop reads that file. No resume, no flags, no second session.

**Page to the owner surrogate (line three, 2026-10-20).** Lines one and two are the cockpit's own 10-minute check-in and the nudge above. Line three covers the case where the cockpit itself is not answering: when the cockpit session has had no turn for 45 minutes or more (`KY_WD_PAGE_IDLE_MIN`; measured as the nudge measures it, from the transcript's last write, whatever the liveness or registry status) AND any of `fast/ARM_ORDER.txt`, `fast/BACKLOG.txt` or an ungated item in `fast/FOLLOWUPS.md` (a `- [ ]` line with none of the words after/when/once/until/pending/held) is non-empty, the watchdog pages the owner surrogate session (`KY_WD_PAGE_SESSION`, default `madhav-6d`), at most every 45 minutes (`KY_WD_PAGE_EVERY_MIN`). Same channel as the nudge: one overwritten line in `$KY_RUN/watchdog/PAGE_SURROGATE.txt`, plus a log line with action `page-surrogate`. If `fast/CONDUCTOR_HEARTBEAT` (a UTC timestamp the conductor writes each tick) is older than 10 minutes (`KY_WD_HEARTBEAT_STALE_MIN`), or missing/unreadable, the page says so; a stale heartbeat alone never pages. No resume, no copy, no flags; held (HOLD/pause) ticks never page.

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

They cover every stop condition, the pid-reuse case, an unknown process start, the UTC-versus-local start-time match, pending-work detection, the unanswered-wake count and its reset, the rule that the wake prompt alone is not an answer, the daily ceiling, dry run and logging, and the nudge (once per 30 minutes under the condition; none when not idle, busy or nothing pending; none and an unchanged wake for a dead session), and the page (sent under the condition, rate-limited to one per 45 minutes, none when nothing is pending or the cockpit was quiet under 45 minutes, stale-heartbeat text, dry run writes no file, the wake path unchanged). A mutation check (liveness forced to "absent") fails two of them.
