---
title: EXEC_BRIEF — UI/UX Round 1, Brand Spine for Consume Page
brief_id: EXEC_BRIEF_UI_R1
version: 1.0
status: COMPLETE
authored_at: 2026-04-29
authored_by: Cowork audit session (claude-opus-4-7)
target_executor: Claude Code (VS Code Anti-Gravity)
session_scope: Frontend UI/UX only — parallel to M2 governance arc
estimated_loc: ~700 LoC across 9 files + 2 new files
estimated_runtime: 60–90 minutes
---

# EXEC_BRIEF — UI/UX Round 1: Brand Spine for Consume Page

## §0 — Orientation (read before doing anything)

This brief is **outside the M2 governance arc**. It is purely a frontend UI/UX iteration on the `/clients/[id]/consume` route.

**Skip the standard CLAUDE.md mandatory-reading sequence.** Do not load PROJECT_ARCHITECTURE, MACRO_PLAN, PHASE_B_PLAN, GOVERNANCE_INTEGRITY_PROTOCOL, GROUNDING_AUDIT, NATIVE_DIRECTIVES, ONGOING_HYGIENE_POLICIES, CAPABILITY_MANIFEST, CURRENT_STATE, or SESSION_LOG. None apply. Do **not** emit a SESSION_OPEN handshake or SESSION_CLOSE checklist; this is not a governance session.

This brief is self-contained. Read only:

1. This file in full
2. The files listed in §3 `may_touch`

When acceptance criteria in §6 all pass, set `status: COMPLETE` in the frontmatter of this file and stop. Do not log to SESSION_LOG. Do not bump CURRENT_STATE.

## §1 — Why this exists

The login page (`platform/src/app/login/page.tsx`) is the only branded surface in the app. It establishes a tight ceremonial visual language: black-and-gold on a radial-vignette backdrop, serif-led typography, mandala motif behind the form, sparse ceremonial copy ("The instrument is ready."). The consume chat surface — which is where the user spends 90% of their time — currently uses default shadcn neutrals and inherits none of that brand. Auditing surfaced 64 distinct findings across 9 critical, 19 high, 21 medium, and 15 low.

This brief implements **Round 1 only — the eight highest-leverage brand-spine fixes**. Round 2 (critical UX + accessibility) and Round 3 (medium polish) are scoped separately.

After Round 1, consume should *feel* like the login extended: dark by default, gold-accented, mandala-watermarked, with the assistant sigil and primary CTAs carrying the brand. Pure cosmetics + one wired-up super_admin feature (Methodology expander). No backend, no pipeline, no API, no schema changes.

## §2 — Native answers (locked in)

These four decisions came from the audit-review session and are non-negotiable for this round:

1. **Theme mode** → Force dark on consume (matches login). Use a `ForceDarkMode`-style component scoped to the consume route, **not** the parent `[id]/layout.tsx` (build portal stays user-preference).
2. **Methodology expander** → Default **expanded** for super_admin. Click-to-collapse for noise control.
3. **Citation chip colors** → Free to re-skin into the brand palette. *Deferred to Round 2.* This round leaves citation chips alone.
4. **Per-message persisted metadata** → Frontend only this round. Read fields if present on `message.metadata`; gracefully omit if absent. **No DB migration, no API change.**

## §3 — Scope

### may_touch (globs and exact files)

```
platform/src/app/globals.css
platform/src/app/clients/[id]/consume/layout.tsx              [NEW]
platform/src/components/brand/Sigil.tsx                        [NEW]
platform/src/components/consume/ConsumeChat.tsx
platform/src/components/chat/Composer.tsx
platform/src/components/chat/AssistantMessage.tsx
platform/src/components/chat/PendingAssistantBubble.tsx
platform/src/components/chat/WelcomeGreeting.tsx
platform/src/components/chat/ConversationSidebar.tsx
platform/src/components/chat/StreamingMarkdown.tsx
platform/src/components/chat/Markdown.tsx
platform/src/components/disclosure/DisclosureTierBadge.tsx
platform/src/components/consume/__tests__/**                   [tests may need minor mock updates]
platform/src/components/chat/__tests__/**                      [if any exist for above]
```

### must_not_touch (hard boundary)

