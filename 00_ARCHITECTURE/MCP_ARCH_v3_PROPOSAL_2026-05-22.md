---
artifact: MCP_ARCH_v3_PROPOSAL_2026-05-22.md
status: DRAFT
version: 3.1
authored_by: Claude (Cowork session, Opus 4.7) — regeneration of Sonnet 4.7's v3.0 draft per native's review-package mandate
authored_on: 2026-05-22
supersedes_in_place:
  - MCP_ARCH_v3_PROPOSAL_2026-05-22.md (Sonnet 4.7, v3.0 — same filename; this is a substantive regeneration, not a polish pass)
prior_supersessions:
  - MCP_ARCH_v2_PROPOSAL_2026-05-22.md (which superseded the v1 shipped under MCP_BRIEF_v1_0.md)
parent_brief: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
sibling_artifact: 00_ARCHITECTURE/MCP_PERF_SYSTEM_BRIEF_2026-05-22.md
companion_handoff: 00_ARCHITECTURE/MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md
audience: native (Abhisek Mohanty); secondary acharya readership at v3.1 close
disposition: architectural proposal for full v3.1 rebuild of the MARSYS-JIS MCP; orthogonal to (does not modify) the web /consume chat
design_rubric:
  primary_user: native + invited acharyas + external clients (multi-tier, all three real)
  quality_north_stars:
    - cross_domain_depth
    - calibrated_epistemics
    - classical_grounding
  explicitly_not_in_rubric: conversational_warmth
  latency_profile: depth_always — no sub-30s target; streaming used to give the host progressive feedback while bundles compose
  token_economy: lifted as a constraint — defaults raised; no server-side bundle truncation; depth, not parsimony
  data_layer: open to rebuild — backfill prioritized by rubric (classical grounding before depth)
  guiding_principle: "The sole north star is the quality of output the user sees. Anything contradicting that can be done away with."
version_bump_rationale: |
  v3.0 → v3.1, not v4.0. The architectural spine (pure MCP, multi-tier, depth-always)
  is preserved from Sonnet's draft. The regeneration substantively changes (a) the
  governance closure — operator-side nightly audit replaces self-audit; (b) the tool
  surface — drops `validate_response`, adds explicit audit-replay and a tier-conditioned
  `chart-snapshot` resource; (c) the bundle semantics — bundles become opt-in
  orchestration aids rather than exhaustive defaults; (d) the backfill ordering —
  classical-grounding before depth, per the rubric's stated priorities; (e) §12 is
  baked into the prose, not appended; (f) adds SSE streaming for bundles, an explicit
  security-threat-model section, and a more granular migration plan. Substantive enough
  to warrant a version bump; the spine is still recognizably v3.
---

# MCP v3.1 — Pure-MCP Architecture for MARSYS-JIS

The MARSYS-JIS MCP server is being redesigned from first principles. v1 shipped a server-side pipeline (planner LLM → tools → synthesis LLM) that exposed `ask_madhav` as its flagship tool. Empirical diagnosis (`MCP_DIAGNOSIS_2026-05-22.md`) showed why that design fails the rubric: it pins synthesis to a single server-side model, it operates right at the Claude Chat ~60-second timeout boundary on the easiest possible query, and the host model — the most capable orchestrator in the loop — is reduced to printing the platform's prefabricated paragraph. v2 (`MCP_ARCH_v2_PROPOSAL_2026-05-22.md`) corrected the synthesis half. v3.0 (Sonnet, same filename as this document, now superseded in place) corrected the planner half. This document is v3.1: a regeneration of v3.0 by Claude Opus 4.7 per the native's review-package mandate, sharpening four architectural choices Sonnet under-resolved and baking the depth-over-tokens directive into the prose rather than appending it.

The architectural commitment is uncompromising: **zero server-side LLM calls on the MCP path**. The platform becomes a retrieval-and-governance surface that delivers the deepest accurate context the host can usefully consume. The host (Claude) reads five resources at session attach to orient itself, orchestrates tool calls directly using its full conversational context, and synthesizes acharya-grade answers without an intermediary speaking for it. The web `/consume` chat remains untouched as a separate surface; v3.1 is the MCP-only architecture.

---

## §0 — TL;DR

v3.1 ships **21 tools across 6 categories**, **5 resources auto-loaded at session attach**, and an **operator-side audit subsystem** that replaces v3.0's self-audit. Every read tool returns a uniform envelope in which `provenance.signal_ids_available[]` is a *strict cite-allowlist* the host is contractually bound to honor; a nightly audit job verifies compliance against recorded traces and surfaces violations to the operator dashboard. Composite bundles (`holistic_bundle`, `multi_school_bundle`) exist as **opt-in orchestration aids** — house-rules instructs the disciplined host to compose its own parallel calls when intent is clear and to fall back to bundles when intent is diffuse. Three audience tiers (`super_admin`, `acharya`, `client`) are enforced server-side but filter only *instrument-meta* data at the retrieval layer (red-team findings, disagreement-register signals, internal audit notes); chart data is uniform across tiers, with presentation differences handled entirely by tier-conditioned `house-rules`. Streaming Server-Sent Events deliver progressive bundle results to the host, removing the "blindfolded wait" UX of long retrieval calls without changing the depth-always latency budget. Data backfill is sequenced **classical-grounding first** (multi-school tables + classical-text corpora — items that unlock a rubric *capability*), then depth (shadbala / ashtakavarga / KP / Tajaka — items that improve a rubric *quality*). The §12 depth-over-tokens directive is baked into every default, every tool description, and every bundle composition rule in this document.

What v3.1 makes possible: the host orchestrates with full visibility, cites only from a bound provenance set, attaches calibrated epistemics to every prediction, surfaces multi-school convergence/divergence honestly, and consumes a perf system that tells it which tools are healthy and which data is sparse before the user opens their mouth. What v3.1 deletes: server-side synthesis, server-side planning, double-LLM antipattern, `marsys_methodology_block` postlude bloat, ~60-second timeout ceilings on easy queries, the planner middle-manager, and the audit theater of asking the host to grade its own response.

---

## §1 — Design rubric (the spine all choices defend)

Four native decisions, recorded in `MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md §5`, fix the optimization target. Every architectural choice in this document is justified against them; choices contradicting any of them are dropped.

**Primary user — multi-tier (`super_admin` + `acharya` + `client`).** All three are real audiences. Tier is load-bearing: it drives retrieval-layer filtering (narrowly: only instrument-meta is filtered) and it drives the output template the host follows (broadly: presentation discipline lives in tier-conditioned `house-rules`). The separation matters and is enforced throughout §6.

**Quality north stars — cross-domain depth, calibrated epistemics, classical grounding.** These three dimensions are multi-selected and equal-weight. Cross-domain depth means the host fans out across MSR + UCN + CGM + CDLM + RM + multi-school + classical-text + LEL + panchang + ephemeris on holistic questions and surfaces linkages no single-domain look would catch. Calibrated epistemics means every non-trivial claim carries a confidence band, every forward-looking claim carries a horizon and a falsifier, every contradiction is surfaced honestly. Classical grounding means convergent claims are cited to the school(s) producing them with chapter-and-verse pointers, and divergent claims are flagged as divergent — not paved over. These three dimensions drive both the tool surface (Tier 1 primitives for depth; Tier 2 bundles for fan-out discipline; explicit `cross_school_lookup` + `read_classical_text` for classical grounding) and the response-envelope shape (provenance, multi-school convergence hints, layer tags, freshness flags).

**Explicitly not in the rubric — conversational warmth.** This non-selection matters as much as the selections. v3.1 leans formal/acharya-grade, not guru-style. The output template (in `house-rules`) is calibrated toward research-instrument rigor — every claim cited, every prediction falsifiable, every contradiction surfaced. A future client-tier surface could layer warmth on top via tier-conditioned `house-rules` without touching the architecture; the architecture itself is built for the rigorous case.

**Latency profile — depth always.** No sub-X-second target. The host (and the user behind it) accepts 30s+ for holistic queries when that's what depth requires. Streaming (§8) prevents the depth-always commitment from becoming a UX failure by giving the host progressive feedback during long fan-outs. Token economy is lifted as a constraint throughout (§5, §9 defaults, §12 migration); the platform delivers the deepest viable context and the host's 200k context window does the pruning.

The fifth implicit decision, repeated everywhere in the review package: **data assets, retrieval tools, and infrastructure are open to rebuild.** Sparse categories are backfilled. Tools are rewritten where they constrain output quality. Resources are added where the host needs orientation. v3.1 takes that latitude.

---

## §2 — Mental model: pure MCP

```
                    External clients
                    (Claude Chat / Cowork / invited acharyas / future external clients)
                              │
                              │  (host model orchestrates: reads resources, picks tools, composes answer)
                              ▼
                ┌──────────────────────────────────────────────┐
                │  MCP server (amjis-mcp, Cloud Run sidecar)    │
                │  — Bearer + URL-key auth, principal stamping  │
                │  — Tool/resource registration                 │
                │  — StreamableHTTPServerTransport (SSE-capable)│
                │  — Per-tier rate limiting                     │
                │  — In-memory key-validation cache (60s TTL)   │
                └──────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────────────────────┐
        │  Platform (amjis-web, Cloud Run primary)                    │
        │                                                             │
        │  /api/mcp/primitives/{tool}      — surgical retrievals      │
        │  /api/mcp/bundles/{name}         — opt-in fan-out bundles   │
        │  /api/mcp/asset                  — raw markdown reads       │
        │  /api/mcp/health/*               — tool + coverage health   │
        │  /api/mcp/trace, /recent         — observability            │
        │  /api/mcp/writes/*               — PPL, outcomes, flags     │
        │  /api/mcp/audit/replay           — audit-side, operator     │
        │                                                             │
        │  ✗  No server-side LLM (no planner; no synthesis)           │
        │  ✓  Aggressive parallel retrieval (no token budgeting)       │
        │  ✓  Tier-aware retrieval filtering (instrument-meta only)   │
        │  ✓  Streaming response support (SSE)                        │
        │  ✓  Strict-allowlist provenance in every envelope           │
        │  ✓  Trace + retrieval-log writes                            │
        └────────────────────────────────────────────────────────────┘
                              │
                              ▼
            [L1 / L1.5 / L2.5 / L3 / L4 data assets]
            (FORENSIC, LEL, MSR, UCN, CDLM, CGM, RM, panchang_daily,
             ephemeris_daily, chart_facts, signal store, rag_chunks,
             multi_school_*, classical_texts, mcp_predictions,
             tool_execution_log, mcp_audit_findings)
```

