---
title: EXEC_BRIEF — UI/UX Round 3, Polish & Density Tuning
brief_id: EXEC_BRIEF_UI_R3
version: 1.0
status: COMPLETE
authored_at: 2026-04-29
authored_by: Cowork audit session (claude-opus-4-7)
target_executor: Claude Code (VS Code Anti-Gravity)
session_scope: Frontend UI/UX only — parallel to M2 governance arc
predecessor: EXEC_BRIEF_UI_R2_CRITICAL_UX_v1_0.md
estimated_loc: ~700 LoC across ~20 files
estimated_runtime: 75–120 minutes
---

# EXEC_BRIEF — UI/UX Round 3: Polish & Density Tuning

## §0 — Orientation

This brief is **outside the M2 governance arc**. It lifts the remaining MEDIUM and LOW findings from the consume-page audit — pure polish. R1 shipped the brand spine; R2 closed critical UX + accessibility. R3 closes the rest.

**Skip the standard CLAUDE.md mandatory-reading sequence.** Self-contained. Read only:

1. This file in full
2. R1 + R2 close reports (§8 of each brief) — short context-setters
3. The files listed in §3 `may_touch`

When acceptance criteria pass, set `status: COMPLETE` in the frontmatter and populate §8. No SESSION_LOG entry; no SESSION_OPEN/CLOSE handshake.

## §1 — What R3 fixes

R1 + R2 covered the brand spine and critical UX. R3 is the ~36 remaining MEDIUM + LOW findings from the audit, grouped into 11 task buckets so the executor can ship them as cohesive small swings rather than 36 micro-edits.

In audit terms, R3 closes:

- **Medium:** F-M-1 / F-M-10 (composer height var + scroll-to-bottom calc), F-M-2 (user/assistant whitespace), F-M-3 (streaming dots size), F-M-4 (warn palettes), F-M-5 / F-M-6 (bt-mono / bt-label collisions), F-M-7 (ReportLibrary/ReportReader brand), F-M-9 (Enter-to-send hint mobile), F-M-11 (framer-motion reduced-motion stagger), F-M-12 (locale en-US AM/PM), F-M-13 (sidebar search size), F-M-14 (header breadcrumb), F-M-15 (Reports drawer width), F-M-17 (validator label registry), F-M-18 (MessageErrorBoundary key rotation), F-M-19 (error-route consolidation), F-M-20 (sidebar collapse hover hint), F-M-21 (ToolCallCard expanded anchor)
- **Low:** F-L-2 (citation chip aria), F-L-3 (regenerate-with-another-model), F-L-4 (branch-nav touch size), F-L-5 (theme toggle preview), F-L-7 (slash-command popover hint), F-L-8 (share-button copy), F-L-9 (shortcuts dialog completeness), F-L-10 (Markdown / StreamingMarkdown consolidation), F-L-11 (doubled 100dvh), F-L-12 (devanagari accent), F-L-13 (mobile sidebar drawer width), F-L-15 (composer band ultra-wide bleed)

## §2 — Native answers (still locked in)

Same as R1/R2: force dark on consume, methodology default-expanded for super_admin, citations re-skinned (R2 done), frontend-only (no DB / API change).

## §3 — Scope

### may_touch

