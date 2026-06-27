---
canonical_id: RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY
version: 1.0
status: DRAFT
created: 2026-06-27
author: Cowork (synthesis of D-GROUNDTRUTH deliverables 1–3) — for native Abhisek Mohanty
classification: D-GROUNDTRUTH deliverable (4 of 4) — the convergence
parent: RETRIEVAL_SYSTEM_DESIGN_APPROACH (§B.3, §B.4)
inputs:
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC (deliverable 1 — LLM-facing best practices)
  - RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX (deliverable 2 — asset comprehension + 8 archetypes)
  - RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL (deliverable 3 — Vedic reading hierarchy; expert-validation pending)
feeds: RetrievalSurface contract (D1), graph design (D4), per-asset fan-out (D5)
changelog:
  - v1.0 (2026-06-27): Initial tool-topology framework — decision rules for single/multi/umbrella-thread tools, the dedup+completeness+retrievability guarantees by construction, conformance to provider best practices, and worked examples per archetype. Synthesizes D-GROUNDTRUTH deliverables 1–3.
---

# RETRIEVAL GROUND-TRUTH — TOOL-TOPOLOGY DESIGN FRAMEWORK (v1.0)

> **What this is.** The convergence of the three D-GROUNDTRUTH studies into the **decision framework for the
> architecture of the retrieval tools over the assets**: when an asset is one tool, multiple tools, or an
> umbrella/thread tool with drill-down children; how de-duplication, completeness, and high retrievability are
> guaranteed *by construction*; and how every tool conforms to the provider best-practices spec. It is
> deliverable 4 of 4 of D-GROUNDTRUTH and the direct input to the RetrievalSurface contract (D1). It is the
> answer to the native's central question: *do we have one tool per asset, multiple, or umbrella tools?*

---

## §1 — The governing answer (stated upfront)

**Tool topology is NOT one-tool-per-asset.** It is decided by a 2-axis rule: **(archetype × traversal-level)**.
The asset's *retrieval archetype* (what kind of data it is — from the Asset Matrix) and the *traversal level
it serves in a reading* (from the Traversal Model) jointly determine its tool shape. The result is a small
set of **umbrella entry tools** that a reading hits first, fanning out into **drill-down leaf tools** and a
**graph traversal tool**, with **prose-retrieval** and **temporal** families — collapsing ~70 assets into a
**workflow-shaped tool set (~10–15 active), not a 70-tool API mirror** (which every provider's docs warn
against).

This is not a new invention *at the doctrine level*: it generalizes the project's already-doctrinal
`query_ucd`-first → drill pattern (from `L2_BODHA_RETRIEVAL_STRATEGY`), which is itself aligned with the
classical "orient → domain → factor → derive → time → cite" reading sequence.

> **[v1.3 code-validation correction — `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION §1.4 / G1`]** In CODE, only
> `query_ucd` actually exists; the drill tools the doctrine names (`query_zoom` / `lens` / `domain-evidence`)
> and the `lel_enabled` toggle are **doc-only — TO-BUILD**. So this topology is implemented almost from a
> clean slate (aligned to doctrine, not yet realized). The good news: `get_cgm_subgraph` and `vector_search`
> already exist as real-but-unwired code (worked example 4/5 can adopt them). Treat every umbrella/drill tool
> below as a build target unless explicitly noted as existing.

---

## §2 — The topology decision rules

For each asset (or asset cluster), apply in order:

**Rule R1 — Classify by archetype** (from Asset Matrix §5): flat-fact / prose-citation / rich-relational /
graph-traversal / cross-domain-contradiction / temporal / orientation-digest / calibration.

**Rule R2 — Classify by traversal level served** (from Traversal Model §2): L-ORIENT / L-DOMAIN / L-FACTOR /
L-DERIVATION / L-TIMING / L-SOURCE / (remedy) / (quality).

**Rule R3 — Map (archetype × level) → tool shape:**

