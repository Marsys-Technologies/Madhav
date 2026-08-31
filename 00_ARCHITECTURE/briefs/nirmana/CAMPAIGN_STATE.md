---
artifact: CAMPAIGN_STATE.md
canonical_id: NIRMANA_CAMPAIGN_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
last_updated: 2026-09-01
---

# Nirmāṇa Velocity-Reset — Campaign State

Authoritative live state for the campaign defined in
`NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`. Read this file first on every session
start/resume; trust it; continue from the recorded position. Once the P3 ops plane
(`nirmana_ops`) exists, the DB is authoritative for asset/queue state and this file carries
narrative + pointers only.

## Current phase: P1 in flight, P2 in flight, P0 substantially complete

| Phase | Status | Notes |
|---|---|---|
| P0 Bootstrap | ✅ substantially done | Worktrees `codex/nirmana-velocity-reset` (revert) + `docs/nirmana-velocity-reset-governance` (P2) created from fresh `origin/main` (`1ba236dec`). Grounding facts re-verified live (see decisions log D-VR-1..4). This file created. |
| P1 Restore deployability | 🟡 in flight | PR #1674 (revert of #1673) open, auto-merge armed. Awaiting CI + merge queue + deploy verification. |
| P2 Land governance | 🟡 in flight | PR #1675 open (prompt + v6.1 amendment + CURRENT_STATE pointer + this file), auto-merge armed. |
| P3 Minimal substrate | ⬜ not started | Blocked on P1/P2 merging first (keep diffs disjoint / avoid queue thrash). |
| P4 Rehearsals | ⬜ not started | |
| P5 Hygiene | ⬜ not started | |
| P6 L0 execution | ⬜ not started | 40 L0 assets per frozen definition `t0-2026-08-26-faa4d6b0`, but monitor last reported `plan_adaptation_required` with 6 drifted assets — must reconcile at P4-A₀ before trusting wave membership. |
| P7 L1-L5 | ⬜ not started | |

## Grounding facts re-verified live (2026-09-01, this session)

- `origin/main` = `1ba236dec7a7ba5b28106abab6554099ed989e50` — confirmed via `git ls-remote`.
- PR #1673 merged 2026-08-30T07:47:17Z, merge commit = current main tip — confirmed via `gh pr view`.
- Deploy to Cloud Run failed for `1ba236dec` (run 33300457679, 2026-08-30T07:58) —
  `error: permission denied for schema nirmana_evidence` (42501) — confirmed via `gh run view --log-failed`.
  Last successful deploy was for `0863734904c28a6bce247547090018cf94c39f96`, matching the
  document's stated production commit `0863734`.
- Migration `639_nirmana_nonbrowser_conductor.sql` is NOT in `_migrations_applied` (last applied:
  `636_nirmana_campaign_control_monitor_read.sql`, 2026-08-29) — confirmed via live DB query.
- No migration or code on `main` after `639` references the reverted tables/files — confirmed via
  `git ls-tree` + grep before reverting. Revert is clean.
- `NIRMANA_HOLD` kill-switch file absent — confirmed.

## Open items / next actions

1. Watch PR #1674 (revert) through CI → merge queue → merge → deploy. On green: verify new Cloud
   Run revision Ready at 100%, `commit-sha` label matches new main, `639` still absent from
   `_migrations_applied`, `production_in_sync` true.
2. Watch PR #1675 (governance) through CI → merge queue → merge.
3. Begin P3 (ops plane + capsule path + verifier + supersession path) only after P1/P2 are merged.
4. At P4-A₀, reconcile the 6 drifted assets in the stale `t0-2026-08-26-faa4d6b0` definition before
   trusting L0 wave membership.
5. Note for later hygiene (P5): this repo currently has ~90 stale/prunable git worktrees under
   `/private/tmp/`, `~/.codex/worktrees/`, and `.clone/worktrees/` from prior campaigns
   (nirmana-*, pariprashna-*). Not touched this session — P5/L0-close scope, not P0.

## Decisions log

- `D-VR-1` (2026-09-01): Re-verified all §1 grounding facts live rather than trusting the
  document's snapshot, per P0's "minutes, not an audit" instruction. All confirmed accurate
  (main SHA, PR #1673 merge, deploy failure cause, migration 639 unapplied). Basis: `gh`, live DB
  query, `git ls-remote`.
- `D-VR-2` (2026-09-01): Created two separate worktrees/branches for P1 (code revert) and P2
  (governance docs) rather than one combined PR, to keep the revert mergeable independently of
  any governance-doc review friction and avoid merge-queue thrash from unrelated file sets.
  Basis: §5 P1/P2 are described as separate PRs in the source document.
- `D-VR-3` (2026-09-01): Used `git revert -m 1` of the merge commit directly rather than hand-
  reconstructing the pre-#1673 tree, since pre-check confirmed no downstream migration/code
  references the reverted files. Basis: §5 P1 pre-check requirement, satisfied.
- `D-VR-4` (2026-09-01): `gh pr merge --auto` reported "merge strategy set by the merge queue" but
  `gh pr view --json autoMergeRequest` confirms auto-merge is armed (method MERGE) — treating this
  as successful queue arming, not a failure, since GitHub's auto-merge will submit to the queue
  once required checks pass. Basis: live API state, not just CLI stdout.

## Finding-fence backlog

(none yet — no findings surfaced during P0/P1/P2 investigation beyond the already-diagnosed
migration-639 grant gap, which is the P1 fix itself, not a backlog item)

## Tripwire readings (2026-09-01, end of this session's work so far)

- Governance share of effort: this session's work so far is P0 (bootstrap/verification) + P2
  (governance docs) + P1 (the one real fix), all required by the phase plan itself — not
  additional machinery. Not yet at a >15% steady-state to evaluate; will self-measure at each
  future microbatch boundary per §7.5.
- Substrate PR count: 0 of the P3 substrate PRs opened yet (correctly — P3 hasn't started).
- Days since last new capsule: N/A — no capsule mechanism exists yet (P3 not started); zero
  capsules is expected at this point, not a stall.
