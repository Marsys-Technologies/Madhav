---
canonical_id: CHAT_V2_R7_MASTER_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-20
owner: Abhisek Mohanty
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
parallel_with:
  - chat-v2/round8-capabilities (R8 — no shared files; flag namespaces isolated)
  - chat-v2/round9-elevation (R9 — no shared files; flag namespaces isolated)
merge_train_position: 1 (first to merge — smallest blast radius)
flag_namespace: MARSYS_FLAG_R7_*
---

# R7 — Chat V2 Polish Round

## Scope

R7 closes the post-§M.16 polish backlog identified in `CHAT_V2_F3_FORENSIC_v1_0.md`. All items are enhancement-only — no new architectural commitments, no schema migrations. The round ships directly on `main` after a single PR with all 7 sessions bundled (or as 7 separate PRs — executor's choice based on review cadence). No operator visual-review gate per-session; automated gates only.

Baseline: Chat V2 is live unconditionally on `main` (post-§M.16 sealing commit `6c431f9`). R7 builds on top of that stable baseline.

## Sessions

| # | ID | Brief | Files Primary | Flag | Depends |
|---|---|---|---|---|---|
| 1 | R7-S1 | R7-S1-citation-double-wrap-fix.md | ConsumeChatV2.tsx | MARSYS_FLAG_R7_CITATION | — |
| 2 | R7-S2 | R7-S2-footnote-citations.md | synthesis_prompt_v2.ts, MarkdownContent.tsx | MARSYS_FLAG_R7_CITATION | R7-S1 |
| 3 | R7-S3 | R7-S3-enrich-citations.md | route.ts, CitationSidePanel.tsx | MARSYS_FLAG_R7_CITATION | R7-S1, R7-S2 |
| 4 | R7-S4 | R7-S4-citation-panel-default-open.md | CitationSidePanel.tsx, ConsumeChatV2.tsx | MARSYS_FLAG_R7_PANEL | R7-S3 |
| 5 | R7-S5 | R7-S5-auto-continue-on-truncation.md | AssistantMessage.tsx, new continue/route.ts | MARSYS_FLAG_R7_CONTINUE | — |
| 6 | R7-S6 | R7-S6-composer-draft-persistence.md | useChatPreferences.ts, Composer.tsx | MARSYS_FLAG_R7_DRAFT | — |
| 7 | R7-S7 | R7-S7-a11y-polish.md | AssistantMessage.tsx, ChatShell.tsx, useHotkeys.ts, MessageActions.tsx | MARSYS_FLAG_R7_A11Y | — |

**Recommended execution order:** S1 → S2 → S3 → S4 (citation chain, sequential); S5, S6, S7 independent (can run in any order after S1).

## Flag Namespace

All R7 flags follow `MARSYS_FLAG_R7_<FEATURE>`. They live in `platform/src/lib/feature_flags.ts`. R7 owns and may append to the `MARSYS_FLAG_R7_*` namespace only. R8 owns `MARSYS_FLAG_R8_*`; R9 owns `MARSYS_FLAG_R9_*`. These namespaces do not overlap.

## Files Locked to Other Streams

R7 must not touch:
- `platform/prisma/schema.prisma` (R8 domain — schema migrations)
- `platform/src/app/api/conversations/branches/**` (R8-S1/S2)
- `platform/src/app/api/conversations/search/**` (R8-S3)
- `platform/src/app/api/projects/**` (R9-S1)
- `platform/src/components/chat/BranchPicker.tsx` (R8-S2)
- `platform/src/components/chat/InlineToolFlow.tsx` (R9-S4)
- `platform/src/components/chat/SlashCommandMenu.tsx` (R8-S6)
- `.github/workflows/deploy.yml` (append-only, avoid unless necessary)
- All governance/architecture files under `00_ARCHITECTURE/`

## Round Acceptance

The R7 round is COMPLETE when:
1. All 7 sessions have their ACs verified (automated gate output attached to PR)
2. `npm run typecheck` exits 0 on the R7 branch
3. `npm test` exits 0 with no new test failures
4. No double-wrap citations observed in a live smoke test
5. PR merged to main via `--no-ff`

## Merge Train Position

R7 merges first (position 1 in the train). R8 rebases on top of merged R7. R9 rebases on top of merged R8. See `MERGE_TRAIN_ORDER_v1_0.md` for the full rebase command sequence.

## Rollback Plan

All R7 changes are additive or refactors within existing components. Rollback strategy: `git revert <merge-commit-sha>` on main. No DB migrations to reverse. No flag to flip (R7 ships always-on per the §M.16 precedent — no flags gate the polished behaviour).

---
*R7 Master Plan v1.0 — authored 2026-05-20 as part of `chat-v2/governance-r7-r9-setup` branch.*
