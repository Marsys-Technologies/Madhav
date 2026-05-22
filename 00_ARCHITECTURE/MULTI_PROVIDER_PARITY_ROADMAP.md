---
artifact: MULTI_PROVIDER_PARITY_ROADMAP.md
project_name: Claude Takeover
version: 1.0
status: CURRENT
authored_on: 2026-05-22
authoring_session: Cowork — Claude Takeover (R11 v2 Multi-Provider Parity) planning
role: >
  Strategic sequencing document for the Multi-Provider Parity arc — the
  multi-phase workstream that brings Marsys consume chat to best-in-class
  capability across all 5 active LLM providers (Anthropic, Google,
  OpenAI, DeepSeek, NVIDIA). This document supersedes the original R11
  single-round plan; R11 is now the umbrella name for the full arc
  R11.A through R11.K.
companion_docs:
  - 00_ARCHITECTURE/CAPABILITY_MATRIX.md (per-capability per-provider status)
  - 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md (umbrella plan)
  - 00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md (why R11 v1 was retired)
---

# Claude Takeover — Multi-Provider Parity Roadmap

> **Project codename:** Claude Takeover. This roadmap sequences the phases of the project that brings Marsys consume chat to best-in-class capability across all 5 active LLM providers.

## §1 — Mission

Bring Marsys consume chat to **best-in-class capability across all 5 active LLM providers**, with a provider-agnostic abstraction layer that:

1. Exposes the **native best capability** each provider offers (rather than collapsing to lowest common denominator).
2. **Hides UI affordances** when the active provider doesn't support a feature, with a "switch stack to use this" hint (per the locked fallback policy).
3. Routes each capability call to the active provider's adapter, so the chat surface never contains provider-specific code.

Reference: `CAPABILITY_MATRIX.md` is the per-capability per-provider data; this document is the **sequencing arc**.

## §2 — Governing amendments (inherited from R11 v1; carry forward)

All R11 v2 phases inherit and re-assert:

1. **NEXT_PUBLIC build-arg discipline** — every client-side flag in `.github/workflows/deploy.yml --build-arg` block (HARD GATE at phase-MERGE).
2. **Mount-verification + parent-context integration test** — every visible component has a click-path documented + a parent-context test.
3. **§M.16 flagless precedent** — purely-additive sessions carry no flag.
4. **Preserved prompt blocks** — R7-S2 footnote block and Y-S4 step-marker instructions remain byte-identical wherever the synthesis prompt is restructured. (R11 v2 may eventually retire these per inline-citation parity, but ANY phase that touches the prompt without intending to retire them MUST preserve verbatim.)
5. **Per-phase deploy.yml coverage gate** — HARD at phase-close. `grep` coverage check before PR opens.
6. **Hide-and-hint fallback** (NEW per R11 v2) — when a provider doesn't natively support a capability, the UI hides the affordance and surfaces a small "Switch to <stack>" hint. No polyfills by default; no auto-routing without explicit user consent.

## §3 — Phase sequence

Eleven phases total. Sequential within each phase; phases run in declared order. Phase X's `depends_on: phase X-1` unless declared parallel-safe.

### R11.A — Foundation (the substrate everything else builds on)

**Goal:** Stand up the provider-agnostic capability adapter layer. No user-facing features yet — pure infrastructure.

**Sessions** (~14, including R11A-MERGE):
- A-S0 — Capability manifest schema + types
- A-S1 — Provider adapter interface (shared TypeScript interfaces for all capabilities)
- A-S2 — Anthropic adapter skeleton + manifest declaration
- A-S3 — Google (Gemini) adapter skeleton + manifest declaration
- A-S4 — OpenAI adapter skeleton + manifest declaration
- A-S5 — DeepSeek adapter skeleton + manifest declaration
- A-S6 — NVIDIA NIM adapter skeleton + manifest declaration
- A-S7 — Capability dispatcher (central registry; chat surface calls this)
- A-S8 — UI capability-availability surface (hide-and-hint affordance reader)
- A-S9 — Telemetry — log capability paths per request (Observatory integration)
- A-S10 — Migration adapter (wrap existing single-shot pipeline; existing behavior preserved)
- A-S11 — Runtime user toggle for the new chat shell (Classic ⇄ Multi-Provider-Parity mode)
- A-S12 — Foundation tests (5-provider basic ping-pong + capability manifest validation)
- R11A-MERGE — push, PR, auto-merge to main

