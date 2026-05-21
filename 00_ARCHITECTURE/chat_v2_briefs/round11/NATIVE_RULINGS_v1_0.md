---
canonical_id: R11_NATIVE_RULINGS
version: 1.0
status: LOCKED
authored_on: 2026-05-21
authored_by: Abhisek Mohanty (native), captured by Cowork session
purpose: >
  Locked rulings from the native on the four R11 Open Native-Input Items
  (and three additional scope clarifications) that gate session execution.
  Sub-agents read this file alongside their brief; the rulings here override
  any default option language in individual briefs.
---

# R11 — Native Rulings (locked)

These rulings were captured in the Cowork session that authored R11. They are the
authoritative scope answers for the duration of R11 execution. They override any
"Open Native-Input Item" language in the master plan or individual briefs.

## §1 — Brand identity (preserve Marsys, replace functionality)

**Marsys preserved (do NOT change):**
- The entire Marsys design system: brand-gold (`oklch(0.78 0.13 80)` ≈ `#d4af37`),
  brand-charcoal (`oklch(0.10 0.012 70)`), brand-ink (`oklch(0.04 0.005 70)`),
  brand-vellum, the gold-on-ink consume-shell aesthetic, gold-hairline borders,
  radial-gradient consume backdrops.
- The astrology-specific brand voice in colors and ornament (Devanagari double-danda
  accents, mandala-spin animation, gold-CTA brand-cta gradient on send button,
  glassmorphic gold-tinted speech-tail user bubble — `--brand-form-fill`,
  `--brand-gold-hairline`, `--brand-gold-glow`, `--brand-gold-faint`).
- The `.consume-shell` CSS class and all its token re-pointing remains the active
  class on the consume route. We do NOT introduce a `.claude-shell` companion class.

**Replaced with Claude (DO change to match Claude.ai):**
- **Fonts** — assistant message body becomes Claude's system-serif stack
  (`ui-serif, Georgia, "Iowan Old Style", "Source Serif Pro", serif`).
  Headings inside assistant responses use the same serif at heavier weight.
  Chrome (sidebar, buttons, labels) and the user-typed text use a sans system stack.
  Code blocks use a monospace system stack.
- **Markdown rendering** — Claude's content rendering: h1 28-30px, h2 22-24px,
  h3 18-19px serif weight 600 with slight negative letter-spacing on h1;
  body 16px / line-height 1.65; lists, blockquotes, code blocks per Claude.
  Code-block background = `var(--card)` (one shade off canvas) inside `.consume-shell`.
- **Message container shape** — **assistant messages are bubble-less** (serif text
  directly on `.consume-shell` canvas, no card chrome). **User messages keep the
  Marsys glassmorphic speech-tail design** but adopt Claude's shape constants:
  `border-radius: 1rem`, `max-width: 80%`, `padding: 12px 14px`, right-aligned.
- **Reading column** — message stream pinned to **max-width 48rem (768px)**
  centered horizontally inside `.consume-shell`.
- **Action bar** — copy/retry/branch icons reveal on **hover only**
  (Claude pattern), not always-visible.
- **Composer chrome** — Claude-minimal shape (rounded 1.5rem, no box-shadow,
  fades into canvas), but `--accent` stays Marsys `var(--brand-gold)` for the
  focus-within border + filled-circle send button background.
- **Sidebar conversation items** — Claude-compact shape (`padding: 8px 12px`,
  `border-radius: 8px`, hover bg from existing `--sidebar-accent`), but the
  near-ink charcoal sidebar background + gold-hairline borders + brand-cta
  "New Chat" button are preserved verbatim.

## §2 — Accent color

**Keep `var(--brand-gold)` everywhere** Claude.ai would use coral. Specifically:
- Composer focus-within border
- Send-button filled circle background (continues to use existing
  `.brand-cta` gradient)
- Inline citation `[N]` marker color
- Link color inside assistant body (with sufficient luminance against
  `.consume-shell` charcoal — verify computed contrast in V-S1 close)
- Stop-button square-glyph background

Coral / `#CC785C` is NOT introduced. Brand-spine continuity (login, admin,
observatory all use brand-gold) is preserved.

## §3 — Citation idiom (full Claude pivot)

**Adopt Claude's citation idiom completely; retire the existing footnote + side-panel system.**

- All citations render as inline-clickable superscript markers at the claim level,
  Claude-style (icon + hover-preview popover + click-out to source).
- The R7-S2 GFM-footnote `[^N]` rendering path is **deprecated** at R11 close.
  Synthesis citations migrate to the same inline-clickable component.
- **`CitationSidePanel` is retired entirely.** `CitationCtx` provider is removed.
  Right-side panel real estate goes back to the message column (which is then
  centered at 768px — see §1).
- Scope expansion folded into **O-S4** (originally "Inline citation parity"):
  O-S4 now ALSO retires `CitationSidePanel`, `CitationCtx`, `NumberedCitation`
  (footnote-style), and the related cite-* color tokens in globals.css if unused.
- The R10 Y-S2 freshness-badge work is preserved by attaching freshness data to
  the inline-citation hover-preview popover (so the badge appears on hover, not
  in a side panel).

## §4 — Prompt cache breakpoints (canonical Anthropic layout, exactly)