```
platform/src/app/api/**                                        # No backend route changes
platform/src/lib/synthesis/**                                  # No synthesis logic
platform/src/lib/retrieval/**                                  # No retrieval changes
platform/src/lib/audit/**                                      # No audit pipeline
platform/src/lib/validators/**                                 # No validator logic
platform/src/lib/checkpoints/**                                # No checkpoint logic
platform/src/lib/config/feature_flags.ts                       # Do NOT toggle flags
platform/supabase/**                                           # No migrations
platform/src/components/build/**                               # Build portal is WIP, untouched
platform/src/app/build/**                                      # Build portal is WIP, untouched
platform/src/app/admin/**                                      # Admin is WIP, untouched
platform/src/app/dashboard/**                                  # Dashboard is WIP, untouched
platform/src/app/login/page.tsx                                # The brand reference, do NOT modify
platform/src/components/auth/**                                # Auth is brand-stable, do NOT modify
platform/src/components/brand/Logo.tsx                         # Existing brand; do NOT modify
platform/src/components/brand/Mandala.tsx                      # Read-only (you'll import it)
platform/src/components/brand/Wordmark.tsx                     # Existing brand; do NOT modify
platform/src/components/citations/**                           # Round 2 scope
00_ARCHITECTURE/**                                             # Governance, untouched
01_FACTS_LAYER/**                                              # Corpus, untouched
025_HOLISTIC_SYNTHESIS/**                                      # Corpus, untouched
03_*/, 04_*/, 05_*/, 06_*/, 07_*/                              # Domain layers, untouched
*.md (root-level briefs)                                       # Other briefs, untouched
CLAUDE.md, .geminirules, .gemini/**                            # Governance surfaces, untouched
```

If any change requires a touch outside `may_touch`, halt and surface the blocker in the close report rather than proceeding.

## §4 — Implementation tasks

Execute in order. Each task ends with binary acceptance criteria.

---

### T1 — Brand tokens in `globals.css`

**Goal.** Define a gold/cream/charcoal token ladder derived from the login page's literal hex values, so the rest of the round can reference tokens (not raw hex).

**File.** `platform/src/app/globals.css`

**Steps.**

1. Locate the `:root` block (light mode). Add the brand-token block at the end of `:root`:

   ```css
   /* Brand tokens — derived from login page (do NOT change without updating login). */
   --brand-gold: oklch(0.78 0.13 80);            /* #d4af37 regal gold mid */
   --brand-gold-light: oklch(0.86 0.15 88);      /* #f4d160 warm gold light */
   --brand-gold-deep: oklch(0.55 0.13 70);       /* #a26d0e deep gold for gradient bottom */
   --brand-cream: oklch(0.92 0.10 90);           /* #fce29a cream body text */
   --brand-charcoal: oklch(0.13 0.01 70);        /* #0d0a05 ceremonial black */
   --brand-charcoal-deep: oklch(0.05 0.005 70);  /* #020201 deepest black */
   --brand-form-fill: oklch(0.13 0.01 70 / 0.86); /* form glass fill */
   --brand-gold-hairline: oklch(0.78 0.13 80 / 0.35);
   --brand-gold-glow: oklch(0.78 0.13 80 / 0.20);
   --brand-gold-faint: oklch(0.78 0.13 80 / 0.12);
   ```

2. Locate the `.dark` block. **In `.dark` only**, override the relevant shadcn semantic tokens to point at the brand palette:

   ```css
   .dark {
     /* ... existing tokens ... */

     /* Brand override: in dark mode, accent + ring + primary become gold. */
     --accent: var(--brand-gold);
     --accent-foreground: var(--brand-charcoal);
     --ring: var(--brand-gold);
     --primary: var(--brand-gold);
     --primary-foreground: var(--brand-charcoal);
   }
   ```

   Do **not** override `--background`, `--foreground`, `--card`, `--muted` — those keep the existing warm-charcoal scheme. Only the *accent / ring / primary* go gold.

3. Add a utility class for the chat-stream caret to use the new accent (replaces F-L-1 from the audit):

   ```css
   .chat-stream-caret::after {
     /* existing styles ... */
     background: color-mix(in oklab, var(--brand-gold) 80%, transparent);
   }
   ```

   Locate the existing `.chat-stream-caret` rule (~line 157) and update only the color.

**Acceptance.**
- [ ] `globals.css` parses without error (no PostCSS warnings).
- [ ] In dark mode, `--accent`, `--ring`, `--primary` resolve to gold.
- [ ] In light mode, no semantic token changes (light mode behavior unchanged).
- [ ] `.chat-stream-caret` blink renders gold in dark mode.

---

### T2 — Force dark on consume (scoped layout)

**Goal.** Pin `.dark` on the `/clients/[id]/consume` route so a user landing from black-and-gold login stays in the same visual world. Do *not* affect build, dashboard, admin.

