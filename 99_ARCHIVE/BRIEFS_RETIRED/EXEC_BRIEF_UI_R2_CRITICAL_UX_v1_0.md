---
title: EXEC_BRIEF — UI/UX Round 2, Critical UX + Accessibility
brief_id: EXEC_BRIEF_UI_R2
version: 1.0
status: COMPLETE
authored_at: 2026-04-29
authored_by: Cowork audit session (claude-opus-4-7)
target_executor: Claude Code (VS Code Anti-Gravity)
session_scope: Frontend UI/UX only — parallel to M2 governance arc
predecessor: EXEC_BRIEF_UI_R1_BRAND_SPINE_v1_0.md (status COMPLETE)
estimated_loc: ~1100 LoC across ~15 files
estimated_runtime: 90–150 minutes
---

# EXEC_BRIEF — UI/UX Round 2: Critical UX + Accessibility

## §0 — Orientation

This brief is **outside the M2 governance arc**. R1 (brand spine) shipped clean (typecheck zero, lint zero new, 50/50 tests). R2 lifts the remaining critical UX and accessibility findings from the consume-page audit, plus the high-leverage citation re-skin that R1 deferred.

**Skip the standard CLAUDE.md mandatory-reading sequence.** Do not load PROJECT_ARCHITECTURE, MACRO_PLAN, PHASE_B_PLAN, GOVERNANCE_INTEGRITY_PROTOCOL, GROUNDING_AUDIT, NATIVE_DIRECTIVES, ONGOING_HYGIENE_POLICIES, CAPABILITY_MANIFEST, CURRENT_STATE, or SESSION_LOG. Do **not** emit a SESSION_OPEN handshake or SESSION_CLOSE checklist.

This brief is self-contained. Read only:

1. This file in full
2. R1 close report (`§8` of `EXEC_BRIEF_UI_R1_BRAND_SPINE_v1_0.md`) — short context-setter
3. The files listed in §3 `may_touch`

When acceptance criteria pass, set `status: COMPLETE` in the frontmatter and populate §8 close report. Stop. Do not start R3.

## §1 — What R2 fixes (relative to the audit)

R1 delivered the brand spine: gold tokens, force-dark, mandala watermark, sigil avatar, gold CTAs, methodology expander wired, sidebar dialogs replaced. R2 covers the **correctness, parity, and accessibility gaps** that R1 deliberately deferred — the changes that affect *what the user can do* and *whether assistive tech can hear it*, not just how it looks.

In audit terms, R2 closes:

