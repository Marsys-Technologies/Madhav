---
artifact: SUVARNA_INTERIM_RUNTIME
canonical_id: SUVARNA_INTERIM_RUNTIME
version: "1.1"
status: "DRAFT — for native review (with the v1.4 plan set, N-1)"
produced_on: 2026-09-29
produced_in: session "L.15 interim runtime safeguards"
companion_of: SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md §5.5 (runtime), SUVARNA_RUNBOOK_v1_0.md §2 step 9
             and §2 steps 11–12, SUVARNA_AUTONOMY_CHARTER_v1_0.md §8 (hold switch) and P13 (no bypass)
changelog:
  - "1.1 (2026-09-29, review pass 2 / plan v1.4, Strategic Suvarṇa): the generated settings move to /Users/Dev/suvarna/config/claude-settings.json (owned by the native, read-only to the swarm) and are passed with --settings to every session, pass and lane (a settings.local.json in a swarm-writable worktree is not a boundary, and lane worktrees never get hq's copy); the generator needs that target (CODE-20) and the template needs the arch §2.4 deny rules (CODE-21). /loop 10m. Tools run from the hq worktree. Isolation (arch §2.4, N-25) and the lane launcher referenced."
  - "1.0 (2026-09-29): first draft. Built and tested the four L.15 deliverables (runtime_settings.py,
     hold_guard.py, the monitor.py conductor_heartbeat check and --notify) against installed Claude
     Code v2.1.239; this runbook section records how to use them and what could and could not be
     confirmed about the installed CLI's settings schema."
---

# Suvarṇa — interim runtime safeguards (L.15)

**v1.1 note (plan v1.4).** Where this document says `.claude/settings.local.json`, read the Suvarṇa settings file
`/Users/Dev/suvarna/config/claude-settings.json`, generated from the same committed template, owned by the native,
read-only to the swarm, and passed with `--settings` to every session, pass and lane (arch §2.4, §5.5; REVIEW_PASS2
C22). The template must carry arch §2.4's full deny list (CODE-21). Lanes start only through the lane launcher.

