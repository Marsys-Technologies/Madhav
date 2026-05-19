# R8 Sessions Log — Chat V2 Capabilities Round

## R8-S1 — Conversation Branches Persistence
- **Completed**: 2026-05-20
- **Commit**: ddcb350
- **Files touched**:
  - `platform/supabase/migrations/066_conversation_branches.sql` (new)
  - `platform/src/app/api/conversations/[id]/branches/route.ts` (new)
  - `platform/src/types/branches.ts` (new)
  - `platform/src/hooks/useBranches.ts` (modified — API hydration + fire-and-forget POST)
  - `platform/src/lib/config/feature_flags.ts` (modified — all 7 R8 flags added)
- **Migration**: 066_conversation_branches.sql (conversation_branches table, self-ref FK, index)
- **Acceptance criteria**: AC.1–AC.14 verified by inspection. tsc: 0 errors. Lint on new files: 0 issues.
- **Pre-existing test failures**: 21 (unchanged baseline)
- **Decisions**:
  - Project uses raw pg (no Prisma) — migration is raw SQL under supabase/migrations/
  - Migration number follows sequential scheme (066 = next after 065)
  - All R8 flags added in single commit to feature_flags.ts; all default false per brief
