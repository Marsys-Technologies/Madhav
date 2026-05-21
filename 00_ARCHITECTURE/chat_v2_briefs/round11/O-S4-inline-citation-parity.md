---
canonical_id: R11_O_S4
version: 1.1
status: CURRENT
session_id: O-S4
title: Inline citation parity — full Claude pivot + retire CitationSidePanel + footnotes
depends_on: ["O-S3"]
blocked_on: []
flag: MARSYS_FLAG_R11_INLINE_CITATIONS
flag_default: false
client_side: "yes — NEXT_PUBLIC; new render path; deletes CitationSidePanel + CitationCtx + NumberedCitation"
authored: 2026-05-21
amended: 2026-05-21 — full Claude pivot per NATIVE_RULINGS §3; retire entire footnote + side-panel system
---

# O-S4 — Inline Citation Parity + Side-Panel Retirement

## Context

**Per `NATIVE_RULINGS_v1_0.md §3` — full Claude pivot.** All citations render as
inline-clickable superscript markers at the claim level (icon + hover-preview
popover + click-out to source). The existing footnote + side-panel system is
**retired entirely**:

- `CitationSidePanel` — deleted
- `CitationCtx` provider — deleted
- `NumberedCitation` (footnote-style `[^N]`) — deleted
- Cite-* CSS tokens (`--cite-signal`, `--cite-asset`, `--cite-chunk`, etc.) — deleted if unused after removal
- R7-S2 GFM footnote rendering path in `MarkdownContent` — deleted

The R10 Y-S2 freshness-badge work is preserved by attaching freshness data to
the new inline-citation hover-preview popover (badge appears on hover, not
in a side panel).

## Files in Scope

### Add
- `platform/src/components/chat/InlineCitation.tsx` (new) — props:
  `{ label: string, source: { title, url, cited_text, freshness?, kind: 'web' | 'signal' | 'asset' | 'chunk' } }`. Renders inline superscript marker with hover-preview popover (title, url, cited_text, freshness badge if present, kind icon) and click-out to source. Marker color uses `var(--brand-gold)` per `NATIVE_RULINGS §2`.

### Modify
- `platform/src/components/chat/MarkdownContent.tsx` — remove the GFM-footnote renderer; replace with the inline-citation renderer that consumes a normalized citation data-part stream and renders `<InlineCitation />` at the position the model marked.
- `platform/src/app/api/chat/consume/route.ts` — confirm citation data parts emitted (web_search_result_location + synthesis citations) carry enough payload for the InlineCitation popover (title, url, cited_text, freshness, kind).
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_INLINE_CITATIONS` (default false, NEXT_PUBLIC).
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11_INLINE_CITATIONS` build-arg (Amendment 1).
- `platform/src/app/globals.css` — remove unused `--cite-signal`, `--cite-asset`, `--cite-chunk`, `--cite-signal-bg`, `--cite-asset-bg`, `--cite-chunk-bg` after retirement (verify no other consumer first).

### Delete (verify zero remaining imports first)
- `platform/src/components/chat/CitationSidePanel.tsx`
- `platform/src/components/chat/NumberedCitation.tsx`
- `platform/src/lib/chat-v2/CitationCtx.tsx` (or equivalent path — locate via grep)
- Any test files exclusively for the deleted components

### Update consumers
- `platform/src/components/consume/ConsumeChatV2.tsx` — remove the right-side panel mount + the `CitationCtx.Provider` wrapper. Adjust layout (main pane re-expands to fill the freed space; the 768px message column from V-S3 centers within).

## Files Must NOT Touch

- `PerMessageDetailsDrawer`, `PanelMember` rendering (sacred per `NATIVE_RULINGS §5`)
- Cost Visibility surface
- Observatory cache metrics emit (O-S2 territory)
- Phase 4C files

## Acceptance Criteria

1. **Flag client-side + deploy.yml (Amendment 1):** `NEXT_PUBLIC_MARSYS_FLAG_R11_INLINE_CITATIONS` in both `feature_flags.ts` and `deploy.yml --build-arg`. Coverage check at R11-MERGE.
2. **InlineCitation renders for all citation types:** web_search citations AND synthesis (signal/asset/chunk) citations both render via `<InlineCitation />` with kind-icon differentiation in the popover.
3. **Freshness badge preserved:** Y-S2 freshness data appears in the hover-preview popover (not in a side panel). Test asserts a citation with `freshness: 'stale'` renders the existing freshness badge component inside the popover.
4. **Side-panel retirement complete:**
   - `CitationSidePanel.tsx` file does NOT exist.
   - `NumberedCitation.tsx` file does NOT exist.
   - `CitationCtx` is not imported anywhere in `platform/src/`.
   - `ConsumeChatV2.tsx` does not mount the panel or the provider.
   - `grep -rn "CitationSidePanel\|NumberedCitation\|CitationCtx" platform/src` returns ZERO matches.
5. **R7-S2 footnote path retired:** `MarkdownContent` no longer renders GFM `[^N]` footnotes (the renderer is removed). If the model accidentally emits `[^N]` syntax, the markdown processor renders it as literal text — acceptable degradation.
6. **Click-path (Amendment 2):** send a synthesis query → inline `[N]` marker appears at each citation point in the answer → hover reveals popover with title + cited_text + freshness badge + click-out link → click navigates to source. No side panel appears anywhere.
7. **Parent-context integration test (Amendment 2):** mount `ConsumeChatV2` with a seeded message containing 3 citations (one web, one signal with freshness, one asset), flag=true. Assert: 3 InlineCitation markers render in order, side panel is NOT in DOM, hover on the signal citation surfaces the freshness badge.
8. **Flag guard:** with flag=false, ConsumeChatV2 falls back to a stub that renders citations as plain text (since the old components are deleted). The user is not expected to use flag=false in production — this is a kill-switch in case the rollout has a critical issue. Document in Decision Log.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11

# Inline component exists
test -f platform/src/components/chat/InlineCitation.tsx && echo "PASS: InlineCitation exists"

# Old components deleted
test ! -f platform/src/components/chat/CitationSidePanel.tsx && echo "PASS: CitationSidePanel deleted"
test ! -f platform/src/components/chat/NumberedCitation.tsx && echo "PASS: NumberedCitation deleted"

# Zero remaining references
grep -rn "CitationSidePanel\|NumberedCitation\|CitationCtx" platform/src --include="*.ts*" && echo "FAIL: stale refs found" || echo "PASS: no stale refs"

# Flag in deploy.yml
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11_INLINE_CITATIONS" .github/workflows/deploy.yml && echo "PASS: deploy.yml"

# Tests
npx jest --testPathPattern="O-S4|InlineCitation|inline-citation" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): full Claude inline citations + retire side panel (O-S4)

InlineCitation renders all citation types (web + signal + asset + chunk) as
inline superscript markers with hover-preview popover. Freshness badge from
R10 Y-S2 surfaces inside the popover.

DELETED: CitationSidePanel, NumberedCitation, CitationCtx provider, GFM
footnote rendering in MarkdownContent. ConsumeChatV2 no longer wraps the
panel/provider. 768px message column centers in the freed space.

Guarded by MARSYS_FLAG_R11_INLINE_CITATIONS=false (NEXT_PUBLIC; deploy.yml
--build-arg added). Default false acts as a kill-switch; with the old
components deleted, flag=false degrades citations to plain text in fallback.

Per NATIVE_RULINGS §3.
```

## Decision Log

*(Executor: paste before/after of a sample 3-citation message; paste grep
output proving zero remaining refs to the deleted components; paste a
screenshot of the hover-preview popover with freshness badge.)*