**Est. duration:** 14-18 hours autonomous Claude Code time.
**Provider scope:** All 5.
**Risk:** Medium-low. Substrate code; no user-facing changes.
**Depends on:** Nothing. R11.A is the foundation.
**Parallel-safe with:** R11.K image generation (low overlap), but recommend serial for cleanliness.

### R11.B — Visual + Look-and-Feel parity

**Goal:** Ship Claude.ai-style content rendering inside the existing Marsys palette. Effectively the V-group from R11 v1, re-scoped to use the R11.A adapter layer.

**Sessions** (~10, including R11B-MERGE):
- B-S0 — Adapter capability check (rendering is provider-agnostic; just verifies dispatcher is healthy)
- B-S1 — Typography stack (Claude system-serif body + sans chrome + mono code inside `.consume-shell`)
- B-S2 — User-bubble dimensions (Marsys glassmorphic speech-tail preserved; Claude shape constants applied)
- B-S3 — Message-container shape (bubble-less assistant + 768px centered column + hover-reveal action bar)
- B-S4 — Composer chrome (Claude-minimal shape + Marsys gold focus retained)
- B-S5 — Sidebar chrome (Claude-compact list items + Marsys dark surface retained)
- B-S6 — Markdown content typescale (serif h1-h3, code-block treatment)
- B-S7 — Inline citation extension (NumberedCitation extended for web URL click-out + freshness in popover; CitationSidePanel retired)
- B-S8 — Marsys brand preservation audit (verify `.brand-cta`, gold-hairlines, speech-tail, Devanagari accents all intact)
- R11B-MERGE

**Est. duration:** 10-13 hours.
**Provider scope:** All 5 (rendering layer is provider-agnostic).
**Risk:** Low-medium. UI restyling within shipped Marsys palette.
**Depends on:** R11.A (uses dispatcher to read theme preference).

### R11.C — Streaming + Thinking (per-provider)

**Goal:** Smooth-stream rate-target across all providers; pre-token thinking indicator; extended-thinking visualization with auto-collapse; tool-card inline rendering tightened.

**Sessions** (~8, including R11C-MERGE):
- C-S0 — Streaming capability check via adapter
- C-S1 — Pre-token thinking indicator (per-provider thinking-detection)
- C-S2 — Smooth-stream rate-target (~30-50 cps; per-provider buffering)
- C-S3 — Extended-thinking visualization unified across Anthropic + Gemini + DeepSeek (auto-collapse on first text_delta)
- C-S4 — Adaptive thinking budgets (`thinking.effort` for Anthropic, `thinkingBudget` for Gemini, polyfill for others)
- C-S5 — Inline tool cards (verify ToolCallCard inline stream order across all providers)
- C-S6 — Stop button morph + partial-turn DB persistence (verify across all providers)
- R11C-MERGE

**Est. duration:** 8-12 hours.
**Provider scope:** All 5.
**Risk:** Medium. Cross-provider streaming behavior verification.
**Depends on:** R11.A.

### R11.D — Caching + Cache-Aware Prompt Layout (per-provider)

**Goal:** Each provider's caching API wired (Anthropic 4-breakpoint, Gemini cachedContent, OpenAI automatic, DeepSeek implicit, NVIDIA n/a). Cache hit-rate observability across all providers.

**Sessions** (~7, including R11D-MERGE):
- D-S0 — Caching capability check via adapter
- D-S1 — Anthropic 4-breakpoint `cache_control` wiring (canonical layout: tools → system → RAG bundle → last assistant)
- D-S2 — Gemini `cachedContent` API integration
- D-S3 — OpenAI automatic caching — telemetry capture (no markers needed)
- D-S4 — DeepSeek implicit caching — telemetry capture
- D-S5 — Cache-aware prompt layout migration (system-prompt order for cache-friendliness)
- D-S6 — Observatory dashboard tile (cache hit rate × provider × per-day)
- R11D-MERGE

