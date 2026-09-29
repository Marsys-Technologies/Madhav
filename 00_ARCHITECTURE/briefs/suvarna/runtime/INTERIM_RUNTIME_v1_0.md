---
artifact: SUVARNA_INTERIM_RUNTIME
canonical_id: SUVARNA_INTERIM_RUNTIME
version: "1.2"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1. The /loop interim is withdrawn by N-34; the settings file, the hook and the Monitor parts remain in force."
produced_on: 2026-09-29
produced_in: session "L.15 interim runtime safeguards"
companion_of: SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md v1.5 §5.5 (runtime, L.14, L.18), SUVARNA_RUNBOOK_v1_0.md §2,
             SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.5 §8 (holds) and P13 (no bypass), NATIVE_SETUP_v1_0.md (NS.8, NS.9)
changelog:
  - "1.2 (2026-09-30, plan set v1.5): the /loop interim and its weekly re-arm are withdrawn (§3/§4 now point to the durable runtime L.14: launchd daemons as `suvarna`, installed by NATIVE_SETUP NS.8; N-34, N-28; Astra F6, F17). The hook fails closed on any malformed payload for Bash and Agent, reads the hold from the hold ledger authority/HOLDS.jsonl (N-35; Astra F4) and runs from the control checkout /Users/Dev/suvarna/control (N-37; Astra F2). conductor_heartbeat is per session (engine, exec), stale threshold = three times the maximum pass backoff, replacing the 45-minute default (Astra F6, F18). §8 power settings are NATIVE_SETUP NS.9."
  - "1.1.1 (2026-09-30, review pass 3; REVIEW_PASS3_DISPOSITION_v1_0.md): the hold-guard hook runs the committed code in the hq worktree (PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance), never Strategic Suvarṇa's worktree, and fails closed for dispatches (a hook that cannot run, or a malformed payload, refuses an Agent dispatch and any dispatch-like command); the Monitor confirmation reads every check ok except isolation, which warns until N-25 is decided; the swarm's allow-list forms per arch §2.4 (code: the template, CODE items in the pass-3 disposition)."
  - "1.1 (2026-09-29, review pass 2 / plan v1.4, Strategic Suvarṇa): the generated settings move to /Users/Dev/suvarna/config/claude-settings.json (owned by the native, read-only to the swarm) and are passed with --settings to every session, pass and lane (a settings.local.json in a swarm-writable worktree is not a boundary, and lane worktrees never get hq's copy); the generator needs that target (CODE-20) and the template needs the arch §2.4 deny rules (CODE-21). /loop 10m. Tools run from the hq worktree. Isolation (arch §2.4, N-25) and the lane launcher referenced."
  - "1.0 (2026-09-29): first draft. Built and tested the four L.15 deliverables (runtime_settings.py,
     hold_guard.py, the monitor.py conductor_heartbeat check and --notify) against installed Claude
     Code v2.1.239; this runbook section records how to use them and what could and could not be
     confirmed about the installed CLI's settings schema."
---

# Suvarṇa — interim runtime safeguards (L.15)

**v1.2 note (plan v1.5).** The `/loop` interim is withdrawn (N-34): it needed a weekly native re-arm, and nothing may
rely on native attendance for progress (N-28). The durable supervised runtime (L.14) is an N-1 prerequisite and runs
every pass (§3). What remains in force from this document: the settings file (§2, §7), the hold-guard hook (§6) and the
Monitor checks (§5). Every tool here runs from the native-owned control checkout `/Users/Dev/suvarna/control` (N-37);
read `/Users/Dev/suvarna/hq/platform/...` in older text as `/Users/Dev/suvarna/control/platform/...`.

**v1.1 note (plan v1.4).** Where this document says `.claude/settings.local.json`, read the Suvarṇa settings file
`/Users/Dev/suvarna/config/claude-settings.json`, generated from the same committed template, owned by the native,
read-only to the swarm, and passed with `--settings` to every session, pass and lane (arch §2.4, §5.5; REVIEW_PASS2
C22). The template must carry arch §2.4's full deny list (CODE-21). Lanes start only through the lane launcher.

