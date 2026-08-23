# Crash diagnostic + safe recovery (paste into a FRESH Claude Code CLI session)

You are NOT the PARIŚEṢA-V4 campaign conductor. Do not touch findings, PRs,
rulings, or any campaign substance — that belongs to the conductor session
once it's safely back up, not to you. Your job right now is narrow: figure out
why the tmux session hosting that campaign just crashed, recover what can be
safely recovered, and hand back a precise list of anything that genuinely
needs the human owner's hands.

Relevant paths: conductor worktree `/Users/Dev/par-night/parisesa-v4-conductor`,
tmux session name `parisesa`, watchdog `watchdog.sh` (v7) with launchd jobs
`com.marsys.parisesa-v4-watchdog` and `com.marsys.parisesa-v4-caffeinate`,
campaign state on `parisesa/campaign-state` inside the Madhav repo at
`00_ARCHITECTURE/briefs/parisesa/state/` (heartbeat.json, RESUME.md,
ledger.json), kill-switch `STOP.flag` in the conductor worktree root.

## Part A — Diagnose first, don't touch anything yet

1. Check whether tmux is actually dead or just detached: `tmux ls`. If a
   session is listed, STOP here and report it — don't create a competing
   session. Only proceed to recovery if it's genuinely gone.
2. Look for a real crash signature, not just an assumption:
   - `ls -lat ~/Library/Logs/DiagnosticReports | head -20` — check for any
     recent crash/hang report naming Terminal, tmux, node, or claude, and
     read the most relevant one in full.
   - `log show --last 30m --predicate 'eventMessage contains "tmux" OR eventMessage contains "claude" OR eventMessage contains "node"' --style compact 2>&1 | tail -100`
     — adjust the time window if the crash was longer ago.
   - Memory pressure at/around the crash: `vm_stat`, and check whether
     anything shows OOM-kill signatures in the log query above.
   - Disk space: `df -h /`. A full disk is a common, boring cause of exactly
     this kind of silent-looking crash.
3. Check for orphaned processes that shouldn't still be running:
   `ps aux | grep -iE "claude|tmux" | grep -v grep`.
4. Check the watchdog/caffeinate launchd jobs independently of the tmux
   crash — they run as separate launchd services and may or may not have
   survived: `launchctl list | grep marsys`. Tail
   `/Users/Dev/par-night/parisesa-v4-conductor/logs/watchdog.out.log` (or
   wherever it actually logs — find it if this path is wrong) for the last
   hour to see whether the watchdog itself noticed and reacted to the crash,
   or whether it died too.
5. Check `STOP.flag` in the conductor worktree root. If present, do not
   proceed past this point — report it and stop; clearing it is the owner's
   decision alone, never yours.
6. Check how stale the campaign state actually is:
   `cat /Users/Dev/par-night/parisesa-v4-conductor/00_ARCHITECTURE/briefs/parisesa/state/heartbeat.json`
   and compare its content against the mtime of the file itself, and against
   `date`, to see how long the conductor has actually been down.

Write down, in plain language, your best evidence-backed theory of what
caused the crash before moving to Part B. If the evidence is genuinely
ambiguous, say so honestly rather than guessing confidently.

## Part B — Recover what's safe to recover automatically

Only proceed if Part A found: tmux genuinely dead (not just detached),
STOP.flag absent, and nothing suggests the underlying Mac itself is in a bad
state (e.g. disk full, thermal shutdown risk) that recovery would make worse.

1. If the watchdog/caffeinate launchd jobs are unloaded or dead, reload them
   from their existing plists (find the plist paths under
   `~/Library/LaunchAgents/` matching `com.marsys.parisesa-v4-*` — do not
   author new ones): `launchctl bootstrap gui/$(id -u) <plist path>` (or
   `launchctl load` if this system uses the older syntax — check which
   applies before running either).
2. Start a fresh tmux session and resume the exact prior conversation — never
   `claude --continue` (cwd alone can't disambiguate when this directory may
   have hosted more than one Claude conversation; this exact ambiguity has
   caused a real cross-campaign near-miss before):
   ```
   tmux new -s parisesa
   cd /Users/Dev/par-night/parisesa-v4-conductor
   claude --resume <claude_session_id from heartbeat.json, read fresh in Part A>
   ```
3. Confirm the resumed session actually has its prior context (don't just
   assume `--resume` worked — check that it responds as the campaign
   conductor with real memory of PARIŚEṢA-V4, not as a blank session).
4. Do not do any further campaign work yourself. Once the conductor session
   is confirmed live and oriented, your job is done.

## Part C — Report back

Give the owner, in plain language:

1. Your best evidence-based theory of what caused the crash (cite the actual
   log lines / files you found — not a guess dressed as a finding).
2. Exactly what you recovered automatically (watchdog reloaded? new tmux
   session started? conductor resumed and confirmed live?).
3. A precise, numbered list of anything you could NOT do and why — a GUI
   permission dialog, a keychain/password prompt, a decision that is
   genuinely the owner's to make (e.g. STOP.flag was set), a `sudo` password
   needed, or anything requiring physical access to the machine. Be specific
   enough that the owner can act on each item without guessing what you mean.
