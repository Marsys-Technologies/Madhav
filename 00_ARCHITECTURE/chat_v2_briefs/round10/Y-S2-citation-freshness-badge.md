---
canonical_id: R10_Y_S2
version: 1.0
status: CURRENT
session_id: Y-S2
title: Citation freshness badge — confidence-colored dot on NumberedCitation
depends_on: [Y-S1]
blocked_on: []
flag: MARSYS_FLAG_R10_CITATION_FRESHNESS
flag_default: true
client_side: "yes — NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS"
authored: 2026-05-20
---

# Y-S2 — Citation Freshness Badge

## Context

MSR signals carry a `confidence` field that reflects signal stability/freshness. Surfacing this visually on inline citations gives users an immediate signal quality indicator without opening the side panel. A small confidence-colored dot (green/yellow/red based on confidence band) appears adjacent to each `NumberedCitation` superscript.

**Amendment 1 (HARD GATE):** `NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS` is a client-side flag. It MUST be added to `.github/workflows/deploy.yml` `--build-arg` block.

**Amendment 3:** FLAGGED — data-dependent; gated for rollout.

**Amendment 2:** Visible component (colored dot on NumberedCitation) → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/citation/NumberedCitation.tsx` — add confidence dot
- `platform/src/components/chat-v2/citation/CitationCtx.tsx` — ensure `citationRichMap` exposes `confidence` from MSR signal store (may already exist from Y-S1 context extension)
- `.github/workflows/deploy.yml` — add `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS=true`
- `platform/tests/` — integration test

## Files Must NOT Touch

- MSR signal store data structures (read-only from CitationCtx)
- Phase 4C files
- Server-side citation assembly (context read-only)

## Acceptance Criteria

1. **deploy.yml (Amendment 1 — HARD GATE):** `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS=true`. Session is NOT complete until present.
2. **Client-side classification (Amendment 1):** Executor confirms via grep: `grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS" platform/src --include="*.ts*"` — confirms usage in a `'use client'` component.
3. **click-path (Amendment 2):** User path: Chat V2 response with numbered citations → each `[^N]` superscript has a small colored dot (2–4px, or a CSS ring/halo): green for high confidence (≥0.8), yellow for medium (0.5–0.79), red for low (<0.5). Hovering the dot shows a tooltip "Confidence: high/medium/low". Document in commit body.
4. **Confidence bands:**
   - `confidence >= 0.8` → green (`text-green-500` or `bg-green-500`)
   - `0.5 <= confidence < 0.8` → yellow (`text-yellow-500`)
   - `confidence < 0.5` → red (`text-red-500`)
   - `confidence === undefined` → no dot (graceful absence)
5. **CitationCtx extension:** `citationRichMap` must expose `confidence: number | undefined` from the MSR signal data part. If `data-citation` events already carry this, extract it; if not, document what is missing as a blocked_on caveat.
6. **Flag guard:** When `NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS=false`, no dots are rendered.
7. **Accessibility:** Dot has `aria-label="Signal confidence: high/medium/low"` or is wrapped in a visually-hidden label.
8. **Parent-context integration test (Amendment 2):** At least one test mounts `NumberedCitation` within a real `CitationCtxProvider` with a mock citationRichMap containing confidence values and flag=true, and asserts: (a) green dot for confidence=0.9, (b) yellow dot for confidence=0.65, (c) red dot for confidence=0.3, (d) no dot when confidence=undefined. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Amendment 1 — HARD GATE
grep "NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS" .github/workflows/deploy.yml && echo "PASS: deploy.yml has flag" || echo "FAIL: HARD GATE"

grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS" platform/src --include="*.ts*" && echo "PASS" || echo "FAIL"

npx jest --testPathPattern="freshness|Freshness|citation.*confidence|confidence.*badge" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): citation confidence badge — colored dot on NumberedCitation

CitationCtx citationRichMap extended with confidence field. Green/yellow/
red dot on [^N] per MSR signal confidence band (>=0.8/0.5-0.8/<0.5).
Tooltip on hover. Guarded by MARSYS_FLAG_R10_CITATION_FRESHNESS=true
(NEXT_PUBLIC + deploy.yml build-arg per Amendment 1).

Click-path: citation [^1] with high confidence → green dot visible.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