**Est. duration:** 8-12 hours.
**Provider scope:** All 5 (NVIDIA = n/a; documented as such).
**Risk:** Medium-high. Cache-related cost regressions are easy to miss; gates measure hit-rate.
**Depends on:** R11.A.

### R11.E — Adaptive Tool Sequencing (multi-step agentic loops per-provider)

**Goal:** Replace single-shot planner with adaptive tool loops that key on each provider's native stop signal. The agentic-loop work originally scoped as R11 v1 O-S3.

**Sessions** (~10, including R11E-MERGE):
- E-S0 — Tool-loop capability check via adapter
- E-S1 — Anthropic `stop_reason: tool_use` while-loop (canonical)
- E-S2 — Gemini `finish_reason: function_calls` while-loop
- E-S3 — OpenAI `finish_reason: tool_calls` while-loop (Responses API where available)
- E-S4 — DeepSeek (OpenAI-compat loop)
- E-S5 — NVIDIA hosted-model loop (depends on model)
- E-S6 — Interleaved text + tool block streaming (Claude 4.x + Gemini 2.5 patterns)
- E-S7 — Tool error recovery (model sees error, retries or pivots)
- E-S8 — Iteration cap safety (8-iteration default, configurable)
- E-S9 — Tool-loop observability (per-iteration usage in Observatory)
- R11E-MERGE

