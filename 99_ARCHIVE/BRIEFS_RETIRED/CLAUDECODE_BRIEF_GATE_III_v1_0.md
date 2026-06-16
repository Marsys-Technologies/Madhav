---
brief_id: GATE-III-INTELLIGENT-CHAT-S1
version: 1.0
status: COMPLETE
closed_on: 2026-05-12
closed_by: Claude Code Sonnet 4.6 (overnight executor)
authored_by: Claude Opus 4.7 (Gate III Design Session) — 2026-05-12
purpose: >
  Transform the consume chat into a domain-aware, pipeline-intelligent Jyotish
  interface. Adds: live reasoning surface (astrological vocabulary only), inline
  reasoning-in-prose with citations, factual correction doctrine, Sanskrit hover
  tooltips, post-answer provenance pills with expandable drawer, context-usage
  cue, smart prior-turn selection, conversation history drawer, conversation
  auto-titling, and an empty state with class-based and dasha-based suggestion
  tabs. Single overnight session.
executor: Claude Code Sonnet 4.6 (Anti-Gravity, VS Code, --dangerously-skip-permissions)
working_directory: /Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat
branch: feature/gate3-intelligent-chat
model_preference: gemini-2.5-pro (critical synthesis/planner); gemini-2.0-flash-lite (titling, suggestions)
banned_models: anthropic/* — flag immediately if seen in touched files
estimated_duration: 6–10 hours (overnight)
parallel_gates: Gate I (perf-center) and Gate II (trace-align) run simultaneously in their own worktrees; do not touch their files
migration_range: 046 (likely 0 migrations used)
---

# CLAUDECODE_BRIEF — Gate III: Intelligent Chat Interface

## §0 — Read This First

This session transforms `components/consume/*` and `app/api/chat/consume/route.ts` from a generic chat into a Jyotish-aware, reasoning-first, pipeline-transparent interface — without modifying a single byte of `components/trace/**` or `lib/admin/trace_assembler.ts` (those are Gate II's territory). The native, Abhisek, locked the full design over a planning conversation; every decision in §3 is fixed and not open for re-litigation by the executor. The session runs end-to-end overnight; manual prerequisites are batched in §1 (start) and manual review handoff is in §8 (end).

**The single most important rule:** all user-facing surfaces speak classical Jyotish vocabulary. Internal asset IDs (MSR, FORENSIC, CGM, UCN, CDLM, RM, LEL) and pipeline mechanics (pgvector, cgm_graph_walk, retrieval ranker) must be **translated** through `lib/jyotish/domain_labels.ts` before they touch any pixel the native sees. Leaking internal jargon to the UI is a regression.

---

## §1 — Entry Gates (manual prerequisites — verify before W0)

These must all be true before the executor starts. If any fail, halt and report.

- [ ] Worktree present at `/Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat`
- [ ] Branch is `feature/gate3-intelligent-chat`
- [ ] `npm install` completed in `platform/` (verify `node_modules/` exists)
- [ ] `.env.local` (or platform env) has `GEMINI_API_KEY`, GCS credentials, Firebase keys
- [ ] Cloud SQL Auth Proxy running on `127.0.0.1:5432` (for any DB queries during dev — required if `/api/consume/conversations` or title persistence reads DB)
- [ ] Baseline `npm test` captured (run once, save pass/fail counts to `.gate3_baseline.txt`)
- [ ] `npx tsc --noEmit` baseline captured (save to `.gate3_tsc_baseline.txt`)

All gates pass → proceed to W0. Any gate fails → write `GATE_III_HALT.md` at worktree root explaining what failed, then exit.

---

## §2 — Scope

### may_touch

- `platform/src/app/clients/[id]/consume/**` (page + conversationId page)
- `platform/src/app/api/chat/consume/route.ts`
- `platform/src/app/api/consume/**` (new endpoints OK in this subtree)
- `platform/src/components/consume/**` (EXCEPT TraceDrawer.tsx — see must_not_touch)
- `platform/src/lib/jyotish/**` (NEW subtree)
- `platform/src/lib/consume/**` (new utilities here)
- `platform/src/lib/planner/**` (smart context selection update)
- `platform/src/lib/prompts/synthesis_*.md` or `.ts` (synthesis prompt updates)
- `platform/src/lib/prompts/planner_prompt_*.md` or `.ts` (planner prompt updates — only the prior-turn-relevance addition)
- `platform/src/lib/synthesis/**` (synthesis orchestrator updates if needed for SSE event emission)
- `platform/src/types/sse_events.ts` (NEW file)
- `platform/src/types/consume.ts` (extend existing if present)
- `platform/supabase/migrations/046_*.sql` (ONLY if needed; budget is 0–1 migrations)
- `platform/tests/consume/**`
- `platform/tests/jyotish/**` (NEW)
- `platform/tests/planner/**` (extend existing)
- `platform/tests/synthesis/**` (extend existing)
- `platform/tests/api/consume/**`

### must_not_touch

- `platform/src/components/trace/**` (Gate II territory — TracePanel, TraceDrawer wrapper if it lives there, LifecycleGraph, all step-detail variants, HealthRail, QueryDNAPanel, RetrievalScorecard, etc.)
- `platform/src/components/consume/TraceDrawer.tsx` — if this is just a thin shell that imports from `components/trace/`, leave the shell alone too. Read it to know its public API but do not modify it. Gate II owns the trace surface end-to-end.
- `platform/src/lib/admin/trace_assembler.ts`
- `platform/src/lib/admin/trace_client.ts`
- `platform/src/app/api/admin/trace/**`
- `platform/src/app/api/trace/stream/**`
- `platform/src/components/performance/**` (Gate I territory)
- `platform/src/app/performance/**` (Gate I territory)
- `platform/src/components/shared/AppShellRail.tsx`
- `platform/src/components/shared/MobileNavSheet.tsx`
- Any nav-item additions — Gate IV adds these
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**`
- Migrations 001–045 and 047+
- `package.json` / `package-lock.json` — **do not add new npm packages**. If a new package would meaningfully improve a work item, flag it in `GATE_III_PACKAGE_REQUESTS.md` at worktree root and proceed without it (use existing libraries).
- Anything matching `anthropic/*` in model strings — flag immediately

### red-line rule

If at any point a work item appears to require touching a `must_not_touch` path, **halt and write `GATE_III_SCOPE_CONFLICT.md`** at worktree root describing the conflict. Do not proceed past the conflict.

---

## §3 — Work Items

Work items are listed in execution order. Each has clear dependencies. Do not parallelize within this session unless explicitly noted.

### W0 — Audit & Anchor

Goal: read enough of the current code to write the rest of the brief's items without guessing.

1. Read these files top-to-bottom (no edits):
   - `platform/src/components/consume/ConsumeChat.tsx`
   - `platform/src/components/consume/AnswerView.tsx`
   - `platform/src/components/consume/StreamingAnswer.tsx`
   - `platform/src/components/consume/TraceDrawer.tsx` (read-only — note its public API + props)
   - `platform/src/app/clients/[id]/consume/page.tsx`
   - `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx`
   - `platform/src/app/api/chat/consume/route.ts`
   - The current synthesis prompt (search `platform/src/lib/prompts/synthesis_*`)
   - The current planner prompt (`platform/src/lib/prompts/planner_prompt_v2_1*` — or whichever current version)
   - `platform/src/lib/synthesis/*` (orchestrator, strategies, validator)
   - `platform/src/lib/planner/*`
   - Any existing `/api/consume/conversations` route (verify if it exists; if not, plan it under W10)
2. Glob `platform/src/components/trace/` and `platform/src/lib/admin/` — list contents to confirm they exist (don't read). Add to a mental "do not touch" set.
3. Write `GATE_III_AUDIT.md` at worktree root with:
   - Confirmed file paths for every must-modify file
   - Current SSE event types emitted by `route.ts` (verbatim names and shapes)
   - Current synthesis prompt version + file path
   - Current planner prompt version + file path
   - Whether `/api/consume/conversations` exists and its shape
   - Whether conversation title persistence schema exists (check DB schema via tsc types or migrations 040–045)
   - List of `components/consume/*` files and their LOC
   - Any deviations from this brief's assumed paths

Output: `GATE_III_AUDIT.md` (audit + corrections to any path assumptions in this brief).

Dependencies: none. Time budget: 30–45 min.

---

### W1 — Domain Labels Translation Map (FOUNDATION)

Goal: single source of truth that translates every internal ID, asset name, query class, pipeline step, and synthesis stage into a user-facing astrological label.

Files:
- `platform/src/lib/jyotish/domain_labels.ts` (NEW)
- `platform/tests/jyotish/domain_labels.test.ts` (NEW)

Contents of `domain_labels.ts`:

```ts
// User-facing labels for internal canonical assets.
// NEVER leak internal IDs to the UI. Route every asset display through this map.
export const ASSET_LABELS: Record<string, string> = {
  FORENSIC: 'Birth Chart',
  MSR:      'Astrological Signals',
  UCN:      'Cross-Domain Patterns',
  CDLM:     'Domain Linkages',
  RM:       'Remedies Matrix',
  CGM:      'Concept Graph',
  LEL:      'Life Events',
  // Add any other canonical assets discovered in W0 audit
};

// Query classes are domain-neutral and clear; keep titles human.
export const QUERY_CLASS_LABELS: Record<string, string> = {
  factual:      'Factual',
  interpretive: 'Interpretive',
  predictive:   'Predictive',
  discovery:    'Discovery',
  holistic:     'Holistic',
  cross_native: 'Cross-Native',
  // include all 7 classes — match planner output exactly
};

// Pipeline steps → astrological-domain narration phrases.
// Used by LiveReasoningCard during the pre-synthesis phase.
export const PIPELINE_STEP_NARRATION: Record<string, string> = {
  classify:           'Reading the question',
  plan:               'Planning the approach',
  vector_search:      'Searching classical sources',
  cgm_graph_walk:     'Following conceptual links across principles',
  structured_sql:     'Looking up chart data',
  hybrid_rank:        'Weighing the most relevant sources',
  context_assembly:   'Assembling the context for synthesis',
  synthesis_start:    'Reasoning through the question',
  validator:          'Checking the answer for consistency',
  audit:              'Recording the trace',
  // ...one entry per pipeline step name discovered in W0
};

// Technical-tag formatting for the provenance drawer "Technical" tab.
// These are visible to the user only inside the expanded technical tab.
// Format compactly: "≈0.87 cosine", "depth 2", "12.3s", etc.
export type TechnicalTagKind =
  | 'vector_score' | 'graph_depth' | 'latency' | 'token_count' | 'model_name' | 'cache_hit';

export function formatTechnicalTag(kind: TechnicalTagKind, value: number | string): string { ... }

// Lookup helper with fallback (returns the input if no translation exists,
// so we never blank-out a label — but we also log a warning so the map can be extended).
export function labelFor(category: 'asset' | 'class' | 'step', key: string): string { ... }
```

Tests cover: every key in every map has a non-empty, non-internal-jargon value; `labelFor` fallback logs a warning; `formatTechnicalTag` produces compact strings.

Dependencies: W0 (need confirmed asset/class/step names).

---

### W2 — SSE Event Schema

Goal: well-typed schema for the multiplexed SSE stream from `/api/chat/consume`.

Files:
- `platform/src/types/sse_events.ts` (NEW)
- `platform/tests/types/sse_events.test.ts` (NEW — at minimum a type-level test via `tsd` if available, else a runtime shape test)

Event types to define:

```ts
export type SSEEventType =
  | 'reasoning_step'      // ambient reasoning narration for LiveReasoningCard
  | 'answer_chunk'        // streamed prose for StreamingAnswer
  | 'context_usage'       // emitted once near the start; tells the UI what prior context was used
  | 'correction'          // emitted once if user query contains factual error; prepended to answer
  | 'out_of_domain'       // emitted once if query is outside Jyotish scope
  | 'sanskrit_terms'      // emitted at end; map of detected terms → definitions (used by hover tooltip)
  | 'provenance'          // emitted at end; structured provenance payload for PostAnswerProvenance
  | 'conversation_title'  // emitted only on first turn of a new conversation
  | 'done'                // stream complete
  | 'error';

export interface ReasoningStepEvent { type: 'reasoning_step'; phase: 'pipeline' | 'synthesis'; text: string; timestamp: number; }
export interface AnswerChunkEvent   { type: 'answer_chunk'; delta: string; }
export interface ContextUsageEvent  { type: 'context_usage'; prior_turns_used: number; reason: string; mode: 'independent' | 'narrative_context' | 'continuation'; }
export interface CorrectionEvent    { type: 'correction'; original_claim: string; corrected_claim: string; classical_source?: string; }
export interface OutOfDomainEvent   { type: 'out_of_domain'; reason: string; }
export interface SanskritTermsEvent { type: 'sanskrit_terms'; terms: Array<{ term: string; definition: string; transliteration?: string }>; }
export interface ProvenanceEvent {
  type: 'provenance';
  models: Array<{ stage: string; role: string; model_id: string; latency_ms?: number; tokens?: number }>;
  sources: {
    astrological: Array<{ asset: string; label: string; items: Array<{ id: string; label: string; }> }>;
    technical:    Array<{ kind: string; label: string; value: string }>;
  };
}
export interface ConversationTitleEvent { type: 'conversation_title'; title: string; }
```

All events serialized to SSE format: `event: <type>\ndata: <JSON>\n\n`.

Tests cover: every event type has the right shape; serialization round-trips.

Dependencies: W0, W1.

---

### W3 — Smart Context Selection in Planner

Goal: planner decides per-query whether prior turns are relevant; emits `prior_turn_relevance`; synthesis prompt enforces "context for understanding, not substance."

Files:
- `platform/src/lib/prompts/planner_prompt_v2_2.md` (NEW — successor to v2.1)
- `platform/src/lib/planner/planner.ts` (UPDATE — read v2.2; extend QueryPlan type)
- `platform/src/types/query_plan.ts` (UPDATE — add `prior_turn_relevance` field)
- `platform/tests/planner/prior_turn_relevance.test.ts` (NEW)
- `platform/tests/planner/golden_set.test.ts` (REGRESSION — keep passing; recall ≥ 0.97, precision ≥ 0.95)

Changes to `planner_prompt_v2_2.md`:
- Carry over every rule from v2.1 verbatim
- Add a new section "**PRIOR-TURN RELEVANCE SELECTION**" that instructs the LLM to emit `prior_turn_relevance: { used: number, reason: string, mode: 'independent' | 'narrative_context' | 'continuation' }`
  - `independent` → query is fully self-contained; `used: 0`, `mode: 'independent'`
  - `narrative_context` → query references prior context for comprehension (e.g., "tell me more about that"); `used: 1–2`, but reasoning must derive from facts/corpus, not from prior turns
  - `continuation` → query is a direct follow-up that requires the prior turn's framing; `used: 1`, narrowly
- Bias the model toward `independent` when in doubt; the only reason to use prior turns is comprehension-of-query, never substance-of-answer
- Update changelog frontmatter at top of v2.2

Updates to `query_plan.ts`:
```ts
export interface QueryPlan {
  // ...existing 7 fields...
  prior_turn_relevance: {
    used: number;                  // 0, 1, or 2 (max)
    reason: string;                // human-readable explanation for the cue
    mode: 'independent' | 'narrative_context' | 'continuation';
  };
}
```

Updates to `planner.ts`:
- Bump version constant from v2.1 to v2.2
- Read v2.2 prompt
- Validate that planner output includes `prior_turn_relevance` (zod or equivalent)
- Synthesis orchestrator (W4) reads this field and (a) trims prior turns to `used`, (b) inserts the "context for comprehension only" directive into the synthesis prompt

Tests:
- Golden-set regression PASSES at recall ≥ 0.97 precision ≥ 0.95 (current baseline)
- New `prior_turn_relevance` test: 10 hand-crafted queries that should map to each of the three modes — verify planner output matches expected mode

Dependencies: W0 (need exact paths and current v2.1 contents).

---

### W4 — Synthesis Prompt Extension

Goal: synthesis prompt now (a) narrates its reasoning into the SSE stream in astrological language, (b) corrects user factual errors, (c) inline-cites every inference, (d) annotates Sanskrit terms with inline spans, (e) flags out-of-domain queries.

Files:
- `platform/src/lib/prompts/synthesis_v2_0.md` (NEW — successor to current synthesis prompt; check W0 for current version number)
- `platform/src/lib/synthesis/single_model_strategy.ts` (UPDATE — read v2.0; parse the new reasoning side-channel)
- `platform/src/lib/synthesis/panel_strategy.ts` (UPDATE if it exists — same parsing for each panel member)
- `platform/tests/synthesis/correction_doctrine.test.ts` (NEW)
- `platform/tests/synthesis/reasoning_narration.test.ts` (NEW)
- `platform/tests/synthesis/sanskrit_annotation.test.ts` (NEW)
- `platform/tests/synthesis/out_of_domain.test.ts` (NEW)

Changes to synthesis prompt — these are additive sections on top of the current prompt; do not delete existing content unless it directly conflicts:

**Section: REASONING NARRATION**

> While synthesizing, emit a stream of short reasoning statements that narrate your in-the-moment thinking. Each statement must:
> - Use **classical Jyotish vocabulary** (e.g., "weighing Saturn's role in the 10th from Moon", "cross-referencing the Navamsa for marital indications", "considering the active Mahadasha lord's natal strength")
> - Be 8–18 words, declarative, one thought per line
> - Be wrapped in the marker `‹reasoning›...‹/reasoning›` and appear at natural inflection points in your synthesis (typically 4–8 per response)
> - **Never** reference internal IDs like MSR, FORENSIC, CGM, signal IDs, vector scores, etc. — only classical astrological concepts

**Section: FACTUAL CORRECTION DOCTRINE**

> If the user's query contains a factual error about their own chart (e.g., "since my Jupiter is in the 7th house" — when Jupiter is actually in the 5th), or a methodological error (e.g., applying Rasi rules to a Navamsa question), or a claim with no classical citation supporting it (e.g., "Saturn in 10th is always bad"):
>
> - **Lead the answer with the correction**, wrapped in `‹correction›...‹/correction›`, with structure:
>   ```
>   ‹correction›
>     original: "<verbatim quote of the user's incorrect claim>"
>     corrected: "<the actual fact, sourced from the chart or classical doctrine>"
>     source: "<classical text and verse, or chart citation>"
>   ‹/correction›
>   ```
> - Then proceed with the answer using the corrected facts. Do not ask the user for permission. Do not hedge unnecessarily — be polite but firm.
> - The bar for what counts as "factually wrong" is **no classical citation supports the claim**. Do not enforce majority view when the user holds a defensible minority position with classical backing.

**Section: INLINE REASONING + CITATIONS**

> The answer is a single piece of prose; there is no separate "Reasoning:" section. Reasoning is woven through the prose naturally, as in your default writing. Every inferential step — every claim that bridges from a fact to a conclusion — carries an inline citation marker `[N]` referring to entries in the post-answer source list. The conclusion is the natural payoff of the reasoning chain. Do not produce a bulleted derivation ledger.

**Section: SANSKRIT TERM ANNOTATION**

> When a Sanskrit, technical Jyotish, or otherwise specialized term appears in your answer, wrap it in `‹sanskrit term="<term>" def="<one-sentence definition>" translit="<IAST or simple roman>"›<display text>‹/sanskrit›`. The renderer turns this into a hover tooltip. Examples of terms to annotate: Vimshottari, Antardasha, Shadbala, Avastha, Karaka, Yoga, Argala, Argala-Pratyaki, Atmakaraka, Lagnesha, Sade-Sati, Drekkana, Navamsa, Ashtakavarga, etc. Do not annotate the same term twice within one answer.

**Section: OUT-OF-DOMAIN HANDLING**

> If the query is clearly outside the Jyotish scope of this instrument (e.g., "what's the weather", "summarize this PDF", "write me a poem unrelated to astrology"), emit `‹out_of_domain reason="<brief reason>"›‹/out_of_domain›` at the start of your response, then answer briefly (3–5 sentences) in good faith without elaborate scaffolding. The flag tells the UI to render an "outside scope" notice above the answer. Do not refuse; do not redirect; do not lecture.

The orchestrator (`single_model_strategy.ts`) parses the streaming model output:
- `‹reasoning›X‹/reasoning›` → emit `reasoning_step` SSE event with `phase: 'synthesis'`, text = X
- `‹correction›YAML‹/correction›` → emit `correction` SSE event with the parsed fields
- `‹sanskrit term=... def=... translit=...›display‹/sanskrit›` → strip from the answer stream (the renderer needs only the display text in `answer_chunk`), accumulate terms, emit `sanskrit_terms` SSE event at end
- `‹out_of_domain reason="X"›‹/out_of_domain›` → emit `out_of_domain` SSE event
- All other content → `answer_chunk` events

Tests:
- `correction_doctrine.test.ts`: 8 prompts with embedded factual errors → verify correction event emitted with right structure
- `reasoning_narration.test.ts`: any synthesis emits ≥3 reasoning events, all under 25 words, all in astrological vocabulary (assert no occurrence of "MSR", "FORENSIC", "CGM", "pgvector", "cosine", "embedding", etc. in any reasoning event)
- `sanskrit_annotation.test.ts`: prompts likely to use Sanskrit → ≥1 sanskrit_terms event emitted with valid structure
- `out_of_domain.test.ts`: 4 non-Jyotish prompts → out_of_domain event emitted; 4 Jyotish prompts → no out_of_domain event

Dependencies: W0 (current synthesis prompt version), W2 (SSE event types).

---

### W5 — Consume API Route SSE Multiplexing

Goal: `/api/chat/consume` now emits all 9 new SSE event types correctly, applies `prior_turn_relevance` from planner, generates conversation title on first turn.

Files:
- `platform/src/app/api/chat/consume/route.ts` (UPDATE)
- `platform/src/lib/consume/sse_emitter.ts` (NEW — small helper)
- `platform/src/lib/consume/conversation_title.ts` (NEW — Flash-based titler)
- `platform/tests/api/consume/sse_events.test.ts` (NEW)
- `platform/tests/api/consume/conversation_title.test.ts` (NEW)

Updates to `route.ts`:
1. After planner returns `QueryPlan` with `prior_turn_relevance`:
   - Trim `priorTurns` slice to the count specified by `prior_turn_relevance.used`
   - Emit `context_usage` SSE event with `prior_turns_used`, `reason`, `mode`
2. Before each pipeline stage starts, emit `reasoning_step` event with `phase: 'pipeline'`, text from `PIPELINE_STEP_NARRATION[stage]`
3. During synthesis streaming, parse model output for `‹reasoning›`, `‹correction›`, `‹sanskrit›`, `‹out_of_domain›` markers (delegated to W4 orchestrator) and forward as SSE events
4. After synthesis completes, emit `provenance` event with:
   - `models`: all model stages from this query (classifier, planner, retrieval ranker, synthesizer, any checkpoints fired) with role labels from `QUERY_CLASS_LABELS` / explicit per-stage role names
   - `sources.astrological`: assets used (from retrieval), each with `asset` (internal ID), `label` (from `ASSET_LABELS`), `items` (granular signal/chunk IDs with their own user-facing labels — produced by retrieval layer)
   - `sources.technical`: vector scores, graph depths, latencies, token counts, cache hits — formatted via `formatTechnicalTag`
5. On first turn of a new conversation:
   - Call `conversation_title.ts` (Flash-based, ~6 words from the first user query)
   - Persist title to DB (verify schema in W0; if missing, plan migration 046 — but most likely the existing `conversations` table already has a `title` column)
   - Emit `conversation_title` SSE event with the generated title
6. Emit `done` event at end, `error` event on failure

`sse_emitter.ts` helper:
```ts
export function emitSSE(controller: ReadableStreamDefaultController, event: SSEEventType, data: object) { ... }
```

`conversation_title.ts`:
- One Gemini Flash call (`gemini-2.0-flash-lite`)
- Input: first user query (raw)
- System prompt: "Summarize this question into a 4–7 word title in title case. No quotes, no punctuation at the end, no Sanskrit unless the question explicitly contains a Sanskrit term."
- Cache: never (it runs once per new conversation)
- Tests: 6 example queries → 6 reasonable titles (assert length 4–7 words, no trailing punctuation)

Tests for `route.ts`:
- A consume request with mocked planner+synthesis → all 9 event types fire in correct order
- A consume request on a brand-new conversation → `conversation_title` event fires
- A consume request continuing a known conversation → no `conversation_title` event
- A consume request where planner says `prior_turn_relevance.used = 0` → synthesis receives 0 prior turns
- A consume request where planner says `prior_turn_relevance.used = 2` → synthesis receives exactly 2 prior turns
- A non-Jyotish query → `out_of_domain` event fires

Dependencies: W2 (event types), W3 (planner output), W4 (synthesis orchestrator), W1 (labels for narration).

---

### W6 — Pipeline Event Translator

Goal: small pure module that converts internal pipeline events into astrological-domain narration strings via `PIPELINE_STEP_NARRATION`.

Files:
- `platform/src/lib/consume/pipeline_event_translator.ts` (NEW)
- `platform/tests/consume/pipeline_event_translator.test.ts` (NEW)

```ts
export function narratePipelineStep(stepName: string, metadata?: Record<string, any>): string {
  // Look up PIPELINE_STEP_NARRATION; fall back gracefully; log warning on miss
  // Optionally enrich with metadata, e.g., "Searching classical sources (3 candidates so far)"
  // Never include internal IDs in output
}
```

Tests: every key in `PIPELINE_STEP_NARRATION` produces a string with no banned tokens (`MSR`, `FORENSIC`, `CGM`, `pgvector`, `cosine`, `embedding`, `chunk`, etc.).

Dependencies: W1.

---

### W7 — LiveReasoningCard Component

Goal: the ambient, collapsible reasoning surface above the streaming answer.

Files:
- `platform/src/components/consume/LiveReasoningCard.tsx` (NEW)
- `platform/tests/consume/LiveReasoningCard.test.tsx` (NEW)

Props:
```ts
interface LiveReasoningCardProps {
  reasoningSteps: Array<{ phase: 'pipeline' | 'synthesis'; text: string; timestamp: number }>;
  isStreaming: boolean;
  defaultExpanded?: boolean; // false
}
```

Behavior:
- When `isStreaming === true` and there are no steps yet, show a small pulsing "thinking" dot + the text "Thinking…"
- When `isStreaming === true` and steps exist, show the **most recent step's text** as a single line with a leading pulsing dot indicator, plus a chevron-down icon on the right
- When `isStreaming === false`, show the most recent step's text (no pulse), plus a chevron-down icon
- Click the card or chevron → expand to show the full chronological list of steps (each: small timestamp, text); chevron rotates to chevron-up
- Click again → collapse
- Pipeline-phase steps and synthesis-phase steps render with subtly different styling (e.g., synthesis-phase has a slight indent or different muted accent), but no jargon difference

Styling:
- Compact card; subtle border or background; respects existing theme tokens
- Text is muted/secondary color; emphasizes calm, not urgency
- Pulse animation is gentle (1.5s ease-in-out, low contrast)
- Fits inline above the answer; does not overflow horizontally

Tests:
- Renders "Thinking…" with no steps
- Renders most-recent step with pulse when streaming
- Renders most-recent step without pulse after streaming
- Click expand → full list visible
- Click collapse → only most-recent visible
- Accessibility: chevron has aria-expanded; full list region has aria-labelledby

Dependencies: W2 (event types — for the prop shape), W1 (labels).

---

### W8 — AnswerView Updates

Goal: existing AnswerView now renders the correction prefix, inline citations, Sanskrit hover tooltips, context-usage cue, and out-of-domain notice.

Files:
- `platform/src/components/consume/AnswerView.tsx` (UPDATE)
- `platform/src/components/consume/CorrectionNotice.tsx` (NEW — small inline component)
- `platform/src/components/consume/ContextUsageCue.tsx` (NEW — small chip)
- `platform/src/components/consume/OutOfDomainBanner.tsx` (NEW)
- `platform/src/components/consume/SanskritTermSpan.tsx` (NEW — span with hover tooltip)
- `platform/tests/consume/AnswerView.test.tsx` (UPDATE)
- Test files for each new subcomponent

`CorrectionNotice`:
- If a `correction` SSE event was received, render as a compact, inline, polite-but-firm callout at the very top of the answer body — single line if possible:
  > **Note:** Your Jupiter is in the 5th house, not the 7th. Proceeding from the correct placement.
  - Optional small classical source citation if `classical_source` is present
  - Styling: thin amber-tinted left border, no heavy "warning" iconography, calm tone

`ContextUsageCue`:
- Small chip in the response header (or footer if header is crowded), e.g., `Independent query` / `1 prior turn (comprehension only)` / `2 prior turns (continuation)`
- Color is muted; no shouting

`OutOfDomainBanner`:
- Appears above the answer when `out_of_domain` event was received
- Single sentence: "This question is outside the Jyotish scope of this instrument — answering briefly."
- Calm, non-blocking

`SanskritTermSpan`:
- Wraps a span; on hover, shows a small tooltip with the term, transliteration (if present), and definition
- Tooltip is keyboard accessible (focus also triggers it)
- Term remains underlined with a dotted underline (or similar subtle indicator) so the native knows it's hoverable

`AnswerView` orchestration:
- Receives an answer payload (props or via state)
- Renders: OutOfDomainBanner (if applicable) → CorrectionNotice (if applicable) → ContextUsageCue → answer prose (with inline citation markers `[N]` linking to the post-answer source list) → PostAnswerProvenance (from W9)
- Sanskrit spans inside the prose render via SanskritTermSpan

Tests:
- Each subcomponent has its own focused test
- AnswerView with a correction → CorrectionNotice appears
- AnswerView with out-of-domain → banner appears
- AnswerView with 0 prior turns → context cue says "Independent"
- AnswerView with Sanskrit terms → hovering shows tooltip
- Inline citation `[1]` is clickable / focusable and scrolls to source list

Dependencies: W2, W1.

---

### W9 — Post-Answer Provenance (Pill Cluster + Drawer)

Goal: compact pill cluster below the answer; click any pill → drawer opens with full breakdown; drawer has two tabs (Astrological / Technical).

Files:
- `platform/src/components/consume/PostAnswerProvenance.tsx` (NEW — the pill cluster)
- `platform/src/components/consume/ProvenanceDrawer.tsx` (NEW — the expandable detail view)
- `platform/tests/consume/PostAnswerProvenance.test.tsx` (NEW)
- `platform/tests/consume/ProvenanceDrawer.test.tsx` (NEW)

`PostAnswerProvenance`:
- Receives a `ProvenanceEvent` payload
- Renders three pills in a single row, compact: `[3 models]`, `[4 sources]`, `[12 signals]` (counts dynamic; labels match the breakdown)
- Each pill has subtle border, hover state, click handler
- Click → opens `ProvenanceDrawer` focused on the clicked category

`ProvenanceDrawer`:
- Right-side slide-in drawer (or modal panel — match existing app patterns from W0 audit)
- Two tabs at the top: **Astrological** and **Technical**
- Astrological tab:
  - **Models** subsection: each model as a row with stage name (translated via QUERY_CLASS_LABELS / role strings), model ID (raw — this is a technical-but-already-public detail), latency, tokens
  - **Sources** subsection: each asset as a collapsible group: top row shows the translated asset label (from ASSET_LABELS) + count of items; expand → granular list of items with their per-item user-facing labels (each item also shows its own ID in a muted secondary line so the user can trace it if they want)
- Technical tab:
  - Compact list of technical tags from `provenance.sources.technical` — formatted via `formatTechnicalTag`
  - One per row, value + label
- Drawer closes on: ESC, outside click, close button
- Keyboard accessible

Tests:
- Pill cluster renders correct counts
- Click pill → drawer opens on correct tab
- Drawer tabs switch correctly
- Sources expand/collapse
- Translation: no internal jargon visible in Astrological tab (assert no occurrences of `MSR`, `FORENSIC`, `CGM`, etc.)

Dependencies: W1, W2.

---

### W10 — Conversation History Sidebar Drawer

Goal: a toggleable sidebar drawer on the consume page that lists prior conversations, with click-to-load.

Files:
- `platform/src/components/consume/ConversationHistoryDrawer.tsx` (NEW)
- `platform/src/components/consume/ConversationHistoryButton.tsx` (NEW — the toggle button in the header)
- `platform/src/app/api/consume/conversations/route.ts` (NEW or UPDATE — verify in W0; if exists, extend; if not, create)
- `platform/tests/consume/ConversationHistoryDrawer.test.tsx` (NEW)
- `platform/tests/api/consume/conversations.test.ts` (NEW)

`/api/consume/conversations` GET handler:
- Auth: native-tier or higher (existing auth pattern)
- Returns: `{ conversations: Array<{ id: string; title: string; last_message_at: string; message_count: number }> }`
- Pagination: query `?limit=50&offset=0`, return `total` in headers
- Ordered by `last_message_at DESC`

`ConversationHistoryDrawer`:
- Toggleable sidebar on the left of the consume page; collapses by default
- Lists conversations with: title, last message timestamp (relative — "2h ago", "Yesterday", "Mar 4")
- Click a conversation → navigate to `/clients/[id]/consume/[conversationId]`
- Search input at the top (filter by title contains)
- Empty state: "No prior conversations" with link to start one
- Loading state: skeleton rows
- Pagination: load-more button at the bottom (or infinite scroll, native's preference — choose infinite scroll for now; native can ask for change later)

`ConversationHistoryButton`:
- Sits in the consume page header next to the new-conversation button (if one exists; if not, add a "New conversation" button alongside)
- Icon: clock or history (lucide-react if available, else inline SVG — verify in W0)
- Click → toggle drawer open/closed
- Keyboard shortcut suggestion (visible in tooltip): `Cmd+B` or similar — only wire the shortcut if a similar shortcut pattern already exists in the app; otherwise skip

Tests:
- Drawer renders list from API
- Search filters list client-side
- Click → triggers navigation
- Pagination loads more
- API endpoint enforces auth
- API returns expected shape

Dependencies: W0 (verify existing API + DB schema for `conversations` table; if title column missing, plan migration 046 — but it almost certainly exists since the conversationId route already does).

---

### W11 — Empty State + Suggestions

Goal: empty consume page shows two-tab suggested queries — class-based and dasha/transit-context-based.

Files:
- `platform/src/components/consume/EmptyState.tsx` (NEW)
- `platform/src/app/api/consume/suggestions/context/route.ts` (NEW)
- `platform/src/lib/consume/class_suggestions.ts` (NEW — hardcoded class-based suggestions)
- `platform/tests/consume/EmptyState.test.tsx` (NEW)
- `platform/tests/api/consume/suggestions_context.test.ts` (NEW)

`class_suggestions.ts`:
- Exports `CLASS_SUGGESTIONS: Record<QueryClass, string[]>` with 4–6 example queries per class, written in plain English, varied
- Examples per class (use as starting set; refine for accuracy):
  - factual: "What house is my Moon in?", "What's my Atmakaraka?", "Which planets are vargottama?"
  - interpretive: "What does my Saturn-Moon affliction mean for my emotional life?", "How do I read the strength of my Lagna lord?"
  - predictive: "What does my current Mahadasha-Antardasha indicate for the next 18 months?", "How will the upcoming Jupiter transit affect my 10th house?"
  - discovery: "What unusual patterns show up across my divisional charts?", "Which yogas in my chart are most active right now?"
  - holistic: "Give me an overall reading of where I am right now", "Synthesize the dominant theme across my Rasi, Navamsa, and current dasha"

`/api/consume/suggestions/context` GET handler:
- Pulls active MD/AD/PD from a dasha utility (verify in W0 whether one exists — if not, this work item shrinks to "skip the By moment tab and ship only the By type tab; flag in CLAUDE.md for follow-up")
- Pulls top 3–5 current transit hits (transit-over-natal aspects active today)
- Sends both to Gemini Flash (`gemini-2.0-flash-lite`) with a prompt asking for 4–6 suggested questions grounded in this moment
- Returns: `{ suggestions: string[] }`
- Caches: per-session (keyed by user_id + current date), 24-hour TTL — use existing cache utility if present; otherwise in-memory module-level cache (acceptable for single-instance deployment)

`EmptyState.tsx`:
- Renders when `messages.length === 0` and no conversationId loaded
- Two tabs: **By type** | **By moment**
- "By type" tab: shows class-grouped suggestion lists (one accordion or column per class)
- "By moment" tab: fetches from API, shows the list; loading skeleton; empty state if API returns 0
- Click any suggestion → fills the input box (do not auto-submit)
- Above the tabs: a single welcoming line "Ask anything about your chart."

Tests:
- Renders both tabs
- Click suggestion → input value updates
- "By moment" tab fetches from API
- API handler returns valid shape; auth gated
- Cache hit on second call

Dependencies: W0 (verify dasha utility exists), W1.

---

### W12 — ConsumeChat Orchestration

Goal: wire all the new pieces into ConsumeChat — LiveReasoningCard above the streaming answer, PostAnswerProvenance below the answer, ConversationHistoryDrawer toggle in the header, EmptyState in the empty state.

Files:
- `platform/src/components/consume/ConsumeChat.tsx` (UPDATE)
- `platform/tests/consume/ConsumeChat.test.tsx` (UPDATE)

Changes:
1. Add SSE event subscription for all 9 event types from W2
2. State for: `reasoningSteps`, `correction`, `outOfDomain`, `contextUsage`, `sanskritTerms`, `provenance`, `conversationTitle`
3. Reset state on new query submission
4. Wire `LiveReasoningCard` directly above `StreamingAnswer` per turn
5. Wire `PostAnswerProvenance` directly below the completed answer per turn
6. Wire `ConversationHistoryDrawer` (collapsible left drawer) + button in header
7. Wire `EmptyState` when no messages and no conversationId
8. On `conversation_title` event: if currently on `/clients/[id]/consume/` (no conversationId), use Next.js router to push to `/clients/[id]/consume/[newConversationId]` — verify in W0 how new conversations are minted today; preserve that flow

Critical: the trace drawer (W0 confirms its location) is unchanged. ConsumeChat still wires it as before. Gate II will modernize it separately.

Tests:
- Empty state renders when no messages
- Submit query → reasoning steps appear → answer streams → provenance pills appear → next turn resets
- Correction event → CorrectionNotice renders in the answer
- Out-of-domain → banner renders
- History drawer toggles open/closed
- Sanskrit hover works inside streamed answer
- The trace drawer (Gate II surface) still renders without regression

Dependencies: W2, W7, W8, W9, W10, W11.

---

### W13 — StreamingAnswer Updates

Goal: StreamingAnswer now handles inline Sanskrit spans and inline citation markers from the `answer_chunk` event stream.

Files:
- `platform/src/components/consume/StreamingAnswer.tsx` (UPDATE)
- `platform/tests/consume/StreamingAnswer.test.tsx` (UPDATE)

Changes:
1. Accept `sanskritTerms` prop (from ConsumeChat); when rendering streamed text, post-process to wrap matching term occurrences in `SanskritTermSpan`
2. Inline citation markers `[N]` in the streamed text become clickable/focusable spans that scroll to source N in the provenance drawer
3. Handle the fact that Sanskrit terms might appear before the corresponding `sanskrit_terms` event arrives (it arrives near end) — fallback: render as plain text until terms arrive, then upgrade in place (or accept that some early text has plain spans — acceptable)

Tests:
- Streamed text + sanskrit_terms → terms become hoverable
- Streamed text with `[1]`, `[2]` → markers are interactive
- Trailing terms apply retroactively to earlier streamed text

Dependencies: W2, W8.

---

### W14 — Final Pass

Goal: everything green.

1. `npx tsc --noEmit` — must match or improve on the baseline (no new errors)
2. `npm run lint` — clean
3. `npm test` — all green; new tests + all existing tests pass
4. Manual smoke test:
   - Run the dev server
   - Submit one query from each of the 5 classes — verify all event types fire, all UI surfaces render, no console errors
   - Submit a query with a deliberate factual error ("since my Sun is in Pisces…" — verify what the actual chart says first via W0; pick a known-wrong placement) — verify CorrectionNotice fires
   - Submit a non-Jyotish query ("what's the weather in Bangalore tomorrow") — verify OutOfDomainBanner fires
   - Open the conversation history drawer — verify it lists prior conversations
   - Verify the trace drawer (Gate II surface) still opens and shows pipeline trace as before (no regression)
5. If anything fails, fix in-session and re-run. Do not move to W15 with red tests.

Dependencies: all prior W.

---

### W15 — Session Close & Manual Handoff

1. Move `CLAUDECODE_BRIEF.md` (the file at worktree root) → `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_III_v1_0.md` and set frontmatter `status: COMPLETE`. (This brief was originally authored at this path in the main repo; the worktree copy is what moves.)
2. Append a `SESSION_LOG.md` entry — convention from past briefs (see `SESSION_LOG.md` for the latest entry's shape; mirror it).
3. Commit everything on `feature/gate3-intelligent-chat`:
   - One commit per work item if practical, otherwise one batched commit per phase (W1–W6 = "Gate III: foundations"; W7–W13 = "Gate III: UI surfaces"; W14 = "Gate III: green pass")
   - Final commit message: `Gate III: Intelligent Chat Interface — SESSION COMPLETE`
4. Write `GATE_III_HANDOFF.md` at worktree root with:
   - Summary: what shipped
   - Manual review items the native must check (open consume → verify each surface)
   - Any deferred items (e.g., npm package requests from `GATE_III_PACKAGE_REQUESTS.md` if it exists)
   - List of files changed (with line counts)
   - Test pass/fail counts (new + total)
   - Confirmation that no files outside `may_touch` were touched
5. Do not merge to main. Macro plan conversation handles the merge sequence.

---

## §4 — Acceptance Criteria

All 25 must pass for session close.

- [ ] AC.III.1 — `lib/jyotish/domain_labels.ts` exists with `ASSET_LABELS`, `QUERY_CLASS_LABELS`, `PIPELINE_STEP_NARRATION`, `formatTechnicalTag`, `labelFor`
- [ ] AC.III.2 — Every key in `ASSET_LABELS` and `PIPELINE_STEP_NARRATION` has a non-empty, non-jargon value (verified by test)
- [ ] AC.III.3 — `types/sse_events.ts` exists with all 10 event types fully typed
- [ ] AC.III.4 — Planner emits `prior_turn_relevance` field with valid `used`, `reason`, `mode`
- [ ] AC.III.5 — Planner golden-set regression: recall ≥ 0.97, precision ≥ 0.95
- [ ] AC.III.6 — Synthesis prompt v2.0 includes reasoning narration, correction doctrine, inline citations, Sanskrit annotation, out-of-domain handling sections
- [ ] AC.III.7 — Synthesis orchestrator parses `‹reasoning›`, `‹correction›`, `‹sanskrit›`, `‹out_of_domain›` markers and emits matching SSE events
- [ ] AC.III.8 — Reasoning narration test: no reasoning step contains any banned token (`MSR`, `FORENSIC`, `CGM`, `UCN`, `CDLM`, `RM`, `LEL`, `pgvector`, `cosine`, `embedding`, `chunk_id`)
- [ ] AC.III.9 — Correction test: 8/8 prompts with factual errors trigger a `correction` SSE event with valid structure
- [ ] AC.III.10 — Out-of-domain test: 4/4 non-Jyotish prompts trigger `out_of_domain`; 4/4 Jyotish prompts do not
- [ ] AC.III.11 — Sanskrit annotation test: prompts likely to use Sanskrit emit at least one `sanskrit_terms` event with valid shape
- [ ] AC.III.12 — `/api/chat/consume` emits all 10 SSE event types in correct order on a representative query
- [ ] AC.III.13 — First turn of a new conversation emits `conversation_title` event; subsequent turns do not
- [ ] AC.III.14 — `LiveReasoningCard` renders thinking indicator, most-recent step, expand/collapse, and stays in place after streaming
- [ ] AC.III.15 — `AnswerView` renders CorrectionNotice when correction event present; OutOfDomainBanner when out_of_domain event present; ContextUsageCue with correct text per `mode`
- [ ] AC.III.16 — `SanskritTermSpan` renders hover tooltip with term, transliteration, definition; keyboard accessible
- [ ] AC.III.17 — `PostAnswerProvenance` renders three pills; click opens drawer; drawer has Astrological and Technical tabs; no internal jargon visible in Astrological tab
- [ ] AC.III.18 — `ConversationHistoryDrawer` lists prior conversations; click navigates; search filters
- [ ] AC.III.19 — `/api/consume/conversations` returns the expected shape and is auth-gated
- [ ] AC.III.20 — `EmptyState` renders two tabs; class-based suggestions appear; moment-based suggestions fetch and render
- [ ] AC.III.21 — `/api/consume/suggestions/context` returns valid suggestion list and is cached per-session
- [ ] AC.III.22 — `ConsumeChat` wires all new components without regression; trace drawer (Gate II surface) still opens and renders
- [ ] AC.III.23 — `npx tsc --noEmit`: no new errors compared to baseline
- [ ] AC.III.24 — `npm run lint`: clean
- [ ] AC.III.25 — `npm test`: all tests green (existing + new)

---

## §5 — LLM Stack

| Role | Model | Notes |
|---|---|---|
| Synthesis (critical) | `gemini-2.5-pro` | Default; no change from current |
| Planner | `gemini-2.5-pro` | Critical; no change |
| Classifier (if separate) | `gemini-2.0-flash-lite` | Cheap |
| Conversation title | `gemini-2.0-flash-lite` | One call per new conversation |
| Empty-state moment suggestions | `gemini-2.0-flash-lite` | Cached per session |
| Validator | (existing — do not change) | |

**BANNED:** `anthropic/*` — if seen in any file you touch or read, halt and write `GATE_III_BANNED_MODEL_FOUND.md` listing the file + line. Do not silently swap; report to native.

---

## §6 — Tests

Minimum coverage bar:
- Every new module has its own test file
- Every new SSE event type has shape + serialization tests
- Planner golden-set regression (existing 46-query suite) PASSES
- Synthesis prompt: 4 new test suites (correction, reasoning, Sanskrit, out-of-domain)
- Each new UI component has component tests covering: render, interaction (click/hover/keyboard), accessibility (aria-*)
- API routes have request/response tests + auth tests

Use Vitest. Mock pattern (per past project lesson): `mockImplementation(function() {...})` not arrow functions (Vitest 4.x).

---

## §7 — Migration Numbers

Range: 046 (Gate III's pre-assigned slot).

Default expectation: **0 migrations used**. The `conversations` table already exists (since `[conversationId]` route works); the `title` column likely already exists. Verify in W0.

If a migration is needed (e.g., to add a `title` column or a `prior_turn_relevance` audit column), use exactly 046, and only 046. Do not encroach on 045 (Gate II) or 047+ (future).

If the audit reveals that the `conversations` table doesn't have what we need, plan migration 046 in W0 and execute it before W10.

---

## §8 — Session Close Checklist

- [ ] All AC.III.1 through AC.III.25 pass
- [ ] `npm test` green
- [ ] `npx tsc --noEmit` no new errors vs baseline
- [ ] `npm run lint` clean
- [ ] All files touched are within `may_touch`; none in `must_not_touch`
- [ ] No new npm packages installed (or — if any were essential — flagged in `GATE_III_PACKAGE_REQUESTS.md` for native to install manually before merge)
- [ ] No `anthropic/*` models introduced anywhere
- [ ] CLAUDECODE_BRIEF.md moved from worktree root → `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_III_v1_0.md` with `status: COMPLETE`
- [ ] `SESSION_LOG.md` entry appended
- [ ] `GATE_III_HANDOFF.md` written at worktree root
- [ ] All commits pushed to `feature/gate3-intelligent-chat` (do not merge to main)
- [ ] Trace drawer surface (`components/trace/**`, `lib/admin/trace_assembler.ts`) is byte-identical to its state at session open — verified by `git diff --stat main -- 'platform/src/components/trace/' 'platform/src/lib/admin/trace_assembler.ts'` showing 0 changes

---

## §9 — Manual Steps (start and end)

### Before triggering the executor (native does these)
1. Confirm worktree is set up (`git worktree list` shows all three gate worktrees)
2. Confirm `npm install` completed in `marsys-gate3-smart-chat/platform`
3. Start Cloud SQL Auth Proxy on `127.0.0.1:5432`
4. Verify `.env.local` has `GEMINI_API_KEY` + GCS + Firebase keys
5. Place this brief at `/Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat/CLAUDECODE_BRIEF.md` (copy from `Madhav/00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_III_v1_0.md` — see post-brief instructions)
6. Open VS Code at the worktree path, launch Claude Code (Anti-Gravity), confirm `--dangerously-skip-permissions` enabled
7. Paste the trigger prompt (see post-brief instructions)

### After the executor reports done (native does these)
1. Read `GATE_III_HANDOFF.md` at worktree root
2. Run `npm run dev` and visually verify each surface (LiveReasoningCard, CorrectionNotice, history drawer, empty-state tabs, provenance pills + drawer, Sanskrit hover tooltips, context cue, out-of-domain banner)
3. Submit at least 5 queries (one per class) to spot-check
4. Submit one deliberately-wrong-factually query to verify correction fires
5. Submit one non-Jyotish query to verify out-of-domain fires
6. If all good, do NOT merge yet — wait for Gates I and II to also report done, then return to the macro plan conversation for the coordinated merge sequence

---

## §10 — Key Project Rules (reminder; non-negotiable)

- **B.10** — Synthesis never invents numerical chart values. If a value isn't in retrieved corpus, mark `[EXTERNAL_COMPUTATION_REQUIRED]` (existing rule; preserved by current synthesis prompt; do not regress).
- **B.11** — Every query routes through L2.5 Holistic Synthesis first (existing behavior; preserved).
- **File placement** — `ROOT_FILE_POLICY.md`. The only allowed root-level file Gate III creates is `CLAUDECODE_BRIEF.md` (which moves to `briefs/` at close), plus the transient `GATE_III_*.md` files (audit, handoff, conflict reports) which move or are deleted at close.
- **GCS URIs** — Layer-prefix only: `L1/`, `L2_5/`, `L3/`. Not used directly in Gate III but flag if seen.
- **DB migrations** — Query `pg_constraint` before any DELETE. Not expected in Gate III.
- **Vitest mocks** — `mockImplementation(function() {...})`, not arrow functions.
- **No new npm packages** — flag in `GATE_III_PACKAGE_REQUESTS.md` if essential.
- **No Anthropic models** — halt and report if seen.

---

## §11 — Architect's Locked Decisions (from planning session)

These are FIXED. The executor must NOT re-litigate any of these mid-session. If a decision appears impossible to implement as specified, halt and write `GATE_III_DESIGN_BLOCKER.md` describing the blocker — do not improvise around it.

1. Full chart pre-load: **dropped**. Retrieval is the only context mechanism.
2. Live reasoning surface vocabulary: **astrological only**. Internal IDs are translated.
3. Live reasoning surface placement: **inline above the streaming answer**.
4. Live reasoning visibility: **most-recent visible, full flow on click-to-expand**, persists after streaming.
5. Reasoning narration source: **both** pipeline events (translated) and synthesis-time LLM narration.
6. Final answer reasoning: **inline in prose**, no separate section.
7. Citations: **inline `[N]` markers in prose**, source list in provenance drawer.
8. Correction doctrine: **lead with correction**, no halt-and-confirm, weave into prose.
9. Correction scope: **all three** — chart facts, classical-consensus errors (when no citation backs the user's claim), methodological errors.
10. Correction bar: **"no classical citation supports the user's claim"** — do not enforce majority view when the user has classical backing.
11. Context handling: **smart per-query selection by planner**; context for comprehension only, never for substance.
12. Visible context cue: **yes**, shows mode (`Independent query` / `1 prior turn (comprehension only)` / etc.).
13. Provenance — models: **every model in chain**, hidden behind expand.
14. Provenance — sources: **asset-level visible**, granular on expand.
15. Provenance split: **astrological + technical tabs**, both hidden by default in the drawer.
16. Dasha/transit panel: **dropped**.
17. Sanskrit definitions: **hover tooltip only**, LLM-annotated at synthesis time.
18. Empty state: **two-tab toggle** — class-based + moment-based.
19. Conversation persistence: **across sessions**, listed in a left sidebar drawer.
20. Input intelligence: **none**. Minimalist input.
21. Visual baseline: **current visual**; enhance, don't redesign.
22. Conversation auto-titling: **after first user query**, one Flash call.
23. Out-of-domain: **answer briefly + flag prominently with banner**; do not refuse or redirect.

---

*End of CLAUDECODE_BRIEF_GATE_III_v1_0.md*
*Authored by Claude Opus 4.7 — Gate III Design Session — 2026-05-12*
