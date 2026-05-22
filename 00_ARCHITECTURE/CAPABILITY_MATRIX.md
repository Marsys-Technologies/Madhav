---
artifact: CAPABILITY_MATRIX.md
project_name: Claude Takeover
version: 1.0
status: LIVING
authored_on: 2026-05-22
authoring_session: Cowork — Claude Takeover (R11 v2 Multi-Provider Parity) planning
role: >
  Single source of truth for every chat capability the consume surface
  supports (or aims to support) × every active LLM provider. Updated at
  every phase-close of the Multi-Provider Parity (R11 v2) arc. Future
  rounds adding new capabilities or providers append rows/columns; future
  rounds shipping a capability flip its status cell from `planned` to
  `shipped`.

  This file is the authoritative answer to the question "what does our
  chat do, on what stack, and what's the gap?"
consumers:
  - Every R11.A through R11.L+ session brief (frontmatter pointer)
  - Future Cowork sessions planning new rounds
  - MULTI_PROVIDER_PARITY_ROADMAP.md (sequencing depends on this matrix)
  - Sub-agents executing capability sessions (read at session open)
mirror_obligations:
  claude_side: CAPABILITY_MATRIX.md (this file)
  gemini_side: tbd — declared when first Gemini-side review touches it
---

# Capability Matrix — Claude Takeover (Marsys Chat × 5 LLM Providers)

> **Project codename:** Claude Takeover. Single source of truth for every chat capability × every provider; status tracker for the active arc (R11.A-E).

## §1 — Purpose

The Marsys consume chat surface aims to expose the **best capability each LLM
provider offers** through a single provider-agnostic UI. This matrix is the
catalog of every capability we track and the per-provider status.

Five active providers: `anthropic`, `google` (Gemini), `openai` (GPT),
`deepseek`, `nvidia` (NIM). Provider selection happens per-conversation via
the existing stack picker in `lib/models/runtime_config.ts`.

## §2 — Symbol legend

| Symbol | Meaning |
|---|---|
| **★** | Native, best-in-class on this provider. The provider's own implementation; canonical. |
| **○** | Native, supported but not best-in-class on this provider. Works but doesn't lead. |
| **▶** | Polyfilled — built on top of provider's primitives but not native to it (e.g., "think step by step" system-prompt nudge to simulate extended thinking on GPT). |
| **—** | Absent. Provider does not support this capability at all. UI hides the affordance and shows a "switch stack to use this" hint per `NATIVE_RULINGS_v1_0.md §8`-equivalent fallback policy. |
| **🚧** | Planned but not yet shipped in Marsys. Future round will deliver. |
| **✓** | Shipped in Marsys today. |

A cell may carry multiple symbols (e.g., **★ 🚧** = native to this provider AND planned but not yet shipped). The status track is independent of the capability-availability track.

## §3 — How to read this matrix

Each row is one chat capability. Each column-pair is one provider, with two sub-cells: **(a)** the provider's native support level, **(b)** the Marsys ship status. Read together, the cell answers two questions: "does this provider support it?" and "have we wired it in our chat yet?"

The matrix is grouped into four clusters matching the R11 v2 roadmap:
- **Cluster A** — Foundation, Look-and-Feel, Streaming, Thinking, Caching, Adaptive Tools
- **Cluster B** — Server-Side Tools
- **Cluster C** — Memory, Projects, Learning-Layer Adaptation
- **Cluster D** — Multi-Modal, Artifacts, Computer Use

## §4 — Cluster A: Foundation + Look-and-Feel + Streaming + Thinking + Caching + Adaptive Tools

### A.1 Visual + look-and-feel (client-side rendering — provider-agnostic)

