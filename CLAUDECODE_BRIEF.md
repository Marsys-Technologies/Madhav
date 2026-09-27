---
artifact: CLAUDECODE_BRIEF_PURNA_ANVESANA_RESUMPTION
version: 1.2
status: ACTIVE_R4_LOCAL_CANDIDATE_ACCEPTANCE
date: 2026-09-28
native_authority: R0-R3 source execution authorized 2026-09-27; R4 local integration and candidate
  acceptance authorized by the Native on 2026-09-28 ("Native authorizes R4 local integration and
  candidate acceptance for Pūrṇa Anveṣaṇa within the following boundary...")
source_execution_authorized: true
r4_local_integration_authorized: true
r4_candidate_acceptance_authorized: true
r3_source_complete_sha: 71ed6bbfda22ec2b23ba85f79158232cff4cd445
main_integration_sha: 9285326caa394f76ea6849fd3fe0309bc6d90239
push_authorized: false
pr_change_authorized: false
merge_to_protected_main_authorized: false
production_authorized: false
database_write_authorized: false
migration_authorized: false
producer_rebuild_authorized: false
deployment_authorized: false
live_collection_authorized: false
r5_authorized: false
product_completion_claim_authorized: false
worktree: /Users/Dev/.codex/worktrees/purna-anvesana-resumption-v2/Madhav
branch: codex/purna-anvesana-resumption-v2
frozen_base: 6b26f3ff05ee0aba3cdd964bce62292496ae6b62
---

# ACTIVE CHECKOUT BRIEF — Pūrṇa Anveṣaṇa R4 local integration and candidate acceptance

This file governs Claude Code whenever it opens this branch. It intentionally replaces the L3 root
brief **only on the isolated Pūrṇa branch**. L3 and all other campaigns remain outside this
worktree and outside this authority.

## Current authority

The Native explicitly authorized autonomous source execution for R0 through R3 on 2026-09-27; R3
was declared source-complete at `71ed6bbfda22ec2b23ba85f79158232cff4cd445` (9 commits from
`96fa7f4c9` through `2114b873c`, 42 commits total after activation; 5 packets closed: explicit-empty
build-fence semantics, actual certify-request byte limit, genuine per-mode proof typing, remaining
residual classification, final R3 boundary regen+review+commit).

On 2026-09-28 the Native authorized R4 local integration and candidate acceptance within this
boundary:

**Authorized:** update this brief to `ACTIVE_R4_LOCAL_CANDIDATE_ACCEPTANCE`; record R3 source
completion at `71ed6bbfd`; integrate `origin/main@4eaa9d2f4` (PR #2739, Jātaka Chart Workspace
Phase-A3) into `codex/purna-anvesana-resumption-v2` locally; resolve source conflicts semantically
(never choosing one side wholesale); reconcile the divergent `BEYOND_ACARYA_ACCEPTANCE` v7 lineage
fork without losing either history; regenerate governed artifacts; run the complete R4
candidate-acceptance program; make local commits.

**Still prohibited:** push; PR creation or modification; merging the campaign into protected main;
production credentials; database writes or repair migrations; producer rebuilds; deployment; live
collection; R5 or product-completion claims.

Main integration completed at merge commit `9285326caa394f76ea6849fd3fe0309bc6d90239` (parents:
`71ed6bbfd` and `4eaa9d2f4`). Origin/main confirmed exactly one commit ahead of the merge-base
(`6b26f3ff0`) — PR #2739's own squash-merge — before integration; Purna's 50-commit local history
was not rewritten, rebased, or cherry-picked.

Before the first edit in a fresh session under this brief, Claude Code must:

1. verify that `pwd` is exactly the worktree recorded above, not a `.claude/worktrees/...` copy;
2. verify the branch, current HEAD, `origin/main`, clean start, remotes, and active worktree census;
3. refresh open PR identities, current migration allocations, and cross-campaign file ownership;
4. stop if the session's own file tools are registered to another checkout, even when its shell has
   changed directory.

## Required reading

1. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PREPARATION_MANIFEST_2026-09-27_v1_0.md`
2. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/RESUMPTION_SALVAGE_MATRIX_v1_0.md`
3. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/RESUMPTION_ARCHITECTURE_ADDENDUM_v1_0.md`
4. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md`
5. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF_v1_0.md`
6. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_CLAUDE_CODE_RESUMPTION_STRATEGY_v1_0.md`
7. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/CLAUDE_CODE_RESUMPTION_KICKOFF_v1_0.md`
8. `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md`
9. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/historical_fork_v7_v11/LINEAGE_FORK_MANIFEST_v1_0.md`
   (new, R4 boundary — the `BEYOND_ACARYA_ACCEPTANCE_v7.json` lineage-fork reconciliation record)

## Authorized writable surface

Source, focused tests, packet-boundary generated projections, and the minimum truthful campaign
records required for R4 local integration and candidate acceptance may be changed in this worktree,
including: resolving the 10 files PR #2739 and the Purna branch both touched; relocating the
Purna-only `BEYOND_ACARYA_ACCEPTANCE_v7-v11.json` chain to `historical_fork_v7_v11/`; creating the
new canonical `BEYOND_ACARYA_ACCEPTANCE_v8.json` naming protected main's `v7` as predecessor; and
regenerating `capability_knowledge.snapshot.json`, `capability_estate_census.json`, and the
route-port goldens from the merged source. All changes must implement the R4 ruling, carry focused
verification, and be committed locally. Old branches and worktrees remain read-only salvage inputs.
No wholesale rebase or cherry-pick of PR #2705, and no rewrite of Purna's own commit history, is
authorized.

## Forbidden under current authority

- push, PR creation/modification, merge into protected main, or branch retargeting;
- database queries requiring production credentials, database writes, repair migrations, producer
  rebuilds, live collection, deployment, or production/configuration changes;
- modifying, cleaning, switching, archiving, or deleting any other worktree;
- reading or committing the raw private live-evidence payload;
- resuming the old Codex task as an executor;
- representing local source work as pushed, merged, deployed, live-proven, or product-accepted;
- beginning R5, or making any product-completion claim, without a further explicit Native
  authorization;
- classifying a conflict-resolution regression as environmental rather than fixing it.

## Execution boundary

R4 local integration and candidate acceptance are active. A blocked near-miss decision,
credentialed read, producer rebuild, or release packet does not stall independent local work.
Claude Code must continue the highest-value unblocked work and report the exact residual authority
gate.

R5 protected delivery is not active. Push, PR operations, merge into protected main, database
mutation/rebuild, deployment, live collection, use of production credentials, and product
acceptance remain separate authority gates, unchanged by this brief.

If this brief and another branch's brief conflict, this file governs only this isolated worktree.
Stop rather than editing another campaign's surface.
