# PARIŚEṢA-V4 — Full Teardown Audit: Is the Mac Back to Normal?

The PARIŚEṢA-V4 campaign is closed (owner decision, 2026-08-22; commits
`186a99879` + `21af169c6` on `parisesa/campaign-state`). tmux, the conductor
process, and the two `com.marsys.parisesa-v4-*` launchd jobs have all been
confirmed gone in earlier checks.

**Your job here is a complete, skeptical audit of everything that campaign
touched at the OS level — especially anything still keeping this Mac awake —
plus safe cleanup of what is unambiguously PARIŚEṢA's.**

## CRITICAL — what you must NOT touch

PARIPRAŚNA is a **separate, live campaign** on this same machine. Its three
launchd jobs (`com.marsys.pariprashna-watchdog`, `com.marsys.pariprashna-serve`,
`com.marsys.pariprashna-trackerd`) are **supposed** to be running. Never unload,
kill, disable, or modify anything `pariprashna`-named, and never kill a process
you have not positively identified as PARIŚEṢA's. If a power assertion or
process is ambiguous between the two campaigns, **report it, do not act on it.**

Also: **never run `sudo` yourself.** If a fix requires sudo, report the exact
command for the owner to run themselves and explain what it does.

## Part A — Why is the machine staying awake? (the main question)

1. `pmset -g assertions` — the authoritative answer. Report **in full**, and for
   every assertion of type `PreventUserIdleSystemSleep`,
   `PreventUserIdleDisplaySleep`, `PreventSystemSleep`, or
   `NoIdleSleepAssertion`, identify the owning PID and process name.
2. For each PID holding an assertion, resolve what it actually is:
   `ps -p <pid> -o pid,ppid,user,lstart,command`. Report the full command line —
   that is what distinguishes a PARIŚEṢA caffeinate from a PARIPRAŚNA one, from
   a legitimate one (Music, a download, Zoom, Time Machine).
3. `ps aux | grep -i caffeinate | grep -v grep` — list every caffeinate process
   with its full command and start time.
4. `pmset -g` and `pmset -g custom` — report current sleep/displaysleep/
   disksleep/powernap/standby settings for both AC and battery.
5. Check whether sleep was hard-disabled at the system level:
   `pmset -g | grep -i disablesleep`. If `disablesleep` is `1`, that is a
   `sudo pmset -a disablesleep 0` fix — **report it for the owner, don't run it.**
6. `pmset -g sched` — report any scheduled wake/poweron events that may have
   been created to keep overnight runs alive.

## Part B — Every launchd trace of PARIŚEṢA

7. `launchctl list | grep -i marsys` — expect only the three `pariprashna` jobs.
   Report anything else.
8. `ls -la ~/Library/LaunchAgents/ | grep -i marsys` and also check
   `/Library/LaunchAgents/` and `/Library/LaunchDaemons/` (read-only listing) for
   any `marsys` or `parisesa` plists installed system-wide rather than per-user.
9. `launchctl print-disabled gui/$(id -u) | grep -i marsys` — a job can be
   "gone" from `list` but sitting in the disabled set; report what you find.
10. For each `com.marsys.parisesa-v4-*.plist` found, `cat` it and report what it
    actually did — specifically its `KeepAlive`, `StartInterval`,
    `RunAtLoad`, and `ProgramArguments` (this tells us whether it would come
    back on next login/reboot).
11. **Report only.** Do not delete the plist files — whether to delete them or
    keep them inert for a possible future campaign is the owner's call. Say
    clearly whether, as currently configured and given they are not loaded,
    they would or would not restart automatically at next login or reboot.

## Part C — Stray processes, tmux, and the kill-switch

12. `tmux ls` — expect "no server running". If any server exists, list all
    sessions and report before touching anything (a session could belong to
    another campaign).
13. `ps aux | grep -iE "parisesa|par-night" | grep -v grep` — any surviving
    process referencing the campaign or its worktree root.
14. `ps aux | grep -i "claude" | grep -v grep` — list every running Claude
    process with its working directory if resolvable
    (`lsof -p <pid> | grep cwd`), so the owner can see what is genuinely alive.
    Flag any whose cwd is under `/Users/Dev/par-night/`.
15. `claude agents` (or `claude agents --json` if supported) — check for any
    lingering background agent registered against this campaign. Report the
    list; **do not stop or delete any agent** without checking with the owner.
16. Confirm the kill-switch is in place:
    `ls -la /Users/Dev/par-night/parisesa-v4-conductor/STOP.flag` and `cat` it.
    If it is missing, say so plainly — the owner intended it to be there.
17. Check for a `caffeinate`-holding wrapper the watchdog may have spawned:
    `pgrep -fl "parisesa"` and `pgrep -fl "watchdog"`.

## Part D — Cleanup you ARE authorized to do

18. If, and only if, Part A/C positively identifies a **caffeinate or watchdog
    process whose command line names PARIŚEṢA / `par-night` / `parisesa-v4`**,
    kill that specific PID (`kill <pid>`, escalating to `kill -9` only if
    needed), then re-run `pmset -g assertions` and `ps aux | grep caffeinate`
    to confirm it is gone and the assertion has cleared.
19. Anything ambiguous, anything `pariprashna`, anything needing `sudo`, and
    anything belonging to an unrelated app: **report, do not act.**

## Final report — answer these plainly

- **Is anything still preventing this Mac from sleeping?** If yes, exactly what,
  owned by which process, and is it PARIŚEṢA's, PARIPRAŚNA's, or unrelated?
- **What did you kill or change** (if anything), with before/after evidence.
- **Would any PARIŚEṢA launchd job come back on reboot or next login?** Yes/no,
  with the plist evidence behind the answer.
- **What still needs the owner's own hands** — every `sudo pmset` command needed
  to restore normal sleep behavior, written out exactly, with a one-line
  explanation of what each does.
- **A clear verdict:** is this machine back to its normal, pre-campaign power
  and process state, or not? If not, list precisely what remains.
