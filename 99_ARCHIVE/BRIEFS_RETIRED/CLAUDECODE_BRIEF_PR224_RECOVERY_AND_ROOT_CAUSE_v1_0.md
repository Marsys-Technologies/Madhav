---
artifact: CLAUDECODE_BRIEF_PR224_RECOVERY_AND_ROOT_CAUSE_v1_0
canonical_id: PR224_RECOVERY_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: Recovery — PR #224 cockpit polish round silently lost merge + root-cause investigation
branch: fix/pr224-recovery
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavPR224Recover (pre-create with `git worktree add`)
estimated_sessions: 1-2
estimated_time: 90-120 min total
llm_cost: $0
---

# PR #224 Recovery + Root-Cause Investigation of Silent Merge Content Loss

## §0 — The bug being recovered (read first)

**Discovery 2026-06-08 evening:** PR #224 was reported merged earlier today. In reality, `git merge-base --is-ancestor 5bf80da6 origin/main` returns NOT-ANCESTOR. The commit lives on `origin/fix/cockpit-polish-round` but never reached main.

**This is the SECOND time today this has happened.** PR #221 (Phase α) had the same silent merge-loss; PR #225 recovered it.

**What PR #224 was supposed to deliver (per commit 5bf80da6):**
- §1 CRITICAL: clear/execute route transaction-wrapped; ClearConfirmModal + ClearIconButton defensive r.text()+JSON.parse() instead of crash-on-non-JSON
- §2 CRITICAL: bg_reference count_sql fix (migration `176_bg_reference_count_sql_fix.sql`)
- §3 UX: layer-grouped global modal summary
- §4 PERF: SSR chart metadata prefetch → no "Loading chart…" delay
- §5 UX: NEW `RefreshIconButton` component + `/api/cockpit/refresh` endpoint, wired at global/layer/asset
- §6 last_built_at display already correct (no code change)
- §7 UX: 14-char chart ID + click-to-copy

