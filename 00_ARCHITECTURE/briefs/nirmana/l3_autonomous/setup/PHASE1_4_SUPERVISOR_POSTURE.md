---
artifact: PHASE1_4_SUPERVISOR_POSTURE
canonical_id: PHASE1_4_SUPERVISOR_POSTURE
version: "1.0"
status: CURRENT
date: 2026-09-22
phase: L3 Kāla pre-elevation setup — Phase 1.4 (supervisor and session posture)
branch: l3/kala-p1-4-supervisor-posture
worktree: /Users/Dev/madhav-l3/p14-supervisor
governing_spec: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/readiness/_work/LANE_G_ENVIRONMENT_SPEC.md §2 (and §1.5 for 1.4c/1.4d)
scope: >
  Four operational controls that stop a broken overnight run from burning hours and money
  unnoticed: a progress detector that can actually read FALSE, an idle backoff, a harness-level
  permission scope, and a mechanically-guaranteed session-persistence environment.
  No production mutation, no migration, no credential rotation, no DB access of any kind was
  needed or performed by this phase.
---

# PHASE 1.4 — SUPERVISOR AND SESSION POSTURE

Every claim below is backed by a command run in this session, or is written as
`COULD NOT VERIFY`. Nothing is asserted from reading code alone (root `CLAUDE.md` §N.8).

## 0. What was delivered, and where

| # | Deliverable | Path (repo-relative) |
|---|---|---|
| 1.4a | progress detector + its rationale | `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/lib/progress.sh` (`progress_fingerprint`) |
| 1.4b | idle backoff | same file (`backoff_secs`) |
| 1.4a/b | before-fail / after-pass proof | `…/setup/tests/test_progress_and_backoff.sh` |
| 1.4c | permission scope | `.claude/settings.json` (repo root, project scope) |
| 1.4d | session-persistence env | `.claude/settings.json` `env` block **and** `…/setup/elevation_supervisor.sh` |
| all | the supervisor that uses them, plus a `preflight` that refuses to start if any control is absent | `…/setup/elevation_supervisor.sh` |

`/Users/Dev/madhav-l3/audit_supervisor.sh` was **read only, never edited** — LANE_G §2 itself
requires it be copied and adapted rather than overwritten ("the audit's own supervisor is a
historical artifact of a different, read-only campaign").

**Where the canonical copy should live — and why it moved into the repo.** LANE_G §2 does not
declare the supervisor a shared operational script that must stay at `/Users/Dev/madhav-l3/`.
It should live **in the repository**, at `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/`,
which is exactly where this repo already keeps an overnight supervisor
(`00_ARCHITECTURE/briefs/overnight_campaign_plans/ekv_supervisor.sh`, tracked). A script that
lives outside every git repo — as `audit_supervisor.sh` does — is unversioned, unreviewable and
undiffable, which is how defects C and D survived an entire campaign without anyone seeing them
in a diff. `elevation_supervisor.sh` is run from a checkout; `ROOT`, `WT`, `LOGD`, `STATE`,
`MODEL`, and every sleep tier are environment-overridable so no operator needs to edit it in place.

---

## 1.4a — the progress detector

### What LANE_G §2 requires

§2.1 ("Progress detector — confirmed defect C") quotes the live code (`audit_supervisor.sh`
lines 17, 48, 56–59):

```bash
fingerprint() { { git -C "$WT" rev-parse HEAD; git -C "$WT" status --porcelain; \
  shasum "$A/AUDIT_STATE.md" 2>/dev/null; ls -1 "$A" "$A/_work" 2>/dev/null; } | shasum | cut -c1-16; }
```

and states the defect: `git status --porcelain` and `ls -1` change on *any* file touch, so
"3-consecutive-no-progress can never fire even during a genuine stall (confirmed defect …— 5
consecutive cycles spent ~$0.80 each polling CI logged `progress=yes`)". §2.1 prescribes a
replacement keyed on a new commit, the `Accepted N/22` counter, and a hash of the state file's
substantive sections only.