These are UI-only capabilities. The active provider does not influence rendering; any provider that streams content into the unified `data-text`/`data-tool`/`data-citation` parts gets the rendering for free.

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Serif body + sans chrome + mono code typography | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.B |
| Bubble-less assistant + Claude-shaped user bubble | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.B |
| 768px centered reading column | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.B |
| Hover-reveal action bar | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.B |
| Minimal-shape composer (rounded, no shadow, fades-in) | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.B |
| Claude-typescale markdown rendering (h1-h3, code blocks) | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.B |
| Runtime user toggle (Classic ⇄ Claude-parity mode) | ★ provider-agnostic | ★ | ★ | ★ | ★ | 🚧 R11.A |
| Camera capture on mobile | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 X-S1 |
| Font-size control | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 X-S7 |
| Selective share + print-friendly | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 X-S8/X-S9 |
| Interactive tables (sort/filter/CSV) | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 X-S10 |
| Mermaid diagrams in messages | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 X-S11 |
| Conversation branching (regenerate + branch picker) | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R8-S1/S2 |
| Conversation search (FTS + semantic) | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R8-S3 + R9-S2 |
| Composer draft persistence | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R7-S6 |
| Personas / styles library | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R9-S3 |
| Pin / archive / folders | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R8-S4 |
| Slash command menu | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R8-S6 |
| Token estimate in composer | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R8-S5 |
| Conversation export (MD/JSON/PDF) | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R8-S8 |
| Inline citation (superscript + hover preview + click-out) | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ Y-S1+Y-S2 + 🚧 R11.B extends to URL click-out |
| Citation freshness badge | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 Y-S2 |
| Validator per-gate expander | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 Y-S8 |

### A.2 Streaming + thinking

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Pre-token "Thinking… Ns" indicator | ★ visible thinking blocks | ★ native `thinking` parts | ▶ no thinking; show elapsed counter only | ★ inline `<think>` blocks | — (depends on model) | 🚧 R11.C |
| Smooth-stream rate-target (~30-50 cps uniform) | ★ provider-agnostic (server adapter) | ★ | ★ | ★ | ★ | 🚧 R11.C (extends Y-S3 word-aware) |
| Extended thinking visible to user | ★ `thinking` content blocks | ★ native `thinking` UIMessage parts | — (o-series deprecated in codebase) | ★ `<think>` middleware extracts | — | ✓ R10 Y-S4 (Anthropic + Gemini + DeepSeek paths) + 🚧 R11.C auto-collapse |
| Adaptive thinking budget | ★ `thinking.effort` (Opus 4.6+, Sonnet 4.6+) | ★ `thinkingBudget: 24576` integer | — | ▶ `thinking: true/false` toggle | — | 🚧 R11.C (per-provider adapter) |
| Extended thinking auto-collapse on first text_delta | ★ provider-agnostic | ★ | n/a | ★ | n/a | 🚧 R11.C |
| Inline tool-use cards mid-stream | ★ progressive `input_json_delta` | ○ progressive functionCall args | ○ progressive `tool_calls.function.arguments` | ○ OpenAI-compat | depends | ✓ ToolCallCard (Apr 29) + 🚧 R11.C tightens + verifies inline stream order |
| Streaming refusals | ★ native streamed refusal | ○ | ○ | ○ | ○ | ✓ existing |
| Stop button morph + partial-turn retention | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R6.5 + 🚧 R11.C verifies persistence to DB |
| Smooth-streaming with thinking interleaved | ★ Claude 4.x interleaved thinking | ★ Gemini 2.5 Pro thinking-during-tool | — | ○ | — | 🚧 R11.C |

### A.3 Caching + cache-aware prompt layout

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Explicit prompt caching (per-block markers) | ★ `cache_control: { type: 'ephemeral' }`, up to 4 breakpoints, 5-min/1-hour TTL, 10% hit cost | ★ `cachedContent` API (separate creation step), TTL configurable, ~25% hit cost | — (automatic; no markers needed) | — (implicit) | — | 🚧 R11.D |
| Automatic prompt caching | — | — | ★ on by default, 25% hit cost reported | ★ implicit, `prompt_cache_hit_tokens` reported | n/a | 🚧 R11.D (telemetry capture) |
| Cache-aware prompt layout (tools → system → messages) | ★ Anthropic-canonical | ▶ `systemInstruction` single block (no breakpoint placement) | ▶ implicit; no explicit ordering required | ▶ implicit | depends | 🚧 R11.D |
| Cache hit-rate observability | ★ `usage.cache_creation_input_tokens` / `cache_read_input_tokens` | ★ `cachedContentTokenCount` in usage | ★ `prompt_tokens_details.cached_tokens` in usage | ★ `prompt_cache_hit_tokens` | depends | 🚧 R11.D (Observatory wiring) |