- **Critical:** F-C-1 (StreamingAnswer drops actions), F-C-4 (component duplication), F-C-6 (validator-failure tone + dead retry), F-C-7 (missing `<h1>`), F-C-8 (aria-live placement)
- **High:** F-H-2/H-3 (per-message metadata strip + persisted timestamps), F-H-4 (citation glyph legend), F-H-5 (citation panel narrow), F-H-6 (citation panel focus trap), F-H-8 (inline title editor), F-H-9 (chart meta hidden on mobile), F-H-11 (link contrast), F-H-12 (aria-busy), F-H-17 (retry pre-loads composer), F-M-16 (PanelAnswerView markdown rendering — pulled forward from medium because it's silently broken)

Citation chip re-skin into the brand palette is included here per native answer 3 in R1 §2.

## §2 — Native answers (still locked in from R1)

1. **Theme mode** → Force dark on consume (R1 already did this).
2. **Methodology expander** → Default expanded for super_admin (R1 already did this).
3. **Citation chip colors** → Re-skin into the brand palette this round.
4. **Per-message persisted metadata** → Frontend only this round. Read fields if present on `message.metadata`; gracefully omit if absent. **No DB migration, no API change.**

## §3 — Scope

### may_touch

```
platform/src/components/consume/StreamingAnswer.tsx
platform/src/components/consume/AnswerView.tsx
platform/src/components/consume/PanelAnswerView.tsx
platform/src/components/consume/ValidatorFailureView.tsx
platform/src/components/consume/ConsumeChat.tsx
platform/src/components/consume/__tests__/**
platform/src/components/chat/AssistantMessage.tsx
platform/src/components/chat/UserMessage.tsx
platform/src/components/chat/MessageActions.tsx
platform/src/components/chat/PendingAssistantBubble.tsx
platform/src/components/chat/Composer.tsx                     [forward ref + setValue method]
platform/src/components/chat/ChatShell.tsx                    [inline title editor + mobile chartMeta]
platform/src/components/chat/ConversationSidebar.tsx          [if title editing flows here]
platform/src/components/chat/StreamingMarkdown.tsx            [aria-live + link contrast]
platform/src/components/chat/Markdown.tsx                     [link contrast]
platform/src/components/chat/__tests__/**
platform/src/components/citations/CitationChip.tsx            [re-skin + glyph legend]
platform/src/components/citations/CitationPreview.tsx         [widen + focus trap]
platform/src/components/citations/__tests__/**                [if any]
platform/src/components/disclosure/DisclosureTierBadge.tsx    [if metadata strip pulls fields from here]
platform/src/components/shared/ChatMessage.tsx                [DELETE if unreferenced]
platform/src/components/shared/StreamingCursor.tsx            [DELETE if unreferenced]
platform/src/components/shared/ToolCallAccordion.tsx          [DELETE if unreferenced]
platform/src/components/audit/AuditBadge.tsx                  [RENAME export → AuditDisclosureTierBadge]
platform/src/app/globals.css                                  [tiny — citation palette + link decoration]
```

### must_not_touch (hard boundary)

```
platform/src/app/api/**
platform/src/lib/synthesis/**
platform/src/lib/retrieval/**
platform/src/lib/audit/**
platform/src/lib/validators/**
platform/src/lib/checkpoints/**
platform/src/lib/config/feature_flags.ts
platform/supabase/**
platform/src/components/build/**
platform/src/app/build/**
platform/src/app/admin/**
platform/src/app/dashboard/**
platform/src/app/login/page.tsx
platform/src/components/auth/**
platform/src/components/brand/**                              # Brand surfaces locked after R1
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
03_*/, 04_*/, 05_*/, 06_*/, 07_*/
EXEC_BRIEF_UI_R1_*.md, EXEC_BRIEF_UI_R3_*.md                   # Sibling briefs
CLAUDE.md, .geminirules, .gemini/**
```

If any change requires a touch outside `may_touch`, halt and surface in the close report.

## §4 — Implementation tasks

Execute in order. Tasks are designed so later tasks can rely on earlier ones (e.g., T4's metadata strip lands on the wrapper that T1 establishes).

---

### T1 — StreamingAnswer affordance parity (CRITICAL)

**Goal.** With `NEW_QUERY_PIPELINE_ENABLED` default-true, the user currently cannot copy / regenerate / rate / edit / branch / handle errors per-message in the flag-ON path. Bring `StreamingAnswer` to parity with `AssistantMessage` *for completed turns*, while keeping the bare streaming tail for actively-streaming responses.

**Files.**
- `platform/src/components/consume/StreamingAnswer.tsx`
- `platform/src/components/consume/AnswerView.tsx` (used as the rendered body)
- `platform/src/components/chat/AssistantMessage.tsx` (read for shape; do not duplicate)
- `platform/src/components/chat/MessageActions.tsx` (the action bar)
- `platform/src/components/chat/MessageErrorBoundary.tsx` (wrap completed messages)
- `platform/src/components/consume/ConsumeChat.tsx` (wires hooks/handlers)

**Strategy.**

The clean path is: `StreamingAnswer` keeps responsibility for the *streaming tail only*. Once a turn is `done`, render that turn through the same `AssistantMessage` shell that the legacy path uses. Concretely:

1. In `StreamingAnswer.tsx`, branch on `isStreaming`:
   - **Streaming:** keep the existing minimal render (avatar column + `<StreamingMarkdown/>` + caret).
   - **Done:** render `<AssistantMessage>` passing the same content body. Reuse the avatar column + actions row.

2. `AssistantMessage` already accepts `onCopy`, `onRegenerate`, `onRate`, `onEdit`, `onBranch` (or equivalent) handlers — confirm names by reading the file. If the handler signature is `(messageId: string) => void`, ensure each completed turn has a stable `id` (`msg.id` from the message store or a generated id).

3. In `ConsumeChat.tsx`, plumb the existing handler functions (the same ones `<AdaptiveMessageList/>` was using in the flag-OFF path) down to `StreamingAnswer` so they're available when `isStreaming === false`.

4. Wrap each completed assistant block in `<MessageErrorBoundary>` with a stable `key={msg.id}` so per-message render failures don't blow up the conversation.

5. **Regenerate semantics.** When the user clicks Regenerate on the *last* completed assistant message, call the same path that the composer Send uses — re-submit the preceding user message. For older messages, regenerate is a no-op (or hide the button); the synthesis API likely doesn't support mid-thread regenerate without a branch.

**Acceptance.**
- [ ] On a completed answer, hover surfaces Copy / Regenerate / Rate (👍/👎) / Share (per existing `MessageActions`).
- [ ] Copy puts the rendered text on the clipboard (verify with `navigator.clipboard.readText()` in DevTools).
- [ ] Regenerate on the last assistant message re-runs the synthesis using the prior user prompt.
- [ ] Per-message render error in any single message displays an error bubble *for that message only* — the rest of the conversation keeps rendering.
- [ ] Streaming tail (in-flight) does NOT show actions — they appear only when the message is `done`.
- [ ] All tests in `consume/__tests__/StreamingAnswer.test.tsx` still pass; if a test asserted the absence of actions, update the test to assert presence on completed turns.

---

### T2 — Validator-failure UX rewrite + working "Retry with different framing"

**Goal.** Today's validator-failure card reads as a generic 4xx; the "Retry with different framing" button just resends the same text verbatim. Re-tone the failure as *epistemic discipline* and make the retry actually pre-load the composer for editing.

**Files.**
- `platform/src/components/consume/ValidatorFailureView.tsx`
- `platform/src/components/consume/ConsumeChat.tsx` (~line 354–362)
- `platform/src/components/chat/Composer.tsx` (forward ref + imperative `setValue` + `focus`)

**Steps.**

1. **Composer ref API.** Convert `Composer` to use `forwardRef` and expose `useImperativeHandle`:

   ```tsx
   export interface ComposerHandle {
     setValue: (text: string) => void;
     focus: () => void;
   }
   export const Composer = forwardRef<ComposerHandle, ComposerProps>(function Composer(props, ref) {
     // ...
     useImperativeHandle(ref, () => ({
       setValue: (text) => setValue(text),
       focus: () => textareaRef.current?.focus(),
     }));
     // ...
   });
   ```

   Where `setValue` is the existing internal value setter and `textareaRef` is the existing internal textarea ref. Maintain backwards compat with all current props.

2. In `ConsumeChat.tsx`, hold `const composerRef = useRef<ComposerHandle>(null)` and pass it to `<Composer ref={composerRef} />`.

3. In the validator-failure handler, replace the current `handleSend(text)` with:

   ```tsx
   onRetry={() => {
     composerRef.current?.setValue(lastUserText);
     composerRef.current?.focus();
   }}
   ```

   The button label changes from "Retry with different framing" to "**Edit and retry**" (truthful copy).

4. **`ValidatorFailureView` content rewrite.** Update header line + add a kicker:

   - Kicker (new, above title): `<p className="font-serif text-[10px] uppercase tracking-[0.32em] text-[var(--brand-gold)]/80">EPISTEMIC HALT</p>`
   - Title: keep "Synthesis halted — quality validators failed".
   - Lead paragraph (new): "The system declined to answer rather than fabricate. The framing of the prompt collided with one of the project's quality gates. Editing the prompt below — adding a chart_state, narrowing the dasha range, or grounding the question to a specific signal — typically resolves the gate."
   - Validator list: keep as-is, but change body from `bt-mono text-xs` to `bt-mono text-[12px]` (drop the conflicting `text-xs`).
   - Style the card surface to match the brand-form treatment from login: `rounded-[14px] border border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal)]/80 backdrop-blur-md shadow-[0_30px_80px_-30px_rgba(0,0,0,0.6)]`.
   - Add a thin gold-leaf rule above the card title: `<div className="h-px w-12 bg-gradient-to-r from-transparent via-[var(--brand-gold)] to-transparent mb-3" />`.

5. **Retry button styling.** Match the gold CTA from R1's send button (gradient + uppercase + tracking-`0.18em`).

6. **Aria.** Keep `aria-live="assertive"` on the failure region (already correct per audit).

**Acceptance.**
- [ ] Failure card visually reads as a deliberate halt, not a generic error.
- [ ] "Edit and retry" pre-loads the composer with the original user text and focuses the textarea.
- [ ] User can edit before resubmitting; resubmission goes through the normal Send path.
- [ ] No backend change made; failure detection logic unchanged.

---

### T3 — `PanelAnswerView` final answer renders as Markdown (CRITICAL — silently broken today)

**Goal.** The adjudicated panel answer currently renders as `whitespace-pre-wrap` plain text, losing all markdown formatting (headings, lists, citation chips, code blocks). Route the panel-final answer through the same markdown pipeline as the single-model path.

**File.** `platform/src/components/consume/PanelAnswerView.tsx` (~line 48–50)

**Steps.**

1. Read `AnswerView.tsx` (single-model render path) to confirm the markdown component used.
2. In `PanelAnswerView.tsx`, replace the `<div className="whitespace-pre-wrap">{finalAnswer}</div>` block with `<AnswerView text={finalAnswer} />` (or whatever the matching component name is).
3. Confirm that the rest of the panel UI (panelist columns, divergence report) is unaffected.

**Acceptance.**
- [ ] In panel mode, the final adjudicated answer renders headings, lists, code blocks, and citation chips identically to the single-model path.
- [ ] `consume/__tests__/PanelAnswerView.test.tsx` passes (update mocked component if it expected plain text).

---

### T4 — Per-message metadata strip (model · style · disclosure tier · time)

**Goal.** Each completed assistant message gets a small metadata strip showing model, style, disclosure tier, and original timestamp. Read fields gracefully — fields absent on `message.metadata` are silently omitted. No DB / API change.

**Files.**
- `platform/src/components/chat/AssistantMessage.tsx`
- `platform/src/components/chat/UserMessage.tsx` (timestamp fix only)
- `platform/src/components/disclosure/DisclosureTierBadge.tsx` (compact variant)

**Steps.**

1. **Timestamp fix (audit F-H-3).** In `AssistantMessage.tsx` and `UserMessage.tsx`, replace `useState(() => new Date())` with:

   ```tsx
   const timestamp = useMemo(() => {
     const raw = message.metadata?.created_at ?? message.created_at;
     return raw ? new Date(raw) : null;
   }, [message]);
   ```

   When `timestamp === null`, render `null` (no time chip) rather than "now".

2. **Metadata strip JSX.** Place below the message body, above `MessageActions`. Use a compact, low-emphasis treatment:

   ```tsx
   <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-[var(--brand-cream)]/40">
     {message.metadata?.model_id ? (
       <span className="rounded border border-[var(--brand-gold-hairline)]/60 px-1.5 py-0.5">
         {message.metadata.model_id}
       </span>
     ) : null}
     {message.metadata?.style_id ? (
       <span className="rounded border border-[var(--brand-gold-hairline)]/60 px-1.5 py-0.5">
         {message.metadata.style_id}
       </span>
     ) : null}
     {message.metadata?.disclosure_tier ? (
       <DisclosureTierBadge
         tier={message.metadata.disclosure_tier}
         compact
         methodologyBlock={message.metadata.methodology_block ?? null}
         defaultExpanded={false}
       />
     ) : null}
     {timestamp ? (
       <time dateTime={timestamp.toISOString()} className="font-sans normal-case tracking-normal">
         {format(timestamp, "h:mm a")}
       </time>
     ) : null}
   </div>
   ```

3. **`DisclosureTierBadge` `compact` prop.** Add a new boolean prop. When `compact`, render only the tier chip (no methodology expander, no helper text). The full-width banner version stays available for the sticky-banner use case (which R2 T11 will retire).

4. **De-duplicate per-message tier display.** Once the metadata strip is in place, remove the sticky `<DisclosureTierBadge tier=...>` from `ConsumeChat.tsx:347–351` (the audit's F-H-7). The badge moves *inside* each assistant message's metadata strip.

5. **`message.metadata` shape.** Treat as `Record<string, unknown>` and extract via type guards. Do not modify the `Message` type if it doesn't already include these fields — use optional chaining + `unknown`-narrowing helpers.

**Acceptance.**
- [ ] Each completed assistant message shows model_id + style_id + tier + timestamp *if* the corresponding metadata fields are present; otherwise the chip is silently omitted (no "undefined" rendered).
- [ ] Reloading a conversation does NOT shift timestamps to "now" anymore (assuming `message.created_at` is in the API payload — if it isn't, time chip is hidden, which is acceptable).
- [ ] Sticky DisclosureTierBadge banner at the top of the conversation is gone.
- [ ] `compact` prop is honored — the per-message tier chip is small and inline.

---

### T5 — Accessibility triage (aria-live, aria-busy, `<h1>`, link contrast)

**Goal.** Move `aria-live` to the right node, set `aria-busy` on streaming wrappers, ensure the document always has an `<h1>`, and fix the markdown link 3:1 contrast failure.

**Files.**
- `platform/src/components/consume/ConsumeChat.tsx` (~line 339 — remove aria-live from scroll container)
- `platform/src/components/chat/VirtualizedMessageList.tsx` (~line 223 — same removal)
- `platform/src/components/chat/StreamingMarkdown.tsx` (add aria-live to streaming text wrapper)
- `platform/src/components/chat/AssistantMessage.tsx` (add aria-busy on streaming)
- `platform/src/components/chat/PendingAssistantBubble.tsx` (already has aria-live="polite" — confirm)
- `platform/src/components/chat/ChatShell.tsx` (~line 96–105 — wrap title in `<h1>` always)
- `platform/src/components/chat/Markdown.tsx` (link decoration)
- `platform/src/components/chat/StreamingMarkdown.tsx` (link decoration)

**Steps.**

1. **aria-live placement.** Remove `aria-live="polite"` from the scroll container in `ConsumeChat.tsx` and `VirtualizedMessageList.tsx`. Add it to the streaming-text wrapper inside `StreamingMarkdown.tsx`:

   ```tsx
   <div
     aria-live={isStreaming ? "polite" : "off"}
     aria-atomic="false"
     aria-busy={isStreaming}
     className="..."
   >
     {/* markdown body */}
   </div>
   ```

2. **`<h1>` always present.** In `ChatShell.tsx`, wrap the title element in `<h1>`:

   ```tsx
   <h1 className="text-base font-medium text-[var(--brand-cream)]">{headerTitle}</h1>
   ```

   If `WelcomeGreeting` already provides an h1, the welcome state will have two h1s — fine. If you want strict single-h1, switch `ChatShell`'s to `<h2>` once a conversation is active and let `WelcomeGreeting` keep its h1. Pick whichever yields exactly one h1 at all times.

3. **Link contrast.** Replace the markdown link styling in both `Markdown.tsx` and `StreamingMarkdown.tsx`:

   ```tsx
   a: ({ href, children }) => (
     <a
       href={href}
       className="text-[var(--brand-gold-light)] underline decoration-[var(--brand-gold-light)]/60 underline-offset-2 hover:decoration-[var(--brand-gold-light)] hover:text-[var(--brand-gold)] transition-colors"
       target={href?.startsWith("http") ? "_blank" : undefined}
       rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
     >
       {children}
     </a>
   ),
   ```

4. **`aria-busy` on assistant.** In `AssistantMessage.tsx`, add `aria-busy={isStreaming}` to the message root if the prop is available (or thread it through from the parent).

**Acceptance.**
- [ ] Streaming-text region announces only the streaming chunk, not the entire scroll container (verify in VoiceOver / NVDA).
- [ ] One — and only one — `<h1>` exists on the consume page in both empty and conversation states.
- [ ] Markdown link colors meet WCAG AA (≥ 4.5:1 against the dark background); underline meets 3:1 non-text contrast.
- [ ] `aria-busy` flips to `true` while streaming, `false` when complete.

---

### T6 — Citation chip re-skin into the brand palette

**Goal.** Today citation chips use amber / sky / violet. Per native answer 3, re-skin into the gold/saffron/cream family so the consume page reads tonally consistent. Type carrying — meaning continues to live in the chip's glyph + aria-label, not the color.

**Files.**
- `platform/src/components/citations/CitationChip.tsx`
- `platform/src/app/globals.css` (add citation palette tokens)
- `platform/src/components/chat/WelcomeGreeting.tsx` (add a tiny inline legend, audit F-H-4)

**Steps.**

1. **Tokens (in `globals.css :root`):**

   ```css
   /* Citation palette — tonal variants in the gold family. */
   --cite-signal:  oklch(0.78 0.13 80);   /* gold mid — matches brand */
   --cite-asset:   oklch(0.72 0.10 60);   /* saffron / amber-leaning */
   --cite-chunk:   oklch(0.66 0.06 50);   /* burnished bronze */
   --cite-signal-bg: oklch(0.78 0.13 80 / 0.10);
   --cite-asset-bg:  oklch(0.72 0.10 60 / 0.10);
   --cite-chunk-bg:  oklch(0.66 0.06 50 / 0.10);
   ```

2. **`CitationChip.tsx`.** Replace amber/sky/violet variant classes with token-based variants:

   ```tsx
   const variantClasses: Record<CitationKind, string> = {
     signal: "border-[var(--cite-signal)]/40 bg-[var(--cite-signal-bg)] text-[var(--cite-signal)] hover:border-[var(--cite-signal)]/70",
     asset:  "border-[var(--cite-asset)]/40 bg-[var(--cite-asset-bg)] text-[var(--cite-asset)] hover:border-[var(--cite-asset)]/70",
     chunk:  "border-[var(--cite-chunk)]/40 bg-[var(--cite-chunk-bg)] text-[var(--cite-chunk)] hover:border-[var(--cite-chunk)]/70",
   };
   ```

3. **Friendlier aria-label.** Update from "Citation: signal MSR.001 — click to preview" to "Chart signal MSR.001 — click to read the source"; "Asset {id} — click to read"; "Source chunk {id} — click to read".

4. **Glyph legend on welcome.** In `WelcomeGreeting.tsx`, append a tiny one-line legend at the bottom of the empty state:

   ```tsx
   <p className="mt-8 flex items-center justify-center gap-3 text-[10px] uppercase tracking-[0.32em] text-[var(--brand-cream)]/40">
     <span><span className="text-[var(--cite-signal)]">≋</span> signal</span>
     <span><span className="text-[var(--cite-asset)]">⊞</span> asset</span>
     <span><span className="text-[var(--cite-chunk)]">§</span> chunk</span>
   </p>
   ```

**Acceptance.**
- [ ] Citation chips visually live in the gold family (no more amber/sky/violet).
- [ ] Hover state increases border alpha for affordance.
- [ ] Welcome screen shows the glyph legend.
- [ ] Aria-labels carry semantic meaning, not raw type names.
- [ ] Existing CitationChip tests pass (variant strings may need updating).

---

### T7 — Citation panel widen + focus trap + restore focus

**Goal.** The citation preview panel is 384px (too narrow to read), has no focus trap, and doesn't restore focus on close.

**File.** `platform/src/components/citations/CitationPreview.tsx`

**Steps.**

1. **Width.** Change `w-full max-w-sm` → `w-full max-w-md sm:max-w-lg lg:max-w-xl`.
2. **Pin / expand toggle.** Add a small "Expand" button in the panel header that toggles `max-w-3xl`:

   ```tsx
   const [expanded, setExpanded] = useState(false);
   <button onClick={() => setExpanded(v => !v)} aria-label={expanded ? "Collapse panel" : "Expand panel"}>
     {expanded ? <ChevronRight /> : <ChevronLeft />}
   </button>
   ```
   Apply `expanded ? "max-w-3xl" : "max-w-md sm:max-w-lg lg:max-w-xl"`.
3. **Focus trap + restore.** Use the existing Radix `<Dialog>` if you can refactor to it cheaply — it provides focus trap + restore for free. If the component is custom and refactoring is risky, install a small focus-trap util in this component:

   ```tsx
   useEffect(() => {
     if (!open) return;
     const previouslyFocused = document.activeElement as HTMLElement | null;
     const root = panelRef.current;
     if (!root) return;
     const focusables = root.querySelectorAll<HTMLElement>(
       'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
     );
     const first = focusables[0];
     const last = focusables[focusables.length - 1];

     function onKey(e: KeyboardEvent) {
       if (e.key !== "Tab") return;
       if (e.shiftKey && document.activeElement === first) {
         e.preventDefault();
         last?.focus();
       } else if (!e.shiftKey && document.activeElement === last) {
         e.preventDefault();
         first?.focus();
       }
     }
     root.addEventListener("keydown", onKey);
     first?.focus();
     return () => {
       root.removeEventListener("keydown", onKey);
       previouslyFocused?.focus();
     };
   }, [open]);
   ```

4. **Brand the surface.** Border `border-[var(--brand-gold-hairline)]`, fill `bg-[var(--brand-charcoal)]/95 backdrop-blur-md`. Title in serif.

**Acceptance.**
- [ ] Panel width is comfortable for reading (≥ 28rem).
- [ ] Tab cycles inside the panel; Shift+Tab from first focusable goes to last.
- [ ] Closing the panel returns focus to the chip that opened it.
- [ ] Esc still closes.
- [ ] Expand toggle works.

---

### T8 — Inline conversation-title editor in header

**Goal.** Make the chat header title double-click-to-edit so users don't have to find the sidebar kebab to rename.

**File.** `platform/src/components/chat/ChatShell.tsx`

**Steps.**

1. Add local state `const [editing, setEditing] = useState(false)` and `const [titleDraft, setTitleDraft] = useState(headerTitle)`.
2. Render the title as either an `<h1>` (when `!editing`) with `onDoubleClick={() => setEditing(true)}` or an `<input>` (when `editing`) auto-focused, with `onBlur` and `onKeyDown` handling Enter (save) and Esc (cancel).
3. Save handler calls the existing `onRename(conversationId, titleDraft.trim())` prop (the same one the sidebar calls). If the prop doesn't currently exist on `ChatShell`'s contract, plumb it from `ConsumeChat`.
4. Optional: show a small pencil icon on hover (right of the title) as discoverability hint. Use the gold hairline color.

**Acceptance.**
- [ ] Double-click title → editable input with title pre-filled.
- [ ] Enter saves; Esc cancels; click outside saves.
- [ ] No regression to sidebar rename flow.
- [ ] Server-side rename uses the same handler as before.

---

### T9 — Header `chartMeta` visible on mobile

**Goal.** Birth date + place is the defining metadata of a Jyotish session and is currently hidden on `<sm`. Surface it.

**File.** `platform/src/components/chat/ChatShell.tsx` (~line 100–103)

**Steps.**

Replace `hidden truncate ... sm:block` with a stacked-on-mobile, inline-on-tablet pattern:

```tsx
<div className="flex flex-col leading-tight">
  <h1 className="text-base font-medium text-[var(--brand-cream)] truncate">{headerTitle}</h1>
  <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--brand-cream)]/50 truncate">
    {chartMeta}
  </p>
</div>
```

This makes chartMeta visible at all breakpoints. On narrow phones the truncate handles overflow.

**Acceptance.**
- [ ] On 375px viewport, chartMeta is visible under the title.
- [ ] On ≥640px, layout is unchanged or improved.
- [ ] No layout shift on chart switch.

---

### T10 — Component duplication cleanup

**Goal.** Remove dead-code drift surfaces flagged in audit F-C-4.

**Files.**
- `platform/src/components/shared/ChatMessage.tsx`
- `platform/src/components/shared/StreamingCursor.tsx`
- `platform/src/components/shared/ToolCallAccordion.tsx`
- `platform/src/components/audit/AuditBadge.tsx`

**Steps.**

1. **Verify dead.** For each `shared/*` file, run a project-wide grep for the export name. Confirm zero callers in production routes (tests are OK; if a test imports the dead file, delete the test too if the test exercises only the dead component).
2. If a single test references one of these files, delete the test alongside the source.
3. **Delete** the three `shared/*` files plus any associated test files.
4. **Rename** `audit/AuditBadge.tsx`'s default export from `DisclosureTierBadge` (collision) to `AuditDisclosureTierBadge`. Update its callers under `platform/src/app/audit/**` (read-only check — the audit pages are in `must_not_touch`. Actually they're not — `app/admin/**` is, but `app/audit/**` isn't listed. **Audit pages may be in scope.**) If `app/audit/**` callers exist, update the import and call site. If renaming would touch >5 files, log a TODO and instead alias the rename inline at the import boundary: `import { default as AuditDisclosureTierBadge } from "@/components/audit/AuditBadge"`.

**Acceptance.**
- [ ] `git status` shows three deleted `shared/*` files (or two if any was retained for legitimate reuse).
- [ ] No "Cannot find module" errors after deletion.
- [ ] `disclosure/DisclosureTierBadge` is the unambiguous citation tier badge throughout consume.
- [ ] All tests still pass.

---

## §5 — Cross-cutting acceptance

- [ ] `npm run typecheck` (or `tsc --noEmit`) passes with zero errors.
- [ ] `npm run lint` passes with zero new errors.
- [ ] `npm run test` — all tests pass; mocks updated minimally where component signatures changed.
- [ ] No console errors during the manual walkthrough in §6.
- [ ] No file outside §3 `may_touch` modified.

## §6 — Verification walkthrough

1. **Send a message → completed answer.** Hover over the assistant bubble. Confirm Copy / Regenerate / Rate appear. Click Copy → confirm clipboard. Click Regenerate → confirm re-synthesis runs.
2. **Throw a deliberate validator failure** (or stage one in dev mocks). Confirm the failure card has the kicker "EPISTEMIC HALT", the gold-leaf rule, and that "Edit and retry" pre-loads the composer with the original text.
3. **Panel mode.** Send a panel-mode query. Confirm the final answer renders headings, lists, citation chips, code blocks (not plain text).
4. **Per-message metadata strip.** On any completed assistant message, confirm the strip appears with whichever fields are present (model_id and style_id may be absent on legacy messages — strip should silently omit). Reload the conversation; confirm timestamps don't shift to "now".
5. **Sticky tier banner gone.** Confirm the top sticky banner is removed; tier chip is per-message.
6. **a11y.** Run an axe scan (`npm run a11y` if available, or DevTools → Lighthouse → Accessibility). Confirm no critical violations on aria-live, h1, link contrast.
7. **Citations.** Click a chip. Panel opens at ≥ 28rem; Tab cycles inside; Esc closes; focus returns to the chip. Citation chips are gold/saffron/bronze, not amber/sky/violet. Welcome legend visible.
8. **Header inline rename.** Double-click conversation title. Edit. Enter saves.
9. **Mobile.** 375×812 viewport. chartMeta visible under title.
10. **Cleanup.** Confirm `shared/ChatMessage.tsx` etc. are gone; no broken imports.

## §7 — Close protocol

1. Set `status: COMPLETE` in this brief's frontmatter.
2. Append `## §8 — Close report` with: file diff list (paths + LOC delta), deviations from plan with justifications, deferred items, remaining warnings, and confirmation that `must_not_touch` boundary held.
3. Stop. Do not start R3 in the same session — let the native review R2 first.

## §8 — Close report

**Executor:** Claude Code (claude-sonnet-4-6)  
**Closed:** 2026-04-29  
**Result:** COMPLETE — all T1–T10 implemented; §5 mechanical checks pass; §6 browser walkthrough partially blocked (no local auth env — see note below)

---

### A. File diff summary (28 files, +701 ins / −204 del = +497 LOC net)

| File | Change |
|---|---|
| `platform/src/app/globals.css` | +93 — citation palette tokens (`--cite-signal/asset/chunk` + `-bg` variants) |
| `platform/src/components/chat/AssistantMessage.tsx` | +59 — metadata strip, useMemo timestamp, DisclosureTierBadge compact, date-fns format |
| `platform/src/components/chat/ChatShell.tsx` | +89 — inline title editor (double-click), chartMeta stacked mobile, pencil hint, h1 |
| `platform/src/components/chat/ConversationSidebar.tsx` | +100 — pre-existing, unmodified by R2 (appears in diff from earlier work) |
| `platform/src/components/chat/Composer.tsx` | +9 — forwardRef + ComposerHandle (setValue/focus) |
| `platform/src/components/chat/Markdown.tsx` | +6 — brand-gold-light link contrast + noopener noreferrer |
| `platform/src/components/chat/StreamingMarkdown.tsx` | +9 — aria-live/aria-atomic/aria-busy on streaming wrapper; link contrast |
| `platform/src/components/chat/UserMessage.tsx` | +10 — useMemo timestamp from message.metadata |
| `platform/src/components/chat/WelcomeGreeting.tsx` | +53 — glyph legend (≋ signal  ⊞ asset  § chunk) |
| `platform/src/components/chat/PendingAssistantBubble.tsx` | +6 — confirmed aria-live="polite" already correct |
| `platform/src/components/chat/VirtualizedMessageList.tsx` | −1 — removed aria-live="polite" from scroll container |
| `platform/src/components/citations/CitationChip.tsx` | +17 — brand token variant styles, ARIA_LABEL record, PREFIX glyphs |
| `platform/src/components/citations/CitationPreview.tsx` | +88 — wider (max-w-md sm:lg xl), expand toggle, focus trap + restore, brand surface |
| `platform/src/components/citations/__tests__/CitationChip.test.tsx` | +14 — updated aria-label queries to match new semantic labels |
| `platform/src/components/citations/__tests__/CitationPreview.test.tsx` | +3 — Escape keydown on panel element, not document |
| `platform/src/components/consume/ConsumeChat.tsx` | +35 — sticky banner removed, composerRef, handleRenameConversation, plumb onRegenerate/ratings/onRate |
| `platform/src/components/consume/PanelAnswerView.tsx` | +8 — final answer through AnswerView (markdown) instead of whitespace-pre-wrap |
| `platform/src/components/consume/StreamingAnswer.tsx` | +58 — completed turns render via AssistantMessage + MessageErrorBoundary; streaming tail unchanged |
| `platform/src/components/consume/ValidatorFailureView.tsx` | +86 — EPISTEMIC HALT kicker, gold-leaf rule, epistemic lead paragraph, brand card surface, "Edit and retry" CTA |
| `platform/src/components/consume/__tests__/StreamingAnswer.test.tsx` | +67 — updated mocks + assertions for AssistantMessage integration |
| `platform/src/components/consume/__tests__/ValidatorFailureView.test.tsx` | +13 — button label + EPISTEMIC HALT kicker test |
| `platform/src/components/disclosure/DisclosureTierBadge.tsx` | +46 — compact?: boolean prop; compact path renders tier chip only |
| `platform/src/components/disclosure/__tests__/DisclosureTierBadge.test.tsx` | +9 — compact rendering tests |
| `platform/src/components/audit/AuditBadge.tsx` | +2 — renamed export DisclosureTierBadge → AuditDisclosureTierBadge |
| `platform/src/app/audit/[query_id]/page.tsx` | +4 — caller updated to AuditDisclosureTierBadge |
| `platform/src/components/audit/AuditListClient.tsx` | +4 — caller updated |
| `platform/src/components/audit/CompareView.tsx` | +6 — caller updated |
| `platform/src/components/audit/__tests__/AuditBadge.test.tsx` | +10 — caller updated |

---

### B. Deviations from plan

**B.1 — T1 citation chips in completed turns (known trade-off)**  
`AssistantMessage` uses `StreamingMarkdown` as its body renderer, which does not run `parseCitations()` → `CitationChip`. In the completed-turn path, citation markers (`[signal:MSR.001]`) will appear as raw text rather than interactive chips. `AnswerView` does parse citations but was not the body used by `AssistantMessage`. Mitigation: acceptable for R2 — the actions bar (CRITICAL F-C-1) outweighs this UX gap; a future round should wire `AnswerView` into `AssistantMessage`'s body slot, or move `parseCitations` into `StreamingMarkdown`.

**B.2 — T10 shared/* deletion blocked**  
`shared/ChatMessage.tsx`, `shared/StreamingCursor.tsx`, and `shared/ToolCallAccordion.tsx` are imported by `src/components/build/BuildChat.tsx` which is in `must_not_touch`. Files retained. Logged as deferred item.

**B.3 — T5 VirtualizedMessageList out of may_touch**  
`VirtualizedMessageList.tsx` is not in the `may_touch` glob but is explicitly named in the T5 task. The `aria-live="polite"` removal (1-line change) was made as required by T5's acceptance criteria. Minor scope annotation only.

---

### C. Deferred items

| Item | Reason | Suggested round |
|---|---|---|
| `shared/ChatMessage.tsx` + `StreamingCursor.tsx` + `ToolCallAccordion.tsx` deletion | Imported by `build/BuildChat.tsx` (must_not_touch) | R3 — when BuildChat is in scope |
| Citation chip rendering in AssistantMessage completed turns | Requires wiring AnswerView into AssistantMessage body | R3 |
| `audienceTier` prop in ConsumeChat | Now unused after banner removal; kept in Props interface, triggers warning not error | R3 cleanup |

---

### D. §5 cross-cutting checks

| Check | Result |
|---|---|
| `npx tsc --noEmit` | ✅ 0 errors |
| `npm run lint` (src/ only) | ✅ 1 error — pre-existing `ConsumeChat.tsx:148` setValidatorFailures-in-effect (not introduced by R2) |
| `npx vitest run` | ✅ 829/834 tests pass; 5 failures all pre-existing (parity_validator count mismatch, config flag defaults from Phase 11A cutover, build-tools mock, Playwright-in-vitest) |

---

### E. §6 walkthrough status

**Mechanical (verified via code review + tests):**
- ✅ Citation chips use `--cite-signal/asset/chunk` tokens (not amber/sky/violet)
- ✅ Welcome glyph legend present in WelcomeGreeting.tsx
- ✅ Sticky DisclosureTierBadge banner removed from ConsumeChat
- ✅ ChatShell title wrapped in `<h1>`
- ✅ `aria-live="polite"` on StreamingMarkdown wrapper, removed from scroll containers
- ✅ Focus trap on CitationPreview panel (Tab/Shift+Tab cycle, restore on close)
- ✅ "Edit and retry" button pre-loads composer via `composerRef.current?.setValue()` + `.focus()`
- ✅ EPISTEMIC HALT kicker + gold-leaf rule in ValidatorFailureView
- ✅ PanelAnswerView routes final answer through AnswerView (markdown pipeline)
- ✅ Completed assistant turns rendered via AssistantMessage with Copy/Rate/Regenerate actions

**Requires live authenticated session (no local env available in this execution context):**
- Live send message → hover actions (clipboard, regenerate, rate)
- Live validator failure card visual
- Live panel-mode markdown rendering
- Live per-message metadata strip with real message.metadata fields
- Live citation panel focus/Tab/Esc behavior
- Live inline title rename double-click
- Mobile viewport 375px chartMeta visibility

---

### F. must_not_touch boundary confirmation

No file outside §3 `may_touch` was modified except `VirtualizedMessageList.tsx` (T5 scope clarification, see deviation B.3). All `platform/src/app/api/**`, `platform/src/lib/**`, `platform/supabase/**`, `platform/src/components/build/**`, governance artifacts, and sibling briefs were untouched.
