# FLAG_GAP_REMEDIATION_LOG.md

**Purpose:** Track NEXT_PUBLIC_* build-arg gap findings and fixes for Chat V2 R7/R8/R9.

**Background:** NEXT_PUBLIC_* flags are baked into the client bundle at Docker build time via `--build-arg`.
If a flag is consumed in source but missing from deploy.yml `--build-arg`, it evaluates as `undefined`/`false`
in the production bundle regardless of any Cloud Run runtime env-var setting.

**Date:** 2026-05-20
**Initiated by:** Autonomous audit session following S177 finding (R9_SEMANTIC_SEARCH missing from deploy.yml)

---

## Phase 0 — Orientation

- Working directory: `/Users/Dev/Vibe-Coding/Apps/Madhav` ✓
- `git fetch --all --prune` complete ✓
- PR #103 state: OPEN, branch: `chat-v2/r9-integration-remediation` ✓

---

## Phase 1 — R9_SEMANTIC_SEARCH build-arg addition (PR #103 amend)

**Status: COMPLETE**

- Commit: `df61b1e` — `fix(r9-s2): add missing NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH build-arg`
- Branch: `chat-v2/r9-integration-remediation` (pushed; PR #103 auto-updated)
- PR #103 comment posted: https://github.com/amonty84/Madhav/pull/103#issuecomment-4493673135

**Final state of R9 build-args in deploy.yml (on PR branch):**
```
NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS=true        # 9882731 (S1 - Projects)
NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS=true        # 9882731 (S3 - Persona picker)
NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW=true       # 9882731 (S4 - Inline tool flow)
NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH=true # df61b1e (S2 - Semantic search toggle)
```
All four consistent at `=true`. ✓

---

## Phase 2 — R7/R8 NEXT_PUBLIC flag audit

**Status: CLEAN — no R7/R8 NEXT_PUBLIC_MARSYS_FLAG_R* build-arg gaps**

**Source-side inventory** (`grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R[78]" platform/src`):
- Result: **EMPTY** — no R7 or R8 `NEXT_PUBLIC_MARSYS_FLAG_R*` flags exist anywhere in `platform/src`.

**Explanation:**
- R7 shipped always-on per §M.16 precedent (CLAUDE.md §E: "R7 ships always-on (no MARSYS_FLAG_R7_*)").
- R8 flags are server-side env vars (`MARSYS_FLAG_R8_*`) set in Cloud Run at runtime — they are NOT
  NEXT_PUBLIC_ baked flags and are correctly absent from the build-args block.

**Full NEXT_PUBLIC_MARSYS flag inventory in source (all rounds):**
```
platform/src/components/chat/InlineToolFlow.tsx:7          NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW
platform/src/components/chat/ModelStylePicker.tsx:73       NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS
platform/src/components/consume/ConsumeChatV2.tsx:1609     NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS
platform/src/components/consume/ConversationSidebarV2.tsx:268  NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH
```
Only R9 flags. All four now covered in PR #103.

**Out-of-scope finding (not actioned — for native review):**
`NEXT_PUBLIC_NIM_STACK_DEGRADED` is consumed at `platform/src/components/chat/ModelStylePicker.tsx:51`
but is absent from deploy.yml build-args. This flag controls NIM model stack degradation display.
If it evaluates as `false` in prod that means the NIM degradation banner never shows (safe default —
no banner is the non-error state). Not a correctness risk but worth a deliberate decision.

---

## Phase 3 — R7/R8 gap fix PR

**Status: SKIPPED — Phase 2 was clean (no R7/R8 NEXT_PUBLIC_MARSYS_FLAG_R* gaps found)**

---

## Phase 4 — Seal

**Status: COMPLETE**

**Summary:**
- Phase 1: Commit `df61b1e` added `NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH=true` to PR #103.
  All four R9 client-side flags now fully wired. PR #103 commented and updated.
- Phase 2: R7/R8 source has zero NEXT_PUBLIC_MARSYS_FLAG_R* flags. R7 always-on; R8 server-side only.
  No build-arg gaps exist for R7 or R8. Phase 3 skipped.
- Out-of-scope: `NEXT_PUBLIC_NIM_STACK_DEGRADED` missing from build-args — safe default (false = no banner),
  noted for native awareness.

**This log committed to main:** see commit following this file creation.
