---
canonical_id: CHAT_V2_F3_FORENSIC
version: 1.0
status: DRAFT
authored: 2026-05-18
author: Claude (Cowork forensic subagent)
governing_plan: 00_ARCHITECTURE/CHAT_V2_ROUND_5_PLAN_v1_0.md v1.0 (Phase F.3 walkthrough)
predecessor_audits:
  - 00_ARCHITECTURE/CHAT_V2_CAPABILITY_REACHABILITY_AUDIT_v1_0.md
  - 00_ARCHITECTURE/CHAT_V2_LAYOUT_DIAGNOSTIC_v1_0.md
  - 00_ARCHITECTURE/CHAT_V2_CHROME_GAP_AUDIT_v1_0.md
workstream: Chat V2 Round 5 → Round 6 fix-wave
output_type: forensic
purpose: Root-cause every F.3 walkthrough finding with file:line precision; surface additional orphans; propose Round 6 PR list and Playwright smoke automation.
---

# CHAT V2 F.3 WALKTHROUGH — FORENSIC v1.0

Master file under investigation: `platform/src/components/consume/ConsumeChatV2.tsx` (1699 lines). All line numbers below are against the version checked into `main` at the time of this forensic.

## §1 — Layout root causes (L1–L4)

### L1 — Chat content visually offset from viewport center

**Where**: `ConsumeChatV2.tsx:1443-1467` (sidebar overlay wrapper + chat-column `md:ml-10|md:ml-56`) and `ConsumeChatV2.tsx:465` (`max-w-4xl mx-auto` on every V2Message), `ConsumeChatV2.tsx:798, 960, 1040, 1200` (same on AttachmentStrip, composer pill, options row, bottom bar), and `MarkdownContent.tsx:108` (additional `max-w-[68ch] mx-auto` inside the message body).

**Root cause**: The sidebar is rendered as a `fixed inset-y-0 left-0 z-40` overlay (lines 1444–1448), *but* the chat-column is also shifted right by `md:ml-10` (collapsed) or `md:ml-56` (expanded) (line 1466). Inside that already-offset column, all content blocks use `mx-auto max-w-4xl`. The composition centers content within `[ml, viewport_w]`, which means visual center is offset right of the true viewport center by `ml/2` (20 px collapsed, 112 px expanded). With sidebar collapsed the offset is small and the eye reads it as *off-center* rather than centered, especially compared to the symmetric legacy layout. With sidebar expanded the offset is large enough to look distinctly left-skewed *of the chat-column-internal center*, because the messages then visually lean toward the right edge of the visible area.

The second compounding factor is `MarkdownContent.tsx:108` which adds its OWN `max-w-[68ch] mx-auto` *inside* the already-centered V2Message. Two nested `mx-auto` clamps mean the prose is centered inside a 1024 px column that is itself centered inside an offset chat-column. The asymmetric offsets at each layer make the visual centerline drift unpredictably with viewport width.

**Minimum fix**: Make the sidebar a true overlay with `pointer-events-none` whitespace strip on collapsed and `pointer-events-auto` slide-over on expanded — and **drop `md:ml-10|md:ml-56` from the chat-column wrapper entirely**. Chat content then centers in the full viewport (`mx-auto max-w-4xl` on a `w-full` column). When expanded, the sidebar overlays the leftmost ~14rem of content; users dismiss to read. This matches Gemini/Claude.ai pattern. Combined with removing the redundant `mx-auto` from `MarkdownContent.tsx:108` (let V2Message own centering), the layout collapses to a single source of truth.

### L2 — Two sidebar toggle buttons render simultaneously

**Where**:
- Toggle #1: `ConsumeChatV2.tsx:1484-1492` — `hidden md:flex` header "Toggle conversations" button.
- Toggle #2: `ConversationSidebarV2.tsx:238-261` — "Collapse" `<` button inside the expanded sidebar header.
- (Plus the "+" new-conversation button at `ConversationSidebarV2.tsx:215-237` — accounts for the "three buttons" the operator described.)

**Root cause**: When `ConversationSidebarV2` was adopted (Phase C.2), its embedded collapse affordance (a vestige of when the sidebar was inlined and self-contained) was not removed. The header toggle (line 1484) is the *new* canonical control; the in-sidebar collapse is the *old* one. Both call the same `onToggle` handler. Duplicate UI affordances violate single-source-of-truth.