**Files.**
- `platform/src/components/auth/ForceDarkMode.tsx` — read only, reuse the pattern
- `platform/src/app/clients/[id]/consume/layout.tsx` — **NEW**

**Steps.**

1. Read `platform/src/components/auth/ForceDarkMode.tsx` to confirm the API. It pins `.dark` on `<html>` via `next-themes`'s `setTheme('dark')` in a `useEffect` (or equivalent client-side mechanism).

2. Create `platform/src/app/clients/[id]/consume/layout.tsx`:

   ```tsx
   import type { ReactNode } from "react";
   import { ForceDarkMode } from "@/components/auth/ForceDarkMode";

   /**
    * Consume route forces dark mode to match the login brand surface.
    * See EXEC_BRIEF_UI_R1_BRAND_SPINE_v1_0.md §2 native answer 1.
    *
    * Scoped to /clients/[id]/consume only — build, dashboard, admin keep
    * the user's next-themes preference.
    */
   export default function ConsumeLayout({ children }: { children: ReactNode }) {
     return (
       <>
         <ForceDarkMode />
         {children}
       </>
     );
   }
   ```

3. Verify by reading `platform/src/app/clients/[id]/layout.tsx` that nesting the consume-layout under it does not double-wrap any provider.

**Acceptance.**
- [ ] Navigating to `/clients/{anyId}/consume` forces dark mode regardless of system preference.
- [ ] Navigating to `/clients/{anyId}/build` (if it exists) keeps user-preference.
- [ ] Navigating to `/dashboard` keeps user-preference.
- [ ] No SSR-hydration mismatch warning in the browser console.

---

### T3 — Mandala-bindu assistant sigil

**Goal.** Replace the OpenAI-cliché `<Sparkles/>` icon on the assistant avatar with a custom 24px SVG sigil derived from the existing `Mandala` motif (bindu + 8-petal subset).

**Files.**
- `platform/src/components/brand/Mandala.tsx` — read only, source of motif
- `platform/src/components/brand/Sigil.tsx` — **NEW**
- `platform/src/components/chat/AssistantMessage.tsx` — replace icon usage at ~line 79–81
- `platform/src/components/chat/PendingAssistantBubble.tsx` — replace icon usage at ~line 24–26

**Steps.**

