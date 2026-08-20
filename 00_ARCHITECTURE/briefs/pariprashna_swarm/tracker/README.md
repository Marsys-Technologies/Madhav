# Paripraśna Execution Observatory (tracker-v2)

Derived-not-narrated live tracker for the Paripraśna swarm build (CLAUDE.md §N.8, earned
signal, applied to the instrument rather than the product). Supersedes the P0-D tracker
(`00_ARCHITECTURE/briefs/pariprashna_swarm/state/{SWARM_TRACKER.json,tracker.html,...}`)
going forward — see the note appended to `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md`.

## Layout

- **Code source** (`00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/` in the repo,
  versioned): `PLAN.yaml` (declarative plan — JSON, which is valid YAML, so this stays
  stdlib-only), `_common.py`, `tracker_emit.py`, `collect.py`, `project.py`, `trackerd.py`,
  `watchdog.py`, `serve.py`, `tracker.html`, `selftest.py`, `launchd/*.template`,
  `install.sh`.
- **Code execution surface** (`$HOME/.pariprashna-tracker-code/` — see "Deployment model"
  below): an immutable copy of the above, materialised by `install.sh --install-from-ref`.
  This, not the repo checkout, is what the launchd jobs actually run.
- **Runtime state** (outside the repo, never appears in `git status`): `~/.pariprashna-tracker/`
  — `events/<writer_id>.jsonl` (append-only), `state.json`, `tracker_data.js`,
  `heartbeat.json`, `collector_snapshot.json`, `trackerd.pid`, `serve_token`, `logs/`.

Python 3 standard library only. No pip installs, no npm, nothing that can perturb the
build environment. The tracker only ever *reads* git (`--no-optional-locks`, `for-each-ref`
/ `rev-list` / `worktree list` / `show` / `merge-base` / `log`) — it never touches an
index, never checks anything out, never enters another worktree.

## Deployment model: frozen snapshot, never the repo checkout

**The repo checkout is never the execution surface.** A live `git checkout` in whatever
directory the daemon happened to be running from would silently swap a running daemon's
code out from under it mid-cycle, and a checkout under `/tmp` can vanish on reboot or
periodic cleanup. Both are real incidents this tracker hit on its first install.

```sh
# One-time / update: materialise an immutable snapshot from a MERGED commit (never from a
# working tree) and (re)install all three launchd jobs to point at it. No observability gap
# longer than one collector cycle — the runtime dir (~/.pariprashna-tracker/, state.json,
# the event log) is untouched by this; only the code directory and the jobs change.
./install.sh --install-from-ref origin/main \
             --prefix "$HOME/.pariprashna-tracker-code" \
             --repo /path/to/any/local/checkout/with/origin/fetched \
             --runtime-git-repo /path/to/a/PERMANENT/checkout
```

`--repo` only needs the ref reachable (`git archive` reads objects, never the working
tree) — any checkout with `origin` fetched works, even a scratch one you delete right
after. `--runtime-git-repo` is different: it's what the **deployed daemon** uses for its
own ongoing read-only git operations (branch/PR derivation, campaign-coordination reads,
the staleness check below) via the `TRACKER_GIT_REPO` environment variable baked into the
launchd plists — it must still exist after `install.sh` exits, so point it at your main,
permanent checkout, not a worktree you're about to remove.

**Provenance is on the dashboard, not just in a file.** `tracker.html`'s header shows the
running code's short sha, classified into one of four states (`classify_code_provenance`,
`_common.py`) rather than a single binary "stale" flag — the binary version conflated
"unmerged, ahead of main" with "genuinely behind" (both read `is_current: false`), training
readers to discount an amber that, when real, matters:

- **CURRENT** (green) — the installed sha is merged and already has everything `origin/main`
  has for this `tracker/` subtree.
- **AHEAD** (neutral, not amber) — unmerged, but already has everything `origin/main` has for
  `tracker/` — e.g. deployed pre-merge for live verification (this is this observatory's own
  normal workflow: every `install.sh --install-from-ref <branch>` run before a PR merges).
- **BEHIND** (amber) — merged, but `origin/main` has since gained `tracker/`-touching commits
  this sha lacks. Genuinely stale — the pill also names the commit count.
- **DIVERGED** (amber) — neither an ancestor of `origin/main` nor has everything it does for
  `tracker/` — no clean ordering (e.g. after a rebase/force-push). A real anomaly.

In-place/dev runs (no `INSTALLED_FROM.json`) show `code UNKNOWN` honestly rather than a fake
green. Each of the four states has its own selftest, each observed failing first by
neutering the classifier and confirming the wrong state was returned for AHEAD/BEHIND/DIVERGED.