How to generate the two execution sessions' permission allowlist, watch the environment (including
each Conductor's own pulse) and enforce the hold at the tool boundary; starting the sessions and the
power/OS settings now live in the durable runtime (L.14) and NATIVE_SETUP_v1_0.md. Companion to `SUVARNA_RUNBOOK_v1_0.md` §2 steps 9 and
11–12, which this section supersedes in detail (the runbook's own step 9 pointed at a **committed**
`hq/.claude/settings.json`; L.15 builds the **local, uncommitted** `settings.local.json` instead —
see §5 below for why).

## §1 · What this adds

| Deliverable | File | What it does |
|---|---|---|
| Settings generator | `platform/scripts/governance/suvarna_tracker/runtime_settings.py` | Writes (or `--check`s) a local `.claude/settings.local.json` from the committed template `suvarna_tracker/runtime/settings.template.json`. |
| Settings template | `platform/scripts/governance/suvarna_tracker/runtime/settings.template.json` | The one source of truth for the allowlist: `defaultMode: dontAsk`, scoped `Edit(...)` rules, the Bash command allowlist, the credential/force-push/bypass denylist, and the hold-guard hook. |
| Hold guard hook | `platform/scripts/governance/suvarna_tracker/hold_guard.py` | A `PreToolUse` hook: while a hold is active in the hold ledger (`$SUVARNA_HOME/authority/HOLDS.jsonl`, N-35), blocks a new `Agent` dispatch and any dispatch-like Bash command; always refuses an attempt to alter the authority files. |
| Monitor additions | `platform/scripts/governance/suvarna_tracker/monitor.py` | A ninth check, `conductor_heartbeat` (warns when either session's Conductor has gone quiet, measured per session); `--notify`, a macOS notification on any change of the non-ok set. |

All four are tested (`platform/scripts/governance/suvarna_tracker/tests/test_runtime_settings.py`,
`test_hold_guard.py`, `test_monitor_runtime.py`); the full suite (345 tests as of this writing) passes.

## §2 · Generate the local settings

Run once per execution session's worktree, and again any time the template changes:

```
cd /Users/Dev/suvarna/control/platform/scripts/governance
python3 -m suvarna_tracker.runtime_settings --write /Users/Dev/suvarna/config/claude-settings.json   # v1.1 target (CODE-20); the native runs it (NATIVE_SETUP)
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

## §3 · Start the two sessions — the durable runtime (L.14)

**Withdrawn in v1.2 (N-34):** the interactive start plus `/loop 10m`. The two execution sessions run under the durable
supervised runtime (arch §5.5, L.14): launchd daemons running as the `suvarna` user, installed by the native once
(NATIVE_SETUP NS.8), that start change-triggered, stateless Conductor passes with backoff (`claude -p` with
`--settings /Users/Dev/suvarna/config/claude-settings.json --permission-mode dontAsk`), one fenced queue owner per
session, a per-session heartbeat (§5), and the Monitor watchdog. It is an **N-1 prerequisite** (launch gate LG.6).
Strategic Suvarṇa's own decision runtime is L.18 (arch §5.5), running as the native's account. The swarm's Claude
Code is pinned at 2.1.239 and authenticates as set up in NATIVE_SETUP NS.7. The daemons' exact commands live in L.14's
own files and NATIVE_SETUP NS.8, not here.

Unchanged rules: never pass `--dangerously-skip-permissions` and never select a `bypassPermissions` mode (charter P13) —
the generated settings' `deny` list also refuses any Bash invocation that itself tries to invoke one, as a second layer
(§6 below).

**Why `dontAsk` and not `acceptEdits`/`auto`:** there is no native present to answer a permission
prompt in an unattended session (charter §1: "the swarm runs long chains with the native absent");
`dontAsk` means the session never blocks on a prompt — a tool call outside the allowlist is refused
and logged, never silently worked around (charter P13, D5).

## §4 · Re-arm `/loop` weekly — withdrawn

Withdrawn in v1.2 (N-34, N-28): there is no `/loop` and no weekly or post-restart re-arm by the native. Restart after a
reboot, crash or usage-limit pause is the launchd daemons' and the Monitor watchdog's job (L.14); a usage-limit pause
waits rather than restart-loops (arch §5.5).

## §5 · Run the Monitor

In v1.2 the Monitor runs as one of L.14's launchd daemons as `suvarna` (NATIVE_SETUP NS.8), from the control
checkout, with these flags; the manual form below is for a drill only:

```
cd /Users/Dev/suvarna/control/platform/scripts/governance
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

**The ninth check, `conductor_heartbeat` (new, L.15; per session in v1.2):** reads
`$SUVARNA_HOME/run/EVENTS.jsonl` for the newest `kind: heartbeat, actor: conductor` line **of each session**
(`engine`, `exec`) separately, so one healthy Conductor never masks the other (Astra F6). `ok` with detail "no
conductor yet" for a session that has never emitted one — a fact about campaign phase, not a failure. The stale
threshold `SUVARNA_CONDUCTOR_STALE_MIN` is **three times the runtime's maximum pass backoff** (L.14's configured value),
the same threshold at which the watchdog relaunches; this replaces v1.1's fixed 45 minutes and its "three ten-minute
loops" wording, which no longer apply once passes are change-triggered with backoff (Astra F18). `warn`, never
`block`, on that check itself: the watchdog relaunches a stale Conductor (arch §5.5, charter G15).