Three architectural commitments anchor v3.1:

**No LLMs on the server.** The MCP path runs zero server-side inference. The `/consume` web chat retains its server-side synthesis on a separate route; v3.1 does not touch it. This is the single most important commitment — every subsequent design decision is downstream of it. The 60-second timeout disappears, the double-LLM antipattern disappears, the cost per call drops by ~30x, and the synthesis LLM (which was the bottleneck) is replaced by the host's own model — which has both the conversation context and the most capable reasoning available.

**No planner.** Tool selection is the host's responsibility. The host has full conversation context, has read the chart's snapshot and overview at session attach, has read `marsys://capabilities` (so it knows which tools are healthy and which data is sparse), and has read `marsys://house-rules` (so it knows the operating discipline). It is better-positioned than any planner LLM to decide what to call. v3.0 retained `holistic_bundle` and `multi_school_bundle` as deterministic parallel macros; v3.1 keeps both but re-frames them — see §3 Tier 2.

**No `ask_madhav` wrapper.** There is no entry-point tool in v3.1. The conversation IS the entry point. The user types a question; the host reads the question against the orientation it loaded at session attach; the host issues tool calls; the host composes the response. The MCP server provides; the host decides.

---

## §3 — Tool surface

v1 shipped 19 tools across 4 tiers. v3.0 proposed 22 tools across 7 tiers. v3.1 ships **21 tools across 6 categories**. The composition deltas are deliberate:

| Category | v1 | v3.0 | v3.1 | Delta vs v3.0 |
|---|---|---|---|---|
| Surgical primitives | 10 | 10 | 10 | (none; same set, all bugs fixed) |
| Composite bundles | 0 | 2 | 2 | (kept, semantics changed — opt-in aids) |
| Raw asset reads | 1 | 2 | 2 | (`read_classical_text` retained) |
| Observability | 2 | 2 | 2 | (none) |
| Performance / coverage | 0 | 2 | 2 | (none) |
| Writes | 3 | 4 | 3 | (kept `score_self_response`, dropped `validate_response`) |
| Validation (self-audit) | 0 | 1 | 0 | (DROPPED — replaced by operator-side audit; see perf brief §5) |
| **Total** | **19** | **22** | **21** | **−1** |

Every tool is justified against the rubric. Every tool's description (the prose the MCP transport delivers to the host) is co-authored with this document; the lying-category problem from v1 (`MCP_DIAGNOSIS §3.1` — `dignity`/`nakshatra`/`house_placement`/`divisional_D9` advertised but not in the enum) is permanently fixed by deriving descriptions from a single source of truth — the enum itself — at registration time.

### §3.1 — Tier 1 — Surgical primitives (10)

These are the workhorses. Each wraps a retrieval tool and returns structured rows with provenance. v3.1 keeps v1's set of 10 because each one is a load-bearing capability against an L1/L1.5/L2.5/L4 data asset; no single one can be deleted without losing a retrieval surface the host needs. Code-level fixes from `MCP_DIAGNOSIS_2026-05-22.md §7` are mandatory inputs (see §10 of this document).

| MCP tool | Underlying retrieval module | What it returns | Code path |
|---|---|---|---|
| `query_chart_facts` | `chart_facts_query` | Structured L1 chart facts (planets, houses, strength, dasha schedules, panchang at birth, etc.) | `platform/src/lib/retrieve/chart_facts_query.ts` |
| `query_signals` | `msr_sql` | MSR L2.5 signal rows with significance + confidence | `platform/src/lib/retrieve/msr_sql.ts` |
| `query_dasha_periods` | `query_dasha_periods` | Dasha schedule windows (Vimshottari, Chara, Yogini, others) | `platform/src/lib/retrieve/query_dasha_periods.ts` |
| `query_panchanga` | `query_panchanga` | Daily panchang (5 limbs + full enrichment: yogas, choghadiya, hora, inauspicious/auspicious windows) | `platform/src/lib/retrieve/query_panchanga.ts` |
| `query_ephemeris` | `query_ephemeris` | Planetary positions over a date range, per planet, full daily granularity | `platform/src/lib/retrieve/query_ephemeris.ts` |
| `query_transit_event` | `query_transit_event` | Transit-event search (sign change, retrograde, station, conjunctions, eclipses) | `platform/src/lib/retrieve/query_transit_event.ts` |
| `lel_query` | `lel_query` | Life Event Log rows (36 events + 5 period summaries + 6 chronic patterns + chart_states) | `platform/src/lib/retrieve/lel_query.ts` |
| `vector_search` | `vector_search` | RAG semantic search over `rag_chunks` (Vertex 768-dim) | `platform/src/lib/retrieve/vector_search.ts` |
| `get_cgm_subgraph` | `cgm_graph_walk` | Causal-Graph-of-Manifestation topology traversal | `platform/src/lib/retrieve/cgm_graph_walk.ts` |
| `cross_school_lookup` | `multi_school_signal_lookup` | Per-school stance on a claim (Parashara / Jaimini / KP / Tajaka) | `platform/src/lib/retrieve/multi_school_signal_lookup.ts` |

Two universal rules apply to every Tier 1 tool in v3.1, both of which are mandatory code changes (see §10):

**Rule 1 — `params` is the source of truth, not `plan`.** The diagnosis (`§3.2`) caught the surgical-primitives dispatcher (`platform/src/app/api/mcp/primitives/[tool]/route.ts:148–161`) building a placeholder `queryPlan` whose `query_text` field is `"surgical_primitive:<tool_name>"` and passing it alongside the user's actual `toolParams`. `vector_search.ts:236` reads `plan.query_text` and silently discards `params.text`; `msr_sql.ts` does the same for `domain`, `limit`, `karakas`. v3.1 requires every Tier 1 tool to accept its filter inputs from `params` first and fall back to `plan` only when called from the legacy `/consume` pipeline. The smuggling pattern is a footgun that produces "the tool returned junk but you can't tell" — the most insidious failure mode in a retrieval system.

**Rule 2 — Depth-first defaults.** Per the §12 directive baked through this document, every primitive's default `limit` is "enough to give the host depth," not "enough to fit a budget." v3.1 defaults:

| Tool | Default limit | Max limit | Rationale |
|---|---|---|---|
| `query_signals` | **100** (raised from 50) | **500** (unchanged) | MSR has 514 signals; one query may legitimately want the whole high-significance head |
| `query_chart_facts` | **100** (raised from 50) | **500** (raised from 200) | When backfilled, `shadbala` alone has 63 rows; depth queries want more |
| `lel_query` | **no cap** (was 50) | n/a | Only 36 events exist; the cap was theatrical |
| `query_dasha_periods` | **no cap** (was 100) | n/a | Vimshottari has 9 maha + ~120 antar across a lifetime; full schedule is small |
| `query_panchanga` | date-range driven | n/a | Returns one row per day with full enrichment; no row-count cap |
| `query_ephemeris` | date-range driven | n/a | One row per planet per day; full granularity |
| `query_transit_event` | **200** (raised from 50) | **1000** (raised from 200) | Transit events over a 10-year window can run into hundreds; depth queries want them |
| `vector_search` | **25** (raised from 10) | **100** (raised from 50) | Sub-25 results miss the long tail of RAG; the host can re-rank |
| `get_cgm_subgraph` | hops=2 default; max hops=4 | no node cap | CGM has ~500 nodes / ~1200 edges; a 4-hop walk can return half the graph and that's fine |
| `cross_school_lookup` | **all schools' full positions** | n/a | Truncating a multi-school view defeats the point |

Tool descriptions emitted to the host explicitly communicate this: "Returns up to 100 rows by default; pass `limit` to cap further if your context budget is constrained — otherwise the tool returns full depth."

**Rule 3 — Honest enum-derived descriptions.** Tool descriptions at MCP registration time are generated from a single source: the enum in `chart_facts_query.ts:21–30` for `query_chart_facts`, the MSR domain registry for `query_signals`, etc. There is no hand-authored description listing fake categories. The `query_chart_facts` description in `platform-mcp/src/tools/query_chart_facts.ts:19,54` is generated at build time and includes both the real categories AND the *current coverage state* per category — so the host reads "as of 2026-05-22, categories `shadbala`, `ashtakavarga_*`, `kp_*`, `upagraha`, `mrityu_bhaga`, `longevity_indicator`, `avastha`, `varshphal` currently return zero rows; prefer `query_signals` for strength questions until v3.2 backfill lands." This is honest plumbing, derived from the data-coverage view; see the perf brief §6.2 for how this is composed.

### §3.2 — Tier 2 — Composite bundles (2) — opt-in orchestration aids

This is the design choice where v3.1 most clearly departs from v3.0. Sonnet positioned bundles as exhaustive-default deterministic fan-outs. v3.1 keeps both bundles but **re-frames them as opt-in orchestration aids** per the native's 2026-05-22 decision: house-rules tells the host to prefer composing its own parallel calls when intent is clear, and to fall back to a bundle when intent is diffuse or when the host wants a single-call B.11 floor satisfier.

The framing matters. A disciplined acharya-grade orchestrator with full conversation context, having read the chart-snapshot and capabilities resources, knows whether the user's question is about Saturn's strength specifically (call `query_chart_facts(strength)` + `query_signals(planet:"Saturn")` directly) or about a vague life theme that needs depth across many domains (call `holistic_bundle`). Forcing a bundle on the first case wastes context window and dilutes the host's reasoning by surfacing irrelevant cross-domain noise. Forcing the host to write five tool calls for the second case (when the host's read of the question is "I need a wide net") slows the conversation and risks the host under-fanning-out. Bundles serve the diffuse case; primitives serve the targeted case; house-rules states the preference rule.

