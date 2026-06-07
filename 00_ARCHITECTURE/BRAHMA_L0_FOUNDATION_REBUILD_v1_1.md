---
artifact: BRAHMA_L0_FOUNDATION_REBUILD_v1_1.md
canonical_id: L0FR_MASTER_PLAN
version: 1.1
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-07
supersedes: BRAHMA_L0_FOUNDATION_REBUILD_v1_0.md
v1.1 changes: §2 + §4 (audience tier elimination, rebuild skepticism), §6 (retrieval registry expanded), §7 (full agentic loop spec + OpenAI/ChatGPT first-class), §8 (per-stream capability registration), §11-12 (new sections), budget updated
governs: 7 streams for L0 Brahma Jñāna full implementation + unified retrieval layer
---

# Brahma L0 Foundation Rebuild — Master Plan v1.1

## §1 — Mission

Replace scaffold-grade L0 Brahma Jñāna with a production-quality dataset AND build the unified L0-L5 retrieval layer (three primitive types, four adapter implementations) so the same data serves every LLM (Claude, Gemini, OpenAI GPT, DeepSeek, NVIDIA) through both clients (platform-mcp server + internal Consume Chat portal) efficiently and at full capability.

Today: 41 hardcoded text chunks, 55 hardcoded remedies, ephemeris partial, pañcāṅga location-locked, audience_tier code residual, retrieval surface fragmented, R11.F-style bounded agentic loop only.

After this arc: ~10k verse chunks across 15 classical texts with vector search, ~5-10k sūtravali rules, 500-1000 curated remedies (10 categories incl. carefully-sourced tantric), ephemeris 1900-2150 (~822k rows), pañcāṅga on-demand service, Swiss Ephemeris as shared infrastructure, AND a unified retrieval registry with full agentic loop + bulk-context + OpenAI function-calling + hybrid adapters serving the same capability set to both MCP and Consume Chat.

## §2 — Locked architectural decisions

**Naming + structure:**
- `brahmagyan.kalapancanga` english_name corrected to "Graha Sphuṭa / Ephemeris"; volume floor 821,250 (was 29,200 — fixes day-vs-row confusion)
- `brahmagyan.panchanga_almanac` dropped from registry; pañcāṅga becomes a service
- `brahmagyan.shastra` expanded from 4 to 15 classical texts (per §3)
- `brahmagyan.sutravali` proper Gemini-Flash LLM extraction (per §5)
- `brahmagyan.upaya_kosha` extended to 500-1000 remedies across 10 categories with tantric careful-inclusion gate
- `brahmagyan.text_index` proper Vertex AI embedding pipeline (was deferred)

**Audience tier — ELIMINATED:**
- Per memory `feedback_no_audience_tier`, audience_tier (client/acharya/super_admin gating) is permanently removed.
- Stream A's kill-list audit removes every residual reference across Madhav + brahma-pipeline + platform-mcp.
- No new code branches on tier. No retrieval capability gates on tier. No MCP tool descriptor includes tier filter.
- `profiles.role` (super_admin vs guest) for operator dashboard access stays — that's not tier gating.

**Rebuild discipline:**
- Per memory `feedback_rebuild_skepticism_of_existing_code`: existing L0 code is reference for INTENT, not authoritative implementation.
- Each stream rewrites where existing code carries cruft. Reuse only after clean-architecture review.

**Infrastructure:**
- Swiss Ephemeris `.se1` files bundled in every Docker image that does astronomical compute (orchestrator + python-sidecar + pyhora-sidecar) per memory `reference_swiss_ephemeris_shared_layer`.
- Master copy at `gs://madhav-ephemeris/`.

**LLM model selection:**
- Vertex AI Gemini 2.5 Flash for bulk extraction work, Flash-Lite where margins matter (per memory `feedback_llm_model_selection`).
- Anthropic API banned for backend use.
- Claude available as MCP CLIENT (via ChatGPT-style MCP connection).
- OpenAI GPT available as both client (via OAuth-authenticated MCP) AND as backend LLM in Consume Chat.

## §3 — Classical text corpus (15 texts)

Same as v1.0 — see v1.0 §3. Tier 1 (texts 1-8) full ingestion, Tier 2 (9-11) full, Tier 3 (12-15) selective. Estimated ~13k verses → ~10k chunks.