Confirm on the dashboard within a few minutes of launch: a `conductor` heartbeat from each session and `monitor`
reading every check ok for the launch stage (the stage-aware matrix, launch gate LG.3), with no repeated
notifications for the same unresolved condition.

## §6 · The hold guard

Charter §8 (v1.5, N-35): while any hold is active, finish the items already running, dispatch nothing new;
production-visible actions stop at the next precondition check. A hold is a line in the append-only hold ledger
`$SUVARNA_HOME/authority/HOLDS.jsonl` (any role sets one with `python3 -m suvarna_tracker.hold --set --reason …`; the
swarm can append, never remove: file `uappnd`, directory native-owned) and is cleared only by a line in the
native-owned `authority/HOLD_CLEARS.jsonl` — SS clears a swarm-set hold after recording the cause resolved; only the
native clears a native (veto) hold. `run/SUVARNA_HOLD`, if present, is read as a hold, never as the clearing mechanism.
**The primary enforcement is at the dispatch boundary:** the build broker and the merge gate refuse while any hold is
active. `hold_guard.py` is the second layer, wired as the settings template's `PreToolUse` hook (matcher
`Bash|Agent`). **It runs the pinned control release** from `/Users/Dev/suvarna/control`
(`PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance`, N-37), never the group-writable hq worktree and
never `/Users/Dev/madhav-suvarna-plan`. It reads the hook's JSON off stdin and:

- **Always** refuses a Bash command that tries to write, move or delete anything under `$SUVARNA_HOME/authority/` or
  the legacy `run/SUVARNA_HOLD` — hold on or off (the storage permissions refuse it anyway; the hook logs the attempt).
- **While a hold is active**, refuses a new `Agent` dispatch, and a Bash command that is
  production-visible or dispatch-like (contains `suvarna-build`, `broker.py`, `merge_gate`, `suvarna_level_wave`,
  `nikasha_certify`, `gh pr merge`, `orchestrator`, or `--apply`).
- **Otherwise lets everything through** — git, tests, reads, the census, `emit` — because
  "finish what is already running" means exactly that, not "stop everything."
- **Fails closed on any malformed payload, for Bash and Agent alike** (Astra F4). If the hook cannot run at all (an
  import failure, an unreadable path, an unreadable hold ledger) or cannot parse its payload, it refuses (exit 2) the
  call and logs a `note` event (actor `hold-guard`) where it can; a hook failure must never let a call through.
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

Moved to **NATIVE_SETUP_v1_0.md NS.9** (v1.2): the `pmset` sleep/disksleep/autorestart settings, lid open, AC power,
automatic macOS updates and restarts off. They are `sudo`/system settings the native applies once; no agent role
performs them. Keeping `caffeinate` running is the Monitor's `--repair` job (§5), not a native step.
