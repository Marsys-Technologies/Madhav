---
title: PARIŚEṢA V4 Pre-Flight Hardening Addendum
session: PARISESA-V4-PREFLIGHT-20260820T181515Z
date: 2026-08-20
status: COMPLETE
supersedes_gono_go_from: CLOSEOUT_AND_HARDENING_REPORT_20260820.md
---

# PARIŚEṢA V4 Pre-Flight Hardening Addendum

**This addendum closes both conditions the closeout report's "GO, conditionally" was waiting on. Read alongside `CLOSEOUT_AND_HARDENING_REPORT_20260820.md`, which this supersedes only on the go/no-go line — every other finding in that report stands unchanged.**

## Updated go/no-go: unconditional GO

Both conditions from the original conditional GO are now closed and proven, not just installed:

1. ~~Sleep prevention must be held explicitly for the campaign window~~ → now self-healing, tied to campaign lifecycle, proven against a real kill (§2).
2. ~~The owner should read the cwd-scoping near-miss residual risk~~ → the gap itself is now patched, Opus-5 reviewed, and proven closed with a dedicated test scenario (§1).

**Still open, still owner-decision, still not addressed by this or the closeout session (unchanged from the closeout report):** the repo-wide branch-protection gap (§3 of the closeout report — PF-001) and the tracker's lack of an enforced single-writer lock (§4 of the closeout report — PF-002's operational lesson). Neither is a blocker; both require explicit owner authorization to act on.

---

## Step 1 — Watchdog cwd-scoping gap, patched and proven

### What was wrong

The closeout session's own watchdog (v4) added a cwd check before any pane send, closing the near-miss that session caused during its own testing. That check was real but, per an Opus-5 review of the patch itself, incomplete in four ways — the same class of gap the check was meant to close, still present elsewhere:

1. The shell-detection pattern `*sh` also matches `ssh` (and `fish`, `dash`, `csh`). An SSH'd-into pane reports its **local** cwd, so the guard would pass while `claude --continue` got typed into a **remote** shell.
2. cwd alone does not prove *session* identity. Live-checked during the review: this exact project directory holds **two** separate Claude Code conversation histories. `claude --continue` resumes whichever has the more recently modified transcript file — the cwd guard has no way to see that, or to stop it picking the wrong one.
3. `tmux display -p` on a pane index that no longer exists was found, live, to silently report the **still-active pane's** info rather than erroring — while `tmux send-keys` on that same bad index correctly fails. The guard could validate a pane different from the one actually receiving the keystrokes.
4. The abort itself wasn't rate-limited — a persistent mismatch would have re-fired every 60 seconds forever, and re-stamped the alert file's timestamp every time, destroying the original detection time.

### What was fixed (v5)

- **Exact shell match** (`bash|zsh|sh|-bash|-zsh`) instead of the `*sh` glob.
- **Session identity pinned, not just directory.** The campaign's own event-folding tool (`build_tracker.py`) now writes the currently-running conductor's `$CLAUDE_CODE_SESSION_ID` into `heartbeat.json` on every fold. The watchdog reads that field and issues `claude --resume <that-uuid>` instead of a bare `claude --continue` — pinning the exact conversation rather than trusting "most recent in this directory." Falls back to bare `--continue` (with a logged warning) only if it finds an older `heartbeat.json` that predates this field.
- **Pane existence checked explicitly** via `tmux list-panes` before trusting anything `display -p` reports, and `tmux send-keys`' own exit status is now checked — the script no longer logs "revival sequence sent" unconditionally regardless of whether the send actually worked.
- **The abort is now rate-limited** through the exact same cooldown/max-attempts state a real revival attempt uses, and each alert file is written only once per incident (not re-stamped every cycle) so the first-detection time survives.
- Two smaller fixes surfaced in the same review: alert JSON is now built through Python's `json.dumps` instead of raw shell string interpolation (a stray character in a path could otherwise produce malformed JSON), and every `tmux` call is wrapped in `timeout 10` so a wedged tmux server can't hang the watchdog silently — the same failure class as the very first PATH bug, one layer down.
- An empty pane cwd (the pane vanished between checks) now gets its own distinct alert message rather than being reported as an ordinary mismatch.

**A real bug was caught and fixed during this session's own testing, not by Opus:** the first implementation of the JSON-alert helper had a `python3 -c` argv off-by-one (`sys.argv[0]` is the literal string `"-c"`, not the first real argument) — it silently failed to write any alert file. Caught by the test suite itself when the cwd-mismatch alert didn't appear where expected; fixed and re-verified.

### Proof (isolated harness, never the live pane)

All 6 original scenarios from the closeout report were re-run against v5 with zero regressions, plus 2 new ones:

| # | Scenario | Result |
|---|---|---|
| 1 | Pane at shell, correct cwd | `claude --resume <pinned-uuid>` invoked (not bare `--continue`) |
| 2 | Pane running a live process | Resume-text only, no claude invocation |
| 3 | Immediate re-run | Cooldown-skipped |
| 4 | `attempt_count=3` forced | `WATCHDOG_ALERT.flag` written, exit 1 |
| 5 | `STOP.flag` present | No-op, including no sleep-prevention hold |
| 6 | Healthy heartbeat | No-op |
| 7 (new) | Stale heartbeat, pane at shell, **cwd deliberately wrong** | Aborted, sent nothing, wrote a distinct cwd-mismatch alert — then confirmed a second immediate run was correctly cooldown-skipped rather than re-firing |
| 8 (new) | Target pane genuinely doesn't exist | Aborted before any `display`/`send-keys` call, wrote a distinct alert, sent nothing |

