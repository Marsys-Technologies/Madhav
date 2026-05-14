---
canonical_id: CO5_VISUAL_AUDIT
version: 1.0
status: CURRENT
authored_at: 2026-05-14
authored_by: AIOPS_CO_5
scope: platform/src/components/consume/** + chat/** + shared/**
---

# CO.5 Visual Design Audit

AIOps Phase 3 — visual polish pass for the Consume UI.

---

## §1 — Typography Scale

**Audit method**: `grep -rn "text-\[" + text-* class enumeration across consume/, chat/`

**Sizes found** (across consume/ + chat/):

| Class | px equiv | Usage |
|---|---|---|
| `text-[10px]` | 10px | Metadata tokens, monospace details |
| `text-[11px]` | 11px | Capsule labels, pill text, tool names |
| `text-xs` | 12px | Hints, secondary labels |
| `text-sm` | 14px | Primary body, composer |
| `text-base` | 16px | Standard paragraph |
| `text-lg` | 18px | Message text |

**Count**: 6 distinct sizes. ✓ Within target (≤ 6).

**Font weights found**: `font-normal` (default), `font-medium`, `font-semibold`, `font-bold` (HeaderTitle only). The 4th weight (`font-bold`) appears only in TraceDrawer SheetTitle — acceptable exception for debug panel heading.

**Decision**: No consolidation changes needed. Scale is clean.

---

## §2 — Spacing Rhythm (4/8 px grid)

**Audit method**: `grep -rn "p-\[" arbitrary spacing values`

**Arbitrary values found and disposition**:

| Location | Value | Grid-aligned? | Action |
|---|---|---|---|
| ConsumeChat.tsx | `w-[65vw]` | N/A (viewport-relative) | Retain — layout constraint |
| ConsumeChat.tsx | `min-w-[700px]` | N/A (min-width) | Retain — layout constraint |
| ConversationSidebar.tsx | `w-14` (56px) | ✓ 8-grid | OK |
| ConversationSidebar.tsx | `w-64` (256px) | ✓ 8-grid | OK |
| MetadataBadge, lifecycle/* | `px-2.5` (10px) | ✓ | OK |
| MetadataBadge | `py-0.5` (2px) | ✓ | OK |

**Conclusion**: No off-grid spacing values in core consume/ components. ✓

---

## §3 — Color Discipline

**Hardcoded values found and disposition**:

| File | Value | Token replacement | Status |
|---|---|---|---|
| ConsumeChat.tsx | `oklch(0.11_0.010_70)` | `var(--brand-charcoal)` | ✅ Fixed in CO.5 |
| ConsumeChat.tsx | `#fce29a` | `var(--brand-gold-cream)` | ✅ Fixed in CO.5 |
| TraceDrawer.tsx | `#211c0a` | `var(--brand-charcoal)` | ✅ Fixed in CO.5 |
| ConversationSidebar.tsx | `oklch(0.5_0.18_25)/40` | `destructive/40` | ✅ Fixed in CO.5 |
| SharedConsumeError.tsx | `rgba(0,0,0,0.6)` | No exact token equivalent | ⚠️ Flagged for native review |
| ValidatorFailureView.tsx | `rgba(0,0,0,0.6)` | No exact token equivalent | ⚠️ Flagged for native review |

**CSS variable references** (not hardcoded, already use token system):
- `rgba(var(--brand-gold-rgb), N)` — token-based, no change needed
- `var(--brand-charcoal)/N` — token-based, no change needed
- `var(--status-warn-bg)`, `var(--status-warn)` — token-based, no change needed

**Flagged for native review**:
1. `shadow-[0_30px_80px_-30px_rgba(0,0,0,0.6)]` in SharedConsumeError.tsx and ValidatorFailureView.tsx: This is a drop-shadow value with no direct token equivalent. The shadow uses pure black (no brand color). Native to decide whether to create a `--shadow-deep` token or accept the inline value.

**No new colors introduced**. ✓

---

## §4 — Motion Language

**Target tiers**:
- 150ms — micro-interactions (hover, focus, toggle)
- 250ms — standard transitions (sidebar expand, panel open)
- 400ms — entry/exit (message bubble appear, modal open)

**Audit findings**:

| Component | Duration | Tier | Status |
|---|---|---|---|
| ConversationSidebar width expand | `duration-[250ms]` | Standard ✓ | Fixed in CO.5 |
| ChatShell hover strip | `duration-200` | Micro ≈ ✓ | Minor variance, acceptable |
| TierPicker button | `transition-colors` (unset duration → default 150ms) | Micro ✓ | OK |
| MetadataBadge | `transition-colors` | Micro ✓ | OK |
| PostAnswerProvenance | `transition-colors` | Micro ✓ | OK |

**Easing**: All transitions use `ease-out` or Tailwind default (`ease-in-out`). ✓
No spring physics. ✓

---

## §5 — Component Library Audit

**Button patterns found across consume/**:

| Pattern | Files | Verdict |
|---|---|---|
| Ghost action button (`text-muted hover:text-foreground`) | ConversationSidebar, ChatShell header | Keep — consistent pattern |
| Brand pill button (`bg-brand-charcoal border-brand-gold-hairline`) | ConversationSidebar "New conversation", Composer | Keep — primary CTA |
| Inline text button (`text-[11px] font-medium border px-2 py-0.5`) | TraceButton, PanelOptIn, TierPicker buttons | Keep — secondary toolbar actions |
| Destructive mini button | ConsumeChat error dismiss | Keep — error-state only |

**No duplicate button patterns that need consolidation.** The 3-tier hierarchy (primary CTA → toolbar action → ghost) is clean.

**Badge/pill patterns**:

| Pattern | Files |
|---|---|
| Token pill (`rounded-full border/50 bg-muted/30 px-2.5 py-0.5 text-[11px]`) | MetadataBadge, PostAnswerProvenance |
| Status pill (`text-muted-foreground/60 text-[11px]`) | StatusPip, ToolCallChronology |

These two patterns are intentionally distinct (data-display vs. live-status). ✓

---

## §6 — Screenshots

**Status**: Deferred. Screenshots require a running browser instance at `/consume` with live data. This environment (CLI/worktree) does not have a running Next.js dev server or browser automation. Screenshots to be captured manually during QA review.

**Reference frames for human reviewer**:
1. `/consume` empty state — verify EmptyState renders cleanly with no hardcoded colors
2. Mid-stream with Gemini 2.5 Pro — verify ReasoningSlot + StatusPip visible
3. Completed message — verify MetadataBadge shows model + cost + latency
4. Sidebar collapsed (`w-14`) + hover-expanded (`w-64`) — verify transition
5. MetadataBadge click-to-expand — verify token breakdown appears

---

*End of CO5_VISUAL_AUDIT.md v1.0*