### A.4 Adaptive tool sequencing (multi-step agentic loops)

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Multi-step tool loop keyed on stop signal | ★ `while (stop_reason === 'tool_use')` canonical | ★ `while (finish_reason === 'function_calls')` | ★ `while (finish_reason === 'tool_calls')` + Responses API native loop | ○ OpenAI-compat | depends on hosted model | 🚧 R11.E |
| Interleaved text + tool in same turn | ★ Claude 4.x | ★ Gemini 2.5 | ○ Responses API | ○ | depends | 🚧 R11.E |
| Tool error recovery (model sees error, retries / pivots) | ★ native | ★ native | ★ native | ○ | ○ | 🚧 R11.E |
| Tool selection observability | ★ via thinking blocks | ★ via thinking parts | ○ via reasoning_content (when available) | ★ via `<think>` blocks | — | 🚧 R11.E |
| Iteration cap safety | ★ provider-agnostic loop logic | ★ | ★ | ★ | ★ | 🚧 R11.E (8-iteration default) |

## §5 — Cluster B: Server-Side Tools

Server-side tools are tools the provider executes inside its own infrastructure, returning results to the model in-flight. Distinct from Marsys's domain-specific tools (`query_panchanga`, `query_signals`, `query_chart_facts`, `query_dasha_periods`, etc.) which run inside our Cloud Run sidecar and are provider-agnostic via the AI SDK tool-definition mechanism.

### B.1 Web search

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Web search built-in tool | ★ `web_search` tool (`web_search_tool_result` content block) | ★ Google Search grounding via `tools: [{ google_search: {} }]` | ★ `web_search_preview` tool (Responses API) | — | — | 🚧 R11.F |
| Citations from web search | ★ `web_search_result_location` content blocks with `cited_text` + `url` + `title` | ★ `groundingMetadata.groundingChunks` (URL + title; no `cited_text`) | ★ `annotations` array with URL citations | — | — | 🚧 R11.F (unified to inline citation surface) |
| Search query refinement (model issues follow-up queries) | ★ native multi-hop | ★ native multi-hop | ○ via Responses loop | — | — | 🚧 R11.F |
| Citation tokens not billed | ★ documented | n/a | ○ partial | n/a | n/a | 🚧 R11.F (cost tracking respects this) |

### B.2 Web fetch (URL retrieval into context)

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| URL fetch built-in tool | ★ `web_fetch` first-party tool | — (must implement via function calling + own fetcher) | ○ via tool definitions + own fetcher | — | — | 🚧 R11.F (Anthropic native + polyfill for others) |

### B.3 Code execution (sandboxed Python or similar)

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Code execution built-in tool | ★ `code_execution` first-party tool (sandboxed Python, charts, file I/O) | ★ Code Execution built-in (sandboxed Python) | ★ Code Interpreter (sandboxed Python + file I/O) | — | depends on hosted model | 🚧 R11.F |
| File output rendering (charts, images) | ★ container result blocks | ★ inline | ★ via attachments | — | — | 🚧 R11.F (unified file-output rendering) |

## §6 — Cluster C: Memory + Projects + Learning Layer

### C.1 Cross-conversation memory

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Native memory feature (model remembers user across conversations) | ★ Memory tool (Claude 4.5+) | ○ via Workspace context binding | ★ Memory feature (ChatGPT-product-only; not API-native) | — | — | 🚧 R11.G |
| Unified memory store (Marsys-managed) | ★ provider-agnostic (queried as a tool by any provider) | ★ | ★ | ★ | ★ | 🚧 R11.G — primary path; ensures continuity across stacks |
| Memory recall observability (which memories were used) | depends | depends | depends | depends | depends | 🚧 R11.G — Marsys-side audit trail |
| Memory deletion / user control | depends | depends | depends | depends | depends | 🚧 R11.G — Marsys-managed UI |

### C.2 Projects + deep context

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Project-scoped conversation grouping | ★ Projects (Anthropic native) | ○ via Workspace | ★ ChatGPT Projects (product feature) | — | — | ✓ R9-S1 (Marsys-side Projects abstraction, provider-agnostic) |
| Project-scoped system prompt / persona | ★ | ○ | ★ | — | — | 🚧 R11.G (extends R9-S1) |
| Project-scoped file context (auto-injected) | ★ | ○ | ★ | — | — | 🚧 R11.G |
| Project-scoped conversation summarization | ★ | ○ | ★ | — | — | 🚧 R11.G |

