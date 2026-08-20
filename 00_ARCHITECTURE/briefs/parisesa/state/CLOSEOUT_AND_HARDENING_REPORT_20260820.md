---
title: PARIŚEṢA V4 Closeout & Hardening Report
session: PARISESA-V4-CLOSEOUT-20260820T173721Z
date: 2026-08-20
status: COMPLETE
---

# PARIŚEṢA V4 Closeout & Hardening Report

**This is the one document to read before deciding whether to authorize the next unattended overnight PARISESA-V4 run.**

## Go/no-go recommendation

**GO, conditionally.** The watchdog mechanism itself is now genuinely proven — not just installed — through an end-to-end test on an isolated harness plus a safe real-environment fire of the launchd plumbing. It is materially more trustworthy than what ran last night. Two conditions before authorizing the next run:

1. **Sleep prevention must be held explicitly for the campaign window** (`caffeinate -dimsu` or `pmset -a sleep 0`) — this Mac sleeps after 1 minute idle, and neither cron nor launchd runs during sleep. This was not the cause of last night's failure (cron fired reliably all night per direct log evidence), but it is a real, currently-unmitigated risk for tonight now that the interval is tighter.
2. **The owner should read §1's residual risk** (a genuine, self-caught near-miss during testing this session) before trusting the revival mechanism blind on a night nobody is watching.

Beyond the watchdog, PF-001/PF-002/PF-004 are closed with no outstanding action, and PF-003 required and received an active intervention (a stray process was killed) rather than a passive finding.

---

## Step 1 — Watchdog root cause and hardening

### 1a. Root cause: a PATH problem, not a permission problem

The prior report's hypothesis ("probably a macOS permission issue, empty log file") was investigated and rejected with reproduced evidence, not accepted.

**What actually happened:** `watchdog.sh` v1 ran under cron with no `PATH=` set anywhere — neither in the script nor the crontab. cron's minimal default PATH (`/usr/gnu/bin:/usr/local/bin:/bin:/usr/bin:.`) does not include `/opt/homebrew/bin`, where `tmux` lives on this Apple Silicon Mac. Every `tmux send-keys` call failed with "command not found" (exit 127) — reproduced directly via `env -i` stripped-environment testing. The script's own `2>/dev/null` redirects on every tmux call silently swallowed that error, which is also why `/tmp/parisesa-watchdog.log` stayed empty (0 bytes) all night.

**Confirmed NOT a permission issue:** `log show --predicate 'process == "cron"'` independently confirms cron itself fired reliably every 5 minutes all night — cron was never the problem. cron runs as the same UID as the interactive session; the tmux socket (`/private/tmp/tmux-504/default`) is owned by that same UID; `tmux send-keys` talks to tmux's own IPC socket, not macOS's Accessibility/UI-automation APIs (unlike `osascript`), so no TCC grant was ever going to be relevant. With PATH corrected, `tmux list-sessions` reaches the real session immediately.

### 1b. Replacement design (Opus-5 reviewed before install)

**Mechanism:** a launchd user agent (`com.marsys.parisesa-v4-watchdog`, `StartInterval=60`) replaces cron. Kept `tmux send-keys` (already proven to need no special permission). The prior session's `CronCreate`+`/loop` stopgap is kept only as a courtesy supplement — it requires an already-alive session to self-schedule its next wakeup, so it structurally cannot substitute for external revival of a truly stuck/dead session.

Escalated the full design to an Opus-5 review before installing anything. Opus endorsed launchd over a one-line crontab `PATH=` fix specifically for: no-overlap guarantee (launchd will not stack concurrent runs; cron would, and this script sleeps), separate stdout/stderr capture (closes the swallowed-stderr half of the v1 defect structurally, not just by convention), and `launchctl kickstart` giving a real test trigger. It also confirmed the `TCC.db` "authorization denied" seen during 1a investigation is normal SIP behavior on any modern Mac, not a red flag.

Opus found **4 real blocking defects** in the first draft, all fixed before install:

