---
canonical_id: PARIPRASHNA_DESIGN_ENGINEERING_PLAN
version: 0.3
status: DRAFT
date: 2026-07-28
author: Claude (Cowork design-engineering session)
supersedes: none
relates_to:
  - 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (engineering substrate; this plan sits ABOVE it)
  - 00_ARCHITECTURE/PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md (the audit that proved the backend was sound)
  - 00_ARCHITECTURE/CHAT_V2_CLOSE_v1_0.md (the prior build this plan learns from)
changelog:
  - "0.2 (2026-07-28): Elevation pass (strategist + world-class UI designer, single session). The relationship arc designed, not just the turn: new P9 (The instrument remembers), §4.0 two trust arcs, J8 (the reading that returns), the arrival line. SIGNATURE INTERACTION chosen and sharpened: the prediction-card lifecycle with the kāla-rekhā time hairline (§6.9) — the one component no other conversational product can have. Typographic anatomy of a reading codified (§6.3.1: verdict/elaboration/verse/gloss/caveat roles as protocol). Settle choreography named the Seal with the closing-rule draw as the surface's one flourish (§5.3); motion constitution + sound decision SND-1 recorded (§5.7). Empty state elevated to an invocation with the ecliptic hairline (§5.3). Sealed-reading print/export added as Phase 2 §10.6; OD-2 resolved to (b). Reference-rail residue purged (§10.3 stubbed, OD-4 retired) honoring the 2026-07-27 native ruling. New AC-16 signature-integrity gate. All standing rulings preserved: D-14, D-15, D-19 controls (§5.8.1), rail removal. Elevations marked [ELEVATION v0.2] throughout."
  - "0.1 (2026-07-28): First draft. Design-led master plan for the Paripraśna chat surface: PRD, principles, IA, journeys, interaction/state design, Marsys visual system, content/voice, component architecture, responsive/a11y, Phase 2 breadth, acceptance criteria, open decisions."
---

# Paripraśna — Design-Engineering Master Plan

*The conversation surface of MARSYS-JIS. Paripraśna (परिप्रश्न): the act of asking, thoroughly and with respect.*

---

## 0. Front matter & how to read this document

### 0.1 Why this document exists, and why it is design-led

This chat engine has been built twice — a legacy phase and Chat V2 — and struggled both times. The native's own diagnosis, confirmed by the grounding audit (`PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md`): **the engine was essentially sound; the gap was the interface.** When the engine was finally invoked end-to-end, the fatal failure was a one-line hardcoded reference. Every symptom actually suffered in use — the cursor landing under tables, text jumping mid-read, the "thinking" phase presented incontinently, internal signal IDs leaking into reader prose — was a failure of interaction design, not of retrieval, synthesis, or grounding.

The prior plans were engineering-led: protocol first, components second, feel last. Both times, "feel" never got built. This document inverts the order. It is the artifact a mature product-design + design-engineering team produces **before a line of code**: PRD → journeys → information architecture → interaction states → visual system → content design → component architecture → acceptance criteria. The stream protocol and the client reducer appear here — in §8 — as the implementation layer *underneath* the design, consuming decisions made in §4–§7, never driving them.

**The bar:** best-in-class interaction robustness — "does it feel like Claude Code, like Gemini" is a real acceptance gate (§11) — but **not** their epistemic opacity. Those products hide both their machinery *and* their grounds. Paripraśna adopts their choreography (stable geometry, append-only rendering, one volatile region, collapsed density) and rejects their opacity. The governing sentence for every screen in this document:

> **Hide how the instrument worked; never hide why the claim stands.**

### 0.2 Phasing

- **Phase 1 — the core conversation, at full depth.** Composer → the three-region turn (working / answer / grounding) → thinking & tool presentation → streaming answer → citations → follow-up → disagreement → every state (idle, composing, thinking, streaming, settled, empty, honest-gap, error, reconnecting). Sections §4–§9 and §11 are Phase 1 at implementation-ready depth.
- **Phase 2 — the whole Paripraśna surface, at architecture depth.** History sidebar, Samīkṣā (prediction review), settings & model management, dashboard entry, and the sealed reading (print/export, §10.6). Section §10, one architecture-depth section each. Phase 2 gets its own deep spec after Phase 1 ships and is reacted to. *(The reference rail — a Vedic-chart panel — was removed by native ruling 2026-07-27; see §3.)*

### 0.3 How to read

- If you are the **native reacting to this plan**: read §1–§2 (what and why), §4 (the journeys — this is what using it will feel like), §6 (what it will look like), §12 (the decisions only you can make).
- If you are a **design engineer implementing**: §5 (states), §6 (tokens/components), §8 (component tree + reducer), §9 (responsive/a11y), §11 (gates).
- If you are a **future session auditing**: §11's gates are the falsifiable claims; everything else is their justification.

Terminology: "the reading" = an assistant turn's prose answer. "The turn" = one question→answer unit. "Settle" = the moment a turn's content is final. "The native" = the operator/super-admin. "Guest" = any other reader.

---

## 1. Product requirements (PRD)

### 1.1 Problem statement

MARSYS-JIS has a sealed six-layer engine (L0–L5) capable of acharya-grade, grounded, calibrated chart readings, exposed through ~130 MCP capabilities. It has **no worthy conversational surface.** Two prior attempts produced engines without instruments — the pipes worked, but reading a response was physically unpleasant (layout shift, caret misbehavior, raw machinery on screen) and epistemically leaky (internal IDs in prose, no legible grounding, thinking spew indistinguishable from the answer). The result: a system of extraordinary depth that its own builder avoids using conversationally.

### 1.2 Users

Two users, one register (D-15 — no audience tiers):

