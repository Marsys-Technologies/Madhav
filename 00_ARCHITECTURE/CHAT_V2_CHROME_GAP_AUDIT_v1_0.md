---
artifact: CHAT_V2_CHROME_GAP_AUDIT_v1_0
canonical_id: CHAT_V2_CHROME_GAP_AUDIT
version: 1.0
status: DRAFT
authored: 2026-05-17
---

# Chat V2 Chrome Gap Audit

Scope: side-by-side comparison of `ConsumeChatV2.tsx` vs. `ConsumeChatLegacy.tsx` to explain why V2 production renders as a narrow, mostly-chromeless surface vs. the full-chrome legacy view, plus the composer cursor anomaly.

Evidence base: file paths cited inline. No file modifications during audit.

---

## §1 — Layout structure comparison

| Layer | Legacy (ConsumeChatLegacy) | V2 (ConsumeChatV2) |
|---|---|---|
| Page (`page.tsx`) | Identical shell — both routes wrap V2/legacy in the same `ConsumeOverlayPortal` via `consume/layout.tsx`. | Same. |
| Overlay container | `ConsumeOverlayPortal.tsx:25` → `<div className="fixed inset-0 z-50">` → `<ZoneRoot zone="ink" style={{height:'100%'}}>` (full viewport, gold-glow background). | Same. |
| Outer chat container | `ConsumeChatLegacy.tsx:507` → `<div className="consume-shell h-full flex flex-col">`. Then `ConsumeShell` adds a 48px header bar, full-width children area. | `ConsumeChatV2.tsx:1183` → `<div className="relative flex h-dvh bg-zinc-950 text-zinc-100">`. Hard-coded `bg-zinc-950` — **overrides the gold-glow background coming through the overlay**. |
| Side rail / sidebar | `ConsumeShell.tsx:108-143` — overlay portal slide-over (`fixed inset-y-0 left-0 z-[60] w-72`), only visible when toggled; main area is always full width. | `ConsumeChatV2.tsx:1200-1215` — **always-mounted, in-flow `w-56` aside** (or `w-10` collapsed strip) on `md+`. Steals 224px / 40px from chat column at every viewport. |
| Main column | `ConsumeShell.tsx:146-191` — single flex column; children consume the remaining viewport after the 48px header. | `ConsumeChatV2.tsx:1217` → `<div className="flex flex-col flex-1 overflow-hidden min-w-0">`; header is its own bar. |
| Header chrome | 48px header with sidebar toggle, back-to-dashboard, serif title + gold-uppercase meta, action slot (Share + Trace). `ConsumeShell.tsx:146-187`. | Thin header with mobile hamburger, hard-coded `V2` pill (violet), name, optional meta. No actions slot. `ConsumeChatV2.tsx:1218-1245`. |
| Chat column width | `mx-auto w-full max-w-4xl px-4` everywhere (≈ 896px). All surfaces (`StreamingAnswer`, `Composer`, `OutOfDomainBanner`, `CorrectionNotice`, `ContextUsageCue`, validator surface) use `max-w-4xl`. | `mx-auto max-w-3xl` (≈ 768px) for messages + composer + attachment strip. **128px narrower than legacy**, AND the chat column is further squeezed by the always-on `w-56` left rail → effective content width drops from 896px to ~544px on a 1280px monitor. |
| Composer width | `max-w-4xl px-4 pb-3 pt-1` on its own `<div>` inside `ConsumeShell`'s children (`Composer.tsx:138`). | `max-w-3xl` inside `flex items-end gap-3` (`ConsumeChatV2.tsx:914`). Sits across full width of the (already squeezed) main column. |
| Right-side panel | `ConsumeShell.tsx:196-205` Reports `Sheet` — opens on demand from `headerActions` button; does NOT consume layout width. | `CitationSidePanel.tsx:21-30` — `md:static md:w-64 md:shrink-0` sibling of `<V2Thread/>` (`ConsumeChatV2.tsx:1358-1365`). Returns `null` when no pinned citations, so no width loss at empty state — but the moment any citation is pinned, another 256px is stolen. |
| Bottom-of-page surfaces | `ScrollToBottomButton` (positioned via `--composer-h` CSS var, `Composer.tsx`-published in `ConsumeChatLegacy.tsx:204-213`). | None — `--composer-h` is never published, scroll-to-bottom in V2 is a fixed-position chevron only. |

