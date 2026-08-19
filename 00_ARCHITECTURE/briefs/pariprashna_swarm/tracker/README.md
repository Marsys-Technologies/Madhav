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
running code's short sha. If that sha is not the latest commit that touched this `tracker/`
subtree on `origin/main`, the pill turns amber and reads **"STALE CODE"** — an observatory
that can't tell you it's running old code isn't trustworthy. In-place/dev runs (no
`INSTALLED_FROM.json`) show `code UNKNOWN` honestly rather than a fake green.

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