## §4 — Remedy corpus (Upāya-kośa)

Same as v1.0 — see v1.0 §4. 10 categories, ~500-1000 remedies, tantric careful-inclusion gate (every tantric row requires source_text + source_chapter + source_verse + classical_attestation).

## §5 — Sūtravali extraction methodology

Same as v1.0 — see v1.0 §5. Three-pass Gemini 2.5 Flash pipeline, 5-criterion rubric, ≥0.8 score live + parked queue.

## §6 — Unified retrieval registry (NEW in v1.1)

Per memory `reference_retrieval_layer_architecture`. The retrieval layer is now a first-class deliverable.

### Three primitive types

| Primitive | Purpose | L0 examples |
|---|---|---|
| **Tools** | Callable functions with args; structured return | `query_planet_position(date, body)`, `search_classical_texts(query)`, `query_panchanga(chart_id, date)` |
| **Resources** | Loadable read-only context by URI | `marsys://chart/<id>/metadata`, `marsys://text/BPHS/chapter/7`, `marsys://asset-registry/all`, `marsys://ephemeris-cache/year/2026` |
| **Prompts** | Templated workflows | `marsys://prompt/analyze-7th-house`, `marsys://prompt/dasha-summary`, `marsys://prompt/whole-chart-read` |

### Single canonical registry

```
platform/src/lib/retrieval/
├── registry/
│   ├── types.ts              # Capability descriptor + llm_hints + adapter interfaces
│   ├── index.ts              # canonical export
│   ├── parity_check.ts       # CI gate ensuring MCP + Consume Chat see same set
│   ├── layers/
│   │   └── L0_brahmagyan/    # Streams B/C/D/E/F populate this
│   └── tool_catalog.ts       # for deferred-loading mode
├── adapters/
│   ├── agentic_loop/         # Claude / OpenAI GPT / DeepSeek / NVIDIA
│   ├── bulk_context/         # Gemini Pro/Flash (huge context)
│   ├── openai_function_calling/  # explicit; includes ChatGPT MCP OAuth flow
│   ├── hybrid/               # Gemini with tools
│   └── shared/
└── tests/
    └── parity.test.ts
```

### Capability descriptor

```typescript
interface Capability {
  uri: string                    // marsys://tool/L0/query_planet_position
  type: 'tool' | 'resource' | 'prompt'
  layer: 'L0'..'L5'
  asset_id: string

  name: string
  description: string            // for tool catalog; human-readable for ChatGPT UI

  args_schema?: ZodSchema        // tools only
  return_schema?: ZodSchema      // tools only
  resource_loader?: (uri) => any // resources only
  prompt_template?: PromptTemplate // prompts only
  handler?: (...) => Promise<any>

  llm_hints: {
    agentic: {
      cost_class: 'cheap' | 'medium' | 'expensive'
      typical_latency_ms: number
      composable_with: string[]   // semantic neighbors for chain composition
      retry_strategies: ('retry_with_wider_args' | 'fallback_to_alternative')[]
    }
    bulk_context: {
      pre_fetch_priority: number  // 0-100 for intent-classified pre-fetch
      bundle_with: string[]
      result_max_kb: number
      include_in_default_resources: string[]
    }
  }

  cost_estimate_usd: number
  freshness_class: 'static' | 'cached_24h' | 'live'

  expose_mcp: boolean
  expose_consume_chat: boolean
  // NO tier gating
}
```

### Both clients reach parity

Per Universal Parity Campaign discipline, both channels must register the same capability set:
- **MCP server** (`platform-mcp/src/tools/`) — exposes via MCP protocol; OAuth-authenticated for ChatGPT
- **Consume Chat portal** (`platform/src/lib/retrieval/`) — exposes via internal API routes

A `parity_check.ts` CI gate enforces this.

## §7 — Four adapter implementations (NEW in v1.1)

### 7.1 Full Agentic Loop (Claude, OpenAI GPT, DeepSeek, NVIDIA)

Replaces R11.F's bounded pattern. Every advanced capability:

