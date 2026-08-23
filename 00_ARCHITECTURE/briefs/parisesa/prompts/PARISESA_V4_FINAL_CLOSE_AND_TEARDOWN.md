# PARIŚEṢA-V4 — Final Session Close & Infrastructure Teardown

**Owner decision, confirmed:** the 6+1 native-scoped closure (F-142-CANDIDATE, F-145,
F-156, F-159, F-165, F-166, F-75-batch) is complete and correct. The remaining 6
`DATA_PARKED` findings (F-104, F-151, F-189, F-23, F-35, F-63) and 4 `EXTERNAL_HOLD`
findings (F-141, F-21, F-52, RATE-07-ENABLE) are to stay exactly as they are —
**deliberately left open by owner instruction, not a gap and not backlog to keep
working.** This session is closing now, on purpose, not because the work ran out.

**Run this from inside the live conductor session** (attach via `claude agents` or
`tmux attach -t parisesa`) — the documentation step needs real conductor session
identity and continuity, not a fresh unrelated session.

## Part A — Record the closure decision honestly, don't just stop silently

1. Do **not** touch, re-triage, investigate further, or advance any of the 10
   `DATA_PARKED`/`EXTERNAL_HOLD` findings listed above. Reading their current state to
   quote it accurately in the record below is fine; no new work on any of them.
2. Append one journal entry recording plainly: the owner directly instructed this
   session to close now; the 6+1 native-scoped batch is complete and verified; the 10
   remaining `DATA_PARKED`/`EXTERNAL_HOLD` findings are intentionally left in their
   current state by explicit owner decision — not because work ran out, was blocked, or
   was forgotten. State clearly that a future session should not resume work on this
   campaign, including those 10 findings, without a fresh, explicit owner go-ahead.
   Match the journal's existing entry conventions (check the last few entries for the
   right event shape) rather than inventing a new schema.
3. Update `heartbeat.json` and `RESUME.md` one final time as the authoritative closing
   record. Near the top of `RESUME.md`, state plainly: **campaign CLOSED BY OWNER
   DECISION as of this session**; list the 10 open findings and their exact statuses;
   state that no further autonomous work should be dispatched against this campaign
   without new, explicit owner authorization.
4. Do **not** title anything a "closure report" implying the backlog is exhausted —
   it isn't, on purpose. If a standalone closing document feels warranted, name it
   plainly as an owner-directed pause (e.g. `SESSION_CLOSE_20260822.md`), not
   `CLOSURE_REPORT_*`, so nobody later mistakes this for full completion.

## Part B — Stop anything that would try to nudge this campaign back to life

5. Check current state: `launchctl list | grep marsys`.
6. Find the real plist filenames rather than assuming them:
   `ls ~/Library/LaunchAgents/ | grep marsys`
7. Unload the watchdog and caffeinate jobs for this campaign only:
   ```
   launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/<the parisesa-v4-watchdog plist found above>
   launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/<the parisesa-v4-caffeinate plist found above>
   ```
   (if this system uses the older syntax, `launchctl unload <plist>` instead — check
   which form actually applies before running either.)
8. Confirm both are gone: `launchctl list | grep marsys` should return nothing.
9. Do **not** touch any `com.marsys.pariprashna-*` jobs or anything outside the
   `com.marsys.parisesa-v4-*` names — PARIPRAŚNA is a separate, unrelated campaign.
10. Set `STOP.flag` in the conductor worktree root as a belt-and-suspenders marker:
    ```
    echo "Closed by owner instruction, 2026-08-22. Do not resume without explicit new owner go-ahead. See RESUME.md." > STOP.flag
    ```

## Part C — Confirm, then stop. Leave the very last step to the human.

11. Print a clear final summary: what was recorded in the journal/RESUME.md,
    confirmation both launchd jobs are unloaded, confirmation `STOP.flag` is set.
12. Do **not** attempt to kill your own tmux session or exit yourself. Ending your own
    process from inside itself isn't confirmable — that step belongs outside, typed by
    the owner, after seeing your summary.

---

## What the owner does last, in a separate terminal, once the above confirms

```
tmux kill-session -t parisesa
tmux ls
```
The second command should show no `parisesa` session (or "no server running") — that's
confirmation the whole setup is torn down.

Then verify no stray process remains:
```
ps aux | grep -i "parisesa-v4-conductor" | grep -v grep
```
This should return nothing. If it does, note the PID and stop before killing anything —
don't assume.