| Tool | Composition (parallel fan-out) | When house-rules says to use it |
|---|---|---|
| `holistic_bundle(query_text, focus_domains?[], time_window?, subset?)` | MSR (`query_signals` filtered by `focus_domains` if provided, else top 100 by significance) + CGM (`get_cgm_subgraph` hops=3 around relevant nodes) + UCN excerpts via `vector_search` filtered to `source_canonical_id=UCN_v4_1` + RM (`vector_search` filtered to `RM_v2_2`) + CDLM convergence via `vector_search` filtered to `CDLM_v1_3` + `lel_query` filtered by `time_window` + current panchang via `query_panchanga(today)` + current dasha state via `query_dasha_periods(active_only:true)` | The user's question spans multiple life domains, requires cross-signal synthesis, or is "give me the deep read on X." The host is not certain which 6 tools to fire. Falls back to the bundle to guarantee B.11 floor. |
| `multi_school_bundle(claim, schools?[])` | `cross_school_lookup(claim)` + per-school targeted queries (Parashara MSR signals matching the claim's keywords; Jaimini karaka rows from `query_chart_facts(category:"strength_extra")` filtered to jaimini; KP cuspal rows from `query_chart_facts(category:"kp_cusp")` when backfilled; Tajaka muntha / saham rows from `query_chart_facts(category:"varshphal")` when backfilled) + `read_classical_text(work, chapter)` for the most-cited classical reference in each school's stance | The user asks for triangulation across schools, calibration of a single claim against tradition, or "do the texts agree on this." The host wants per-school evidence in one envelope. |

Both bundles fire all sub-tools in parallel (Promise.all with per-tool timeouts and per-tool error isolation — a failure in one sub-tool does not fail the bundle). Both return a single envelope whose `result.bundle_entries[]` is an array of per-sub-tool result blocks, each carrying its own `provenance.signal_ids_available[]`. The host receives the union of all available signal IDs as the response envelope's top-level `provenance.signal_ids_available[]` — which becomes the strict cite-allowlist for the host's answer (§5).

**`subset` parameter (optional, both bundles).** Lets the host narrow the composition: `holistic_bundle({query_text:"...", subset:["MSR","CGM","UCN"]})` fires only those three sub-tools. Useful when the host wants a bundle's *envelope shape* (consolidated cite-allowlist, per-sub-tool provenance) but doesn't want the full fan-out. Default is exhaustive.

**`time_window` parameter (`holistic_bundle` only).** When provided as `["YYYY-MM-DD","YYYY-MM-DD"]`, narrows `lel_query` to events in that window and narrows the panchang/ephemeris fetches to anchors in/near it. Useful for predictive queries ("what's happening in the next 18 months").

**`holistic_bundle` does NOT include a planner-style LLM.** It does not interpret `query_text` to choose sub-tools; it interprets it only as a string passed verbatim to `vector_search` and `query_signals` filtering. Sub-tool composition is rule-based and parallel-deterministic. The "deterministic, no LLM" property is preserved from v3.0; what v3.1 changes is the *guidance about when to use it*, not the implementation.

**No bundle is mandatory.** There is no path in v3.1 that forces the host to call `holistic_bundle` before answering. The B.11 floor is enforced via two paths: house-rules instructs the host to consult ≥1 L2.5 tool before any non-factual answer, and the operator-side nightly audit (see perf brief §5) flags responses where no L2.5 retrieval was logged for the trace. Bundles make B.11 trivial to satisfy in one call when the host wants that; primitives compose to B.11 with discipline when the host wants targeted depth.

### §3.3 — Tier 3 — Raw asset reads (2)

| Tool | What it returns |
|---|---|
| `read_asset(canonical_id, section?)` | Raw markdown of a canonical artifact (MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL). Returns the full asset if `section` is omitted; returns the named section (e.g. `"§3.15"`) if provided. **No implicit truncation** per the §12 directive. The full FORENSIC v8.0 is ~120k tokens; returning it in one call is the host's right. |
| `read_classical_text(work, chapter?, verse_range?)` | Raw text of a classical work (BPHS, Jaimini Sutram, KP Reader, Tajaka Neelakanthi) from `08_CLASSICAL_CROSS_REFERENCE/`. Returns full chapter or verse range; citation-ready chapter/verse identifiers preserved in output. **Coverage caveat in v3.1**: this tool returns content only for assets present in the `classical_texts` corpus; v3.1 ships with sparse coverage (BPHS partial, Jaimini Sutram partial, KP partial, Tajaka unindexed) and v3.2's classical-grounding backfill is what makes this tool fully useful (§9). |

The `read_classical_text` tool is the bridge between the host's classical-grounding rubric and the corpus. Without it, the host can know via `cross_school_lookup` that "BPHS 8.12 addresses Saturn-in-10th delays" but cannot quote the actual verse. With it (and with v3.2's backfill), the host can quote chapter and verse — which is what acharya-grade classical grounding looks like.

### §3.4 — Tier 4 — Observability (2)

| Tool | What it returns |
|---|---|
| `get_trace(trace_id)` | Full step ledger for a prior MCP call, including all sub-tool calls, params, latencies, row counts, error class, `signal_ids_available[]` at each step, and any audit findings the nightly job has attached. Trace retention is 90 days hot, archived to GCS Parquet older. |
| `list_recent_queries(limit?, since?, principal?)` | Recent call history for the calling principal. Super_admin can pass `principal` to inspect other principals' history; acharya/client see only their own. |

These tools are unchanged from v1 in shape, but the trace records they return are richer in v3.1 (carrying audit-findings via `mcp_audit_findings` join — see perf brief §5).

### §3.5 — Tier 5 — Performance and coverage (2)

| Tool | What it returns |
|---|---|
| `tool_health(tool_name?, window_hours?)` | Per-tool metrics: p50/p95/p99 latency, ok/zero-rows/error rates, grounding rate, average bundle size in tokens, recent caveats authored by the operator. Tier-gated: visible to super_admin + acharya; hidden from client. |
| `data_coverage(asset_id?, subkey?)` | Per-data-source coverage: row counts by category/subset, last bootstrap timestamp, expected-vs-actual completeness, staleness flag, operator-authored `next_backfill_planned` and `notes`. Tier-gated: visible to super_admin + acharya; hidden from client. |

These tools surface the perf system to the host. Detailed specifications in the sibling `MCP_PERF_SYSTEM_BRIEF_2026-05-22.md`. Their existence in the tool surface is what closes the "blindfolded orchestrator" loop: the host can ask, mid-conversation, whether a tool that returned zero rows is broken or simply un-backfilled, and route accordingly.

### §3.6 — Tier 6 — Writes (3)

v3.0 had four write tools including `validate_response` (self-audit). v3.1 drops `validate_response` (audit moves operator-side; see §7.6 and perf brief §5) and retains three:

| Tool | What it does |
|---|---|
| `log_prediction(horizon_days, domain, prediction_text, confidence_band, falsifier, source_signals[])` | Logs a forward-looking prediction to `mcp_predictions`. **Host-driven** per v3.1 governance: house-rules requires the host to call this for every forward-looking claim before declaring an answer final. `confidence_band` is the host's own assessment (e.g. `0.65`, or `"medium"` if calibrated language is preferred); `falsifier` is a concrete observable that would disconfirm; `source_signals[]` is a subset of `provenance.signal_ids_available[]` from the most recent retrieval. |
| `record_outcome(prediction_id, outcome, observed_at, notes?)` | Records what actually happened against a prior prediction. Outcome is one of `"realized"`, `"disconfirmed"`, `"partial"`, `"horizon_not_yet_reached"`. This is the data the calibration loop (perf brief §9) consumes to produce `prediction_calibration_score`. |
| `flag_disagreement(class, description, evidence_signal_ids[])` | Writes to `DISAGREEMENT_REGISTER_v1_0.md`'s shadow DB table. Used when the host detects a contradiction across signals/schools/sources that wasn't already pre-registered. Surfaces to the operator dashboard. |

The `score_self_response` tool from v3.0 is **folded into `log_prediction`**: the host's self-assigned confidence band is captured at prediction time, not after-the-fact. This is cleaner — the confidence is attached to the claim at the moment of claim, not retro-attached to a trace. Non-predictive claims (factual lookups, descriptive synthesis) do not need self-scoring because they are auditable directly against the source signals — the operator-side audit (§7.6) verifies cited IDs ⊂ available IDs and flags fabricated numericals; no host self-grading is required.

### §3.7 — Composition diff vs v1 (final)

| Removed from v1 | Why | Added vs v1 | Why |
|---|---|---|---|
| `ask_madhav` | Server-side synthesis; double-LLM antipattern; timeout dominant root cause | `holistic_bundle` | Opt-in B.11-floor / fan-out aid |
| `plan_query` | Server-side planner; host owns orchestration | `multi_school_bundle` | First-class triangulation per classical-grounding rubric |
| `execute_plan` | Server-side planner | `read_classical_text` | Enables classical quoting |
| | | `tool_health` | Agent-facing perf visibility |
| | | `data_coverage` | Agent-facing data visibility |
| | | `score_self_response` (then folded into `log_prediction`) | Calibrated epistemics at claim time |

Net: −3, +5 (one folded), total 21. Every addition maps to an explicit rubric dimension.

---

## §4 — Resource surface

MCP separates *tools* (per-turn calls) from *resources* (loaded once at session attach). v1 shipped two resources. v3.0 shipped four. **v3.1 ships five**, adding `marsys://chart-snapshot` — a structured-facts resource that complements `marsys://chart-overview`'s narrative synthesis.