| Capability | Implementation |
|---|---|
| Chain-of-thought between tool calls | Thinking blocks pass through; CoT is part of multi-iteration state |
| Deferred tooling | LLM receives tool *catalog* (names+descriptions) up front; loads schemas only when calling |
| Adaptive tooling | After each call, adapter re-plans; LLM can load/drop/compose tools mid-loop |
| Tool composition | Chains tool outputs as next tool inputs without user round-trips (parallel + sequential) |
| Reflection passes | Periodic "review accumulated context; ready to synthesize?" prompts |
| Error recovery | Tool failure → adapter offers semantic alternatives, retries with adjusted args, marks dead path |
| Cost-budget awareness | Per-call cost tracked; LLM gets remaining budget header each turn |
| No hard iteration cap | Loop runs until LLM signals "ready to synthesize" OR soft budget exceeded |

### 7.2 Bulk Context (Gemini Pro/Flash, 1M-2M token context window)

| Step | Implementation |
|---|---|
| Intent classification | Cheap classifier (regex + small LLM) tags query: career/health/marriage/spiritual/temporal/whole-chart |
| Resource pre-fetch | For tagged intent, pre-fetch all relevant resources (chart metadata, positions, dasha, top-50 text passages, top-100 sūtravali rules, related remedies) |
| Bundling + clipping | Results bundled into structured system context (200k-800k tokens); each result clipped to `result_max_kb` |
| Single-pass synthesis | Gemini receives bundle + query + can call tools for follow-up |
| Cited synthesis | Output uses `[^chunk_id]` markdown citations into bundled context |

### 7.3 OpenAI Function Calling (GPT API + ChatGPT MCP) — FIRST CLASS

Per native ratification 2026-06-07: OpenAI GPT must work fully both as MCP client (ChatGPT desktop/web) AND as backend LLM in internal Consume Chat. Two sub-paths:

**ChatGPT consuming our MCP server:**
- platform-mcp adds OAuth 2.0 authorization flow (currently API key only)
- Stream A authors the OAuth endpoints: `/mcp/oauth/authorize`, `/mcp/oauth/token`, `/mcp/oauth/refresh`
- Tool descriptions are GPT-UI friendly (action-verb-first, concise, no internal jargon)
- Resources URIs are stable and discoverable
- Smoke test: connect from ChatGPT desktop, list tools, invoke `query_planet_position`, receive correct result

**GPT models via API in Consume Chat:**
- Full Agentic Loop adapter implements OpenAI's function-calling schema with parallel tool calls, structured outputs, reasoning tokens for o1
- Supports `tool_choice='auto' | 'required' | 'none'`
- Streaming responses
- Cost tracking per model (4o vs 4.5 vs o1)
- Smoke test: query through GPT-4o end-to-end with ≥3 tool calls and final synthesis

### 7.4 Hybrid (Gemini Pro with tools)

Pre-fetches top-priority resources + exposes remaining tools. Bulk synthesis + targeted follow-ups.

## §8 — Per-stream capability registration tables (NEW in v1.1)

Each stream registers specific capabilities into the unified registry. Per-stream §4.5 in each brief.

### Stream A — Infrastructure capabilities

| URI | Type | Description |
|---|---|---|
| `marsys://tool/L0/resolve_entity` | tool | Resolve name (Sanskrit/English/synonym) → canonical_id |
| `marsys://tool/L0/list_entities` | tool | List entities by class (planet/nakshatra/sign/house) |
| `marsys://resource/asset-registry/all` | resource | Full asset registry as readable JSON |
| `marsys://resource/asset-registry/L0` | resource | L0-only registry slice |
| `marsys://prompt/intent-classify` | prompt | The intent classifier used by Bulk Context adapter |

### Stream B — Ephemeris capabilities

| URI | Type | Description |
|---|---|---|
| `marsys://tool/L0/query_planet_position` | tool | (date, body, ayanamsha) → tropical longitude + speed |
| `marsys://tool/L0/query_planet_transit` | tool | (body, start_date, end_date) → transit events |
| `marsys://tool/L0/query_aspects_at_time` | tool | (date) → all classical aspects active |
| `marsys://tool/L0/query_retrograde_periods` | tool | (body, year_range) → retrograde windows |
| `marsys://resource/ephemeris-cache/year/<yyyy>` | resource | One year's planet positions as bulk JSON |
| `marsys://resource/ephemeris-cache/native-lifetime` | resource | Native's lifetime + 35y ahead, all bodies |

### Stream C — Classical text capabilities