Dev/local testing only — **not** for a standing install:

```sh
# one-shot cycle:
python3 trackerd.py --once

# falsifiable self-test suite (freezes, breaks, verifies red, unfreezes):
python3 trackerd.py --selftest

# in-place mode: points the jobs at THIS script's own directory (mutable, no provenance)
./install.sh
```

## Ref freshness: the private mirror

**Every `origin/*` git read comes from a mirror this daemon owns outright, fetched on its
own cadence — never from a shared checkout whose remote-tracking refs only advance when
some unrelated process happens to fetch there.** That was a real bug in the first version
of this tracker: lane branches, ahead/behind, the "is this code current" check, and the
coordination-lease cell all silently read whatever `origin/*` last resolved to in the
shared checkout — plausible-looking, quietly stale, exactly the failure mode this tracker
exists to catch (CLAUDE.md §N.8, one layer down: the detector itself needs a real
detector).

- **`~/.pariprashna-tracker/mirror.git`** — `git clone --mirror`, bootstrapped
  automatically on first cycle if missing (~60s, ~130MB for this repo), then
  `git fetch --prune` every cycle after (~1-2s, incremental). `collect.py`'s
  `mirror_fetch()` owns this entirely; nothing in `install.sh` sets it up.
- Ref names inside a mirror have **no** `refs/remotes/origin/` prefix — `git clone
  --mirror` maps the remote's refs verbatim into the mirror's own `refs/heads/*` and
  `refs/tags/*`. Read `main`, `pariprashna/p0`, `campaign-coordination`, never
  `origin/main`.
