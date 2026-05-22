---
canonical_id: R11B_B_S7
session_id: B-S7
title: Inline citation parity — extend NumberedCitation; retire CitationSidePanel + CitationCtx
phase: R11.B — Look-and-Feel
depends_on: [B-S6]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL + hook
client_side: yes
authored: 2026-05-22
---

# B-S7 — Inline Citation Parity

## Context

`NumberedCitation.tsx` already does inline `[N]` superscript + 350ms hover snippet (Y-S1) + confidence dot (Y-S2). Extend it for full Claude parity: web URL click-out, non-SIG citation kinds (`web`, `asset`, `chunk`), freshness badge inside the hover-preview popover. Retire only the side-panel surface (`CitationSidePanel` + `CitationCtx`).

## Files in Scope

### Modify

- `platform/src/components/chat/NumberedCitation.tsx` — add props: `sourceKind?: 'signal'|'asset'|'chunk'|'web'`, `sourceUrl?: string`, `freshness?: 'fresh'|'stale'|'unknown'|{age_days: number}`, `onActivate?: (n, signalId, url?) => void`. Web kind → click opens URL in new tab. Freshness shown in popover.
- `platform/src/components/chat/MarkdownContent.tsx` — pass new fields when rendering NumberedCitation.
- `platform/src/components/consume/ConsumeChatV2.tsx` — remove the CitationSidePanel mount + CitationCtx Provider wrapper. The freed horizontal space lets B-S3's 768px column center within.
- `platform/src/lib/config/feature_flags.ts` — register `MARSYS_FLAG_R11B_INLINE_CITATIONS` (default false, NEXT_PUBLIC) as a sub-flag of the umbrella flag, in case rollback granularity is needed.
- `.github/workflows/deploy.yml` — add build-arg.

### Delete (verify zero remaining imports)

- `platform/src/components/chat/CitationSidePanel.tsx`
- `platform/src/lib/citations/citation_ctx.tsx` (or equivalent path)
- Test files exclusively for CitationSidePanel.

## Files MUST NOT Touch

- Y-S1 hover-snippet dwell timing (350ms preserved)
- Y-S2 confidence dot color thresholds
- citation_data_part.ts extractor (preserved)
- citation_check.ts synthesis-side validator
- Sacred components
- Phase 4C files

## Acceptance Criteria

1. NumberedCitation extended with new props; existing props preserved (`onPin` renamed to `onActivate` with back-compat wrapper).
2. Web kind: clicking opens URL in new tab.
3. Freshness shown in popover (uses existing Y-S2 freshness badge component).
4. Y-S1 350ms dwell preserved.
5. Y-S2 confidence color thresholds preserved.
6. CitationSidePanel.tsx + CitationCtx file do NOT exist.
7. `grep -rn "CitationSidePanel\|CitationCtx" platform/src --include="*.ts*"` returns ZERO matches.
8. NumberedCitation.tsx still exists (NOT deleted).
9. Click-path: synthesis query → inline [N] markers → hover for 350ms shows snippet + freshness + (for web) URL → click activates source. No side panel mounts.
10. Parent-context test: 3 citations (signal, web with sourceUrl, signal with freshness 'stale') all render correctly inline; side panel NOT in DOM.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
test -f src/components/chat/NumberedCitation.tsx && echo "PASS: kept"
test ! -f src/components/chat/CitationSidePanel.tsx && echo "PASS: side panel deleted"
grep -rn "CitationSidePanel\|CitationCtx" src --include="*.ts*" | grep -v ".test." && echo "FAIL: stale refs" || echo "PASS"
grep -n "sourceKind\|sourceUrl\|onActivate" src/components/chat/NumberedCitation.tsx && echo "PASS: extended"
npx jest --testPathPattern="NumberedCitation|B-S7|inline-citation" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): extend NumberedCitation; retire CitationSidePanel (B-S7)

NumberedCitation extended with sourceKind/sourceUrl/freshness/onActivate.
DELETED: CitationSidePanel + CitationCtx. ConsumeChatV2 no longer mounts the
panel; freed space lets B-S3's 768px column center.

PRESERVED: NumberedCitation (extended only), Y-S1 350ms dwell, Y-S2 confidence
color thresholds, citation_data_part.ts extractor.

Per NATIVE_RULINGS §3 (full Claude citation pivot).
```

## Decision Log

*(Executor: paste before/after of 3-citation message; grep output proving CitationSidePanel + CitationCtx gone.)*