| URI | Type | Description |
|---|---|---|
| `marsys://tool/L0/read_classical_text` | tool | (text_id, verse_ref) → verse content sa + en |
| `marsys://tool/L0/read_chapter` | tool | (text_id, chapter) → all verses |
| `marsys://tool/L0/search_classical_texts` | tool | (query, top_k) → hybrid vector + full-text search |
| `marsys://tool/L0/list_classical_texts` | tool | Text registry with metadata |
| `marsys://tool/L0/find_verses_about` | tool | Semantic search filtered by texts |
| `marsys://resource/text/<text_id>/chapter/<n>` | resource | Full chapter as readable resource |
| `marsys://resource/text/<text_id>/index` | resource | TOC + verse index |
| `marsys://prompt/classical-canon` | prompt | Common text-retrieval workflow |

### Stream D — Sūtravali capabilities

| URI | Type | Description |
|---|---|---|
| `marsys://tool/L0/query_rules` | tool | (antecedent_pattern) → matching rules with citations |
| `marsys://tool/L0/query_rules_for_planet` | tool | (body, house=None) → planet-specific rules |
| `marsys://tool/L0/read_rule` | tool | (rule_id) → full rule + extraction audit trail |
| `marsys://tool/L0/list_rules_by_text` | tool | All rules from one text |
| `marsys://resource/sutravali/all-by-planet/<planet>` | resource | Bulk rules for one planet |
| `marsys://resource/sutravali/all-by-house/<n>` | resource | Bulk rules for one house |

### Stream E — Pañcāṅga capabilities

| URI | Type | Description |
|---|---|---|
| `marsys://tool/L0/query_panchanga` | tool | (chart_id, date) → five limbs + sunrise/sunset |
| `marsys://tool/L0/query_panchanga_range` | tool | (chart_id, start, end) → date series |
| `marsys://tool/L0/query_muhurta` | tool | (chart_id, date, type) → auspicious windows |
| `marsys://tool/L0/query_choghadiya` | tool | (chart_id, date) → day/night choghadiya |
| `marsys://tool/L0/query_hora` | tool | (chart_id, date) → planetary hours |
| `marsys://resource/panchanga/native-lifetime` | resource | Pre-cached native's full pañcāṅga history |

### Stream F — Remedy corpus capabilities

| URI | Type | Description |
|---|---|---|
| `marsys://tool/L0/query_remedies` | tool | (planet, domain, category) → matching remedies |
| `marsys://tool/L0/query_remedies_for_chart` | tool | (chart_id, affliction) → context-aware |
| `marsys://tool/L0/list_remedies_by_category` | tool | Catalog by category |
| `marsys://tool/L0/read_remedy` | tool | (remedy_id) → full remedy + source |
| `marsys://tool/L0/query_tantric_remedies` | tool | (deity, purpose) → tantric-tier only |
| `marsys://resource/remedies/by-planet/<planet>` | resource | Bulk remedies for one planet |
| `marsys://prompt/remedy-recommendation` | prompt | Standard remedy workflow |

## §9 — Stream topology (updated budgets)

```
┌────────────────────────────────────────────────────────────┐
│  STREAM A — Foundation Infrastructure (EXPANDED)            │
│  • GCS bucket + .se1 file upload + Docker bundling          │
│  • Schema migrations (corpus extensions)                    │
│  • Orchestrator --global-build mode                          │
│  • Asset registry seed correction                            │
│  • PyHora sidecar Dockerfile + ephemeris path                │
│  • >> NEW: Retrieval registry scaffolding (Capability type, │
│    parity_check, layers structure, 4 adapter implementations)│
│  • >> NEW: MCP OAuth 2.0 flow for ChatGPT support            │
│  • >> NEW: audience_tier kill-list audit (Madhav + brahma-   │
│    pipeline + platform-mcp); zero residual references       │
│  • >> NEW: First 5 L0 capabilities registered (resolve_entity│
│    + list_entities + 3 resources) as pattern validation     │
│  • OPERATOR REVIEW GATE 1                                    │
│  Budget: $500 (was $300)                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ unblocks all
        ┌────────────┼────────────┬──────────────┬────────────┐
        │            │            │              │            │
   ┌────▼─────┐ ┌────▼──────┐ ┌──▼─────────┐ ┌──▼─────────┐ ┌─▼──────────┐
   │ STREAM B │ │ STREAM C  │ │ STREAM E   │ │ STREAM F   │ │ STREAM G   │
   │Ephemeris │ │Text       │ │Pañcāṅga    │ │Remedy      │ │Pyhora      │
   │+ B caps  │ │Ingestion  │ │Service     │ │Corpus      │ │Integration │
   │Budget    │ │+ C caps   │ │+ E caps    │ │+ F caps    │ │+ tests     │
   │$150      │ │Budget $600│ │Budget $250 │ │Budget $350 │ │Budget $150 │
   └──────────┘ └─────┬─────┘ └────────────┘ └────────────┘ └────────────┘
                     │ unblocks D
                ┌────▼──────┐
                │ STREAM D  │
                │Sūtravali  │
                │+ D caps   │
                │Budget: $250│
                └───────────┘

                     ↓ all 7 streams close + Gate 3 approval

                  L0 SEALED + RETRIEVAL LAYER LIVE
```