**Est. duration:** 12-16 hours.
**Provider scope:** All 5 (NVIDIA depends on which hosted model is active).
**Risk:** HIGH. Biggest behavioral change. Default false until verified per stack.
**Depends on:** R11.A, R11.D (prompt caching means agentic loops aren't ruinously expensive).

### R11.F — Server-Side Tools (web search, web fetch, code execution)

**Goal:** Wire each provider's native server-side tools through the unified adapter. UI shows the new capabilities as composer affordances ("Search the web", "Run code") that route to the active provider's native implementation.

**Sessions** (~14, including R11F-MERGE):
- F-S0 — Server-tool capability check via adapter
- F-S1 — Anthropic `web_search` tool wiring + result rendering
- F-S2 — Anthropic `web_fetch` tool wiring
- F-S3 — Anthropic `code_execution` tool wiring + sandboxed result rendering
- F-S4 — Gemini Google Search grounding + groundingMetadata citation extraction
- F-S5 — Gemini Code Execution built-in
- F-S6 — OpenAI `web_search_preview` (Responses API)
- F-S7 — OpenAI Code Interpreter
- F-S8 — Unified citation rendering from web-search results (across all providers — inline at the claim, freshness shown)
- F-S9 — Unified code-execution result rendering (charts, file outputs, errors)
- F-S10 — UI composer affordances (Search button, Code button — visible only when active stack supports)
- F-S11 — Hide-and-hint behavior for DeepSeek + NVIDIA (no server tools — show "switch stack" hint)
- F-S12 — Cost attribution (cited tokens not billed; per-tool cost tracking)
- F-S13 — Server-tool observability (which tool fired, on which provider, with what result)
- R11F-MERGE

**Est. duration:** 16-22 hours.
**Provider scope:** All 5 (DeepSeek + NVIDIA hide-and-hint).
**Risk:** Medium-high. Each provider's server-tool API differs significantly; per-provider integration testing is essential.
**Depends on:** R11.A, R11.E (server tools work best inside the agentic loop).

### R11.G — Memory + Projects + Deep Context

**Goal:** Cross-conversation memory store (provider-agnostic, queried as a tool by any stack) + native memory integration where the provider supports it + Projects deep context binding.

**Sessions** (~11, including R11G-MERGE):
- G-S0 — Memory capability check via adapter
- G-S1 — Marsys unified memory store schema + DB migration (vector + key-value hybrid)
- G-S2 — Memory recall tool (any provider can call this as a function/tool)
- G-S3 — Memory write tool (extract user preferences + facts from conversations)
- G-S4 — Memory UI (user-facing memory list + delete affordance)
- G-S5 — Anthropic native Memory tool integration (Claude 4.5+) — bridge to Marsys store
- G-S6 — OpenAI Memory feature integration where available (ChatGPT product-specific; mostly polyfill via Marsys store for API)
- G-S7 — Projects-scoped system prompt + persona (extends R9-S1 abstraction)
- G-S8 — Projects-scoped file context (auto-injected as system message or RAG)
- G-S9 — Projects-scoped conversation summarization (history compaction with project awareness)
- G-S10 — Anthropic Compaction API integration where context window approaches limit
- R11G-MERGE

**Est. duration:** 12-16 hours.
**Provider scope:** All 5 (memory store is provider-agnostic; native integration where available).
**Risk:** Medium. Schema-touching session; data migration required.
**Depends on:** R11.A.

### R11.H — Learning-Layer Adaptation (deferred until Learning Layer scaffolds)

**Goal:** Tool-affordance learning + preference learning + prediction-outcome feedback loops via the Learning Layer.

**STATUS: BLOCKED on `06_LEARNING_LAYER/` scaffold per `MACRO_PLAN_v2_0.md`.** R11.H is the FIRST round to depend on the Learning Layer. R11.H scoping happens AFTER the Learning Layer scaffold lands. Until then, R11.H sits as a placeholder with no sessions authored.

**Estimated sessions when ready:** ~12-15.
**Provider scope:** Provider-agnostic (Learning Layer feedback applies to any stack).
**Risk:** Higher uncertainty due to upstream dependency.
**Depends on:** R11.A, R11.G (memory store needed for preference signal storage), `06_LEARNING_LAYER/` scaffold.

### R11.I — Multi-Modal Input + Voice Output

**Goal:** Audio + video input where each provider supports; voice output (TTS streaming) where supported. Image input already shipped (R8-S7).

**Sessions** (~14, including R11I-MERGE):
- I-S0 — Multi-modal capability check via adapter
- I-S1 — Audio input UI (record button in composer, file-upload via attachment)
- I-S2 — Gemini Live API integration (real-time audio in + voice out)
- I-S3 — OpenAI Audio Preview model integration
- I-S4 — Video input UI (file-upload as attachment)
- I-S5 — Gemini 2.5 video input (frame extraction + native multimodal)
- I-S6 — OpenAI video input (frame-by-frame; partial)
- I-S7 — PDF input — Files API integration (Anthropic + Gemini + OpenAI)
- I-S8 — Voice output (TTS) — Gemini Live streaming
- I-S9 — Voice output (TTS) — OpenAI Audio Preview
- I-S10 — Voice playback UI (pause/resume/scrub)
- I-S11 — Per-modality cost observability
- I-S12 — Hide-and-hint for stacks lacking each modality (Anthropic = no voice; DeepSeek/NVIDIA = no audio/video)
- I-S13 — Smoke test across each modality × provider matrix
- R11I-MERGE

**Est. duration:** 16-22 hours.
**Provider scope:** All 5 with extensive hide-and-hint.
**Risk:** Medium-high. New surfaces (audio in/out, video) with provider-specific quirks.
**Depends on:** R11.A.

### R11.J — Artifacts (live-rendered HTML/React/SVG, editable, multi-file)

**Goal:** Claude.ai-style artifacts that render live in-chat and are editable across turns. Provider-agnostic since rendering is client-side; provider only needs to emit artifact-marked content via system-prompt convention.

**Sessions** (~11, including R11J-MERGE):
- J-S0 — Artifact capability declaration (all providers ★ via system-prompt convention)
- J-S1 — Artifact data-part shape definition (SSE part for artifact content + version + type)
- J-S2 — Artifact extraction in synthesis (parse artifact blocks from model output across all 5 providers via system-prompt convention)
- J-S3 — Artifact rendering — HTML / SVG sandbox
- J-S4 — Artifact rendering — React (Tailwind-only, no localStorage per Marsys artifact rules)
- J-S5 — Artifact rendering — Mermaid (extends R10 X-S11)
- J-S6 — Artifact version history (per-conversation artifact list with diff view)
- J-S7 — Artifact edit affordance (user requests modification → next turn emits updated artifact)
- J-S8 — Multi-file artifact (project workspace inside chat)
- J-S9 — Artifact share / export
- J-S10 — Artifact cost observability (artifact emission is content tokens; no special accounting)
- R11J-MERGE

**Est. duration:** 12-16 hours.
**Provider scope:** All 5 (provider-agnostic via system-prompt convention).
**Risk:** Medium. Sandboxing + iframe security require care.
**Depends on:** R11.A.

### R11.K — Computer Use / Agentic Browsing + Image Generation

**Goal:** Agentic browsing across providers + image generation as a tool.

**Sessions** (~13, including R11K-MERGE):
- K-S0 — Computer-use + image-gen capability check via adapter
- K-S1 — Anthropic Computer Use API integration (screenshot + click + type)
- K-S2 — OpenAI Computer Use Agent (CUA) via Responses API
- K-S3 — Gemini browser tool calling (limited)
- K-S4 — Marsys-side Chrome MCP integration (extends MCP workstream)
- K-S5 — Long-running async agent infrastructure (hours, not minutes)
- K-S6 — Image generation — Imagen via Gemini API
- K-S7 — Image generation — gpt-image-1 via OpenAI API
- K-S8 — Image generation — DALL-E via OpenAI tool call
- K-S9 — Image rendering in chat (inline + downloadable)
- K-S10 — Computer-use safety (action confirmation prompts for destructive operations)
- K-S11 — Computer-use observability (per-action audit log)
- K-S12 — Hide-and-hint for DeepSeek/NVIDIA (no computer use, no image gen)
- R11K-MERGE

**Est. duration:** 16-22 hours.
**Provider scope:** All 5 with extensive hide-and-hint.
**Risk:** HIGH. Computer Use has real-world side effects; safety prompts mandatory.
**Depends on:** R11.A, R11.E (computer use works best in agentic loops).

## §4 — Sequencing rationale

**Why R11.A is first:** The adapter substrate must exist before any capability ships. Sub-agents can't write provider-aware code without an interface to write against.

**Why R11.B and R11.C precede R11.D:** Visual and streaming changes are user-perceivable; they give the native confidence the substrate works before we touch cost-sensitive caching (R11.D) and behavior-sensitive agentic loops (R11.E).

**Why R11.D before R11.E:** Adaptive tool loops can issue many provider calls per turn; without caching, costs balloon. Caching makes agentic loops affordable.

**Why R11.F (server tools) depends on R11.E:** Server tools are most effective inside an agentic loop where the model can iterate on tool results.

**Why R11.G (memory) before R11.H (Learning Layer):** The unified memory store IS the substrate for preference learning.

**Why R11.H is blocked:** Learning Layer scaffold (`06_LEARNING_LAYER/`) is currently deferred per MACRO_PLAN. R11.H sits as a placeholder.

**Why R11.I (multi-modal) is parallel-safe with R11.J (artifacts):** No shared file scope.

**Why R11.K (computer use + image gen) is last:** Highest blast radius; depends on all prior phases for safety + integration.

## §5 — Total scope summary

**Active commitment (2026-05-22, amended to drop R11.F):** R11.A through R11.E only. R11.F through R11.K are DEFERRED to a future arc per native scope decision; their content remains below as future planning material.

| Phase | Sessions | Est. hours | Cumulative hours | Provider scope | Risk | Commitment status |
|---|---|---|---|---|---|---|
| R11.A | 14 | 14-18 | 14-18 | All 5 | Medium-low | **COMPLETE 2026-05-22** — merge SHA f2df0524 (PR #143) |
| R11.B | 10 | 10-13 | 24-31 | All 5 | Low-medium | **COMPLETE 2026-05-22** — merge SHA 24a21dda (PR #145) |
| R11.C | 8 | 8-12 | 32-43 | All 5 | Medium | **COMPLETE 2026-05-22** — merge SHA d268d429 (PR #144) |
| R11.D | 7 | 8-12 | 40-55 | All 5 | Medium-high | **COMPLETE 2026-05-22** — merge SHA e9cbffc9 (PR #146) |
| R11.E | 10 | 12-16 | 52-71 | All 5 | HIGH | **COMPLETE 2026-05-22** — merge SHA 5d0064f9 (PR #147) |
| R11.F | 14 | 16-22 | 68-93 | All 5 (2 hide-and-hint) | Medium-high | **DEFERRED 2026-05-22** |
| R11.G | 11 | 12-16 | 80-109 | All 5 | Medium | **DEFERRED 2026-05-22** |
| R11.H | ~12-15 | TBD | TBD | All 5 | BLOCKED on Learning Layer | **DEFERRED 2026-05-22** + BLOCKED |
| R11.I | 14 | 16-22 | 96-131 | All 5 (extensive hide-and-hint) | Medium-high | **DEFERRED 2026-05-22** |
| R11.J | 11 | 12-16 | 108-147 | All 5 | Medium | **DEFERRED 2026-05-22** |
| R11.K | 13 | 16-22 | 124-169 | All 5 (DeepSeek/NVIDIA hide-and-hint) | HIGH | **DEFERRED 2026-05-22** |
| **ACTIVE TOTAL (R11.A–R11.E)** | **49** | **52-71** | — | — | — | — |
| FULL-ARC TOTAL (incl. deferred, excl. H) | 112 | 124-169 | — | — | — | future-state reference |

**Wall-clock estimate for active commitment (R11.A–R11.E):** **~52-71 hours of autonomous Claude Code time, spread across ~5-7 calendar weeks** assuming 1-2 phase launches per week with halt-triage breaks.

**Future-arc estimate (R11.F + R11.G + R11.I + R11.J + R11.K):** another ~72-98 hours when re-scoped. R11.H adds another ~12-20 hours when the Learning Layer scaffold lands.

## §6 — Per-phase launch pattern (inherited from R11 v1 + Conductor v1)

Each phase ships via its own Conductor instance:
- `00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-<X>/` — per-phase brief bundle
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11<X>_v1_0.md` — per-phase orchestrator
- `00_ARCHITECTURE/CONDUCTOR/session_queue_R11<X>.yaml` — per-phase queue
- Each phase commits to its own branch: `chat-v2/round11-<X>-<scope-tag>` (e.g., `chat-v2/round11-a-foundation`, `chat-v2/round11-b-look-and-feel`)
- Each phase opens its own worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavR11<X>`
- Each phase auto-merges to main at phase-close (per the existing R11 native-override pattern)

Phases run **sequentially** by default. After each phase merges, the native triggers the next phase's setup via a new Claude Code prompt (paste-into-Antigravity per `USER_INTERACTION_PREFERENCES.md §1`).

## §7 — Living document protocol

This file is **CURRENT** (versioned). Updated when:

- A phase closes — append `closed_on` + merge SHA to that phase's row in §3.
- A phase's session count is revised upward/downward — update §5 table.
- A new phase is inserted or reordered — bump to version 1.1+.
- R11.H unblocks (Learning Layer scaffold lands) — author R11.H session list.

Per the project's `ONGOING_HYGIENE_POLICIES_v1_0.md`, this file is **never silently mutated**; every revision carries a changelog entry below.

## §8 — Decision audit trail

| Decision | Date | Source | Rationale |
|---|---|---|---|
| Scope: All 4 clusters (A+B+C+D) | 2026-05-22 | Native, Cowork chat | Wants "complete Claude experience" with multi-provider parity |
| Fallback policy: hide-and-hint | 2026-05-22 | Native, Cowork chat | User stays in control; no surprises |
| Deliverable shape: matrix + roadmap + R11.A bundle | 2026-05-22 | Native, Cowork chat | Most rigorous; later rounds authored just-before |
| R11 v1 disposition: SUPERSEDED | 2026-05-22 | Native, Cowork chat | Cleanest mental model; no half-launched state |
| Provider count: 5 (anthropic, google, openai, deepseek, nvidia) | 2026-05-22 | Codebase verification | All five currently active per `lib/models/registry.ts` |
| R11.H blocked on Learning Layer | 2026-05-22 | MACRO_PLAN_v2_0.md | Learning Layer scaffold currently deferred |

---

*End of MULTI_PROVIDER_PARITY_ROADMAP.md v1.0.*
*Authored 2026-05-22 in Cowork session that scoped Multi-Provider Parity.*
*Future updates append §9 (changelog) below this line as phases close.*