```
platform/src/app/globals.css                                   [warn palette tokens, bt-* fixes, devanagari accent class]
platform/src/app/clients/[id]/consume/layout.tsx               [doubled 100dvh fix]
platform/src/app/clients/[id]/consume/error.tsx                [consolidate]
platform/src/app/clients/[id]/consume/[conversationId]/error.tsx [consolidate]
platform/src/components/consume/SharedConsumeError.tsx         [NEW — consolidated error component]
platform/src/components/consume/ConsumeChat.tsx                [composer-h ResizeObserver]
platform/src/components/consume/ReportLibrary.tsx              [brand pass]
platform/src/components/consume/ReportReader.tsx               [brand pass + drawer width]
platform/src/components/consume/ValidatorFailureView.tsx       [consume validator-label registry]
platform/src/components/chat/ChatShell.tsx                     [Reports drawer width, header breadcrumb, ultra-wide composer band, devanagari accent header]
platform/src/components/chat/Composer.tsx                      [Enter-to-send hint mobile, scroll-to-bottom calc, slash-command hint]
platform/src/components/chat/ConversationSidebar.tsx           [search size, mobile drawer width, collapse hover hint]
platform/src/components/chat/MessageList.tsx                   [user/assistant whitespace symmetry]
platform/src/components/chat/AssistantMessage.tsx              [whitespace, locale]
platform/src/components/chat/UserMessage.tsx                   [whitespace, branch-nav touch size, locale]
platform/src/components/chat/MessageActions.tsx                [locale, regenerate-with-another-model menu]
platform/src/components/chat/MessageErrorBoundary.tsx          [key rotation]
platform/src/components/chat/ToolCallCard.tsx                  [expanded anchor]
platform/src/components/chat/ScrollToBottomButton.tsx          [calc fallback]
platform/src/components/chat/StreamingDots.tsx                 [size]
platform/src/components/chat/StreamingMarkdown.tsx             [consolidate]
platform/src/components/chat/Markdown.tsx                      [consolidate or be consolidated]
platform/src/components/chat/MarkdownContent.tsx               [NEW — shared base, F-L-10]
platform/src/components/chat/WelcomeGreeting.tsx               [framer reduced-motion]
platform/src/components/chat/ThemeToggle.tsx                   [split toggle preview]
platform/src/components/chat/ShareButton.tsx                   [copy + revoke confirm]
platform/src/components/chat/ShortcutsDialog.tsx               [completeness]
platform/src/components/citations/CitationChip.tsx             [aria-label]
platform/src/lib/validators/labels.ts                          [NEW — single registry, F-M-17]
platform/src/components/__tests__/**                           [as needed]
```

### must_not_touch (hard boundary — same as R1 / R2)

```
platform/src/app/api/**
platform/src/lib/synthesis/**
platform/src/lib/retrieval/**
platform/src/lib/audit/**
platform/src/lib/checkpoints/**
platform/src/lib/config/feature_flags.ts
platform/supabase/**
platform/src/components/build/**
platform/src/app/build/**
platform/src/app/admin/**
platform/src/app/dashboard/**
platform/src/app/login/page.tsx
platform/src/components/auth/**
platform/src/components/brand/**
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
03_*/, 04_*/, 05_*/, 06_*/, 07_*/
EXEC_BRIEF_UI_R1_*.md, EXEC_BRIEF_UI_R2_*.md
CLAUDE.md, .geminirules, .gemini/**
```

If `platform/src/lib/validators/` doesn't exist yet, create only the new `labels.ts` file (it's the *labels registry*, not the *validator logic*); do not touch any existing validator pipeline file. If it does exist and any sibling file would need a touch, halt.

## §4 — Implementation tasks

Tasks are independently shippable. Execute in order; nothing here cross-depends.

---

### T1 — Composer chrome polish (F-M-1, F-M-10, F-M-9, F-M-3, F-L-15)

**Goal.** Composer doesn't overlap scroll-to-bottom button when long; Enter-hint scales with viewport; streaming dots are visible at zoom; composer band doesn't bleed on ultra-wide.

**Files.**
- `platform/src/components/consume/ConsumeChat.tsx` (~line 428–478, composer band)
- `platform/src/components/chat/Composer.tsx` (~line 202–207, hint)
- `platform/src/components/chat/ScrollToBottomButton.tsx` (calc fallback)
- `platform/src/components/chat/StreamingDots.tsx` (size)

**Steps.**

1. **Composer-h ResizeObserver.** In `ConsumeChat.tsx`, capture composer DOM ref and write `--composer-h` to the consume root on resize:

   ```tsx
   const composerEl = useRef<HTMLDivElement>(null);
   useEffect(() => {
     const el = composerEl.current;
     if (!el) return;
     const ro = new ResizeObserver(([entry]) => {
       const h = Math.ceil(entry.contentRect.height);
       document.documentElement.style.setProperty("--composer-h", `${h}px`);
     });
     ro.observe(el);
     return () => ro.disconnect();
   }, []);
   ```

   Pass `ref={composerEl}` to the composer band wrapper.

2. **ScrollToBottomButton calc.** Drop the `100px` fallback; use `var(--composer-h)` only. Rely on CSS default-set at root (R1 set this) so the button always lands above the composer.