| URI | Content (~size at super_admin tier) | Refresh trigger | Tier conditioning |
|---|---|---|---|
| `marsys://chart-snapshot` (NEW) | Structured L1 facts: lagna sign + degree + lord + state; planetary positions in D1 with house + sign + degree + dignity + nakshatra + nak-lord + retrograde; Yogakaraka / Atmakaraka / Amatyakaraka identification; current dasha schedule (active maha/antar/pratyantar with start/end dates); top 5 currently-active transit events; immediate panchang at "now" (tithi, vara, nakshatra, yoga, karana). Acharya-grade structured markdown — no prose synthesis. ~2.5k tokens. | FORENSIC bumps; daily for the "active dasha/transit/panchang" tail. | All tiers receive the chart-snapshot; client tier glosses Sanskrit terms inline; the data itself is uniform. |
| `marsys://chart-overview` | Compact synthesis of the chart's most load-bearing themes: ~1-paragraph synthesis of the L2.5 reading (top 5 themes from MSR/UCN), key contradictions (top 2 from CDLM), the chart's "operational anchor" claim (per CGM convergence), the current life-phase characterization (per LEL period summary). ~3k tokens at super_admin/acharya; 800 tokens at client (3-line intro). | FORENSIC bumps; MSR bumps. | Super_admin = full; acharya = full minus internal-audit themes; client = compact intro. |
| `marsys://house-rules` | Operating manual the host follows during the session: school commitments (Parashari primary; Jaimini for karaka work; KP for cuspal time; Tajaka for varshphal); terminology conventions; citation conventions (cite only from `provenance.signal_ids_available[]`); B.11 expectation (consult ≥1 L2.5 tool before non-factual answer); disclosure-tier output template (calibrated band + falsifier + horizon mandatory for predictions); multi-school triangulation rules; when to use bundles vs primitives; how to log predictions; what the operator-side audit checks for; current per-tier output-template variants. | Governance changes; quarterly. | Super_admin = full including internal-audit + red-team annotations; acharya = full minus internal-audit; client = simplified output template (Sanskrit glossed on first use; confidence as language; mandatory falsifier; no internal-audit references). |
| `marsys://capabilities` | Current operational state of every tool and data source: tool descriptions including current coverage caveats, per-tool 24h reliability snapshot (p50/p95, ok-rate, zero-rows-rate, grounding-rate), per-asset coverage breakdown, recent backfill activity, operator-authored caveat strings. Built from the perf system's materialized views at session attach (cheap; sub-100ms). ~3k tokens. | Generated at session attach. | Super_admin + acharya = full; client = tool names + tool-gloss only, hide reliability stats. |
| `marsys://school-conventions` | Reference for the four schools (Parashara, Jaimini, KP, Tajaka): what each school is authoritative for; how each school's outputs differ in form (e.g., KP cusps vs Parashari houses; Jaimini karakas vs Parashari significators); known points of disagreement; classical-text anchors per school. Static reference; rarely changes. ~2.5k tokens. | Manual edits when conventions evolve. | Uniform across tiers. |

Total token load at session attach (super_admin tier): ~13k tokens of orientation, well within any modern context window's budget. Pays for itself in saved discovery tool calls — the host knows the chart's lagna, the active dasha, the current transits, the school commitments, and the operational state of every tool before the user's first message. The depth-always rubric means we are not parsimonious here: the host benefits from full orientation, and we are not paying for it twice (resources are loaded once per session).

The addition of `marsys://chart-snapshot` to v3.0's four resources reflects a sharper read of the rubric: an acharya consuming this instrument wants to *see the chart*, not be told a story about it. The narrative (`chart-overview`) supplements but does not replace the facts (`chart-snapshot`). Both exist; the host has both at attach; the acharya-grade output template (in `house-rules`) tells the host to ground every claim in chart-snapshot facts where the claim is L1 and in retrieved L2.5 signals where the claim is synthesis.

---

## §5 — Response envelope (uniform, strict-allowlist provenance)

Every read tool (Tier 1 primitives, Tier 2 bundles, Tier 3 raw reads, Tier 5 perf, Tier 4 observability) returns a uniform envelope. The `result` field varies per tool; the wrapper is invariant. This makes the host's parsing trivial and makes the audit job (perf brief §5) able to operate on any retrieval uniformly.

```jsonc
{
  "ok": true,
  "trace_id": "qry_2026-05-22_uuid",
  "audience_tier": "super_admin" | "acharya" | "client",

  "tool_call": {
    "tool_name": "query_signals",
    "params_received": { /* exactly what the host sent */ },
    "params_resolved": { /* defaults applied; tier filters applied */ },
    "served_from_cache": false,
    "latency_ms": 35,
    "streamed": false  // true for Tier 2 bundles when SSE was used
  },

  "result": {
    /* tool-specific payload */
    /* For primitives: rows[] with signal_id, content, layer, confidence, significance, source_canonical_id, source_version, source_section */
    /* For bundles: bundle_entries[] of per-sub-tool result blocks, each with its own result + provenance */
    /* For read_asset: { markdown, section_id, source_version, source_canonical_id } */
    /* For tool_health: tools[] with metric rows */
    /* For data_coverage: assets[] with per-subkey coverage rows */
  },

  "provenance": {
    "data_sources_touched": ["MSR_v5_0", "FORENSIC_v8_0", "LEL_v1_6"],
    "layer_tags_present": ["L1", "L1.5", "L2.5"],
    "signal_ids_available": ["SIG.MSR.053", "SIG.MSR.179", "SIG.MSR.317", "FORENSIC.§3.15", "LEL.E.014", /* ... */],
    "signal_ids_available_total": 87,
    "rows_returned": 87,
    "tier_filtering": {
      "applied": true,
      "rows_filtered_out": 3,
      "reason": "acharya tier — 3 instrument_meta signals suppressed (red_team + disagreement_register)"
    },
    "result_hash": "sha256:e9adc9b3797f4f6098d7686b4d5e04e9...",
    "cite_allowlist_contract": "strict"  // see §5.1
  },

  "epistemics_hints": {
    "data_freshness": "current" | "stale" | "missing",
    "is_forward_looking_data": false,
    "multi_school_convergence_in_result": null | { "schools_present": 3, "convergence_score": 0.85, "divergent_schools": ["Tajaka"] },
    "applicable_confidence_floor": 0.7,
    "horizon_relevant": null | "this dasha lord's antar (~14 months)",
    "operator_caveats": [
      "chart_facts category 'shadbala' currently empty; rely on SIG.MSR.053 et al for strength claims"
    ]
  },

  "warnings": [
    /* runtime warnings: known sub-tool bugs not yet fixed; partial bundle failures; staleness; etc. */
  ]
}
```

Four intentional choices:

**No `answer_markdown` field anywhere.** The platform produces zero prose. Synthesis is the host's job. If a future v3.x re-introduces a server-side synthesis path for the web `/consume` chat or for a "second voice" inter-rater workflow, it lives in a *different envelope* — not piggybacked on the MCP read envelope.

**`epistemics_hints` not `epistemics`.** v1 had the platform asserting `confidence`/`falsifier`/`horizon` on synthesis output. v3.1 has the platform *hinting* (freshness, forward-looking flag, multi-school convergence, applicable floor, operator caveats) so the host can build the final epistemics on the claim it composes. The host writes its own confidence band back via `log_prediction` for forward-looking claims; for non-forward claims, the audit subsystem (§7.6) verifies citation discipline post-hoc.

**`tier_filtering.applied: bool`** is mandatory and visible in every envelope. The host always knows whether what it saw was the complete data set or a tier-filtered subset, and *why* — the `reason` string names the filter applied. This is what makes the multi-tier model auditable: an acharya inspecting their own session can confirm they're seeing the full chart data and only instrument-meta is filtered.

**`provenance.signal_ids_available[]` is a strict cite-allowlist.** This is the single most important governance contract in v3.1. The host is contractually bound to cite only from this set in any response derived from this retrieval. House-rules states the rule explicitly: "When responding to the user, every citation `[^N]` must resolve to an identifier that appears in `provenance.signal_ids_available[]` from the retrieval(s) you performed for this turn. Citing IDs not in the allowlist is a fabricated citation and is recorded as a violation." The operator-side nightly audit (perf brief §5) joins traces with response transcripts (where available — Cowork sessions have these; Claude Chat sessions do not) and computes `fabricated_cites = cited_ids − available_ids`. For bundles, the union of all sub-tools' `signal_ids_available[]` becomes the bundle envelope's top-level allowlist.

### §5.1 — Why "strict cite-allowlist" replaces v3.0's `validate_response`

v3.0's `validate_response` tool asked the host to call a self-audit on its own draft before declaring an answer final. Two problems: (a) it's optional, so under load it gets skipped; (b) it's the host grading itself, which is structurally weak audit. v3.1 replaces it with a stronger contract: the platform names the allowed citation set in every retrieval envelope, house-rules makes citation-discipline load-bearing in the host's operating instructions, and the operator-side nightly audit (independent of the host) verifies compliance against the recorded trace. The platform tells the host what it may cite; the operator verifies what the host did cite; the host's autonomy in between is preserved.

This is the single most consequential governance change in v3.1 vs v3.0. The detailed mechanism is in the perf brief §5 (the audit subsystem).

---

## §6 — Audience-tier model (narrowly scoped)

Three audience tiers. Each is API-key-stamped at the MCP transport layer and carried as `X-MCP-Audience-Tier` through to retrieval. v3.1 narrows the retrieval-layer filtering to one thing — *instrument-meta data* — and pushes every other tier difference to tier-conditioned `house-rules`.

| Tier | Retrieval-layer filtering (what the platform does) | Output-template differences (what house-rules tells the host) |
|---|---|---|
| `super_admin` | No filtering. All signals, all schools, all draft/contradicted material, all instrument-meta (red-team findings, disagreement-register signals, internal audit notes appearing in MSR/UCN). | Acharya-grade rigor. Every claim cited. Multi-school annotation where convergent. Confidence band + falsifier on predictions. Open contradictions surfaced. No softening. Internal-audit references permitted in the response. |
| `acharya` | Instrument-meta signals filtered out (signals tagged `instrument_meta: true` in MSR/UCN — these are about the *instrument's state*, not the chart). Chart data uniform with super_admin. | Same rigor as super_admin. Allowed to surface uncertainty more openly (the acharya peer-review case). No internal-audit references in the response (the data wasn't retrieved). |
| `client` | Same as acharya — instrument-meta filtered; chart data uniform. **No additional retrieval filtering.** | Sanskrit glossed on first use. Confidence as plain language ("high confidence" rather than "0.85") unless the user explicitly asks for numbers. **Mandatory falsifier on every prediction, prominently placed.** Multi-school divergence flagged but not deeply explored unless the user asks. No internal-audit references. |