**Minimum fix**: Delete the in-sidebar "Collapse" button (`ConversationSidebarV2.tsx:238-261`). Keep header toggle as the only collapse/expand control. The "+" new-conversation button stays — it's a distinct affordance, not a duplicate.

### L3 — Two send/stop buttons during streaming

**Where**: `ConsumeChatV2.tsx:998-1033`. The `{isRunning ? (...two buttons...) : (...single send...)}` ternary renders:
- White `Square` stop button (`ComposerPrimitive.Cancel`, line 1000-1010) — cancels current run only.
- Golden `ArrowUp` button (line 1011-1020) — cancels current run *and* re-submits as a new query.

**Root cause**: Intentional code from β3 — designed as "stop OR cancel-and-send-new query" UX. But the two buttons are visually indistinguishable from "stop" + "send" of two different states, leading users to believe one is a duplicate. The intent is unclear without copy or affordance differentiation.

**Minimum fix**: Single button during streaming. Default to white stop button only; reveal the "cancel + resend" affordance via long-press, right-click, or a hover tooltip explaining the interrupt-send model. Alternatively keep two buttons but apply distinct iconography + a separator + a per-button tooltip so the two intents are unambiguous.

### L4 — Sidebar bottom logo "broken"

**Where**: `ConversationSidebarV2.tsx` (full file scanned). **There is no logo render site in this file at all.** Neither the collapsed strip (lines 173-200) nor the expanded sidebar (lines 204-291) include a `<Logo />` import or render.

**Root cause**: The operator's expectation is grounded in legacy `ChatShell.tsx` / `ConversationSidebar.tsx`, which render a brand `Logo` at sidebar bottom. `ConversationSidebarV2` never carried this over. This is a *missing* component, not a *broken* one. The visual artifact the operator perceives as "broken" is empty space at the sidebar bottom.

**Minimum fix**: Import `Logo` from `@/components/brand/Logo` and render at the bottom of the expanded sidebar (above the conversation list scroll terminus, inside a `mt-auto` flex item). Skip in collapsed mode.

## §2 — Behavior root causes (B1–B6)

### B1 — Stage stepper not visible during streaming

**Where**: V2Message reads `const dataParts = (message.metadata?.unstable_data ?? []) as ReadonlyArray<unknown>` at `ConsumeChatV2.tsx:353`, then filters for `type === 'data-stage'` at line 385. StageStepper renders only when `isStreaming && stageHistory.length > 0` (line 543).

**Root cause**: The route emits stage events via `writer.write({ type: 'data-stage', data: ... })` (`route.ts:872, 873, 880, 889`). With `@assistant-ui/react-ai-sdk`, these data writes land in `message.content` as `DataMessagePart { type: 'data', name: 'stage', data: {...} }` — **NOT** in `message.metadata.unstable_data`. The V2Message's data-correction path *already* knows this and reads from BOTH sources (lines 422-440 — checks `message.content` with `name === 'correction'` AND `dataParts`/`metadata.unstable_data` with `type === 'data-correction'`). The V2AssistantText citation path (lines 204-222) also reads from `message.content` with `name === 'citation'`. The stage parser DOES NOT — it only checks `metadata.unstable_data`. Result: `stageHistory.length === 0`, StageStepper bails out via `if (stages.length === 0) return null` (`StageStepper.tsx:23`).

The same bug applies to ToolCallCard rendering (line 549–554), prediction candidates (line 410-419), citation_gate (line 367-374), panel data (line 261-285). All read only from `metadata.unstable_data`. None are reaching production.

**Minimum fix**: Add a unified `useDataParts(message)` hook that merges `message.metadata?.unstable_data` and `message.content` filtered to `type==='data'`, normalizing each entry to a single `{ type: 'data-stage', data: ... }` shape. Replace every direct `dataParts.find(...)` and `dataParts.filter(...)` with the merged source. Single source of truth for live + post-stream data parts.

**Bonus root cause**: Even if the data parts reached V2Message, the route never emits `stagePart('synthesis', 'done')` — only `'running'` at `route.ts:889`. The synthesis pip would stay pulsing indefinitely. Add a `writer.write({ type: 'data-stage', data: stagePart('synthesis', 'done', synthesisMs) })` after the `result.toUIMessageStream` merge finishes (or in onFinish).

### B2/B3 — Raw `SIG.MSR.NNN` left in response text; chips render in footer instead of inline

