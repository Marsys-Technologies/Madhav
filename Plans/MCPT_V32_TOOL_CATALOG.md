# MCPT v3.2 Tool Catalog
Generated: 2026-05-23 (Phase 3 — Description Standardization)

All 21 tools use `buildToolDescription` from `platform-mcp/src/tools/description_builder.ts`.
Every description: starts with a disambiguator, contains "When to prefer:", ≤ 1200 chars.

---

## Tier 2 — Composite Bundles

| Tool | Description |
|------|-------------|
| `holistic_bundle` | What it does: Performs a parallel 8-tool holistic read of the MARSYS-JIS corpus, fanning out across MSR signals, CGM subgraph, UCN/RM/CDLM vector layers, LEL events, current panchang, and active dasha state. All sub-tools run concurrently with 8-second per-tool timeouts, error isolation, and 5-minute content-addressable caching. When to prefer: FIRST CALL when any synthesis question requires cross-layer context before reasoning. Use the subset param to restrict to specific layers (e.g., subset: ["MSR","DASHA"]). Prefer individual surgical primitives when you need only one data type without synthesis overhead. |
| `multi_school_bundle` | What it does: Runs a parallel multi-school convergence check on an astrological claim — fires cross_school_lookup, per-school evidence queries (Parashara/Jaimini/KP/Tajaka), and reads the most-cited classical text reference, all concurrently. All four school evidence sets fully populated (MCPT v3.3); results cached 5 minutes. Valid categories: parashara, jaimini, kp, tajaka. When to prefer: Use when the question explicitly concerns whether all four schools agree or disagree on a claim. Prefer holistic_bundle when you want multi-school data synthesized alongside the native's actual signals. Prefer cross_school_lookup directly for a lightweight stance-only check without per-school evidence. |

---

## Tier 3 — Surgical Primitives

