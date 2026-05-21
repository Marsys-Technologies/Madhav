---
artifact: POST_MERGE_OPERATOR_CHECKLIST.md
canonical_id: POST_MERGE_OPERATOR_CHECKLIST
version: 1.0
status: LIVE
authored_by: Cowork (Claude Opus 4.7) 2026-05-21
purpose: >
  Single-page operator checklist of post-merge actions following PR #112
  (chat-v2/pr-111-remediation). Covers Cloud Run flag flips, fresh Cloud Build,
  panchang bootstrap rebuild, and the launch order for the three governance
  hygiene follow-up briefs spawned from PR-111-REMEDIATION's SESSION_HALT.md.
---

# Post-PR-112 Operator Checklist

## §1 — Review and merge PR #112

1. Visit [PR #112](https://github.com/amonty84/Madhav/pull/112). Read SESSION_HALT.md on the branch (now `00_ARCHITECTURE/chat_v2_briefs/pr_111_remediation/` after the next governance pass; on this branch it's still at root as SESSION_HALT.md per the brief's §6 explicit allowance).
2. Verify the AC.1–AC.10 table in the PR body matches expectations.
3. Spot-check `platform/cloudbuild.yaml` — `grep -c "NEXT_PUBLIC_MARSYS_FLAG_R10" platform/cloudbuild.yaml` should return 5.
4. Merge via the GitHub UI or `gh pr merge 112 --squash --delete-branch`. Worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavPR111/` can be removed via `git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavPR111` after merge.

## §2 — Cloud Run env-var flips (R8 server-side flags)

PR #112 wired the props but `feature_flags.ts` defaults to `false`. Until the operator flips the env-vars in Cloud Run, slash/export/tokens features won't render in prod.

```bash
gcloud run services update amjis-web --region asia-south1 --update-env-vars \
  MARSYS_FLAG_R8_SLASH_ENABLED=true,\
MARSYS_FLAG_R8_EXPORT_ENABLED=true,\
MARSYS_FLAG_R8_TOKENS_ENABLED=true
```

After each flip, smoke-test the corresponding UI feature on `https://madhav.marsys.in/clients/.../consume` — type `/` to confirm slash menu, click the export icon in the header to confirm dropdown, type in the composer to confirm token-count line appears.

## §3 — Fresh Cloud Build (for the NEXT_PUBLIC R10 build-args)

The two new `NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE` + `NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES` build-args are baked into bundled JS at build-time. They only take effect after a fresh Cloud Build runs.

```bash
gcloud builds submit --config=platform/cloudbuild.yaml platform/
```

After deploy, smoke-test (a) scroll discipline — scroll up in a long chat, confirm autoscroll-resume behavior matches expectation; (b) validator failure bands — trigger a validator failure (or check an existing failed-validator chart) and confirm the failure band renders.

If either feature still doesn't render, check the build log for the build-arg propagation and confirm the Cloud Run revision picked up the new image.

## §4 — Panchang bootstrap rebuild (carryover from PR #110)

Still pending from PR #110 (per CLAUDE.md §E Phase 4C entry, operator steps marked PENDING):

```bash
# 1. Apply migration 069 (extends panchanga_daily with 5 JSONB columns + GIN indexes)
psql $DATABASE_URL -f platform/migrations/069_extend_panchanga_daily.sql

# 2. Dry-run bootstrap (validates plan, no writes)
python platform/scripts/panchang/bootstrap_panchanga.py --dry-run

# 3. Full rebuild (writes ~73K rows to panchanga_daily_staging; ~60 min)
python platform/scripts/panchang/bootstrap_panchanga.py

# 4. Staging swap per RUNBOOK_EPHEMERIS_REBUILD_v1_0.md §4 (cuts traffic to the staging table)
```

The bootstrap guard fix from PR #111 commit `77a27dc` (now `panchanga_daily_staging`, not the live table) means step 3 won't abort on a populated live table. Good.

## §5 — Governance hygiene follow-up briefs (launch order)

Three briefs sit in `00_ARCHITECTURE/governance_hygiene_briefs/`. Recommended sequence — each is its own session, each runs independently:

### Run 1 — `GH_DRIFT_DETECTOR_FIX_BRIEF_v1_0.md`

Smallest, most narrow. Resolves the exit-4 crash. Future hygiene sessions can then run the full validator triple cleanly.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
cp 00_ARCHITECTURE/governance_hygiene_briefs/GH_DRIFT_DETECTOR_FIX_BRIEF_v1_0.md CLAUDECODE_BRIEF.md
# Edit CLAUDECODE_BRIEF.md status: STORED → ACTIVE
claude --dangerously-skip-permissions "Read CLAUDE.md (§C mandatory reading) and CLAUDECODE_BRIEF.md in full. Execute the brief autonomously end to end. Emit SESSION_OPEN handshake first. Run every §4 step in order. Halt only via SESSION_HALT.md per §5. Do not merge. Emit Step 9 final summary."
```

After PR opens and is reviewed + merged, `rm CLAUDECODE_BRIEF.md` from main checkout root.

### Run 2 — `GH_SESSION_LOG_STRUCTURE_BRIEF_v1_0.md`

Medium scope. Run after Run 1 so the validator suite is clean. Restructures SESSION_LOG.md headings to satisfy 36 HIGH violations.

```bash
cp 00_ARCHITECTURE/governance_hygiene_briefs/GH_SESSION_LOG_STRUCTURE_BRIEF_v1_0.md CLAUDECODE_BRIEF.md
# status: STORED → ACTIVE, then launch claude --dangerously-skip-permissions as above
```

### Run 3 — `GH_CORPUS_FRONTMATTER_BACKFILL_BRIEF_v1_0.md`

Largest scope. 100+ files touched. Run last. Closes 118 MEDIUM + 3 HIGH violations.

```bash
cp 00_ARCHITECTURE/governance_hygiene_briefs/GH_CORPUS_FRONTMATTER_BACKFILL_BRIEF_v1_0.md CLAUDECODE_BRIEF.md
# status: STORED → ACTIVE, then launch as above
```

After all three merge, run the full validator triple manually as a baseline:

```bash
python3 platform/scripts/governance/schema_validator.py; echo "schema exit: $?"
python3 platform/scripts/governance/drift_detector.py; echo "drift exit: $?"
python3 platform/scripts/governance/mirror_enforcer.py; echo "mirror exit: $?"
```

Expected end-state — schema_validator exit ≤ 2 (LOW residuals OK), drift_detector exit ≤ 3, mirror_enforcer exit 0.

## §6 — What you do NOT need to do

- `useBranches` wiring for Chat V2 Checks 23/24 — defer to a separate R10/R11 session with its own brief.
- Edit CLAUDE.md AC-wording for "exit 0" — the AC wording was per-brief, not global. The new GH briefs already specify "exit ≤ 3" instead. CLAUDE.md itself doesn't need an amendment.
- `git rm CLAUDECODE_BRIEF.md` from main checkout root — the Cowork session that authored the PR-111-REMEDIATION brief has already removed it. Verify with `ls -la CLAUDECODE_BRIEF.md` — should return "No such file or directory".

## §7 — Tracking

If you want a one-glance status surface for the three hygiene briefs, the cleanest pattern is to keep this checklist file updated as each PR merges. After each governance hygiene PR merges, append a "merged YYYY-MM-DD as PR #N" tag to the relevant §5 sub-section above.

End of checklist.