**Where**: `V2AssistantText` at `ConsumeChatV2.tsx:196-256`. Line 232 calls `renderWithCitations(text, enrichedOnPin)` which DOES produce inline `NumberedCitation` elements interleaved with text fragments — but then line 233 throws away the text fragments via `.filter((p): p is React.ReactElement => typeof p !== 'string')`. Only the chip elements survive. The raw `text` (with `SIG.MSR.NNN` still present) is handed to `<MarkdownContent>{text}</MarkdownContent>` at line 247. Chips re-render in a separate footer `<div>` at lines 249-253.

**Root cause**: `MarkdownContent` takes a `string` child only (`MarkdownContent.tsx:11-15`). Inserting React elements inline would require either (a) substituting `SIG.MSR.NNN` → `[N]` text markers before markdown parsing, then rehyping `[N]` into React via a remark/rehype plugin, OR (b) using a different rendering primitive that accepts mixed children. The current code chose neither — it punted to a footer chip list.

The synthesis prompt emits `→ SIG.MSR.NNN` markers per the audit (route's onFinish parser confirms this format). For the rich-inline rendering to work, the simpler path is **option (a)**: the synthesis prompt instructs the model to emit `[^N]` Markdown footnote markers directly, with the server-side citation builder producing a footnote definition list at end-of-message. `streamdown`/remark-gfm already supports footnotes. The chips then render at the `[^N]` site naturally.

**Minimum fix path (recommended)**: Update the synthesis prompt (`lib/synthesis/prompts/synthesis_prompt_v2.ts`) to emit `[^1]`, `[^2]` … `[^N]` instead of `→ SIG.MSR.NNN`. Append a footnote definition block at end-of-stream. Add a custom `footnoteReference` component to `MarkdownContent.tsx:23` that renders our `NumberedCitation`. Drop the chip footer from V2AssistantText. Remove the `renderWithCitations` text-stripping logic.

**Minimum fix path (interim, no prompt change)**: Inside `V2AssistantText`, run a regex replace on `text` substituting `SIG.MSR.NNN` → `[^N]` (or some sentinel) BEFORE handing to MarkdownContent, then use a custom remark plugin to rewrite the sentinel into a React element. More moving parts; reserve for if prompt change is risky.

### B4/B5 — Click citation chip → window opens with name only, no description

**Where**: `NumberedCitation.tsx:30` `onClick={() => onPin?.(n, signalId)}`. Pinned citations flow into `CitationSidePanel.tsx` (rendered at `ConsumeChatV2.tsx:1683-1687`). The panel renders `c.signal_id` (always present) and `c.snippet && (<span>{c.snippet}</span>)` (line 52-54 of CitationSidePanel) — the snippet conditional hides if empty.

**Root cause — *not* what C.3 thought it was**. C.3 assumed the route was emitting rich citation parts with snippets and V2 wasn't consuming them. False. Look at `extractCitations` in `lib/citations/citation_data_part.ts:27-44`:

```
result.push(citationPart({
  index: result.length + 1,
  signal_id: signalId,
  layer: 'L2.5',
  snippet: '',   // ← ALWAYS empty
}))
```

The route at `route.ts:1141-1161` calls `extractCitations(lastAssistantText)` and forwards the *empty* snippets into `writer.write({ type: 'data-citation', ... })`. The V2AssistantText `citationRichMap` (lines 204-222) builds the map correctly from `message.content`, but every entry has `snippet === ''` and `layer === 'L2.5'` hardcoded. `enrichedOnPin` receives the empty values, `handlePin` builds a pinned entry with empty snippet, panel hides the snippet line.

**Minimum fix**: `extractCitations` (or a sibling `enrichCitations` function called in onFinish) must resolve each `SIG.MSR.NNN` against the MSR signal store (e.g. `lib/citations/msr_lookup.ts` or directly via `query_signal_state`). Populate `snippet` with the signal's gloss/title from the actual MSR row and `layer` with its true layer (L1 vs L2.5 vs L3 depending on the signal's origin). Then C.3's existing consumption code in V2AssistantText works correctly. This is a backend wiring fix masquerading as a frontend bug — explains why the prior PR claimed to ship C.3 but the operator still sees empty descriptions.

### B6 — Regenerate icon too small