| Tool | Description |
|------|-------------|
| `query_chart_facts` | What it does: Queries the chart_facts table with structured filters (category, planet, house, as_of_date) and returns raw fact rows without synthesis. category is required; planet/house/as_of_date are optional filters; limit defaults to 50. 2,717 rows across 27 categories. Valid categories: house, dasha_chara, planet, dasha_vimshottari, saham, sensitive_point, birth_metadata, strength_extra, yoga, dasha_yogini, deity_assignment, shadbala, ashtakavarga_sav, kp_cusp, navatara, panchang, cusp, arudha_occupancy, bhava_bala, chandra_placement, mrityu_bhaga, longevity_indicator, arudha, aspect, chalit_shift, kp_planet, special_lagna, strength, upagraha, ashtakavarga_bav, kakshya_zone, mercury_convergence, ashtakavarga_pinda, ishta_kashta, kp_significator, varshphal, avastha. When to prefer: Use for single fact lookups ("What is Saturn's shadbala?", "Which planets are in house 7?"). Prefer query_signals for MSR signal corpus data. Prefer holistic_bundle when synthesis or multi-tool retrieval is needed. |
| `query_signals` | What it does: Queries the MSR signal corpus (499+ astrological signals) with structured filters (domain, planet, dasha_lord, min_confidence, forward_looking) and returns raw signal rows without synthesis. 499+ signals across all Jyotish domains. When to prefer: Use for "give me all forward-looking career signals" style queries. Prefer holistic_bundle when interpretation or cross-domain synthesis is also needed. Prefer query_chart_facts for raw chart-fact rows rather than MSR signals. |
| `query_dasha_periods` | What it does: Returns the Vimshottari dasha schedule for the native's chart — Mahadasha, Antardasha, Pratyantar — with exact start/end dates, bypassing synthesis. Input: at (single ISO date), range ({start, end}), or omit both for the full sequence. When to prefer: Use for "what dasha is active on date X?" without synthesis overhead. Prefer holistic_bundle when you also need interpretation of what the period means for the native. Prefer query_chart_facts with category "dasha_vimshottari" for raw DB rows without the structured period wrapper. |
| `query_panchanga` | What it does: Returns the 5 limbs of the Vedic day (tithi, vara, nakshatra, yoga, karana) plus hora, choghadiya, muhurat windows, and inauspicious periods (Rahu Kalam, Gulika, Yamaghanta) for any date. Pre-computed panchanga_daily table: 73,414 rows covering 1900–2100. When to prefer: Use for date-specific panchang questions ("What is today's nakshatra?", "When is Rahu Kalam?"). Prefer holistic_bundle when you also need chart-level interpretation of the panchang for the native. Input: date required (YYYY-MM-DD); observer optional lat/lon (defaults to Bhubaneswar). |
| `query_ephemeris` | What it does: Returns date-indexed planetary positions (sign, degree, nakshatra, retrograde status, speed) from the ephemeris_daily table for a given planet and date range. Swiss Ephemeris output; max ~1 year range recommended per call. Valid categories: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu. When to prefer: Use for "What sign was Saturn in during Q1 2025?" or retrograde status checks. Prefer query_transit_event for "when does X enter Y?" searches. Prefer holistic_bundle when positional data needs chart synthesis. |
| `query_transit_event` | What it does: Searches ephemeris_daily for specific transit events (sign ingresses, conjunctions, degree crossings) within a date range and returns exact event dates with before/after planet state. When to prefer: Use for "When does Saturn enter Aquarius?" style questions — event-date lookup rather than daily scan. Prefer query_ephemeris for day-by-day position data over a range. Prefer holistic_bundle when the transit's meaning for the native's chart is also needed. |
| `lel_query` | What it does: Queries the Life Event Log (LEL) — 36 verified life events, 5 period summaries, 6 chronic patterns — with optional category, date range, and significance filters. Returns raw event records as ground-truth data for calibration and backtesting. M4 ground-truth spine; confidence up to 0.89. When to prefer: Use to retrieve verified life events ("what career events happened 2015–2020?"). Prefer holistic_bundle when interpretation in light of current chart state is also needed. Pair with query_dasha_periods to correlate events with active dasha lords. |
| `vector_search` | What it does: Semantically searches the RAG chunk corpus (MSR signals, UCN, CDLM, domain reports, L1 facts) using Vertex AI 768-dim embeddings and returns top-K chunks ranked by cosine similarity. 4,589+ RAG chunks across all synthesis layers. Valid categories: l1_fact, ucn_section, msr_signal, cdlm_cell, domain_report, rm_element. When to prefer: Use for "find content similar to X" queries where you do not know the exact signal ID. Prefer query_signals for structured MSR lookups with exact domain/confidence/dasha_lord filters. Prefer holistic_bundle when semantically similar content needs to be synthesized into an answer. |
| `get_cgm_subgraph` | What it does: Traverses the Cross-Domain Linkage Matrix (CGM) from a seed node and returns a subgraph of connected signals and domains up to N hops, with typed edges (amplifies, contradicts, shares_ruler, temporal_co-activation). CGM encodes cross-domain linkages across all 573 MSR signals. When to prefer: Use to map cross-domain signal topology ("what signals are connected to SIG.MSR.234 within 2 hops?"). Prefer holistic_bundle when cross-domain connections need to be synthesized into a holistic answer. Prefer query_signals for flat signal lookups without graph traversal. |
| `cross_school_lookup` | What it does: Checks an astrological claim against Parashara, Jaimini, KP, and Tajaka and returns where each school agrees, disagrees, or is silent, with a convergence score (0–1). All four school evidence sets fully populated (MCPT v3.3). Valid categories: parashara, jaimini, kp, tajaka. When to prefer: Use when the question is explicitly about multi-school convergence on a rule or claim. Prefer multi_school_bundle when you also want per-school evidence queries and classical text references. Prefer query_signals to find signals already tagged with school convergence metadata. |

---

## Tier 4 — Raw-Asset Reads

| Tool | Description |
|------|-------------|
| `read_asset` | What it does: Returns the raw markdown of a canonical MARSYS-JIS artifact by its canonical_id (MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE), with optional section filter. Valid categories: MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE. When to prefer: Use when you need the full text of a synthesis layer document (e.g., full CGM for a graph overview, full FORENSIC for a birth-data audit). Prefer query_signals or query_chart_facts for targeted fact lookups within documents. Prefer holistic_bundle for any question requiring synthesis across multiple documents. |
| `read_classical_text` | What it does: Retrieves excerpts from the MARSYS-JIS classical corpus (BPHS, KP Reader, Jaimini Sutram, Tajaka Neelakanthi) ranked by semantic similarity to a query. Vertex AI 768-dim embeddings; limit 1–20 excerpts per call. Valid categories: BPHS, KP_READER, JAIMINI, TAJAKA. When to prefer: Use when the question requires a classical textual citation ("what does Parashara say about Ketu in the 12th?"). Prefer vector_search for cross-layer semantic retrieval including MSR signals and LEL data. Prefer query_chart_facts or query_signals for structured fact lookups that do not require quoting. |