Net effect on a 1280×800 desktop: legacy chat column ≈ 896px centered. V2 chat column ≈ 1280 − 224 (sidebar) − margins = ~1024px shell, with inner `max-w-3xl` clamp → ~768px column **shifted left** (because the sidebar pushes everything off centre).

---

## §2 — Chrome inventory (legacy features missing in V2)

| Legacy element | What it does | Component path | Status in V2 |
|---|---|---|---|
| Brand header (serif title + gold uppercase DOB/place) | `ConsumeShell.tsx:166-179` | `ConsumeShell.tsx` | **Missing** — replaced with `text-sm font-semibold text-zinc-100` (`ConsumeChatV2.tsx:1237`). No serif font, no brand-gold metadata. |
| `PanelLeft` sidebar toggle in header | `ConsumeShell.tsx:150-158` | `ConsumeShell.tsx` | **Missing** on desktop. Only a mobile hamburger exists (`ConsumeChatV2.tsx:1223-1233`). Desktop has only the inline collapse arrow inside the rail itself (`ConsumeChatV2.tsx:144-153`). |
| Back-to-dashboard chevron | `ConsumeShell.tsx:161-163` | `ConsumeShell.tsx` | **Missing**. User must use browser back. |
| Share button | `ConsumeChatLegacy.tsx:517` | `ShareButton` (`platform/src/components/chat/ShareButton.tsx`) | **Missing** entirely. |
| Trace button (super_admin) | `ConsumeChatLegacy.tsx:519-534` | `TraceDrawer` (`platform/src/components/consume/TraceDrawer.tsx`) | **Missing**. `TraceDrawer` exists but is not imported. |
| Stack/style picker ("Gemini Stack 2M ctx · Acharya depth") | `ConsumeChatLegacy.tsx:722-728` | `ModelStylePicker` (`platform/src/components/chat/ModelStylePicker.tsx`) | **Missing**. No way to switch stack or depth. |
| Life Events: On/Off toggle | `ConsumeChatLegacy.tsx:731-751` | inline button + `lelContextEnabled` state | **Missing**. V2 always sends with default LEL behavior; user has no control. |
| Tier picker (super_admin) | `ConsumeChatLegacy.tsx:755-757` | `TierPicker` (`platform/src/components/consume/TierPicker.tsx`) | **Missing**. |
| Panel-mode opt-in (`Columns3` icon, branded) | `ConsumeChatLegacy.tsx:759-781` (branded label, in toolbar row) | inline label | Present but **re-implemented as `PanelModeToggle`** at composer-options row (`ConsumeChatV2.tsx:994-996`). Different design language (violet pill not gold-faint outlined label). |
| Reports library / Reader (right panel) | `ConsumeChatLegacy.tsx:490-504` + `ReportLibrary`, `ReportReader` | n/a | **Missing**. `reports` prop is accepted by V2 (via shared `ConsumeChatProps`) but never read. |
| Empty state with chart-aware prompts | `ConsumeChatLegacy.tsx:558-565` | `EmptyState` (`platform/src/components/consume/EmptyState.tsx`) | **Missing**. V2 shows hard-coded "Ready · Chat V2 — assistant-ui" (`ConsumeChatV2.tsx:1067-1074`). |
| Composer keyboard hint ("↵ Send · ⇧ ↵ New line") | `Composer.tsx:210-212` | `Composer.tsx` | **Missing**. |
| Paperclip + file picker inside composer | `Composer.tsx:188-209` | inline in `Composer` | Present but **outside** the input bubble (sibling button, not chip-row inside) — different IA (`ConsumeChatV2.tsx:926-937`). |
| Composer brand styling (gold-rim, focus-ring shadow, drag-state highlight, rounded-3xl chip-row) | `Composer.tsx:144-148` | `Composer.tsx` | **Missing**. V2 uses generic `border-zinc-700 bg-zinc-900 rounded-xl` — zinc/indigo palette. |
| Conversation list with rename/delete | `ConsumeShell.tsx:130-141` → `ConversationSidebar` | `ConversationSidebar` (`platform/src/components/chat/ConversationSidebar.tsx`) | **Missing**. V2 has its own inlined `ConversationSidebar` component (`ConsumeChatV2.tsx:79-183`) — buttons only, no rename/delete affordances. |
| `ScrollToBottomButton` brand-styled | `ConsumeChatLegacy.tsx:650-654` (uses `--composer-h` CSS var) | `ScrollToBottomButton.tsx` | **Missing**. V2 uses inline `<button class="fixed bottom-24 right-6 bg-zinc-700">` (`ConsumeChatV2.tsx:1079-1090`). |
| `ShortcutsDialog` + `CommandPalette` (⌘K) | `ConsumeChatLegacy.tsx:806-807` + `useHotkeys` (`ConsumeChatLegacy.tsx:268-276`) | `ShortcutsDialog`, `CommandPalette` | **Missing**. |
| `LiveReasoningCard`, `CorrectionNotice`, `ContextUsageCue`, `OutOfDomainBanner`, `PostAnswerProvenance` | `ConsumeChatLegacy.tsx:586-640` | all in `platform/src/components/consume/` | **Missing**. V2 ignores the legacy SSE marker stream entirely. |
| `ValidatorFailureView` (legacy version) | `ConsumeChatLegacy.tsx:568-582` | `platform/src/components/consume/ValidatorFailureView.tsx` | Not imported — V2 uses the newer `ValidatorFailureBand`/`ValidatorFooterChip` from `components/chat/`. |
| `useChatPreferences` (per-chart stack + style persistence) | `ConsumeChatLegacy.tsx:169` | `useChatPreferences` hook | **Missing** — V2 has no per-chart preferences. |
| Error band with retry/dismiss for run failures | `ConsumeChatLegacy.tsx:657-703` | `classifyChatError` | **Missing**. |
| Conversation branches (alternate replies viewer) | `ConsumeChatLegacy.tsx:256, 706-718` | `useBranches` + return-to-latest banner | **Missing**. V2's `BranchPickerPrimitive` is present at message level but no "viewing archived" banner. |