**Where**: `ConsumeChatV2.tsx:327` — `V2RegenerateButton` uses `h-6 w-6` button with `h-3 w-3` inner SVG. Same sizing for Details (line 627), Copy (line 638), Edit (line 488). Compared to the composer Send button at line 1026 which is `h-9 w-9` with `h-4 w-4` SVG, the action bar icons are visibly undersized.

**Root cause**: The β6 action-bar implementation went with tight `h-6 w-6` to fit multiple icons in a row. Visually too small at default 16 px font sizes; touch-tap targets are below WCAG 2.5.5 (44 px target size).

**Minimum fix**: Scale action-bar buttons to `h-8 w-8` with `h-4 w-4` inner SVG. Increase gap from `gap-1` to `gap-1.5`. Apply consistently across Edit, Regenerate, Details, Copy. Add `min-h-[40px] min-w-[40px]` for touch parity (slightly below 44 px to keep design compact, but the buttons should be focusable + touch-friendly).

## §3 — Newly surfaced root causes (N1–N3)

### N1 — Reports library opens but empty

**Where**: `platform/src/app/clients/[id]/consume/page.tsx:33-38` — server fetches reports via `query('SELECT * FROM reports WHERE chart_id=$1 ORDER BY domain ASC', [id])`. Empty array passed to `<ConsumeChat reports={reports} />` at line 53. Propagates to `ConsumeChatV2` props (line 1286) → `ConsumeReportLibraryV2` (line 1516). `ReportLibrary.tsx:31-34` shows `"No reports yet"` when `reports.length === 0`.

**Root cause**: The `reports` table contains no rows for the current chart. ReportLibrary wiring is correct. The empty state copy *does* exist but the operator may have missed it under the sheet's brand header, or the empty-state text is muted and hard to spot. There is no orchestration that writes reports anywhere in the V2 flow — this entire panel is a passive viewer of pre-existing rows. No code path in V2 (or in legacy, near as I can tell from grepping) writes to the `reports` table from the chat flow.

**Minimum fix**: This is not a wiring bug. Two options: (a) seed sample reports for the development chart so the panel demos correctly; (b) write a "Reports library is empty for this chart" empty-state hero with sub-copy explaining what reports are and where they would be generated (currently the only source is the panel-synthesis legacy path). Defer to product. The fix-wave can simply make the empty-state more prominent and accept this is a content/data issue, not a code issue.

### N2 — Sidebar conversation grouping typography not per design system

**Where**: `ConversationSidebarV2.tsx:68-74` — `SectionHeader` uses `text-[10px] font-semibold uppercase tracking-widest text-zinc-500`. Design system tokens are not referenced (no `text-muted-foreground`, no brand-gold variants). Compare `ConsumeChatV2.tsx:1506` (chart meta) which uses `text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)]` — closer to brand discipline.

**Root cause**: The sidebar was authored before the chrome-parity work landed brand-gold tokens systematically. The typography uses Tailwind zinc literals instead of design tokens.

**Minimum fix**: Replace `text-[10px] font-semibold uppercase tracking-widest text-zinc-500` with `text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)]`. Apply the same treatment to the "Conversations" header at line 211-213 (currently `text-xs font-semibold text-zinc-400 uppercase tracking-wide`). All four typography tokens (size, weight, letter-spacing, color) should match the chart-meta line for consistency.

### N3 — Three-dot menu doesn't trigger rename/delete

**Where**: `ConversationSidebarV2.tsx:106-128`. The "…" affordance is a `<span aria-hidden>` with no `onClick`, no `role="button"`, no handler — purely decorative SVG. There is no rename or delete handler on `ConversationSidebarV2Props` either (lines 26-35).

**Root cause**: The component scaffolds the visual affordance but the menu was never wired. Endpoint `DELETE /api/conversations/[id]` exists (per audit S3.4) but no client trigger calls it. Rename has no endpoint at all — `/api/conversations/[id]` only supports DELETE (archive), not PATCH (rename).

**Minimum fix**: This requires both backend and frontend changes.
- Backend: add `PATCH /api/conversations/[id]` accepting `{ title: string }` and updating `conversations.title`. ~20 lines.
- Frontend: replace decorative `<span>` with a `Popover` trigger button. Two `MenuItem`s: "Rename" (opens inline `<input>` overlay), "Delete" (confirmation dialog → DELETE call → reload sidebar). Add `onRename(id, title)` + `onDelete(id)` to `ConversationSidebarV2Props`. Pass through from `ConsumeChatV2` with handlers that call the endpoints and trigger `setSidebarReloadTick(n => n+1)`. ~80 lines.