How to generate the two execution sessions' local permission allowlist, start them, keep the
weekly `/loop` armed, watch the environment (including the Conductor's own pulse), and the one-time
power/OS settings the native applies by hand. Companion to `SUVARNA_RUNBOOK_v1_0.md` §2 steps 9 and
11–12, which this section supersedes in detail (the runbook's own step 9 pointed at a **committed**
`hq/.claude/settings.json`; L.15 builds the **local, uncommitted** `settings.local.json` instead —
see §5 below for why).

## §1 · What this adds

| Deliverable | File | What it does |
|---|---|---|
| Settings generator | `platform/scripts/governance/suvarna_tracker/runtime_settings.py` | Writes (or `--check`s) a local `.claude/settings.local.json` from the committed template `suvarna_tracker/runtime/settings.template.json`. |
| Settings template | `platform/scripts/governance/suvarna_tracker/runtime/settings.template.json` | The one source of truth for the allowlist: `defaultMode: dontAsk`, scoped `Edit(...)` rules, the Bash command allowlist, the credential/force-push/bypass denylist, and the hold-guard hook. |
| Hold guard hook | `platform/scripts/governance/suvarna_tracker/hold_guard.py` | A `PreToolUse` hook: while `$SUVARNA_HOME/run/SUVARNA_HOLD` is present, blocks a new `Agent` dispatch and any dispatch-like Bash command; always refuses an attempt to delete the hold file itself. |
| Monitor additions | `platform/scripts/governance/suvarna_tracker/monitor.py` | A ninth check, `conductor_heartbeat` (warns when a session's Conductor has gone quiet); `--notify`, a macOS notification on any change of the non-ok set. |

All four are tested (`platform/scripts/governance/suvarna_tracker/tests/test_runtime_settings.py`,
`test_hold_guard.py`, `test_monitor_runtime.py`); the full suite (345 tests as of this writing) passes.

## §2 · Generate the local settings

Run once per execution session's worktree, and again any time the template changes:

```
cd /Users/Dev/suvarna/hq/platform/scripts/governance
python3 -m suvarna_tracker.runtime_settings --write /Users/Dev/suvarna/config/claude-settings.json   # v1.1 target (CODE-20); the native runs it
```

This **creates or overwrites** `.claude/settings.local.json` in the hq worktree — never
`.claude/settings.json`. `runtime_settings.py` refuses any target path whose file name is not exactly
`settings.local.json` (exit 2), specifically so a typo or a copy-paste can never produce a committed,
repo-wide settings file. `.claude/settings.local.json` is Claude Code's own per-checkout, uncommitted
settings layer (confirmed present as a real, already-used file in this environment, e.g.
`/Users/Dev/madhav-l3/*/​.claude/settings.local.json`) — it is not tracked by `.gitignore` additions
this session made; it is simply never `git add`ed, per the standing instruction not to create or
modify any `.claude/settings.json` in any repository.

**Check for drift** (e.g. in a periodic health pass, or before trusting a long-running session's
settings) without writing anything:

```
python3 -m suvarna_tracker.runtime_settings --write /Users/Dev/suvarna/config/claude-settings.json --check
```

Exit 0 = matches the template. Exit 1 = drift; the differences are printed to stderr, one per line
(`missing: ...`, `unexpected: ...`, `changed: ...`).

Both execution sessions (Nikaṣa Engine and Exec Suvarṇa, per `SUVARNA_RUNBOOK_v1_0.md` §2 steps
11–12) run from the same `/Users/Dev/suvarna/hq` worktree, so one generated file covers both.

## §3 · Start the two sessions

Unchanged from `SUVARNA_RUNBOOK_v1_0.md` §2 steps 11–12, with the settings generated first (§2
above) and the model spelled out explicitly per the L.15 brief (Opus 5.5):

```
cd /Users/Dev/suvarna/hq && claude --model opus --settings /Users/Dev/suvarna/config/claude-settings.json --permission-mode dontAsk
```

Then, in the Nikaṣa Engine session:

```
Read and follow /Users/Dev/suvarna/hq/00_ARCHITECTURE/briefs/suvarna/prompts/NIKASHA_ENGINE_START_PROMPT_v1_0.md
```

and, once it reports, arm the interim runtime (D5, to G2 — arch §5.5's "Interim, from launch to G2"):

```
/loop 10m Run one stateless Conductor pass per ROLE_CONDUCTOR_v1_0.md ("What you do — one pass").
```

Repeat both steps in a second terminal for the Exec Suvarṇa session, with
`EXEC_SUVARNA_START_PROMPT_v1_0.md` in place of the Nikaṣa one. Never pass
`--dangerously-skip-permissions` and never select a `bypassPermissions` mode (charter P13) — the
generated settings' `deny` list also refuses any Bash invocation that itself tries to invoke one, as
a second layer (§6 below).

**Why `dontAsk` and not `acceptEdits`/`auto`:** there is no native present to answer a permission
prompt in an unattended session (charter §1: "the swarm runs long chains with the native absent");
`dontAsk` means the session never blocks on a prompt — a tool call outside the allowlist is refused
and logged, never silently worked around (charter P13, D5; `SUVARNA_RUNBOOK_v1_0.md` §2 step 11's own
description of this exact mode).

## §4 · Re-arm `/loop` weekly

`/loop`'s scheduled task **expires after 7 days and does not survive a restart** — this is a hard
limit of the interim runtime (arch §5.5, `SUVARNA_RUNBOOK_v1_0.md` §2's "Interim runtime limits"),
not a bug to work around. Re-arm both sessions' loops:

- **Every 7 days**, whether or not anything else happened (the daily digest carries the date, per
  runbook §3, so the native has a standing reminder).
- **After every restart** (reboot, sleep, crash, or a manually stopped session) — a resumed session
  does **not** get its self-paced loop back automatically; the `/loop` line must be re-sent.
- **After a usage-limit pause** clears (the pause itself stops the loop; nothing restarts it until
  the native re-arms it, or the durable runtime L.14 replaces `/loop` with a supervised process —
  see arch §5.5's "Durable, before B.W1 (L.14)").

There is no script for this: `/loop` is a Claude Code slash command inside the running session, not
a tool this package can invoke on the session's behalf. It is a native (or Steward) action, recorded
the same way any other operational step is.

## §5 · Run the Monitor

```
cd /Users/Dev/suvarna/hq/platform/scripts/governance
nohup python3 -m suvarna_tracker.monitor --watch 300 --emit --repair --notify \
  >> /Users/Dev/suvarna/run/monitor.log 2>&1 &
```

- `--watch 300`: re-check every 5 minutes (the runbook's own launch-checklist interval, §2 step 6).
- `--emit`: heartbeat every run, a `note` event on any change of the non-ok check set.
- `--repair`: conservatively restart the tracker, the DB proxy, or `caffeinate` if one of them is
  down and not already restarting — never touches hold, credential, disk or power (unchanged from
  before L.15).
- `--notify` (**new, L.15**): fires exactly one macOS notification
  (`osascript -e 'display notification "…" with title "Suvarṇa Monitor"'`) per change of the non-ok
  set — it shares `--emit`'s own dedupe state (`monitor_state.json`'s `non_ok` field), so a native
  glancing at the notification centre sees one alert per state change, not one every five minutes.
  A failed notification (no `osascript`, no notification centre, e.g. over SSH) is swallowed and
  never fails the monitor or its exit code.

**The ninth check, `conductor_heartbeat` (new, L.15):** reads `$SUVARNA_HOME/run/EVENTS.jsonl` for
the newest `kind: heartbeat, actor: conductor` line (either session's Conductor writes one every
pass, arch §5.1). `ok` with detail "no conductor yet" before either session has ever emitted one —
that is a fact about campaign phase, not a failure, and must never read as a problem on a fresh
launch. `ok` while the newest heartbeat is within `SUVARNA_CONDUCTOR_STALE_MIN` minutes (default 45 —
wider than the watchdog's own three-missed-loop relaunch threshold, arch §5.5, so this check warns
*before*, never after, the watchdog would already have acted). `warn`, never `block`, once it is
older: a stale Conductor is the watchdog's job to relaunch (arch §5.5, charter G15), not a reason to
stop dispatch outright.

Confirm on the dashboard within a few minutes: a `conductor` heartbeat from each session, `monitor`
reading `ok: 9/9`, and — once L.14's durable watchdog exists — no repeated notifications for the same
unresolved condition.

## §6 · The hold guard

Charter §8: *"`$SUVARNA_HOME/run/SUVARNA_HOLD` present: finish the items already running, dispatch
nothing new. Production-visible actions stop at the next precondition check."* `hold_guard.py` is one
of those precondition checks, wired as the settings template's `PreToolUse` hook (matcher
`Bash|Agent`). It reads the hook's JSON off stdin and:

- **Always** refuses a Bash command that tries to delete the hold file itself (`rm`/`unlink` on
  `SUVARNA_HOLD`, however spelled) — hold on or off. Only the native removes it (charter §8).
- **While the hold is set**, refuses a new `Agent` dispatch, and a Bash command that is
  production-visible or dispatch-like (contains `suvarna-build`, `suvarna_level_wave`,
  `nikasha_certify`, `gh pr merge`, `orchestrator`, or `--apply`).
- **Otherwise lets everything through** — git, tests, reads, the census, `emit`/`decide` — because
  "finish what is already running" means exactly that, not "stop everything."
- **Never wedges the session** on a malformed or empty stdin payload: it exits 0 (allows the call)
  but logs a `note` event (actor `hold-guard`) so the gap is visible on the dashboard rather than
  silently swallowed.
- Every block is logged the same way, before the exit code (2) reaches the harness — charter §11:
  "an action that is not logged did not happen," applied to a refusal as much as to an action taken.

This is a second, structural layer under the charter's own discipline (Steward/Conductor honouring
the hold by choice); the hook enforces it even if a role's own judgement about "is this
production-visible" were ever wrong.

## §7 · What could not be confirmed for v2.1.239, and how this template compensates

Checked against the installed CLI (`claude --version` → `2.1.239 (Claude Code)`) via
`claude --debug` on a throwaway settings file (never against a live Suvarṇa session):

| Setting | Status | Evidence / compensation |
|---|---|---|
| `permissions.defaultMode`, `.allow`, `.deny`, `.ask`, `.additionalDirectories` | **Confirmed valid** | Present and exercised in the installed CLI's own global `~/.claude/settings.json`. |
| `hooks.PreToolUse[].matcher` / `.hooks[].{type,command,timeout}` | **Confirmed valid** | Same source; this project's own global settings already use a `PreToolUse` command hook of exactly this shape. |
| `Read(<glob>)` covers Read **and** Glob, Grep, NotebookRead; `Edit(<glob>)` covers Edit **and** Write, MultiEdit, NotebookEdit | **Confirmed** | `claude --debug` on the installed global settings logs, verbatim: *"Glob(\*\*) is not matched by file permission checks — only Read(path) rules are… Write(\*\*) is not matched by file permission checks — only Edit(path) rules are."* The template therefore never writes a bare `Write(...)`/`Glob(...)`/`Grep(...)`/`MultiEdit(...)` path rule — one would be a **dead rule that silently grants nothing**, a materially different (and worse) failure mode than an over-broad rule. |
| `Bash(<prefix> *)` prefix matching, with the leading space before `*` significant | **Confirmed, indirectly** | The installed global settings already use this exact shape (`Bash(git -C … commit -m ' *)`); no lint warning fired against `Bash(git status *)` or `Bash(git commit -- *)` in the probe, where it does fire against genuinely dead rule shapes (above) — the absence of a warning here is corroborating, not proof of the underlying matcher's full semantics. |
| `permissions.disableBypassPermissionsMode` | **Not confirmed** | No `--debug` lint message appeared for it (neither accepting nor rejecting it), but the same probe showed the settings loader does **not** warn on an entirely invented key either — so silence is not evidence either way. A functional probe (setting it, then launching with `--permission-mode bypassPermissions`) produced no observable refusal, but was inconclusive rather than negative (no baseline confirmed the flag does anything even when unset). **Left in the template anyway** (least-harm: an unrecognized key is silently ignored per `-p` mode's own documented behaviour, "Settings files that fail validation are silently ignored… no error dialog is shown"), but it is **not** relied on as the enforcement mechanism. |
| The actual enforcement against bypass mode | **Structural, not this one flag** | `defaultMode` is `dontAsk`, never `bypassPermissions`; the launch command in §3 never passes `--dangerously-skip-permissions`; and the `deny` list separately refuses any Bash command that itself contains `--dangerously-skip-permissions` or invokes `claude … bypassPermissions` (belt-and-suspenders against a subagent or a nested `claude` invocation trying to relax its own permissions, not only against the top-level session's own mode). |
| Whether `dontAsk` truly default-denies (vs. default-allows) a tool call absent from `allow` | **Not independently verified in this session** | Relied on as documented: charter §5.5/D5 and `SUVARNA_RUNBOOK_v1_0.md` §2 step 11 both describe `dontAsk` against an allowlist as "a denial is logged, never worked around" — i.e. default-deny is the intended and documented behaviour of this mode, but this session did not construct a live unattended `dontAsk` session and attempt a genuinely disallowed tool call to observe the refusal directly (that would require running an actual Suvarṇa session, out of scope for building the safeguards themselves). |

**If a future CLI version changes any of the above** (in particular, if `Write(<glob>)`/`Glob(<glob>)`
ever start being honoured, or if `disableBypassPermissionsMode` turns out to need a different value
or location), update `suvarna_tracker/runtime/settings.template.json` and re-run `--check` against
both sessions' generated files to see the drift before regenerating.

## §8 · Power and OS settings (native, once)

Not scriptable by an agent — the L.15 brief is explicit that these are commands **the native runs**,
not the agents (they require `sudo` and touch the whole machine, not only the Suvarṇa campaign).
Apply once, for the campaign's duration (`SUVARNA_RUNBOOK_v1_0.md` §2 step 3 restates the sleep and
lid-open half of this; this is the fuller command form):

```
sudo pmset -c sleep 0 disksleep 0     # never sleep the system or the disk while on AC power
sudo pmset autorestart 1              # automatically power back on after a power failure
```

Plus, kept running for the campaign's duration (this part **is** something the launch checklist
already does per-session, `SUVARNA_RUNBOOK_v1_0.md` §2 step 3 — restated here so the full power
picture is in one place):

```
pgrep -x caffeinate || (nohup caffeinate -dimsu >/dev/null 2>&1 &)
```

Also native, one-time, for the campaign's duration: lid open, AC power, automatic macOS updates and
restarts off (`SUVARNA_RUNBOOK_v1_0.md` §2 step 3). None of these five settings/commands are wrapped
in a script here — they are single `sudo`/system commands the native runs directly, not a
repeated or unattended operation any agent role has a grant to perform.