---

## §3 — Built-but-not-rendered features

Reading `ConsumeChatV2.tsx:26-40` (the import block), every component listed is imported. I checked render-sites for each:

| Component | Import? | Render? | Trigger / condition |
|---|---|---|---|
| `StageStepper` | yes (`L38`) | yes (`L510-512`) | Only while `isStreaming && stageHistory.length > 0`. **Stages emit `done` only at synthesis-start** (`route.ts:854-862`) — stepper has a real lifetime ≈ tens of seconds during streaming, but cannot be seen post-stream because the gate evaporates. |
| `ToolCallCard` | yes (`L39`) | yes (`L515-521`) | Same `isStreaming` gate as stepper. Same brief visibility window. |
| `PanelModeToggle` | yes (`L40`) | yes (`L994-996`) | Below composer, in `mx-auto max-w-3xl flex items-center pt-1.5` row. Always visible. **Implemented**. |
| `PerMessageDetailsDrawer` | yes (`L30`) | yes (`L619-624`) | Triggered by per-message "ⓘ" button (`L588-599`). Renders **inside** `MessagePrimitive.Root` so `useMessage()` works. **Wired**. |
| `ValidatorFailureBand` | yes (`L35`) | yes (`L501-507`) | Gated on `citationGate?.status === 'fail'`. Conditional. |
| `ValidatorFooterChip` | yes (`L36`) | yes (`L533-539`) | Gated on `citationGate?.status === 'warn'`. Conditional. |
| `ReasoningProgress` | yes (`L33`) | yes (`L527`) | Renders for `Reasoning` parts. Auto-collapse >2k tokens per γ2. Wired via `MessagePrimitive.Parts.components.Reasoning`. |
| `PanelConfidenceRibbon` | yes (`L31`) | yes (`L491-498`) | `isPanel && panelMeta` — only when panel mode produced data-panel-meta part. |
| `PanelDissentTabs` | yes (`L32`) | yes (`L542-547`) | `isPanel && showDissent && panelMembers.length > 0`. Toggle is part of the ribbon. |
| `NumberedCitation` | yes (`L27`) | **NO** — only the count is computed (`L270-273`). Inline JSX citations are intentionally NOT rendered by `V2AssistantText` (comment at L271 says "Inline JSX citation rendering is handled by the data-citation parts path (O3 fix); here we only count."). The `MarkdownContent` path bypasses `renderWithCitations` entirely → **citation chips do not appear in the rendered answer body**. The drawer badge still shows a count; the pin/unpin onClick is unreachable from the message body. |
| `CitationSidePanel` | yes (`L28`) | yes (`L1360-1364`) | Only renders when `pinnedCitations.length > 0`. Since the message body never produces clickable chips, **the panel is unreachable** in practice. |
| `PredictionLogModal` | yes (`L34`) | yes (`L626-639`) | Super-admin-only, gated on `predictionCandidates.length > 0`. |
| File upload UI | yes (`AttachmentStrip`, `useAttachmentManager`) | yes (`L912, L926-937`) | Present in composer; multi-modal upload flow wired. |
| "View trace" link in drawer | imported via drawer | drawer body | Need to verify inside `PerMessageDetailsDrawer`. Drawer has `queryId` available via `useMessage().metadata.custom`. (Per file header, drawer renders meta rows incl. `queryId`.) |
| Cost / token rows in drawer | yes | yes | Drawer reads `data-cost` part from `metadata.unstable_data`. Wired. |

