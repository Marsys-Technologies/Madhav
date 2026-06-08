---
artifact: PR224_RECOVERY_v1_0
canonical_id: PR224_RECOVERY
version: 1.0
status: COMPLETE
authored_by: Claude Code (recovery session) 2026-06-08
native: Abhisek Mohanty
---

# PR #224 Recovery — Cockpit Polish Round Content Restored (2026-06-08)

## Discovery

After PR #224 was reported merged and the session notes written, the native observed:
- No refresh button anywhere in the cockpit
- Delete button still crashing with "Unexpected end of JSON input" on error paths

Investigation via `git merge-base --is-ancestor 5bf80da6 origin/main` → NOT-ANCESTOR.
Commit 5bf80da6 (`fix+feat(cockpit): polish round — 11 issues bundled`) was on
`origin/fix/cockpit-polish-round` but never landed on main.

**GitHub API confirmed: PR #224 state = OPEN, mergeCommit = null.** The PR was never merged.

## Root Cause (§9 investigation)

The Ganga Quality Gate Workflow completed successfully (all CI checks green), which was
misinterpreted as "PR merged" in session notes. The actual GitHub merge action was never
triggered. This is the SECOND occurrence today:
- PR #221 (feature/l0-phase-alpha) → recovered via PR #225
- PR #224 (fix/cockpit-polish-round) → recovered via this PR

Full root-cause analysis: `/tmp/merge_loss_root_cause_hypothesis.md`
(key finding: NOT a GitHub bug — session notes confirmed Ganga gate success, not git ancestry)

## Conflict Landscape (vs PR #225 which landed in between)

Only one file had real git conflicts:

| File | Conflict | Resolution |
|---|---|---|
| `asset_registry_seed.ts` | count_sql: HEAD=15-table sum, #224=5-table sum | KEEP HEAD (15-table, already correct from PR #225) |
| `migrations/176_bg_reference_count_sql_fix.sql` | Number collision with PR #225's migration | RENAMED to `180_bg_reference_count_sql_fix.sql` |

All other 12 files cherry-picked cleanly (auto-resolved by git).

## Recovery Actions

1. Cherry-picked `5bf80da6` onto `fix/pr224-recovery` from `d365bea9` (main HEAD)
2. Resolved conflict: kept 15-table count_sql (HEAD is already the correct version)
3. Renamed migration 176→180 (176 already used by Phase α recovery)
4. Updated migration content to use full 15-table sum (consistent with seed)
5. Fixed TypeScript implicit-any in `cockpit/refresh/route.ts` lines 32+38
6. Verified prod count_sql already = 15-table sum → no prod migration apply needed

## What This PR Restores

- **§1 CRITICAL**: `clear/execute` route transaction-wrapped + defensive JSON parse
- **§2 CRITICAL**: bg_reference count_sql migration (renamed to 180; prod already correct)
- **§3 UX**: Layer-grouped global modal summary in ClearConfirmModal
- **§4 PERF**: SSR chart metadata prefetch → no "Loading chart…" delay
- **§5 UX**: NEW `RefreshIconButton` component + `/api/cockpit/refresh` endpoint,
  wired at global / layer / asset scopes with super_admin gating
- **§7 UX**: 14-char chart ID + click-to-copy in CockpitHeader

## Verification

- RefreshIconButton wired in: CockpitHeader.tsx, LayerPanel.tsx, AssetRow.tsx ✓
- /api/cockpit/refresh route present ✓
- Migration renamed to 180 ✓
- tsc: no new errors in changed files (pre-existing missing-node_modules baseline) ✓
- Phase α 12 L0 assets preserved in seed + asset_names ✓
- Prod count_sql: full 15-table sum already present → no migration apply needed ✓

## Architectural Lesson Reinforced

Every session claiming a PR merged MUST verify git ancestry before writing session notes:
```bash
git fetch origin
git merge-base --is-ancestor <pr-head-commit> origin/main || echo "ERROR: NOT MERGED"
```

This check is zero-cost and catches this failure mode immediately. See root-cause
hypothesis for full Option A/B/C mitigation analysis.

Source brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PR224_RECOVERY_AND_ROOT_CAUSE_v1_0.md`
