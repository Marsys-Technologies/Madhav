---
artifact: CLAUDECODE_BRIEF_PURNA_ANVESANA_RESUMPTION
version: 1.0
status: PREPARATION_COMPLETE_AWAITING_NATIVE_SOURCE_EXECUTION_AUTHORIZATION
date: 2026-09-27
native_authority: preparation only
source_execution_authorized: false
merge_authorized: false
production_authorized: false
worktree: /Users/Dev/.codex/worktrees/purna-anvesana-resumption-v2/Madhav
branch: codex/purna-anvesana-resumption-v2
frozen_base: 6b26f3ff05ee0aba3cdd964bce62292496ae6b62
---

# ACTIVE CHECKOUT BRIEF — Pūrṇa Anveṣaṇa preparation lock

This file governs Claude Code whenever it opens this branch. It intentionally replaces the L3 root
brief **only on the isolated Pūrṇa branch**. L3 and all other campaigns remain outside this
worktree and outside this authority.

## Current authority

The Native authorized preparation only. Preservation, read-only reconciliation, the isolated
worktree, and the resumption briefs may be inspected and verified. Source implementation has not
been authorized.

Until this file is explicitly revised after a separate Native authorization, Claude Code must:

1. verify the exact cwd, branch, base, and clean preparation state;
2. read the preparation corpus;
3. perform read-only inspection if asked;
4. report the preparation state;
5. make no additional repository change.

## Required reading

1. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PREPARATION_MANIFEST_2026-09-27_v1_0.md`
2. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/RESUMPTION_SALVAGE_MATRIX_v1_0.md`
3. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/RESUMPTION_ARCHITECTURE_ADDENDUM_v1_0.md`
4. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md`
5. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF_v1_0.md`
6. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_ANVESANA_CLAUDE_CODE_RESUMPTION_STRATEGY_v1_0.md`
7. `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/CLAUDE_CODE_RESUMPTION_KICKOFF_v1_0.md`
8. `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md`

## Preparation-only writable surface

No further files are writable under the present authority. The preparation artifacts are expected
to be committed locally and the worktree left clean.

## Forbidden under current authority

- application, test, generated, workflow, migration, campaign-state, or acceptance-corpus edits;
- cherry-pick, rebase, merge, push, PR creation/modification, or branch retargeting;
- database queries requiring secrets, database writes, rebuilds, live collection, deployment, or
  production/configuration changes;
- modifying, cleaning, switching, archiving, or deleting any other worktree;
- reading or committing the raw private live-evidence payload;
- resuming the old Codex task as an executor;
- representing source, candidate, live, or product completion.

## Activation rule

Source execution begins only after all of the following:

1. the Native explicitly authorizes source execution in the product-strategy conversation;
2. that authority and its exact boundary are recorded here;
3. status changes to `ACTIVE_SOURCE_EXECUTION`;
4. current `origin/main`, open PRs, migration allocations, and cross-campaign ownership are refreshed;
5. the kickoff prompt is issued to Claude Code in this exact worktree.

Merge, database mutation/rebuild, deployment, live collection, and product acceptance remain separate
authority gates even after source execution is activated.

If this brief and another branch's brief conflict, this file governs only this isolated worktree.
Stop rather than editing another campaign's surface.