Critical: the **two stream-time surfaces** (`StageStepper`, `ToolCallCard`) only render while `isStreaming` is true. Once streaming completes, they vanish — there is no persisted "pipeline trace" anywhere on the message. Audit W1-W15 of the remediation campaign never measured "are stage badges visible during a streaming response", they only checked imports + tests.

And the **citation chip path** is dead (see `NumberedCitation` row): O3's "render via data-citation parts" intent was never implemented inside the markdown renderer, but the inline path was disabled. Net: no clickable citations in the answer body.

---

## §4 — Cursor / composer bug investigation

V2 composer composition (`ConsumeChatV2.tsx:890-1000`):

```
<div ref=containerRef onDrop onDragOver style={paddingBottom: env(safe-area-inset-bottom)}>
  <ComposerPrimitive.Root className="border-t border-zinc-800 bg-zinc-950 px-4 py-3">
    {interruptToast && ...}
    <AttachmentStrip ... />          // mx-auto max-w-3xl above input
    <div className="mx-auto max-w-3xl flex items-end gap-3">
      <input type=file sr-only ref=fileInputRef />
      <button h-11 w-11 ...>📎</button>     // paperclip — SIBLING of input
      <ComposerPrimitive.Input
        className="flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-base md:text-sm text-zinc-100 placeholder-zinc-500 ..."
        placeholder="Ask about the chart…"
        rows={3}                              // → minRows for TextareaAutosize
      />
      <div className="flex flex-col gap-2 pb-0.5">
        <Send/Cancel button>                  // SIBLING of input
      </div>
    </div>
    <div className="mx-auto max-w-3xl ..."><PanelModeToggle/></div>
  </ComposerPrimitive.Root>
</div>
```