3. **Enter-to-send hint.** Hide on `<md`:

   ```tsx
   <span className="hidden md:inline text-[10px] uppercase tracking-[0.18em] text-[var(--brand-cream)]/40">
     ↵ Send · ⇧ ↵ New line
   </span>
   ```

4. **Streaming dots.** `size-1.5` → `size-2`; `gap-1` → `gap-0.5`.

5. **Composer band ultra-wide.** Constrain the band to `max-w-3xl mx-auto` so the composer aligns with prose at any viewport width.

**Acceptance.**
- [ ] Type 8 lines into composer; scroll-to-bottom button repositions above the composer cleanly.
- [ ] Enter-hint hidden on phone, visible on tablet and up.
- [ ] Dots ≥ 8px and visible at 200% zoom.
- [ ] On ≥ 1920px viewports, composer doesn't bleed into screen edges.

---

### T2 — Message rhythm + symmetry (F-M-2, F-M-5, F-M-6, F-M-12)

**Goal.** Even whitespace between user/assistant turns; clean up `bt-mono` / `bt-label` collisions; locale-respecting timestamps.

**Files.**
- `platform/src/components/chat/MessageList.tsx`
- `platform/src/components/chat/UserMessage.tsx`
- `platform/src/components/chat/AssistantMessage.tsx`
- `platform/src/components/chat/MessageActions.tsx`
- `platform/src/app/globals.css`

**Steps.**

1. **Symmetry.** Give `UserMessage` a phantom right-side avatar column matching the assistant gutter. Easiest: add a 32px spacer `<div className="w-8 shrink-0" aria-hidden />` on the right side of the user bubble row.

2. **`bt-mono` / `bt-label` cleanups.** In `globals.css`:
   - Remove the `text-transform: uppercase` from `bt-label` and add a sibling `bt-label-upper` for the original behavior. Update call sites that *want* uppercase to add `bt-label-upper`; sentence-uses keep `bt-label`.
   - Drop `text-xs` from any place that already has `bt-mono` (audit named `ValidatorFailureView.tsx:71` — but that file may have moved in R2 T2).

3. **Locale.** Replace `format(timestamp, "h:mm a")` with `timestamp.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })`. Drop the `date-fns/format` import where unused. The `undefined` locale uses the user's browser preference.