### What was implemented

`lib/progress.sh::progress_fingerprint <worktree> <state-file>` emits four terms:

```
head | accepted | state_sub | tracked
```

1. **head** — `git rev-parse HEAD`: a real commit landed.
2. **accepted** — `Accepted N/22`, the campaign's own headline counter.
3. **state_sub** — sha of the state file's `## Position … ## End` block only. Not its mtime,
   not its timestamp header, not a "last supervisor cycle: N" line.
4. **tracked** — sha of `git diff HEAD` over **tracked** files, with liveness churn excluded:
   `**/*.log`, `**/*.ndjson`, `**/logs/**`, `**/EVENTS.jsonl`,
   `00_ARCHITECTURE/autonomy/state/*.jsonl` (HEARTBEAT, SPEND), `**/.DS_Store`, and the state
   file itself (term 3 already measures it, so a bumped timestamp cannot mask a stall).

**Why "progress" is defined this way.** The cycle contract these sessions run under (LANE_G §3.5,
carried verbatim from `AUDIT_CHARTER.md`) already says: *"a cycle is complete only if it pushed a
commit and rewrote the state file with its own cycle number."* So progress is defined as **what
survived into git, plus what the campaign's own declared counters say** — never as "some file
changed". This is why **untracked files are excluded entirely**: an untracked scratch note in
`_work/` is not progress; if it were real work the contract requires it committed by cycle end.
Term 4 goes beyond §2.1's prescription (which measures only HEAD + counter + state) so that a
cycle doing real, uncommitted work in a long-running packet is not wrongly called stalled.

**Residual risk, stated rather than hidden** (LANE_G §2.1 carries the same note): a cycle could
still move `head` with a cosmetic no-op commit. This detector does not close that adversarial
case. The honest-stop rule (LANE_G §3.6) is the defence against a *dishonest* agent; this is the
defence against an *honest* one's accidental false positive, which is what defect C actually was.
The cycle prompt in `elevation_supervisor.sh` now states the detector's exact rule to the agent
and explicitly tells it **not** to try to satisfy it.

### Proof — before FAILS, after PASSES

`tests/test_progress_and_backoff.sh legacy|new` runs the *same fixture and the same assertions*
against the old and the new implementation. The fixture simulates a genuinely stuck session:
it appends to the supervisor log and the cycle NDJSON, appends a heartbeat line to `EVENTS.jsonl`
and `HEARTBEAT.jsonl`, drops a scratch note in `_work/`, bumps the state file's
`last_supervisor_cycle:` / `updated:` header, and touches a deliverable's mtime — and commits
nothing, moves no counter, and changes no substantive state.

Assertions: **A1** three stuck cycles produce a no-progress streak of 3 (the halt can fire);
**A2** a genuine-progress cycle resets the streak to 0 (the detector is not simply always-false —
§N.8 cuts both ways); **A3/A3b** the backoff is tiered; **A4** the tracked-content term is live,
not permanently empty.