**Four `cache_control: { type: "ephemeral" }` breakpoints in this exact order:**

1. End of the **tools block** (after the last tool definition).
2. End of the **static system prompt** (before any per-conversation RAG/MSR injection).
3. End of the **RAG bundle** (MSR/UCN/CDLM context injection block).
4. The **most recent assistant turn** for incremental conversation caching.

O-S2 ships exactly this layout. No adjustment, no experimental variants.
Cache TTL: 5-minute ephemeral (per Anthropic docs default).

## §5 — Sacred Marsys components (preserve verbatim)

The following components are NOT touched by any R11 session — preserved as-is:
- `PerMessageDetailsDrawer` (cost/audit drawer)
- Cost Visibility surface (`COST_VISIBILITY_FOR_USERS` flag-gated)
- `PanelMember` rendering (multi-perspective synthesis output)
- Observatory integration points (cost/usage SSE emit)

The following components ARE in-play (R11 may restyle or remove):
- `CitationSidePanel`, `CitationCtx`, `NumberedCitation` → **retired by O-S4** (§3).
- `ReasoningProgress` → restyled by S-S3 (auto-collapse heuristic); Y-S4 step-marker
  rendering preserved structurally but visual styling brought to Claude's pattern.
- `InteractiveTable` (R10 X-S10) → typography adjusted in V-S6 to match the Claude
  markdown typescale; sort/filter/CSV logic untouched.
- `MermaidBlock` (R10 X-S11) → similar: typography pass only.
- `MarkdownContent` → restyled by V-S6.
- `AssistantMessage` → bubble-less restyle by V-S3.
- `UserMessage` → dimensions adjustment by V-S2 (speech-tail preserved).
- `Composer` → minimal-shape restyle by V-S4.
- `ConversationSidebarV2` → compact list-item shape by V-S5.

## §6 — Conductor execution policy

- **Halt policy:** STRICT — Conductor halts on first gate-command non-zero exit
  OR any sub-agent `status: HALT_NEEDS_HUMAN`. Halt is logged to
  `CONDUCTOR_HALT_LOG.md` and pings the native in the Cowork chat.
- **Permissions:** Sub-agents run under `--dangerously-skip-permissions` per the
  existing Conductor §3 sub-agent prompt template. All file writes are permitted
  inside the worktree.
- **PR / merge policy:** After all 16 R11 sessions PASS, the Conductor runs a
  17th queue entry **`R11-MERGE`** that pushes the branch, opens a PR to main,
  waits for CI, and **auto-merges** (`gh pr merge --auto --squash --delete-branch`).
  Native review is opt-in only — the user may intervene by pausing the Conductor
  before R11-MERGE runs. `requires_human_approval: false` on R11-MERGE is an
  **explicit native override** of the Wave 1 Conductor invariant
  "PR-to-main always human-gated". This override is local to R11 only.
- **No silent skip on gate failure:** STRICT halt + Cowork ping is the only path
  that bypasses the auto-merge.

## §7 — Flag rename

The original master-plan flag `MARSYS_FLAG_R11_CLAUDE_SHELL` is renamed
`MARSYS_FLAG_R11_CLAUDE_RENDERING` — "shell" implied a separate palette theme
(which we are NOT introducing per §1). "Rendering" reflects what the flag
actually gates: Claude-style content rendering inside the existing `.consume-shell`.

All V-group briefs use this single renamed flag, default false at flag
introduction. After V-S6 visual parity is verified, per-user opt-in is
controlled by the V-S0 toggle (§8 below) rather than a flag flip.

## §8 — Runtime user toggle (added 2026-05-21)

The native requested that users be able to flip between Classic Chat V2 and the
R11 Claude-parity surface **at runtime**, not only via the build-time env-var.
This is encoded as a new **V-S0** session that runs FIRST in R11:

- A new hook `useClaudeRendering()` returns `boolean`. Returns true iff:
  - `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING === 'true'`
    (env-var — the team's master kill-switch), AND
  - `localStorage['marsys.chatRenderingMode'] === 'claude'`
    (per-browser user preference — the user's choice).
- A new component `ChatRenderingToggle` renders a settings toggle, visible only
  when the env-var is true. Lets the user flip the preference live without a
  redeploy.
- V-S1..V-S6 wire their conditional to `useClaudeRendering()` rather than reading
  the env-var directly. Flipping the toggle switches the surface live in the
  current tab (and across tabs via the `storage` event).

**Default state of the user preference: `'classic'`** — meaning even after the
env-var is flipped to true in production, existing users see the current Chat V2
until they explicitly opt in.

Two-flag truth table:

| env-var | user-pref | what the user sees |
|---|---|---|
| false | (anything) | Classic Chat V2 (R11 code paths inactive — toggle hidden) |
| true | 'classic' (default) | Classic Chat V2 (R11 code paths loaded; toggle visible) |
| true | 'claude' | R11 Claude-parity interface |

V-S0 sits at queue position 0; V-S1's `depends_on` includes V-S0; R11-MERGE
also depends on V-S0.

---

*Locked. Sub-agents executing R11 sessions read this file in addition to their
individual brief and the master plan. Any ambiguity between this file and a
brief resolves in favor of this file.*