1. **C-c into a live TUI Claude pane is swallowed by the app, not delivered as SIGINT.** The old unconditional "C-c, then `claude --continue`" sequence only works if the pane already died back to a shell. Fixed: the script now branches on `tmux display -p '#{pane_current_command}'` — if it's a shell, run the full launch sequence; if a process (including a live Claude) is still resident, send **only** the resume text, no C-c.
2. **No cooldown → a revival storm.** At 60s `StartInterval`, a stale heartbeat that outlives one cycle would re-fire the revival sequence every single minute, forever, interrupting the very session it just launched. Fixed: a cooldown stamp file (600s) plus a max-attempts cap (3) that writes a `WATCHDOG_ALERT.flag` instead of retrying silently forever — a permanently-failing watchdog must not be silent again.
3. **1200s (20min) stale threshold too tight.** A real subagent in this repo was independently observed running 30+ minutes with no heartbeat write during ordinary, healthy operation. Raised to 2700s (45min).
4. **This Mac sleeps after 1 minute idle** (`pmset -g` → `sleep 1`), with only short-lived `caffeinate` holds observed (300s, expiring). Neither cron nor launchd runs during sleep. This is not something the watchdog script itself can fix — documented as a campaign-launch-time responsibility (see the go/no-go conditions above).

### 1c. Built and proven end-to-end — including a self-caught near-miss

**The mechanism was proven, not just installed — but the first attempt at proving it caused a real, if contained, incident, disclosed in full below.**

The first Step 1c test created a plain new tmux session and ran the real watchdog logic against it, believing it was a blank pane. It was not. `claude --continue`'s session-resume is scoped by the invoking shell's **working directory**, not by tmux session identity — and the test pane's inherited cwd (`/Users/Dev/Vibe-Coding/Apps/Madhav`, the shared primary checkout) coincided with the cwd of a live, unrelated **PARIPRAŚNA** conversation (waiting on CI for PR #1396). The test's `claude --continue` + "Resume per RESUME.md" sequence was delivered into that real, foreign session, not a fresh one.

It had completed exactly one read-only search (no writes, no commits, no pushes) before being interrupted with Escape within roughly 90 seconds. A follow-up message explained the error and asked it to disregard and continue its own work; it did so cleanly ("Understood, ignoring that — continuing to wait on PR #1396"). **No file, branch, commit, or PR was touched.** This is disclosed in full rather than smoothed over, in keeping with how PF-001 through PF-004 were handled last session.