**RUN 1 — `./tests/test_progress_and_backoff.sh legacy` (today's behaviour) — FAILS:**

```
$ ./tests/test_progress_and_backoff.sh legacy
==============================================================
 PHASE 1.4a/1.4b proof — detector/backoff mode: legacy
==============================================================

-- A1: three consecutive genuinely-stuck cycles ---------------
  cycle 1  progress=yes  streak=0  sleep=30s
            before=a81686ef543ffe56
            after =b644789c8a2e6451
  cycle 2  progress=yes  streak=0  sleep=30s
            before=b644789c8a2e6451
            after =d54500e324565398
  cycle 3  progress=yes  streak=0  sleep=30s
            before=d54500e324565398
            after =18b3e3cc509ff94d
  FAIL  no-progress streak after 3 stuck cycles              got=0 want=3
  FAIL  3-strikes halt fires                                 got=never want=HALT

-- A2: a cycle that really moved the campaign -----------------
            before=18b3e3cc509ff94d
            after =41e29367038f395f
  PASS  genuine progress resets the streak                   got=0

-- A3: idle backoff actually spent over that stall -------------
            schedule = 30 30 30 (total 90s)
  FAIL  sleep after stuck cycle 1                            got=30 want=300
  FAIL  sleep after stuck cycle 2                            got=30 want=900
  FAIL  sleep after stuck cycle 3                            got=30 want=900

-- A3b: backoff function in isolation (independent of detector) -
  PASS  backoff crash=0 noprog=0                             got=30
  FAIL  backoff crash=0 noprog=1                             got=30 want=300
  FAIL  backoff crash=0 noprog=2                             got=30 want=900
  FAIL  backoff crash=0 noprog=3                             got=30 want=900
  PASS  backoff crash=3 noprog=0                             got=300
  PASS  backoff crash=5 noprog=2                             got=300

-- A4: the tracked-content term is live, not permanently empty --
     (A1 showed it ignores EVENTS/HEARTBEAT churn; this shows it does
      fire for an UNCOMMITTED edit to a real deliverable — so the term
      has a real detector behind it, not a constant. CLAUDE.md §N.8.)
            before=41e29367038f395f
            after =5cd75601022b0370
  PASS  uncommitted deliverable edit counts as progress      got=yes

RESULT: FAILURES PRESENT (legacy)
legacy exit=1
```

**RUN 2 — `./tests/test_progress_and_backoff.sh new` (after the fix) — PASSES:**

```
$ ./tests/test_progress_and_backoff.sh new
==============================================================
 PHASE 1.4a/1.4b proof — detector/backoff mode: new
==============================================================

-- A1: three consecutive genuinely-stuck cycles ---------------
  cycle 1  progress=NO   streak=1  sleep=300s
            before=442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
            after =442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
  cycle 2  progress=NO   streak=2  sleep=900s
            before=442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
            after =442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
  cycle 3  progress=NO   streak=3  sleep=900s
            before=442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
            after =442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
  PASS  no-progress streak after 3 stuck cycles              got=3
  PASS  3-strikes halt fires                                 got=HALT

-- A2: a cycle that really moved the campaign -----------------
            before=442a485aa890|Accepted 0/22|6722e39197305887|da39a3ee5e6b4b0d
            after =12acc3e4c64a|Accepted 1/22|5cee5fc0b3a3b25b|da39a3ee5e6b4b0d
  PASS  genuine progress resets the streak                   got=0

-- A3: idle backoff actually spent over that stall -------------
            schedule = 300 900 900 (total 2100s)
  PASS  sleep after stuck cycle 1                            got=300
  PASS  sleep after stuck cycle 2                            got=900
  PASS  sleep after stuck cycle 3                            got=900

-- A3b: backoff function in isolation (independent of detector) -
  PASS  backoff crash=0 noprog=0                             got=30
  PASS  backoff crash=0 noprog=1                             got=300
  PASS  backoff crash=0 noprog=2                             got=900
  PASS  backoff crash=0 noprog=3                             got=900
  PASS  backoff crash=3 noprog=0                             got=300
  PASS  backoff crash=5 noprog=2                             got=300

-- A4: the tracked-content term is live, not permanently empty --
     (A1 showed it ignores EVENTS/HEARTBEAT churn; this shows it does
      fire for an UNCOMMITTED edit to a real deliverable — so the term
      has a real detector behind it, not a constant. CLAUDE.md §N.8.)
            before=12acc3e4c64a|Accepted 1/22|5cee5fc0b3a3b25b|da39a3ee5e6b4b0d
            after =12acc3e4c64a|Accepted 1/22|5cee5fc0b3a3b25b|1195ba79e11bea25
  PASS  uncommitted deliverable edit counts as progress      got=yes

RESULT: ALL ASSERTIONS PASS (new)
new exit=0
```

The legacy detector logged `progress=yes` on every one of three genuinely stuck cycles
(`streak=0` throughout) — i.e. the 3-strikes halt is unreachable, exactly as §2.1 says. The new
detector returns a **byte-identical fingerprint** across all three, reaching `streak=3` and
firing the halt, while still reporting progress for a real commit (A2) and for an uncommitted
deliverable edit (A4: the `tracked` term moves from the empty-sha `da39a3ee5e6b4b0d` to a real
value). The detector has now been observed reading both TRUE and FALSE.

---

## 1.4b — idle backoff

### What LANE_G §2 requires

§2.2 ("Idle backoff — confirmed defect D") quotes `audit_supervisor.sh` line 63:

```bash
[ $crash -ge 3 ] && sleep "$CRASH_SLEEP" || sleep "$CYCLE_SLEEP"
```

— two tiers only (30s normal, 300s after 3 crashes), "nothing scales with consecutive
no-progress". §2.2 prescribes: crash tier unchanged; 1st no-progress cycle 300s; 2nd 900s; no
third tier, because the existing 3-strikes halt makes one unreachable.

### What was implemented

`lib/progress.sh::backoff_secs <crash> <noprog>` — implemented exactly as §2.2 specifies.
§2.2 left no parameter genuinely open (it names 300 and 900 itself), so nothing was invented;
all four values are env-overridable (`CYCLE_SLEEP`, `CRASH_SLEEP`, `IDLE_SLEEP_1`, `IDLE_SLEEP_N`)
so an operator can tune without editing logic.

| condition | sleep | rationale |
|---|---|---|
| `crash >= 3` | 300s | unchanged from the audit supervisor |
| `noprog == 1` | 300s | first honest idle — give CI/a blocker time to clear |
| `noprog >= 2` | 900s | second idle — the run is probably genuinely blocked |
| otherwise | 30s | unchanged |

**Justification against the real cost.** The failure this prevents is the documented one: five
consecutive cycles at ~$0.80 each, fired 30 seconds apart, polling CI with nothing to do. With an
honest detector plus this backoff, the same stall costs three cycles spread over **2100 seconds**
of waiting instead of 90 (proof run A3), and the halt still fires at exactly the same strike
count — only the money and wall-clock spent reaching it change. The crash tier is kept separate
from the idle tier because a crashing run and an idling run need different treatment and
conflating them is how the single-tier version lost the distinction in the first place.

### Proof

Same two runs above. A3 (backoff actually spent over a 3-cycle stall):
legacy `30 30 30 (total 90s)` → FAIL; new `300 900 900 (total 2100s)` → PASS.
A3b tests `backoff_secs` in isolation from the detector, so 1.4b's proof does not depend on
1.4a's: legacy answers 30s for `noprog` 1, 2 and 3 (three FAILs); new answers 300/900/900, and
both agree on the crash tier (`crash=3 → 300`, `crash=5,noprog=2 → 300`).

---

## 1.4c — `.claude/settings.json` allow/deny scope

### What LANE_G §1.5 requires

A scoped allow/deny list, `.claude/settings.json` (project, not `settings.local.json`), because
`--dangerously-skip-permissions` with no scope means every campaign constraint — "read-only",
"never run mutating git", "never print credentials" — was enforced "**purely by the prompt text,
with zero technical backstop**". §1.5 offers a starting proposal and explicitly calls it
"a starting proposal, not a validated final list". It is LANE_G Gap #2, severity
**BLOCKS-CAMPAIGN**. §2.3 separately records a `COULD NOT VERIFY`: which flag combination means
"obey settings.json but never block on a prompt".

### The design trade-off, stated

A deny rule that is too broad blocks legitimate work at 3am with nobody awake to approve it.
So the file **denies the specifically dangerous things and allows broadly otherwise** — it does
not try to enumerate every legitimate command. Concrete instances of that choice:

* **Only `deploy.yml` is denied, not `.github/workflows/**`.** LANE_G Gap #7 asks the campaign to
  *add* a CI lint for the migration-number partition; denying the whole workflows directory would
  block its own remedy.
* **Migration denies are ranged, not blanket.** Applied migrations (`NNN_*`, `1000–1070_*`,
  `ws2_*`) and Pūrṇa's range (`1120+`) are denied; the campaign's own `1071–1119` range is open.
  A blanket `platform/migrations/**` deny would have blocked the campaign's authorized work.
* **`psql` write denies are limited to the irreversible set** (`DROP DATABASE|SCHEMA|TABLE|OWNED|
  ROLE`, `ALTER ROLE`, `TRUNCATE`). A blanket ban on `INSERT`/`UPDATE` would break the
  disposable-PG15 harness (LANE_G §1.3), which is the campaign's *sanctioned* write path.
* **`Bash(*gcloud secrets versions access*)` is denied, but `Bash(source …/dbenv.sh*)` is
  allowed.** Permission rules match the command string handed to the Bash tool; `dbenv.sh` runs
  `gcloud secrets` *inside* the sourced file, where no rule sees it. The sanctioned read-only DB
  path keeps working; a session reaching for a secret directly does not.
* **A session may not widen its own scope**: `Edit(.claude/settings.json)`,
  `Edit(.claude/settings.local.json)` and `Edit(//Users/Dev/.claude/settings.json)` are denied.
* Writes to the other campaign worktrees (`readiness`, `audit`, `review`, `setup`) and to
  `/Users/Dev/Vibe-Coding/Apps/Madhav` are denied; **reads are not**, because cross-checking a
  sibling worktree read-only is legitimate and blocking it would cost a cycle at 3am.

The file carries **34 allow rules and 62 deny rules**. `--dangerously-skip-permissions` is
dropped from the supervisor in favour of `--permission-mode bypassPermissions` (see the verified
finding below) — but note the deny list binds under **both**, so the choice is not load-bearing
for safety.

### How it was verified — executable, not asserted

Claude Code **2.1.239**. Every probe ran a real `claude -p` session; refusal text is quoted
verbatim from the session's own report.

**(a) The file parses.**
```
$ python3 -c "import json;json.load(open('.claude/settings.json'))" && echo PARSE-OK
PARSE: OK
env keys      : ['CLAUDE_CODE_FORCE_SESSION_PERSISTENCE']
allow rules   : 34
deny rules    : 62
```

**(b) The harness reads it, and deny binds under `--permission-mode bypassPermissions`** — the
mode `launch.sh` uses. Probe run with cwd = this worktree:

```
1. Bash: echo "PERSIST=[$CLAUDE_CODE_FORCE_SESSION_PERSISTENCE]"  → PERSIST=[1]
2. Bash: printenv HOME        → Permission to use Bash with command printenv HOME has been denied.
3. Bash: git stash list       → Permission to use Bash with command git stash list has been denied.
4. Write platform/migrations/999_p14_probe.sql   → File is in a directory that is denied by your permission settings.
5. Write platform/migrations/1069_p14_probe.sql  → File is in a directory that is denied by your permission settings.
6. Write 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/_probe_allowed.md → File created successfully
```

**(c) Control: the globs are precise, not a blanket directory deny.** The refusal text in (4)/(5)
says "directory", so a control was run to prove the *ranges* are what denied them:

```
1) Write platform/migrations/1075_p14_control.sql  (campaign range 1071–1119) → File created successfully
2) Write platform/migrations/1121_p14_control.sql  (Pūrṇa range 1120+)        → denied
```
Both probe artefacts were deleted afterwards; `git status --porcelain platform/migrations/` is clean.

**(d) Deny binds under `--dangerously-skip-permissions` too** (the flag `audit_supervisor.sh`
uses), in a scratch fixture:
```
2) printenv P14_PROBE_MARKER → Permission to use Bash with command printenv P14_PROBE_MARKER has been denied.
3) p14lead --go              → Permission to use Bash with command p14lead --go has been denied.
CONTROL: p14other --go       → the shell ran it: "Exit code 127 ... command not found: p14other"
```
The control matters: it shows the refusal in (3) came from the `Bash(*p14lead*)` deny rule and not
from some blanket refusal, and therefore that **leading-wildcard Bash rules do match** in 2.1.239.

**This resolves LANE_G §2.3's `COULD NOT VERIFY`.** The answer is
`--permission-mode bypassPermissions`: it never blocks on a prompt, and the settings deny list
still binds. It also binds *against* the user's global `~/.claude/settings.json`, which carries a
blanket `"Bash"` / `"Bash(*)"` allow and `defaultMode: bypassPermissions` — deny outranks allow
from a higher-precedence source, demonstrated by (b2) and (d2).

**(e) No dead rule forms.** The harness prints a warning for every permission rule written in a
form it never matches. Running a session in this worktree produced **twelve such warnings, all of
them for `/Users/Dev/.claude/settings.json`** (the user's global file: `Glob(**)`, `Write(**)`,
`MultiEdit(**)`, `NotebookEdit(**)`, `Write(//Users/Dev/.ssh/**)`, …) and **zero** for this
project file. `elevation_supervisor.sh preflight` now enforces that mechanically:

```
  OK    1.4c deny list non-empty (62 rules)
  OK    1.4c no dead rule forms (Write/Glob/NotebookEdit path rules)
```
and the negative control (a settings file whose only rule is `Write(.github/workflows/deploy.yml)`):
```
  FAIL  1.4c dead rule form(s), never matched by the harness: ['Write(.github/workflows/deploy.yml)']
preflight: FAIL — supervisor will not start
```

**Finding carried out of this phase:** LANE_G §1.5's proposed list contains dead rules —
`Write(platform/**)`, `Write(00_ARCHITECTURE/briefs/nirmana/**)`,
`Write(.github/workflows/deploy.yml)`, `Write(platform/tests/pariprashna/**)`. Only `Edit(path)`
rules are matched by file permission checks; `Edit` covers Write, Edit and NotebookEdit. The
committed file uses `Edit(...)` throughout. This is a §N.8 defect in the proposal itself — four
rules that read as protection and could never fire — and it is the reason `preflight` checks for
the form rather than trusting the author.

**Committed despite `.gitignore`.** `.gitignore` line 5 is `.claude/`, so
`git check-ignore -v .claude/settings.json` reports it ignored; the `!.claude/agents/` /
`!.claude/skills/` negations on lines 6–9 are **dead** (git cannot re-include a path whose parent
directory is excluded — `git check-ignore -v .claude/agents/foo.md` also reports it ignored; those
files are tracked only because they were force-added). The file is therefore force-added the same
way, `git add -f .claude/settings.json`, which is this repo's existing practice. `.gitignore` was
deliberately **not** edited: adding another `!` negation under an excluded directory would be one
more rule that reads as working and does nothing.

---

## 1.4d — mechanical `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`

### What LANE_G requires

§1.5: the two lines `unset CLAUDE_CODE_CHILD_SESSION` / `export
CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` "must be set before every nested/parallel session spawn —
currently this appears only as prose in one audit prompt file … zero mechanical enforcement".
LANE_G Gap #1.

### Where it was put, and why that location guarantees it

| # | Location | What it guarantees |
|---|---|---|
| 1 | `.claude/settings.json` `env` block | **The guarantee that cannot be forgotten.** Read by *every* session whose cwd is a checkout of this repo, regardless of who launched it or how — supervisor, `launch.sh`, or a human typing `claude` in a worktree. No launcher has to remember. |
| 2 | `elevation_supervisor.sh` top (`unset` + `export`) | Process environment, inherited by the `claude` process and by every in-process Agent-tool subagent. **This is the only place that can UNSET `CLAUDE_CODE_CHILD_SESSION`** (see the verified limitation below). |
| 3 | `elevation_supervisor.sh` cycle launch line (`env -u CLAUDE_CODE_CHILD_SESSION CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1 gtimeout … claude …`) | Re-asserted per cycle, so a long-running supervisor cannot inherit a stale value if something re-exports it between cycles. |
| 4 | `elevation_supervisor.sh preflight` | Refuses to start if (1) or (2) is not actually in effect. A control that is silently absent is worse than no control. |

`/Users/Dev/madhav-l3/launch.sh` already does the same two lines (its lines 12–13) and was **not
edited** — it is outside this worktree and outside this phase's scope.

### Verified in a launched session, not assumed

The launching shell explicitly `unset` the variable first, so a pass could not come from
inheritance:

```
$ unset CLAUDE_CODE_FORCE_SESSION_PERSISTENCE CLAUDE_CODE_CHILD_SESSION
$ cd <dir with .claude/settings.json declaring the env block>
$ claude -p --permission-mode bypassPermissions --model haiku '…echo "PERSIST=$CLAUDE_CODE_FORCE_SESSION_PERSISTENCE"…'
   → MARKER=probe-ok PERSIST=1
```
Confirmed the same way under `--dangerously-skip-permissions` (`PERSIST=1 MARKER=probe2-ok`) and
in this worktree against the real committed file (`PERSIST=[1]`, probe (b1) above).

### Verified limitation — stated, not papered over

A settings `env` block **cannot unset an inherited variable.** Probed directly: with
`CLAUDE_CODE_CHILD_SESSION=1` in the launching environment and
`"CLAUDE_CODE_CHILD_SESSION": ""` in the settings `env` block, the launched session reported
`CHILD=[1] PERSIST=[1]` — the inherited value won. So the harness-level guarantee covers
*forcing persistence* everywhere, but **clearing `CLAUDE_CODE_CHILD_SESSION` is only achievable
from the launching process** (supervisor / `launch.sh`). LANE_G Gap #1's real residual — a human
manually launching a second top-level `claude` from inside a first — is therefore **not** closed
by settings.json and remains a discipline rule. The cycle prompt now states it explicitly:
all parallelism goes through in-process Agent-tool subagents; never launch a second top-level
`claude` from inside a cycle.

---

## 2. The live-path test — what actually invokes what, today

| Control | Live caller today | Status |
|---|---|---|
| 1.4a detector, 1.4b backoff | `elevation_supervisor.sh` (this phase's new script) | **No live caller found within scope** (scope searched: `grep -rIl` for `audit_supervisor.sh`, `launch.sh`, `elevation_supervisor` across this whole worktree excluding `.git`/`node_modules`; `ps -Ao command` for any running supervisor/launcher; `/Users/Dev/madhav-l3/` directory listing). The elevation campaign has not been launched. The audit supervisor is the only supervisor with a history of live use and it is currently held: `/Users/Dev/madhav-l3/AUDIT_HOLD` exists, and `audit_supervisor.sh run` refuses to start while it does. No supervisor process is running. |
| 1.4c settings.json | every `claude` session whose cwd is a checkout containing it | **Live, but branch-scoped today.** Verified live in this worktree (probes (b), (c), (e)). `git cat-file -e origin/main:.claude/settings.json` → absent on `origin/main`, so it binds only on this branch until merged. The campaign worktrees (`kala-frontier` / `kala-spine` / `kala-kshetra`, LANE_G §1.1) are branched from `origin/main` at creation time — **they will not carry this file until this branch lands on `main`.** That is the single gating dependency for Gap #2 actually closing. |
| 1.4d env | `elevation_supervisor.sh` (not yet called), `launch.sh` (the live interactive conductor launcher, already sets it at its lines 12–13), and `.claude/settings.json` (live in any checkout carrying it) | Live via settings.json in this worktree; verified. |

**The script the campaign actually launches today** is `/Users/Dev/madhav-l3/launch.sh` — it
`cd`s to `/Users/Dev/madhav-l3/integration`, reads `/Users/Dev/madhav-l3/NEXT_PROMPT.md`, and
execs `caffeinate -dimsu claude --permission-mode bypassPermissions`. It is an *interactive
conductor* launcher, not a cycle supervisor: it has no progress detector and no backoff to fix.
It is outside this worktree and was not edited. A supervisor fix in a script nothing invokes is
not a fix, so this is stated plainly: **`elevation_supervisor.sh` becomes live only when the
campaign's kickoff runbook calls it instead of, or alongside, `launch.sh`.** Wiring that is not
this phase's scope.

---

## 3. What remains open

1. **Gap #2 does not close until this branch reaches `origin/main`.** Campaign worktrees branch
   from `origin/main`; until the merge, `.claude/settings.json` exists only here. (This phase was
   instructed not to push or open a PR.)
2. **`elevation_supervisor.sh` has no live caller.** The kickoff runbook must invoke
   `elevation_supervisor.sh preflight` then `run`, with `WT` pointed at the campaign worktree.
3. **The state file the detector reads does not exist yet.** `progress_fingerprint` expects
   `…/l3_autonomous/KALA_ELEVATION_STATE.md` with an `Accepted N/22` line and a
   `## Position … ## End` block. Whoever seeds the campaign state must create it in that shape;
   `preflight` fails loudly if it is missing, and the detector degrades to `NO-COUNTER` plus an
   empty-section hash (still a stable, i.e. correctly no-progress, value) rather than crashing.
4. **The no-op-commit gaming case is deliberately not closed** (LANE_G §2.1's own residual risk).
   Defence is the honest-stop rule, not the detector.
5. **`CLAUDE_CODE_CHILD_SESSION` cannot be cleared by settings.json** (verified above). Gap #1's
   nested-top-level-session residual remains a discipline rule.
6. **`/Users/Dev/.claude/settings.json` carries twelve dead permission rules** (`Write(...)`,
   `Glob(**)`, `MultiEdit(**)`, `NotebookEdit(**)` path forms), including deny rules protecting
   `~/.ssh`, `~/.aws`, `~/.config/gcloud` and `~/Library/Keychains` that **never fire** — each of
   those paths is also covered by a matching `Read(...)`/`Edit(...)` rule, so the protection is
   not absent, but the `Write(...)` half of each pair is decorative. User-scope file, outside this
   phase's write scope; reported, not touched.
7. **`Bash(*psql*…*)` denies are string matches, not SQL parsing.** They stop the obvious
   irreversible statement typed into a `psql -c`; they do not stop a destructive statement inside
   a `.sql` file passed with `-f`, or one built by a script. The role-level backstop LANE_G §1.2
   asks for (`REVOKE INSERT, UPDATE, DELETE, TRUNCATE … FROM amjis_app`) is the real control and
   is still open as LANE_G's own gap.
8. **Not verified from here:** whether `elevation_supervisor.sh run` completes a real cycle
   end-to-end. `preflight` was exercised in three configurations (pass, missing-state-file fail,
   dead-rule fail); `run` was not, because it would launch a paid multi-hour campaign cycle
   against a worktree that does not exist yet. `COULD NOT VERIFY: elevation_supervisor.sh run
   against a live campaign worktree — the campaign worktrees (kala-frontier/spine/kshetra) have
   not been created, and running it would dispatch real campaign cycles, which is outside this
   phase's authorisation.`

---

## 4. Safety record for this phase

No production change, no migration authored or applied, no credential rotated, no `WATCHDOG_SECRET`
access, and **no database access of any kind** — this phase needed none.
`/Users/Dev/madhav-l3/audit_supervisor.sh`, `launch.sh`, `stream_format.sh`, `redact.py`,
`BOOTSTRAP.md` were read only. No file outside `/Users/Dev/madhav-l3/p14-supervisor` was written.
The probe fixtures live in the session scratchpad, not in the repo; the two probe artefacts
written into the worktree by the permission probes were deleted and verified gone.
`/Users/Dev/madhav-l3/redact.py --scrub` was run over the worktree before commit.
Nothing this phase wrote captures process output: the supervisor's cycle pipe already routes the
agent's stream through `redact.py` before it reaches any file, and the launch line deliberately
never echoes or logs the environment at all — `preflight` reports only whether a variable equals
`1`, never its value, and never enumerates the environment.
