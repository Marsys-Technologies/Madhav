---
artifact: CLAUDECODE_BRIEF_PURNA_ANVESANA_RESUMPTION
version: 1.5
status: R5A_COMPLETE_R5B_SOURCE_MERGE_AUTHORIZED_FOR_PR_2742
candidate_disposition: PR_CANDIDATE_REVIEWED_CI_GREEN_CANDIDATE_VALIDATION_NOT_RUN
date: 2026-09-28
native_authority: R0-R3 source execution authorized 2026-09-27; R4 local integration, candidate
  acceptance and a narrow current-main refresh authorized 2026-09-28; R5A (candidate publication,
  pull-request creation, CI repair and independent review only) authorized by the Native on
  2026-09-28.
source_execution_authorized: true
r4_local_integration_authorized: true
r4_candidate_acceptance_authorized: true
r5a_candidate_publication_authorized: true
r5a_status: COMPLETE   # PR #2742 accepted by the Native at d5c4c1f27; CI green
r5b_source_merge_authorized: true   # PR #2742 ONLY, once its head is clean and fully green
r5b_source_merge_status: AUTHORIZED_NOT_YET_VERIFIED_IN_THIS_FILE   # completion is recorded only after the merge is verified, outside this file (protected main)
r3_source_complete_sha: 71ed6bbfda22ec2b23ba85f79158232cff4cd445
first_main_integration_sha: 9285326caa394f76ea6849fd3fe0309bc6d90239
r4_local_candidate_sha: ac226f4fce790616d9e58e2c235497ca071650cc
pull_request: https://github.com/Marsys-Technologies/Madhav/pull/2742
push_authorized: true   # R5A: this branch only, ordinary pushes, never force
pr_change_authorized: true   # R5A: PR #2742 only; PR #2704 and #2705 are untouchable
merge_to_protected_main_authorized: false   # except PR #2742 under r5b_source_merge_authorized
production_authorized: false
database_write_authorized: false
migration_authorized: false
producer_rebuild_authorized: false
deployment_authorized: false
live_collection_authorized: false
r5c_or_later_authorized: false
product_completion_claim_authorized: false
worktree: /Users/Dev/.codex/worktrees/purna-anvesana-resumption-v2/Madhav
branch: codex/purna-anvesana-resumption-v2
frozen_base: 6b26f3ff05ee0aba3cdd964bce62292496ae6b62
---

# ACTIVE CHECKOUT BRIEF — Pūrṇa Anveṣaṇa R4 local integration and candidate acceptance

This file governs Claude Code whenever it opens this branch. It intentionally replaces the L3 root
brief **only on the isolated Pūrṇa branch**. L3 and all other campaigns remain outside this
worktree and outside this authority.

## R5B (2026-09-28) — source merge of PR #2742 only

The Native accepted R5A as complete (PR #2742, head `d5c4c1f27`, all required checks green) and
authorized R5B: merge PR #2742 only, without auto-merge, after reconfirming the head is clean and
fully green against current protected main. Main moved once more (PR #2745, deploy-workflow files
only, no overlap); it was integrated with an ordinary merge commit and its files verified
byte-identical to main. This file records the state at merge time; because protected main cannot
be edited after the merge without another PR, **completion of the merge is not asserted here** —
it is recorded in the closeout report and the follow-up kickoff package.

**Not complete, and not claimed:** production deployment, empirical/candidate validation
(`candidate_validation` remains `NOT_RUN`), and campaign or product completion. Still prohibited:
deployment, production credentials, database writes, migration application, producer rebuilds,
live collection, auto-merge, and any further merge.

## R5A (2026-09-28) — publication and review

The Native authorized R5A: publish the candidate, open one pull request against `main`, repair
branch-caused CI, and run an independent review — nothing further. **Still prohibited:** merging
the PR; closing or modifying PR #2704 or #2705; production credentials; database writes, repair
migrations or migration application; producer rebuilds; deployment; live collection; R5B or later;
product-completion, live, empirical or production-acceptance claims. The branch is kept current
with protected main through ordinary merge commits only — never a force-push or history rewrite.

State: branch pushed; PR #2742 open against `main`. CI found one branch-caused failure (a
Next.js-illegal export from the inquiry route module, fixed by extracting `bounded_body.ts` and
proven with a real `next build`). Protected main then advanced by PRs #2741, #2743 (BYOK routing)
and #2744; merged with six semantic conflict resolutions and a regenerated census. Independent
security and semantic reviews found no HIGH defect; the semantic review's three MED findings
(managed successor gap, Portal citation delivery, fenced-probe/unfenced-read) were each verified
and fixed with tests, the last requiring the canonical acceptance successor
`BEYOND_ACARYA_ACCEPTANCE_v9.json` (predecessor v8, all six metrics unchanged).
`candidate_validation` remains `NOT_RUN`: local deterministic suites are not candidate, live,
empirical or production validation.

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
was not rewritten, rebased, or cherry-picked. The R4 candidate-acceptance program (tsc, both
codegen freshness checks, pin-lint, full suite, independent review) then ran green on the follow-up
G-ARTIFACT commit `9c6c01e912581fe890ab2594906cd719f472b03e` (regenerated snapshot/census/goldens,
new canonical `BEYOND_ACARYA_ACCEPTANCE_v8.json` naming main's v7 as predecessor).

**Narrow R4 current-main refresh (2026-09-28, same-day, does not expand authority into R5):**
origin/main advanced by exactly one further commit, `acf8d2baed6345097dd28a34e533329be52046ec`
(PR #2740, "fix(deploy): add protected Jātaka migration window") — confirmed the only movement
after `4eaa9d2f4`. One incidental shared path
(`00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_CONTROLLED_PRODUCTION_ROLLOUT_ADDENDUM_v1_0.md`)
was PR #2739 content Purna never authored or modified, so PR #2740's further edit to it required no
reconciliation. Merged locally with `git merge` (no conflicts, no `--theirs`/`--ours` needed) at
`110be90304a6e833ee72f52e3a4203e775699b10` (parents: `9c6c01e91` and `acf8d2bae`). PR #2740's
deployment workflow, Jātaka capability script, and associated security/tests verified byte-identical
to `origin/main`'s own copies post-merge. Purna source was not touched merely because main advanced.
Post-merge: PR #2740's 3 focused test files (73 tests) pass; `tsc --noEmit` clean; both codegen
freshness checks report the SAME hashes as before this refresh (`sha256:0556249e...` snapshot,
`sha256:5545d037...` census — zero drift); pin-lint 0 new violations (63 pre-existing, unchanged);
full suite 13,037 passed / 0 failed / 723 skipped (pre-existing) / 2 todo across 1,214 files (up
from 1,213 — PR #2740's new `jataka_schema_capability.test.ts`). The canonical `v7.json`, the 5
`historical_fork_v7_v11/` files, and `v8.json` are all byte-identical to their pre-refresh state
(verified by diff); no new acceptance artifact was created, since neither the executable acceptance
report nor the capability content changed — `v8.json`'s own `candidate_validation: NOT_RUN` field
was not touched and remains honest. **Local candidate disposition:
`R4_LOCAL_CANDIDATE_READY_CANDIDATE_VALIDATION_NOT_RUN`** — the local deterministic suites above are
NOT candidate, live, empirical, or production validation; they are exactly what they are, local
deterministic checks.

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