Scope-wise this is the most-expensive N-class fix. Could be deferred to a Round 7 if Round 6 is tight.

## §4 — Additional orphans found (research-driven)

### O1 — `synthesis` stage never transitions to `'done'` (HIGH)

`route.ts:889` emits `stagePart('synthesis', 'running')` but no matching `'done'` event ever fires. Even after fixing B1 so the stepper renders at all, the synthesis pip will pulse indefinitely. Add the closing event in the post-merge block or in onFinish.

### O2 — `pointer-events-none` on collapsed-sidebar wrapper kills expand button (HIGH — possibly existing user-facing bug)

`ConsumeChatV2.tsx:1444-1448` — when `sidebarCollapsed=true`, the wrapper has `md:pointer-events-none`. Inside, `ConversationSidebarV2.tsx:174-199` renders the collapsed strip which has `pointer-events-none` at the outer div and `pointer-events-auto` only on the expand button itself (line 179). The button gets clicks. But the strip is "decorative" between mouseovers — only one focusable element. This is intentional but fragile: any future button added to the strip silently breaks because `pointer-events-none` propagates inward. Add a TODO or refactor: drop `pointer-events-none` from the wrapper and let the strip be normally interactive.

### O3 — Citation chip footer + repeated `SIG.MSR.NNN` in body double-displays the citation count (LOW-MEDIUM)

Because B2/B3 leaves raw `SIG.MSR.NNN` in body text AND renders chips in the footer, users see each citation twice (once raw, once as `[N]` chip). Fixing B2/B3 resolves this.

### O4 — `useChatPreferences` returns `setAudienceTier` but the prefs ctx never publishes it (LOW)

`ConsumeChatV2.tsx:1296, 1300` — `activeTier` and `audienceTier` are both in context, but only `activeTier` is settable via `setActiveTier`. Inconsistent. `audienceTier` is the prop from server; `activeTier` is the in-chat override. The naming makes both look settable. Rename to `setActiveTierOverride` or document inline.

### O5 — `V2QueryIdTracker` + `V2ConversationIdTracker` + `V2TitleTracker` each separately subscribe to the same runtime (LOW)

`ConsumeChatV2.tsx:1052, 1081, 1117` — three null-rendering components, each calling `runtime.subscribe(...)`, each scanning all messages on every state update. O(n²) when n messages exist and many state updates happen during a stream. Consolidate into one tracker that emits all three events. Performance, not correctness.

### O6 — `CitationSidePanel` is mounted unconditionally at the runtime root (LOW)

`ConsumeChatV2.tsx:1683-1687` — `CitationSidePanel` is always inside the AssistantRuntimeProvider tree. It self-hides when `pinnedCitations.length === 0` (line 19). Fine, but its mobile presentation is `fixed bottom-0 inset-x-0 ... max-h-[45vh]` (line 24) — it can cover up to 45% of the mobile viewport. Touch users with one pinned citation lose half their screen. Add a collapsed/expanded mode for mobile.

### O7 — Audit AD3 (extractCitations always-empty snippet) propagates to `pdf_extractor`-style B.10 violation (CRITICAL semantic)

The synthesis prompt instructs the model to cite SIG.MSR.NNN. The model complies. The route extracts them. Snippet is empty. The user sees a chip with `SIG.MSR.NNN` and no description. The user cannot verify the citation matches the claim without leaving the UI. This is a soft B.10 violation: the citation is *present* but *unauditable*. The fix (B4/B5) is therefore higher-stakes than "polish".

### O8 — `EmptyState` is wrapped inside `ThreadPrimitive.Empty` (REACHABLE but possibly invisible at v2 startup) (LOW)

`ConsumeChatV2.tsx:1249-1256`. Verify that `ThreadPrimitive.Empty` fires correctly when initialMessages is undefined vs an empty array; an off-by-one here would silently hide the chart-aware suggestions.

### O9 — `HISTORY_COMPRESSION_ENABLED` and `COST_VISIBILITY_FOR_USERS` flags are wired but never tested in F.3 (LOW)

Grep confirms both flags are wired (route.ts + consume page + history_compression.ts). They're FLAG-GATED-OFF by default. F.3 cannot have validated their behavior. Either flip in staging and add an F.3 test case, or accept they remain dormant until a future round. The Round 5 plan E.2 ambiguously called for "wire or remove" — they're wired; promotion to true is the only remaining decision.

