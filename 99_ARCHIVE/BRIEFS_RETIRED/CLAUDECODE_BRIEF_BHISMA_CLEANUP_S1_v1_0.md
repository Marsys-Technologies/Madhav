---
title: "BHISMA Phase 1 Round 1 — W2 Residual Cleanup"
brief_id: BHISMA_CLEANUP_S1
version: 1.0
status: COMPLETE
created_date: 2026-05-04
session_id: BHISMA-CLEANUP-S1
executor: claude-sonnet-4-6
active_phase: "BHISMA Phase 1 — CI / Hardening"
isolation_tier: BHISMA_ONLY
blocked_by: none
must_complete_before: none
parallel_safe_with: BHISMA_CI_S1
---

# BHISMA-CLEANUP-S1 — W2 Residual Cleanup

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

Lever 2 closed 2026-05-04. Several debugging artifacts and scaffolding comments from Wave 2 development are now obsolete and should be removed:

1. `NIM_DEBUG_BODY` logger in `platform/src/lib/models/nvidia.ts` — explicitly marked "Remove once Lever 2 is unblocked." Lever 2 is unblocked.
2. 4 untracked NIM debugging scripts in `platform/scripts/` — one-off probes from the NIM investigation phase; should be excluded from the repository.
3. `CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md` has a modified status field (set to `COMPLETE` when S-C closed) that was never committed.

---

## §1 Pre-Work Audit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Confirm working tree state
git status --short

# Confirm the NIM_DEBUG_BODY block exists at the expected location
grep -n "NIM_DEBUG_BODY" platform/src/lib/models/nvidia.ts

# Confirm the 4 untracked scripts
ls platform/scripts/nim_catalog_check.mjs 2>/dev/null && echo "FOUND" || echo "NOT FOUND"
ls platform/scripts/nim_model_test.mjs 2>/dev/null && echo "FOUND" || echo "NOT FOUND"
ls platform/scripts/run_nim_catalog_check.command 2>/dev/null && echo "FOUND" || echo "NOT FOUND"
ls platform/scripts/run_nim_test.command 2>/dev/null && echo "FOUND" || echo "NOT FOUND"

# Check if .gitignore already has entries for these
grep -n "nim_catalog\|nim_model_test\|run_nim" .gitignore 2>/dev/null || echo "No existing entries"

# Sweep W2 TODO/FIXME in platform source
grep -rn "TODO.*W2\|FIXME.*W2\|NIM_DEBUG\|Remove once Lever" platform/src/ 2>/dev/null
```

---

## §2 Scope of Work

### Task 1 — Remove `NIM_DEBUG_BODY` logger from `nvidia.ts`

The block to remove is inside the `nimFetch` function. Locate and delete these lines (approximately lines 47–54 in `platform/src/lib/models/nvidia.ts`):

```typescript
  // NIM_DEBUG_BODY=1: log the first 3000 chars of the request body to stderr.
  // Used to diff AI SDK wire format against raw-fetch probes. Remove once
  // Lever 2 is unblocked.
  if (process.env.NIM_DEBUG_BODY && init?.body) {
    const body = init.body
    const snippet = typeof body === 'string' ? body.slice(0, 3000) : '(non-string body)'
    process.stderr.write(`[nim-debug] → ${snippet}\n`)
  }
```

The `nimFetch` function after removal should open directly with the `AbortSignal.timeout` line. Verify the function still compiles: `cd platform && npx tsc --noEmit 2>&1 | grep nvidia`.

### Task 2 — Suppress 4 untracked NIM debugging scripts via `.gitignore`

Add entries to the root `.gitignore` (not `platform/.gitignore`). Do NOT delete the files from disk — the native may still want them locally.

Append a clearly-labelled block to `.gitignore`:

```
# BHISMA Wave 2 — NIM debugging scripts (local probes, not committed)
platform/scripts/nim_catalog_check.mjs
platform/scripts/nim_model_test.mjs
platform/scripts/run_nim_catalog_check.command
platform/scripts/run_nim_test.command
```

Verify they disappear from `git status` after the gitignore update:
```bash
git status --short platform/scripts/nim_catalog_check.mjs
# Should output nothing (ignored)
```

### Task 3 — Commit `CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md` status change

This file's `status` field was set to `COMPLETE` when S-C closed but was never committed.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md
git commit -m "docs: mark BHISMA_SC brief as COMPLETE"
```

### Task 4 — Sweep W2 residual TODOs

Run the grep from §1 Task 4. For any TODO/FIXME bearing "W2" or "Remove once Lever" in `platform/src/`:

- If the item is clearly obsolete (Lever 2 closed, the condition is now met): remove the comment or inline note.
- If the item is ambiguous: leave it and note it in the session close (do NOT guess and delete).

---

## §3 File Scope

### may_touch
```
platform/src/lib/models/nvidia.ts    [EDIT — remove NIM_DEBUG_BODY block]
.gitignore                           [EDIT — add 4 ignored paths]
CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md  [COMMIT ONLY — no content change]
```

### must_not_touch
```
platform/tests/**
platform/scripts/nim_catalog_check.mjs    [do NOT delete — only ignore]
platform/scripts/nim_model_test.mjs       [do NOT delete — only ignore]
platform/scripts/run_nim_catalog_check.command  [do NOT delete — only ignore]
platform/scripts/run_nim_test.command     [do NOT delete — only ignore]
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
CLAUDE.md
.github/**
/Users/Dev/Vibe-Coding/Apps/Ustad/**
```

---

## §4 Acceptance Criteria

- [ ] `NIM_DEBUG_BODY` block is gone from `nvidia.ts` — `grep -n "NIM_DEBUG_BODY" platform/src/lib/models/nvidia.ts` returns no output
- [ ] `nvidia.ts` still compiles — `cd platform && npx tsc --noEmit 2>&1 | grep nvidia` returns no errors
- [ ] All 4 untracked NIM scripts are suppressed — `git status --short` shows none of them
- [ ] `CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md` committed — `git log --oneline -1 -- CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md` shows a recent commit
- [ ] No additional W2 residual TODO/FIXME items remain unresolved in `platform/src/` (or each ambiguous one is noted in session close)
- [ ] `git status` shows a clean working tree (only this session's changes, nothing unexpected)

---

## §5 Hard Constraints

1. **Do not delete the nim_* script files** — only add them to `.gitignore`. The native may still use them locally for investigation.
2. **Do not modify any other TypeScript source files** — only `nvidia.ts` is in scope.
3. **Do not touch any test files** — `platform/tests/**` is off-limits.
4. **Do not modify governance files** (`CLAUDE.md`, `00_ARCHITECTURE/**`).
5. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §6 How to Start

Open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_CLEANUP_S1_v1_0.md and execute it.
```