### C.3 Learning Layer adaptation

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Tool-affordance learning (model gets better at tool selection over time via Learning Layer feedback) | provider-agnostic — depends on Marsys Learning Layer scaffold | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | 🚧 R11.H — depends on `06_LEARNING_LAYER/` scaffold (currently deferred per MACRO_PLAN_v2_0.md) |
| Preference learning (assistant adopts user's preferred style/tone/format over conversations) | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | 🚧 R11.H |
| Prediction-outcome feedback loop (Prospective Prediction Logging cadence) | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | 🚧 R11.H — depends on PPL scaffold (NAP.M5.0 cadence plan pending) |

## §7 — Cluster D: Multi-Modal + Artifacts + Computer Use

### D.1 Multi-modal input

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Image input | ★ vision (Claude 3.5+) | ★ native | ★ native | — | depends on hosted model | ✓ R8-S7 (vision pipeline) |
| Audio input | — | ★ native (Gemini Live + Gemini 2.5) | ★ Audio Preview models | — | — | 🚧 R11.I |
| Video input | — | ★ native (Gemini 2.5) | ○ partial (frames) | — | — | 🚧 R11.I |
| PDF input | ★ Files API + inline | ★ Files API | ★ via Files endpoint | — | — | 🚧 R11.I (currently text extraction only) |
| Multi-modal input observability | ★ usage breakdown | ★ usage breakdown | ★ usage breakdown | n/a | n/a | 🚧 R11.I |

### D.2 Multi-modal output

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Voice output (TTS streaming) | — | ★ Gemini Live (real-time TTS) | ★ Audio Preview / TTS streaming | — | — | 🚧 R11.I |
| Image generation | — | ★ Imagen via API | ★ DALL-E / gpt-image-1 | — | depends | 🚧 R11.K |

### D.3 Artifacts (live-rendered interactive content)

Provider-agnostic since rendering is client-side; provider only needs to emit artifact-marked content via system-prompt convention.

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Live-rendered HTML / React / SVG artifacts | ★ Claude.ai-native (artifact convention in system prompt) | ★ provider-agnostic | ★ provider-agnostic | ★ provider-agnostic | ★ provider-agnostic | 🚧 R11.J |
| Multi-file artifacts (project workspace) | ★ Claude.ai 4+ | ○ provider-agnostic | ○ provider-agnostic | ○ provider-agnostic | ○ provider-agnostic | 🚧 R11.J |
| Editable artifacts with version history | ★ Claude.ai | ○ provider-agnostic | ○ provider-agnostic | ○ provider-agnostic | ○ provider-agnostic | 🚧 R11.J |
| Mermaid diagrams as artifact | ★ provider-agnostic | ★ | ★ | ★ | ★ | ✓ R10 X-S11 (light version) + 🚧 R11.J full-artifact wrapper |

### D.4 Computer use / agentic browsing

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Computer Use API (screenshot + click + type) | ★ Anthropic Computer Use (Claude 3.5 Sonnet+) | — | ★ Computer Use Agent (CUA) via Responses API | — | — | 🚧 R11.K |
| Claude in Chrome / browser extension | ★ Claude in Chrome | ○ Gemini in Chrome (limited) | ★ ChatGPT extension | — | — | 🚧 R11.K — Marsys-side Chrome MCP integration |
| Long-running async agents (hours, not minutes) | ★ Claude Code agents | ○ | ★ Responses API persistent | — | — | 🚧 R11.K |

## §8 — Cross-cutting capabilities

### E.1 Cost + usage observability

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Per-request input/output token reporting | ★ | ★ | ★ | ★ | ★ | ✓ Observatory (Phase O) |
| Cache hit/miss reporting | ★ explicit | ★ explicit | ★ implicit | ★ implicit | depends | ✓ partial (anthropic_observed.ts wires `cache_creation_input_tokens` + `cache_read_input_tokens`) + 🚧 R11.D extends to all 5 |
| Reasoning-token reporting | n/a | ★ `thoughtsTokenCount` | n/a | n/a | n/a | ✓ Gemini path; n/a others |
| Per-tool cost attribution | depends | depends | depends | depends | depends | 🚧 R11.D |

### E.2 Safety + classifiers

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Server-side classifier (CBRN + CSAM + self-harm) | ★ Constitutional Classifiers (next-gen, low FP rate) | ○ implicit moderation | ○ Moderation API | minimal | minimal | ✓ default (each provider enforces its own) |
| Streaming refusal handling | ★ native | ○ | ○ | ○ | ○ | ✓ existing |
| Marsys-side validator gates (citation, panel-mode, dasha) | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | provider-agnostic | ✓ R10 Y-S8 + existing checkpoint flags |

### E.3 Structured outputs

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| JSON schema-enforced output | ○ via tool_use forcing | ○ `responseSchema` | ★ `response_format: { type: 'json_schema', strict: true }` | ○ | ○ | ✓ planner uses structured output today |
| Streaming structured output (partial JSON) | ★ `input_json_delta` for tools | ○ partial | ★ Responses API streaming JSON | ○ | ○ | partial — used in planner |

### E.4 Long context

| Capability | Anthropic | Google | OpenAI | DeepSeek | NVIDIA | Marsys ship |
|---|---|---|---|---|---|---|
| Max context window | ★ 1M tokens (Sonnet 4.6, Opus 4.7 Enterprise) | ★ 2M tokens (Gemini 2.5 Pro) | 200K (GPT-4.1) | 128K (DeepSeek V3) | depends on hosted model | ✓ existing (per-provider limits respected) |
| Server-side context compaction (auto-summarize older turns) | ★ Anthropic Compaction API | ○ implicit truncation | ○ via tools | — | — | ✓ partial — `HISTORY_COMPRESSION_ENABLED=true` is Marsys-side compaction (not provider-native); 🚧 R11.G integrates Anthropic-native where available |

## §9 — Provider capability manifests (machine-readable, declared in adapter)

Each provider adapter declares a `capabilities` object at module load. The dispatcher consults this manifest to decide:
- Which UI affordances to expose (e.g., voice button visible only if any active provider supports voice input)
- Which polyfills to engage (e.g., GPT gets a "think step by step" system-prompt nudge instead of native thinking)
- Which "switch stack" hints to surface ("This stack doesn't support audio input. Try Gemini.")

**Manifest shape** (TypeScript pseudo-type — actual implementation in `lib/providers/<provider>/manifest.ts`):

```typescript
interface ProviderCapabilities {
  // Cluster A — Foundation
  extendedThinking: 'native_effort' | 'native_budget' | 'inline_blocks' | 'polyfill_cot' | null;
  promptCaching: 'explicit_4bp' | 'cached_content_api' | 'automatic' | 'implicit' | null;
  adaptiveToolLoop: 'stop_reason' | 'finish_reason_function_calls' | 'finish_reason_tool_calls' | null;
  interleavedThinkingTool: boolean;
  smoothStreaming: boolean; // always true via Marsys server adapter
  // Cluster B — Server-side tools
  webSearch: 'first_party' | 'grounding' | 'preview_api' | null;
  webFetch: 'first_party' | null;
  codeExecution: 'first_party' | null;
  // Cluster C — Memory + Projects + Learning
  nativeMemory: 'memory_tool' | 'workspace' | 'product_only' | null;
  // Cluster D — Multi-modal + Artifacts + Computer Use
  inputImage: boolean;
  inputAudio: boolean;
  inputVideo: boolean;
  inputPdf: 'files_api' | 'inline' | null;
  outputVoice: 'live_api' | 'tts_streaming' | null;
  outputImage: 'imagen' | 'dalle' | 'gpt_image' | null;
  computerUse: 'computer_use_api' | 'cua_responses' | null;
  // Cross-cutting
  structuredOutputs: 'json_schema_strict' | 'response_schema' | 'tool_force' | null;
  maxContextTokens: number;
}
```

## §10 — Maintenance protocol

This file is **LIVING**. Updated at the close of each R11 v2 phase that ships a capability:

- The phase-close session updates the affected status cells from `🚧 R11.X` to `✓ R11.X (shipped DATE)`.
- When a new provider is added (e.g., xAI Grok, Mistral), a new column-pair is appended.
- When a new capability is discovered (Anthropic ships a new tool, Gemini adds a new modality), a new row is appended with status `🚧` for "to-evaluate" until decided.
- When the Learning Layer scaffolds (currently deferred), the §6.C.3 row triggers re-scope.

Mirror obligation (`mirror_obligations` field above): when Gemini-side review starts touching this file, declare a Gemini-side mirror partner and lift `mirror_mode` to `adapted_parity`.

---

*End of CAPABILITY_MATRIX.md v1.0.*
*Authored 2026-05-22 in Cowork session that scoped Multi-Provider Parity (R11 v2).*
*Future updates append §11 (changelog) below this line as phases close.*