### O10 — Dead import: none found

Grep against `ConsumeChatV2.tsx` imports shows every import is used. No dead imports.

### O11 — `LiveReasoningCard` (legacy) and `LogPredictionAction` (legacy) still in `components/consume/` after Phase E.4 was supposed to delete them

Per the capability audit S2.3 / S2.8 — these are legacy V2-orphaned components. Phase E.4 was supposed to delete stranded legacy components. Confirm they're still there; queue for deletion.

## §5 — Cumulative root-cause pattern

Three pattern threads emerge:

**Pattern A — Inconsistent data-parts source-of-truth.** `message.content` (assistant-ui DataMessagePart, `type:'data', name:'<x>'`) versus `message.metadata.unstable_data` (`type:'data-<x>'`) is checked inconsistently across V2Message subscribers. Citation + correction + out-of-domain code defends against both. Stage + tool + panel + citation_gate + prediction code only checks `unstable_data`. The route emits to whatever assistant-ui chooses, which is `message.content`. Result: half the live UI is invisible. **One bug, ~5 affected surfaces (B1, plus tools, panel, gate, predictions).**

**Pattern B — Duplicate affordances that were never reconciled at adoption.** When ConversationSidebarV2 was adopted, its inherited collapse button was not removed; the header toggle was added in parallel. The composer's two-button streaming UX was never copy-clarified. The action bar shows hover-only on touch (B-class fix already known). **Reconciliation discipline missing at every component-replacement step.** L2 + L3 + sidebar-logo missing are all instances.

**Pattern C — Backend stubs that the frontend assumes are rich.** `extractCitations` ALWAYS sets snippet=''. The frontend's `citationRichMap` builds a map of empty entries. The CitationSidePanel hides the snippet block because the conditional fails. C.3 thought the route was emitting rich data and the V2 wasn't consuming it; in fact the route's emission is a thin shim around empty data. Same shape applies to pdf_extractor (Vertex DU returns fixture), fakeGcsRetrieve (in-process Map), and prediction extraction (regex-based, low precision). The pattern: **stubs that satisfy the type signature but not the semantic contract**.

The fix-wave should therefore address Pattern A as a single PR (unified `useDataParts(message)` hook), Pattern B as 3 small PRs (one per duplicate), and Pattern C as targeted backend fixes per capability.

## §6 — Recommended Round 6 fix-wave scope

### P0 — Blocks reflip
- **R6.1** — Unified `useDataParts(message)` hook + replace 5 call sites → fixes B1 + stage/tool/panel/gate/prediction visibility.
- **R6.2** — Inline citation rendering via `[^N]` Markdown footnotes (synthesis prompt change + MarkdownContent footnote component) → fixes B2/B3 + O3.
- **R6.3** — Enrich `extractCitations` against MSR signal store → fixes B4/B5 + O7.
- **R6.4** — Sidebar layout discipline: drop `md:ml-{10,56}`; sidebar overlay only; delete in-sidebar collapse button → fixes L1 + L2.
- **R6.5** — Single send/stop button during streaming → fixes L3.
- **R6.6** — `stagePart('synthesis', 'done')` emission in onFinish → fixes O1.

### P1 — Important but not blocking
- **R6.7** — Action-bar icon scale-up (h-8 w-8, h-4 w-4) → fixes B6.
- **R6.8** — Sidebar `<Logo />` at bottom + brand typography tokens → fixes L4 + N2.
- **R6.9** — Wire conversation rename + delete (3-dot menu) → fixes N3. Backend PATCH + frontend Popover.
- **R6.10** — Consolidate three runtime trackers into one → fixes O5.

### P2 — Polish
- **R6.11** — Reports library empty-state hero copy → addresses N1.
- **R6.12** — Delete LiveReasoningCard + LogPredictionAction → addresses O11.
- **R6.13** — Mobile citation panel collapsed mode → addresses O6.
- **R6.14** — Audit `useChatPreferences` naming → addresses O4.

### Acceptance for reflip (Phase F.4)
After R6.1–R6.6 merge: re-run F.3 walkthrough. L1/L2/L3/B1/B2/B3/B4/B5/O1 must all PASS via Playwright assertions (see §7). Operator visual review confirms parity with legacy + Gemini reference.

## §7 — Smoke test automation recommendation