Then, separately, the live production pane's own cwd was re-confirmed to exactly match the guard's expected path — the v5 guard does not and will not false-positive against the real pane as currently configured.

### 1e. Updated plain-language description

Same 60-second cycle as before, with two changes to step 5 of the closeout report's description: before typing anything, the watchdog now (a) confirms the target pane still exists, and (b) if it's about to relaunch Claude, reads the exact conversation ID the last healthy campaign session recorded and asks specifically to resume *that* conversation (`claude --resume <id>`) rather than just "whatever's most recent in this folder" — because this folder has, at least once, held more than one conversation. If either check fails, or the pane's directory isn't exactly where the campaign lives, it sends nothing and writes a clearly-labeled alert file instead of guessing.

---

## Step 2 — Durable, self-healing sleep prevention

### What was wrong

`pmset -g` confirmed this Mac sleeps after 1 minute idle. The only thing holding it off was a manually-run `caffeinate` with a 300-second timeout, already counting down — nothing durable, nothing tied to whether a campaign was actually running, and nothing that would notice or recover if it died.

### What was built

`watchdog.sh` gained an `ensure_caffeinate()` step that now runs at the start of every 60-second cycle the campaign isn't stopped (the same `STOP.flag` gate as everything else — sleep prevention is tied to the campaign's own lifecycle, not held indefinitely regardless of whether anything is running):

- Checks a recorded PID (`logs/caffeinate.pid`) for a process that is both alive **and** actually still `caffeinate` (guards against PID reuse pointing at some unrelated process).
- If it's alive, logs and does nothing.
- If it's dead or missing, launches a fresh `caffeinate -dimsu -t 43200` (12 hours — a full overnight window), records the new PID, and — if there *was* a dead PID it just replaced — writes `WATCHDOG_ALERT_CAFFEINATE_DEAD.flag` recording the dead PID and detection time, so a mid-night death is visible, not silent.

### Proof

First on the isolated test harness (short durations, scratch paths): fresh launch, no-op-while-alive (same PID, no duplicate process), dead-process detection with automatic recovery (new PID, alert file written), and a PID-reuse guard (a fake non-caffeinate process at the recorded PID is correctly rejected, not mistaken for a live hold).

Then **against real production paths**, not just the test harness: launched the real `ensure_caffeinate()` against `logs/caffeinate.pid` under the real conductor directory, confirmed via `pmset -g assertions` that a genuine `PreventUserIdleSystemSleep` (and 4 companion) assertion was active under that exact PID, killed that real process, re-ran, and confirmed it detected the death and launched a replacement with a new PID, writing the dead-PID alert with the real conductor path. Cleaned up afterward (killed the replacement, removed the pid/alert files) since no campaign is actually running yet — the mechanism will assert this for real, automatically, the moment the next campaign session runs and the owner clears `STOP.flag`.

### 2e. How it works, and how to check or cancel it

**How it holds sleep:** every watchdog cycle, as long as `STOP.flag` is absent, it makes sure a `caffeinate -dimsu` process is alive, launching a fresh 12-hour one if the last one died or was never started.

**To verify it's active right now:** `cat /Users/Dev/par-night/parisesa-v4-conductor/logs/caffeinate.pid` for the PID, then `pmset -g assertions | grep -A2 "pid <that-pid>"` to see the live assertion. `watchdog.out.log` also logs "caffeinate PID N still alive" every cycle it's healthy.

**If it ever dies mid-campaign:** the next watchdog cycle (within 60s) will notice, relaunch it, and write `WATCHDOG_ALERT_CAFFEINATE_DEAD.flag` recording the dead PID — that file's mere presence is the signal something died once, even after it's since recovered.

**To let the Mac sleep for an unrelated reason:** either `touch STOP.flag` (stops the whole watchdog, including this) — the standard, already-familiar kill switch — or, to stop only the sleep-prevention while leaving revival active, `kill $(cat logs/caffeinate.pid)` once; note the watchdog will simply relaunch it on its next cycle unless `STOP.flag` is also set, since that's the intended self-healing behavior.

---

## Step 4 — Readiness confirmation

- `STOP.flag`: confirmed present at session start and end. **Not cleared by this session** — that remains the owner's action.
- cwd: `/Users/Dev/par-night/parisesa-v4-state` (state worktree; `watchdog.sh` itself lives in and was edited in the conductor worktree, `/Users/Dev/par-night/parisesa-v4-conductor`).
- Watchdog alive: `com.marsys.parisesa-v4-watchdog` present in `launchctl list`, running v5, confirmed via a real `launchctl kickstart -k` fire during this session (correctly no-op'd on `STOP.flag`, stderr empty, live pane byte-identical before/after).
- Sleep assertion: proven active and self-healing against real production paths this session (§2), then deliberately cleaned up afterward since no campaign is currently running — it will assert for real, automatically, on the first watchdog cycle after the owner clears `STOP.flag` and a campaign session starts writing `heartbeat.json`.

**Ready for the next overnight kickoff; `STOP.flag` remains set pending the owner's decision to clear it.**

## Boundaries observed

No new finding-repair work. No merges, no deploys, no data writes, no touching the 21 open PRs' content. No writes to any sibling or stranger namespace. All testing used isolated harnesses or `STOP.flag`-gated safe fires against the real environment — the live "parisesa" production pane was never sent a keystroke this session.