**Design implication, not yet fixed:** `claude --continue` is not scoped to a specific campaign/session identity, only to the invoking shell's cwd. If the real "parisesa" pane's shell were ever at the wrong cwd when the watchdog fires (a mid-session `cd`, or a respawned shell in the wrong directory), the same hijack could happen for real, silently, with no error surfaced. This was invisible to the Opus design review (it only became visible live) and is **not implemented as a fix this session** — flagged here as a residual risk with a suggested mitigation (verify `tmux display -p '#{pane_current_path}'` matches the expected conductor directory before sending `claude --continue`; abort + alert instead of sending blind if it doesn't) for a future hardening pass.

**After redesigning the test to be genuinely safe** (isolated cwd with no real session history, the real `claude` binary shadowed by a logging stub so no genuine CLI invocation was possible), 6 scenarios were run and all passed:

| # | Scenario | Result |
|---|---|---|
| 1 | Stale heartbeat, pane at shell | Stub `claude --continue` invoked (confirmed via log), resume line delivered |
| 2 | Stale heartbeat, pane running a live process | No C-c, no claude invocation — resume line sent alone (confirmed empty invocation log) |
| 3 | Immediate re-run | Correctly cooldown-skipped |
| 4 | `attempt_count=3` forced | `WATCHDOG_ALERT.flag` written, exit 1 — did not retry silently |
| 5 | `STOP.flag` present | Immediate no-op |
| 6 | Healthy (fresh) heartbeat | No-op |

Separately, launchd's own plumbing was proven **against the real environment, safely**: the plist installed cleanly (`launchctl bootstrap` exit 0), `launchctl kickstart -k` forced a real immediate fire, the stdout log correctly captured the STOP.flag no-op (STOP.flag has been set for this entire closeout session, guaranteeing this was harmless), stderr was empty, and the live "parisesa" production pane's content was captured before and after — byte-identical, confirmed untouched.

The old cron entry for `watchdog.sh` was removed (PARIPRAŚNA's own unrelated cron line left untouched) so launchd is now the sole revival mechanism — avoiding the double-fire race a surviving cron entry would reintroduce.

### 1d. How the final mechanism works, in plain language

Every 60 seconds, macOS's launchd runs `watchdog.sh`. The script:
1. Exits immediately if `STOP.flag` exists (the owner's kill switch — always respected first).
2. Exits immediately if `heartbeat.json` doesn't exist yet (campaign hasn't started) or is fresh (< 45 minutes old — the campaign is healthy).
3. If the heartbeat is stale, checks a cooldown file — if a revival was attempted in the last 10 minutes, it waits rather than re-firing.
4. If 3 revival attempts have already happened with the heartbeat still stale, it gives up loudly — writes `WATCHDOG_ALERT.flag` instead of trying a 4th time silently.
5. Otherwise, it looks at what's actually in the tmux pane. If it's a plain shell (the session died), it types `claude --continue` and waits for it to load, then sends the resume instruction. If something is still running in the pane (Claude itself, just very busy), it sends **only** the resume instruction — never an interrupt keystroke, because that keystroke would be swallowed by a live Claude Code TUI rather than stopping it.

Logs land in `00_ARCHITECTURE/briefs/parisesa/../logs/watchdog.{out,err}.log` (stderr is never discarded, unlike v1). To verify it's live: `launchctl list | grep parisesa-v4-watchdog`. To force a test fire safely: `launchctl kickstart -k gui/$(id -u)/com.marsys.parisesa-v4-watchdog` (harmless as long as `STOP.flag` is present).

---

## Step 2 — PF-003 (EKAVĀKYATĀ not dormant)

**Given real attention, not a rubber stamp, per the mandate.**

Live `ps aux` confirmed exactly one EKAVĀKYATĀ process running: PID 30415, a raw `claude -p` non-interactive invocation whose full kickoff prompt (there is no separate binary or script — the prompt *is* its source) identified it as SENTINEL, EKAVĀKYATĀ's standing verifier role. It had been running continuously since **Sunday 2026-08-16 00:35:32** — 4 days 22+ hours — with only 51 minutes of accumulated CPU time (a very low duty cycle, consistent with sitting idle rather than working). It ran under `--permission-mode bypassPermissions`, with a self-declared write scope of exactly one file (`LEDGER_SENTINEL.md` on its own branch) and the explicit promise "you never edit source, never merge, never rule" — a prompt-level discipline only, not OS-enforced.

Its companion launcher process had already gone idle after dispatching both SENTINEL and PRATINIDHI (EKAVĀKYATĀ's ruling authority) in a bounded 2-attempt retry loop; no PRATINIDHI process was found running anywhere.

**EKAVĀKYATĀ's own coordination record settles the "is P-1.4's dormancy note still true" question directly:** `CAMPAIGN_COORDINATION.md` on `origin/campaign-coordination` carries a formal closure banner — `EKAVAKYATA-CLOSED-PARTIAL, 2026-08-15T23:38Z`. SENTINEL's own branch went silent at 2026-08-16 03:37:53 (a post-closure addendum); PRATINIDHI's last commit was 2026-08-16 04:58:35. `LEASES.json` (unchanged since the 2026-08-16 seed) confirms EKAVĀKYATĀ's ownership scope sits entirely inside Madhav repo source paths that PARISESA-V4's own 21 open PRs could, in principle, also touch — though zero actual overlap was ever observed; SENTINEL wrote nothing after 2026-08-16 03:37, well before PARISESA-V4's session even started.

**Escalated the final safe/not-safe judgment to Opus 5**, as required. Verdict: **not safe as-is.** An orphaned `bypassPermissions` agent with a live API connection, holding standing (if prompt-only-constrained) write ability into the exact repo PARISESA-V4's PRs target, has zero legitimate remaining work — its campaign is closed and its only ruling authority is dead — against a real, if low-probability, residual risk. Opus independently re-verified the process was still alive and read the launcher's exact retry-loop condition to confirm killing it could not trigger a respawn, and explicitly judged terminating it to be in-scope environment hygiene (not "finding repair" on the 141-corpus) — Step 2's own mandate was to determine whether something needs to change first.

**Action taken:** `kill 30415` (SIGTERM). Confirmed within 7 seconds: process gone, no respawn.

**The "3 other unidentified Claude processes"** from last session's report are the Antigravity IDE extension's own background Claude Code sessions (4 processes with `--resume=<uuid>` flags, no worktree/campaign path in their command lines) — the user's own personal IDE tooling, unrelated to either campaign. Left untouched.

**Residual for the owner:** confirm on next login that no EKAVĀKYATĀ process has reappeared — nothing in this investigation ruled out a human manually relaunching the standing-roles script.

---

## Step 3 — PF-001 (F-50 review-chain bypass)

Read the actual diff of commit `877b75d12` (PR #1347), not just its message. It genuinely implements the claimed fix: when a graha/domain filter is active, the narration now reads "X leads this &lt;scope&gt;-filtered resonance result: priority class Y (rank Z of 9 chart-wide)" instead of the previously misleading unconditional "#1 remedy-priority target" framing. Three new tests cover graha-filtered, domain-filtered, and an unfiltered control case (which correctly preserves the "#1" framing when legitimately unfiltered) — exactly matching the ledger's own cited live production canary. **Confirmed correct and tested by direct source read, not accepted from the commit message.**

**Is the review-chain gap a one-off or repeatable?** `gh pr view 1347` shows branch `codex/v4-f50-remedy-lead-honesty` (a genuinely different tool/session than this campaign, corroborating "unreviewed sibling attempt"), author and merger both the human owner, **zero reviews**. Checking systemically: `gh api repos/.../branches/main/protection` returns **404 "Branch not protected"** — main has no required-review rule configured at all. The last 20 merged PRs across the whole repo (all campaigns, all tools) show the identical pattern: `reviews: 0`, self-merged by the owner, every time.

**This is not a campaign-tag-detection gap in a merge-queue rule — there is no merge-queue rule of any kind.** Every PR in this repo, from every tool, is self-mergeable with zero required review, by design or by the complete absence of a protection ruleset. F-50 was not an anomaly; it is the norm.

**Proposed, not implemented** (per this session's no-repair-work boundary): if campaign-class review chains (PRATINIDHI ratification, Opus panels, etc.) should be structurally un-bypassable rather than a procedural convention, the concrete fix is a GitHub branch protection rule on `main` requiring N reviews or a specific status check. This is an infrastructure/policy decision requiring explicit owner authorization — left for the owner.

---

## Step 4 — PF-002 (concurrent continuation, 5 commits)

**Independently re-verified, not trusted from the prior session's own claim:** recomputed the full SHA-256 hash chain across `journal.ndjson` seq 1–637 from scratch in this session — every event's hash and prev-hash link matches, zero exceptions across all 637 events. The chain is genuinely intact.

**However, the prior session's own root-cause hypothesis for the trigger is very likely wrong**, in exactly the same way its watchdog-permission hypothesis was wrong. It attributed the concurrency to "most likely the cron watchdog firing `claude --continue`." Step 1a's hard evidence directly contradicts that: the v1 cron watchdog's `tmux send-keys` calls failed with exit 127 for the entire night — it was mechanically incapable of ever delivering a `claude --continue` keystroke, including during the PF-002 window (2026-08-20 14:21–14:25 IST).

**Best-available explanation, reported honestly as such (not as confirmed):** the 5 commits are well-formed, doctrine-consistent "round 4" tracker-fold work — exactly what the conductor's own turn logic would produce — and the main campaign had already invoked both `CronCreate` (fixed-interval `/loop`) and `ScheduleWakeup` (dynamic `/loop`) automation earlier in that session. Both are harness-level mechanisms that resume a session directly through the CLI's own continuation API, not via tmux keystroke injection, and are therefore not subject to the PATH/tmux failure that rules out the cron watchdog. The most plausible explanation is one of those scheduled continuations firing while the original thread was still mid-flight waiting on round-4 subagent notifications — two genuinely concurrent executions of "continue the campaign" under the same session identity. **This could not be pinned down with certainty** — no harness-level scheduling log was available to inspect retroactively for a session that has since closed.

**Operational lesson for the owner:** any automated continuation mechanism (watchdog *or* harness-level `/loop`) can produce genuine concurrent-writer collisions against a "single writer" tracker design that assumes but does not enforce exclusivity. Worth considering an actual lock (a lease/pid-file check before the fold step) rather than a documented convention, before authorizing another overnight run with automated continuation active.

---

## Step 5 — PF-004 (git stash collision)

`git stash list` on the shared Madhav `.git` shows exactly **7 entries** — the same count recorded immediately after the incident was self-corrected. All 7 are pre-existing and foreign to PARISESA-V4 (owned by other campaigns/sessions); none were touched. **No residual contamination.**

The "never `git stash`" mitigation is durably documented in two places beyond any single session's memory: `CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md` item X-5 ("`git stash` is banned in any worktree sharing this `.git`... Use a WIP commit on the lane branch"), and PARISESA-V4's own closure factory plan ("Do not use `git stash` as the primary handoff... never hide the handoff in stash"). Both predate this campaign. **Closed.**

---

## Step 6 — Bookkeeping (143 vs. 141)

The ledger held 141 canonical `F-<n>` IDs, plus `F-112-DOCSTRING` (a legitimate split — verified this session, not just accepted: it was split out by an Opus ESC-001 review as a genuinely separate, real narration-fidelity defect, independently evidenced end-to-end through PR #1394/`MORNING_SHIP_READY`), plus `F-75-batch` (a stale marker row).

**Verified, not accepted on the report's word, that all 6 findings `F-75-batch` referenced are individually resolved**: F-75, F-76, F-80, F-82, F-85, F-86 are all independently confirmed `CONTROL_CLOSED`/`LANDED` with their own live-query evidence. Deleted `F-75-batch` from the ledger's reduced view (its full history remains readable in `journal.ndjson` for audit-trail completeness — a new `bookkeeping_delete_finding_row` event type was added to the reducer rather than editing journal history, preserving the append-only/single-writer discipline).

**A second, unrelated bug was caught while verifying the split:** F-112's own structured status field had been left at `DECISION_PARKED` by a prior correction event whose own prose explicitly said it should revert to closed — the prose and the structured field had silently diverged. Corrected in the same pass (`SERVICE_CLOSED`/`SERVICE_CLOSED`).

**Ledger now reads exactly 141 canonical finding rows + 1 legitimate split (F-112-DOCSTRING) = 142 real entries**, confirmed by direct count after the correction.

---

## Boundaries observed

No new finding-repair work was performed. No merges, no deploys, no data writes, no content changes to any of the 21 open PRs. No writes to any sibling or stranger namespace beyond the single, disclosed, fully-corrected near-miss in §1c and the judged-in-scope kill of PID 30415 in §2. `STOP.flag` remains set — clearing it is the owner's decision, not this session's.

## Noted for the next overnight queue, not acted on this session

- The `claude --continue` cwd-scoping risk surfaced in §1c (pin/verify pane cwd before sending).
- The branch-protection gap surfaced in §3 (repo-wide, not F-50-specific).
- The tracker's lack of an enforced single-writer lock, surfaced in §4.