- **The shared checkout is still read** — read-only, `--no-optional-locks`, via
  `TRACKER_GIT_REPO` — but for exactly one thing a bare mirror structurally cannot
  provide: `git worktree list`. (Filesystem-based signals like `expected_artifacts` path
  existence and migration numbering also still read the shared checkout's working tree —
  that's a different kind of signal than ref freshness, not the bug this fixes.) These two
  git sources are deliberately not consolidated: collapsing them back into one is how this
  bug happens again.
- **A failed fetch degrades every mirror-derived cell to `UNKNOWN`** with the fetch error
  as provenance for that cycle — it never falls back to whatever the mirror's on-disk refs
  still say from the last successful fetch, even though that data is still physically
  there. Consecutive failures are counted across cycles (`~/.pariprashna-tracker/mirror_fetch_state.json`).
- **Ref freshness is its own header pill** — a third liveness axis, independent of observer
  freshness (is the tracker alive) and subject progress (is the swarm moving): the
  observatory can be alive, the swarm can be moving, and the refs it's reasoning from can
  still be stale, all independently. ≤60s green · 60–180s amber "REFS LAGGING" · >180s red.
- **Free consistency check**: `gh` is network-live, the mirror can lag it by up to one
  fetch cycle. Every cycle, the last 20 merged PRs (`gh pr list --state merged`) get their
  merge commit checked against the mirror's `main` via `git merge-base --is-ancestor`. If
  `gh` says merged but the mirror disagrees, that's a real divergence — an `anomaly`
  event fires. This is the one cell where being confidently wrong recreates the PR #1341
  incident (a stale lease/merge read treated as current).

### Operational proof (item 7, 2026-08-20): a real push, propagating and then not

Ref freshness matters because, without it, two very different situations render
identically: "the lane hasn't pushed yet" and "this tracker's refs are frozen." Selftest
already proves the classification function's boundaries on synthetic ages
(`test_ref_freshness_boundaries`); this is the operational version — a real branch pushed
to the real remote, a real mirror, real elapsed wall-clock time, run against an isolated
copy of this daemon (`HOME` override, so none of it touched the live
`~/.pariprashna-tracker/` another campaign's monitoring depends on):

1. Bootstrapped an isolated mirror, ran one cycle — baseline, no demo branches present.
2. Pushed `pariprashna/zz-demo-ref-freshness-a` to `origin`. Ran one cycle
   (`git fetch --prune`, 1585ms): the branch appeared in `git_lane_branches` immediately.
3. Broke the mirror's own remote (`git remote set-url origin
   https://invalid.example.invalid/...`, isolated to this one demo mirror clone — never
   touches the shared checkout or the production mirror). Pushed
   `pariprashna/zz-demo-ref-freshness-b`. Ran a cycle immediately: `mirror_fetch.ok=false`,
   and — this is the finding worth stating precisely — **the entire `git_lane_branches`
   cell went `evidence_class: UNKNOWN`, not "branch A only."** The code already refuses to
   serve the mirror's still-physically-present on-disk refs once this cycle's fetch has
   failed (see "Ref freshness" above). That is a *stronger* resolution of the ambiguity
   than freezing at the last-good list would have been: a frozen A-only list could be
   misread as "nothing new happened," where an honest UNKNOWN cannot be misread as anything
   but "can't tell right now."
4. Left the fetch broken and let real time pass, re-running a cycle at each point:
   age=57.6s → `green`, age=124.0s → `amber`, age=250.4s → `red`. Branch B never appeared
   at any point; `git_lane_branches` stayed `UNKNOWN` throughout, provenance = the actual
   `Could not resolve host` error.
5. Restored the remote URL. Next cycle: `mirror_fetch.ok=true`, both
   `zz-demo-ref-freshness-a` and `-b` appeared together, ref age back to 2.4s (`green`).
6. Cleanup: both demo branches deleted from `origin`, the isolated `HOME` runtime dir
   removed. The production daemon's own `~/.pariprashna-tracker/heartbeat.json` was
   confirmed untouched by any of the above (separate `HOME`, separate mirror, separate
   pidfile).

## The 2026-08-19 incident: a real 23m37s blind window

Measured from the event log, not reconstructed after the fact: last heartbeat before the
gap was cycle 94 at `2026-08-19T20:35:52Z`. The macOS unified log
(`log show --predicate 'eventMessage CONTAINS "com.marsys.pariprashna"'`) shows all three
launchd jobs — `trackerd`, `watchdog`, `serve` — explicitly `removing service`d in the same
instant, `2026-08-19T20:36:22Z`: a deliberate `launchctl bootout`, not a crash and not a
sleep/wake cycle (`pmset -g log` shows no sleep transition in the window). Nothing
resurrected them until `2026-08-19T20:59:13Z`, when `backgroundtaskmanagementd` re-registers
all three from the plists on disk — a full reinstall, not a self-heal. First new heartbeat:
`cycle: 1` at `20:59:29Z` (the counter reset confirms a brand-new process, not a resumed
one). **`watchdog.jsonl`, this tracker's own T2 event log, is silent across the entire
window** — its only entry is an unrelated resurrection from hours earlier. T2 could not
have helped: whatever removed the jobs removed the watchdog too, and a watchdog that no
longer exists cannot watch anything.

**Attribution (2026-08-20 follow-up), corrected from the first pass.** The macOS unified
log resolves the exact `launchctl` process shape at both timestamps, not just the launchd
side of it:

- `20:36:22Z`: three **separate, bare `launchctl bootout` processes** (PIDs 68296-68298,
  each `launchctl` alone with no accompanying `bootstrap`), preceded 12s earlier by a
  `launchctl list` (PID 68033) — the shape of someone checking status, then stopping.
- `20:59:13Z`: three **`bootout`+`bootstrap` PAIRS** (PIDs 6864-6872) — the shape of
  `install.sh`'s own per-job loop (bootout immediately followed by bootstrap, for each job
  in turn), confirming the recovery was a real `install.sh` run.

This rules out the first-pass theory that `20:36:22Z` was a stalled or interrupted
`install.sh` run: `install.sh`'s loop always pairs bootout with bootstrap per job, so a
partial run would show *some* bootstraps interleaved, not three bare bootouts. What the
`20:36:22Z` shape matches **exactly** is the old undocumented "Stop all three" one-liner this
very `install.sh` used to print at the end of every run (see item (b) below) — a plain
`for j in trackerd watchdog serve; do launchctl bootout ...; done`, no marker, no record of
intent, no accompanying bootstrap.