| Archetype | Typical level | Tool shape | Rationale |
|---|---|---|---|
| Orientation-digest | L-ORIENT | **Umbrella entry tool** (one), returns de-duplicated gestalt + drill pointers | reading always orients first; this is the primary surface |
| Rich-relational + lenses | L-DOMAIN | **Umbrella tool with drill-down children** | a domain is framed broad then drilled; multi-vantage reconciled inside |
| Flat-fact | L-FACTOR / leaf | **Single leaf tool** (often parameterized, not one-per-table) | exact keyed lookup; consolidate sibling facts under one `action`/param tool |
| Graph-traversal | L-DERIVATION | **One dedicated traversal tool** (neighbors/paths/clusters/contradictions) | distinct shape; the superhuman-value surface |
| Cross-domain-contradiction | L-DERIVATION / L-DOMAIN | folded into the domain umbrella + the graph tool | contradictions surface during framing and derivation |
| Prose-citation | L-SOURCE / remedy | **Hybrid-retrieval tool** (BM25+dense+rerank) | semantic + exact-term over verse/rule corpora |
| Temporal | L-TIMING | **Time-keyed tool family** | classical method separates static from timing |
| Calibration | (quality) | **Quality/serve tools** (+ LEL toggle plumbed through) | trust metadata + serve-time overlay |

**Rule R4 — Consolidate, don't mirror.** Sibling flat-fact assets that a reading consults together collapse
into ONE parameterized tool (e.g. one "graha condition" tool spanning position+dignity+strength+avasthā), per
the provider guidance to keep the active tool set <~20 and consolidate related operations. One-tool-per-asset
is the *exception* (a genuinely standalone asset), not the rule.

**Rule R5 — Umbrella tools own multi-vantage reconciliation.** Because the classical method reads each matter
from house+kāraka+varga and reconciles, the umbrella/domain tools return the *reconciled* multi-vantage view
(one entry, perspectives attached), never forcing the LLM to issue N calls and de-dup itself.

**Rule R6 — Drill happens by reference.** Leaf/graph/prose tools are invoked *after* an umbrella call, keyed
by the identifiers the umbrella returned (signal_id / fact_id / chunk_id / node_id), so each fact resolves
once. This is the structural enforcement of F1 (below).

---

## §3 — The three guarantees, by construction

### §3.1 — De-duplication (F1: reference-don't-repeat)
- **Primary surface = the umbrella/digest tools**, which already merge each signal once with its perspectives
  attached (msr salience + cdlm linkage + cgm centrality + ucd tier on ONE entry). The LLM is steered to call
  these first, not five raw asset tools.
- **Drill tools return references + delta**, not whole re-stated facts; the orchestrator (MARO) resolves each
  reference once during composition.
- **Enforcement:** the same fact_id/signal_id appearing N× in one assembled answer is a FAIL (the existing B6
  test). Dedup is a property of the topology (umbrella-first + reference-drill), not of LLM discipline.

### §3.2 — Completeness (full-enumeration parity)
- Tools expose the WHOLE of each asset (salience is a returnable/sortable field, never a hidden filter — per
  `feedback_bodha_b1_full_enumeration_parity`); the weak tail is reachable via pagination/`response_format`.
- An umbrella tool's drill-pointers MUST cover every child fact (no silent truncation of the enumerable set);
  truncation is paginated + signalled, never dropped.
- **Enforcement:** a coverage gate — every `bodha_*` table, every `source_subsystem`, every cross-subsystem
  edge, every discovery reachable through some tool path; nothing orphaned.

### §3.3 — High retrievability (hybrid + structured)
- Prose-citation tools use hybrid retrieval (BM25 + dense embeddings + RRF + cross-encoder rerank + top-20 +
  Contextual-Retrieval preprocessing) — never pure-dense (which silently misses Sanskrit terms / asset IDs).
- Structured cross-layer hydration via `constituent_facts_array`→L1 and `classical_sources_jsonb`→L0 so every
  judgment retrieves WITH its value and its citation (F3 layer-resolution-DOWN).
- Graph tool exposes both metric-ranked entry (pagerank/centrality) and semantic entry (768-dim node vectors).

---

## §4 — Conformance to the LLM-provider spec (the LLM face)

Every tool in the topology MUST satisfy the deliverable-1 obligations, notably:
- **Workflow-shaped + consolidated + <~20 active** (all providers); namespaced; names `[A-Za-z0-9_.]`,
  **no `-`** (Gemini), snake_case/dot.