**Total budget cap: $2,250** (was $1,700; +$550 for retrieval-layer scaffolding + per-stream capability registration + OAuth flow).

## §10 — Per-stream acceptance criteria (additions in v1.1)

Each stream's ACs add:

| Stream | New AC additions |
|---|---|
| A | Audience_tier residual = 0 references in code; Capability type system authored; parity_check.ts passes (0 capabilities initially); 4 adapter scaffolds compile; OAuth flow round-trips with a test ChatGPT instance; resolve_entity + list_entities registered and callable from both MCP + Consume Chat |
| B | All capabilities in §8 Stream B registered; each callable from both clients; Claude-mode + Gemini-mode + GPT-mode smoke tests return native's birth Sun position |
| C | All capabilities in §8 Stream C registered; vector search smoke test from each adapter mode |
| D | All capabilities in §8 Stream D registered; LLM-extracted rules surfaced through all 4 adapters |
| E | All capabilities in §8 Stream E registered; pañcāṅga compute end-to-end through all 4 adapters |
| F | All capabilities in §8 Stream F registered; tantric remedies separately query-able |
| G | PyHora integration validated; ephemeris tool returns match PyHora-internal compute |

Plus the existing v1.0 ACs.

## §11 — Cost model (updated for v1.1)

| Component | Cost |
|---|---|
| Ephemeris compute | $0.05 |
| Document AI OCR (8,000 pages) | $12 |
| Gemini Flash chunking + curation | $1.50 |
| Vertex AI embeddings | $0.63 |
| Gemini Flash sūtravali extraction | $8-15 |
| Remedy LLM curation | $0.05 |
| GCS + Cloud Run compute | $1.50 |
| **Adapter/registry authoring** (TypeScript, no LLM cost) | $0 |
| **OAuth implementation** (TypeScript) | $0 |
| **Capability registration per stream** (TypeScript) | $0 |
| **Smoke tests across 4 adapters per stream** | ~$1 LLM total |
| **Subtotal** | **~$30** |
| Dev iteration buffer (3x) | $60-90 |
| **TOTAL ONE-TIME** | **~$90-120** |

Monthly storage delta: ~$0.50-0.60/mo (unchanged from v1.0).

## §12 — Operator review gates (updated)

- **Gate 1 (post-Stream A):** validate audience_tier elimination, retrieval registry scaffolding, 4-adapter compile, OAuth flow, asset registry corrections
- **Gate 2 (mid-Stream C):** chunk quality on first 3 texts; capability registration pattern reviewed
- **Gate 3 (pre-seal):** smoke tests of all 4 adapters across all registered L0 capabilities; ChatGPT MCP connection round-trip; first global-build + per-chart-build end-to-end

## §13 — Output artifacts after seal

- 15 classical texts with ~10k chunks + embeddings
- ~5-10k live sūtravali rules
- 500-1000 remedy corpus across 10 categories
- Static ephemeris cache 1900-2150 (~822k rows)
- Pañcāṅga on-demand service
- Shared Swiss Ephemeris infrastructure
- `--global-build` orchestrator mode
- **Unified L0 retrieval registry** with ~30 capabilities
- **Four adapter implementations** serving Claude/Gemini/OpenAI GPT/DeepSeek/NVIDIA
- **ChatGPT MCP OAuth flow** live
- Zero audience_tier references