Add a single Playwright spec `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` covering every F.3 finding. Wire as a required check on chat-v2 PRs via `.github/workflows/chat-v2-smoke.yml`. The spec runs against a dev-server-with-mocks fixture mode so it does not need live LLM credentials.

### Specific assertions

| F.3 finding | Playwright assertion |
|---|---|
| L1 | `await expect(page.getByTestId('v2-chat-column')).toHaveCSS('margin-left', '0px')` (after fix); plus a visual baseline at viewport widths 1280, 1440, 1920 |
| L2 | `await expect(page.getByTestId('v2-sidebar-collapse')).toHaveCount(0)` (inside the sidebar); `await expect(page.getByTestId('v2-desktop-sidebar-toggle')).toHaveCount(1)` |
| L3 | During streaming: `await expect(page.locator('[data-testid="v2-abort-btn"], [data-testid="v2-interrupt-send-btn"]')).toHaveCount(1)` |
| L4 | `await expect(page.getByTestId('v2-conversation-sidebar').locator('[data-testid="brand-logo"]')).toBeVisible()` |
| B1 | After sending a query: `await expect(page.getByTestId('v2-stage-stepper')).toBeVisible({ timeout: 5000 })` + `await expect(page.getByTestId('v2-stage-synthesis')).toBeVisible()` |
| B2/B3 | `await expect(page.getByTestId('v2-message-text')).not.toContainText(/SIG\.MSR\.\d{3}/)` (raw markers gone) + `await expect(page.getByTestId('v2-citation-badge').first()).toBeVisible()` (inline chips present) |
| B4/B5 | Click first citation: `await page.getByTestId('v2-citation-badge').first().click(); await expect(page.getByTestId('v2-citation-panel-item').locator('text=/^[A-Z]/')).toBeVisible()` (snippet starts with a letter, not empty) |
| B6 | `await expect(page.getByTestId('v2-regenerate-btn')).toHaveCSS('height', '32px')` (h-8 = 32px) |
| N1 | Open reports: `await expect(page.getByText(/No reports yet|Reports library is empty/)).toBeVisible()` |
| N2 | `await expect(page.locator('p:has-text("Today")').first()).toHaveCSS('letter-spacing', /0\.20em/)` |
| N3 | Click "…" menu: `await expect(page.getByRole('menuitem', { name: /Rename/ })).toBeVisible()`; then `await expect(page.getByRole('menuitem', { name: /Delete/ })).toBeVisible()` |
| O1 | After stream finishes: `await expect(page.getByTestId('v2-stage-synthesis')).toHaveAttribute('class', /text-zinc-400/)` (done state, not running animate-pulse) |

### File/workflow sketch

- New file: `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` — ~180 lines, one `test.describe('Round 6 walkthrough', ...)` block, one `test(...)` per row above.
- New file: `platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts` — registers a mock route handler for `POST /api/chat/consume` that emits a canned stream with stage events, citation parts, a sample answer containing two SIG.MSR.NNN markers, and a completion. No live LLM call.
- Existing file: `platform/playwright.config.ts` — confirm `chat-v2` project is registered with `auth.setup.ts` storageState dependency.
- New workflow: `.github/workflows/chat-v2-smoke.yml`:
  - Trigger: `pull_request` on paths `platform/src/components/consume/ConsumeChatV2.tsx`, `platform/src/components/chat-v2/**`, `platform/src/components/chat/ConversationSidebarV2.tsx`, `platform/src/app/api/chat/consume/route.ts`.
  - Steps: checkout → `npm ci` → `npx playwright install chromium` → `npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=github`.
  - Required check: branch protection rule on `main` makes this required for `chat-v2-r6/*` and `fix/chat-v2-*` branches.
- Existing `chat-v2` test infra (T1-T8 per capability audit) stays. The Round 6 smoke is **additive**, not replacing.

The CI cost is low: chromium-only, no live LLM, single spec file, < 60s wall time per run.

## §8 — Changelog

- **v1.0 (2026-05-18, DRAFT)** — Initial forensic. Twelve operator-observed F.3 findings root-caused; eleven additional orphans surfaced; cumulative root-cause pattern identified; Round 6 fix-wave prioritized (P0/P1/P2); Playwright smoke spec sketched. Awaiting operator triage before any Round 6 EXEC briefs are authored.

---

*End CHAT_V2_F3_FORENSIC v1.0 DRAFT.*
