---
artifact: MCP_BRIEF_v1_0.md
canonical_id: MCP_BRIEF
version: 1.0
status: CURRENT
authored_by: Claude (Cowork session, Sonnet)
authored_on: 2026-05-21
sealed_on: 2026-05-21
sealed_by: Conductor run 2026-05-21 (9-for-9, PR #127)
brief_path: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
parent_plan: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md (concurrent workstream — does not modify the macro arc)
related_artifacts:
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json (adds new canonical asset MCP_SERVER)
  - 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md §D.11 (Multi-Agent Collaboration — MCP extends the collaboration surface to claude.ai and Cowork)
  - 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md (the planner the MCP wraps for ask_madhav())
  - platform/src/lib/retrieve/index.ts (the 30 retrieval tools the MCP exposes a curated subset of)
  - platform/src/app/api/chat/consume/route.ts (the pipeline the MCP server invokes via a new /api/mcp/execute endpoint)
governance:
  workstream_name: MCP
  concurrent_workstream: true
  blocks_macro_progress: false
  declared_in_CLAUDE_md_section_E: pending native approval (see §11 of this brief)
  mirror_pair: none (Claude-side only; no Gemini surface)
estimated_phases: 5
estimated_total_sessions: 7–10
---

# MARSYS-JIS MCP Server — Master Brief v1.0

**Project:** MARSYS-JIS Jyotish Instrument
**Workstream:** MCP — concurrent workstream, runs alongside active M5-A
**Date:** 2026-05-21
**Status:** DRAFT — awaiting native approval to seal
**Author:** Claude (Cowork session)

---

## §1 — Context: Why This Now

The native asked: *"can we expose MARSYS-JIS to Claude (in Cowork and Claude Chat) as an MCP, so external Claude sessions can seamlessly leverage the data assets and, where it makes sense, the query pipeline and retrieval tools — to provide best-in-class astrological interpretation/prediction/synthesis?"*

Three discoveries from exploration shaped the answer:

1. **The platform already has all the moving parts.** 30 retrieval tools (`platform/src/lib/retrieve/`), a planner that emits structured `PipelinePlan` JSON (`pipeline_planner.ts` × `PLANNER_PROMPT_v2_0.md`), a pipeline driver with traced stages (`/api/chat/consume/route.ts`), a Postgres signal/asset store, 768-dim Vertex embeddings, a Python sidecar for ephemeris/panchang/muhurat, and 50+ HTTP route handlers. An MCP is not new logic — it is a new transport over existing logic.

2. **There is one critical asymmetry.** Tool execution is in-process inside the chat route. There is no current HTTP endpoint that lets an external caller say "run `chart_facts_query` with these params and give me back the result." This single fact dominates the architecture: an MCP server has to be paired with a new platform endpoint (`/api/mcp/execute` or equivalent) that wraps the orchestrator for external use. That endpoint is the single load-bearing platform change.

3. **The most underrated value isn't "Claude can answer chart questions" — it is that Claude becomes a second seat at the instrument.** Different model family, different RLHF prior, different verbal habits. With `plan_query` / `execute_plan` / `get_trace` exposed, Cowork sessions can run differential analysis (run a query, edit the plan, re-run, compare). A panel of acharyas, each in their own Claude Chat hitting the same MCP, generates inter-rater reliability data on signal interpretation as a side effect. That is research instrumentation, not chat.

The native authorised in this brainstorm pass:

- **MCP shape: Layered (Option 4).** `ask_madhav()` runs the full pipeline + a curated set of primitives + `plan_query`/`execute_plan` for research workflows. Preserves governance by default, allows surgical use.
- **Auth model: API key per principal.** Tokens bound to Firebase UID + audience_tier. Works for both Cowork (Cowork supports remote MCPs) and Claude Chat custom integrations.
- **Topology: Hosted HTTP/SSE only.** Cloud Run sidecar service. Both Cowork and Claude Chat connect remotely. No separate stdio binary to ship/maintain.
- **Versioned brief authored now, full master-plan depth.** This document.

This document is the master.

---

## §2 — Decisions Settled (via brainstorming with native, 2026-05-21)

Four product decisions were captured before drafting:

| # | Decision | Native's Call |
|---|---|---|
| D1 | MCP shape | **Layered (Option 4).** `ask_madhav()` end-to-end + curated primitives + `plan_query`/`execute_plan` + raw-asset reads. Writes (Option 5) deferred to Phase 4. |
| D2 | Authentication model | **API key per principal.** Each token binds to a Firebase UID + audience_tier. Simple to ship now; OAuth-via-Firebase deferred to Phase 5 when invited acharyas/clients onboard. |
| D3 | Deployment topology | **Hosted HTTP/SSE only.** Cloud Run sidecar service, registered as a custom integration in Claude Chat and as a remote MCP in Cowork. No local stdio binary. |
| D4 | Brief depth | **Full master-plan brief authored now**, sealed only after native review. Subsequent execution sessions get standard CLAUDECODE_BRIEF_* docs. |

Implicit further decisions consequent to D1–D4:

| # | Decision | Consequence |
|---|---|---|
| D5 | Governance carry-over | `ask_madhav()` MUST preserve B.11 floor, audience-tier stamping, validator gates, citation gates, query_trace_steps logging, PPL discipline. Primitives MAY skip B.11 but are tagged `surgical: true` in audit. |
| D6 | Single principal model | API-key auth resolves to the existing Firebase principal model (uid, audience_tier). No new principal type. Same `getServerUser()` semantics. |
| D7 | Disclosure tier preserved | Every MCP response carries an `epistemics` block (confidence band, falsifier, horizon when applicable). The Ethical Framework distinction (calibrated/probabilistic vs fortune-telling) does not erode in the MCP transport. |
| D8 | Trace ID returned to caller | Every MCP tool response includes `trace_id`. Claude (or the native) can pass that to `get_trace(trace_id)` to investigate. Existing `/api/audit/[query_id]` infrastructure supports this without change. |
| D9 | No Gemini-side surface | MCP is Claude-side only. No mirror pair (no MP.N entry). Gemini-side equivalent is a separate workstream if and when the native wants it. |

Open questions resolved in second brainstorm pass (2026-05-21, same session):

| # | Decision | Native's Call | Consequence |
|---|---|---|---|
| D10 | Conversation history in MCP calls | **No conversation history. Single-shot calls only.** | The host chat (Cowork or Claude Chat) owns the conversation thread. MCP calls carry no `conversation_id`. The platform's `conversation_messages` table is not loaded or written by MCP. Significant simplification: drops the entire conversation-loading path from `/api/mcp/execute`. Claude (the client) is responsible for any context carry-over — if it needs MARSYS to know what the prior turn said, it includes that context inline in the next `ask_madhav` `query` string. Optional `context_hint` parameter on `ask_madhav` lets Claude pass a summary of relevant prior turns as plain text, but the MCP server never persists or reads conversation state. |
| D11 | `chart_id` parameter | **No chart_id. Always Abhisek (singleton).** | Matches today's state. Tool signatures are cleaner. When multi-native lands (post-M10), MCP version bumps and `chart_id` is added then. |
| D12 | Trace transparency | **Full transparency for all callers.** | `get_trace` returns full prompts, payloads, retrieval results to everyone, regardless of tier. Aligns with the research-instrument framing — auditability is total. No tier-based redaction logic. Any API key issued is implicitly trusted with full trace access. Operational implication: do not issue API keys to parties you wouldn't trust with the contents of your prompts and signal IDs. |
| D13 | End-to-end tool name | **`ask_madhav`.** | Final. Reads naturally in Claude's reasoning. Brand-aligned. |

---

## §3 — Strategic Placement

### §3.1 — Concurrent workstream, not a macro phase

The MCP is a transport layer over existing capabilities — it builds no new astrological semantics, no new retrieval tools, no new synthesis prompts. It is exactly the kind of concurrent workstream that runs alongside the macro arc, like Phase O (Observatory), Chat V2, Phase 4C (Panchang), and Conductor. Precedent for declaring it in `CLAUDE.md §E` is established. The macro plan (M1–M10) is unchanged; no MACRO_PLAN amendment required.

### §3.2 — Layer placement in the architecture diagram

```
                    External clients
                         │
                         │   (HTTP/SSE, Bearer-authenticated)
                         ▼
                ┌────────────────────┐
                │  MCP Server        │  ← NEW (this workstream)
                │  (Cloud Run        │
                │   sidecar service) │
                └────────────────────┘
                         │
                         │   (HTTPS, in-VPC)
                         ▼
              ┌──────────────────────┐
              │ /api/mcp/execute     │  ← NEW endpoint on the platform
              │  (wraps orchestrator)│
              └──────────────────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │ Existing orchestrator path:    │
         │   planner → arbitrate →        │
         │   compose_bundle → retrieval → │
         │   synthesis → trace logging    │
         └────────────────────────────────┘
                         │
                         ▼
              [L1 / L1.5 / L2.5 / L4 assets]
                (FORENSIC, LEL, MSR, UCN, CDLM,
                 CGM, RM, ephemeris, panchang,
                 chart_facts, signal store, …)
```

The MCP server adds **transport + tool taxonomy + auth**. It does **not** re-implement any synthesis, planning, or retrieval logic. The `/api/mcp/execute` endpoint is what makes the orchestrator callable from outside the chat route.

### §3.3 — Relationship to existing concurrent workstreams

| Concurrent workstream | Interaction with MCP |
|---|---|
| Phase O (Observatory) | MCP requests are LLM calls; cost telemetry already wired via existing observatory hooks. MCP-originated calls will appear in observatory dashboards once tagged with a `source: "mcp"` field. |
| Chat V2 (R7/R8/R9/R10) | MCP is transport-layer; Chat V2 is UI-layer. Zero overlap. |
| Phase 4C (Panchang) | `query_panchanga` is one of the primitive tools the MCP exposes. Already shipped. |
| Conductor | Independent infrastructure. MCP could in principle be used by Conductor sub-agents in the future, but not in v1. |

No blocking dependencies. MCP runs strictly additive.

---

## §4 — Product Specification

### §4.1 — Tool taxonomy (the layered shape)

The MCP exposes ~18 tools in v1, grouped into five tiers. Names are illustrative; final names settle in Phase 1 implementation.

#### Tier 1 — End-to-end (default tool)

| Tool | Purpose |
|---|---|
| `ask_madhav(query, mode?, context_hint?)` | Runs the full pipeline: planner → arbitrate → compose_bundle → retrieval (parallel) → synthesis → response. Returns `{answer_markdown, citations[], trace_id, plan, predictions_logged[], epistemics}`. This is the canonical tool — preserves B.11 floor, validator gates, citation gates, audience tier (stamped from API key, not a parameter), trace logging, and PPL discipline. **Single-shot per D10** — no conversation history loaded; the host chat owns the thread. `context_hint` is an optional plain-text string Claude can use to pass a summary of relevant prior turns; it is fed to the planner as additional context but not persisted. **Singleton chart per D11** — always Abhisek's chart; no `chart_id` parameter. |

**Modes:** `auto` (planner chooses query_class), `holistic` (force B.11 holistic read), `factual` (single-tool surgical), `predictive` (forces forward-looking PPL logging), `cross_domain`, `discovery`, `remedial`, `classical_grounding`, `multi_school_triangulation`. These mirror the existing `query_class` enum on `PipelinePlan`.

#### Tier 2 — Plan inspection & explicit execution

| Tool | Purpose |
|---|---|
| `plan_query(query)` | Returns the `PipelinePlan` JSON without executing it. Lets the caller (Claude or native) inspect what would run. |
| `execute_plan(plan)` | Runs an explicit plan. Plan can be the output of `plan_query` (optionally edited). Enables differential-analysis workflows: plan → edit → execute → compare. |

#### Tier 3 — Surgical primitives (curated subset of the 30 retrieval tools)

| Tool | Underlying retrieval tool | One-line purpose |
|---|---|---|
| `query_chart_facts(category, planet?, house?, as_of_date?, limit?)` | `chart_facts_query` | 795-row parametric chart-fact lookup. |
| `query_signals(domain?, planet?, dasha_lord?, min_confidence?, forward_looking?, limit?)` | `msr_sql` | MSR signal lookup (the 499-signal corpus). |
| `query_dasha_periods(at?, range?, system?)` | `query_dasha_periods` | Dasha schedule. Surgical for "what's the dasha on date X?" |
| `query_panchanga(date, observer?)` | `query_panchanga` | Daily panchang (5 limbs, sunrise-anchored). |
| `query_ephemeris(planet, date_range)` | `query_ephemeris` | Date-indexed planetary position lookup. |
| `query_transit_event(planet, target, date_range)` | `query_transit_event` | Transit event search ("when does Saturn enter Aquarius?"). |
| `lel_query(category?, date_range?, min_significance?)` | `lel_query` | Life event log ground-truth retrieval. |
| `vector_search(text, doc_type[], top_k)` | `vector_search` | Semantic search over RAG chunks (Vertex 768-dim). |
| `get_cgm_subgraph(node_id, hops?, edge_types[]?)` | `cgm_graph_walk` | CGM topology traversal. |
| `cross_school_lookup(claim, schools[]?)` | `multi_school_signal_lookup` | Cross-school convergence on a claim. |

The other 20 retrieval tools (`pattern_register`, `resonance_register`, `cluster_atlas`, `contradiction_register`, `temporal`, `query_msr_aggregate`, `manifest_query`, `kp_query`, `saham_query`, `divisional_query`, `domain_report_query`, `remedial_codex_query`, `timeline_query`, `classical_text_search_tool`, `classical_attribution_lookup_tool`, `convergence_score_lookup`, `query_signal_state`, `query_kp_ruling_planets`, `query_varshaphala`, `cross_varga_dignity_query`) stay in-process. They are available **through `ask_madhav()`** (the planner can call any of them) but are not exposed as MCP tools in v1. Rationale: keep the v1 surface small and well-described; promote more primitives in v2 based on observed usage.

#### Tier 4 — Raw asset reads (for when Claude wants the whole document)

| Tool | Purpose |
|---|---|
| `read_asset(canonical_id, section?)` | Returns the raw markdown of a canonical artifact (MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL) by `canonical_id`, with optional section filter. Honors the audience tier (no super-admin-only sections leak to client tier). |

#### Tier 5 — Observability (read)

| Tool | Purpose |
|---|---|
| `get_trace(trace_id)` | Returns the full `query_trace_steps` payload for a previous query. Stages, inputs, outputs, latencies, tokens. |
| `list_recent_queries(limit?, since?)` | Returns recent MCP query history for the calling principal. |

**Total v1 surface:** 1 (end-to-end) + 2 (plan) + 10 (primitives) + 1 (asset read) + 2 (observability) = **16 tools** plus **2 resources** (`marsys://chart-overview`, `marsys://house-rules` — see §4.5) that Claude reads once at session attach.

### §4.2 — Response shape contract

Every MCP tool response has a common envelope:

```jsonc
{
  "ok": true,
  "trace_id": "qry_2026-05-21_a4f3e2",          // for get_trace()
  "audience_tier": "super_admin",                 // stamped by auth
  "epistemics": {                                 // disclosure-tier discipline
    "surgical": false,                            // true if a primitive was called
    "confidence_band": "high|medium|low",
    "horizon_days": 90,                           // null for non-predictive
    "falsifier": "Native does not relocate before 2026-12"
  },
  "result": { /* tool-specific payload */ },
  "citations": [ /* MSR signal IDs, asset section IDs */ ],
  "plan": { /* PipelinePlan, present for ask_madhav and execute_plan */ },
  "predictions_logged": [ /* PPL entries created during this call */ ],
  "synthesis_audit": {                            // present for ask_madhav and execute_plan
    "l25_tools_fired": ["msr_sql", "cgm_graph_walk"],   // proves B.11 floor was honored
    "l25_contribution_summary": "12 MSR signals + 7 CGM edges synthesized",
    "dominant_signals": ["SIG.MSR.234", "SIG.MSR.512", "SIG.MSR.661"],
    "domains_touched": ["career", "health", "spiritual"],
    "holistic_read_passed": true
  },
  "suggested_followups": [                        // 2-3 plausible next questions
    "How does this interact with the Saturn-Jupiter aspect in Q3?",
    "What does the LEL say about prior periods like this?"
  ],
  "warnings": []
}
```

Error envelope:

```jsonc
{
  "ok": false,
  "trace_id": "qry_...",
  "error": {
    "class": "auth|validation|planner_error|orchestrator_error|rate_limit|internal",
    "message": "...",
    "remediation": "..."
  }
}
```

The `epistemics` block is mandatory. The point: the ethical-framework distinction cannot be silently dropped by the transport.

### §4.3 — Auth model

Each principal gets a long-lived API key. Format: `mcp_<env>_<random32>`. Stored hashed in a new table:

```sql
CREATE TABLE mcp_api_keys (
  key_id text PRIMARY KEY,                -- short prefix shown to user
  key_hash text NOT NULL,                 -- bcrypt of full key
  user_uid text NOT NULL REFERENCES profiles(uid),
  audience_tier text NOT NULL,            -- 'client' | 'super_admin'
  scopes text[] NOT NULL DEFAULT '{}',    -- future: per-tool scoping
  created_at timestamptz NOT NULL DEFAULT now(),
  last_used_at timestamptz,
  revoked_at timestamptz,
  label text                              -- human label, e.g. "claude-chat-laptop"
);
```

The MCP server validates `Authorization: Bearer <key>` by:

1. Splitting prefix off, looking up by `key_id`.
2. bcrypt-comparing the rest against `key_hash`.
3. Loading the bound user/audience_tier.
4. Calling `/api/mcp/execute` with an internal service token + the resolved principal in headers.

Key issuance lives behind an admin-only UI surface at `/admin/mcp/keys` (Phase 1 ships a minimal CRUD; richer key management deferred). Keys are shown once at issuance and never again.

### §4.4 — Rate limiting & cost discipline

- Per-key rate limit: 60 RPM default, configurable per key.
- Per-key daily token budget: configurable; defaults via observatory cost policy.
- MCP calls tagged `source: "mcp"` in observatory; existing budget alerts apply.
- `ask_madhav()` calls dominate cost; primitives are cheap.

### §4.5 — MCP Resources (read once at session attach)

MCP distinguishes **tools** (called per-turn) from **resources** (read once when the client attaches). Resources let Claude orient itself without burning a tool call every session. v1 ships two:

#### §4.5.1 — Resource: `marsys://chart-overview`

A compact, well-structured summary of the singleton chart (Abhisek's). Authored once, regenerated when FORENSIC bumps. Format: structured Markdown ~600-1000 words. Contains:

- **Birth data line:** date, time, place, ayanamsha.
- **Lagna & key placements:** Lagna sign + lord; Atmakaraka; Amatyakaraka; Putrakaraka; Darakaraka.
- **Planets-by-house** compact grid.
- **Active dasha state:** current Mahadasha (with start/end), Antardasha (with start/end), Pratyantar.
- **Top 5 active L2.5 themes:** signal-domain summaries from MSR's highest-significance forward-looking entries.
- **One-paragraph synthesis:** the "elevator pitch" of this chart as a whole.

Authored by: native, with Claude assist. Stored at `platform-mcp/resources/chart-overview.md`. Versioned. Regenerated on FORENSIC bump (`drift_detector.py` flags staleness).

#### §4.5.2 — Resource: `marsys://house-rules`

A primer Claude reads to operate at acharya-grade in this corpus. Format: structured Markdown ~400-600 words. Contains:

- **School commitments:** Parashara primary, Jaimini for karakatva, KP for cuspal subtleties, Tajaka for varshaphal. Multi-school triangulation when invoked.
- **Terminology conventions:** which English terms map to which Sanskrit (we say "Atmakaraka" not "soul significator", "shadbala" not "six-fold strength" except on first use).
- **Quality bars:** no generic astrology; no "as is known classically" without source; predictions carry falsifier + horizon + confidence; cite signals by ID, not by paraphrase.
- **Disclosure tier:** probabilistic and calibrated; not fortune-telling.
- **When to defer:** what to call vs. what to ask the user. E.g., if the question is about another native, MCP cannot answer (singleton chart) — Claude should explain.
- **When to escalate:** if a contradiction surfaces between MSR signals, flag it; do not silently pick one.

Authored by: native (this is the operating manual). Stored at `platform-mcp/resources/house-rules.md`. Versioned. Updated as the discipline evolves.

These two resources together replace what would otherwise be 5-10 tool calls of orientation per session.

### §4.6 — Tool description standard

Tool descriptions are load-bearing — Claude picks tools by reading their description every turn. Generic one-liners produce poor tool selection. v1 ships every tool with a description that includes:

| Block | Length | Purpose |
|---|---|---|
| **What it does** | 1-2 sentences | Plain-language purpose. |
| **When to prefer** | 1-2 sentences | Differentiates from sibling tools ("prefer `query_chart_facts` over `ask_madhav` when the question is a single fact lookup; prefer `ask_madhav` for any question requiring synthesis"). |
| **Input shape hints** | 2-3 lines | Param semantics beyond what the JSON schema captures. |
| **Output shape preview** | 1 line | What the response envelope looks like for this tool. |
| **Inline example** | 1 example | Realistic usage with realistic params and abbreviated response. |

Target length per tool: 120-180 words. Authoring is an explicit Phase MCP-2 acceptance criterion (AC.2.5), not implicit.

### §4.7 — Suggested follow-ups affordance

Every `ask_madhav` response includes a `suggested_followups` array of 2-3 plausible next questions (per §4.2 envelope). Source: the planner already knows what tools it deprioritized and what query_classes it didn't run. The orchestrator emits these as a final step. Cheap to compute, large UX win — Claude can proactively surface them to the user, increasing user agency without requiring an extra round-trip.

---

## §5 — Engineering Architecture

### §5.1 — Two services, one repo

```
platform/                                  ← existing Next.js app
  src/app/api/mcp/
    execute/route.ts                       ← NEW: orchestrator HTTP entry
    plan/route.ts                          ← NEW: planner-only HTTP entry
    primitives/[tool]/route.ts             ← NEW: surgical tool HTTP entries
    keys/route.ts                          ← NEW: admin key CRUD (super_admin)
  src/lib/mcp/
    auth.ts                                ← NEW: API key validation
    epistemics.ts                          ← NEW: epistemics envelope builder
    primitives_registry.ts                 ← NEW: which 10 retrieval tools are surgical-exposed
  supabase/migrations/070_mcp_api_keys.sql ← NEW: API keys table

platform-mcp/                              ← NEW: separate Node service
  src/
    server.ts                              ← @modelcontextprotocol/sdk HTTP/SSE server
    tools/                                 ← MCP tool definitions (the 16 tools)
      ask_madhav.ts
      plan_query.ts
      execute_plan.ts
      query_chart_facts.ts
      ... (one file per tool)
    client.ts                              ← calls back to /api/mcp/* on platform
    types.ts                               ← shared with platform via @marsys/mcp-types
  Dockerfile
  cloudbuild.yaml                          ← Cloud Run deploy config
  README.md
```

The MCP server is a thin Node service. Logic stays on the platform. The MCP server's job: translate MCP tool calls into HTTPS calls to `/api/mcp/*`, translate responses back into MCP tool results. It is the SDK adapter; the platform is the brain.

### §5.2 — Data flow for `ask_madhav()`

```
Claude (Cowork or Claude Chat)
  │
  ▼ MCP tool call: ask_madhav({query, mode?, context_hint?})
┌──────────────────────────────────────────┐
│ platform-mcp (Cloud Run sidecar)          │
│   validates Bearer key → user, tier       │
│   POST /api/mcp/execute                   │
│     {tool: "ask_madhav", params, user, tier} │
└──────────────────────────────────────────┘
  │
  ▼ HTTPS, internal service token
┌──────────────────────────────────────────┐
│ platform /api/mcp/execute                 │
│   buildPipelinePlannerContext()           │
│   callPipelinePlanner() → step:'classify' │
│   arbitrateBudgets()                      │
│   hydrateBundle() → step:'compose_bundle' │
│   Promise.all(toolsAuthorized) →          │
│     step:'tool_name' × N                  │
│   createOrchestrator().synthesize() →     │
│     step:'synthesis'                      │
│   buildEpistemicsBlock()                  │
│   logPredictionsToPPL() if predictive     │
└──────────────────────────────────────────┘
  │
  ▼ Response: {answer, citations, trace_id, plan, predictions_logged, epistemics}
back through MCP server → Claude
```

Every step writes to `query_trace_steps` (existing behaviour, no change). `trace_id` is the existing `query_id`.

### §5.3 — Data flow for primitives (e.g. `query_chart_facts`)

```
Claude
  │
  ▼ MCP tool call: query_chart_facts({category: "shadbala", ...})
┌──────────────────────────────────────────┐
│ platform-mcp                              │
│   validates Bearer key                    │
│   POST /api/mcp/primitives/chart_facts_query │
│     {params, user, tier}                  │
└──────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────┐
│ platform /api/mcp/primitives/[tool]       │
│   getTool(toolName)                       │
│   tool.execute({queryPlan, plannerParams: params}) │
│   logToTraceSteps({source: "mcp_primitive", surgical: true}) │
└──────────────────────────────────────────┘
  │
  ▼ Response: {result, trace_id, epistemics: {surgical: true, ...}}
back to Claude
```

Surgical calls do not run the planner, do not enforce B.11, do not run synthesis. They are tagged `surgical: true` so audit can distinguish them from full-pipeline answers.

### §5.4 — Data flow for `plan_query` + `execute_plan`

`plan_query` runs only the planner stage and returns the `PipelinePlan` JSON. `execute_plan` accepts a `PipelinePlan` (optionally edited by the caller) and runs everything from arbitration onward. Validation: `execute_plan` re-validates the plan against `PipelinePlanSchema` and re-checks audience-tier-permitted tools (a `client`-tier caller can't smuggle in `super_admin`-only tools by editing the plan).

### §5.5 — Cloud Run deployment

- Service name: `amjis-mcp` (sibling to `amjis-web`).
- Region: `asia-south1` (same as platform).
- Runtime: Node 20.
- Memory: 512 MB (server is thin; logic is on platform).
- Concurrency: 80 (default).
- Min instances: 1 (avoid cold start on first MCP call).
- Egress: outbound HTTPS to `amjis-web` Cloud Run URL.
- Ingress: public HTTPS. Bearer auth at app layer.
- IAP / Cloud Armor: optional Phase 2 hardening.

### §5.6 — Internal service-to-service auth

`platform-mcp` → `platform` uses a Cloud Run service-to-service identity token (audience: `amjis-web` URL). Platform `/api/mcp/*` endpoints require:

1. Valid service identity token (proves the caller is `amjis-mcp`).
2. Internal headers carrying the resolved principal (`X-MCP-User`, `X-MCP-Audience-Tier`, `X-MCP-Key-Id`).

This makes `/api/mcp/*` reachable only from `amjis-mcp`, not from arbitrary internet clients. Defence in depth: MCP server validates the Bearer key, platform validates the service token + trusts the resolved principal.

---

## §6 — Governance Carry-Over

These rules MUST hold across the MCP transport. Each is a hard check on the brief's success.

| # | Rule | Where enforced |
|---|---|---|
| G1 | B.11 Whole-Chart-Read floor on `ask_madhav()` (≥1 L2.5 tool) | `/api/mcp/execute` reuses the existing arbitrateBudgets floor logic. Primitive calls bypass and are tagged `surgical: true`. |
| G2 | Audience tier stamping | API key → tier resolved at MCP server; passed in `X-MCP-Audience-Tier`; orchestrator stamps `plan.audience_tier`; citation/validator gates already key off it. No new code. |
| G3 | Trace logging | Every MCP call writes `query_trace_steps`. `trace_id` returned in envelope. `get_trace()` exposes the same data **with no tier-based redaction (per D12)** — full prompts, payloads, retrieval results returned to every caller. |
| G4 | PPL discipline | Predictive `ask_madhav()` calls write to the prospective-prediction log before returning. `predictions_logged[]` in the envelope makes this visible to the caller. |
| G5 | Disclosure tier | `epistemics` block is mandatory on every response. Builder lives at `src/lib/mcp/epistemics.ts`. |
| G6 | Citation discipline | `ask_madhav()` returns citations via the existing R7 footnote pipeline. Citations resolve to MSR signal IDs / asset section IDs. `read_asset` honors section-level access control. |
| G7 | No fabrication (B.10) | All numerical chart values come from `chart_facts` / `ephemeris_daily` / `panchang_daily` / FORENSIC / sidecar. MCP introduces zero new compute paths. |
| G8 | Layer purity (B.1) | MCP exposes L1 reads (primitives, `read_asset`), L1.5 reads (panchang/ephemeris), L2.5 synthesis (`ask_madhav`). It does not mix layers in a single response — the answer field is L2.5; the citations point back to L1. |
| G9 | Versioning discipline (B.8) | MCP server itself carries semver. Breaking changes bump major. `CAPABILITY_MANIFEST.json` MCP_SERVER entry tracks the live version. |
| G10 | Scope boundary (no pre-build) | MCP v1 ships against M5-A's active surface. It does not pre-build for M6+ retrieval tools that don't exist yet. |
| G11 | Mirror discipline | No Gemini-side counterpart in v1; no MP.N pair declared. If a Gemini-side MCP is later authored, it gets its own brief and mirror pair declaration. |
| G12 | Red-team obligation | Per §M cadence, every third MCP-workstream session triggers a red-team pass. MCP workstream closes its phase with a §IS.8(b) red-team check before merging. |

---

## §7 — Phasing

Five phases. Each phase = one closed-artifact session (or a short bundle) per §M cadence.

### §7.1 — Phase MCP-1: Foundation (platform endpoint + service shim)

**Scope:**
- Migration 070: `mcp_api_keys` table.
- `platform/src/lib/mcp/auth.ts` — API key validation.
- `platform/src/lib/mcp/epistemics.ts` — envelope builder.
- `platform/src/app/api/mcp/execute/route.ts` — wraps existing orchestrator with envelope.
- `platform/src/app/api/mcp/keys/route.ts` — super-admin-only CRUD.
- Admin UI page `/admin/mcp/keys` (minimal: list, create, revoke).
- Unit tests for envelope, auth, key validation (≥15 tests).

**Out of scope:** the MCP server itself (Phase 2), primitives endpoints (Phase 3).

**Acceptance criteria:**
- AC.1.1 — `curl -X POST /api/mcp/execute -H "Authorization: Bearer <test-key>" -d '{"tool":"ask_madhav","params":{"query":"What is my Atmakaraka?"}}'` returns a valid envelope with `result`, `trace_id`, `epistemics`, `citations`, **`synthesis_audit`**, **`suggested_followups`**.
- AC.1.2 — Invalid key returns `{ok: false, error: {class: "auth"}}` with HTTP 401.
- AC.1.3 — Trace row written for the call.
- AC.1.4 — Audit dashboard shows the MCP call.
- AC.1.5 — `synthesis_audit.holistic_read_passed` is `true` whenever `mode != "factual"`; `false` if B.11 floor was bypassed (and a warning is emitted).
- AC.1.6 — `suggested_followups` returned for every `ask_madhav` call; non-empty for any non-trivial query.

**Estimated:** 1 session.

### §7.2 — Phase MCP-2: MCP server (hosted HTTP/SSE) + resources + tool descriptions

**Scope:**
- `platform-mcp/` new Node service.
- `@modelcontextprotocol/sdk` HTTP/SSE server.
- `ask_madhav`, `plan_query`, `execute_plan` tools.
- **Tool descriptions authored to the §4.6 standard** (3 tools × ~150 words each = ~450 words of carefully-written prose).
- **Two MCP resources authored:** `marsys://chart-overview` (~600-1000 words) and `marsys://house-rules` (~400-600 words). Resources served via MCP resource protocol.
- Cloud Run deploy config (`amjis-mcp` service).
- Service-to-service identity token wiring.
- `client.ts` calls back to `/api/mcp/execute` and `/api/mcp/plan`.
- Smoke test from local Claude Chat custom integration setup.

**Acceptance criteria:**
- AC.2.1 — MCP server registers with Claude Chat as a custom integration.
- AC.2.2 — `ask_madhav("What is my Atmakaraka?")` from Claude Chat returns a coherent answer with citations.
- AC.2.3 — `plan_query` + `execute_plan` round-trip works.
- AC.2.4 — Service-to-service auth blocks unauthenticated `/api/mcp/*` calls.
- AC.2.5 — **All 3 tool descriptions meet §4.6 standard (≥120 words each, include all 5 blocks). Reviewed by native.**
- AC.2.6 — **Both MCP resources load on session attach in Claude Chat and Cowork. Content reviewed and authored by native (chart-overview) and native (house-rules).**
- AC.2.7 — Held-out test: Claude session given access to MCP + resources, asked 5 questions cold, answers cite house-rules conventions correctly (≥4/5).
- AC.2.8 — Cloud Run service `amjis-mcp` healthy in `asia-south1`.

**Estimated:** 2 sessions (1 engineering + 1 authoring/review for descriptions and resources).

### §7.3 — Phase MCP-3: Primitives + asset read + observability

**Scope:**
- `platform/src/app/api/mcp/primitives/[tool]/route.ts` — surgical dispatcher.
- 10 primitive tool wrappers in `platform-mcp/src/tools/`.
- `read_asset` tool (with section-level access control).
- `get_trace` + `list_recent_queries` tools (wrappers over `/api/audit/[query_id]` and a new `/api/mcp/recent` endpoint).
- Per-tool rate limits.
- Integration tests for each primitive (≥1 per tool).

**Acceptance criteria:**
- All 10 primitives callable from Claude Chat.
- `surgical: true` correctly stamped on primitive responses.
- `read_asset("MSR")` returns full MSR markdown.
- `get_trace(trace_id)` returns full step ledger.
- Rate limit returns `ok: false, error: {class: "rate_limit"}` cleanly.

**Estimated:** 2 sessions.

### §7.4 — Phase MCP-4: Writes (PPL integration) + red-team

**Scope:**
- `log_prediction`, `record_outcome`, `flag_disagreement` tools.
- PPL endpoint wiring (uses existing `06_LEARNING_LAYER/` substrate when it lands; interim path documented).
- Red-team pass on MCP workstream per §IS.8(b).
- Acceptance test suite.

**Acceptance criteria:**
- Predictions logged through MCP appear in PPL with full provenance (caller, key_id, trace_id).
- Outcome recording correctly links to prior prediction.
- `flag_disagreement` writes to `DISAGREEMENT_REGISTER`.
- Red-team report: no class-1 findings.

**Estimated:** 2 sessions (1 implementation + 1 red-team).

### §7.5 — Phase MCP-5: OAuth + onboarding

**Scope:**
- OAuth flow for Claude Chat custom integrations (replaces/augments API keys).
- Invited-user onboarding flow.
- Documentation: "How to set up MARSYS-JIS as a Claude Chat integration."
- Light Cowork remote-MCP setup guide.

**Acceptance criteria:**
- New user can OAuth via Firebase, get an MCP token automatically, register the integration in Claude Chat.
- API keys remain valid (additive, not replacement).

**Estimated:** 1–2 sessions. **Defer this phase** until phases 1–4 are running cleanly and the native explicitly wants external onboarding.

### §7.6 — Execution via Conductor (autonomous orchestration)

Phases MCP-1 through MCP-4 execute autonomously via the project's Conductor pattern (per `CONDUCTOR_PROMPT_MCP_v1_0.md`). The native runs two prompts in two Claude Code sessions:

1. **Setup** (in main `/Users/Dev/Vibe-Coding/Apps/Madhav`): paste `MCP_SETUP_PROMPT_v1_0.md`. Commits the 9 governance files to main, runs `SETUP_WORKTREE_MCP.sh`, creates the worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` on branch `feature/mcp-server`.

2. **Kickoff** (in new `MadhavMCP` worktree): paste `MCP_KICKOFF_PROMPT_v1_0.md`. Same prompt is **reusable on any halt** — re-paste in a fresh Claude Code session and the Conductor resumes from disk state.

Queue (`00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml`) — 9 sequential entries:

| Session | Type | Maps to phase | Halt mode |
|---|---|---|---|
| MCP-0-AUTHOR | Brief authoring meta-session | (governance) | sub_agent_halt only |
| MCP-1-S1 | Implementation | Phase MCP-1 | gate or sub_agent_halt |
| MCP-2-S1 | Implementation | Phase MCP-2 (engineering half) | gate or sub_agent_halt |
| MCP-2-S2 | Implementation + content authoring | Phase MCP-2 (descriptions + resources) | gate or sub_agent_halt |
| MCP-3-S1 | Implementation | Phase MCP-3 (primitives + dispatcher) | gate or sub_agent_halt |
| MCP-3-S2 | Implementation | Phase MCP-3 (read_asset + observability + rate limit) | gate or sub_agent_halt |
| MCP-4-S1 | Implementation | Phase MCP-4 (writes + PPL) | gate or sub_agent_halt |
| MCP-4-S2 | Red-team pass | Phase MCP-4 (§IS.8(b) discharge) | sub_agent_halt on class-1 findings |
| MCP-MERGE | Auto-merge to main | Workstream close | gate failure only |

**Native overrides** captured in `session_queue_MCP.yaml` + `CONDUCTOR_PROMPT_MCP §2`:
- MCP-MERGE has `requires_human_approval: false` (explicit native authorisation 2026-05-21)
- MCP-2-S2 resource drafts ship as-is; native iterates content post-merge

Phase MCP-5 (OAuth) is **not** in this Conductor queue. It runs as a separate workstream once MCP-1 through MCP-4 are live and the native wants external onboarding.

The `MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md` sibling brief also runs as a separate Conductor queue, parallelizable with MCP-3+.

---

## §8 — Risks & Open Questions

| Risk / Question | Mitigation / Resolution |
|---|---|
| **R1.** `ask_madhav()` latency may exceed Claude Chat's tool-call timeout (currently ~60s). | The chat route already has `maxDuration=120s`. We test under realistic loads; if needed, the MCP server returns a `pending` token and the caller polls `get_trace`. Streaming response over SSE is the proper fix; Phase 2 ships streaming. |
| **R2.** Primitive responses may leak `super_admin`-tier data to `client`-tier callers if audience tier isn't honored consistently. | Single principal model (D6); audience tier stamped at entry; existing citation/validator gates already key off it; integration tests assert tier-respect on every primitive. |
| **R3.** Cost: a power user can spam `ask_madhav()` and rack up LLM bills. | Per-key rate limits + per-key daily token budgets. Observatory dashboards tag MCP calls separately; budget alerts apply. |
| **R4.** Claude (the client) may misuse `plan_query` to skip the orchestrator's safety/quality discipline. | `execute_plan` re-validates plans against `PipelinePlanSchema` and re-checks audience-tier-permitted tools. Plans that omit required L2.5 tools for holistic queries are auto-augmented (B.11 floor still applies). |
| **R5.** API key leakage. | Bcrypt-hashed storage; one-time display at issuance; per-key audit log; `last_used_at` surfaced in admin UI; one-click revoke. |
| **R6.** MCP server becomes a bottleneck or single point of failure. | Min-instances ≥1; Cloud Run autoscaling; thin service so cold start is fast; client retries on 5xx. |
| **R7.** Mirror discipline: does any MCP artifact need a Gemini-side counterpart? | No (per D9). MCP_BRIEF, `mcp_api_keys` migration, `platform-mcp/` service — all Claude-side. Declared in §11 of this brief. |
| **R8.** OAuth (Phase 5) complexity may delay external user onboarding. | Acceptable. API keys carry external use until OAuth is ready. Native uses API key himself for own Cowork + Claude Chat in the interim. |
| **R9.** PPL substrate location ambiguity (deferred to Step 11 of LEARNING_LAYER scaffold per CLAUDE.md §E). | Phase MCP-4 documents the interim PPL path (LEL prediction subsection) and migrates cleanly when `06_LEARNING_LAYER/` scaffolds. |
| **OQ1.** ~~Should `ask_madhav` support multi-turn conversations natively?~~ **CLOSED → D10.** | Resolved: **No.** The host chat (Cowork or Claude Chat) owns the thread; MCP calls are single-shot. Optional `context_hint` parameter lets Claude pass a summary of relevant prior turns. No `conversation_messages` reads or writes from MCP. |
| **OQ2.** ~~Should the MCP expose a `chart_id` parameter?~~ **CLOSED → D11.** | Resolved: **No.** Always Abhisek (singleton). `chart_id` added in a future MCP version when multi-native lands. |
| **OQ3.** ~~Should `get_trace` redact sensitive prompt content for client-tier callers?~~ **CLOSED → D12.** | Resolved: **No redaction.** Full transparency for all callers. Operational implication: do not issue API keys to parties you would not trust with full prompt and signal-ID visibility. |
| **OQ4.** ~~Naming for the end-to-end tool?~~ **CLOSED → D13.** | Resolved: **`ask_madhav`.** |

---

## §9 — Acceptance Criteria (workstream-level)

Workstream is considered shipped when:

- AC.1 — All 16 tools callable from a freshly-set-up Claude Chat custom integration, end-to-end, returning valid envelopes.
- AC.2 — All 16 tools callable from Cowork as a remote MCP, end-to-end.
- AC.3 — `ask_madhav` produces answers indistinguishable in quality from the web `/consume` chat for a held-out test set of 20 queries spanning all `query_class` enums (rated by native).
- AC.4 — Observatory dashboards show MCP traffic, cost, latency, error rate, segmented by `source: "mcp"`.
- AC.5 — Audit dashboard exposes MCP traces with full payload drill-down (super-admin tier).
- AC.6 — Red-team pass (§IS.8(b)) returns no class-1 findings.
- AC.7 — Documentation: README in `platform-mcp/` covers setup, auth, all 16 tools, response envelope, error classes, rate limits.
- AC.8 — At least one external user (or simulated external session) successfully uses the integration through OAuth (Phase 5; deferred AC).

---

## §10 — Scope Boundary

### §10.1 — `may_touch` (Phase MCP-1; later phases will extend this)

```
platform/src/app/api/mcp/                                # CREATE — new directory
platform/src/lib/mcp/                                    # CREATE — new directory
platform/supabase/migrations/070_mcp_api_keys.sql        # CREATE
platform/src/app/admin/mcp/                              # CREATE — admin UI
platform/src/components/admin/mcp/                       # CREATE — admin components
platform/src/lib/__tests__/mcp/                          # CREATE — tests
platform-mcp/                                            # CREATE — new Node service (Phase 2)
platform-mcp/resources/chart-overview.md                 # CREATE — Phase 2 resource (native-authored)
platform-mcp/resources/house-rules.md                    # CREATE — Phase 2 resource (native-authored)
platform-mcp/src/tools/                                  # CREATE — Phase 2 tool definitions with §4.6 descriptions
00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md                 # this file, status flip on seal
00_ARCHITECTURE/BRIEFS/MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md  # CREATE — sibling brief (this session)
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_v1_0.md    # CREATE — Phase 1 execution brief
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                 # APPEND — MCP_SERVER asset entry (Phase 2)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                    # UPDATE — declare workstream
CLAUDE.md                                                 # UPDATE §E — concurrent workstreams list
```

### §10.2 — `must_not_touch` (every phase)

```
01_FACTS_LAYER/                                          # L1 facts are sealed; MCP is read-only against them
025_HOLISTIC_SYNTHESIS/                                  # L2.5 corpus is sealed
06_LEARNING_LAYER/                                       # PPL substrate is owned by M-arc, not MCP
platform/src/lib/retrieve/                               # MCP wraps these tools but does not modify them
platform/src/lib/pipeline/                               # MCP calls the planner but does not modify it
platform/src/app/api/chat/consume/route.ts               # MCP adds a sibling route; does not modify this one
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                   # planner prompt is sealed; MCP wraps, not edits
00_ARCHITECTURE/MACRO_PLAN_v2_0.md                       # MCP is concurrent, not a macro phase
00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md              # SUPERSEDED; do not touch
```

---

## §11 — Proposed Updates to Governance Surfaces (for native review)

These changes are **NOT** applied in this brief. They land at brief-seal (status flip from DRAFT → CURRENT) plus Phase MCP-1 session-open.

### §11.1 — `CLAUDE.md §E` — add tenth concurrent workstream

Proposed row to insert after the Conductor entry:

> - **MCP — MARSYS-JIS Model Context Protocol Server** — canonical_id `MCP_BRIEF_v1_0`, path `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md`. **STATUS: PHASE_MCP_1_PENDING.** Workstream declared 2026-05-21 under the Phase O / Chat V2 / Phase 4C / Conductor concurrent-workstream precedent. Scope: hosted HTTP/SSE MCP server (Cloud Run sidecar `amjis-mcp`) exposing 16 tools (1 end-to-end `ask_madhav`, 2 plan-introspection, 10 surgical primitives, 1 raw-asset read, 2 observability) to Claude Chat custom integrations and Cowork remote MCPs. API key auth bound to Firebase UID + audience_tier. Layered shape preserves B.11 floor, validator gates, citation gates, audience-tier stamping, trace logging, and PPL discipline by default through `ask_madhav()`. Primitives tagged `surgical: true` in audit. Worktree TBD. Five phases (MCP-1 foundation → MCP-5 OAuth) per §7 of the brief. Concurrent with M5-A.

Header sentence updates: **"Nine workstreams"** → **"Ten workstreams"**.

### §11.2 — `CAPABILITY_MANIFEST.json` — add MCP_SERVER asset entry (lands Phase 2)

Skeleton:

```json
{
  "canonical_id": "MCP_SERVER",
  "kind": "service",
  "path": "platform-mcp/",
  "deployed_at": "https://amjis-mcp-<hash>-uc.a.run.app",
  "version": "1.0.0",
  "status": "CURRENT",
  "exposes": {
    "tools": ["ask_madhav", "plan_query", "execute_plan", "query_chart_facts", "query_signals", "query_dasha_periods", "query_panchanga", "query_ephemeris", "query_transit_event", "lel_query", "vector_search", "get_cgm_subgraph", "cross_school_lookup", "read_asset", "get_trace", "list_recent_queries"],
    "transport": "http+sse",
    "auth": "bearer_api_key"
  },
  "depends_on": ["FORENSIC", "LEL", "MSR", "UCN", "CDLM", "CGM", "RM", "PANCHANG_DAILY", "EPHEMERIS_DAILY"],
  "mirror_pair": null
}
```

### §11.3 — `CURRENT_STATE_v1_0.md` — concurrent workstreams block

Add MCP to the concurrent-workstreams enumeration with status `PHASE_MCP_1_PENDING`.

### §11.4 — No mirror pair declared

Per D9 / G11, no `MP.N` entry in `CANONICAL_ARTIFACTS_v1_0.md §2` is added. If a Gemini-side MCP later ships, it gets its own brief and declares its own mirror pair.

---

## §12 — Cadence & Sealing

Per CLAUDE.md §M: daily sessions, closed-artifact-per-session, red-team passes per §IS.8 cadence.

**Sealing protocol for this brief:**

1. Native reviews this DRAFT.
2. Native marks accepted / rejected / requests revisions.
3. On acceptance:
   - Status flips DRAFT → CURRENT in this file's frontmatter.
   - `sealed_on` + `sealed_by` populated.
   - `CLAUDE.md §E` updated with the row in §11.1.
   - `CURRENT_STATE_v1_0.md` updated.
   - `CLAUDECODE_BRIEF_MCP_1_v1_0.md` authored to drive Phase MCP-1 execution.

**Workstream close (post-Phase MCP-5):**

- `MCP_CLOSE_v1_0.md` sealing artifact authored.
- This brief moves SUPERSEDED-AS-COMPLETE.
- `CAPABILITY_MANIFEST.json` MCP_SERVER entry kept LIVE.
- `CLAUDE.md §E` row updated to STATUS: COMPLETE.

---

*End of MCP_BRIEF_v1_0.md (DRAFT 2026-05-21). Decisions D1–D4 captured from native brainstorm 2026-05-21; D5–D9 are consequent decisions inferred from those calls and listed for explicit native review.*
