---
canonical_id: CHAT_V2_MERGE_TRAIN_ORDER
version: 1.1
status: CURRENT
authored: 2026-05-20
amended: 2026-05-20
governing_plans:
  - 00_ARCHITECTURE/chat_v2_briefs/round7/R7_MASTER_PLAN_v1_0.md
  - 00_ARCHITECTURE/chat_v2_briefs/round8/R8_MASTER_PLAN_v1_0.md
  - 00_ARCHITECTURE/chat_v2_briefs/round9/R9_MASTER_PLAN_v1_0.md
  - 00_ARCHITECTURE/chat_v2_briefs/round10/R10_MASTER_PLAN_v1_0.md
---

# Chat V2 Merge Train Order — R7 → R8 → R9 → R10

## Rationale

Three parallel streams execute simultaneously across isolated worktrees. They share no source files during development. Merging order is determined by blast radius (smallest first) and dependency chains (R9-S2 needs R8-S3).

```
main ──── R7 merge ──── R8 merge ──── R9 merge ──── final state
             ↑               ↑               ↑
         Polish only    Capabilities    Elevation
         No migrations  DB migrations   Heavy schema
         ~7 sessions    ~8 sessions     ~4 sessions
```

## Position 1 — R7 (Polish)

**Branch:** `chat-v2/round7-polish`  
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavR7`  
**PR title:** `feat(chat-v2/r7): polish — citation fix + footnotes + enrichment + panel auto-open + continue + draft + a11y`

### Pre-PR rebase commands (from R7 worktree)
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR7
git fetch origin
git rebase origin/main
# Expect: no conflicts (R7 branch started from same main commit)
git push --force-with-lease origin chat-v2/round7-polish
```

### Gate before merge
```bash
cd platform && npx tsc --noEmit && npm test -- --passWithNoTests
```

### Merge command (from main repo)
```bash
git checkout main
git merge --no-ff chat-v2/round7-polish -m "feat(chat-v2/r7): R7 polish round merge"
git push origin main
```

---

## Position 2 — R8 (Capabilities)

**Branch:** `chat-v2/round8-capabilities`  
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavR8`  
**Prerequisite:** R7 merged to main  
**PR title:** `feat(chat-v2/r8): capabilities — branches + search + folders + tokens + slash + vision + export`

### Pre-PR rebase commands (from R8 worktree)
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR8
git fetch origin
git rebase origin/main
# Expected conflicts: NONE (R8 owns different files from R7)
# If conflicts appear in feature_flags.ts: take both flag sets (merge, don't replace)
git push --force-with-lease origin chat-v2/round8-capabilities
```

### Conflict resolution notes
- `platform/src/lib/feature_flags.ts`: if R7 added `MARSYS_FLAG_R7_*` entries, R8 rebase should append `MARSYS_FLAG_R8_*` entries — do NOT drop R7's additions.
- `platform/src/components/chat/Composer.tsx`: R7-S6 modified this file. R8-S5 also modifies it. On rebase, take R7's changes as base and apply R8-S5's changes on top.

### Gate before merge
```bash
cd platform && npx tsc --noEmit && npm test -- --passWithNoTests && npx prisma migrate status
```

### Merge command (from main repo, after R7 is merged)
```bash
git checkout main
git merge --no-ff chat-v2/round8-capabilities -m "feat(chat-v2/r8): R8 capabilities round merge"
git push origin main
```

---

## Position 3 — R9 (Elevation)

**Branch:** `chat-v2/round9-elevation`  
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavR9`  
**Prerequisite:** R7 AND R8 merged to main  
**PR title:** `feat(chat-v2/r9): elevation — projects + semantic search + personas + inline tool flow`

### Pre-PR rebase commands (from R9 worktree)
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR9
git fetch origin
git rebase origin/main
# Expected conflicts: search/route.ts (R8-S3 + R9-S2 both touch this file)
# Resolution: take R8-S3's trgm handler as the base; add R9-S2's ?semantic=true branch
# Do NOT replace the trgm handler — add the semantic branch alongside it
git push --force-with-lease origin chat-v2/round9-elevation
```

### Known conflict: `platform/src/app/api/conversations/search/route.ts`
R8-S3 creates this file. R9-S2 extends it with `?semantic=true`. Resolution strategy:
```typescript
// After rebase, the file should contain BOTH:
if (searchParams.get('semantic') === 'true') {
  // R9-S2: semantic vector search path
} else {
  // R8-S3: pg_trgm search path (existing handler — preserve verbatim)
}
```

### Pre-merge operator checks
- [ ] `pgvector` extension installed in production Postgres (required for R9-S2 migration)
- [ ] Embedding service endpoint configured (required for R9-S2 semantic search)

### Gate before merge
```bash
cd platform && npx tsc --noEmit && npm test -- --passWithNoTests && npx prisma migrate status
```

### Merge command (from main repo, after R7+R8 are merged)
```bash
git checkout main
git merge --no-ff chat-v2/round9-elevation -m "feat(chat-v2/r9): R9 elevation round merge"
git push origin main
```

---

## Flag Namespace Ownership