The reframe vs v3.0: v3.0 had client tier seeing different *data* (raw shadbala/virupa rows hidden, etc.). v3.1 has client tier seeing the same data, presented differently. The platform's job is to deliver the deepest accurate context (per the §12 directive). Whether a client sees the number `59.18 virupa` or a gloss like `"maximum dignity strength"` is a presentation choice that lives in `house-rules`'s tier-conditioned output template — not a retrieval choice.

**Why this matters operationally.** The retrieval layer becomes simpler: one filter (`WHERE NOT instrument_meta`) for non-super-admin tiers, applied uniformly across every primitive. The output layer (the host's response) becomes richer: the same retrieval drives three different prose styles, each justified by tier-conditioned house-rules. The architecture supports adding a fourth tier (e.g. `public_redacted`, already enumerated in `platform/src/app/api/mcp/execute/route.ts:121` but unused) without touching the retrieval layer — just by authoring a fourth `house-rules` variant.

**Tier inheritance and key revocation.** API keys carry a single tier. Tier escalation requires a new key (admin-issued). Tier de-escalation requires key revocation + re-issuance. The `mcp_api_keys` table (migration 070) has `audience_tier`, `revoked_at`, `expires_at` columns; v3.1 adds `tier_change_history` JSONB column for audit of tier reassignments. Per-tier rate limits live in a small `mcp_tier_limits` table (recommended initial values: super_admin 1000 RPM, acharya 200 RPM, client 50 RPM — generous enough that legitimate use never hits them; tight enough that runaway loops self-throttle).

---

## §7 — Governance under v3.1

v1 had 12 governance rules (G1–G12 per `MCP_BRIEF_v1_0 §6`). v3.0 re-derived them under server-side synth removal. v3.1 re-derives the same rules under self-audit removal. Each rule's enforcement is named precisely.

| Rule | v1 enforcement | v3.0 enforcement | v3.1 enforcement |
|---|---|---|---|
| **G1 — B.11 Whole-Chart-Read floor** | `enforceB11Floor()` server-side injection of L2.5 tools | `house-rules` instructs the host + `validate_response` self-check | `house-rules` instructs the host + **operator-side nightly audit** flags traces with no L2.5 retrieval before a non-factual answer. Audit findings surface to dashboard; violation rate is a tracked metric (perf brief §3.1, §5). |
| **G2 — Audience-tier stamping** | API key → tier → plan stamp | API key → tier → retrieval filter | Same as v3.0. Tier-stamped in every envelope's `audience_tier` field. Retrieval-layer filter applies only to instrument-meta (§6). |
| **G3 — Trace logging** | Every step in `query_trace_steps` | Every MCP tool call + sub-tool call logged | Same as v3.0 + audit findings joined to traces via `mcp_audit_findings.trace_id` (perf brief §4.3). |
| **G4 — PPL discipline** | Server auto-logged with placeholder falsifiers | Host calls `log_prediction` per house-rules | Same as v3.0 + audit job flags forward-looking responses where no `log_prediction` was emitted in the same session (perf brief §9). |
| **G5 — Disclosure tier (epistemics)** | Server-built block | Host-built via output template + `score_self_response` write-back | Host-built via tier-conditioned output template (in `house-rules`); confidence band folded into `log_prediction` at claim time (no separate `score_self_response` tool); audit verifies template compliance. |
| **G6 — Citation discipline** | Regex extraction from synth text | Host cites from `provenance.signal_ids_available[]`; self-check via `validate_response` | **Strict cite-allowlist contract** (§5.1) + operator-side audit verifies `cited_ids ⊆ available_ids`. Fabricated cites surface as audit findings. |
| **G7 — No fabrication (B.10)** | Server synth prompt sees only retrievals | Host sees only bundle + self-check | Audit subsystem regex-extracts numerical claims (`\d+\.?\d*\s*(virupa|degrees|rupas|points)?`) from response transcripts where available, joins to retrieved row contents, flags claims whose numerical values don't appear in retrieved data. |
| **G8 — Layer purity (B.1)** | Mixed in synth prompt | Per-result layer tags in provenance | Same. Audit verifies L1 claims cite L1 sources, L2.5 claims cite L2.5 sources; cross-layer attribution flagged. |
| **G9 — Versioning** | platform-mcp semver | Same | platform-mcp version bumps to **3.1.0**. SDK semver enforced. |
| **G10 — Scope boundary** | Brief scope | Brief scope | Same. v3.1's `may_touch` / `must_not_touch` defined in the CLAUDECODE brief (§13). |
| **G11 — Mirror discipline (Gemini)** | No Gemini-side surface | Same | Same. v3.1 is still Claude-side only. No MP.N entry in `CANONICAL_ARTIFACTS_v1_0.md §2`. |
| **G12 — Red-team obligation** | Discharged MCP-4-S2 | Required for v3.0 | Required for v3.1 (threat model shifts; see §11). Red-team session is a v3.1 close prerequisite — 0 class-1 findings required. |

### §7.6 — The operator-side audit (the moved governance closure)

v3.0's self-audit (`validate_response`) is replaced by an operator-side nightly audit job. The full mechanism lives in the perf brief §5; the summary here is:

**Inputs:** all trace records from the last 24h (`tool_execution_log`, `query_trace_steps`, `mcp_predictions`); response transcripts where available (Cowork sessions; not Claude Chat).

**Per-trace checks:**
1. **B.11 floor.** For any trace with a final response classified non-factual (heuristic on response length + question shape), verify ≥1 retrieval from MSR/UCN/CDLM/CGM/RM was logged before the final response. If not, attach finding `audit.b11_skipped`.
2. **Citation set-membership.** For any trace with response text available, regex-extract `[^N]` citations and `SIG.MSR.NNN` / `LEL.E.NNN` / `FORENSIC.§N.N` patterns. Verify each cited ID appears in some retrieval's `signal_ids_available[]` in the trace. Findings: `audit.cite_grounded` (good), `audit.cite_fabricated` (bad).
3. **Numerical claim grounding.** Regex-extract numerical claims (e.g., `\d+\.?\d*\s*virupa`). Cross-check against retrieved row contents in the trace. Findings: `audit.numerical_grounded`, `audit.numerical_unverified`.
4. **PPL emission.** For any trace whose response heuristically contains forward-looking language, verify ≥1 `log_prediction` was emitted in the same session. Finding: `audit.ppl_missing`.
5. **Tier-template compliance.** For any client-tier trace, verify house-rules template requirements (Sanskrit glossing on first use; mandatory falsifier on predictions). Heuristic — coarse but better than nothing.

**Outputs:** rows written to `mcp_audit_findings` (perf brief §4.3); findings surfaced on `/admin/mcp/health` dashboard's Audit tab; severity-thresholded alerts (Slack/email) for `cite_fabricated` rate spikes.

**Why this is stronger than v3.0's self-audit.** (a) Mandatory, not opt-in. (b) Independent — the audit job runs without the host's cooperation. (c) Retrospective and continuous — every response is checked, not just the ones the host remembers to validate. (d) Operator-visible — violations surface as backlog items, not silent metric drift. The trade-off is that audit feedback arrives after the response is delivered (the host can't self-correct in the turn), which is acceptable because the host's house-rules guidance is detailed enough to make first-pass compliance high, and audit findings inform house-rules iteration over time.

---

## §8 — Transport, streaming, and the depth-always UX

The depth-always rubric is structurally honest: holistic queries take 15–40 seconds when bundles fan out across 8 tools in parallel. Without streaming, that's 15–40 seconds of dead air for the host (and for the user behind the host). v1's MCP transport (`StreamableHTTPServerTransport` in `platform-mcp/src/server.ts:141`) is SSE-capable but the platform endpoints don't emit progressively. v3.1 wires streaming end-to-end for Tier 2 bundles.

**Streaming contract for `holistic_bundle` and `multi_school_bundle`:**

The bundle endpoint emits SSE events as sub-tools complete. Each event is a partial-result chunk with the same envelope shape as a final response but with `tool_call.streamed: true` and a `partial: true` flag. The final event carries `partial: false` and the consolidated `provenance.signal_ids_available[]` (the union across all sub-tools).

```
event: bundle.sub_tool.completed
data: {"sub_tool":"query_signals","ok":true,"rows_returned":87,"signal_ids":["SIG.MSR.053",...]}

event: bundle.sub_tool.completed
data: {"sub_tool":"get_cgm_subgraph","ok":true,"rows_returned":42,"signal_ids":["CGM.N.014",...]}

event: bundle.sub_tool.error
data: {"sub_tool":"vector_search","ok":false,"error_class":"timeout","attempted_params":{...}}

event: bundle.completed
data: { /* full bundle envelope with consolidated provenance.signal_ids_available */ }
```

**Host-side UX.** The host model receives sub-tool completion events as they happen and can surface progress to the user ("Retrieved 87 MSR signals; retrieving CGM subgraph..."). The user sees motion. For Claude Chat specifically, this matters: even though the Claude Chat MCP timeout is ~60s, streaming responses keep the connection alive indefinitely as long as events flow. Long bundles never trip the timeout.

**Per-sub-tool error isolation.** A single sub-tool failure does not fail the bundle. The bundle returns successfully with `bundle_entries[].errored: true` flags for the failing sub-tools and full results for the rest. The host receives a partial bundle and can decide whether to retry the failing sub-tool, work around it, or surface the partial state to the user. This is what makes bundles robust to transient retrieval failures.

**Tier 1 primitives are not streamed.** Surgical primitives are single-call, sub-second-to-low-second. Streaming overhead is not worth it for them. Only Tier 2 bundles use SSE.

**Server implementation.** Wire `StreamableHTTPServerTransport.streamText` through `/api/mcp/bundles/{name}/route.ts` using Next.js `Response` with a `ReadableStream` body that emits SSE-formatted chunks. The orchestration on the platform side uses `Promise.allSettled` over sub-tool calls and pipes each settled promise's result into the SSE stream as it resolves. Detailed implementation lives in the CLAUDECODE brief (§13 below).

---

## §9 — Data layer audit and prioritized backfill

The native explicitly authorized data-asset changes. The audit below is empirical (from v1 probing in `MCP_DIAGNOSIS_2026-05-22.md §3.1`) and the backfill plan is prioritized **classical-grounding first** per the rubric's stated priorities.

### §9.1 — What's actually populated (empirical baseline)

| Asset | Status | Notes |
|---|---|---|
| `chart_facts` (FORENSIC L1) | **~5/37 categories populated** | `planet`, `house`, `strength`, `birth_metadata`, `dasha_vimshottari` have data. `shadbala`, `ashtakavarga_*`, `bhava_bala`, `kp_*`, `upagraha`, `mrityu_bhaga`, `longevity_indicator`, `avastha`, `varshphal`, `arudha_occupancy` — empty or sparse. |
| `msr_signals` (MSR L2.5) | **514 signals, all queryable** | But some `params` filters (domain, karakas, limit) are ignored by `msr_sql` per the smuggling bug (§3.1 Rule 1). Mandatory fix. Also: 419/573 signals lack explicit FORENSIC/LEL citations per the v1.3 carry-forward queue. |
| `lel_events` | **36 events + 5 period summaries + 6 chronic patterns, complete** | Full bodies queryable. Chart-states Swiss-Ephemeris-populated. |
| `panchang_daily` | **Complete 1900–2100, full enrichment** | Bootstrapped post-Phase 4C (73,414 rows × full enrichment per `CLAUDE.md §E`). |
| `ephemeris_daily` | **Complete 1900–2100** (verify) | Phase 4B work referenced; verify via `query_ephemeris({planet:"Saturn", date_range:["2026-01-01","2026-12-31"]})`. |
| `rag_chunks` + `rag_embeddings` | **Complete, Vertex 768-dim** | Indexed over FORENSIC + UCN + MSR + L2.5 syntheses + portions of multi-school + classical. |
| `multi_school_*` tables | **Parashara ~100%, Jaimini ~80%, KP ~60%, Tajaka ~20%** | Per Sonnet's read; confirm via probe. Tajaka is the most-sparse, KP next. |
| `classical_texts` (BPHS / Jaimini Sutram / KP / Tajaka) | **BPHS partial; Jaimini Sutram partial; KP partial; Tajaka unindexed** | The `read_classical_text` tool's coverage depends entirely on this corpus. v3.2 backfill is what makes the tool useful. |
| `mcp_predictions` | **New in v1; ~0 rows at v3.1 start** | PPL history begins accumulating with v3.1 deployment. |
| `mcp_audit_findings` | **NEW table in v3.1** | Empty at v3.1 deployment; populates from the first audit run. |

### §9.2 — Ranked backfill priorities (classical-grounding first)

The v3.0 ordering put `shadbala` and `ashtakavarga` first (depth gaps). v3.1 inverts: **classical-grounding gaps first** because they remove a *capability* (the classical-grounding rubric dimension cannot be served at all without them), whereas depth gaps merely degrade a quality (the strength rubric dimension is degraded but still partially served via MSR signals). Restoring a capability outranks improving a quality.

| Phase | # | Backfill | Rubric dimension served | Effort |
|---|---|---|---|---|
| **v3.2** | 1 | `classical_texts` — BPHS chapters 1–30 indexed (Brihat Parashara Hora Shastra) | Classical grounding | Large — text procurement, OCR/cleaning, chapter/verse indexing, embedding |
| **v3.2** | 2 | `classical_texts` — Jaimini Sutram 1.1–4.4 fully indexed | Classical grounding | Medium — Jaimini Sutram is shorter than BPHS |
| **v3.2** | 3 | `classical_texts` — KP Reader (volumes 1–6) indexed | Classical grounding | Large — multiple volumes, OCR work |
| **v3.2** | 4 | `classical_texts` — Tajaka Neelakanthi indexed | Classical grounding | Medium — single text |
| **v3.2** | 5 | `multi_school_*` — Jaimini karaka tables per signal (~80% → 100%) | Classical grounding | Medium |
| **v3.2** | 6 | `multi_school_*` — KP cuspal mappings per signal (~60% → 100%) | Classical grounding | Large — KP requires careful cuspal computation |
| **v3.2** | 7 | `multi_school_*` — Tajaka muntha + saham + year-lord tables (~20% → 100%) | Classical grounding | Large — substantial content authoring |
| **v3.3** | 8 | `chart_facts.shadbala` (Sthana / Dig / Kala / Cheshta / Naisargika / Drik virupas per planet × 9 planets × 7 measures = 63 rows) | Depth | Medium — Jagannatha Hora or Swiss-Ephemeris extraction + ingest |
| **v3.3** | 9 | `chart_facts.ashtakavarga_*` (SAV, BAV, pinda, kakshya, sarvashtakavarga totals) | Depth + classical grounding | Medium — same source as shadbala |
| **v3.3** | 10 | `chart_facts.bhava_bala` (per-house BVB) | Depth | Small — derivable once shadbala lands |
| **v3.3** | 11 | `chart_facts.kp_*` (cusp + planet sub-lord + significator + ruling-planet tables) | Depth (KP) | Medium |
| **v3.3** | 12 | `chart_facts.upagraha` (Gulika, Mandi, Yamaganda, Kala, Maandi) | Depth | Small |
| **v3.3** | 13 | `chart_facts.varshphal` (Tajaka muntha + year-lord per year) | Depth + classical grounding (Tajaka) | Medium |
| **v3.4** | 14 | MSR signal-grounding (419/573 signals lack FORENSIC/LEL citations per v1.3 carry-forward queue) | Calibrated epistemics (citation auditability) | Large — per-signal manual or semi-automated grounding |
| **v3.4** | 15 | `mcp_predictions` historical backfill from `/consume` chat (if any historical predictions exist) | Calibrated epistemics (calibration history) | Small if data exists; skip if not |

The phase mapping: v3.2 ships classical grounding (items 1–7); v3.3 ships depth (items 8–13); v3.4 ships epistemic refinement (items 14–15) alongside the red-team. This is a 3-phase data backfill following the v3.1 foundation phase. Total: ~9–12 sessions across v3.2 + v3.3 + v3.4, the longest pole being the classical-text OCR/indexing work.

### §9.3 — New data assets v3.1 introduces

| Asset | Purpose | Build cost |
|---|---|---|
| `tool_call_metrics` (materialized view) | Per-tool aggregated metrics — feeds `tool_health()` | Small (perf brief §4.2) |
| `data_source_coverage` (materialized view) | Per-asset coverage stats — feeds `data_coverage()` | Small (perf brief §4.2) |
| `data_source_expected` (table) | Declarative expected-coverage targets — joined against actual to compute completeness | Small — operator-authored |
| `tool_caveats` (table) | Operator-authored caveat strings surfaced in `tool_health()` and `capabilities` resource | Small — operator-edited via dashboard |
| `mcp_audit_findings` (table) | Output of the nightly audit job (B.11 violations, fabricated cites, etc.) | Small — schema in perf brief §4.3 |
| `mcp_session_summaries` (materialized view) | Per-session rollup for the operator dashboard's Sessions tab | Small |
| `school_convergence_index` (materialized view) | Pre-computed per-claim convergence scores across schools, refreshed nightly | Medium — depends on multi-school backfill (v3.2) |

All seven introduced infrastructure is *additive* — none of it changes existing tables or their writes. v3.1 just adds new tables, views, and the nightly-audit cron entry.

---

## §10 — Code-level fixes mandated by the v1 diagnosis

These five fixes from `MCP_DIAGNOSIS_2026-05-22.md §7` are mandatory inputs to v3.1. None can be deferred; each is a hard prerequisite for v3.1 ship.

| # | Fix | Where | What |
|---|---|---|---|
| F.1 | `vector_search` placeholder-query bug | `platform/src/lib/retrieve/vector_search.ts:236` | Prefer `params.text` / `params.query_text` over `plan.query_text` when the latter starts with `surgical_primitive:`. One-line fix; verified by probe: `vector_search({text:"saturn shadbala"})` should return Saturn-shadbala chunks, not generic Cross-Reference Matrix excerpts. |
| F.2 | Audit every primitive for `plan.*` vs `params.*` smuggling | All files in `platform/src/lib/retrieve/` | Each tool must accept its filter inputs from `params` first, fall back to `plan` for `/consume` callers. Known affected: `msr_sql` (domain, limit, karakas ignored). Audit and fix every primitive in the registry. |
| F.3 | `query_chart_facts` description lists fake categories | `platform-mcp/src/tools/query_chart_facts.ts:19,54` | Replace hand-authored description with generated-from-enum description (the enum is at `platform/src/lib/retrieve/chart_facts_query.ts:21–30`). Generated description includes both real categories AND current coverage state per category. |
| F.4 | `cloudbuild.yaml` missing `MCP_INTERNAL_TOKEN` | `platform-mcp/cloudbuild.yaml` | Bind via Secret Manager; auto-mount on deploy. Same on `amjis-web` Cloud Run service. Document in v3.1 close-out artifact. |
| F.5 | Bearer key validation not cached | `platform-mcp/src/auth.ts` | Add in-memory `Map<key_prefix, {principal, expires_at}>` with 60-second TTL. Saves 50–250ms per call, hottest path in the MCP. Revocation has a 60s grace; acceptable. |

Two additional fixes v3.1 introduces (not from the diagnosis):

| # | Fix | Where | What |
|---|---|---|---|
| F.6 | Remove `marsys_methodology_block` from the synthesis prompt template | `platform/src/lib/prompts/templates/shared.ts:140` | Only relevant for the web `/consume` path. v3.1 doesn't run server synthesis, so this fix is orthogonal to the MCP rebuild. Recommended regardless because it's the single highest-leverage fix for the `/consume` timeout problem (50+ seconds saved per typical call). Note this fix in the v3.1 close-out artifact as a recommended action for the `/consume` workstream (out of scope for v3.1 sealing but flagged). |
| F.7 | Remove `arbitrateBudgets()` from the v3.1 MCP path | `platform/src/lib/pipeline/budget_arbiter.ts` (the function) and the MCP route (the call site) | Per §12 directive. This function rations tool output tokens against a synthesis prompt's context window — but v3.1 has no server-side synthesis prompt. Keep the function for the `/consume` path; remove its invocation from the MCP retrieval path. |

---

## §11 — Security threat model under multi-tier

v3.1 expands the principal surface (acharya + client tiers beyond just super_admin). The threat model expands correspondingly. v3.0 did not explicitly cover this; v3.1 names threats and mitigations.

| Threat | Vector | Mitigation in v3.1 |
|---|---|---|
| **T.1 Tier escalation via key leakage** | A client-tier key is leaked; attacker uses it to call write tools (`log_prediction`, `record_outcome`, `flag_disagreement`). | Write tools check `audience_tier` server-side before accepting writes. Client-tier writes to `mcp_predictions` are permitted but tagged with the principal — operator can audit who wrote what. Writes to `flag_disagreement` are super_admin-only; client/acharya keys get 403. |
| **T.2 Cross-principal data exfiltration** | Acharya A is curious about acharya B's session history; calls `list_recent_queries({principal:B})`. | `list_recent_queries` checks principal authorization: super_admin can pass any `principal`; acharya/client see only their own (the `principal` param is ignored or 403'd for non-super-admin). |
| **T.3 Chart-data exfiltration via URL-key leak** | A client registers the connector URL `https://amjis-mcp...?api_key=mcp_prod_X` in their browser; URL leaks via referrer/log/shared screenshot; attacker uses the leaked key. | URL-embedded keys are flagged in `mcp_api_keys.allows_url_param: bool`. Super_admin keys may have this enabled (for Claude Chat custom-integration UX); acharya/client keys must not. Tier limit enforced at key issuance time. Document this clearly in the operator runbook. |
| **T.4 Replay attacks on writes** | Attacker captures a `log_prediction` request and replays it. | All writes carry a server-stamped `trace_id`; the `mcp_predictions` table enforces `UNIQUE(trace_id, prediction_text_hash)`. Replays no-op. |
| **T.5 Resource exfiltration via `read_asset`** | A client-tier key calls `read_asset("FORENSIC_v8_0")` and exfiltrates the full chart. | Acceptable per tier rubric — the chart IS the product. The platform's role is to deliver chart data; tier limits guard the *instrument-meta* surface (red-team findings, disagreement-register), not the chart itself. If the operator wants strict chart-data protection for clients, the `read_asset` tool is gated to super_admin + acharya at registration time (one config flag). |
| **T.6 Rate-limit DoS** | Attacker hammers Tier 2 bundle endpoints to exhaust platform capacity. | Per-tier rate limits in `mcp_tier_limits` (§6); per-key rate limits per principal; Cloud Run autoscaling absorbs short bursts. Bundle endpoints have a per-key concurrency cap (default: 4 concurrent bundles per acharya/client; 16 for super_admin). |
| **T.7 Audit bypass via response not transcribed** | Audit job depends on response transcripts for citation/numerical checks. Claude Chat sessions don't transcribe to the platform. | Audit job degrades gracefully: traces without response transcripts get a subset of checks (B.11 floor + PPL emission, both verifiable from trace alone). Citation + numerical-fabrication checks run only on Cowork sessions (which do transcribe via the cowork session-info MCP). This is a known limitation; v3.x could add an opt-in "send transcript" path from Claude Chat. |
| **T.8 Prompt injection via retrieved data** | A malicious actor seeds content into the LEL or MSR that, when retrieved, instructs the host to misbehave. | Retrieved content is rendered as quoted markdown in tool returns; house-rules instructs the host to treat retrieved content as data not instructions. The audit subsystem flags suspicious instruction-like patterns in retrieved rows. This is partial mitigation; full mitigation requires content provenance verification at ingest time (write-discipline on `msr_signals` and `lel_events` — already in place per `CLAUDE.md §I B.10`). |

Red-team session for v3.1 (per G12) explicitly probes T.1, T.2, T.3, T.7, T.8. Zero class-1 findings required for v3.1 sealing.

---

## §12 — Migration plan

v3.0 proposed 4 phases. v3.1 expands to **5 phases with finer granularity** because the foundation phase is larger than v3.0 estimated (v3.0 said "2 sessions"; v3.1 estimates 5–6 sessions for v3.1.0 alone).

### v3.1.0 — Foundation (~5–6 sessions)

**Scope.** Remove the `/api/mcp/execute` server entrypoint (delete `ask_madhav`, `plan_query`, `execute_plan`). Implement Tier 2 bundles with streaming. Implement Tier 5 perf tools. Implement Tier 6 writes (3, not 4). Rewrite all MCP tool descriptions (enum-derived). Author all 5 resources (with tier conditioning). Fix all §10 code-level bugs (F.1–F.7). Implement the operator-side audit subsystem (perf brief §5). Stand up the operator dashboard at `/admin/mcp/health` (perf brief §8). No data backfill in this phase.

**Sub-phase breakdown:**
- **v3.1.0-S1** — Code-level fixes (F.1–F.5, F.7). Pure-MCP path cleared of v1 bugs. Bearer cache + cloudbuild hardening. Acceptance: every Tier 1 primitive honors `params` filters; `vector_search` returns relevant chunks; cloudbuild redeploys are clean.
- **v3.1.0-S2** — Tier 2 bundles + SSE streaming. `holistic_bundle` and `multi_school_bundle` shipped with per-sub-tool error isolation and SSE response framing. Acceptance: `holistic_bundle("strongest planet")` returns ≥6 sub-tool entries within 15 s end-to-end; partial-failure case returns successful sub-tools + errored sub-tools flagged.
- **v3.1.0-S3** — Resources (5) + tool description regeneration. Resources auto-load at session attach; tool descriptions enum-derived with coverage caveats inline. Acceptance: session attach loads ~13k tokens of orientation in super_admin tier; `query_chart_facts` description names real categories only.
- **v3.1.0-S4** — Perf system + audit subsystem (per perf brief Phases P0–P3). `tool_execution_log` extended; materialized views built; `tool_health` + `data_coverage` tools shipped; `marsys://capabilities` resource generator wired; audit job runs nightly. Acceptance: `tool_health()` returns metrics for all 10 primitives; nightly audit produces first set of findings.
- **v3.1.0-S5** — Operator dashboard at `/admin/mcp/health`. Three tabs (tool health, data coverage, audit findings). Inline-editable caveats + backfill notes + alert thresholds. Acceptance: operator edits a caveat; caveat surfaces in next `tool_health()` call.
- **v3.1.0-S6** — Tier-conditioned `house-rules` content authoring + v3.1 sealing of foundation. House-rules variants for super_admin / acharya / client / public_redacted (latter authored but not yet keyed). Acceptance: same query against same data returns different output templates by tier (verified by operator-run probe with three keys).

**Out of scope:** data backfill (v3.2/v3.3), red-team (v3.4).

### v3.2 — Classical-grounding backfill (~5 sessions)

**Scope.** Items 1–7 from §9.2. Multi-school table backfill + classical-text corpus indexing.

**Sub-phase breakdown:**
- **v3.2-S1** — BPHS chapters 1–30 indexed (the largest single text). Acceptance: `read_classical_text({work:"BPHS", chapter:8})` returns chapter 8 verses with verse_id refs.
- **v3.2-S2** — Jaimini Sutram + KP Reader indexed. Acceptance: `read_classical_text({work:"Jaimini Sutram"})` returns full text by chapter; KP chapters accessible.
- **v3.2-S3** — Tajaka Neelakanthi indexed. Acceptance: `read_classical_text({work:"Tajaka Neelakanthi"})` returns text.
- **v3.2-S4** — Multi-school tables backfilled: Jaimini karakas (100%), KP cuspal (100%). Acceptance: `cross_school_lookup({claim:"Saturn in 10th delays career"})` returns substantive Parashara + Jaimini + KP stances.
- **v3.2-S5** — Tajaka tables backfilled + `school_convergence_index` materialized. Acceptance: `multi_school_bundle({claim:"Mercury is the operational anchor"})` returns ≥4 per-school evidence blocks; `school_convergence_index` view populated.

### v3.3 — Depth backfill (~3–4 sessions)

**Scope.** Items 8–13 from §9.2. `chart_facts` shadbala, ashtakavarga, bhava_bala, kp_*, upagraha, varshphal.

**Sub-phase breakdown:**
- **v3.3-S1** — Shadbala + ashtakavarga ingestion (sources from Jagannatha Hora or Swiss-Ephemeris derivation). Acceptance: `query_chart_facts({category:"shadbala", rank_by:"total_rupas"})` returns 9 planets ranked.
- **v3.3-S2** — bhava_bala + kp_* + upagraha ingestion. Acceptance: `query_chart_facts({category:"kp_cusp"})` returns 12 cusps with sub-lord; `query_chart_facts({category:"upagraha"})` returns Gulika + Mandi rows.
- **v3.3-S3** — Tajaka varshphal ingestion (depends on v3.2 Tajaka classical-text indexing for citation grounding). Acceptance: `query_chart_facts({category:"varshphal", year:1984})` returns muntha + year-lord rows for native's birth year.
- **v3.3-S4** — `data_coverage("chart_facts")` reports ≥30/37 categories complete; sealing.

### v3.4 — Epistemic refinement + red-team + sealing (~2 sessions)

**Scope.** Items 14–15 from §9.2. MSR signal-grounding pass (closes the 419/573 ungrounded-signals gap). Red-team session per G12. Author `MCP_v3_1_CLOSE.md` sealing artifact.

**Sub-phase breakdown:**
- **v3.4-S1** — MSR signal-grounding pass. Semi-automated: for each ungrounded signal, identify candidate FORENSIC/LEL anchors via embedding similarity; operator review + accept. Acceptance: `data_coverage("msr_signals")` reports `citation_grounded_pct: ≥0.95` (was 73% at v3.1 start).
- **v3.4-S2** — Red-team + sealing. Per `IS.8(b)`. Threat model from §11 above. 0 class-1 findings required. Author close-out artifact. Acceptance: red-team report attached to close-out; SESSION_LOG appended; MP.1/MP.2 mirrors updated (Claude side only; no Gemini-side artifact per G11).

**Total estimated effort:** v3.1.0 (5–6) + v3.2 (5) + v3.3 (3–4) + v3.4 (2) = **15–17 sessions** across the full v3 cycle. v3.1.0 is the blocking foundation; v3.2 is the rubric-capability backfill; v3.3 is depth refinement; v3.4 closes the loop. Each sub-phase produces a closed, versioned, frontmatter-bearing artifact per `CLAUDE.md §M` cadence.

### v3 isolation model

v3.1.0 ships on main behind a feature flag `MARSYS_FLAG_MCP_V3_ENABLED` (default false at first commit; flipped to true after v3.1.0-S6 sealing). v1's `/api/mcp/execute` route remains live while the flag is false; flipping the flag swaps the registered tool list and the route resolves to the v3 dispatcher. v3.2 / v3.3 / v3.4 don't need a flag — they're data backfill on top of the v3.1 tool surface and are additive to capability, not behavioral. Rollback for v3.1.0 is `flag flip` (sub-1-minute); rollback for v3.2/v3.3 backfills is `data revert via build_id` (the same atomic staging→live swap pattern used for Phase 4C panchang per `CLAUDE.md §E`).

Optionally, v3.1.0 ships on a concurrent-workstream branch (`feature/mcp-v3`) per the Phase O / Chat V2 / Phase 4C precedent — operator's call. Recommendation: concurrent worktree for v3.1.0-S1 through S5; merge to main for S6 sealing. This keeps main green during the substantive rebuild and matches the pattern used for every prior multi-session workstream.

---

## §13 — Open questions (with Opus 4.7's positions)

Sonnet flagged 7 open questions in v3.0 §10. v3.1 settles most and surfaces two new ones.

| # | Question | v3.1 position |
|---|---|---|
| Q1 | Should `holistic_bundle` accept a `depth` parameter (standard vs. exhaustive)? | **Settled by native:** bundles are opt-in orchestration aids; default composition is exhaustive; optional `subset` parameter narrows. No `depth` parameter; the host's decision is between calling a primitive directly (targeted) or calling a bundle (diffuse). §3.2 reflects this. |
| Q2 | Per-tier rate limits? | **Settled:** super_admin 1000 RPM, acharya 200 RPM, client 50 RPM (initial values; tune from observed usage). Per-key concurrency cap on bundle endpoints: 16 / 4 / 4 by tier. Lives in `mcp_tier_limits` table. §6. |
| Q3 | Should `tool_health()` be tier-gated? | **Settled:** visible to super_admin + acharya; hidden from client (clients don't see instrument operational state). Same for `data_coverage`. §3.5. |
| Q4 | Multi-native future for `marsys://chart-overview`? | **Deferred until multi-native lands (post-M10).** When it does, parameterize via URI: `marsys://chart-overview?chart_id=X`. Architecture supports either approach; no decision blocks v3.1. Same for `chart-snapshot`. |
| Q5 | Public-tier (`public_redacted`) — ship in v3.1? | **House-rules variant authored at v3.1.0-S6** (so it's ready when needed) but no key issued. When the operator wants to enable public-tier sharing, key issuance is one config change. §6 supports this. |
| Q6 | Bundle response caching? | **Settled: yes, content-addressable 5-min cache** on bundle results keyed on `hash(query_text + focus_domains + time_window + subset + tier + chart_id)`. Cheap; cuts redundant work in multi-turn conversations. Implement in v3.1.0-S2. |
| Q7 | `validate_response` — mandatory or recommended? | **Resolved by dropping the tool entirely.** Replaced by operator-side audit subsystem (§7.6, perf brief §5). Stronger governance than either of v3.0's framings. |
| Q8 | Web `/consume` chat — eventual convergence? | **Deferred.** v3.1 keeps `/consume` untouched. F.6 (remove `marsys_methodology_block`) recommended for the `/consume` workstream regardless. Future rebuild of `/consume` on v3.1 primitives + a thin synthesis layer is possible but out of scope for v3.x. Flagged for post-v3 consideration. |
| Q9 | Alerting thresholds on perf dashboard? | **Settled: yes, ship with v3.1.0-S5.** Slack + email hooks on `zero_rows_rate` 24h spike, `error_rate` 1h spike, `cite_fabricated` rate > 0.05 over 24h. Configurable per tool. §7 of perf brief. |
| Q10 | Operator-disable a tool from dashboard? | **Settled: yes, ship with v3.1.0-S5.** `tool_enabled` column on a small `tool_registry` table; MCP primitives dispatcher checks before executing. Disable surfaces in `tool_health()` as `status: "disabled"`. Useful for "stop calling X until we fix Y" cases. |
| Q11 | MCP-5 OAuth phase — sooner given multi-tier with external clients? | **v3.1 ships with Bearer + URL-key auth.** OAuth adds complexity (per `MCP_BRIEF §7.5`) and v3.1's tier model is enforceable on Bearer keys. OAuth deferred until first external-client deployment requires it (per-user identity for audit), at which point it becomes a v3.5 (or v4) workstream. |
| Q12 | `synthesize: true` opt-in path (the v2 idea)? | **Dropped per v3.0; v3.1 confirms drop.** No server-side synthesis path on the MCP. If "second voice" inter-rater is wanted, that's the web `/consume` chat's job (it has server-side synthesis). |
| **Q13 (NEW)** | Should v3.1 expose an audit-replay tool to the host (`audit_replay(trace_id)` returning findings for that trace)? | **Settled: yes,** add a Tier 4 observability extension. The host can call `get_trace(trace_id)` which returns findings as part of the step ledger (v3.1 schema change). No new tool — extend `get_trace`'s envelope. Findings show as `audit_findings: [{class, severity, description, attached_at}]`. |
| **Q14 (NEW)** | Streaming for non-bundle long calls — `vector_search` over 100 chunks, `query_ephemeris` over 10-year range? | **Recommend: no streaming for primitives in v3.1.** Primitive latencies are sub-second to low-second; streaming overhead not worth it. If a future primitive becomes long-running, revisit per-tool. |

### §13.1 — Two questions I'm leaving open for native judgment

These two genuinely warrant Marsys's preference:

**O.1 — Should `mcp_predictions` from `/consume` historical chat be backfilled into the MCP-tier PPL?** Sonnet's §9.2 #10 marked this small-if-data-exists. Worth doing if you (a) have the historical predictions accessible and (b) want them subject to the v3.1 calibration loop. If neither, skip and let v3.1 PPL accumulate fresh.

**O.2 — Should v3.1 expose a `holistic_bundle` cache-invalidation tool?** Caching is opt-in (Q6 settled yes). But operator-side: if `msr_signals` is updated mid-day, the 5-min cache becomes stale. Two options: shorter TTL (1 min — cheap, less effective); operator-driven invalidation tool (`/admin/mcp/cache/invalidate`); or pub-sub on `msr_signals` table updates (overkill). Recommendation: 5-min TTL + a one-button "invalidate all" on the dashboard. Decide at v3.1.0-S5.

---

## §14 — One-paragraph TL;DR

v3.1 redesigns the MARSYS-JIS MCP as a pure context-provider with zero server-side LLMs. The host (Claude) reads five resources at session attach — `chart-snapshot` (structured L1 facts, new in v3.1), `chart-overview` (synthesis), `house-rules` (operating discipline, tier-conditioned), `capabilities` (live tool + data health), `school-conventions` (multi-school reference) — and orchestrates 21 tools directly: 10 surgical primitives with the v1 smuggling bugs fixed and defaults raised for depth; 2 composite bundles (`holistic_bundle`, `multi_school_bundle`) repositioned as opt-in orchestration aids preferred when intent is diffuse; 2 raw-asset reads (now including classical texts); 2 observability (with audit findings joined to traces); 2 perf-system tools (`tool_health`, `data_coverage`); 3 writes (`log_prediction`, `record_outcome`, `flag_disagreement` — `score_self_response` folded into `log_prediction`; v3.0's `validate_response` dropped). Three audience tiers (super_admin / acharya / client) enforce only one filter at retrieval (instrument-meta strip for non-super-admin) and push all presentation differences into tier-conditioned `house-rules`. Every response envelope carries `provenance.signal_ids_available[]` as a strict cite-allowlist; an operator-side nightly audit subsystem verifies compliance against recorded traces and surfaces violations to the operator dashboard — a stronger governance closure than v3.0's self-audit. Tier 2 bundles stream over SSE, giving the host progressive feedback during long fan-outs and removing the timeout ceiling for arbitrarily-deep retrievals. Data backfill is sequenced classical-grounding first (v3.2 — restores the rubric capability), then depth (v3.3 — refines the rubric quality), then epistemic refinement + red-team (v3.4 — seals the cycle). The §12 depth-over-tokens directive is baked into every default, every tool description, and every bundle composition rule. The platform's job becomes: deliver the deepest accurate context possible. Pruning is the host's decision. Audit is the operator's job. Synthesis belongs to the host. The sole north star is the quality of output the user sees.

---

*End of MCP_ARCH_v3_PROPOSAL_2026-05-22.md v3.1 (DRAFT, Opus 4.7 regeneration). Paired with `MCP_PERF_SYSTEM_BRIEF_2026-05-22.md` v3.1. Companion handoff in `MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md`. Awaits native review; if accepted, supersedes Sonnet's v3.0 in place and supersedes v1 shipped + v2 proposal entirely.*