| User | Who | What differs | What does NOT differ |
|---|---|---|---|
| **The native (super-admin)** | Abhisek — builder, primary subject, operator | Entitlement: all charts, all audit affordances resolve, Samīkṣā write access, model management, cost visibility | The reading itself — same prose, same register |
| **Guest** | A person the native gives access to (family member, a chart's subject) | Entitlement: their chart(s) only; some audit affordances may not resolve to raw data | The reading itself — acharya-grade, reader-legible, gap-honest, same as the native gets |

There is **no "simple mode."** Depth of audit is an *affordance* (expand a chip, open the working region), never a *mode*. Entitlement gates data, never the existence of the affordance.

### 1.3 Jobs-to-be-done

1. **Ask the chart a question and receive an acharya-grade reading** — career, marriage, health, timing — with the depth of the full L1–L5 stack behind it, in prose a non-astrologer can read.
2. **See why a claim stands** — which chart factors, which classical sources, what epistemic grade — without the machinery ever forcing itself into the prose.
3. **Ask hard things safely** — death, illness, divorce — and receive calibrated, paced, non-ominous answers that neither soften into mush nor land like a verdict.
4. **Push back** — "that doesn't match my life" — and have the disagreement handled as data (the instrument's calibration loop), not as an argument to win.
5. **Continue over time** — threads persist; predictions made in March are recalled in July; the instrument asks about outcomes (Samīkṣā, Phase 2).
6. **Operate the instrument** (native only) — switch models mid-conversation, watch the working region for routing quality, audit any claim to its fact IDs.

### 1.4 Goals

- **G1 — Interaction robustness at the Claude Code / Gemini bar.** Zero layout shift above the volatile tail, caret discipline, calm streaming, collapsed machinery. This is the goal the prior builds missed and the one this plan exists to hit.
- **G2 — Visible epistemics.** Every settled reading shows its grounding count, offers citation chips, and distinguishes confirmed from catalog-only findings (§N.6 density principle). Honest gaps are stated calmly and unmissably.
- **G3 — One register.** Acharya-grade and reader-legible simultaneously, for everyone. Sanskrit where it is the substance, always glossed. No internal IDs in prose, ever.
- **G4 — Depth routing made visible and trustworthy.** The engine's completeness-gated `dossier` path exists; naive routing to shallow `assess_*` tools scored 15–33% on depth in live audit. The UI must (a) route interpretive questions to depth and (b) show the reader what depth they received ("Grounded in 14 chart factors · 3 classical sources" is itself the depth signal).
- **G5 — Emotional safety as a design property.** Pacing, calibrated-probability framing, attributive remedy language, calm gap presentation — designed in §5/§7, not left to model temperament.
- **G6 — Durable foundation for Phase 2.** The turn model, stream protocol, and component architecture must accept the history sidebar and Samīkṣā without rework.

### 1.5 Non-goals (explicit)

- **Not a public product.** No marketing surface, no signup funnel, no theming beyond Marsys.
- **Not a chart-builder UI.** Building charts stays in the existing cockpit; Paripraśna consumes built charts.
- **Not a general-purpose LLM chat.** No web search, no file analysis, no personas. One instrument, one domain.
- **Not audience-tiered.** No "beginner mode," no simplified rewrite pipeline (D-15).
- **Not Phase-2-deep in this document.** Samīkṣā, sidebar get architecture only (§10).
- **Not a redesign of the engine.** The MCP capability surface, the dossier tool, the retrieval planner are consumed as-is; where the UI needs the planner to route deeper, that is a routing-policy input to the engine, not new engine architecture.

### 1.6 Success metrics

| # | Metric | Target | How measured |
|---|---|---|---|
| M1 | Settled-region layout shift during streaming | **CLS contribution = 0** above the volatile tail | Automated: layout-shift observer scoped to settled blocks, in the test harness; any shift with a settled-block source fails CI |
| M2 | Caret orphaning (caret rendered detached from last text node — under a table, after a block boundary, on its own line) | **0 occurrences** across the streaming fixture corpus (tables, lists, headings, code, Sanskrit, citation-adjacent) | Visual regression fixtures + DOM assertion: caret element is always the last inline child of the deepest last text-bearing node of the tail block |
| M3 | Time-to-first-visible-signal (submit → working region live) | < 300 ms perceived (region mounts instantly on optimistic turn open; server phase label may arrive later) | RUM timestamp |
| M4 | Time-to-first-token (submit → first answer prose) | p50 < 4 s, p90 < 12 s for interpretive queries (dossier-routed turns will be slower — the working region is what makes that wait legible) | RUM |
| M5 | Internal-ID leakage in reader prose (SIG.*, fact_id, asset names, "L2", table names) | **0** — enforced by server-side prose lint before the wire (§8.4) | Wire-tap test on response corpus + regex lint in CI |
| M6 | Citation-chip transmutation (plain text later replaced by a badge) | 0 — chips render at final geometry on first paint | Fixture assertion |
| M7 | Honest-gap calm rating | Rubric ≥ 4/5 (§11.5 rubric) on all gap fixtures | Design QA panel (native + one outside reader) |
| M8 | Mobile fixture pass | 100% of §9 mobile scenarios (keyboard, tap-citation, sheet, reconnect) | Manual + Playwright device profiles |
| M9 | axe-core | 0 critical / 0 serious violations on every state fixture | CI |
| M10 | **The native's verdict** | "This feels like Claude Code" — stated after one week of daily use, unprompted symptoms list empty | The ultimate gate. Subjective, binary, non-negotiable (§11.8) |

M10 is deliberately unfalsifiable by machine. The prior builds passed their machine gates and failed in the hand. This plan treats the hand as the last gate.

---

## 2. Design principles

Nine principles, specific to this product. Every interaction decision in §4–§7 traces to at least one. When principles conflict, the earlier-numbered wins.

### P1 — Settled content is sacred
Once prose has rendered and the reader may have begun reading it, it never moves, reflows, restyles, or re-announces. All volatility is quarantined in one region (the tail block) below everything settled.
*Rationale:* every physical symptom of the prior builds — jumping text, cursor under tables — was a violation of this one principle.
**Do:** append-only blocks; fixed-geometry chips; stable-height working header. **Don't:** re-render a paragraph to inject a citation badge; let a late-arriving image or table push settled prose; recompute markdown for the whole message per token.

### P2 — Machinery collapses; epistemics never
Tool calls, retrieval plans, phase chatter collapse to a one-line band by default. Grounding counts, epistemic grades, honest gaps are always visible on the settled surface — they are the product, not the plumbing.
*Rationale:* the reconciliation of the Claude Code bar with this instrument's differentiation. Hide how it worked; never hide why the claim stands.
**Do:** "Consulting the chart · 12s" → expandable. "Grounded in 14 chart factors" → always shown. **Don't:** stream raw tool JSON into the transcript; bury the grounding line behind a click; show a naked answer with no epistemic footer.

### P3 — Calm under fear
People ask this instrument about death, illness, marriage. Every state — especially gaps, errors, and long waits — must read as composed. Nothing pulses red; nothing says "FAILED"; a silence in the chart is presented as a finding, not a withholding.
*Rationale:* in a fear state, users read ambiguity as bad news being hidden. Design decision 5.
**Do:** "The chart is silent on this — that silence is the finding." Neutral gold hairline ribbon. **Don't:** warning triangles on honest gaps; red error toasts mid-reading; a spinner that looks like it's struggling.

### P4 — The register is one
One reading, acharya-grade and reader-legible, for the native and every guest. Audit depth is an affordance behind the surface, never a different surface.
*Rationale:* D-15. Tiered registers rot into a "real" product and a "dumbed-down" one; this instrument refuses that.
**Do:** "Śaśa Yoga (Saturn strongly placed)" for everyone. **Don't:** a "detail level" setting; guest-only simplified prose; expert jargon gated behind admin.

### P5 — Depth is visible
The reader must be able to see, without asking, whether they received a deep reading or a shallow one: grounding counts, source mix, grade chips, and — when composition was completeness-gated — that fact ("all twelve houses consulted").
*Rationale:* the dossier routing insight — the engine can do depth but defaults shallow; visible depth creates the pressure and the trust that keep routing honest.
**Do:** grounding region with real counts; a grade chip on load-bearing claims. **Don't:** identical presentation for a 3-fact quick answer and a 40-fact dossier; fake counts.

### P6 — The number is held, not thrown
Probabilities are calibrated and real, but they arrive as framed language first ("more likely than not; hold it loosely") with the number one affordance away. A bare "70%" never leads.
*Rationale:* calibrated numbers are the instrument's spine, but a naked percentage lands as either verdict or dice; framing preserves both truth and the reader.
**Do:** framed phrase inline, exact figure + calibration basis on expansion. **Don't:** "72% divorce probability" in prose; vague mush with no number anywhere.

### P7 — The instrument answers; the tradition prescribes
Voice discipline: readings are declarative about the chart, attributive about remedies, and never imperative about the reader's life.
*Rationale:* ethical framework + emotional register; "you should" from a machine reading a birth chart is a category error.
**Do:** "The tradition prescribes strengthening Jupiter here." **Don't:** "You should fast on Thursdays."

### P8 — Motion is confirmation, not spectacle
Every animation confirms a state change the user caused or must notice. Durations 120–240 ms, standard easing, opacity/transform only, full `prefers-reduced-motion` degradation.
*Rationale:* a ceremonial instrument is calm; and animation is where layout shift sneaks back in.
**Do:** 160 ms fade-in of the grounding region on settle. **Don't:** shimmer effects, typing rubber-banding, gradient sweeps, anything gold that glows.

### P9 — The instrument remembers `[ELEVATION v0.2]`
A chat product designs turns; an instrument designs a relationship. Every surface decision asks not "how does this read the first time?" but "what does this accrue into by the hundredth conversation?" Predictions return to be graded; contradictions demonstrably weight later readings; a reopened thread greets the reader with where the daśā and the open windows stand. The product's gravity is the loop — reading → window → outcome → sharper reading — and the UI's job is to make that loop *felt* on the reading surface, not merely stored in L5.
*Rationale:* daily return is not sustained by novelty but by accrual; an instrument that visibly keeps its own ledger across months is the one thing that draws the native back after the hundredth conversation.
**Do:** the arrival line (J2); window-close prompts; a prediction card whose eyebrow ages in place (§6.9); "this instrument's prior call on this domain resolved true" in a later grounding region. **Don't:** treat threads as disposable sessions; let a prediction window close silently; make Samīkṣā a form the native must remember to visit.

---

## 3. Information architecture

### 3.1 Surface map

```
MARSYS Dashboard
   │  "Open Paripraśna" (primary action on chart card / global nav)
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PARIPRAŚNA (app shell)                                              │
│                                                                     │
│  ┌──────────┐  ┌──────────────────────────────────────────────┐     │
│  │ History  │  │  CONVERSATION (Phase 1) — stands alone       │     │
│  │ sidebar  │  │                                              │     │
│  │ (Ph 2)   │  │  Thread header · chart pin · model pill      │     │
│  │          │  │  Arrival line (chrome, once per session)     │     │
│  │ threads  │  │  ────────────────────────────────────────    │     │
│  │ by chart │  │  Turn 1                                      │     │
│  │          │  │   ├ working region                           │     │
│  │ Samīkṣā  │  │   ├ answer region (± prediction card)        │     │
│  │ tab (Ph2)│  │   └ grounding region                         │     │
│  │  + badge │  │  Turn 2 …                                    │     │
│  │          │  │  ────────────────────────────────────────    │     │
│  │          │  │  Depth · Length · Model  +  Composer (pinned)│     │
│  └──────────┘  └──────────────────────────────────────────────┘     │
│                 (reference rail REMOVED — native ruling 2026-07-27) │
│                                                                     │
│  Overlays: citation card (popover/sheet) · settings (Ph 2) ·        │
│            model picker (popover from composer)                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 What lives where

| Element | Home | Phase | Notes |
|---|---|---|---|
| Thread header | Top of conversation column | 1 | Chart pin ("Abhisek Mohanty · Aries lagna · b. 1984") + model pill + thread title. The frame check that satisfies B.11 for retrieval-depth turns lives here conceptually — every turn is visibly *of a chart*. |
| Arrival line `[ELEVATION v0.2]` | Beneath thread header (chrome, non-scrolling) | 1 | One quiet Inter line on thread open: current daśā year + open prediction windows ("Śani daśā, fourth year · one window open — mid-2027"). Once per session; derived from L1/Kāla truth, never model-composed (J2, P9). |
| The three-region turn | Conversation column | 1 | §5. The atom of the product. |
| Composer | Pinned to column bottom | 1 | Multiline, submit, model picker, stop control during streaming. |
| Citation card | Popover (desktop) / bottom sheet (mobile) | 1 | Opens from a chip; never navigates away. |
| Honest-gap ribbon | Inline in answer region | 1 | A block type, not an overlay. |
| Prediction card | Inline in answer region when a turn emits a time-indexed claim | 1 (render) / 2 (lifecycle) | Rendered in Phase 1 as a settled block; its review lifecycle is Samīkṣā, Phase 2. |
| History sidebar | Left rail, collapsible | 2 | Threads grouped by chart; search. |
| Samīkṣā | Sidebar tab + badge; own panel | 2 | Prediction review queue, window-close prompts. |
| ~~Reference rail~~ | — | — | **REMOVED (native ruling 2026-07-27).** The rail was the Vedic chart (kuṇḍalī, lagna, current daśā). The native does not want a chart panel — the reading speaks the chart in prose; there is no diagram to cross-reference. The conversation column stands alone. Any factor a citation needs is shown in the citation card, not a persistent rail. |
| Settings / model management | Overlay | 2 | Provider keys, defaults, cost. Mid-conversation model *switching* is Phase 1 (composer); model *management* is Phase 2. |

### 3.3 Navigation model

- **One level deep, always.** Dashboard → Paripraśna → (thread). No route deeper than a thread. Citation cards, working-region expansion, and grade details are in-place overlays/disclosures — the reader never loses the transcript.
- **URL scheme:** `/pariprashna` (last thread or empty state) · `/pariprashna/t/{thread_id}` · `/pariprashna/t/{thread_id}#turn-{n}` (deep link to a turn; used by Samīkṣā "this prediction came from…" back-references in Phase 2).
- **Chart context is thread-scoped.** A thread binds to exactly one chart at creation (from the dashboard entry point or a chart picker in the empty state). No mid-thread chart switching — that is a new thread. This keeps every turn's frame check unambiguous.
- **Entry from the dashboard:** each built chart's card carries "Open Paripraśna" → new or most-recent thread for that chart. A global nav entry opens the last active thread.

### 3.4 The turn as the IA atom

Everything in Phase 1 is a composition of turns. A turn's three regions have a fixed vertical order and fixed mount policy:

```
┌─ TURN ────────────────────────────────────────────────┐
│ ① WORKING REGION   mounts at turn open, never unmounts │
│ ② ANSWER REGION    blocks append; one volatile tail    │
│ ③ GROUNDING REGION mounts once, post-settle, below     │
└────────────────────────────────────────────────────────┘
```

This ordering is a design commitment, not an implementation detail: the reader's eye learns that *status is above, prose is middle, warrant is below*, for every turn, forever.

---

## 4. User journeys (Phase 1)

Each journey names the states traversed (state names defined in §5.2). These are the narratives the interaction design must make true.

### 4.0 Two trust arcs above the journeys `[ELEVATION v0.2]`

The journeys design *turns*. Two longer arcs sit above them, and every journey must serve both:

- **The guest's first five minutes.** A guest arrives carrying a lifetime of exposure to astrology-as-carnival. The trust sequence is fixed and designable: (1) the restraint of the surface — jet, one gold, no mystique — says *this is not a fortune site* before a word is read; (2) the first reading's specificity to *their* chart does what no marketing could; (3) the grounding ledger — the moment a guest sees a reading carry its own warrant is the moment the category flips from oracle to instrument; (4) the first honest gap, when one occurs — nothing converts skepticism faster than the instrument declining to know. Design implication: nothing on the first screen may *spend* trust (no ornament that promises magic, no cosmic theater), because the ledger will earn it wholesale two minutes later.
- **The native's hundredth conversation.** Daily return is sustained by *accrual*, not novelty (P9): the arrival line that says where the daśā and the open windows stand; predictions that come back to be graded (J8); contradictions that visibly weight later readings. The instrument must feel like a ledger-keeping companion across years, or daily use decays into occasional consultation. Phase 1 plants the seeds (arrival line, prediction card, contradiction note); Phase 2's Samīkṣā is the arc's engine.

### J1 — First question

*States: `empty` → `composing` → `submitted` → `thinking` → `streaming` → `settling` → `settled`.*

1. The native opens Paripraśna from Abhisek's chart card. **Empty state**: jet-black field, a single ivory Cormorant line — *"Ask the chart."* — beneath it a hairline-bordered composer, and three quiet example prompts in Inter (drawn from the chart: "What does this period ask of my career?"). No dashboard chrome shouting. Focus is already in the composer.
2. He types "What is the honest picture of my career over the next two years?" The composer grows to three lines without moving the field above it (**composing**). Enter submits (Shift+Enter for newline).
3. Instantly (**submitted**, < 100 ms, optimistic): his question renders as a settled user block — ivory Inter, right-set — and beneath it the turn's **working region** mounts at its permanent height: a single stable band, gold eyebrow lettering: `CONSULTING THE CHART` with a live elapsed counter `· 4s`. A thin gold progress hairline breathes beneath the band (opacity oscillation, not movement).
4. The engine plans a deep route (this is an interpretive query → dossier path). The working band's label updates *in place* — `CONSULTING THE CHART — DAŚĀ STRUCTURE · 9s` — text swap only, zero geometry change (**thinking**). A disclosure chevron sits at the band's right edge; he ignores it. (If he clicked: collapsed activity rows expand *in place below the band* — "Read 214 chart facts · Vimśottarī daśā spine · 2 classical passages consulted" — pushing only the unstarted answer region down, never anything settled.)
5. First prose arrives (**streaming**). The answer region opens below the working band. Prose flows in Cormorant Garamond, committed paragraph by paragraph: each completed block freezes; only the tail block is volatile; the caret sits at the end of the last text node, always. A table of daśā windows arrives mid-answer: it renders *complete* (tables are commit-only block types, never streamed raggedly — §5.6), and the caret continues *after* it, in the next text block — never beneath or inside it.
6. The final token lands (**settling**): the working band flips, in the same box, to `GROUNDED IN 14 CHART FACTORS · 3 CLASSICAL SOURCES · 41s` — same geometry, new content. The caret fades out (120 ms). The **grounding region** fades in below the answer (160 ms): citation chips `⟦1⟧–⟦6⟧` with source labels, a grade summary ("Core claim: well-grounded"), and — because this was a dossier route — the line *"Composed from complete house coverage."*
7. **Settled.** Nothing on this turn will ever move again. The composer, which dimmed to 60 % during streaming, returns to full presence with focus.

*What must never happen in J1:* the question jumping when the working region mounts; the working band changing height when its label changes; a paragraph re-wrapping when a citation chip resolves; the caret rendering under the daśā table; raw tool names or `SIG.MSR.413` anywhere.

### J2 — Follow-up in an existing thread

*States: `settled` → `composing` → `submitted` → `thinking` → `streaming` → `settled`.*

1. Later, he reopens the thread. It restores scrolled to the last settled turn, composer focused. Prior turns are fully settled — working bands showing their grounded summaries, grounding regions present. `[ELEVATION v0.2]` Beneath the thread header sits a single quiet **arrival line** — Inter 12.5, `--ink-dim`, one line, never more: *"Śani daśā, fourth year · one prediction window open — mid-2027."* It is the instrument saying *I know where we are* before a word is typed. It is chrome, not transcript (it does not scroll with prose), renders once per session, and is derived from L1/Kāla truth via the same capability surface as everything else — never composed by the model.
2. He asks "And within that, when specifically should I not initiate anything new?" The new turn appends below. **Scroll discipline:** the viewport anchors so the new question sits in the upper third; as the answer streams, the view follows the tail *only if* he was already at the bottom. The moment he scrolls up to re-read turn 1, following stops; a quiet gold pill — `↓ Reading continues` — floats at the field's bottom edge. Tapping it resumes following. Streaming never fights his scroll.
3. The follow-up is timing-specific → the planner routes a narrower retrieval; the working band reads `CONSULTING THE CHART — TRANSIT WINDOWS · 3s` and settles in 8 s with `GROUNDED IN 6 CHART FACTORS`. The smaller count is honest and visible (P5): shallow-when-appropriate is legitimate; *invisible* shallowness is not.

### J3 — A hard reading (health, asked in fear)

*States: as J1, plus the emotional-register rules of §7 shaping streaming and settled content.*

1. A guest — the native's family member, on her own chart — types "Is there serious illness coming for me in the next few years?"
2. No special "sensitive mode" banner appears (P3 — flagging the question as scary *is* scary). The working region behaves exactly as always: the sameness is the calm.
3. The answer streams with designed pacing (§7.2): the first committed block is the *stance*, short and steady — uncertainty up front, never a cliff-hanger structure that makes her read 400 words to learn if she should be afraid. Hard content arrives in shorter blocks with more frequent commits (the engine's composition contract, §8.4): each paragraph settles quickly, so she is never mid-sentence on a frightening clause in a volatile block.
4. A probability is involved. The prose says: *"…a period that asks for attention to health, more likely than not to pass without a serious event — hold that loosely."* A small gold expansion affordance follows the phrase; tapping it opens a quiet inline detail: the calibrated figure, the window, and the calibration basis in one sentence (P6).
5. The chart is partly silent on her specific fear. An **honest-gap ribbon** renders as its own settled block: hairline gold border, faint gold tint field, Inter text — *"On the specific question of surgery, this chart is silent. Silence here is a finding: the factors that would speak to it are unremarkable."* Neutral, unmissable, unpanicked (T-5 + P3).
6. Remedial matter is attributive: *"For this period, the tradition prescribes…"* (P7).
7. Grounding settles as always: her warrant to trust — or to question — the reading is on the surface, same as the native's.

### J4 — Disagreeing with a reading

*States: `settled` → `composing` → `submitted` → `thinking` (recall-inflected) → `streaming` → `settled`.*

1. The native reads a career verdict and replies: "This doesn't match — 2019 was actually my best year, not a setback."
2. The instrument treats this as **data, not debate** (this is the calibration loop's front door). The working band reads `WEIGHING THE DISAGREEMENT · 5s`; expanded activity shows it re-consulted the life-event log and the original turn's grounding.
3. The answer follows the disagreement contract (§7.6): (a) restate his account plainly and without concession-flavored hedging; (b) show what the chart said and *on what grounds* — chips to the same citations; (c) name the reconciliation honestly — refined reading, timing offset, or a standing contradiction; (d) if it is a contradiction, say so as a finding: *"Held as an open contradiction against this chart — it will weight future readings."* A small settled block — a **contradiction note**, visually a sibling of the prediction card — records it.
4. Nothing about the *original* turn is edited or annotated retroactively (P1 — settled turns are the audit trail). The reconciliation lives in the new turn.

### J5 — Mid-conversation model switch

*States: `settled` → (picker open) → `composing` → `submitted` → …*

1. Mid-thread, the native taps the **model pill** in the composer ("Claude Opus"). A popover lists providers/models (Gemini · Claude · OpenAI · DeepSeek · OpenRouter) in Inter, each one line: name, a terse capability note, latency class. No logos parade; this is an instrument setting, not a brand shelf.
2. He selects Gemini. The pill updates. A one-line system note appends to the transcript as a settled micro-block — `Model changed: Claude Opus → Gemini 3 Pro` in mono, hairline-topped — so the audit trail of *which model produced which reading* is in the transcript itself, not hidden in metadata.
3. The next turn runs on Gemini. **Everything about the turn's choreography is identical** — regions, bands, chips, grades are Paripraśna's, not the provider's. The reader should be unable to tell providers apart by layout; only the pill and the system note tell.
4. If the switched-to provider fails midstream, the reconnect/error design (J6, §5.9) applies uniformly — with the taxonomy naming the provider when relevant ("Gemini is overloaded at the moment").

### J6 — Reconnect after a network drop

*States: `streaming` → `reconnecting` → (`streaming` resumed | `interrupted`).*

1. Mid-stream on the train, the connection drops. **The prose does not vanish, gray out, or shake.** Every committed block stays exactly as it was (P1). The tail block's caret changes to a hollow caret; the working band's counter freezes and the band appends, in place, `— RECONNECTING` (**reconnecting**). One quiet state, no toast, no red.
2. The client resumes the stream (§8.5: server-buffered turn + `Last-Event-ID`). Deltas the client already applied are discarded idempotently; the caret refills; streaming continues *as if nothing happened*. Target: a drop under 30 s is a non-event.
3. If resume fails past the window, the turn enters **interrupted**: the tail block commits as-is with a hairline rule and a calm line beneath: *"The connection was lost partway. What arrived is above; nothing was altered."* A single gold-outlined **Continue** action asks the engine to complete the answer as a continuation turn. Partial prose is never deleted (it may already have been read — sacred) and never silently patched.

### J7 — An honest-gap answer

*States: as J1, ending in `settled` with gap presentation.*

1. Question: "Should I take the Dubai offer or the Singapore one?" The engine finds the chart genuinely non-discriminating between the two.
2. The answer does not stall, over-hedge, or manufacture a difference. It reads what the chart *does* say (the period's character for relocation generally), then an honest-gap ribbon states the boundary: *"Between these two, the chart is silent — no factor consulted distinguishes them. The choice is yours on other grounds; the chart speaks to the timing either way."*
3. The grounding region still renders with real counts — a gap answer is still a grounded answer; the grounding is *how we know it's silent* (P2, P5). The grade summary reads `Honest gap — silence verified across consulted factors.`
4. Visual temperature: identical to any other settled turn. The ribbon is typographically distinct (unmissable) but chromatically neutral (calm). Both at once — that duality is the whole design of the component (§6.8).

### J8 — The reading that returns `[ELEVATION v0.2]` *(the signature arc; Phase 1 renders, Phase 2 completes)*

*States: `idle` → prompted → `composing` → `submitted` → `thinking` (recall-inflected) → `streaming` → `settled`.*

1. Months after J1, the mid-2027 window from that turn's prediction card enters its final weeks. In any thread of that chart, a one-line band appears above the composer — *"A reading's window closes this week — review when ready."* Dismissible, never modal, never nagging (P3, §10.2). On the card itself, the kāla-rekhā's today-dot (§6.9) has visibly crossed into the gold window segment — time made physical, without a single notification.
2. The native opens the prompt. Samīkṣā does not present a form; it opens a **turn** the instrument frames: *"In July I read an occupational shift, self-initiated, most likely around mid-2027 ⟦→⟧. The window is closing — what happened?"* The back-reference chip deep-links to the original turn (§3.3), which is byte-identical to the day it settled (P1 — the transcript *is* the audit trail).
3. He answers in prose, as always. The instrument grades the outcome against the framed claim, records it to L5, and the original prediction card's **eyebrow ages in place** — `TIME-INDEXED READING · RESOLVED — CONFIRMED` — the only retroactive change a settled turn ever receives, and it is eyebrow text only, geometry untouched (§6.9).
4. The next reading that touches career carries a new line in its grounding region: *"This instrument's prior call on this domain resolved true."* The calibration loop closes **on the reading surface**, where it convinces — not in a buried stats panel.

*Why this is the signature:* every chat product answers; none is accountable months later for what it said. The prediction card with its lifecycle is the one component no competitor can copy, because no competitor has an L5 behind it. J8 is the arc that turns the instrument's central claim — calibrated, testable, correctable — from an architecture diagram into a felt experience.

---

## 5. Interaction & state design — the heart of Phase 1

### 5.1 The three-region turn, normatively

```
┌─ TURN (assistant) ──────────────────────────────────────────────────┐
│                                                                     │
│ ① WORKING REGION — the stable band                                  │
│ ┌─────────────────────────────────────────────────────────┐         │
│ │ ⟡ CONSULTING THE CHART — DAŚĀ STRUCTURE          · 12s ⌄│  h: 40px│
│ └─────────────────────────────────────────────────────────┘  FIXED  │
│   (expanded, optional, grows DOWNWARD only:)                        │
│ │  · Read 214 chart facts                                           │
│ │  · Vimśottarī daśā spine · 3 levels                               │
│ │  · Bṛhat Parāśara Horā Śāstra — 2 passages                        │
│                                                                     │
│ ② ANSWER REGION                                                     │
│   [frozen block]  paragraph …                          ── committed │
│   [frozen block]  daśā table (rendered whole)          ── committed │
│   [frozen block]  paragraph …                          ── committed │
│   [VOLATILE TAIL] current paragraph streaming ▊         ── the only │
│                                                            movable  │
│ ③ GROUNDING REGION (mounts once, at settle)                         │
│ ┌─────────────────────────────────────────────────────────┐         │
│ │ Grounded in 14 chart factors · 3 classical sources      │         │
│ │ ⟦1⟧ Saturn daśā · ⟦2⟧ 10th lord · ⟦3⟧ BPHS 34.12 · …    │         │
│ │ Core claim: WELL-GROUNDED ● │ Composed: full coverage   │         │
│ └─────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

**Region contracts (the non-negotiables):**

- **① Working region.** Mounts the instant the turn opens, at its final fixed height (40 px band). It **never unmounts** — at settle its content flips in the same box from status to summary (`CONSULTING… · 12s` → `GROUNDED IN 14 SOURCES · 12s`). Label changes are text-swaps at constant height. Expansion is user-initiated only, grows strictly downward, and only ever displaces the (not-yet-started or below-tail) content — never anything above it. Activity rows inside are append-only and individually stable once written (`activity.upsert` may update a row's *status glyph*, never its geometry).
- **② Answer region.** A vertical list of **blocks**. A block is born volatile (the tail), receives deltas, then **commits** and freezes — its DOM subtree memoized, never re-rendered, removed from the aria-live region (§9). Exactly **zero or one** volatile block exists at any moment. The caret is an inline element owned by the tail block, positioned after its last text node; block types that cannot host a caret gracefully (tables, block-quotes of verses) are **commit-only**: they arrive whole via `block.open`+`block.commit`, and the caret lives in the following text block. **The caret can never orphan** because it is never positioned by layout guesswork — it is a DOM child of the text it trails.
- **③ Grounding region.** Mounts exactly once, after `turn.commit`, below the final answer block, with a 160 ms fade (opacity only). It never mounts early, never reflows the answer, and once mounted is settled content (P1).

### 5.2 The state machine (per turn) and (per surface)

**Turn states:** `submitted → thinking → streaming ⇄ reconnecting → settling → settled`, with exits to `interrupted` (resume window exceeded) and `errored` (classified failure before/without partial prose). Settled/interrupted/errored are terminal and immutable.

**Surface states:** `empty` (no thread content), `idle` (thread open, no active turn), `composing` (text in composer), plus the active turn's state. The composer is enabled in all surface states; during an active turn it accepts typing but its submit becomes **Stop** (one active turn at a time).

### 5.3 State-by-state specification

For each state: what the user sees · what must never happen.

**`empty`** — *Sees:* the invocation `[ELEVATION v0.2]`: one 1 px gold hairline — the **ecliptic line** (`--rule`) — drawn across the empty field at ~38% height, scaleX 0→1 from center over 400 ms on mount (the surface's arrival gesture; instant under reduced motion). Centered above it, "Ask the chart." (Cormorant, 28 px ivory) with the chart pin over it; below it, the focused composer and 3 chart-aware example prompts as quiet gold-hairline pills. The ecliptic line is the same stroke the turn separator uses (§6.4) — the empty state and the settled transcript speak one geometric language, and the line quietly *is* the cosmology: a single horizon, nothing else. *Never:* a blank void with an unfocused input; generic examples ("Tell me about astrology"); dashboard chrome noise; any star field, wheel, or zodiac figure — the line is the entire astronomy of the surface.

**`composing`** — *Sees:* composer grows downward up to 8 lines then scrolls internally; field above does not move; character of the border sharpens (hairline 0.25 → 0.50 alpha). Submit affordance (↵ glyph) turns from dim to full gold when non-empty. *Never:* the transcript shifting as the composer grows (the transcript column reserves the max-composer height? No — the composer overlays its growth over a bottom gutter: transcript bottom padding = max composer height, so growth fills reserved space); Enter ambiguity (Enter submits; Shift+Enter newline; documented in placeholder on first run).

**`submitted`** — *Sees:* user block renders instantly (optimistic), composer clears, working band mounts at once with `CONSULTING THE CHART · 0s` before any server ack. *Never:* a dead beat between Enter and *anything* (M3); the user's own text repainting when the server echoes it (client text is authoritative for display).

**`thinking`** — *Sees:* the band's phase label updates in place as `phase` events arrive; elapsed counter ticks (1 s resolution — a calm clock, not a stopwatch); breathing hairline. Long thinks (> 20 s) surface the *current* activity row's short label into the band ("— CROSS-CHECKING YOGAS") so waiting has narrative. *Never:* height change on label swap (band text truncates with ellipsis, never wraps); raw tool names/IDs in labels (labels come from a curated phase lexicon, §7.8); a spinner instead of the counted band (a counter says *working*; a spinner says *stuck*).

**`streaming`** — *Sees:* §5.1 answer-region contract; §5.5 scroll rules; composer dims to 60 %, submit becomes Stop (gold square-in-circle, hairline). *Never:* ANY layout mutation above the tail (M1); caret detachment (M2); markdown re-parse flicker (committed blocks are parse-final); style transmutation (text that later becomes a chip/bold/heading — the wire protocol commits only at safe boundaries, §8.4); mid-word tail flushes on slow streams (tail applies deltas on rAF, coalesced).

**`settling`** — a named choreography: **the Seal** `[ELEVATION v0.2]`, 300–600 ms, strictly ordered: (1) tail commits & freezes; (2) caret fades 120 ms; (3) working band content flips in place (status → grounded summary); (4) grounding region fades in 160 ms; (5) the turn's **closing rule** — the centered 64 px hairline of §6.4 — draws in beneath the grounding region, scaleX 0→1 from center, 400 ms: the surface's one deliberate flourish, the visible moment the reading is sealed; (6) composer restores to full presence with focus. Under reduced motion, steps collapse to instant appearances in the same order. *Never:* reordered or overlapped steps producing simultaneous movement in two places (one thing settles at a time — the eye is escorted); a scroll jump when grounding mounts (if the tail was at viewport bottom, mount scrolls *the minimum* to reveal the grounding band's first line, 200 ms ease, and only if the user was following).

**`settled`** — *Sees:* the immutable turn. Hoverable chips, expandable band, expandable probability details — all disclosures overlay or grow downward into inter-turn space. *Never:* any re-render of settled DOM (verified by React profiler in dev harness); disclosure of one turn shifting another settled turn's content upward.

**`honest-gap`** (a settled sub-state) — *Sees:* §4 J7 + §6.8 ribbon. *Never:* warning iconography; the gap buried mid-paragraph as prose only (it is always *also* a ribbon block — unmissable); an empty grounding region (silence is grounded too).

**`errored`** — *Sees:* the working band flips to a calm terminal label per the classify-error taxonomy (§7.5): `THE MODEL IS OVERLOADED — NOTHING WAS LOST`. Below the band, one short Inter sentence and one action (Retry — re-runs the turn; the user block stays). Field temperature unchanged. *Never:* red; stack traces; the word "error" in display copy where a plainer word serves; a retry that duplicates the user block.

**`reconnecting` / `interrupted`** — per J6. *Never:* graying-out committed prose; auto-deleting partial prose; more than one visual element changing to signal the drop (the band alone carries it).

### 5.4 Cursor/caret discipline (the named pain, designed out)

1. The caret is a styled inline `<span>` — 2 px gold bar, 1.1 em — that is a **DOM sibling of the streaming text node** inside the tail block. It moves because text is inserted before it, never by coordinate math.
2. Commit-only blocks (tables, verse quotes, prediction cards) never host the caret. On `block.open(table)`, the caret's home is the *next* text block, which opens immediately (possibly empty) — so during table render the caret idles at the start of the following empty text block, *below* the table, on the left margin: a deliberate, stable "awaiting prose" position. It is never *under* a table because the table's block and the caret's block are different elements with committed geometry.
3. At `turn.commit`, the caret fades then unmounts. It never persists into settled content.
4. Exactly one caret exists per surface (one active turn). Reconnect swaps its fill (solid→hollow) — same element, no reflow.

### 5.5 Scroll discipline

- **Follow mode** is on iff the reader is within 120 px of the bottom. Any upward user scroll disables it instantly; the `↓ Reading continues` pill appears (bottom-center, hairline pill, Inter 12) and re-enables on tap or on scrolling back to bottom.
- Auto-follow scrolls via `scrollTop` assignment on the same rAF as tail paint — one writer, no smooth-scroll fighting streaming.
- New-turn anchoring: on submit, scroll places the user block in the upper third (constant, predictable — the reader always knows where their question went).
- `overflow-anchor` is disabled in the transcript; anchoring is owned by our logic, not the browser's heuristic (the browser's anchor is exactly what shoved carets under tables historically).

### 5.6 Streaming content types

| Block type | Streamed? | Notes |
|---|---|---|
| Paragraph (prose) | Yes — delta'd tail | Cormorant; commits at paragraph boundary |
| Heading | Commit-only | Arrives whole; prevents "# Care" → "# Career" transmutation |
| List | Item-wise: each `<li>` is delta'd, commits per item | Caret lives in the current item |
| Table | Commit-only | Server buffers full table before emitting; renders complete with committed column widths |
| Verse / classical quote | Commit-only | Distinct styling (§6.5); Sanskrit + gloss |
| Honest-gap ribbon | Commit-only | |
| Prediction card | Commit-only | |
| Citation chip | Inline token within prose blocks | Sentinel rewritten server-side pre-wire; renders at final geometry: fixed-width numbered chip. Chip *cards* hydrate lazily; the chip itself never changes size (M6) |
| Probability detail | Inline disclosure within prose | The framed phrase is prose; the expansion affordance is a fixed-geometry inline glyph |

### 5.7 Motion & micro-interaction principles

- Palette of motion: opacity and transform only. Durations: 120 ms (micro: caret, chip hover), 160–200 ms (region mounts), 240 ms max (sheet/popover). Easing `cubic-bezier(0.25, 0.6, 0.3, 1)` everywhere.
- Nothing animates unprompted twice: the breathing hairline in `thinking` is the sole ambient motion on the surface, and it stops at settle.
- Token application is frame-decoupled: deltas buffer; one DOM write per rAF; long deltas (post-reconnect catch-up) apply in a single write, no replay animation.
- `prefers-reduced-motion`: breathing hairline → static 50 %-alpha hairline; fades → instant; auto-follow → instant jumps on commit boundaries only.
- **The motion constitution `[ELEVATION v0.2]` (the system, named):** nothing animates faster than 120 ms or slower than 400 ms; only `opacity` and `transform` ever animate; one easing curve for the entire surface (`cubic-bezier(0.25, 0.6, 0.3, 1)`); at most one element moves at a time; the only *ambient* motion is the thinking hairline's breath, and the only motion above 240 ms is the Seal's closing-rule draw and the empty state's ecliptic line — the same 400 ms gesture opening and closing the surface's life. Everything else: 120 ms micro (caret, chip hover), 160–200 ms region mounts, 240 ms sheets/popovers. Any animation that cannot cite its slot in this constitution is cut in review.
- **Sound — decided, recorded as SND-1 `[ELEVATION v0.2]`:** the instrument has exactly one sound — an optional **settle tone** at the Seal: a single soft struck note, ~180 ms, low-mid register, mixed very quiet, **off by default**, per-user setting. No send sound, no error sound, no typing sound — an error that *sounds* is an alarm (P3), and a keystroke that sounds is a toy. If the one tone reads as notification noise during AC-15 week, it is deleted without ceremony.

### 5.8 The composer

- Structure: a hairline-bordered field bar `[ multiline field ] [ submit/stop ]`, with a **control cluster directly above it**: `[ Depth ] [ Length ] [ Model ]` as three pill popovers, left-aligned, plus a right-aligned footnote (`acharya-grade · one register`, which changes to a `… override` note when a control leaves Auto).
- Multiline, autogrowing 1→8 lines; internal scroll beyond. Enter submits; Shift+Enter breaks; Esc clears focus (and, second press, collapses any expanded working region — the keyboard walks outward).
- During an active turn: field stays editable (draft the follow-up while listening), submit is replaced by **Stop**. Stop halts generation; the turn settles as `interrupted` with what arrived (never discarded).
- Attachments: **none in Phase 1** (non-goal — the instrument reads the chart, not documents). The bar reserves no dead space for them.
- Switching model mid-thread emits the system micro-block (J5).

#### 5.8.0 Native layout rulings — 2026-07-27 [v0.3, binding]

Five rulings from the native's hero-mockup review, integrated here and in §3/§6:

1. **Header:** clear breathing room between the *Paripraśna* wordmark and the chart-holder's name (they must never read as one string). **Right side of the header carries the `MARSYS JIS` wordmark — not the provenance stamp.** Build id / priors move out of the header entirely; provenance lives in the audit drawer and the right dock's footer, available on demand, never ambient chrome.
2. **The right dock (collapsible).** To maximize vertical room for the conversation, the **prediction card + kāla-rekhā and the grounding ledger move into a collapsible right panel**. The conversation column carries prose and chips only; region ③ (grounding) *docks* right instead of mounting inline. Chips still deep-link: clicking ⟦n⟧ opens the dock to that row. Collapsed by default on smaller widths; remembered per user.
3. **Left sidebar (collapsible): past readings.** Thread history — title, date, active-thread tick — collapsible to icons, remembered per user.
4. **Control order: `Model → Depth → Length`.** Model first (the native's primary control), then the two Auto-defaulting shapers.
5. **Composer field: ≥3 lines tall at rest** (~3 × line-height ≈ 96px min-height), growing to 8; the question deserves room to be composed, not a slit.

Three further rulings — 2026-07-27, second review [binding]:

6. **Thinking is ONE line by default.** The working band's resting state shows only the *current* activity — the live line updates in place as phases advance ("Retrieved — timing cycles…" → "Consulting the classics…"). No ledger visible unless asked. Clicking the band expands the full ledger **inside a fixed-height, internally-scrolling well (~5 rows visible)** — expansion never grows the turn unboundedly; the user scrolls within it. Collapse returns to one line. All completed history is retained and reachable; none of it is ambient.
7. **The conversation viewport is FIXED-HEIGHT.** The thread region owns its own scroll; the frame's geometry never changes as a response streams. While the user is at bottom, the view follows the stream (pinned-follow). The moment the streaming content exceeds the viewport with the user unpinned — or the user scrolls up — a **↓ follow pill** appears; clicking it (or scrolling to bottom) re-pins. The page never grows; the reading scrolls. This makes §5.5's follow discipline *structural*: the scroll container is the component, not the page.
8a. **[2026-07-27, third review] Adaptive multi-pass turns — the pass-seam model.** When an agentic model interleaves (reason → tools → partial prose → more tools → enhanced prose → …): **one working band per turn**, whose ledger groups rows under `PASS 1 / PASS 2 / …`; and between prose segments an inline **pass seam** — a one-line working indicator in the §7.8 lexicon (`LOOKING FURTHER — THE DIVISIONAL CHARTS…`) rendered *where the next segment will continue*, which **settles in place** into a slim hairline divider recording the pass (`· LOOKED FURTHER · 2 RETRIEVALS · 1.8s ·`). Properties: prose segments freeze as always; the seam is appended, mutates only itself, never unmounts — append-only holds across passes; the band's live line and the active seam always agree; grounding accrues in the dock across passes (count ticks up). Seam lexicon entries: `LOOKING FURTHER —`, `READING DEEPER —`, `CROSS-CHECKING BEFORE CONCLUDING`, `RECONSIDERING —` (post-gate revision).
8b. **[2026-07-27, third review] Grounding lives in the right dock, not inline** — applied to the interactive mockup (the earlier inline region ③ is retired in favour of the ruling-2 dock everywhere). The conversation column carries prose + ⟦n⟧ chips only; chips deep-link into the dock, opening it if collapsed.
8c. **[2026-07-27, third review] Provenance is visible NOWHERE ambient** — amends ruling 1: not the header, **not the dock footer either**. Build id / priors / stamp live exclusively behind the audit affordance (the drawer). The surface never shows them unasked.

8. **Tool calls are visible, named by the data point they serve.** Every retrieval appears as its own ledger row — `RETRIEVED — TIMING CYCLES · 536 periods · 0.6s`, `RETRIEVED — YOGA COMBINATIONS, CROSS-CHECKED · 12 firings` — with counts in mono. **Never the internal tool name** (`ganita_dashas_get` etc. live only behind the audit affordance). The `RETRIEVED — ⟨data point⟩` pattern joins the §7.8 closed lexicon; the label comes from the registry's reader vocabulary, so an unmapped tool falls back to `RETRIEVED — CHART DATA` + CI warning rather than leaking its id.

#### 5.8.1 The three query controls (D-19)

Three per-query controls sit above the field. **All shape the query; none is an audience tier.** D-14 (one reader-legible register) and D-15's core (no tiers, acharya-grade always) are intact: Depth changes *how much the engine looks*, Length changes *how much it says*, neither changes *the standard* or *the register*. **Auto is the default for Depth and Length and is exactly the scope-tuple derivation the engine already performs** — the control surfaces that derivation and lets the user override it. This is a refinement of D-15, not a reversal: D-15 removed the *hidden* depth parameter and the *audience tier*; D-19 restores a *visible, user-owned, Auto-defaulting* depth-and-length control.

**Depth** — how much of the chart and how many corroborating layers the engine brings to bear:

| Option | Behaviour |
|---|---|
| **Auto** *(default)* | Derived from the question via the DR-8 scope tuple. Pinpoint factual → light fast pass (RS-4 proportionality carve-out); life question → full whole-chart read. |
| **Quick** | Pinpoint / factual lookup. Fast, targeted. |
| **Standard** | The full acharya-grade whole-chart read (Bodha-first, B.11). |
| **Deep dive** | Forces the completeness-gated composition (`dossier`, 100% coverage), all corroborating layers, cross-domain links surfaced. **This is the user's lever on the depth the planner otherwise under-routes (G4 / the 15–33% dossier-defeat finding).** Slower. |

**Length** — how much prose the *same* reading is expressed in:

| Option | Behaviour |
|---|---|
| **Auto** *(default)* | Matched to the question and the weight of the finding. A hard reading gets room; a quick one stays tight. |
| **Concise** | Verdict + essential grounding, tightly. |
| **Balanced** | Standard. |
| **Detailed** | Full elaboration — every nuance and caveat. |

**Model** — the synthesizing LLM. Unlike Depth/Length, its default is an **explicit model** (Claude Opus), not Auto, because the native has chosen to own model selection; an **Auto (best available)** option sits at the top of the list for those who don't care. The picker lists Gemini · Claude · OpenAI · DeepSeek · OpenRouter, each with its capability tier (A full-loop / B compact / C bundle) — mid-thread switching is live (J5).

**Interaction rules:** all three are pill popovers (Inter 12, gold-on-tint), one open at a time, closing on outside-click; the selected value shows in the pill; a non-Auto selection is reflected in the footnote so the user always knows when they've left Auto; state is remembered per thread (a Deep-dive thread stays Deep-dive until changed). On mobile they collapse into a single "controls" affordance above the field (§9).

### 5.9 Failure choreography (uniform across providers)

One design for all five providers. The classify-error taxonomy (`rate_limit`, `model_overload`, `timeout`, `network`, `auth`, `unknown`) maps to: (a) a band label; (b) one sentence of Inter copy; (c) one action. Copy in §7.5. Auto-retry policy: `network` retries silently within the reconnect window before surfacing anything; `rate_limit`/`overload` surface immediately with Retry (and, natively, the suggestion to switch models — the picker opens pre-filtered to healthy providers); `timeout` surfaces with Continue (attempt completion) and Retry.

---

## 6. Visual design system (Marsys-inherited)

### 6.1 Token table (authoritative for this surface)

| Token | Value | Use |
|---|---|---|
| `--surface` | `#000000` | The field. Pure jet. No gradients in the field, ever. |
| `--ink` | `#EBE3D2` | Primary text (prose, headings) |
| `--ink-dim` | `rgba(235,227,210,0.64)` | Secondary text (activity rows, metadata prose) |
| `--gold` | `#C9A24C` | The single accent: eyebrows, chips, caret, icons, actions |
| `--gold-dim` | `#A37F37` | Secondary gold (inactive pills, counters) |
| `--gold-tertiary` | `#7A5A1F` | Hairlines at rest, tertiary marks |
| `--gold-foil` | `linear-gradient(#F2D88A, #E0B85A, #B8862E, #E8C77A)` | Foiled-metal text effect. Reserved: one emphasized word per surface at most (e.g. the wordmark "Paripraśna" in the header). Never in body, never on chips, never animated. |
| `--rule` | `rgba(201,162,76,0.25)` | Standard hairline |
| `--rule-strong` | `rgba(201,162,76,0.50)` | Active/focus hairline |
| `--tint` | `rgba(201,162,76,0.06)` | Faint field tint (ribbon fills, band fill, hover fills) |
| `--font-serif` | Cormorant Garamond | Display + reading prose |
| `--font-sans` | Inter | Data, eyebrows, activity rows, UI chrome |
| `--font-mono` | JetBrains Mono | Technical metadata, citation refs, audit detail |
| `--track-eyebrow` | `0.28em` | Eyebrow letter-spacing, uppercase Inter |
| Icons | Lucide-style, 1.6 px stroke, `--gold` tint | Metadata strips only. **No emoji. No colored glows. No shadows carrying color.** |

Elevation: overlays separate by a `--rule-strong` border + `rgba(0,0,0,0.6)` scrim, not drop shadows (shadows on pure black are invisible anyway; the hairline *is* the elevation language).

### 6.2 The Cormorant legibility decision (made, not hand-waved)

Cormorant Garamond is ceremonially right and mechanically thin: low x-height, delicate hairline strokes that fall apart small and dark-on-black. The ruling:

- **Reading prose (answer region): Cormorant Garamond Medium (500), 19 px / 1.62 line-height desktop, 18 px / 1.65 mobile, `letter-spacing 0.002em`, max measure 68ch.** The Medium weight is the load-bearing choice: at 400 on `#000`, ivory hairlines scintillate; 500 restores stroke mass without losing the face's character. 19 px puts its small x-height at the effective size of a 16–17 px workhorse serif.
- **Cormorant floor: 16 px / weight 500.** Below 16 px, Cormorant is banned — Inter takes over. This single rule decides every marginal case.
- Therefore **Inter owns:** all UI chrome, eyebrows, activity rows, chips, grounding metadata, table *cells* (data is sans — a daśā table is data), buttons, error copy, timestamps. **Cormorant owns:** answer prose, block quotes/verse glosses (18 px italic), display lines ("Ask the chart."), turn-level headings inside readings (24/28 px, 600).
- **JetBrains Mono owns:** citation reference strings inside cards (`BPHS 34.12`, fact refs when an entitled user drills), the model-switch micro-block, audit expansions. Mono never appears on the reading surface proper.
- Rendering guards: `-webkit-font-antialiasing: antialiased` on dark, `font-synthesis: none`, real italics only, `text-rendering: optimizeLegibility`; numerals in prose use lining figures via `font-feature-settings` (Cormorant's oldstyle figures dance distractingly in date-heavy readings).
- This is also flagged as Open Decision OD-1 (§12): if the native, reading on his own devices for a week, finds even Medium-500 Cormorant tiring, the prepared fallback is Cormorant for display + a sturdier literary serif (e.g. Source Serif 4) for body. The type ramp is built so this is a two-token swap.

### 6.3 Type ramp

| Style | Face | Size/LH | Weight | Use |
|---|---|---|---|---|
| Display | Cormorant | 28/34 | 600 | Empty-state invitation, Phase-2 panel titles |
| Reading H | Cormorant | 24/30 | 600 | Headings inside a reading |
| **Body (reading)** | **Cormorant** | **19/31** | **500** | **Answer prose** |
| Verse | Cormorant italic | 18/30 | 500 | Classical quotes + glosses |
| UI base | Inter | 14/20 | 450 | Chrome, cards, composer |
| Metadata | Inter | 12.5/18 | 450 | Activity rows, grounding line, timestamps |
| Eyebrow | Inter caps | 11/16, +0.28em | 600 | `CONSULTING THE CHART`, section eyebrows |
| Chip | Inter | 11.5/1 | 550 | Citation + grade chips |
| Mono meta | JetBrains Mono | 12/18 | 400 | Refs, audit detail, model-switch note |

### 6.3.1 The anatomy of a reading `[ELEVATION v0.2]`

A reading is set like a well-set legal opinion: holding first, reasoning after, dicta marked. Five block roles, each with a fixed treatment, so the eye can parse a reading's structure before reading a word of it:

| Role | Treatment |
|---|---|
| **Verdict** (first block; §7.1 rule 4) | Cormorant **21/34, 500** — one step above body, never bold; a **2 × 18 px solid gold tick** hangs in the left margin beside its first line — the only marginal mark prose ever receives. One verdict block per reading, ≤ 3 sentences. |
| **Elaboration** | Body 19/31 as ramped. No marks, no borders — naked ivory on jet. |
| **Verse / classical authority** | Cormorant italic 18/30, 2 px `--gold-tertiary` left rule, 20 px indent; gloss line beneath in `--ink-dim` (§6.6). |
| **Gloss (inline Sanskrit)** | Term in gold italic, plain gloss in `--ink-dim` roman parentheses — now normative: **gold in prose marks the tradition's own words and nothing else.** |
| **Caveat / boundary** | Closing block(s) that scope the reading, including the agency close (§7.2): Cormorant 17/28, `--ink-dim` — the voice audibly settling; above the 16 px floor, quieter than body. |

Rules: the verdict tick renders with its block (commit-only decoration, never added retroactively — P1); roles arrive on the wire as block metadata (`role: verdict | elaboration | verse | caveat` on `block.open`) so the anatomy is protocol, not client inference (§8.4.3).

### 6.4 Spacing & layout

4 px base unit. Conversation column: max 720 px, centered; answer prose measure 68ch within it. Vertical rhythm: 12 px between blocks within a region, 20 px between regions within a turn, 48 px between turns with a centered 64 px-wide `--rule` hairline as the turn separator (the **closing rule** — drawn by the Seal at settle, §5.3; the one ornamental gesture on the surface, and the same stroke as the empty state's ecliptic line and the prediction card's kāla-rekhā: one line, three duties `[ELEVATION v0.2]`). Composer gutter: transcript bottom padding reserves max composer height + 24 px.

### 6.5 Component: working-region band + activity rows

- **Band (rest/streaming):** 40 px fixed, full column width, `--tint` fill, `--rule` top & bottom hairlines. Left: 14 px Lucide glyph (`sparkle`-class, gold). Eyebrow-style label, single line, ellipsis. Right: counter (`--gold-dim`, Inter 12 tabular) + chevron. Breathing hairline: bottom border animates opacity 0.25→0.5, 2.4 s cycle.
- **Band (settled):** same box; glyph swaps to a small seal glyph; label flips to `GROUNDED IN 14 CHART FACTORS · 3 CLASSICAL SOURCES`; counter shows final elapsed; breathing stops. Hover: fill deepens to `rgba(201,162,76,0.09)`.
- **Expanded:** chevron rotates 180°; rows slide down 160 ms. Rows: Inter 12.5 `--ink-dim`, 28 px tall, 1.6 px gold glyph per class (chart-read, daśā, classical text, cross-check), right-aligned per-row elapsed in `--gold-tertiary`. Active row: small solid gold dot pulses opacity (the only moving row element); completed rows: dot goes hollow — geometry constant. Rows use the curated lexicon (§7.8), never tool names. Entitled drill: a settled row's hover reveals a mono affordance (`view detail ↗`) opening the audit overlay — affordance exists for all, resolves per entitlement (P4).

### 6.6 Component: answer block

Committed prose block: Body style, no borders, no background — the reading is naked ivory on jet; the chrome lives in the other regions. Selection color: `rgba(201,162,76,0.30)`. Links (rare) are ivory with `--rule-strong` underline, never gold (gold = instrument affordance, not hyperlink). Tables: Inter 13/20 cells, `--rule` row hairlines, header row eyebrow-style, no zebra fill, committed column widths. Verse blocks: 2 px `--gold-tertiary` left rule, 20 px indent, Cormorant italic, gloss on the following line in `--ink-dim`.

### 6.7 Component: citation chip + card, grade chips

- **Chip:** inline `⟦n⟧` — 20×16 px fixed box, Inter 11.5 gold on `--tint`, 3 px radius, hairline border, baseline-aligned, `vertical-align` locked so it never alters line-height (P1). Rest: dim gold. Hover/focus: border → `--rule-strong`, fill → 0.10 alpha, 120 ms. Active (card open): solid `--gold-dim` fill, `#000` numeral.
- **Card (popover ≤ 360 px / mobile sheet):** black field, `--rule-strong` border. Anatomy: eyebrow source class (`CHART FACTOR` / `CLASSICAL SOURCE` / `COMPUTED WINDOW`) · Inter 14 title ("Saturn's daśā, third pāda — active through 2027") · two lines of plain-language relevance · mono ref line (`BPHS 34.12` / entitled fact ref) · grade chip. One card at a time; Esc/scrim closes; focus returns to the chip.
- **Grade chips:** `WELL-GROUNDED` (solid gold dot ●), `SUPPORTED` (half dot ◐), `CATALOG-ONLY — UNVERIFIED` (hollow dot ○), `HONEST GAP` (em-dash glyph —). Same geometry, Inter caps 10.5, hairline boxes; **shape + label differentiate, never color** (no red/amber — P3, a11y). Catalog-only rows additionally sit under an eyebrow divider `AWAITING CROSS-VERIFICATION` in the grounding region — flattening confirmed with unverified is a §N.6 violation the layout itself prevents.

### 6.8 Component: grounding region & honest-gap ribbon

- **Grounding region:** `--rule` top hairline; line 1: Inter 13 `--ink` summary ("Grounded in 14 chart factors · 3 classical sources"); line 2: wrapped chip row with 6-word labels; line 3: grade summary + composition note (`Composed from complete house coverage` when dossier-gated — P5). Rest is compact; `View all ⌄` expands the full source list downward.
- **Honest-gap ribbon:** own block: `--tint` fill, `--rule` full border, 4 px radius, 16 px padding. Eyebrow `THE CHART IS SILENT HERE` + one Cormorant 17/28 sentence naming precisely *what* it is silent on and *why that is a finding*. No icon (any glyph reads as warning). Unmissable by structure — the only bordered, tinted block a reading can contain — calm by chrome: same golds as everything else (T-5 + P3, resolved in one component).

### 6.9 Component: prediction card — the signature component `[ELEVATION v0.2]`

**This is the hero.** Chosen deliberately over the other candidates (grounding ledger, honest-gap ribbon, the recall opening) because it is the one object no other conversational product can have — an answer that remains accountable months later — and because it carries the whole relationship loop (P9, J8) inside a single settled block. Everything else on the surface is best-in-class discipline; this is the thing that is *ours*.

Settled block: `--rule-strong` border, 4 px radius, 16 px padding. Anatomy, top to bottom:

1. **Eyebrow** — `TIME-INDEXED READING` + lifecycle state: `· WINDOW OPEN` → `· WINDOW CLOSING` → `· AWAITING OUTCOME` → `· RESOLVED — CONFIRMED / MISSED / MIXED`. The eyebrow is the **only** element that changes after settle — text swap at fixed height, the same in-place-flip discipline as the working band (P1 honored even by the one living component).
2. **Claim** — Cormorant 18/26 ("An occupational shift, self-initiated, most likely around mid-2027").
3. **The kāla-rekhā** (time hairline) — a full-width 1 px `--rule` hairline spanning from the reading's date to the window's far edge; the prediction window is a **2 px `--gold` segment** on it; a **3 px solid gold dot marks today** and advances along the line as real time passes — the one element of the entire surface that moves on the scale of months. Caps microtype beneath: `TODAY` under the dot, the window dates under the segment. No other chat surface has a component whose geometry *is* a calendar; the kāla-rekhā is the instrument's claim made physical, and it shares its stroke language with the ecliptic line and the closing rule (§6.4).
4. **Footer row** — confidence phrase chip (framed language; calibrated number one affordance behind it — P6) · mono prediction ref · (Phase 2) `Record what happened`, appearing only when the window closes.

Lifecycle restyles the eyebrow and advances the dot; nothing else ever changes. In Phase 1 the card renders and registers; Phase 2's Samīkṣā gives it its return journey (J8).

### 6.10 Component: composer

Bar: `--rule` border, 8 px radius, `#000` fill, 12 px padding; focus-within → `--rule-strong`. Field: Inter 15/22 ivory (input is data; Cormorant is for the chart's voice — a deliberate voice/register distinction: *the reader writes in sans; the instrument answers in serif*). Placeholder: `Ask the chart` in `--ink-dim`. Submit: 32 px circle, hairline, gold ↵; disabled = `--gold-tertiary`; streaming = Stop (gold square). Dictation/IME safe: no keydown hijacking during composition events.

### 6.11 Component: model picker

Popover above the pill, 280 px, black + `--rule-strong` border. Rows: 40 px — Inter 13 model name, `--ink-dim` capability note ("deep synthesis · slower"), right-side latency class dot (hollow/half/solid — relative speed, not health). Section eyebrows per provider. Active row: `--tint` fill + solid dot left. Unhealthy provider (from failure taxonomy telemetry): row dims, note reads "overloaded — try later"; never removed. Keyboard: arrows + Enter; Esc returns focus to pill.

---

## 7. Content & voice design

The words are components. These rules are enforceable in review, and several (leak lint, phase lexicon) by machine.

### 7.1 The reader register — rules

1. **No internal identifiers, ever, in reader prose.** No `SIG.MSR.413`, no fact_ids, no asset names, no layer numbers, no table names, no tool names. Machine-enforced pre-wire (M5). The *concept* appears in reader language; the identifier lives one affordance down, in mono, in the card.
2. **Sanskrit where it is the substance, glossed inline, for everyone.** Pattern: *Term (plain gloss)* — "Śaśa Yoga (Saturn strongly placed)". Gloss on first use per turn; bare term allowed after within the same turn. Never a Sanskrit term whose removal would leave the sentence's meaning intact (ornament) — only terms that *are* the finding.
3. **Declarative about the chart, never oracular about the person.** "The chart shows a period that…" not "You will…". The chart is the subject of sentences; the reader is the subject of their life.
4. **Verdict first where a verdict exists.** The stance opens the reading; evidence and texture follow. (Density principle: the verdict layer is never empty when grounding exists.)
5. **No hedging theater.** "Perhaps possibly it may be that…" is banned. Calibration is carried by the probability-phrase system (§7.4), once, precisely — not by scattering maybes.

### 7.2 Pacing rules for hard readings

- Stance in the first committed block, ≤ 3 sentences, containing the reading's emotional bottom line. No structural cliffhangers on fear topics.
- Hard content in shorter paragraphs (commit boundaries every 2–3 sentences — a composition contract the server enforces on sensitive-topic turns, §8.4) so frightening clauses spend minimal time volatile.
- Uncertainty stated *before* the frightening specific, not after ("The picture is mixed and mostly reassuring; the one factor that asks attention is…").
- Every hard reading ends with agency: what the period *asks of* the person — never a bare adverse verdict as the final block.

### 7.3 Honest-gap phrasings

The fixed skeleton: **name the silence · scope it · state what silence means · return agency.**

- "On ⟨question⟩, this chart is silent. The factors that would speak to it are unremarkable — and that is the finding, not a failure to look. ⟨14 factors were consulted; the grounding is below.⟩"
- Two-option gaps (J7): "Between these two, the chart does not choose. It speaks to the *timing* of a move — favorable through ⟨window⟩ — but is silent on the destination. That choice is yours on other grounds."
- **Banned:** "Unfortunately, no data…", "I couldn't find…", "The system was unable…" (machine failure register); "It is not for us to know…" (mystification); any apology.

### 7.4 Calibrated-probability phrasings

Fixed ladder, phrase-first, number one affordance down (with window + calibration basis):

| Band | Inline phrase |
|---|---|
| ≥ 85% | "the chart is close to unequivocal here" |
| 70–85% | "distinctly more likely than not" |
| 55–70% | "more likely than not — hold it loosely" |
| 45–55% | "the chart genuinely does not lean" |
| 30–45% | "less likely than not, though the door is not closed" |
| 15–30% | "distinctly unlikely" |
| ≤ 15% | "the chart speaks strongly against it" |

Expansion copy pattern: "Calibrated at 68% for April–June 2027 — this instrument's 60–70% calls have resolved true at ⟨rate⟩ so far." (Structural-mode honesty while L5 accrues data: "calibration history is still accruing; treat the band, not the point.") A bare percentage never leads a sentence (P6).

### 7.5 Error copy (classify-error taxonomy → display language)

| Class | Band label | Sentence | Action |
|---|---|---|---|
| `rate_limit` | `A MOMENT — THE PROVIDER ASKS US TO SLOW` | "Nothing was lost. Try again shortly, or switch models." | Retry · Switch model |
| `model_overload` | `THE MODEL IS OVERLOADED` | "⟨Provider⟩ is under load. Your question is kept; another model can take it." | Retry · Switch model |
| `timeout` | `THE READING RAN LONG AND WAS CUT SHORT` | "What arrived is above. The reading can be continued." | Continue · Retry |
| `network` | `RECONNECTING` (then, if exhausted) `THE CONNECTION WAS LOST` | "What arrived is above; nothing was altered." | Continue |
| `auth` | `THIS MODEL NEEDS ITS KEY RENEWED` (native) / `THIS MODEL IS UNAVAILABLE` (guest) | native: "Renew in settings." / guest: "Another model can take the question." | Settings · Switch model |
| `unknown` | `SOMETHING FAILED ON OUR SIDE` | "Not the chart, not your question — the plumbing. It is logged." | Retry |

Rules: never "Error:"; never blame the user; always state what was preserved; exactly one sentence + actions.

### 7.6 Disagreement responses (the calibration voice)

Skeleton: **receive plainly → restate the chart's ground → reconcile honestly → record.** "You're saying 2019 was your strongest year — taking that as given. The reading rested on ⟦2⟧⟦5⟧, which mark 2019 as a pressure period. Two readings are compatible if the pressure expressed as *load, not loss* — that fits a strong year that cost a great deal. If that's not how it felt either, this stands as an open contradiction against the chart, and it will weight future readings." Banned: "You may have misunderstood…", instant capitulation ("You're right, the chart actually shows…"), and re-arguing without new ground.

### 7.7 Empty-state & remedy copy

Empty state: "Ask the chart." + subline "Career, timing, relationships, health — the reading draws on the full depth of ⟨name⟩'s chart." Example pills generated from the chart's live features, phrased as first-person questions. Remedies: always attributive — "the tradition prescribes", "Parāśara's line for this affliction is…", never "you should"; remedy blocks carry their classical citation chip like any other claim (P7).

### 7.8 The phase lexicon (working-region labels) — COMPLETE closed vocabulary [v0.3]

**The rule:** this is a **closed** map. Every `activity.upsert` carries a `label_key`; the client renders only lexicon strings. An engine capability with no entry falls back to `CONSULTING THE CHART` **plus a CI warning** — a raw tool name, layer name, or internal id can never reach the band, structurally.

**Band-level phases** (the header label; one at a time, in order; each flips in place):

| # | Engine phase | Band label | Notes |
|---|---|---|---|
| 1 | scope resolution | `READING THE QUESTION` | sub-second; may be skipped visually if <300ms |
| 2 | session/ledger recall | `RECALLING PAST READINGS` | includes open-window check → may trigger the J8 counter-question |
| 3 | plan + floor compile | `COMPOSING THE APPROACH` | shows step count when known: "· 9 steps" |
| 4 | B.11 whole-chart read | `READING THE WHOLE CHART` | Bodha-first; always present on interpretive questions |
| 5 | retrieval (per family) | `CONSULTING THE CHART — ⟨facet⟩` | facets below |
| 6 | classical corpus | `CONSULTING THE CLASSICS` | |
| 7 | dossier / full coverage | `COMPLETING FULL COVERAGE` | Deep-dive or auto-routed; shows "· 82%" progress from the completeness receipt |
| 8 | synthesis (visible reasoning) | `COMPOSING THE READING` | reasoning-token models add a collapsed `DELIBERATING` row with token count |
| 9 | grounding gate | `VERIFYING EVERY CLAIM` | shows "· 14/14" as citations validate |
| 10 | seal/persist | `SEALING` → flips to `GROUNDED IN ⟨n⟩ SOURCES · ⟨t⟩s` | the Seal choreography (§5) |

**Row-level facets** under phase 5 (activity rows, plain language, Sanskrit only where substantive and glossed):

`— DAŚĀ STRUCTURE` (timing cycles) · `— TRANSIT WINDOWS` (gochara) · `— HOUSE & LORDSHIPS` · `— YOGAS, CROSS-CHECKED` (never "firing"/"catalog" in the band — grades belong to the ledger) · `— STRENGTHS & DIGNITIES` · `— DIVISIONAL CHARTS` (D-9, D-10 named plainly: "the marriage chart", "the career chart") · `— SENSITIVE DEGREES` · `— REMEDIAL TRADITION` (remedies retrieval).

**Edge & exception states** (each is a lexicon entry, not an improvisation):

| Situation | Band shows | Never |
|---|---|---|
| Engine asks back (clarification) | band pauses at `A QUESTION FIRST` and the question renders as a normal turn | a modal; a form |
| Open window relevant (J8) | `BEFORE I ANSWER —` + the counter-question turn | silently proceeding |
| Chart rebuilt since last turn | `THE CHART HAS BEEN REBUILT — RE-READING` one-line row, then normal flow | answering on drifted data silently |
| Network drop mid-turn | `RECONNECTING…` (band stays; content untouched) → `RESUMED — NOTHING LOST` | losing the partial; a toast that covers text |
| Provider overloaded / rate-limited | `THE MODEL IS BUSY — RETRYING` → on fail, §5.9 failure band + switch-model suggestion | raw provider error strings |
| Timeout | `TAKING LONGER THAN USUAL…` at 20s; failure band at hard limit | infinite spinner |
| Cost/coverage cap trips (partial) | `SERVED WITHIN LIMITS — ⟨n⟩ OF ⟨m⟩ STEPS` + honest-gap ribbon in answer | pretending completeness |
| User presses Stop | `STOPPED — KEPT WHAT ARRIVED` ; turn settles as interrupted | discarding streamed text |
| Mid-turn model switch requested | queued: `WILL SWITCH TO ⟨model⟩ NEXT TURN` | hot-swapping mid-answer |
| Queue wait (busy instrument) | `IN LINE — STARTS IN A MOMENT` | fake progress |

**Voice rules for the band:** verbs in present participle, tracked-caps Inter; ellipsis only while in progress; counts and durations in mono; no first person in the band (the *answer* may say "I"; the machinery never does); Sanskrit in the band only when it is the object being consulted (`DAŚĀ`, `GOCHARA` as facet names are acceptable — asset ids are not).

---

## 8. Component architecture (design → engineering bridge)

Everything here exists to make §5 physically true in React. The protocol serves the choreography.

### 8.1 Component tree (1:1 with the design)

```
<PariprashnaApp>
 ├─ <ThreadHeader chartPin modelPill title/>
 ├─ <Transcript>                        // owns scroll (§5.5); overflow-anchor:none
 │   └─ <Turn key={turnId}>             // one per turn; settled turns fully memoized
 │       ├─ <UserBlock/>                // settled at submit (optimistic, client-authoritative)
 │       ├─ <WorkingRegion>             // mounts at turn open, never unmounts
 │       │    ├─ <WorkingBand/>         // fixed 40px; label/counter/flip
 │       │    └─ <ActivityList>         // user-expanded; append-only
 │       │         └─ <ActivityRow/>    // status-glyph updates only
 │       ├─ <AnswerRegion>
 │       │    ├─ <FrozenBlock/>*        // memo(…, ()=>true) — NEVER re-renders
 │       │    │    (Paragraph|Heading|Table|Verse|GapRibbon|PredictionCard|List)
 │       │    └─ <VolatileTail>         // ≤1; rAF-buffered deltas; owns <Caret/>
 │       └─ <GroundingRegion>           // mounts once on turn.commit
 │            ├─ <GroundingSummary/> <ChipRow><CitationChip/>*</ChipRow>
 │            └─ <GradeSummary/> <SourceListDisclosure/>
 ├─ <Composer field modelPill submit|stop/>
 ├─ <FollowPill/>                       // "↓ Reading continues"
 └─ <OverlayLayer> <CitationCard/> <ModelPicker/> <AuditDrawer/> </OverlayLayer>
```

### 8.2 Freeze/memo discipline (P1 in code)

- `<FrozenBlock>` is `React.memo` with an always-equal comparator; its props are set exactly once at commit. Content mutation post-commit is impossible by construction. The dev harness wraps the transcript in a React Profiler and **fails on any FrozenBlock re-render** — P1 as a CI assertion.
- `<VolatileTail>` is the only component receiving high-frequency updates; deltas go to a ref-held buffer, flushed to state once per rAF. On `block.commit`, the tail's final content is handed to a new FrozenBlock and the tail resets (or unmounts).
- Settled `<Turn>`s memo on `turnId` alone. A 200-turn thread streams its 201st with re-render cost O(tail), not O(transcript). Virtualize the transcript only above a length threshold and only for fully-settled turns (virtualization is a classic P1 violator if it touches live content).
- `<WorkingBand>` label/counter updates are text-node swaps inside a `height: 40px; overflow: hidden` box — geometry clamped in CSS, not by discipline alone.

### 8.3 Stream protocol → reducer (events as the design's data)

Wire events (server → client, SSE with event ids): `turn.open` · `phase` · `activity.upsert` · `block.open` · `block.delta` · `block.commit` · `citation.define` · `flag` · `grade` · `turn.commit` · `turn.close` · `error`.

Client state (single reducer, one store per thread):

```ts
interface TurnState {
  id: string; status: 'submitted'|'thinking'|'streaming'|'reconnecting'
                    |'settling'|'settled'|'interrupted'|'errored';
  phaseLabel: string;            // ← phase (via lexicon, server-resolved)
  elapsed: number;               // client clock from turn.open
  activities: ActivityRow[];     // ← activity.upsert (append or status-patch by id)
  blocks: CommittedBlock[];      // ← block.commit (append-only, frozen)
  tail: { blockId, type, text } | null;   // ← block.open / block.delta
  citations: Record<n, Citation>;         // ← citation.define (chip metadata + card payload)
  grades: Grade[]; flags: Flag[];         // ← grade / flag (honest_gap, catalog_only_present,
                                          //    contradiction_recorded, timing_anchored…)
  grounding: GroundingSummary | null;     // ← turn.commit payload
  error: ClassifiedError | null;
  lastEventId: string;                    // resume cursor
}
```

Reducer laws (each is a designed behavior): `block.delta` may touch only `tail` (never `blocks`) — P1. `block.commit` moves tail→blocks append-only. `citation.define` may arrive *before* its chip's prose (define-then-reference), so chips render fully-formed on first paint — M6. `turn.commit` populates `grounding` and triggers the settling choreography as one ordered effect (§5.3). Duplicate event ids are dropped idempotently — reconnect safety. `flag` events drive presentation flags (a gap ribbon is *also* a `flag: honest_gap` so the grade summary and any Phase-2 surface can see it without parsing prose).

### 8.4 Server-side composition responsibilities (design enforced pre-wire)

1. **Citation sentinel rewrite:** model emits sentinels; server resolves to `⟦n⟧` + `citation.define` before the wire. The client never sees a sentinel.
2. **Prose leak lint:** internal-ID regexes + asset/tool vocabulary run on every prose delta buffer; a hit blocks the flush, rewrites or strips, and logs a violation (M5's enforcement point).
3. **Block discipline:** the server owns commit boundaries — paragraphs at paragraph ends; tables/headings/verse buffered and emitted commit-only (§5.6); on sensitive-topic turns (engine intent classification), shorter commit intervals (§7.2). `[ELEVATION v0.2]` The server also tags each prose block's reading role (`verdict | elaboration | caveat`, §6.3.1) at `block.open` — the typographic anatomy is protocol, never client inference.
4. **Phase lexicon resolution:** server maps engine phases → display labels (§7.8); the client renders labels verbatim, trusting the wire.
5. **Turn buffering for resume:** every turn's event log is server-retained until `turn.close` + grace; reconnects replay from `Last-Event-ID`.
6. **Depth routing policy:** interpretive-intent turns route to the completeness-gated dossier path by default; the `turn.commit` grounding payload carries the composition note ("full coverage") that §6.8 renders — G4's mechanism.

### 8.5 State ownership

| State | Owner |
|---|---|
| Turn/stream state | Thread store (reducer above) — the single source for everything §5 renders |
| Scroll/follow mode | `<Transcript>` local (never in the store — no render coupling to scroll) |
| Composer draft | `<Composer>` local, persisted to sessionStorage per thread |
| Overlays (card, picker) | `<OverlayLayer>` — one open overlay max, by design |
| Model selection | Thread-level, server-persisted; switch emits the system micro-block |
| Entitlement | Session context; gates card *contents* and audit drawer *resolution*, never affordance existence (P4) |
| Elapsed counters | Client clock from `turn.open` receipt (no per-second wire chatter) |

---

## 9. Responsive & accessibility spec

First-class scope: the prior builds failed partly by treating this section as an appendix. These are Phase 1 acceptance surfaces (M8, M9).

### 9.1 Breakpoints & layout transforms

- **≥ 1200 px:** three-zone shell (rails collapsed by default in Phase 1; conversation centered 720 px).
- **768–1199 px:** conversation only; rails become overlays (Phase 2).
- **< 768 px (mobile):** full-bleed column, 20 px gutters; prose 18/29.7; turn separator spacing 40 px; thread header condenses to chart pin + overflow (model pill moves here); working band 44 px (touch target floor).

### 9.2 Touch & mobile interaction

- **Citations are tap-first everywhere:** chip tap → **bottom sheet** (not popover): slides up 240 ms, drag-handle, scrim, swipe-down/scrim-tap closes. Chip touch target ≥ 40×40 via padded hit area (visual box unchanged — P1). **No hover-only affordance exists anywhere** on any input type; hover is only ever an *earlier* hint of an affordance that also works by tap/focus.
- **Bottom sheets, never push-downs:** every disclosure that would displace settled content on mobile (citation card, probability detail, model picker, audit) is a sheet. The *working region expansion* remains in-flow (it only displaces unsettled/below content by contract) but caps at 40 vh with internal scroll.
- **Virtual keyboard:** composer pins above the keyboard via `visualViewport` tracking (not `100vh` guesses); the transcript resizes rather than being covered; if follow mode was on, keyboard appearance keeps the tail visible above the composer. Keyboard dismissal on scroll-up (reading gesture); no focus theft — streaming never yanks focus to or from the composer.
- Overscroll containment on transcript and sheets (`overscroll-behavior: contain`) — no pull-to-refresh accidents mid-reading.
- Stop button ≥ 44 px on touch. FollowPill sits above the composer, thumb-reachable.

### 9.3 Accessibility checklist (normative)

**Live regions & streaming**
- [ ] One `aria-live="polite"` region per surface = the volatile tail's text. **Committed blocks leave the live region at commit** (moved to inert settled DOM) — a screen reader hears prose once, never re-announced on later renders. This is P1's aural twin.
- [ ] Working-band label changes announce via a separate throttled polite region (≥ 5 s between announcements); elapsed-counter ticks are `aria-hidden`.
- [ ] Settle announces one summary: "Reading complete. Grounded in 14 chart factors, 3 classical sources."
- [ ] Honest-gap ribbon: `role="note"`, announced within reading order — not `role="alert"` (P3 aurally: no alarm tone semantics).
- [ ] Error states: `role="status"`, polite; the single sentence + actions are the announcement.

**Structure & navigation**
- [ ] Landmarks: `main` (transcript), `form` (composer), `complementary` (rails, Phase 2). Each turn an `article` labelled "Your question / The reading, ⟨time⟩".
- [ ] Headings inside readings preserve document outline (turn = h2, reading heads = h3).
- [ ] Citation chips are `button`s: `aria-label="Source 3: Bṛhat Parāśara Horā Śāstra 34.12"`; card open sets `aria-expanded`, focus moves into card, Esc returns to chip.
- [ ] Full keyboard path: composer → send/stop → per-turn band toggle → chips → grounding disclosure → picker; roving tabindex within chip rows; visible focus ring (`--rule-strong` 2 px offset) on `#000` — verified ≥ 3:1 against field.
- [ ] Working-band expansion is a disclosure (`aria-expanded` on the band button); activity rows are a list.

**Perception**
- [ ] Contrast: `--ink` on `#000` ≈ 15:1 ✓; `--gold` on `#000` ≈ 8.9:1 ✓; `--gold-dim` ≈ 6:1 ✓ (AA at all sizes); `--gold-tertiary` is decorative-only (hairlines), never text under 18 px.
- [ ] Grade semantics never color-only (shape + label — already §6.7).
- [ ] `prefers-reduced-motion` honored per §5.7; `prefers-contrast: more` bumps hairlines to 0.5 alpha and `--ink-dim` to 0.8.
- [ ] Zoom to 200% text-only: no loss, no horizontal scroll; Cormorant floor rule re-verified at zoom.
- [ ] Sanskrit terms carry `lang="sa-Latn"` for correct pronunciation.

**Harness**
- [ ] axe-core runs in CI against a fixture per §5.3 state (including reconnecting, interrupted, errored, honest-gap, sheet-open) — M9.
- [ ] Screen-reader smoke script (VoiceOver + NVDA): J1 and J6 end-to-end, documented pass required per release.

---

## 10. Phase 2 surface (architecture depth)

Each subsection: purpose, IA position, key design commitments, and what Phase 1 must not foreclose. Full interaction design deferred to the Phase 2 spec.

### 10.1 History sidebar

Left rail, collapsible, threads grouped by chart then recency; thread rows: Inter 13 title (auto-generated from first question, editable), chart glyph, relative time. Search across thread titles + full prose (server index). Design commitments: selection never reloads the shell (route swap inside `<Transcript>`); a streaming thread shows a quiet gold dot in its row; deleting is archival (threads are audit trail — hard delete is native-only with confirmation in the instrument's register). *Phase 1 must not foreclose:* thread ids in URLs (done, §3.3), turn anchors for deep links (done).

### 10.2 Samīkṣā (prediction review)

The calibration loop's face. Sidebar tab with count badge (`--gold-dim` numeral pill — never red). Panel: a queue of prediction cards (same component as §6.9) in lifecycle order: window closing soon → awaiting outcome → recently graded. Recording an outcome is conversational-first: the card's "Record what happened" opens a *thread turn* pre-framed by the instrument ("In March I indicated X for April–June — what happened?"), because the highest-leverage moment is the engine *asking* — the design routes outcome entry through the conversation, with the panel as index, not form. Window-close prompts may also appear as a quiet one-line band above the composer in any thread of that chart ("A reading's window closes this week — review when ready"): dismissible, never modal, never nagging (P3). Grades flow to L5; graded cards show resolution in the same framed-probability language. *Phase 1 must not foreclose:* prediction cards carry stable refs (done); `flag`/`grade` events in the protocol (done).

### 10.3 ~~Reference rail~~ — REMOVED (native ruling 2026-07-27) `[ELEVATION v0.2 — residue purged]`

Retained as a numbered stub so cross-references stay stable. The rail is not deferred — it is **removed**: no kuṇḍalī diagram, no ambient positions panel, no daśā strip. The reading speaks the chart in prose; any factor detail a claim needs lives in its citation card. What survives from this section's old idea, in one direction only: citation payloads carry factor refs (§8.3), and a citation card may offer *"ask about this"* as a composer pre-fill — conversation remains the only surface.

### 10.4 Settings & model management

Native-only overlay: provider keys + health, default model per-surface, cost visibility (per-thread token/cost line in mono — instrument honesty applied to itself), guest entitlement management (which charts a guest sees), data controls (export thread as typeset PDF — the ceremonial register earns print). Guests see only: their profile, appearance (reduced motion, text size), and nothing that implies hidden tiers (P4). *Phase 1 must not foreclose:* model switching lives in the composer independent of this panel (done).

### 10.5 Dashboard entry

The existing MARSYS dashboard gains: per-chart "Open Paripraśna" primary action; a "recent readings" strip (last 3 threads, one-line each); a Samīkṣā badge surfaced at dashboard level when outcomes are due. Design commitment: the dashboard *points into* conversation; no reading content is duplicated onto dashboard cards (one home for prose).

### 10.6 The sealed reading — print & export `[ELEVATION v0.2]`

A reading worth trusting is worth possessing. Phase 2 adds **export of a settled turn (or thread) as a typeset document** — the ceremonial register earning paper. Design commitments:

- **The one sanctioned inversion:** ivory paper (`#EBE3D2` field, jet ink), resolving OD-2 as (b). The screen instrument stays jet; print is the only light Marsys surface that will ever exist.
- Marsys letterhead: the wordmark set solid `--gold-dim` (foil gradients do not print; they are not faked).
- Cormorant body at book sizes; citation chips become true numbered endnotes; the grounding ledger sets as an appendix table; honest-gap ribbons print as rule-bound indented paragraphs.
- The prediction card prints with its kāla-rekhā **frozen at export date**, captioned "as of ⟨date⟩" — the document honestly declares its own moment.
- A mono provenance footer (chart build, model, date) — the audit trail travels with the artifact.

Why it earns its place: a hard reading a family member wants to sit with should not require a login; and a sealed document is the trust arc (§4.0) extended beyond the screen. *Phase 1 must not foreclose:* turn payloads are already self-contained (blocks + grounding + citations + flags in the store, §8.3) — export is a renderer, not a schema change.

---

## 11. Acceptance criteria & design QA

A build that fails any gate here does not ship, whatever its feature count. Gates are ordered cheap-to-expensive.

### 11.1 Mechanical gates (CI, every build)
- **AC-1 · Settled CLS = 0.** Layout-shift observer scoped above the tail across the full streaming fixture corpus (long tables, nested lists, Sanskrit + glosses, rapid-fire short deltas, 5 kB single delta post-reconnect). Any settled-source shift = red. (M1)
- **AC-2 · Caret never orphans.** DOM invariant asserted per animation frame in harness: caret is last inline child of the tail's deepest text-bearing node; caret absent ⇔ no volatile block. Includes the table-adjacency fixture that reproduces the historical bug. (M2)
- **AC-3 · No transmutation.** Snapshot diffing across stream steps: a committed block's serialized DOM is byte-identical at every subsequent step; chips render at final geometry on first appearance. (M6)
- **AC-4 · Zero internal-ID leakage.** Wire-tap regex suite (SIG.*, fact ids, `ga_`/`bo_`/`ka_`/`ph_`/`mi_` asset ids, table names, tool names, "L2"-style layer refs) on the full response corpus = 0 hits. (M5)
- **AC-5 · FrozenBlock re-render count = 0** via profiler harness. (§8.2)
- **AC-6 · axe-core 0 critical/serious** on every §5.3 state fixture. (M9)

### 11.2 Performance gates
- **AC-7 · TTFS < 300 ms** (submit → working region live, optimistic). **TTFT p50 < 4 s / p90 < 12 s** on interpretive fixtures; dossier-routed turns exempt from TTFT but must show a phase-label update ≤ 8 s intervals (waiting always has narrative). (M3/M4)
- **AC-8 · Streaming at 60 fps** on reference hardware incl. a mid-range Android profile; long-thread (200 turns) input latency < 100 ms.

### 11.3 Journey gates (scripted walkthroughs, human-verified per release)
- **AC-9 ·** J1–J7 executed end-to-end against the live engine; each journey's "must never happen" list is the checklist; any occurrence = fail.
- **AC-10 · Reconnect:** scripted 10 s and 45 s drops mid-stream → non-event and interrupted-state respectively, per J6; partial prose byte-identical across the drop.
- **AC-11 · Model switch:** mid-thread switch across all five providers; layout indistinguishable across providers except pill + micro-block; provider failure lands in the uniform taxonomy.
- **AC-16 `[ELEVATION v0.2]` · Signature integrity:** on every time-indexed fixture the prediction card renders per §6.9 — kāla-rekhā geometry correct against the window dates, today-dot position derived from the real date, and a lifecycle eyebrow swap leaving the rest of the card's serialized DOM byte-identical; the arrival line renders once per session from L1/Kāla data (never model prose) and never scrolls with the transcript; the Seal fires in §5.3 order with the closing-rule draw as the only motion above 240 ms.

### 11.4 Depth & epistemics gates
- **AC-12 · Depth routing:** the interpretive-question fixture set (the audit's 15–33% failures included) routes to the completeness-gated path; grounding regions show composition notes; a shallow route on an interpretive fixture = fail.
- **AC-13 · Density:** no fixture response flattens confirmed and catalog-only findings into one undifferentiated list; verdict layer non-empty whenever grounding exists; honest empties carried as flags. (§N.6 conformance at the UI)

### 11.5 The calm rubric (subjective gate with structure)
Honest-gap, hard-reading, and error fixtures rated by the native + one outside reader who has *not* seen this document, 1–5 on four axes: *"I understood exactly what is and isn't known" · "Nothing felt withheld" · "Nothing felt alarming beyond the content itself" · "I knew what, if anything, to do next."* Ship bar: **≥ 4 on every axis, both raters, all fixtures.** (M7)

### 11.6 Mobile gate
- **AC-14 ·** All §9 scenarios on physical iOS + Android: keyboard/composer, tap-citation sheet, reconnect on cellular, streaming with keyboard open, 200% text zoom. (M8)

### 11.7 Design-QA review (pre-ship, per release)
A structured pass against §2: each principle gets a hunt ("find any violation of P1 anywhere") by someone other than the implementer. Violations are ship-blockers unless the native waives in writing (waiver recorded in this document's changelog).

### 11.8 The ultimate gate
- **AC-15 ·** The native uses Paripraśna daily for one week for real questions. At week's end, two questions: *"Does it feel like Claude Code?"* and *"List every physical annoyance you noticed."* Ship = **yes** + an empty (or waived-trivial) list. This gate has no automation and no substitute; it is the gate the prior builds never faced.

---

## 12. Open design decisions (for the native)

| # | Fork | Options | Recommendation | What's prepared either way |
|---|---|---|---|---|
| **OD-1** | Body face: Cormorant vs. sturdier serif | (a) Cormorant Medium 19/31 per §6.2 · (b) Cormorant display-only + Source Serif 4 body · (c) Cormorant with size bump to 20 px | **(a), tested in the flesh during AC-15 week** — the ceremonial register is worth defending, and Medium-at-19 is engineered to hold; but this is an eyes-on-device call only you can make | Two-token swap (`--font-body`, ramp row); fixtures rendered in both for side-by-side |
| **OD-2** | Light mode, ever? | (a) Never — the instrument is jet, full stop · (b) A print/export light treatment only (PDF) · (c) Full light theme | **RESOLVED v0.2: (b), designed as §10.6 (the sealed reading)** — the screen instrument stays jet (the brand *is* the darkness); print earns the one ivory inversion | Tokens are CSS variables throughout; print stylesheet stubbed |
| **OD-3** | Default density of the settled turn | (a) Grounding region compact (summary + 1 chip row) as specced · (b) Grounding fully expanded by default · (c) Working region also auto-expands on settle | **(a)** — epistemics visible, machinery collapsed (P2); (b) risks making every reading feel like an appendix | The disclosure states exist regardless; a per-user default is one setting |
| ~~**OD-4**~~ | ~~Reference-rail depth (Phase 2)~~ | — | **RETIRED v0.2** — the rail was removed by native ruling 2026-07-27 (§3.2, §10.3); no depth question remains | Citation payloads still carry factor refs (they serve the citation card) |
| **OD-5** | Guest visibility of the working region's expanded activity | (a) Same affordance, rows visible, drill-to-audit gated by entitlement (P4-pure) · (b) Rows visible but abstracted labels only for guests | **(a)** — the lexicon labels are already reader-safe by construction; tiering row *visibility* would be the first crack in D-15 | Lexicon is the only string source either way |
| **OD-6** | Stop-button semantics | (a) Stop settles the turn as `interrupted` with partial prose kept (as specced) · (b) Stop offers keep/discard | **(a)** — settled content is sacred includes content the user chose to stop; a discard prompt is a decision imposed at a moment of impatience | Reducer treats stop as server-side `turn.close(interrupted)` either way |
| **OD-7** | Example-prompt generation in the empty state | (a) Chart-aware, engine-generated per chart · (b) Curated static set per chart, native-editable | **(a)** with (b) as fallback if generation quality embarrasses — first impressions are the register's first proof | Empty state consumes a prompt list from either source |

---

## Appendix A — Traceability: the named pains → the design that removes them

| Pain (as suffered) | Removed by |
|---|---|
| Cursor landing under tables | §5.4 (caret is DOM-child of trailing text; tables commit-only; caret's home is the following block) + AC-2 |
| Text jumping mid-read | §5.1 region contracts + §8.2 freeze discipline + `overflow-anchor` off (§5.5) + AC-1/AC-5 |
| Thinking phase presented incontinently | §5.3 `thinking` + §6.5 stable band + §7.8 closed lexicon + P2 |
| Internal IDs in prose | §7.1 rule 1 + §8.4 server lint + AC-4 |
| Plain text → badge transmutation | §5.6 commit-only types + define-then-reference citations (§8.3) + AC-3 |
| Machinery indistinguishable from answer | The three-region geometry itself (§3.4, §5.1) |
| Depth invisible / shallow routing unnoticed | P5 + grounding counts & composition notes (§6.8) + AC-12 |
| Gaps reading as withheld bad news | P3 + §6.8 ribbon + §7.3 phrasings + §11.5 rubric |
| Reconnect/mobile/a11y as afterthoughts | §5.9, §9 as Phase 1 scope + AC-10/AC-14/AC-6 |

---

*End of PARIPRASHNA_DESIGN_ENGINEERING_PLAN v0.2 (DRAFT — elevated). Next step: native reaction pass — especially the `[ELEVATION v0.2]` marks, §12's open decisions, and the §4 journeys (J8 in particular) — before any implementation planning. On approval, this plan governs Phase 1 build scope; `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` is revised to sit beneath it as the implementation layer.*