| Namespace | Owner | Flags |
|---|---|---|
| `MARSYS_FLAG_R7_*` | R7 branch | CITATION, PANEL, CONTINUE, DRAFT, A11Y |
| `MARSYS_FLAG_R8_*` | R8 branch | BRANCHES, SEARCH, FOLDERS, TOKENS, SLASH, VISION, EXPORT |
| `MARSYS_FLAG_R9_*` | R9 branch | PROJECTS, SEMANTIC_SEARCH, PERSONAS, TOOL_FLOW |

**Rule:** Each stream appends only its own namespace entries to `platform/src/lib/feature_flags.ts`. On rebase, never remove another stream's entries.

## deploy.yml — Append-Only Rule

`.github/workflows/deploy.yml` is append-only per stream. If a stream needs to add a new env var or step:
1. Add it in a clearly-labelled block (`# R7 additions`, `# R8 additions`, `# R9 additions`)
2. Never reorder or remove existing blocks
3. On rebase conflicts: take both blocks (earlier stream's additions + your stream's additions)

## Post-Train Cleanup

After all three rounds are merged:
1. Delete worktrees: `git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavR7 --force` (x3)
2. Delete remote branches: `git push origin --delete chat-v2/round7-polish chat-v2/round8-capabilities chat-v2/round9-elevation`
3. Update CLAUDE.md §E to mark all three workstreams COMPLETE
4. Author `CHAT_V2_R7_R9_CLOSE_v1_0.md` sealing artifact

---

## Position 4 — R10 (Polish + Capability)

**Branch:** `chat-v2/round10`  
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/Panchang` (existing Panchang worktree — NOT a new worktree)  
**Prerequisite:** R7 + R8 + R9 + R9-remediation (#103) ALL merged to main ✅ (confirmed 2026-05-20)  
**PR title:** `feat(chat-v2/r10): polish + capability — 21 sessions (scroll, tables, mermaid, citations, streaming)`  
**Execution:** Single sequential stream (no parallel sub-streams). Group P (X-S0..X-S11) then Group C (Y-S1..Y-S9).

### Phase 4C interaction caveat (⚠️ native action required)

The Panchang worktree is simultaneously home to `feature/phase-4c-panchang` branch work. R10 is on a separate branch (`chat-v2/round10`) so there is **no file-level conflict during development**. However, before R10's PR is merged:

1. Check whether any Phase 4C PRs targeting main are open: `gh pr list --base main | grep phase-4c`
2. If Phase 4C PR(s) are open: **merge Phase 4C first**, then rebase `chat-v2/round10` onto the updated main before merging R10.
3. File overlap: R10 touches `platform/src/` and `00_ARCHITECTURE/chat_v2_briefs/round10/`. Phase 4C touches `00_ARCHITECTURE/BRIEFS/` and `00_ARCHITECTURE/CONDUCTOR/`. **No overlap** — but verify before rebasing.

### Pre-PR rebase commands (from Panchang worktree)
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
git fetch origin
git rebase origin/main
# Expect: no conflicts (R10 adds new files under platform/src/ not touched by other branches)
# If feature_flags.ts conflicts: take all R10_* additions — do NOT drop prior flag entries
git push --force-with-lease origin chat-v2/round10
```

### Amendment 5 coverage gate (HARD — run before PR)
```bash
# From Panchang worktree root:
STEP1=$(grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10" platform/src --include="*.ts*" -o | awk -F: '{print $NF}' | sort -u)
STEP2=$(grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R10[XY]?_[A-Z_]+" .github/workflows/deploy.yml | sort -u)
echo "Source flags: $STEP1"
echo "deploy.yml flags: $STEP2"
# STEP1 must be a subset of STEP2. Any flag in STEP1 missing from STEP2 = HARD FAILURE.
# Fix: add missing flag to deploy.yml --build-arg before opening PR.
# Document result in STREAM_R10_COMPLETE.md.
```

### Gate before merge
```bash
cd platform && npx tsc --noEmit && npm test -- --passWithNoTests
```

### Merge command (from main repo, after Phase 4C PRs resolved)
```bash
git checkout main
git merge --no-ff chat-v2/round10 -m "feat(chat-v2/r10): R10 polish + capability round merge"
git push origin main
```

---

## Flag Namespace Ownership (updated)

| Namespace | Owner | Status |
|---|---|---|
| `MARSYS_FLAG_R7_*` | R7 branch | ✅ MERGED (PR #101) |
| `MARSYS_FLAG_R8_*` | R8 branch | ✅ MERGED (PR #102) |
| `MARSYS_FLAG_R9_*` | R9 branch | ✅ MERGED (PR #100 + #103) |
| `MARSYS_FLAG_R10_*` | R10 branch | 🔄 IN PROGRESS |
| `NEXT_PUBLIC_NIM_STACK_DEGRADED` | R10 X-S0 cleanup | Orphaned flag; added to deploy.yml via X-S0 |

---
*Merge Train Order v1.1 — amended 2026-05-20 to add R10 (Panchang worktree, single sequential stream). v1.0 authored 2026-05-20 for R7/R8/R9 train.*