Findings:

1. **`ComposerPrimitive.Input` is `react-textarea-autosize`, NOT a native textarea** (`@assistant-ui/react/src/primitives/composer/ComposerInput.tsx:392`). The `rows={3}` prop is interpreted as `minRows`. TextareaAutosize manages height by setting an inline `style.height`. On first paint, before the measurement effect runs, the textarea briefly renders at the browser-default rows height; once mounted, autosize sets `height` inline.

2. **No explicit `line-height` set** on the V2 input. Legacy uses `text-[15px] leading-[1.55]` (`Composer.tsx:176`). V2 uses `text-base md:text-sm` with NO leading override. At desktop (md+), `text-sm` ships with `leading-5` (20px line-height for 14px font) by default Tailwind — that part is fine. But the `text-base md:text-sm` switch creates **a font-size discrepancy at the responsive breakpoint** (16px on mobile, 14px on desktop) that interacts with `react-textarea-autosize`'s height measurement (which reads computed line-height from the live DOM). On the breakpoint transition, the textarea height re-measures and the cursor visually jumps. This matches "cursor appears in a weird location".

3. **Paperclip is OUTSIDE the focusable input.** It's a sibling button to the input inside a `flex items-end` row. This is the most common cause of "cursor appears next to the icon, not at text start" because the user perceives the paperclip + input as one composer surface and expects the cursor right after the paperclip. The cursor IS at position 0 inside the input, but the paperclip is a 44px gap (`h-11 w-11` + `gap-3`) to the LEFT of the input border. Compare to legacy: paperclip is INSIDE the same `rounded-3xl` container as the textarea (`Composer.tsx:144-243`), in a footer row BELOW the textarea. The cursor in legacy is unambiguously at the top-left of the input visually.

4. **`flex items-end` aligns children to the bottom** of the row. The textarea grows multiline as content is added (autosize, no maxRows set). The paperclip and send button stay at the bottom. When the textarea is empty, the cursor sits at the **top-left of the input** (because `px-4 py-3` is symmetric padding), but the visual focus ring + the paperclip+send buttons are at the bottom — looks misaligned. Combined with the breakpoint font-size flip, the cursor's vertical position is fragile.

5. **`--composer-h` CSS variable is never published** in V2 (legacy publishes via ResizeObserver at `ConsumeChatLegacy.tsx:204-213`). This does not directly affect the cursor — but several downstream components (`ScrollToBottomButton.tsx:22`) use `bottom: calc(var(--composer-h) + 12px)`. In V2, this variable is undefined, so any inherited brand component that references it will compute to invalid CSS.

6. **No `outline:none` is universally inherited.** V2's `focus:outline-none focus:ring-2 focus:ring-indigo-500/50` is fine. No risk here.

The dominant root cause of "weird cursor location" is **point 3** (paperclip-as-sibling-not-inside), aggravated by **point 4** (`items-end` alignment) and possibly **point 2** (responsive font-size flip). All three are layout decisions in `ConsumeChatV2.tsx:914-947`.

---

## §5 — Root-cause summary + fix surface

**1. Dominant root causes.**

(a) V2 was built as a **clean-room shell on top of assistant-ui primitives** with a hand-rolled visual design (zinc/indigo/violet on `bg-zinc-950`), completely ignoring the legacy "Modern Dark Pro reskin" (brand-gold + brand-charcoal tokens, serif title, gold focus ring, rounded-3xl composer with paperclip-inside-pill IA). The two surfaces don't share a single chrome component — not header, not composer, not sidebar, not empty state.

(b) V2 wires an **always-mounted in-flow sidebar** (`w-56` / `w-10`) instead of legacy's portal-overlay sidebar, which steals 224 / 40px of horizontal width at every viewport. Combined with `max-w-3xl` (vs legacy's `max-w-4xl`), the chat column is 128px narrower than legacy AND visually shifted left, producing the "narrow column on the left" complaint.

