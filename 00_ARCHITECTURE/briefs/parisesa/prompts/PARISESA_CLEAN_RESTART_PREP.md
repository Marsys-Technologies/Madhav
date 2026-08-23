# PARIŚEṢA-V4 — Clean Kill & Restart Prep (paste into your OUTSIDE-tmux Claude Code session)

**Run this from your separate, already-logged-in Claude Code CLI session — the
plain Terminal window you used earlier for `/login`, outside tmux.** Do NOT run
this from inside the `parisesa` tmux session itself: part of this prep kills
that tmux session, which would cut you off mid-task if you were running from
inside it.

Your job is prep only. **Stop before actually launching the resumed session** —
you (the agent) cannot hand the human an attached, interactive `claude`
process; that final step has to be typed by the human in their own terminal.
Do the discovery, the safe kill, and the fresh tmux setup, then print the
exact command and stop.

## Part A — Discover, don't guess

1. Check `STOP.flag` in the conductor worktree root
   (`/Users/Dev/par-night/parisesa-v4-conductor/STOP.flag`). If it exists, halt
   immediately and report it — clearing it is the owner's decision alone,
   never yours. Do not proceed past this step if present.
2. Quick network sanity check, since the user reported the stuck session
   claiming a network issue while the network was fine outside it:
   ```
   ping -c 3 github.com
   curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://api.github.com
   ```
   Report the actual results plainly — don't assume either way.
3. Find the real PID of the stuck conductor process. Grep by the campaign's
   actual working directory string, not a bare `claude` match, so you can't
   accidentally hit an unrelated session (your own outside-tmux session, the
   watchdog, or the separate PARIPRAŚNA campaign):
   ```
   ps aux | grep -i "parisesa-v4-conductor" | grep -v grep
   ```
   - If this returns **zero** lines: the process is already gone; skip to
     Part C.
   - If it returns **more than one** line: stop and report all of them
     verbatim — do not pick one to kill on your own judgment.
   - If it returns exactly one line: note the PID (second column).
4. Check current tmux state: `tmux ls`. Note whether `parisesa` is listed.
5. Check the watchdog/caffeinate launchd jobs are still alive independently
   of this (they run as separate services and shouldn't be touched, just
   observed): `launchctl list | grep marsys`.

## Part B — Kill only the confirmed PID

6. `kill <pid>` (the one PID confirmed in step 3). Wait ~5 seconds.
7. Re-run the same grep from step 3 to confirm it's gone. If it's still
   listed, escalate: `kill -9 <pid>`, then confirm again.
8. Do not touch any other `claude` process you may see running — only the
   one PID confirmed in step 3.

## Part C — Kill and recreate tmux (only if `parisesa` still exists per step 4)

9. `tmux kill-session -t parisesa`
10. Confirm via `tmux ls` that `parisesa` no longer appears.
11. Create a fresh detached session and pre-position it in the right
    directory (detached, since you're not the one who will attach — the
    human will):
    ```
    tmux new -d -s parisesa
    tmux send-keys -t parisesa "cd /Users/Dev/par-night/parisesa-v4-conductor" Enter
    ```

## Part D — Read the fresh session id, don't trust memory

12. Read the current heartbeat state fresh — the id may have changed since
    it was last known as `a12a4293-...`:
    ```
    cat /Users/Dev/par-night/parisesa-v4-conductor/00_ARCHITECTURE/briefs/parisesa/state/heartbeat.json
    ```
    Extract whatever field holds the Claude session id. Explicitly say
    whether it matches `a12a4293-...` or is different.
13. Also `cat` the current `RESUME.md` in the same directory in case it notes
    anything relevant to how this specific resume should be started.

## Part E — Stop here. Report, don't launch.

14. Do **not** run `claude --resume` yourself, and do not use `--continue` or
    `--fork-session` under any circumstance.
15. Give the human, in plain language:
    - Network check result (step 2).
    - Whether `STOP.flag` was present (and if so, that you halted).
    - The PID situation: found/killed cleanly, needed `-9`, was already gone,
      or was ambiguous (multiple matches — report which, untouched).
    - Whether tmux had to be killed and recreated, or was already gone.
    - The session id read fresh from `heartbeat.json`, flagged clearly if it
      differs from `a12a4293-...`.
    - The exact two commands to type themselves, in order:
      ```
      tmux attach -t parisesa
      claude --resume <the fresh session id from step 12>
      ```
16. Nothing else. Do not investigate campaign substance, ledger state, or PR
    status in this session — that's the resumed conductor's job once it's
    actually back up, not yours.
