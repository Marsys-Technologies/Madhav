# Paripraśna Execution Observatory (tracker-v2)

Derived-not-narrated live tracker for the Paripraśna swarm build (CLAUDE.md §N.8, earned
signal, applied to the instrument rather than the product). Supersedes the P0-D tracker
(`00_ARCHITECTURE/briefs/pariprashna_swarm/state/{SWARM_TRACKER.json,tracker.html,...}`)
going forward — see the note appended to `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md`.

## Layout

- **Code** (this directory, in the repo, versioned): `PLAN.yaml` (declarative plan — JSON,
  which is valid YAML, so this stays stdlib-only), `_common.py`, `tracker_emit.py`,
  `collect.py`, `project.py`, `trackerd.py`, `watchdog.py`, `serve.py`, `tracker.html`,
  `selftest.py`, `launchd/*.template`, `install.sh`.
- **Runtime state** (outside the repo, never appears in `git status`): `~/.pariprashna-tracker/`
  — `events/<writer_id>.jsonl` (append-only), `state.json`, `tracker_data.js`,
  `heartbeat.json`, `collector_snapshot.json`, `trackerd.pid`, `serve_token`, `logs/`.

Python 3 standard library only. No pip installs, no npm, nothing that can perturb the
build environment. The tracker only ever *reads* git (`--no-optional-locks`, `for-each-ref`
/ `rev-list` / `worktree list` only) — it never touches an index, never checks anything
out, never enters another worktree.

## Running it

```sh
# one-shot cycle (for testing):
python3 trackerd.py --once

# falsifiable self-test suite (freezes, breaks, verifies red, unfreezes):
python3 trackerd.py --selftest

# install as three launchd jobs (KeepAlive daemon + watchdog + LAN server):
./install.sh
```

## The three-tier tap (dead-man's switch)

1. **T1** — `trackerd.py` stamps `~/.pariprashna-tracker/heartbeat.json` every cycle
   (20s while lanes are changing, backs off to 60s after 10 idle cycles).
2. **T2** — `com.marsys.pariprashna-watchdog` (launchd `StartInterval=60`) kills any stale
   pid and restarts `trackerd.py` if the heartbeat is >90s old, and emits a `daemon` /
   `resurrection` event with the observed gap — displayed on the dashboard, never swallowed.
3. **T3** — `tracker.html` computes staleness **client-side** from `TRACKER_DATA.generated_at`
   against the browser's own clock on a 5s timer, independent of whether the fetch of a
   fresh `tracker_data.js` succeeds. A completely dead backend still produces a loud, exact,
   red banner — the page's freshness claim never depends on the thing that might be gone.

## LAN access (phone)

`serve.py` binds `0.0.0.0:8934` and serves `~/.pariprashna-tracker/` under a random path
token generated at first run and persisted to `~/.pariprashna-tracker/serve_token`
(printed to `logs/serve.out.log` at every start). **This is unauthenticated plaintext on
the local network. Do not port-forward or tunnel it.**

## What's derived vs. claimed

- **DERIVED** (counts toward any completion figure): git branch/worktree state, GitHub PR
  state via `gh api`, filesystem artifact existence, Cloud Run revisions/traffic via
  `gcloud`, migration numbering. Any signal that fails to collect is `UNKNOWN` with the
  failure text as provenance — it never carries the previous cycle's value forward.
- **CLAIMED** (rendered distinctly, never counted): agent self-reports of lane state for
  states that leave no artifact (e.g. `BUILDING` before a branch exists). A claim that
  contradicts derived evidence (e.g. `MERGED` claimed for a branch that is not an ancestor
  of `origin/main`) produces an `anomaly` event and never moves a completion count.

## Known, honestly-scoped gaps (not silently dropped — logged here, §N.6)

- **Lane-to-artifact mapping for P1–P5 is best-effort.** Those 47 lanes have not been
  built yet; their `expected_artifacts.paths` in `PLAN.yaml` are plausible guesses from the
  phased-swarm plan's prose, not confirmed file paths. Each lane's own brief should refine
  its `PLAN.yaml` entry when it opens (`PLAN.yaml` edits are commits — the plan has history).
- **`--selftest`'s client-side banner check tests the pure function directly**
  (`stalenessClass`/`staleness_class`, kept byte-identical between `tracker.html`'s JS and
  `_common.py`) but does **not** drive a real headless browser — no browser automation
  tooling is available to this stdlib-only, no-new-dependencies tracker. The DOM rendering
  path (`updateStaleBanner`) is exercised only by manual/visual check, not by `--selftest`.
- **`gh pr list --state open` only** (as specified, for API-budget reasons) — a lane whose
  PR already merged is detected via git ahead/behind against `origin/main`, not via GitHub
  PR history; this is an approximation (a squash-merge can leave a branch's own commits
  "ahead" of `origin/main` even though its content merged) and can occasionally
  under-detect a just-merged lane for one cycle until the branch ref itself is deleted or
  its ahead/behind resolves. Not silently perfect — flagged here.
- **Budget spend tracking is CLAIMED-only.** No API meters real dollars spent; the budget
  bars fold `kind:"budget"` events, which are necessarily self-reported by whatever spawns
  the swarm's agents. This is the one figure on the dashboard that structurally cannot be
  DERIVED without a billing API this tracker doesn't have access to — shown honestly as
  such (not styled as a DERIVED figure).