- **Detailed intent-rich descriptions** (the #1 selection lever for all four families).
- **`outputSchema` + `structuredContent` + serialized-text fallback** (MCP); **`response_format`/verbosity
  enum** (concise/detailed); cursor pagination; default token cap.
- **UUIDs resolved to human-meaningful names** in outputs (chart_id and signal_id are opaque UUIDs — measured
  to hurt precision).
- **Schemas authored to the safe intersection** (`type`/`properties`/`required`/`enum`/`items`/`description`,
  `additionalProperties:false`, all-required + null-unions for strict compatibility); value constraints in
  descriptions + validated in code.
- Served identically through both channels via MARO so MCP↔chat cannot drift; the same tool definitions, the
  same query logic.

---

## §5 — Worked examples (one per major shape)

1. **Whole-chart orientation (umbrella, L-ORIENT).** `get_chart_orientation(chart_id, lel_enabled=false,
   response_format)` over **bo_samvada (UCD)** + chart-defining bo_laksana signals. Returns the gestalt
   (Lagna/Moon/Sun frame, top yogas, chart-defining signatures) as de-duplicated entries each carrying
   {salience, domains, centrality, tier} + drill-pointers (signal_ids). *First call of nearly every reading.*

2. **Domain framing (umbrella-with-children, L-DOMAIN).** `get_domain_reading(chart_id, domain, lel_enabled,
   response_format)` over **bo_drishti (lens)** + **bo_sangati (CDLM)**. Returns the reconciled multi-vantage
   view of the domain (house + kāraka + varga merged), convergences and contradictions flagged, each entry a
   single signal with perspectives + drill-pointers. Honors R5.

3. **Factor drill (consolidated leaf, L-FACTOR).** `get_graha_condition(chart_id, graha, ayanamsha?)` over
   **ga_positions + ga_condition + ga_strength + ga_structural** (R4 consolidation — one tool, not four).
   Exact keyed lookup; returns position, dignity, shadbala, avasthā, key configs with `fact_id`s.

4. **Graph traversal (dedicated, L-DERIVATION).** `traverse_chart_graph(chart_id, from_signal?, mode∈
   {neighbors,paths,convergence,contradictions}, depth, filter)` over **bo_bimba + bo_karanajala +
   bodha_contradictions**. The superhuman-value tool; returns subgraph/paths/clusters keyed by signal_id.

5. **Classical grounding (hybrid retrieval, L-SOURCE).** `search_classical_basis(query, topic?, school?,
   top_k)` over **bg_texts + bg_rules + bg_yogas** with BM25+dense+rerank. Returns verse/rule chunks with
   citations; also reachable by reference from any signal's `classical_sources_jsonb`.

6. **Timing (time-keyed family, L-TIMING).** `get_active_periods(chart_id, window, level)` over **ga_dashas
   (+ ga_tajaka/ga_sade_sati; L3 ka_* when built)**. Time-window/daśā-period keyed; separate from static tools.

7. **Remedy (prose+relational).** `get_remedies(chart_id, problem|signal_id, tradition?)` over **bo_upaya
   (RM) + bg_remedies**, keyed to the signal/resonance the problem maps to.

8. **Quality/trust (calibration).** `get_synthesis_confidence(chart_id)` over **bo_pramana_mapa** (+ L5 mi_*
   when built); the LEL toggle is plumbed through every tool above, not a separate tool.

This is ~8 umbrella/family tools + a handful of consolidated leaves ≈ the target <~20 active tools, covering
all ~70 assets — the workflow-shaped surface the providers prescribe, mirroring how a reading is actually done.

---

## §6 — Open items handed to downstream waves

- **D1 (contract):** encode (archetype × level) → shape as the RetrievalSurface contract every asset declares.
- **D4 (graph):** detailed design of `traverse_chart_graph` (store, Text2Cypher vs API, PPR/budget primitive).
- **D5 (fan-out):** apply R1–R6 to every one of the ~70 assets; produce the full tool roster; resolve the
  two-catalog drift (seed vs manifest; 137 vs 117) so the roster has a single source of truth.
- **Validation:** the Traversal Model (§3 input) is acharya-validation-pending; topology that depends on its
  ordering carries the same provisional status until reviewed.

*End of RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY v1.0 — D-GROUNDTRUTH deliverable 4 of 4. Synthesizes the LLM
provider spec, the asset matrix, and the (expert-validation-pending) traversal model.*