**Current observable symptoms** (because PR #224 isn't on main):
- Delete button still crashes with "Unexpected end of JSON input" on error paths
- No refresh button anywhere
- "Loading chart…" delay persists
- Global modal still shows "5 tables + 32 more" overflow
- Chart ID still 8-char truncated

**Complication:** PR #225 (Phase α recovery) landed AFTER PR #224's branch was cut. PR #225 touched several of the same files. Cherry-pick will have REAL conflicts (clean cherry-pick is not available).

## §1 — Conflict map

Files touched by both PR #224 (5bf80da6) AND PR #225 (d365bea9):

| File | PR #225 brought (Phase α work) | PR #224 brought (polish round) | Resolution strategy |
|---|---|---|---|
| `platform/scripts/seed/asset_registry_seed.ts` | +4 brahmagyan entries, bg_text_index/bg_reference count_sql update | +1 line tweak (likely bg_reference count_sql refinement) | KEEP BOTH: §225's entries + apply §224's count_sql tweak ON TOP |
| `platform/src/lib/jyotish/asset_names.ts` | +4 L0 entries (bg_yogas/dashas/doshas/compendium-index) | No change in §224 | KEEP §225 (no conflict) |
| `platform/src/lib/retrieval/registry/parity_check.ts` | L0_BRAHMAGYAN_ASSETS const with 12 keys | No change in §224 | KEEP §225 (no conflict) |
| `platform/src/app/api/cockpit/clear/execute/route.ts` | (pre-existed; PR #225 didn't change) | §224's transaction-wrap + per-table try/catch | TAKE §224 entirely |
| `platform/src/app/api/cockpit/clear/route.ts` | (pre-existed) | §224's per-asset try/catch + layer_summary | TAKE §224 entirely |
| `platform/src/app/api/cockpit/refresh/route.ts` | DOES NOT EXIST | NEW from §224 | ADD §224's file as-is |
| `platform/src/lib/components/cockpit/v2/RefreshIconButton.tsx` | DOES NOT EXIST | NEW from §224 | ADD §224's file as-is |
| `platform/src/lib/components/cockpit/v2/ClearConfirmModal.tsx` | (pre-existed) | §224's defensive parse + layer-grouped render | TAKE §224 entirely |
| `platform/src/lib/components/cockpit/v2/ClearIconButton.tsx` | (pre-existed) | §224's defensive parse | TAKE §224 entirely |
| `platform/src/lib/components/cockpit/v2/CockpitShell.tsx` | (pre-existed; may have minor §225 changes) | §224's defensive parse + initialChartMeta prop | TAKE §224, integrate §225's L0 awareness if any |
| `platform/src/lib/components/cockpit/v2/CockpitHeader.tsx` | (pre-existed) | §224's 14-char chartId + RefreshIconButton wire | TAKE §224 entirely |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | (pre-existed; PR #225 may have touched it via the recovery cherry-pick) | §224's RefreshIconButton wire | MANUAL MERGE: keep PR #225's existing structure + add §224's RefreshIconButton block |
| `platform/src/lib/components/cockpit/v2/LayerPanel.tsx` | (pre-existed; same notes) | §224's RefreshIconButton wire | MANUAL MERGE |
| `platform/src/app/clients/[id]/build/page.tsx` | (pre-existed; layout work) | §224's SSR chart metadata prefetch | TAKE §224 |
| `platform/src/hooks/useChartContext.ts` | (pre-existed) | §224's initialMeta parameter | TAKE §224 |

**Migration number collision:**
- `platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql` — already on main (from PR #225)
- `platform/supabase/migrations/176_bg_reference_count_sql_fix.sql` — what PR #224 wants to add

Two files claiming migration number 176. **RESOLUTION:** rename PR #224's migration to the next available number (likely `180_bg_reference_count_sql_fix.sql`). Re-apply to prod only if needed — check first whether the count_sql on prod is already correct.

## §2 — Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --prune

# Confirm current state
git log --oneline origin/main -3
# Expect d365bea9 at top (Phase α recovery)

# Verify the polish-round branch still has 5bf80da6 on origin
git log --oneline origin/fix/cockpit-polish-round -3
# Expect 5bf80da6 at top

# Pre-create the worktree
git worktree add -b fix/pr224-recovery /Users/Dev/Vibe-Coding/Apps/MadhavPR224Recover main

cd /Users/Dev/Vibe-Coding/Apps/MadhavPR224Recover
git log --oneline -3   # confirm on main HEAD = d365bea9

# DB proxy (for verification queries; no schema changes from this brief)
bash platform/scripts/start_db_proxy.sh > /tmp/proxy_pr224.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
```

**CHECKPOINT setup:** worktree on `fix/pr224-recovery`; main HEAD is `d365bea9`.

## §3 — Cherry-pick 5bf80da6 with conflict resolution

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavPR224Recover
git cherry-pick 5bf80da6
```

**Expected behavior:** git reports conflicts in some/all files listed in §1. Resolve per the conflict map. For each file:

1. Open it; find the `<<<<<<<` / `=======` / `>>>>>>>` markers
2. Resolve per §1's "Resolution strategy" column
3. `git add <file>`

**Migration collision resolution:**
```bash
# 5bf80da6 added platform/supabase/migrations/176_bg_reference_count_sql_fix.sql
# main already has  platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql
# RENAME the conflicting one to use the next available number
NEXT=$(ls platform/supabase/migrations/ | grep -E '^[0-9]+_' | sed -E 's/^([0-9]+).*/\1/' | sort -n | tail -1 | awk '{print $1+1}')
git mv platform/supabase/migrations/176_bg_reference_count_sql_fix.sql platform/supabase/migrations/${NEXT}_bg_reference_count_sql_fix.sql
echo "Renamed to: ${NEXT}_bg_reference_count_sql_fix.sql"
```

When all conflicts resolved:
```bash
git status   # expect: no remaining conflict markers
git cherry-pick --continue   # opens the editor with cherry-pick commit message; keep it
```

**CHECKPOINT 3:** cherry-pick committed. `git log --oneline -3` shows your cherry-picked commit on top of d365bea9.

```bash
# Verify what landed
git diff origin/main..HEAD --stat | tail -20
# Expect ~15 files changed (per §1), ~400 insertions
```

## §4 — Verify the polish-round work is now staged correctly

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavPR224Recover

# RefreshIconButton component file
ls platform/src/lib/components/cockpit/v2/RefreshIconButton.tsx && echo "  RefreshIconButton present ✓"

# refresh route file
ls platform/src/app/api/cockpit/refresh/route.ts && echo "  /api/cockpit/refresh present ✓"

# Migration renamed
ls platform/supabase/migrations/*bg_reference_count_sql_fix*.sql && echo "  bg_reference fix migration present ✓"

# Verify RefreshIconButton is wired in 3 places
grep -l "RefreshIconButton" platform/src/lib/components/cockpit/v2/*.tsx | head -10
# Expect: at minimum CockpitHeader.tsx, LayerPanel.tsx, AssetRow.tsx
```

## §5 — Code quality verification

```bash
cd platform
npx tsc --noEmit 2>&1 | tail -20
# Expect 0 errors

npx vitest run src/lib/jyotish/__tests__/asset_names.test.ts 2>&1 | tail -10
# Expect 28/28 pass (Phase α tests preserved)

npx vitest run src/app/api/cockpit/clear/__tests__/ 2>&1 | tail -15 || echo "(test dir may not exist; ignore)"
cd ..
```

**CHECKPOINT 5:** tsc clean. Tests pass. If tsc fails, the conflict resolution missed something — fix before committing.

## §6 — Determine whether bg_reference count_sql fix needs prod apply

```bash
# Read the migration content
cat platform/supabase/migrations/*bg_reference_count_sql_fix*.sql

# Check current prod count_sql for bg_reference
psql_prod -At -c "SELECT count_sql FROM asset_registry WHERE asset_id='bg_reference'"
```

If prod count_sql already matches the migration's intent (the 15-table sum, with all SQL keywords correct), DO NOT re-apply — the migration stays in main as installable history for fresh deploys only.

If prod count_sql is broken (missing SELECT or otherwise malformed), apply the migration:
```bash
psql_prod -f platform/supabase/migrations/*bg_reference_count_sql_fix*.sql
```

## §7 — Commit + push + PR

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavPR224Recover

# Add the audit trail markdown
cat > 00_ARCHITECTURE/PR224_RECOVERY_v1_0.md <<EOF
# PR #224 Recovery — Cockpit Polish Round Silently Lost (2026-06-08)

## Discovery
After PR #224 was reported merged + Cockpit polish round shipped memory was written,
native observed:
- No refresh button on cockpit
- Delete button still crashing with "Unexpected end of JSON input"

Investigation:
\`git merge-base --is-ancestor 5bf80da6 origin/main\` returned NOT-ANCESTOR.
Commit 5bf80da6 was on \`origin/fix/cockpit-polish-round\` but never landed on main.

This is the SECOND occurrence today; PR #221 (Phase α) had the same silent merge-loss.

## Conflict landscape vs PR #225
Files touched by both PR #224 and PR #225 (which landed in between):
- asset_registry_seed.ts (keep both)
- clear/execute/route.ts (take PR #224)
- clear/route.ts (take PR #224)
- ClearConfirmModal.tsx (take PR #224)
- ClearIconButton.tsx (take PR #224)
- CockpitShell.tsx, CockpitHeader.tsx, AssetRow.tsx, LayerPanel.tsx (manual merge)
- Migration 176 collision: renamed PR #224's to next available number

## Recovery
Cherry-picked 5bf80da6 onto fix/pr224-recovery from current main HEAD.
Resolved conflicts per the conflict map.
Verified RefreshIconButton + /api/cockpit/refresh present + wired.
tsc + vitest green.

## Architectural lesson reinforced
See \`[[feedback-phase-sealed-needs-merge-verification]]\`. Today's pattern shows the
verification discipline needs to apply to every merge, not just phase-level ones.
EOF

git add -A
git status

git commit -m "fix(cockpit): recovery — bring PR #224 polish round to main + root-cause audit

PR #224 was reported merged but commit 5bf80da6 never landed on main.
\`git merge-base --is-ancestor 5bf80da6 origin/main\` returns NOT-ANCESTOR.

This PR cherry-picks 5bf80da6 onto current main HEAD (d365bea9 Phase α recovery)
with conflicts resolved per CLAUDECODE_BRIEF_PR224_RECOVERY_AND_ROOT_CAUSE_v1_0
§1 conflict map.

What this restores:
- §1 clear/execute route transaction-wrap + defensive client JSON parse
- §2 bg_reference count_sql fix (migration renamed to avoid #176 collision)
- §3 layer-grouped global modal summary
- §4 SSR chart metadata prefetch (no 'Loading chart…' delay)
- §5 NEW RefreshIconButton component + /api/cockpit/refresh endpoint, wired
     at global / layer / asset scopes with super_admin gating
- §7 14-char chart ID + click-to-copy in CockpitHeader

This is the SECOND silent-merge-loss recovery today.
PR #221 → PR #225 (Phase α recovery)
PR #224 → THIS PR (cockpit polish recovery)

Audit trail: 00_ARCHITECTURE/PR224_RECOVERY_v1_0.md
Source brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PR224_RECOVERY_AND_ROOT_CAUSE_v1_0.md
Lesson memory: feedback_phase_sealed_needs_merge_verification.md

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push -u origin fix/pr224-recovery

gh pr create --title "fix(cockpit): recovery — bring PR #224 polish round to main (lost merge)" \
  --body "**Critical recovery PR — SECOND silent-merge-loss today.** PR #224 was reported merged but its commit (5bf80da6) never landed on main.

This PR cherry-picks 5bf80da6 onto current main (d365bea9), resolving conflicts with PR #225 (Phase α recovery that landed in between).

Brings to main: refresh button, defensive JSON parse, transaction-wrapped execute, layer-grouped modal, SSR chart prefetch, chart ID copy-on-click.

Audit trail: 00_ARCHITECTURE/PR224_RECOVERY_v1_0.md" \
  --base main --head fix/pr224-recovery
```

## §8 — Post-merge verify (after operator merges + deploys)

```bash
# After merge + Cloud Run deploy completes:
sleep 60
NATIVE_SESSION=$(npx tsx platform/scripts/mint_session_cookie.ts 2>/dev/null || cat /tmp/native_session)

# Probe: /api/cockpit/refresh should exist (was 404)
curl -s -o /dev/null -w "refresh route: %{http_code}\n" \
  -X POST -b "__session=$NATIVE_SESSION" \
  -H "Content-Type: application/json" \
  -d '{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","scope":"global"}' \
  https://madhav.marsys.in/api/cockpit/refresh
# Expect 200 (or 401 if cookie expired); NOT 404
```

UI smoke (Chrome MCP):
- Open `/clients/<id>/build`
- Confirm refresh button visible next to delete at 3 scopes
- Click trash on bg_ephemeris → modal shows real counts (not "Unexpected end of JSON input")
- Click trash on Brahmagyan layer header → modal shows layer-grouped summary
- Chart ID in header shows 14 chars + clicking copies to clipboard

## §9 — ROOT-CAUSE INVESTIGATION (parallel to recovery)

Two PRs in one day silently lost their content. Need to understand why. Investigate WITHOUT blocking the recovery PR above.

### §9.1 — Examine the PR #224 merge commit on GitHub

The merge commit (whatever it ended up being) tells us what GitHub actually merged.

```bash
# Find merge commit referencing PR #224 from anywhere
gh pr view 224 --json mergeCommit,mergedAt,mergedBy,mergeable,mergeStateStatus,baseRefName,headRefName,state 2>&1
```

**Critical to capture:**
- `mergeCommit.oid` — the SHA of the merge commit GitHub created
- `mergedAt` — when it was merged
- `mergedBy` — who clicked the merge button
- `state` — should be MERGED (per the report)

```bash
# Inspect the merge commit
MERGE_SHA=$(gh pr view 224 --json mergeCommit -q .mergeCommit.oid)
echo "PR #224 merge commit: $MERGE_SHA"

# Show what was actually included in the merge
git show "$MERGE_SHA" --stat
# This tells us: if the merge commit DIFFER FROM main HEAD = the merge applied to a different branch (highly unlikely)
# OR if the merge commit IS on main = then the merge applied but produced empty diff (the actual bug)

# Verify ancestor relationship
git merge-base --is-ancestor "$MERGE_SHA" origin/main && echo "  merge on main: YES" || echo "  merge on main: NO"
```

### §9.2 — Same for PR #221

```bash
gh pr view 221 --json mergeCommit,mergedAt,mergedBy,mergeable,mergeStateStatus,baseRefName,headRefName,state 2>&1
MERGE_SHA_221=$(gh pr view 221 --json mergeCommit -q .mergeCommit.oid)
echo "PR #221 merge commit: $MERGE_SHA_221"
git show "$MERGE_SHA_221" --stat
git merge-base --is-ancestor "$MERGE_SHA_221" origin/main && echo "  merge on main: YES" || echo "  merge on main: NO"
```

### §9.3 — Compare with a known-working merge (PR #225 worked)

```bash
gh pr view 225 --json mergeCommit,mergeStateStatus 2>&1
MERGE_SHA_225=$(gh pr view 225 --json mergeCommit -q .mergeCommit.oid)
echo "PR #225 merge commit (working): $MERGE_SHA_225"
git show "$MERGE_SHA_225" --stat
```

### §9.4 — Possible root causes to test

Based on output of §9.1-§9.3, the bug is ONE of:

1. **Squash-merge edge case** — if both PRs used "Squash and merge" and the squash produced empty content. Inspect the squash commit content.
2. **Branch-protection rule rewriting commits** — if there's a CI hook (e.g. `.github/workflows/rewrite-on-merge.yml`) that re-cherry-picks selectively. Check `.github/` for any merge-time workflow.
3. **Rebase-then-merge mis-application** — if the PR was rebased before merge and the rebase dropped commits. Check git reflog on the feature branch.
4. **Squash + rebase collision** — feature branch was rebased AFTER squash merge button was clicked, producing a no-op merge.
5. **GitHub bot or operator action** — someone (a bot, an operator) ran a force-push after the merge that reverted main.

Check for likely culprits:
```bash
# Check for any rewriting workflows
ls .github/workflows/*.yml | xargs -I {} grep -l "merge\|squash\|rebase\|cherry" {} | head -5

# Check git reflog for unusual main-branch activity
git reflog origin/main 2>&1 | head -20 || echo "(reflog may not be available for remote-tracking refs)"

# Show last 5 commits on main with full details (author + date + message)
git log origin/main --pretty=format:'%h %ai %an %s' -10
```

### §9.5 — Hypothesis to write up

Based on §9.1-§9.4 output, write `/tmp/merge_loss_root_cause_hypothesis.md` with:
- What the GitHub merge commits actually contain
- Likely root cause from the 5 candidates above
- Recommended mitigation (e.g. enforce "Create a merge commit" instead of squash; or add a post-merge verification CI gate that fails the build if the merge commit's diff is empty)
- Decision: is this likely to recur on the NEXT PR if not fixed?

Surface this hypothesis in the recovery PR description so native can review + decide on the mitigation.

## §10 — Hard stops

- §3 cherry-pick conflicts can't be resolved (markers don't make sense) → STOP, halt + report; the lost-merge recovery may need to be done by hand-applying each file
- §3 migration rename produces unexpected number collision → STOP, audit the migration numbering scheme
- §5 tsc fails after cherry-pick → conflict resolution missed an integration; fix or report
- §6 prod count_sql is malformed → migration needs prod apply; do it, verify
- §8 post-deploy refresh route still returns 404 → DEPLOY didn't pick up the merge; check Cloud Run revision SHA vs merge SHA
- §9 investigation produces no clear root cause → write up "unresolved" hypothesis; propose a CI post-merge verification gate as defense-in-depth

## §11 — Out of scope

- Phase β/γ L0 work
- New features beyond what PR #224 originally promised
- Fixing the GitHub merge bug itself (we identify; native chooses mitigation)

## §12 — Memory updates after merge

Append to `[[cockpit-polish-round-shipped]]` memory:
> AMENDMENT 2026-06-08 evening: PR #224 was discovered lost-merge same day; PR #N (this PR) recovered. See `[[pr224-recovery]]`.

Add new memory `[[pr224-recovery-and-merge-loss-investigation]]` capturing what §9 found.

Update `[[feedback-phase-sealed-needs-merge-verification]]` to emphasize "applies to EVERY merge, not just phase-level."

Begin §2 setup.

---

*End of brief.*