---

## Tier 5 — Observability + Perf

| Tool | Description |
|------|-------------|
| `get_trace` | What it does: Returns the full query_trace_steps ledger for a prior MCP query — every pipeline stage (classify, compose_bundle, each retrieval tool, synthesis, done) with inputs, outputs, latencies, and token estimates per step. When to prefer: Use get_trace after a holistic_bundle call to debug what happened, verify which tools fired, inspect the synthesis prompt, or understand per-stage latency. Use for differential analysis (plan → edit → execute → compare traces). Do NOT use get_trace to answer chart questions — that is holistic_bundle's job. |
| `list_recent_queries` | What it does: Returns recent MCP call history for the current API key — each entry includes trace_id, tool name, source (mcp or mcp_primitive), timestamp, and a brief query summary. When to prefer: Use when you want an audit of what this API key has called recently, or need to find a trace_id from a prior session for follow-up investigation with get_trace. Do not use for answering chart questions — use holistic_bundle for that. |
| `tool_health` | What it does: Returns aggregate health metrics for all registered MCP tools over the last N hours (default 24h) — call counts, error rates, average latency, audit finding counts, and active caveats. When to prefer: Use to understand the operational state of the MCP server: which tools have elevated error rates, which have pending audit findings. Essential for operator debugging. Do NOT use to answer chart questions — use query_signals or holistic_bundle for that. Available: super_admin + acharya only. client tier = 403. |
| `data_coverage` | What it does: Returns expected vs actual row counts per category for all tools, including backfill status (KP, Tajaka, Shadbala, Ashtakavarga, Upagraha, Bhava-Bala) and active tool caveats from mcp_audit_findings. When to prefer: Use data_coverage before calling a tool that relies on backfilled data (query_chart_facts with category kp_cusp, varshphal, shadbala, etc.) to verify data is present. Use tool_health for operational metrics; use data_coverage for data availability. Available: super_admin + acharya only. client tier = 403. |

---

## Tier 6 — Write Tools

| Tool | Description |
|------|-------------|
| `log_prediction` | What it does: Logs a prospective prediction to the MARSYS-JIS Prospective Prediction Log (PPL) with domain, horizon, confidence, and falsifier BEFORE any outcome is observed. Required fields: domain, horizon, prediction_text, confidence, falsifier. When to prefer: FIRST CALL when you are making any time-indexed, testable astrological prediction — this is a governance obligation, not optional. Log before discussing outcomes; PPL discipline requires predictions are logged first. Use record_outcome later when the outcome is observable. |
| `record_outcome` | What it does: Records an observed outcome against a prior PPL prediction (by prediction_id from log_prediction), closing the prediction-outcome loop required by the Learning Layer discipline. When to prefer: Use ONLY after an outcome is observable and you have factual evidence of what occurred. Do not call speculatively or before the horizon date passes. Partial matches record with verified=false and explanation in notes. |
| `flag_disagreement` | What it does: Logs a formal disagreement to the MARSYS-JIS governance register (mcp_disagreements table) when you detect a contradiction between MSR signals and FORENSIC L1 data, between two synthesis outputs, or any irresolvable conflict. When to prefer: Use when you encounter a factual L1 conflict, inter-session output conflict, or structural scope issue that cannot be silently resolved. This is a formal governance channel — the native reviews entries. Do NOT use for minor uncertainty; only for genuine, irresolvable conflicts. Available: super_admin only. acharya/client tier = 403. |

---

## Implementation Notes

- **Builder**: `platform-mcp/src/tools/description_builder.ts` — `buildToolDescription()` function
- **Catalog**: `platform-mcp/src/tools/catalog.ts` — `CATALOG` export for lint testing
- **Lint test**: `platform-mcp/test/tool_descriptions.test.ts` — `MCPT v3.2 Phase 3 — Tool description lint gate` describe block
- **Lint rules**: disambiguator prefix, "When to prefer:" present, ≤ 1200 chars, non-empty (>50 chars)
- **All 98 tests pass** including 5 new lint tests (4 per-rule + 1 catalog coverage check)