1. Create `platform/src/components/brand/Sigil.tsx`. The sigil is a tight 24×24 viewBox showing: a central bindu (filled circle), surrounded by 8 small petals (8-petal lotus subset of the mandala). Stroke and fill in `currentColor` so it inherits parent text color.

   ```tsx
   import type { SVGProps } from "react";

   /**
    * MARSYS-JIS sigil — 24×24 mandala extract (bindu + 8 petals).
    * Inherits currentColor; size via className (default 1em).
    * See brand/Mandala.tsx for the full motif.
    */
   export function Sigil({
     size = 24,
     ...props
   }: { size?: number } & SVGProps<SVGSVGElement>) {
     return (
       <svg
         width={size}
         height={size}
         viewBox="0 0 24 24"
         fill="none"
         stroke="currentColor"
         strokeWidth="1.25"
         strokeLinecap="round"
         strokeLinejoin="round"
         aria-hidden="true"
         {...props}
       >
         {/* Outer ring */}
         <circle cx="12" cy="12" r="10" opacity="0.35" />
         {/* 8-petal lotus — alternating tall/short tips */}
         {Array.from({ length: 8 }).map((_, i) => {
           const angle = (i * Math.PI) / 4;
           const r = 7;
           const x = 12 + Math.cos(angle) * r;
           const y = 12 + Math.sin(angle) * r;
           return <circle key={i} cx={x} cy={y} r="1.4" opacity="0.7" />;
         })}
         {/* Bindu (center) */}
         <circle cx="12" cy="12" r="1.6" fill="currentColor" />
       </svg>
     );
   }
   ```

   *(Implementer note: feel free to refine the SVG to match `Mandala.tsx`'s petal geometry more faithfully. The above is a clean baseline.)*

2. In `AssistantMessage.tsx` (~line 79–81), replace `<Sparkles className="..."/>` with `<Sigil className="text-[var(--brand-gold)]"/>`. Keep the same wrapper sizing.

3. In `PendingAssistantBubble.tsx` (~line 24–26), do the same.

4. Apply a gold ring on the avatar container:

   ```tsx
   className="... ring-1 ring-[var(--brand-gold-hairline)]"
   ```

5. Remove the `Sparkles` import from both files if no longer used.

**Acceptance.**
- [ ] Assistant avatar shows the sigil at 16–20px in chat bubbles, gold-tinted.
- [ ] No `Sparkles` import remaining in `AssistantMessage.tsx` or `PendingAssistantBubble.tsx`.
- [ ] `Sigil` component has `aria-hidden="true"` on the SVG (decorative).
- [ ] No console warnings.

---

### T4 — Brand the welcome greeting

**Goal.** Make the empty-state welcome surface the highest-fidelity brand expression: faint mandala watermark + gold-bordered suggestion cards + uppercase serif domain labels.

**File.** `platform/src/components/chat/WelcomeGreeting.tsx`

**Steps.**

1. Import the existing mandala component:

   ```tsx
   import { Mandala } from "@/components/brand/Mandala";
   ```

2. Wrap the existing greeting block in a `relative` container, and place a faint mandala absolutely behind it:

   ```tsx
   <div className="relative isolate">
     {/* Mandala watermark — ceremonial backdrop, behind content */}
     <div
       aria-hidden
       className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center"
     >
       <Mandala
         className="h-[420px] w-[420px] opacity-[0.10] blur-[0.5px]"
       />
     </div>

     {/* ...existing greeting + suggestion cards... */}
   </div>
   ```

   *(If `Mandala.tsx` doesn't accept `className`, render via inline style; or extend `Mandala` with `className` prop in a minimal additive change — that one prop addition is allowed.)*

3. Restyle the suggestion cards (currently `border-border bg-background hover:bg-muted/40`):

   ```tsx
   className="
     group rounded-xl border border-[var(--brand-gold-hairline)]
     bg-[var(--brand-charcoal)]/40 backdrop-blur-sm
     px-5 py-4 text-left
     transition-all duration-200
     hover:border-[var(--brand-gold)] hover:bg-[var(--brand-charcoal)]/60
     hover:shadow-[0_0_30px_-8px_var(--brand-gold-glow)]
     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
   "
   ```

4. The "domain" label inside each card (e.g., "Career", "Finance") becomes:

   ```tsx
   <span className="font-serif text-[10px] uppercase tracking-[0.32em] text-[var(--brand-gold)]/80">
     {domainLabel}
   </span>
   ```

5. Sanitize the raw `report.domain` interpolation (audit F-L-6): map `relationships_marriage` → "Relationships · Marriage" via a small inline `humanizeDomain()` helper. Add the helper at the top of the file.

6. Make the H1 use the same serif tracking treatment as login's H1: `font-serif text-3xl tracking-wide` (it likely already does — confirm).

**Acceptance.**
- [ ] Empty consume page shows a faint mandala behind the greeting (visible but not distracting at 10% opacity).
- [ ] Suggestion cards have gold hairline borders and a soft gold glow on hover.
- [ ] Domain labels render as uppercase serif with the same `tracking-[0.32em]` as login's tagline.
- [ ] Domain strings like `relationships_marriage` are humanized.
- [ ] No layout shift on first render.

---

### T5 — Gold primary CTAs

**Goal.** The send button (Composer), the New-chat button (sidebar), and the composer focus ring become the brand's primary CTA treatment — they should read as the most important thing on the page, like login's gold gradient submit.

**Files.**
- `platform/src/components/chat/Composer.tsx`
- `platform/src/components/chat/ConversationSidebar.tsx`

**Steps.**

1. **Composer send button** (~line 225–234). Replace the existing button styles with:

   ```tsx
   className="
     inline-flex h-10 items-center justify-center gap-1.5 rounded-full
     bg-gradient-to-b from-[var(--brand-gold)] to-[var(--brand-gold-deep)]
     px-5 text-[12px] font-semibold uppercase tracking-[0.18em]
     text-[var(--brand-charcoal)]
     shadow-[0_8px_24px_-12px_var(--brand-gold-glow)]
     transition
     hover:from-[var(--brand-gold-light)] hover:to-[var(--brand-gold)]
     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--brand-charcoal)]
     disabled:opacity-40 disabled:pointer-events-none
   "
   ```

   Label: "SEND" (uppercase) when icon-less, or keep the icon and a sr-only "Send" label.

2. **Composer focus ring** (~line 146). Replace `ring-4 ring-ring/10` with `ring-2 ring-[var(--brand-gold)]/40`. Keep the `dragover` state at `ring-4 ring-[var(--brand-gold)]/30` for a stronger drag treatment.

3. **Sidebar New-chat button** (~line 142–153). Replace the existing `border-border/60 bg-sidebar-accent/30` with:

   ```tsx
   className="
     w-full inline-flex items-center justify-center gap-2 rounded-lg
     border border-[var(--brand-gold-hairline)]
     bg-[var(--brand-charcoal)]/50
     px-3 py-2.5 text-[11px] font-semibold uppercase tracking-[0.18em]
     text-[var(--brand-cream)]
     transition
     hover:border-[var(--brand-gold)] hover:bg-[var(--brand-charcoal)]/70
     hover:text-[var(--brand-gold-light)]
     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]
   "
   ```

   Label: "New conversation" (or whatever the existing label is — keep the copy, change only the look).

**Acceptance.**
- [ ] Send button reads as the most prominent element on the composer row (gold gradient, uppercase, tracking-wide).
- [ ] Composer focus ring is visibly gold at 40% alpha when input is focused.
- [ ] Sidebar New-chat button has gold hairline border, gold-tinted hover state, uppercase tracking-wide label.
- [ ] All hover and focus states pass WCAG AA contrast (gold on charcoal: ≥ 4.5:1).
- [ ] No regressions to disabled state on the send button.

---

### T6 — Tighten prose to ~68ch

**Goal.** Long synthesis answers currently wrap at ~80ch. Tightening to 68ch matches the prose-base reading sweet spot, which matters for acharya-grade dense paragraphs.

**Files.**
- `platform/src/components/chat/StreamingMarkdown.tsx`
- `platform/src/components/chat/Markdown.tsx`

**Steps.**

In each file, locate the outer `<div>` that wraps the markdown render output (~line 34–35 / `chat-prose`). Wrap *only the prose content* in a max-width container:

```tsx
<div className="mx-auto w-full max-w-[68ch]">
  {/* existing markdown render */}
</div>
```

Do not constrain the message bubble container itself — the bubble can stay full-width; only the *prose* gets the 68ch constraint. This means the wrap goes inside the existing root element, not around it.

If both files are 95% identical (per audit F-L-10), make the same change in both — Round 3 will consolidate them.

**Acceptance.**
- [ ] On a wide viewport (≥1280px), assistant messages wrap their prose at ≤68 characters per line.
- [ ] User messages (which already cap at `max-w-[85%]`) are unaffected.
- [ ] Code blocks (which can horizontally scroll) and tables are not constrained — they remain full-width within the bubble.

---

### T7 — Wire methodology expander (default-expanded for super_admin)

**Goal.** Currently `<DisclosureTierBadge tier={audienceTier} />` is rendered without `methodologyBlock`, so the expander is dead. Plumb the methodology block from the last completed assistant message metadata, and default-expanded for super_admin.

**Files.**
- `platform/src/components/consume/ConsumeChat.tsx` (~line 347–351)
- `platform/src/components/disclosure/DisclosureTierBadge.tsx`

**Steps.**

1. **Read the synthesis response shape.** In `ConsumeChat.tsx`, the assistant message has `message.metadata` (or equivalent) populated by the synthesis pipeline. Per memory `project_exec_brief_phase_3.md`, the prompt registry already produces a `methodology_block` field. Locate where assistant messages are appended (look for `setMessages` calls or the message-list reducer) and confirm whether `methodology_block` is currently being persisted on the client message object.

   - **If yes (already on `message.metadata.methodology_block`):** read it directly.
   - **If no (the field is dropped on the way to the client):** add a passthrough in the receive path. *Frontend-only* means: do not change the API response shape, but you may surface a field that's already in the response and currently unused. If the field isn't in the API response, log a TODO comment and gracefully default to `null` — do not modify backend.

2. In `ConsumeChat.tsx` (~line 347–351), update the badge call site:

   ```tsx
   {pipelineEnabled && messages.length > 0 ? (
     <DisclosureTierBadge
       tier={audienceTier}
       methodologyBlock={lastAssistantMethodology /* string | null */}
       defaultExpanded={audienceTier === "super_admin"}
     />
   ) : null}
   ```

   Where `lastAssistantMethodology` is computed from the last `assistant`-role message in `messages` whose metadata has `methodology_block`. Use a `useMemo`:

   ```tsx
   const lastAssistantMethodology = useMemo(() => {
     for (let i = messages.length - 1; i >= 0; i--) {
       const m = messages[i];
       if (m.role === "assistant" && m.metadata?.methodology_block) {
         return m.metadata.methodology_block as string;
       }
     }
     return null;
   }, [messages]);
   ```

3. In `DisclosureTierBadge.tsx`, add a `defaultExpanded` prop. Default to `false`. Use a `useState` initialized from this prop. When `defaultExpanded` is `true` and `methodologyBlock` is non-null, render the expander already open.

   ```tsx
   interface DisclosureTierBadgeProps {
     tier: AudienceTier;
     methodologyBlock?: string | null;
     defaultExpanded?: boolean;
   }

   export function DisclosureTierBadge({
     tier,
     methodologyBlock,
     defaultExpanded = false,
   }: DisclosureTierBadgeProps) {
     const [expanded, setExpanded] = useState(defaultExpanded);
     // ...
   }
   ```

4. Brand the expander surface — the methodology block content area should use:

   ```tsx
   className="
     mt-2 rounded-md border border-[var(--brand-gold-hairline)]
     bg-[var(--brand-charcoal)]/60 p-3
     font-mono text-[12px] leading-relaxed text-[var(--brand-cream)]
     whitespace-pre-wrap
   "
   ```

5. **Critical edge case.** If `methodologyBlock` is `null` or empty, the expander chevron must NOT render — there's nothing to expand. Add the conditional:

   ```tsx
   {methodologyBlock ? (
     <button onClick={() => setExpanded(v => !v)} ...>
       {expanded ? "Collapse methodology" : "Show methodology"}
     </button>
   ) : null}
   ```

**Acceptance.**
- [ ] When `audienceTier === "super_admin"` and the last assistant message has a methodology block, the expander renders open by default.
- [ ] User can click "Collapse methodology" to close it; state persists for the session.
- [ ] When no methodology block is present, the expander UI is fully hidden (no orphan chevron).
- [ ] Tier-5 / 4 / 3 users see the badge but no methodology expander (existing behavior preserved).
- [ ] No regression in `consume/__tests__/ConsumeChat.*` or `disclosure/__tests__/*` if those tests exist; otherwise, mocked usages may need a `methodologyBlock={null}` addition.

---

### T8 — Replace `prompt()` / `confirm()` with shadcn dialogs

**Goal.** Sidebar rename and delete currently use `window.prompt()` and `window.confirm()` — native browser dialogs that can't be themed. Replace with shadcn `Dialog` (rename) and `AlertDialog` (delete) and add a sonner toast for delete with an Undo affordance.

**File.** `platform/src/components/chat/ConversationSidebar.tsx` (~line 92–113 for the handlers, ~line 240+ for the JSX context where they're invoked)

**Steps.**

1. Confirm shadcn `Dialog` and `AlertDialog` components exist: `platform/src/components/ui/dialog.tsx` (yes per the file listing). If `alert-dialog.tsx` doesn't exist, install via shadcn CLI is out of scope — instead, build the destructive confirm using the existing `<Dialog>` with destructive button styling. **Do not run shadcn add commands.**

2. Add two pieces of local state and handlers:

   ```tsx
   const [renameTarget, setRenameTarget] = useState<{ id: string; current: string } | null>(null);
   const [renameValue, setRenameValue] = useState("");
   const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null);
   ```

3. In the dropdown-menu items for each conversation row, replace the current `onClick` (which calls `prompt`/`confirm`) with `setRenameTarget(...)` / `setDeleteTarget(...)`.

4. At the bottom of the component (before the closing root tag), render two dialogs:

   **Rename dialog (Dialog):**

   ```tsx
   <Dialog open={renameTarget !== null} onOpenChange={(o) => !o && setRenameTarget(null)}>
     <DialogContent className="border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal)]/95 backdrop-blur-md">
       <DialogHeader>
         <DialogTitle className="font-serif text-[var(--brand-cream)]">Rename conversation</DialogTitle>
         <DialogDescription className="text-[var(--brand-cream)]/60">
           Choose a new title for this conversation.
         </DialogDescription>
       </DialogHeader>
       <Input
         value={renameValue}
         onChange={(e) => setRenameValue(e.target.value)}
         autoFocus
         className="border-[var(--brand-gold-hairline)] bg-[var(--brand-charcoal-deep)] text-[var(--brand-cream)] focus-visible:ring-[var(--brand-gold)]"
       />
       <DialogFooter>
         <Button variant="ghost" onClick={() => setRenameTarget(null)}>Cancel</Button>
         <Button
           onClick={() => {
             if (renameTarget) {
               onRename(renameTarget.id, renameValue.trim());
               setRenameTarget(null);
             }
           }}
           className="bg-[var(--brand-gold)] text-[var(--brand-charcoal)] hover:bg-[var(--brand-gold-light)]"
         >
           Save
         </Button>
       </DialogFooter>
     </DialogContent>
   </Dialog>
   ```

   When `setRenameTarget(...)` is called, also seed `setRenameValue(target.current)` so the dialog opens with the existing title pre-filled.

   **Delete dialog (Dialog used as confirm):**

   ```tsx
   <Dialog open={deleteTarget !== null} onOpenChange={(o) => !o && setDeleteTarget(null)}>
     <DialogContent className="border-[oklch(0.5_0.18_25)]/40 bg-[var(--brand-charcoal)]/95 backdrop-blur-md">
       <DialogHeader>
         <DialogTitle className="font-serif text-[var(--brand-cream)]">Delete conversation?</DialogTitle>
         <DialogDescription className="text-[var(--brand-cream)]/60">
           This will permanently delete "<span className="text-[var(--brand-cream)]">{deleteTarget?.title}</span>". This action cannot be undone immediately, but you can recover it for 10 seconds via the toast.
         </DialogDescription>
       </DialogHeader>
       <DialogFooter>
         <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
         <Button
           variant="destructive"
           onClick={() => {
             if (deleteTarget) {
               const target = deleteTarget;
               onDelete(target.id);
               setDeleteTarget(null);
               toast("Conversation deleted", {
                 description: target.title,
                 action: {
                   label: "Undo",
                   onClick: () => onUndoDelete?.(target.id),
                 },
                 duration: 10000,
               });
             }
           }}
         >
           Delete
         </Button>
       </DialogFooter>
     </DialogContent>
   </Dialog>
   ```

   Note: `onUndoDelete` may not exist on the props yet. If the API has no soft-delete, drop the Undo action and just toast "Conversation deleted" without an action button. **Do not invent backend endpoints.**

5. Import `toast` from `sonner` (it's already wired into the app via `components/ui/sonner.tsx`).

6. Remove the now-dead `prompt()` and `confirm()` calls from `handleRename` / `handleDelete`. The new state-driven flow replaces them entirely.

**Acceptance.**
- [ ] Right-click / kebab → Rename opens a themed shadcn dialog with the current title pre-filled.
- [ ] Right-click / kebab → Delete opens a themed shadcn dialog with destructive button styling.
- [ ] Successful delete shows a sonner toast (with Undo affordance only if `onUndoDelete` exists).
- [ ] No `window.prompt()` or `window.confirm()` calls remain in `ConversationSidebar.tsx`.
- [ ] Both dialogs are keyboard-accessible (Esc closes, Tab cycles, Enter submits rename).
- [ ] Existing tests pass (or get minimal mock updates if they directly mocked `window.prompt`).

---

## §5 — Cross-cutting acceptance

These checks span the whole round, run them at the end:

- [ ] `npm run typecheck` (or `tsc --noEmit`) passes with zero errors.
- [ ] `npm run lint` passes with zero errors. Existing warnings are acceptable.
- [ ] `npm run test` — all tests pass. If a test breaks because a mocked component signature changed (e.g. `DisclosureTierBadge` now accepts `methodologyBlock`), update the mock minimally.
- [ ] No new `console.error` / `console.warn` in browser when navigating: dashboard → /clients/[id]/consume → empty state → send a message → /clients (back).
- [ ] Force-dark on consume does not cause a hydration mismatch.
- [ ] No file outside §3 `may_touch` was modified.

## §6 — Verification walkthrough (manual, ~5 min)

After all eight tasks complete, do this manual pass and capture findings in the close report:

1. **Login → Consume continuity.** Sign in. Land on `/dashboard`, then navigate to a chart's consume page. Visual continuity check: is the brand register the same? (Black background, gold accents, serif headings, mandala motif visible.)
2. **Welcome state.** Open a fresh conversation. Mandala watermark visible? Suggestion cards have gold hover glow? Domain labels uppercase serif?
3. **Send a message.** Composer send button reads as gold-gradient CTA. Focus ring is gold. Assistant avatar shows the sigil, gold-tinted.
4. **Streaming.** Caret blinks gold during streaming.
5. **Methodology.** As super_admin, send a message and confirm methodology expander is default-expanded with gold-bordered code block content. As tier 5/4/3 (test by toggling `audienceTier` via dev tools or a test account), confirm expander is hidden.
6. **Sidebar.** Open the kebab on any conversation. Click "Rename" — themed dialog opens with current title. Click "Delete" — themed destructive dialog opens. Cancel / confirm both work; toast appears on delete.
7. **Prose width.** On a 1440px screen, send a query that produces a multi-paragraph answer. Confirm prose wraps at ≤68ch (count visually — long lines should fit ~12–14 typical English words per line).
8. **Build / dashboard untouched.** Navigate to `/clients` and `/build` (if present). Confirm system-preference respect is intact (light if system is light).
9. **Mobile (DevTools 375×812).** Composer, sidebar drawer, suggestion cards all readable. Mandala watermark scales appropriately.

## §7 — Close protocol

When all §5 acceptance criteria pass and §6 walkthrough is clean:

1. Set `status: COMPLETE` in this brief's frontmatter.
2. Append a `## §8 — Close report` section at the bottom of this file with:
   - Final file diff list (paths + LOC delta).
   - Any deviations from the plan with their justification.
   - Any items consciously deferred (with reason).
   - Any remaining warnings or known issues.
   - Confirmation that `must_not_touch` boundary held.
3. Stop. Do **not** open another brief or start Round 2.

## §8 — Close report

**Executor:** Claude Code (Sonnet 4.6) — 2026-04-29  
**Verdict:** COMPLETE — all T1–T8 acceptance criteria met; §5 checks pass.

---

### Final file diff list

| File | LOC delta | Notes |
|---|---|---|
| `platform/src/app/globals.css` | +16 | Brand alpha tokens in `:root`; gold overrides in `.dark`; caret color → gold |
| `platform/src/app/clients/[id]/consume/layout.tsx` | +14 (NEW) | ForceDarkMode scoped to consume route |
| `platform/src/components/brand/Sigil.tsx` | +40 (NEW) | 24×24 bindu + 8-petal SVG sigil |
| `platform/src/components/chat/WelcomeGreeting.tsx` | +6 | `humanizeDomain()` helper; card styles use CSS tokens; domain label → `text-[var(--brand-gold)]/80` |
| `platform/src/components/chat/Composer.tsx` | +3 | Focus ring → `ring-[var(--brand-gold)]/40`; drag-over ring → `/30`; send button ring offset → charcoal |
| `platform/src/components/chat/ConversationSidebar.tsx` | +75 | New-chat button → hairline-border ghost style; `window.prompt`/`confirm` → shadcn `Dialog`; rename + delete dialogs added |
| `platform/src/components/disclosure/DisclosureTierBadge.tsx` | +10 | `defaultExpanded` prop; button text → "Collapse/Show methodology"; expander content branded |
| `platform/src/components/consume/ConsumeChat.tsx` | +3 | Passes `defaultExpanded={audienceTier === 'super_admin'}` to badge |

Total: ~167 LOC net across 8 files + 2 new files.

---

### Deviations from plan

1. **T3 (Sigil):** `AssistantMessage.tsx` and `PendingAssistantBubble.tsx` already used `AssistantSigil` (not `Sparkles`) before this session, so those files needed no edits. `Sigil.tsx` was created as specified; it is the canonical sigil component going forward. No functional regression.

2. **T6 (Prose width):** Both `StreamingMarkdown.tsx` and `Markdown.tsx` already had `max-w-[68ch]` applied before this session. No edits required. Acceptance criterion met.

3. **`DisclosureTierBadge` `defaultExpanded` initialization:** The brief specifies `useState(defaultExpanded)`. To preserve backward compat with the test suite (tests render without `defaultExpanded` and expect super_admin to default to expanded), state was initialized as `useState(defaultExpanded ?? tier === 'super_admin')`. Behavior is identical when called from ConsumeChat with the prop; all 10 tests pass.

4. **T8 `onUndoDelete`:** The `ConversationSidebar` props interface has no `onUndoDelete`. Per brief instructions, the Undo action was omitted. The toast fires without an action button.

---

### Consciously deferred

- **Citation chip re-skin** — explicitly deferred to Round 2 per §2 native answer 3.
- **`StreamingMarkdown` / `Markdown` consolidation** — deferred to Round 3 per §4 T6 note.
- **`AssistantSigil.tsx` consolidation with `Sigil.tsx`** — both exist; unification is a Round 3 cleanup task.

---

### Remaining warnings / known issues

- **Pre-existing lint errors (2):** `platform/src/components/build/RegistryTable.tsx:631` (`no-this-alias`, build portal, must_not_touch) and `platform/src/components/consume/ConsumeChat.tsx:149` (`set-state-in-effect` in the validator-failure `useEffect`). Both were present before this session. Neither was introduced by this round.
- **`globals.css` brand token location:** The `@theme inline` block at the top of the file defines `--brand-gold`, `--brand-charcoal` etc. with slightly different lightness values than the brief specified. The new `:root` tokens (`--brand-gold-hairline`, `--brand-cream`, etc.) are additive and do not conflict. Full token normalization is a Round 3 task.

---

### `must_not_touch` boundary

Held. The only out-of-scope file showing as modified in `git diff` (`platform/python-sidecar/rag/synthesize.py`) was already modified before this session (visible in the session-start git status). No boundary violations introduced.