*Who ran it* could not be recovered: process parent/responsible-PID chains are not retained
by the unified log for `launchctl` invocations, shell history on this machine carries no
timestamps, `last` shows one continuous console login spanning the whole day (single-user
Mac, uninformative), and an exhaustive search of every local Claude Code session transcript
active in the window — the long-running main session covering the full incident window, all
~40 of its subagents, every other project directory under `~/.claude/projects`, Codex
session stores, and Claude Desktop's session stores — found no literal record of the command
being issued. The nearest context: an ambient screen-activity summary
(`.codex/memories/.../2026-08-19T20-20-00-*-10min-memory-summary.md`) shows a *different*
Paripraśna-tracker hardening closeout (PR #1353) had just finished verifying the daemon
healthy at `~20:23Z` (cycle 4 — a recent restart) before the user's visible focus moved to
an unrelated repo; that session's own transcripts don't contain the bootout command either.
Most likely: a cloud-hosted or otherwise locally-untranscribed session or terminal, in the
same general timeframe as that closeout, ran the printed one-liner as a normal stop —
without realizing (because nothing told it) that doing so left nothing watching the
observatory for the next 23 minutes.

**Whether it recurs does not depend on identifying who.** The one-liner was `install.sh`'s
own documented, printed instruction for stopping the tracker — anyone who follows it,
copies it from old scrollback, or has it in muscle memory from a prior session will produce
this exact unmarked, ambiguous-looking gap again, human or agent, regardless of `$HOME`.
That is a standing process hazard, not a one-off, and it is what item (b) exists to close:
`install.sh` no longer prints the raw command at all (see below) — only `tracker-stop`,
which cannot stop the jobs without also writing the record that makes the gap legible as
intentional. Item (a)'s `$HOME`/label-prefix guard remains a real, independently-verified
hazard in the code (confirmed by its own selftest) and is closed regardless of whether it
was *this* incident's mechanism — it just is not the confirmed cause of *this* one.

## (a) Label-namespace isolation

`install.sh` now takes `--label-prefix <prefix>` (`LABEL_PREFIX`, default
`com.marsys.pariprashna`, exported as `DEFAULT_LABEL_PREFIX`) and refuses to run at all —
before ever calling `launchctl` — if it detects `$HOME` has been overridden (compared
against the real passwd-db home via `dscl`) while `LABEL_PREFIX` is still the production
default. The refusal prints every label it *would* have booted out and explains why, in a
comment at the guard site and again at the label-assignment site in the bootstrap loop:
**"HOME isolation does not isolate launchctl labels."** Every plist template's `Label` key
was hardcoded before this change (`__LABEL__` placeholder now, substituted by `render()`);
the loop's template *source* file is still keyed by the fixed job name
(`com.marsys.pariprashna-<job>.plist.template`) regardless of `LABEL_PREFIX` — only the
rendered output's path and internal `Label` vary. Selftested by actually invoking
`install.sh` in a subprocess with `$HOME` overridden and a fake `launchctl` first on `PATH`
that records every invocation: the test asserts a non-zero exit **and** that the fake
`launchctl` was never called at all — not just that the right error text appeared.

## (b) Intentional-stop marker

`tracker-stop ["reason"]` replaces the old undocumented `launchctl bootout` one-liner: it
writes `~/.pariprashna-tracker/STOPPED_INTENTIONALLY.json` (`ts`, `reason`,
`invoking_user`) **before** booting the three jobs out — order matters, since the marker
must exist for the *entire* duration the jobs are down, not just at the moment `tracker-stop`
happens to return. `tracker-start` re-bootstraps the three jobs from the plists already on
disk (it does not redeploy code — that is `install.sh`'s job), waits up to 90s for a fresh
heartbeat, then clears the marker. The marker is cleared *after* the wait, not before
triggering the restart: clearing it first would make item (d)'s startup check see no marker
during the very restart the marker was supposed to cover. Selftested end-to-end (fake
`launchctl`, isolated `$HOME`, no real launchd touched): asserts every `bootout` call the
fake `launchctl` recorded happened while the marker file was already present on disk, and
that the marker is gone after `tracker-start` completes.

## (c) T4 — out-of-band tier, in a different subsystem

T1-T3 below all ultimately depend on the launchd GUI domain being intact — the 2026-08-19
incident removed all three jobs from that domain in one shot, so nothing left *inside* it
could have noticed. `tracker-cron-watchdog` is installed by `install.sh` into `crontab`
(**cron, not launchd** — a launchd-domain bootout cannot touch a crontab entry) on a 5-minute
`*/5 * * * *` schedule, marker-scoped by `LABEL_PREFIX` in its comment tag so a test install's
cron entry can never collide with production's. Every run: if `STOPPED_INTENTIONALLY.json` is
present, exit immediately (T4 must never fight an intentional stop). Otherwise, if
`heartbeat.json` is older than 180s, log an `out_of_band_resurrection` incident event
*immediately* (not after the re-bootstrap's own health-wait completes — that can take up to
90s, and the fact "T4 saw a dead observer and is intervening" is already true the moment
that decision is made), fire a local `osascript` notification, then call `tracker-start`.
Selftested by invoking the script directly (exactly how cron would) with a fake `launchctl`
and three heartbeat scenarios — marker present, heartbeat fresh, heartbeat stale with no
marker — asserting it is a no-op for the first two and both re-bootstraps and logs an
incident for the third. **`crontab` installation itself is deliberately NOT selftested** —
mutating the real user crontab from an automated test (which could run in production, since
`--selftest` runs at every real daemon start) is a strictly worse risk than the thing being
tested; this is the same class of honest scoping as the no-headless-browser gap below, not a
silent gap.

**Proven live (2026-08-20), not just in selftest.** T4 is the only tier that had never been
exercised against the real system, and it exists precisely because every in-band tier (T1-T3)
can be removed by a single command. Deployed this PR's code to production (`install.sh
--install-from-ref`, `git archive`, never touched the shared checkout), confirmed the cron
entry installed, then reproduced the actual incident: the raw `launchctl bootout` one-liner,
no `tracker-stop`, no marker.

- Last good heartbeat: `2026-08-19T22:06:17Z`. Bootout issued: `22:06:26Z`.
- Confirmed down: `launchctl list | grep pariprashna` empty immediately after.
- T4's `*/5` tick fired at `22:10:01Z` (the first tick after the heartbeat crossed 180s
  stale) and logged the incident event immediately:
  `{"ts":"2026-08-19T22:10:01Z","writer_id":"cron_watchdog","payload":{"event":"out_of_band_resurrection","tier":"T4"},...}`.
- New process healthy (fresh heartbeat, `cycle: 1`, `selftest_last.all_passed: true`) at
  `22:10:17Z`. **Measured restore time: 3m51s from bootout, 3m44s from T4's own detection to
  full health.**
- `BLIND_WINDOW.json` was written with the real measured gap (`gap_start_ts:
  2026-08-19T22:06:17Z`, `gap_end_ts: 2026-08-19T22:10:02Z`, `duration_s: 225.6`,
  `acknowledged: false`) and confirmed present in `state.json` (what `tracker.html`'s banner
  reads).
- Performed a second, clean, marker-covered restart (`tracker-stop` + `tracker-start`)
  immediately after, specifically to test survival: `BLIND_WINDOW.json` came out **byte-for-
  byte identical** across that restart — the record is not reset just because the daemon came
  back up green.
- Acknowledged via `tracker-ack-blind` afterward to leave production clean (this was a
  deliberate test, not a real incident).

**Closing the loop — the conductor, not another tier of the same kind.** T1-T4 keep the
*observer* alive, but every one of them is itself something that can be down.
`tracker-health-check` (item 2a) is a machine-checkable contract meant to be called by the
Paripraśna conductor swarm at every lane transition and treated as a hard halt on failure —
because the conductor, by construction, is the one thing guaranteed to be running at the
exact moment a lane transition happens; the 2026-08-19 23m37s blind window would have been
caught in seconds by it. Checks all five conditions that make the dashboard trustworthy, not
just heartbeat age: **jobs loaded** (`launchctl list`, no lock), **heartbeat fresh** (<180s),
**selftest passing** (as of its last run, carried in `heartbeat.json`), **refs fresh** (mirror
fetched successfully within 180s), **no unacknowledged blind window**. Exits 0 (safe to
proceed) only if all five hold; exits 1 with a one-line diagnosis naming which failed
otherwise. Deliberately does **not** source `_tracker_lock.sh` — a conductor calling this at
every lane transition must never be made to wait behind `install.sh`/`tracker-stop`/
`tracker-start` holding the label lock, since this script never moves a label, only reads
state. Measured under 0.7s against production. Selftested: all five failure conditions
triggered independently (one at a time) plus the all-healthy case, asserting the lock
directory is never created and total runtime stays under 1s; observed failing first by
disabling the jobs-unloaded check specifically and confirming that scenario silently reported
healthy. The binding rule that makes this call mandatory, not optional, is in
`PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` (item 2b) — wiring the actual call into the
conductor's own kickoff loop is outside this PR's `tracker/**` scope; that amendment is the
contract the conductor's prompts adopt at its next phase boundary.

## (d) Remembered blindness

A restart must never launder an outage into green. On every real daemon start (not
`--selftest`, not `--once`; a dedicated fast path, `--check-blind-window-only`, exists so
this is testable without the heavy collect/project machinery), `trackerd.py` compares the
previous `heartbeat.json`'s `ts` against now. If the gap exceeds 120s (`compute_blind_window`
in `_common.py`, pure) **and** no `STOPPED_INTENTIONALLY.json` is present, it writes
`~/.pariprashna-tracker/BLIND_WINDOW.json` (`gap_start_ts`, `gap_end_ts`, `duration_s`,
`acknowledged: false`) and fires a real `anomaly` event — both persist across further
restarts. `tracker.html` renders a **separate, distinctly-styled persistent banner**
(magenta, not the amber/red of the live staleness banner above — a different axis: "was
there a gap nobody explained," not "is the data I'm looking at right now fresh") reading
e.g. `BLIND 00:23:37 (2026-08-19T20:35:52Z → 2026-08-19T20:59:29Z)`, and it does **not**
clear itself when the daemon comes back up green. Only `tracker-ack-blind`, an explicit
operator action, retires it (sets `acknowledged: true`, keeps the record). Selftested two
ways: the pure `compute_blind_window` function's four cases (first-ever boot, under
threshold, over-threshold-but-marked-intentional, the one that fires), and a real subprocess
run of `trackerd.py --check-blind-window-only` against a fabricated 300s-stale heartbeat in
an isolated `$HOME` — asserting the persistent file and the anomaly event both actually land
on disk, and that the same stale heartbeat with a marker present produces neither.

## Mutual exclusion between install.sh / tracker-stop / tracker-start / T4

Four scripts are now capable of moving the `com.marsys.pariprashna-*` launchd labels:
`install.sh`, `tracker-stop`, `tracker-start`, and `tracker-cron-watchdog`. Without mutual
exclusion, two running concurrently (a human re-running `install.sh` while T4's cron tick
fires, say) can interleave `bootout`/`bootstrap` calls against the same labels in an
undefined order. `_tracker_lock.sh`, sourced by all four, is a single advisory lock —
atomic `mkdir` under `~/.pariprashna-tracker/label_ops.lock` (portable, no `flock(1)`
dependency, which is not reliably present on macOS) — held only around each script's own
actual `launchctl` calls, never around unrelated work (`tracker-start`'s up-to-90s health-
wait, for instance, runs unlocked).

- **`install.sh`, `tracker-stop`, `tracker-start`** acquire *blocking* (retry up to 30s,
  then fail loudly rather than proceed unlocked).
- **`tracker-cron-watchdog`** acquires *non-blocking, a single attempt, no retry* — per its
  own standing contract: if the lock is held, something legitimate is already working on
  these labels, so it logs a `deferred_lock_held` event and exits, rather than fighting it.
  Cron's next tick (5 minutes later) re-evaluates from scratch. It only *peeks* the lock
  (acquire-then-immediately-release) to detect in-progress work; the actual protected
  mutation happens inside `tracker-start`, which it calls afterward and which takes its own
  proper hold — this avoids a same-process reentrancy deadlock that a naive
  "hold-through-the-whole-call" design would hit.
- **`install.sh` also writes `STOPPED_INTENTIONALLY.json` itself**, around its own bootout
  window, and clears it after — but only if *it* created it. If the marker already existed
  (an operator deliberately stopped the tracker via `tracker-stop` and is now separately
  redeploying code while still meaning to stay stopped), `install.sh` leaves it in place
  rather than accidentally resuming an intentional stop. This means T4 stands down for a
  legitimate reinstall via the *marker* (semantic intent) as well as the *lock* (mutual
  exclusion against a narrow timing race) — belt and suspenders, not redundant: the lock
  protects against T4's heartbeat check firing in the split second before the marker lands;
  the marker protects the whole visible duration of the reinstall.

Selftested by holding the real lock (the same file all four scripts source) in a background
process — including one real `launchctl bootstrap` call inside the held window, standing in
for `install.sh`'s own — while a concurrent `tracker-cron-watchdog` run is driven against a
stale-heartbeat-no-marker scenario: asserts exactly one `bootstrap` call total (the holder's)
and a real `deferred_lock_held` event from cron, never both intervening. Observed failing
first by neutering cron's lock-peek check (produced 4 bootstrap calls — the holder's plus
cron's own full 3-job re-bootstrap — and no deferral), then restored.

## Where lane and phase state actually comes from

**The board is derived from what the swarm emits, never from anything hand-typed here.**
That was not true until 2026-08-20, and the failure it caused is the reason this section
exists: `PLAN.yaml` carried `"status": "PLANNED"` string literals, 46 of 53 lanes had no
evidence source at all, and lane ids (`P1-A`) were matched against branches the swarm
names by gate (`pariprashna/g1-a-safety-gate`). The result was a board that sat frozen
through two entire shipped phases — P1 (10 lanes) and P2 (15 lanes) — while `generated_at`
ticked every 36 seconds and every liveness light stayed green.

Sources, in precedence order:

1. **Merged PRs (DERIVED — the primary source).** A merge is a fact. `collect.extract_lane_identifiers`
   reads each merged PR's **title** plus the identifiers its body marks in **bold**, which
   is the swarm's own consistent convention: a body bolds the lanes it implements and
   mentions others in plain prose. Validated against every real phase PR (#1349/#1356/
   #1360/#1363/#1364/#1365), reproducing the published lane totals exactly (P1 = 10,
   P2 = 15). Scanning plain body prose instead is *actively wrong*, not just noisy —
   #1363 says "gating for G3-B/C/D/E/F/G" about lanes it does not implement.
   A lane is MERGED only if the PR's merge commit is an ancestor of the **mirror's** main:
   never claim a merge off a commit this tracker cannot see.
2. **The conductor's own `state/SWARM_TRACKER.json` (CLAIMED).** The conductor never
   adopted this observatory's `tracker_emit.py` hook (DD-11 is "IN FORCE — NOT YET WIRED"),
   but it does keep that file current on main. It is the subject describing itself, so it
   is rendered CLAIMED, never counted as evidence, and always loses to (1).
3. **`UNOBSERVABLE` (the honesty floor).** No merged PR, no branch, no artifact, no
   conductor entry ⇒ `UNOBSERVABLE`/`UNKNOWN`. Never `PLANNED` — `PLANNED` is a claim this
   tracker has no basis for, and asserting it as `DERIVED` is exactly the §N.8 defect the
   instrument exists to catch.

**Phase status is computed** from those lane states plus the conductor's gate results
(`fold_phase_status`), and carries its own `status_provenance` string. `PLAN.yaml` no
longer contains a phase `status` field at all.

**Lane↔gate mapping.** Lanes carry a `gate` field (`P2-I` → `G3-A`) because the swarm
works in gate ids. Only unambiguous 1:1 mappings are assigned; where one gate covers
several lanes (G5 → P3-E/F, G7 → P4-A..D) no gate is set, since an ambiguous mapping would
attribute one PR to lanes it never touched.

## The fourth liveness axis: board vs. world

Observer freshness, ref freshness and subject progress all answer *"is the observer
working?"*. None answers *"does the board match what the world did?"* — which is why the
frozen board survived three separate rounds of being certified healthy.

`board_world_divergence` closes that: every cycle it checks whether any merged PR
implementing a lane this plan recognises has landed on main without that lane showing as
done. If so it raises an `anomaly` and the header pill turns red — **BOARD BEHIND WORLD**.
Its selftest asserts it fires on a frozen board and stays silent on a correct one, and it
was observed failing as a no-op (its literal state before this change) against the real
frozen-board scenario.

## The four-tier tap (dead-man's switch)

1. **T1** — `trackerd.py` stamps `~/.pariprashna-tracker/heartbeat.json` every cycle
   (20s while lanes are changing, backs off to 60s after 10 idle cycles).
2. **T2** — `com.marsys.pariprashna-watchdog` (launchd `StartInterval=60`) kills any stale
   pid and restarts `trackerd.py` if the heartbeat is >90s old, and emits a `daemon` /
   `resurrection` event with the observed gap — displayed on the dashboard, never swallowed.
   **Cannot survive its own launchd domain being removed** — see the 2026-08-19 incident
   above; that gap is what T4 exists to cover.
3. **T3** — `tracker.html` computes staleness **client-side** from `TRACKER_DATA.generated_at`
   against the browser's own clock on a 5s timer, independent of whether the fetch of a
   fresh `tracker_data.js` succeeds. A completely dead backend still produces a loud, exact,
   red banner — the page's freshness claim never depends on the thing that might be gone.
4. **T4** — `tracker-cron-watchdog`, installed into `crontab` (not launchd) by `install.sh`,
   every 5 minutes. See "(c) T4" above for the full mechanism, including why it lives in a
   different subsystem on purpose.

## LAN access (phone)

`serve.py` binds `0.0.0.0:8934` and serves `~/.pariprashna-tracker/` under a random path
token generated at first run and persisted to `~/.pariprashna-tracker/serve_token`
(printed to `logs/serve.out.log` at every start). **This is unauthenticated plaintext on
the local network. Do not port-forward or tunnel it.**

## What's derived vs. claimed

- **DERIVED** (counts toward any completion figure): git branch/worktree state (mirror for
  `origin/*` refs, shared checkout for `worktree list`), GitHub PR state via `gh api`,
  filesystem artifact existence, Cloud Run revisions/traffic via `gcloud`, migration
  numbering. Any signal that fails to collect is `UNKNOWN` with the failure text as
  provenance — it never carries the previous cycle's value forward. A mirror-fetch failure
  degrades every mirror-derived cell this same way, for the same reason.
- **CLAIMED** (rendered distinctly, never counted): agent self-reports of lane state for
  states that leave no artifact (e.g. `BUILDING` before a branch exists). A claim that
  contradicts derived evidence (e.g. `MERGED` claimed for a branch that is not an ancestor
  of the mirror's `main`) produces an `anomaly` event and never moves a completion count —
  same for a `gh`-vs-mirror merge-commit divergence (see "Ref freshness" above).

## Operational hazards (for whoever runs this by hand)

- **Scratch cleanup deletes by exact filename only — never `rm -rf` a directory that
  contains tracked files.** During the 2026-08-20 PARIPRASHNA-CLOSEOUT session, cleaning up
  two local adhoc `drift_detector.py` scratch-output files with
  `rm -rf 00_ARCHITECTURE/drift_reports/` deleted the entire tracked directory — 166
  committed historical files, not just the 2 scratch ones — because that directory holds
  both. Caught via `git status` before anything was committed, restored with
  `git checkout -- 00_ARCHITECTURE/drift_reports/`, verified restored, then the two actual
  scratch files were removed by exact name (`rm <file1> <file2>`). No harm done, but it cost
  a full stop-and-restore cycle that a one-line habit would have avoided. Recording it here
  so the next session doesn't rediscover it the same way: when a script writes scratch
  output into a directory that also holds tracked files (this repo has several such
  directories — check `git status` on the directory *before* deleting anything in it, every
  time), delete by exact filename, never by directory.

## Known, honestly-scoped gaps (not silently dropped — logged here, §N.6)

- **T4's `crontab` installation step is not selftested** (see "(c) T4" above) — mutating the
  real user crontab from a suite that runs at every real daemon start is a worse risk than
  the thing being tested. `tracker-cron-watchdog`'s own conditional logic (skip on marker,
  skip on fresh heartbeat, intervene + log on stale-with-no-marker) is selftested by
  invoking the script directly with a fake `launchctl` and isolated `$HOME`; only the
  `crontab -l | ... | crontab -` line in `install.sh` is unverified by automation.
- **Lane-to-artifact mapping for P1–P5 is best-effort.** Those 47 lanes have not been
  built yet; their `expected_artifacts.paths` in `PLAN.yaml` are plausible guesses from the
  phased-swarm plan's prose, not confirmed file paths. Each lane's own brief should refine
  its `PLAN.yaml` entry when it opens (`PLAN.yaml` edits are commits — the plan has history).
- **`--selftest`'s client-side banner check tests the pure function directly**
  (`stalenessClass`/`staleness_class`, kept byte-identical between `tracker.html`'s JS and
  `_common.py`) but does **not** drive a real headless browser — no browser automation
  tooling is available to this stdlib-only, no-new-dependencies tracker. The DOM rendering
  path (`updateStaleBanner`) is exercised only by manual/visual check, not by `--selftest`.
- **`gh pr list --state open` only** for the main lane-state derivation (as specified, for
  API-budget reasons) — a lane whose PR already merged is detected via git ahead/behind
  against the mirror's `main`, not via GitHub PR history; this is an approximation (a
  squash-merge can leave a branch's own commits "ahead" even though its content merged)
  and can occasionally under-detect a just-merged lane for one cycle until the branch ref
  itself is deleted or its ahead/behind resolves. (The *separate* `gh pr list --state
  merged --limit 20` consistency check exists specifically to catch the more serious
  version of this same class of gap — see "Ref freshness" above — but is bounded to the 20
  most recent merges for API budget, same reasoning.) Not silently perfect — flagged here.
- **Budget spend tracking is CLAIMED-only.** No API meters real dollars spent; the budget
  bars fold `kind:"budget"` events, which are necessarily self-reported by whatever spawns
  the swarm's agents. This is the one figure on the dashboard that structurally cannot be
  DERIVED without a billing API this tracker doesn't have access to — shown honestly as
  such (not styled as a DERIVED figure).
- **`github_rate_limit` reads the `graphql` bucket, not `core` — fixed 2026-08-20.** This
  collector's own poll (`gh pr list`, open and merged, every cycle) is GraphQL-backed, not
  REST. Verified empirically before fixing: `gh api rate_limit` diffed immediately before
  and after a live `gh pr list` call showed `resources.core.used` unchanged at 0 while
  `resources.graphql.used` incremented by 2 in that one call. The prior version read
  `resources.core`, which this tracker's own polling never spends from — it reported
  5000/5000 every cycle regardless of load, a decorative meter dressed as a budget one. The
  PR-poll itself was confirmed executing every cycle (unconditionally for open PRs; for
  merged PRs whenever the mirror is healthy) — the defect was the bucket read, not a
  skipped poll. `parse_rate_limit()` is a pure function with a fixture-based selftest
  (`test_rate_limit_reads_graphql_not_core`) so a regression back to `core` fails loudly.