(c) V2's `bg-zinc-950` hard-coded background **clobbers the gold-glow ConsumeOverlayPortal background**, so the page also looks visually wrong (flat zinc instead of warm bottom-up gradient).

**2. Why this escaped W1-W15 + audit.**

W1-W15 was a **functional walkthrough** (does this button do this thing) plus a Lighthouse run plus an a11y operator pass. None of the 15 walks asked: "does V2 visually match legacy at the same viewport on the same chart" or "list every legacy affordance and verify presence in V2". The audit findings O1-O10 were about correctness-of-emitted-data and validator-band behavior, not chrome inventory. The plugin's `cowork-plugin-customizer` skill exists for parity work but was not invoked. There is also **no Playwright test that loads both ConsumeChat surfaces side-by-side and screenshot-diffs**.

**3. Minimum work surface to reach visual parity.**

| File | Scope | Notes |
|---|---|---|
| `platform/src/components/consume/ConsumeChatV2.tsx` | **Large** (~250 lines) | Replace inlined `ConversationSidebar`, header, composer with shared components. Drop `bg-zinc-950`, switch palette to brand-gold/brand-charcoal tokens. Move `max-w-3xl` → `max-w-4xl`. Convert sidebar to portal-overlay (use `ConsumeShell` pattern). |
| `platform/src/components/consume/ConsumeShell.tsx` | **Small** (refactor only) | Make `ConsumeShell` accept an `assistantUiThread` child so V2 can mount inside the same shell as legacy. Currently `ConsumeShell` assumes children render their own `<div ref={scrollRef}>`. |
| `platform/src/components/chat/Composer.tsx` | **Small** | Extract a `ComposerShell` (the brand-gold pill, paperclip-inside, focus ring, footer row) that wraps either a native `<textarea>` (legacy) or `<ComposerPrimitive.Input>` (V2). |
| `platform/src/components/chat-v2/StageStepper.tsx`, `ToolCallCard.tsx` | **None for chrome**; small for persistence | Render badges as a collapsed post-stream summary, not just during `isStreaming`. |
| `platform/src/components/consume/EmptyState.tsx` | **None** | Reuse in V2 — already imports cleanly. |
| `platform/src/components/consume/ModelStylePicker.tsx`, `TierPicker.tsx`, `LiveReasoningCard.tsx`, `OutOfDomainBanner.tsx`, etc. | **None** | Drop into V2's toolbar row + scroll area; no internal change. |
| `platform/src/components/chat/CitationSidePanel.tsx` and V2's `V2AssistantText` | **Small but pointed** | Re-enable inline citation chip rendering inside `MarkdownContent` (currently disabled per L271 comment), OR thread the data-citation parts path through `MarkdownContent` so chips appear in the text body. Pick one; right now neither path renders. |

Rough estimate: 1–2 sessions to chrome-parity if `ConsumeShell` + `ComposerShell` are made reusable. 3 sessions if the team decides to build V2 chrome bottom-up without sharing components.

**4. Architectural decision required.**

The legacy chrome is **refactorable** into shared components — `ConsumeShell`, `Composer`, `EmptyState`, `ModelStylePicker`, `LiveReasoningCard`, etc. are all currently coupled to `ConsumeChatLegacy` only by the parent's state-management glue (refs, `useChatSession`, `useFeedback`, `useBranches`). The runtime layer in V2 is fundamentally different (assistant-ui `AssistantRuntimeProvider` vs. legacy `useChatSession`), so the SHELL can be shared but the message-rendering interior cannot. Decision needed: do we (a) refactor `ConsumeShell` to host either runtime, or (b) duplicate the chrome inside V2. Option (a) is the right answer for long-term maintenance; option (b) is faster but doubles the surface area for every future chrome tweak.

---

*End of CHAT_V2_CHROME_GAP_AUDIT v1.0.*
