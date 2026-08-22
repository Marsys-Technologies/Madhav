# Shared stash-stack archive — 2026-08-23

`git stash` is a single stack shared across every worktree of this repo, not per-worktree. As of
2026-08-23 it held 7 entries belonging to other campaigns/sessions (coord-d3s30, parishkara/mr-41-42,
siddhanta ×2, pratijna-satya, shabda-shuddhi ×2) — none belonging to the session that archived them.

Each entry's full diff is preserved here (`stash_N.diff`, `N` = the stash index at time of archiving)
before the stack was cleaned up, so the drop below loses nothing.

## Disposition

| Index | Branch | Content | Landed on `origin/main`? | Action |
|---|---|---|---|---|
| 0 | `coord-d3s30-1786732397` | `CAMPAIGN_COORDINATION.md` — session-31 sanity-pass note | **No** | archived, dropped |
| 1 | `parishkara/mr-41-42-suppression` | `kala_views/{ahead,now,story}.ts` — real code changes | not checked | **archived, NOT dropped** — see below |
| 2 | `pratijna-v4/lane-b1-chart-reader` (holds a `siddhanta` stash) | `SIDDHANTA_STATE.md` | not checked | archived, dropped |
| 3 | `siddhanta/lane-p1-pratijna-v3` | `SIDDHANTA_STATE.md` | not checked | archived, dropped |
| 4 | `pratijna-satya/integration` | `PRATIJNA_SATYA_STATE.md` — Phase A unblock note | **No** | archived, dropped |
| 5 | `shabda-shuddhi/integration` | `test_domain_vocabulary_census.py`, `bo_pratijna.py` | not checked | archived, dropped |
| 6 | `shabda-shuddhi/lane-l8-detectors` | `stage2_promise.py`, `ph_nimitta/engine.py` | not checked | archived, dropped |

**Index 1 was deliberately left in the stash stack, not dropped.** Its own stash message already
carries an explicit instruction — *"RESTORED: unrelated G14b AHEAD auto-file changes accidentally
popped by another worktree's shared stash list (pk-mr4142 MR-41/42 session, do not drop)"* — left
there by whichever session put it back after an earlier accidental pop. It may still be in active
use as a literal stash slot by that session's workflow, not merely a historical record, so it is
archived here for safety but the live stash entry itself is untouched.

The other six were not individually verified as landed-elsewhere before dropping — two are
confirmed *not* landed (0, 4). Dropping them from the stack does not delete the work; it is fully
recoverable from the diffs in this directory, or by re-applying with `git apply stash_N.diff`
(strip the header lines above the `diff --git` block first).
