---
artifact: CAMPAIGN_STATE.md
canonical_id: NIRMANA_CAMPAIGN_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
last_updated: 2026-09-01T-post-P1-P2-verification
---

# Nirmāṇa Velocity-Reset — Campaign State

Authoritative live state for the campaign defined in
`NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`. Read this file first on every session
start/resume; trust it; continue from the recorded position. Once the P3 ops plane
(`nirmana_ops`) exists, the DB is authoritative for asset/queue state and this file carries
narrative + pointers only.

## Current phase: P0/P1/P2 complete and verified; P3 next

| Phase | Status | Notes |
|---|---|---|
| P0 Bootstrap | ✅ done | Worktrees created from fresh `origin/main` (`1ba236dec`). Grounding facts re-verified live (D-VR-1..4). State file created. |
| P1 Restore deployability | ✅ done, verified | PR #1674 merged via queue (squash `621efd792`). Deploy to Cloud Run run succeeded (conclusion=success). Cloud Run `amjis-web` latest ready revision `amjis-web-01809-zn5` at 100% traffic, `commit-sha` label = `621efd7928a07f886399f86f81c5bb1d96a58443` — matches. `639` confirmed still absent from `_migrations_applied` post-deploy (query returned 0 rows). `nirmana_evidence` schema/grants untouched (revert only removed app code + the never-applied migration file). |
| P2 Land governance | ✅ done | PR #1675 merged via queue (squash `5fc008d4c`), docs-only (4 files, no code/schema). Current `origin/main` tip. |
| P3 Minimal substrate | 🟡 starting | Prep done: confirmed `nirmana_evidence` schema owned by `nirmana_evidence_owner`; reverted 639's design used per-action service-account principals (`amjis-nirmana-conductor@…`, `amjis-nirmana-verifier@…`) with a lease/fence pattern — reusable per §5 P3 ("lift the lease/fence design from 639, drop its policy/readiness tables"). Target ≤2 PRs, tripwire at 4. |
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

1. Begin P3: design `nirmana_ops` schema (queue/state/lease/fence/cost, enum-checked), the
   `asset_terminal_accepted`/`layer_frozen` capsule vocabulary addition to the evidence ingress
   with zod validation, a non-browser authenticated submission path, and the definition
   supersession path. Target ≤2 PRs (tripwire at 4 per §7.5/§5 P3).
2. Then P4: rehearsals A₀ (supersede stale definition, reconcile 6 drifted assets), A (probe
   rehearsal on `bg_ephemeris_engine`/`bg_panchanga`), B (build rehearsal on
   `bg_formula_constants`, full route incl. one induced rejection + kill-switch drill).
3. At P4-A₀, reconcile the 6 drifted assets in the stale `t0-2026-08-26-faa4d6b0` definition before
   trusting L0 wave membership.
4. Note for later hygiene (P5): this repo currently has ~90 stale/prunable git worktrees under
   `/private/tmp/`, `~/.codex/worktrees/`, and `.clone/worktrees/` from prior campaigns
   (nirmana-*, pariprashna-*). Not touched this session — P5/L0-close scope, not P0.
5. Housekeeping: this session's own worktrees (`codex/nirmana-velocity-reset`,
   `docs/nirmana-velocity-reset-governance`, `docs/nirmana-state-p1-p2-verified`) can be removed
   once their PRs are merged — routine, not deferred to P5.

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
- `D-VR-5` (2026-09-01): Merge queue took ~4.5 min for #1674 and ~16.5 min for #1675 (queue
  re-runs the 5 required checks against a synthetic merge ref, min 5 min batch wait per repo
  ruleset). Treated as normal queue latency, not a stall — verified via GraphQL
  `isInMergeQueue`/`mergeQueue.entries` rather than assuming a problem from `gh pr checks`
  showing pending. Basis: repo ruleset `min_entries_to_merge_wait_minutes: 5`.
- `D-VR-6` (2026-09-01): Left the `_migrations_applied` vs. repo-file discrepancy (632/633/636
  recorded as applied but no longer present as files on `main`) as `DEFER_TO_LAYER_BACKLOG` — it
  predates this campaign, does not affect the #1674 revert (639 was never applied), and
  investigating it further is not required for P1 closure. Basis: §4 item 7 finding fence.

## Finding-fence backlog

- `_migrations_applied` records `632_nirmana_evidence_server_writer_guard.sql`,
  `633_nirmana_evidence_writer_ownership.sql`, and `636_nirmana_campaign_control_monitor_read.sql`
  as applied, but these files do not exist in the repo at `origin/main` (only 630, 631, 634, 635,
  637, 638 remain from that range, plus 639 which was just reverted). Disposition:
  `DEFER_TO_LAYER_BACKLOG` — pre-existing, does not block P1, affects replay-from-scratch fidelity
  not live production. Needs an owner before any full-DB rebuild/replay is trusted.

## Tripwire readings (2026-09-01, end of P0/P1/P2)

- Governance share of effort: P0 (bootstrap/verification) + P1 (one real production fix, merged
  and deployed) + P2 (required governance landing) — all phase-plan-mandated, no discretionary
  machinery added. Under the 15% threshold; will re-measure at each future microbatch boundary.
- Substrate PR count: 0 of the P3 substrate PRs opened yet (correctly — P3 starts next).
- Days since last new capsule: N/A — capsule mechanism doesn't exist until P3 ships it; zero
  capsules is expected at this point, not a stall.