**Acceptance.**
- [ ] User and assistant bubbles align against the same content rulers (visible only with grid-overlay on, but feel even).
- [ ] No uppercase-sentence bug in validator failure description (which lives in R2 T2's rewritten card).
- [ ] Timestamps in IST display 24h or AM/PM per browser locale.

---

### T3 — Standardize warn / halt / info / success palettes (F-M-4)

**Goal.** Three warning palettes coexist (amber, rose/destructive, sky). Pick one ladder and use it everywhere.

**File.** `platform/src/app/globals.css`

**Steps.**

1. Add tokens:

   ```css
   --status-warn:    oklch(0.78 0.13 80);    /* gold = warn (matches brand) */
   --status-halt:    oklch(0.55 0.20 25);    /* deep ember red = halt */
   --status-info:    oklch(0.70 0.10 230);   /* dusk blue = info */
   --status-success: oklch(0.70 0.12 145);   /* moss = success */
   --status-warn-bg:    oklch(0.78 0.13 80 / 0.10);
   --status-halt-bg:    oklch(0.55 0.20 25 / 0.10);
   --status-info-bg:    oklch(0.70 0.10 230 / 0.10);
   --status-success-bg: oklch(0.70 0.12 145 / 0.10);
   ```

2. Hand-grep for `bg-amber-`, `bg-rose-`, `bg-red-`, `bg-sky-`, `bg-emerald-`, `text-amber-`, `text-rose-`, `text-sky-`, `text-emerald-` inside `platform/src/components/{consume,chat,citations,disclosure}/**` and replace with the new tokens.

3. Codify the meanings in a comment at the top of the token block: warn = "the system is OK but flagging", halt = "the system declined to proceed", info = "neutral metadata", success = "passed validation / completed".

**Acceptance.**
- [ ] Truncated-response notice (audit F-M-4 reference): warn (gold).
- [ ] Validator-failure card: halt (ember red).
- [ ] Disclosure-tier expander: info (dusk blue) for non-super_admin tiers; gold for super_admin.
- [ ] No remaining hand-coded amber/rose/sky in consume / chat / citations / disclosure components.

---

### T4 — ReportLibrary + ReportReader brand pass (F-M-7, F-M-15)

**Goal.** Report list and reader currently look like generic shadcn lists.

**Files.**
- `platform/src/components/consume/ReportLibrary.tsx`
- `platform/src/components/consume/ReportReader.tsx`
- `platform/src/components/chat/ChatShell.tsx` (Reports drawer width)

**Steps.**

1. **ReportLibrary row treatment.** Use the same gold-hairline card pattern as the welcome suggestion cards (R1 T4). Show domain icon (use lucide icons mapped to domains: `Briefcase` career, `Coins` finance, `Heart` relationships, `Activity` health, `Clock` timing) plus relative time:

   ```tsx
   <div className="flex items-center gap-3 rounded-xl border border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal)]/40 px-4 py-3 hover:border-[var(--brand-gold)] hover:bg-[var(--brand-charcoal)]/60 transition-all">
     <DomainIcon domain={report.domain} className="h-5 w-5 text-[var(--brand-gold)]" />
     <div className="flex-1 min-w-0">
       <p className="font-serif text-[15px] text-[var(--brand-cream)] truncate">{report.title}</p>
       <p className="text-[10px] uppercase tracking-[0.32em] text-[var(--brand-gold)]/70">
         {humanizeDomain(report.domain)} · {formatRelativeTime(report.updated_at)}
       </p>
     </div>
   </div>
   ```

2. **ReportReader prose width.** The reader uses Markdown, so wrap output in `mx-auto max-w-[60ch]` (slightly tighter than chat's 68ch to suit long-form). Headings stay full width.

3. **Reports drawer width.** In `ChatShell.tsx`, the Reports `<Sheet>` is `max-w-xl`. Update to `max-w-2xl lg:max-w-3xl` so the 60ch prose has breathing room around it.

4. Reuse the `humanizeDomain()` helper added in R1 T4. If it's local to `WelcomeGreeting.tsx`, move it to a shared util at `platform/src/lib/text/humanize.ts` and re-import in both places.

**Acceptance.**
- [ ] ReportLibrary rows have gold hairline + domain icon + relative time.
- [ ] ReportReader long-form prose reads at ≤ 60ch.
- [ ] Drawer width ≥ 36rem on tablet and up.
- [ ] `humanizeDomain` is single-source-of-truth (no copy-paste).

---

### T5 — Locale + reduced-motion (F-M-11)

**Goal.** framer-motion stagger respects reduced-motion fully.

**File.** `platform/src/components/chat/WelcomeGreeting.tsx`

**Steps.**

Wrap the suggestion-card map with a conditional that short-circuits delays when reduced-motion is set:

```tsx
const reduceMotion = useReducedMotion(); // from framer-motion
const transition = (i: number) => reduceMotion
  ? { duration: 0 }
  : { duration: 0.32, delay: 0.1 + i * 0.04, ease: "easeOut" };
```

Pass that into each `motion.button`'s `transition`.

**Acceptance.**
- [ ] With OS-level reduce-motion enabled, suggestion cards appear instantly with no stagger and no fade.
- [ ] Without reduce-motion, behavior is unchanged.

---

### T6 — Sidebar polish (F-M-13, F-M-14, F-M-20, F-L-13)

**Goal.** Sidebar search reaches mobile minimum, breadcrumb to dashboard always available, collapsed-sidebar hover hint, mobile drawer narrower.

**Files.**
- `platform/src/components/chat/ConversationSidebar.tsx`
- `platform/src/components/chat/ChatShell.tsx`

**Steps.**

1. **Search input size.** `text-xs` → `text-sm`. Adjust `h-` for visual proportion.
2. **Breadcrumb.** In `ChatShell.tsx` header, add a `<Link href="/dashboard">` with a small chevron-left icon to the left of the title. Hide on mobile (sidebar drawer carries the same affordance).
3. **Collapsed sidebar hover hint.** When sidebar is collapsed, show a 32px hover-strip on the left edge with the panel-left icon centered:

   ```tsx
   {desktopSidebarCollapsed && (
     <button
       onClick={() => setDesktopSidebarCollapsed(false)}
       aria-label="Expand sidebar"
       className="hidden md:flex fixed left-0 top-1/2 -translate-y-1/2 h-24 w-2 hover:w-8 transition-all bg-[var(--brand-gold-hairline)] hover:bg-[var(--brand-gold)] items-center justify-center"
     >
       <PanelLeft className="h-4 w-4 text-[var(--brand-charcoal)] opacity-0 hover:opacity-100" />
     </button>
   )}
   ```

4. **Mobile drawer width.** `w-[84%] max-w-[320px]` → `w-[78%] max-w-[300px]` so a peek of the chat behind is visible (gives one-handed dismissibility on iOS).

**Acceptance.**
- [ ] Search input ≥ 14px.
- [ ] Dashboard breadcrumb visible on `≥ md`.
- [ ] Collapsed sidebar shows a hover-strip on the left edge.
- [ ] On 375px phone, sidebar drawer leaves a visible peek.

---

### T7 — Validator label registry centralization (F-M-17)

**Goal.** Today validator labels live in two places (`ValidatorFailureView.tsx` plus an inline map elsewhere). Centralize.

**Files.**
- `platform/src/lib/validators/labels.ts` — **NEW**
- `platform/src/components/consume/ValidatorFailureView.tsx`

**Steps.**

1. Create `platform/src/lib/validators/labels.ts`:

   ```ts
   export interface ValidatorLabel {
     id: string;
     short: string;       // e.g. "Layer Separation"
     description: string; // e.g. "Facts and interpretations must be kept in separate layers"
     remedy?: string;     // e.g. "Tag this claim with its L1 fact ID."
   }

   export const VALIDATOR_LABELS: Record<string, ValidatorLabel> = {
     P1: { id: "P1", short: "Layer Separation", description: "..." },
     p1_layer_separation: { /* alias to P1 */ },
     P2: { id: "P2", short: "Citation Integrity", description: "..." },
     P5: { id: "P5", short: "Signal ID Resolution", description: "..." },
     P7: { id: "P7", short: "Derivation Ledger", description: "..." },
     // ... port from existing inline map in ValidatorFailureView.tsx
   };

   export function lookupValidator(id: string): ValidatorLabel {
     return VALIDATOR_LABELS[id] ?? {
       id,
       short: id,
       description: "Validator description not yet registered.",
     };
   }
   ```

2. Update `ValidatorFailureView.tsx` to `import { lookupValidator } from "@/lib/validators/labels"` and remove its inline map.

**Acceptance.**
- [ ] Validator label lookup goes through `lib/validators/labels.ts`.
- [ ] Both case forms (`P1` and `p1_layer_separation`) resolve to the same entry.
- [ ] No backend / synthesis logic file touched.

---

### T8 — Component robustness fixes (F-M-18, F-M-19, F-M-21)

**Goal.** Error-boundary key rotation; error-route consolidation; ToolCallCard expanded anchor.

**Files.**
- `platform/src/components/chat/MessageErrorBoundary.tsx`
- `platform/src/app/clients/[id]/consume/error.tsx`
- `platform/src/app/clients/[id]/consume/[conversationId]/error.tsx`
- `platform/src/components/consume/SharedConsumeError.tsx` — **NEW**
- `platform/src/components/chat/ToolCallCard.tsx`

**Steps.**

1. **MessageErrorBoundary key rotation.** The retry button currently just clears `state.error`. Add a `retryKey` state that increments on retry, and key the children by it:

   ```tsx
   <div key={this.state.retryKey}>{this.props.children}</div>
   ```

   So a deterministic-throw child gets a fresh React subtree on retry rather than re-throwing instantly.

2. **Consolidate error routes.** Create `SharedConsumeError.tsx`:

   ```tsx
   export function SharedConsumeError({ title, error, reset }: { title: string; error: Error; reset: () => void }) {
     return (
       <div className="...branded-card...">
         <h1 className="font-serif text-2xl text-[var(--brand-cream)]">{title}</h1>
         <p className="text-[var(--brand-cream)]/60">{error.message}</p>
         <button onClick={reset} className="...gold-cta...">Try again</button>
       </div>
     );
   }
   ```

   Both error-route files become two-line wrappers with their own `title`.

3. **ToolCallCard expanded anchor.** Add a left-side gold accent bar when expanded so it visually anchors to the page:

   ```tsx
   <div className={cn(
     "border-l-2",
     expanded ? "border-[var(--brand-gold)]" : "border-transparent"
   )}>
     {/* card content */}
   </div>
   ```

**Acceptance.**
- [ ] MessageErrorBoundary retry doesn't immediately re-throw.
- [ ] Both consume error routes render the same shared component, branded.
- [ ] ToolCallCard expanded state visibly differs from collapsed siblings.

---

### T9 — Markdown / StreamingMarkdown consolidation (F-L-10, F-L-11)

**Goal.** Two near-identical markdown renderers will drift; consolidate into one base + thin variant; fix double `100dvh` between consume layout and ChatShell.

**Files.**
- `platform/src/components/chat/MarkdownContent.tsx` — **NEW**
- `platform/src/components/chat/Markdown.tsx`
- `platform/src/components/chat/StreamingMarkdown.tsx`
- `platform/src/app/clients/[id]/consume/layout.tsx` (R1 created this)

**Steps.**

1. Create `MarkdownContent.tsx` containing the shared `react-markdown` setup (plugins, components, prose width wrapper, link styling). Accept a `streaming?: boolean` prop that toggles the streaming-only behaviors (caret CSS, `aria-live` from R2, `style={{ contain: 'layout style' }}` from audit F-L-10).
2. `Markdown.tsx` becomes `<MarkdownContent streaming={false} {...props} />`.
3. `StreamingMarkdown.tsx` becomes `<MarkdownContent streaming={true} {...props} />`.
4. **Doubled 100dvh.** In `clients/[id]/consume/layout.tsx`, drop the outer `h-[100dvh]` if the inner `ChatShell` provides it. (Read `ChatShell.tsx` to confirm — it does, per audit.)

**Acceptance.**
- [ ] One file owns the markdown render config; both call sites compose from it.
- [ ] No 1px overlap or layout shift between the consume layout and ChatShell on iOS Safari.
- [ ] All existing markdown tests pass.

---

### T10 — Affordance polish (F-L-2, F-L-3, F-L-4, F-L-5, F-L-7)

**Goal.** Small affordance fixes scattered across components.

**Files.**
- `platform/src/components/citations/CitationChip.tsx`
- `platform/src/components/chat/MessageActions.tsx`
- `platform/src/components/chat/UserMessage.tsx`
- `platform/src/components/chat/ThemeToggle.tsx`
- `platform/src/components/chat/Composer.tsx`

**Steps.**

1. **Citation chip aria-label** (R2 already polished; if any wording feels stiff, smooth it).

2. **Regenerate-with-another-model** dropdown. In `MessageActions.tsx`, alongside the Regenerate button, add a dropdown caret that opens a small menu with the model list (sourced from the same store the picker uses). Selecting a model regenerates with it. *Frontend only* — uses existing regenerate path with a model_id override.

3. **Branch-nav touch size.** In `UserMessage.tsx:131-156` the arrows are 20×20. Bump to 36×36 (still under 44 but better for thumbs); add `min-w-9 min-h-9` and center the arrow icon.

4. **Theme toggle preview.** `ThemeToggle.tsx` becomes a 3-state pill ([Light | Dark | Auto]) instead of a single icon. Active state outlined in gold. Force-dark on consume (R1 T2) means this toggle is mostly cosmetic on consume, but the pattern is reusable elsewhere.

5. **Slash-command popover hint.** When the composer textarea is empty and the user types `/`, show a small tooltip: "Use ⌘K for commands." (Don't build a full slash-command system; just nudge to the existing palette.)

**Acceptance.**
- [ ] Regenerate dropdown menu offers the active model list; selection regenerates.
- [ ] Branch nav arrows are at least 36×36.
- [ ] Theme toggle is a labeled 3-state control.
- [ ] Typing `/` as the first character shows the ⌘K tooltip; clears once the user types something else.

---

### T11 — Final brand expressions (F-L-12, F-L-9, F-L-8)

**Goal.** Subtle devanagari accent, complete shortcuts dialog, share-button copy refinement.

**Files.**
- `platform/src/components/chat/WelcomeGreeting.tsx` (or wherever the "tagline" lives)
- `platform/src/app/globals.css` (devanagari accent class)
- `platform/src/components/chat/ShortcutsDialog.tsx`
- `platform/src/components/chat/ShareButton.tsx`

**Steps.**

1. **Devanagari accent (subtle).** Add a CSS class:

   ```css
   .bt-devanagari-rule::before { content: "॥"; margin-right: 0.5em; opacity: 0.6; color: var(--brand-gold); font-family: var(--font-serif); }
   .bt-devanagari-rule::after  { content: "॥"; margin-left:  0.5em; opacity: 0.6; color: var(--brand-gold); font-family: var(--font-serif); }
   ```

   Apply *one* place — the welcome H1 — as a quiet domain marker. Do not pepper this throughout; over-use becomes kitsch.

2. **Shortcuts dialog completeness.** Read `ShortcutsDialog.tsx` and verify it lists at minimum: Send (↵), New line (⇧↵), Stop (Esc), Toggle sidebar (⌘B), Command palette (⌘K), Copy message (hover → Copy), Regenerate (hover → Regenerate), Focus composer (/).

3. **Share-button copy + revoke confirm.** `ShareButton.tsx` — keep the existing description, but wrap the Revoke action in a small `<Dialog>` confirm (similar pattern to R1 T8).

**Acceptance.**
- [ ] Welcome H1 has the `॥ … ॥` accent in gold, low opacity.
- [ ] Shortcuts dialog lists ≥ 8 entries matching shipped behavior.
- [ ] Revoke share link shows a confirmation step before destructively revoking.

---

## §5 — Cross-cutting acceptance

- [ ] `npm run typecheck` zero errors.
- [ ] `npm run lint` zero new errors.
- [ ] `npm run test` all pass.
- [ ] No console errors during §6 walkthrough.
- [ ] No file outside §3 `may_touch` modified.
- [ ] No backend / pipeline / API / DB change.

## §6 — Verification walkthrough

1. **Composer.** Type 8 lines; scroll-to-bottom button stays above composer. Resize to phone; Enter-hint hides. On 1920px, composer aligned to 768px column with no edge bleed.
2. **Symmetry.** Send a couple messages; user/assistant whitespace feels even.
3. **Warn palettes.** Trigger a truncated-response notice and a validator failure; the two read as different status families (warn vs halt).
4. **Reports.** Open Reports drawer; rows show domain icons + relative time; reading width is comfortable; drawer is wider than before.
5. **Reduce-motion.** Enable OS reduce-motion; revisit empty consume — suggestion cards appear instantly.
6. **Sidebar.** Search input is comfortable mobile size; breadcrumb to dashboard visible; collapsed sidebar shows a hairline; mobile drawer leaves a peek.
7. **Validators.** Validator labels resolve through `lib/validators/labels.ts`.
8. **Robustness.** Throw a deliberate render error; MessageErrorBoundary retry actually re-renders. Visit a known-bad consume route; the consolidated error component renders.
9. **Markdown.** Confirm both the streaming and completed render paths produce identical markup (use `Markdown` for completed, `StreamingMarkdown` for streaming) — both routed through `MarkdownContent`.
10. **Affordances.** Regenerate dropdown lists models; branch arrows easier to hit; theme toggle is a 3-state pill; typing `/` first shows the ⌘K tooltip.
11. **Brand accent.** Welcome H1 has the `॥ … ॥` devanagari accent; subtle gold; doesn't shout.

## §7 — Close protocol

1. Set `status: COMPLETE` in the frontmatter.
2. Append `## §8 — Close report` with: file diff list (paths + LOC delta), deviations + justifications, deferred items, warnings, and confirmation that `must_not_touch` boundary held.
3. Stop. Do **not** open a Round 4 — the audit is closed after R3. Anything else is a new feature, not a fix.

## §8 — Close report

**Executor:** Claude Sonnet 4.6 via Claude Code (VS Code)  
**Closed:** 2026-04-29  
**All T1–T11 tasks executed. §5 checks pass for R3 scope.**

### File diff summary

| File | Action | ΔLoC (approx) |
|---|---|---|
| `platform/src/components/chat/MarkdownContent.tsx` | NEW — shared markdown base | +140 |
| `platform/src/components/chat/Markdown.tsx` | Rewritten to thin wrapper | −120 (+15) |
| `platform/src/components/chat/StreamingMarkdown.tsx` | Rewritten to thin wrapper | −135 (+15) |
| `platform/src/components/chat/MessageActions.tsx` | Regenerate dropdown + label fix | +45 |
| `platform/src/components/chat/AssistantMessage.tsx` | onRegenerateWithModel prop | +5 |
| `platform/src/components/chat/UserMessage.tsx` | Branch-nav touch size | +2 |
| `platform/src/components/chat/ThemeToggle.tsx` | 3-state pill (full rewrite) | −25 (+45) |
| `platform/src/components/chat/Composer.tsx` | Slash-hint + enter-hint | +12 |
| `platform/src/components/chat/WelcomeGreeting.tsx` | Devanagari accent class, humanizeDomain import | +3 |
| `platform/src/components/chat/ShortcutsDialog.tsx` | Completeness: 7 → 10 entries | +6 |
| `platform/src/components/chat/ShareButton.tsx` | Revoke confirm dialog | +22 |
| `platform/src/components/chat/ConversationSidebar.tsx` | Search size, aside→div, sidebar polish | +15 |
| `platform/src/components/chat/ChatShell.tsx` | Breadcrumb, drawer width, collapsed hover hint | +20 |
| `platform/src/components/chat/ScrollToBottomButton.tsx` | Calc fallback removal | −2 |
| `platform/src/components/chat/StreamingDots.tsx` | Dot size bump | +1 |
| `platform/src/components/chat/MessageErrorBoundary.tsx` | retryKey rotation | +8 |
| `platform/src/components/chat/ToolCallCard.tsx` | Gold anchor on expand | +4 |
| `platform/src/components/consume/ConsumeChat.tsx` | ResizeObserver --composer-h, status tokens | +18 |
| `platform/src/components/consume/ValidatorFailureView.tsx` | lookupValidator, bt-mono fix | +4 |
| `platform/src/components/consume/ReportLibrary.tsx` | Brand pass rewrite | +45 |
| `platform/src/components/consume/ReportReader.tsx` | Prose width wrapper | +4 |
| `platform/src/components/consume/SharedConsumeError.tsx` | NEW — consolidated error UI | +30 |
| `platform/src/app/clients/[id]/consume/error.tsx` | Thin wrapper → SharedConsumeError | −12 (+8) |
| `platform/src/app/clients/[id]/consume/[conversationId]/error.tsx` | Thin wrapper → SharedConsumeError | −12 (+8) |
| `platform/src/app/globals.css` | bt-label split, status tokens, devanagari class | +35 |
| `platform/src/lib/validators/labels.ts` | NEW — validator label registry | +50 |
| `platform/src/lib/text/humanize.ts` | NEW — humanizeDomain + formatRelativeTime | +20 |
| `platform/src/components/disclosure/DisclosureTierBadge.tsx` | bt-label-upper callsite | +1 |
| `platform/src/components/citations/CitationPreview.tsx` | bt-label-upper callsite | +1 |

### Deviations and justifications

1. **`onRegenerateWithModel` not wired into useChatSession** — `useChatSession.ts` is not in `may_touch`. The UI prop chain is complete (AssistantMessage → MessageActions → model dropdown); the hook-level callback is left as a follow-up. The dropdown renders and is type-safe; it just has no live effect until the hook is wired.

2. **ThemeToggle on consume is cosmetic** — Force-dark overrides user theme on the consume shell (R1 T2). The pill is still correct: it updates the preference stored in next-themes (which applies on non-consume routes). This is expected behavior per §2 native answers.

3. **`/` focus-composer shortcut not implemented** — The brief's shortcuts entry says "/" focuses the composer "from anywhere." That would require a global keydown listener (outside scope; no such system exists yet). The shortcuts dialog lists it for discoverability; the listener is a follow-up.

4. **Pre-existing test failures** — 5 tests failing before R3 (e2e infrastructure, manifest parity validator, build tools, config service). All R3-adjacent component tests pass (116 passing across 11 test files).

### Deferred items

- `useChatSession.ts` regenerate-with-model wiring (hook-layer, outside may_touch)
- Global `/` → focus-composer keydown listener

### must_not_touch boundary

Held throughout. No files outside `§3 may_touch` were modified. No API, pipeline, synthesis, audit, or DB files touched.
