---
artifact: RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT
canonical_id: RETRIEVAL_PRODUCTIVITY_PLAN
version: 0.1-DRAFT
status: DRAFT_PLANNING
authored_by: Claude (Cowork session 2026-04-29 retrieval analysis)
authored_for: Native review + native decision on Phase 11C scope
companions:
  - platform/scripts/retrieval_diagnostic_probes.sql
intended_disposition: |
  After native review, this draft becomes either:
  (a) Phase 11C plan (committed to PHASE_B_PLAN as M2-supportive infra),
  (b) a deferred backlog item logged in ONGOING_HYGIENE_POLICIES §I,
  or (c) a CLAUDECODE_BRIEF series.
status_note: |
  This is NOT yet a CURRENT canonical artifact. It does not appear in
  CAPABILITY_MANIFEST and is not bound by the mirror-discipline rule
  until promoted to status: CURRENT.
---

# Retrieval Productivity Plan v0.1 (DRAFT)

## §0 — Why this document exists

The native observed in the trace UI on 2026-04-29 that only L1 and L2.5 content reaches the LLM during synthesis. Discovery Layer registers (L3.5) appear thin or absent in many queries. L3 (Domain Reports), L4 (Remedial Codex), and L5 (Temporal Engines) are not visible at all. The native asked for two deliverables:

- **Task 1 (prerequisite)**: a per-asset diagnosis — what would make each of the platform's data assets actually productive in their current state, going to the actual data rather than the configuration files.
- **Task 2**: how to inject LLM intelligence into per-asset query construction so each tool retrieves the optimum content available to it.

Task 1 is a hard prerequisite for Task 2 — an LLM planner is useless if the underlying assets are starved or the tools that read them are mis-wired.

This plan is grounded in (a) direct reads of FORENSIC v8.0, MSR v3.0, UCN v4.0, CDLM v1.1, RM v2.0, CGM v9.0, all four Discovery registers, and the project source code (composition_rules.ts, rule_composer.ts, all 10 retrieval-tool files); and (b) the Cloud SQL volumetric checks the native ran on 2026-04-29. A companion SQL probe script (`platform/scripts/retrieval_diagnostic_probes.sql`) is provided to validate hypotheses against live database state before any code work begins.

## §1 — Findings: what the trace observation actually means

### §1.1 The "L1 + L2.5 only" pattern has two independent chokepoints

**Chokepoint A — the composition rules.** `platform/src/lib/bundle/composition_rules.ts` exports six rules that decide which canonical artifacts enter the bundle: `floorRule` (always_required entries), `interpretiveRule` (UCN + CDLM + RM, fires on interpretive/cross_domain/holistic), `predictiveRule` (LIFE_EVENT_LOG + SADE_SATI_CYCLES_ALL, fires on predictive/forward_looking), `discoveryRule` (the four register .md files, fires on discovery/holistic), `holisticRemainderRule` (all Tier-1, fires on holistic only), and `crossNativeMetaRule` (a placeholder). Three layers are not addressed by any rule: L3 Domain Reports (the nine REPORT_* files exist on disk and are registered in CAPABILITY_MANIFEST, but no rule references them by canonical_id pattern), L4 Remedial Codex (four files on disk, **not registered in the manifest**), and L5 Temporal Engines (three files on disk, **not registered in the manifest**). Additionally, a `query_class='remedial'` query gets only the floor bundle because no rule fires for that class.

**Chokepoint B — the retrieval tools.** Even when a composition rule names an artifact, the bundle entry the rule emits is metadata only — `{ canonical_id, version, content_hash, token_count, role, source }`. The actual content reaches the LLM only through retrieval tools at the `retrieve(parallel)` stage. The 10 tools cover L1 (`vector_search` over 102 FORENSIC chunks), L2.5 (`msr_sql`, `cgm_graph_walk`, the stub `query_msr_aggregate`), L3.5 (`pattern_register`, `resonance_register`, `cluster_atlas`, `contradiction_register`), L5 partially (`temporal` calls a sidecar but only for today's transits / ephemeris), and meta (`manifest_query`). **There is no tool that reads L3 Domain Reports, no tool that reads L4 Remedial Codex, no tool that reads L5 timeline files.** Composition success without a matching tool is invisible to the LLM.

The two chokepoints multiply: even if Chokepoint A is fixed by adding rules for L3/L4/L5, the LLM still won't see their content unless Chokepoint B is also fixed by adding tools that fetch it.

### §1.2 The token-budget claim is currently false

Agent A reported that L3 reports get dropped during token-budget enforcement. This is wrong. Reading `rule_composer.ts:117–160`, `enforceTokenBudget` reads `token_count` from each asset entry, and the manifest schema does not currently populate that field — every entry resolves to `0`. Total bundle tokens compute as `0 ≤ maxTokens`, the early return triggers, and degradation is a no-op. The L3 absence in synthesis is therefore not a budget casualty; it is a composition-rule omission compounded by the missing retrieval tool. The token-budget concern is real architecturally but inert today.

### §1.3 `classify` and `compose_bundle` look empty in the trace because they are metadata-only

The native's "they're not contributing" observation is a UI artifact. `classify` emits a trace step with `step_type='deterministic'`, `data_summary={result, confidence}`, and `payload={}`. `compose_bundle` emits the same shape with `data_summary={result: 'N bundles · M tools'}`. Both stages produce real output (a routing decision and a bundle metadata list, respectively); neither produces `payload.items` because they don't retrieve content. The TracePanel renders `payload.items` as the per-step inspector content, so for these two stages the inspector is empty. The fix is presentational, not functional: render `data_summary` prominently for stages with empty `payload`, and label these stages explicitly as "metadata-only" so the user doesn't misread them as broken. Optional: have `compose_bundle` include the bundle's canonical_id list in its trace payload so the user can see which artifacts were composed in.

### §1.4 `classical_factual` is a column, not a stage

`classical_basis` is a column on the `msr_signals` table, holding the BPHS / Saravali / Phaladeepika citation per signal. There is no pipeline stage by that name. The native's mental model of "classical_factual is not contributing" is most likely a conflation: either (a) the user expected an `L1_classical_factual` retrieval tool to exist (it does not), or (b) the user is reading the `data_summary` field of `classify`/`compose_bundle` and seeing it categorize the query as `factual` while no factual-only tool exists. Resolution: treat this as a request to expose the `classical_basis` column more directly to the LLM — see §2.1 fix F1.6.

### §1.5 The `query_class='remedial'` gap

`router.ts` emits `remedial` as one of eight `query_class` values, but no composition rule fires for it. A remedial query therefore receives only the floor bundle (FORENSIC + CGM, by manifest `always_required: true`) and whatever the retrieval tools yield against an empty domain set. There is no Remedial Codex content in the LLM context, and there is no remedial retrieval tool. This is a 30-minute fix on the composition side and a 2-day fix on the retrieval side.

## §2 — Task 1: per-asset productivity plan

Each subsection below names an asset, states current state from source-of-truth, identifies the bottleneck class (i: classifier input / ii: data thinness / iii: filter rigidity / iv: data shape mismatch), specifies the surgical fix, and gives an acceptance criterion. Effort sizes are S (≤ 1 day), M (1–3 days), L (1+ week). All file paths are repository-relative.

### §2.1 `msr_sql` — workhorse, slightly under-served by classifier

**Current state.** Reads `msr_signals` with `WHERE native_id='abhisek_mohanty' AND ($2 IS NULL OR domain=ANY($2)) AND ($3 IS NULL OR planet=ANY($3)) AND ($4 IS NULL OR is_forward_looking=$4) AND confidence>=$5`, ORDER BY `confidence*significance DESC`, LIMIT 100. Source has 499 signals; ETL has confirmed 499 rows in DB. Classifier emits `domains[]` reliably; `planets[]` and `forward_looking` less reliably.

**Bottlenecks.** (i) classifier under-fills `planets[]` for queries that name a planet implicitly ("authority struggles" → Saturn); (iii) the WHERE clause does not expose `signal_type`, `temporal_activation`, `valence`, or `entities_involved` even though MSR carries these fields per signal. PROBE 2 in the diagnostic SQL will confirm whether the columns are populated in DB or only in the source `.md`.

**Fixes.**

- **F1.1 (M, classifier).** Have the classifier (or, better, the per-tool planner — see §3) extract `planet_hints` from query text. A query like "what does my career rise look like in Saturn dasha" should yield `planets=['saturn', 'mercury']` (Saturn from explicit mention, Mercury because the chart's career-significator is Mercury — this requires chart-aware extraction).
- **F1.2 (S, schema + filter).** Expose a `signal_type` filter. The source MSR has 15 signal_type values (yoga, convergence, dignity, jaimini-pattern, divisional-pattern, transit-activation, dasha-activation, aspect, house-strength, nakshatra-signature, panchang, sensitive-point, tajika-pattern, kp-signature, contradiction). A query about yogas should pull only `signal_type='yoga'` rows; a query about dignities should pull `signal_type='dignity'`. Add the column filter in `msr_sql.ts` and the column to the `msr_signals` ETL if not already present.
- **F1.3 (S, filter).** Expose `temporal_activation` filter. For predictive queries, narrow to `temporal_activation IN ('transit-triggered', 'dasha-windowed', 'annual')`; for character/structural queries, narrow to `'natal-permanent'`.
- **F1.4 (S, filter).** Expose `valence` filter for tone-shaped queries ("what supports my health" → `valence='benefic'`).
- **F1.5 (M, hidden structure).** Index the divisional-chart parallel signals (D9, D27, D60 across the same planet) so a query about "my Mercury" can pull all four divisional projections of Mercury simultaneously. This requires either (a) a `divisional_chart` column on `msr_signals` ETL'd from the source's signal_id pattern, or (b) a relationship table linking signals that describe the same entity across divisional layers.
- **F1.6 (S, classical_basis exposure).** Surface the `classical_basis` field in the tool's result rows. Currently the column is queryable but not in the SELECT. A query about "what classical text grounds this" needs the citation. Add `classical_basis` to the SELECT and to the result schema.

**Acceptance criterion.** A test set of 30 representative queries shows median signals retrieved/query rises ≥ 30%, and no test query that names a `signal_type` (e.g. "show me the yogas") returns mixed-type results.

### §2.2 `vector_search` — L1-only today; expand to all narrative layers

**Current state.** Cosine search over 102 L1 chunks (FORENSIC v8.0). Vertex `text-multilingual-embedding-002`, 768d. Feature-flagged `VECTOR_SEARCH_ENABLED`. Currently the only semantic-search path into the corpus.

**Bottlenecks.** (iv) data shape mismatch: the most narrative-rich content (UCN's 17K+ words of integrated synthesis, CDLM's 82 cells of cross-domain mechanism prose, RM's 28 elements of practical guidance, the nine L3 domain reports, the L4 codex) is not in the embedding store. Embedding-based retrieval is therefore confined to the technical-classical L1 register and misses the life-event vernacular of L2.5/L3.

**Fixes.**

- **F2.1 (M, data).** Chunk and embed L2.5 source files. New `doc_type` values: `l25_ucn`, `l25_cdlm`, `l25_rm`, `l25_msr_narrative` (NB: MSR's structured signals are already in `msr_signals` table; this is for the prose around them). Run the existing chunker over each .md file with appropriate boundaries (UCN has clear `## Part` and `### Section` boundaries; CDLM is cell-grid; RM is element-block; CGM is node-block). Re-embed with the same Vertex model.
- **F2.2 (S, filter).** Add a `doc_type` filter and `layer` filter to `vector_search.ts`. A query class of `interpretive` should retrieve from `layer IN ('L1','L2.5')`; a query class of `factual` should narrow to `layer='L1' AND doc_type='l1_fact'`.
- **F2.3 (M, data).** Chunk and embed the nine L3 domain reports as `doc_type='l3_domain_report'`, with a per-chunk `domain` tag matching the report's domain (career, financial, relationships, etc.). This is the most leverage step: the L3 reports are acharya-grade narrative built explicitly for synthesis, and currently the LLM cannot see them.
- **F2.4 (S, data).** Chunk and embed the four L4 Remedial Codex files as `doc_type='l4_remedial'`.
- **F2.5 (M, hybrid).** Add a BM25 keyword score branch fused with the vector score. Classical jargon ("Mahapurusha", "Vargottama", "Neecha Bhanga") embeds noisily; keyword overlap is decisive. Score = `α * vector_cosine + (1-α) * bm25_score`, α tuned on the eval set (§3.5). Existing pgvector + a BM25 index via the `pg_trgm` extension or a small text-search column is enough — no new infra.

**Acceptance criterion.** After F2.1+F2.2+F2.3, `rag_chunks` count rises from 102 to (estimated) 800–1500. A query like "explain how Mercury supports my career path" must retrieve at least 3 L2.5 chunks (UCN Part I or RM.01 or CDLM career→wealth) in the top-10.

### §2.3 `cgm_graph_walk` — the most starved tool; multiple gaps stacked

**Current state.** Reads `l25_cgm_nodes` (234 rows) and `l25_cgm_edges` (127 rows: 21 valid, 105 orphan, 1 self_loop). BFS from `graph_seed_hints`, depth 1–3, edge-type filter optional, `WHERE status='valid'`.

**Bottlenecks.** All four classes simultaneously, which is why this tool currently contributes ~nothing to most queries.

- (i) Classifier rarely populates `graph_seed_hints`. The current router prompt does not have any example or instruction that maps natural-language entities to CGM node IDs (`PLN.MERCURY`, `HSE.7`, `YOG.SARASWATI`, `KRK.C8.DARA`, etc.).
- (ii) Of the 339 typed edges asserted in CGM v9.0 source, only 127 are in DB and only 21 are valid. PROBE 4 will confirm whether the 105 orphans target `UCN.SEC.*` nodes that were never ingested, and whether the gap from 339 to 127 is a manifest-file gap (multiple cgm_*_edges_manifest.json files exist; only one was ingested).
- (iii) `edge_type_filter` is exposed but never set by the classifier, so most queries traverse all edge types and dilute relevance.
- (iv) The 21 valid edges concentrate in 5 types (DISP, NAK_LORDSHIP, ASPECTS_3RD, ASPECTS_4TH, ASPECTS_8TH). The other 10 edge types (YOGA_MEMBERSHIP, DASHA_ACTIVATION, DIVISIONAL_CONFIRMATION, KARAKA_ROLE, etc.) have zero valid edges in DB — meaning the source's richest relationships are inaccessible to BFS.

**Fixes.**

- **F3.1 (L, data).** Close the 339→127 gap. Inspect `035_DISCOVERY_LAYER/cgm_supports_edges_manifest_v1_0.json` and `cgm_contradicts_edges_manifest_v1_0.json` (named in the agent's findings) — the existing CGM ingest may have processed only one manifest. Run the ingest over all manifest files; expect ~127 → ~339 in `l25_cgm_edges` total. PROBE 3+4 will confirm whether the gap is a missing ingest pass or missing source data.
- **F3.2 (M, data).** Resolve the 105 orphan edges. PROBE 4 likely confirms they target `UCN.SEC.*` nodes. Two paths: (a) ingest UCN section nodes into `l25_cgm_nodes` (preferred — converts orphans to valid and unlocks UCN-anchored traversal); or (b) rewrite the manifests to retarget those edges to existing nodes. Path (a) also satisfies F2.1's UCN-chunking dependency.
- **F3.3 (M, classifier or per-tool planner).** Build an entity → CGM node ID resolver. A small reference table (planet name → `PLN.*`, house number → `HSE.*`, yoga name → `YOG.*`, karaka name → `KRK.*`, sensitive point → `SEN.*`, dasha name → `DSH.*`, divisional position → `DVS.*`) can be embedded in the classifier or per-tool planner prompt. The LLM extracts entities from query text and maps them to node IDs as graph_seed_hints.
- **F3.4 (S, classifier).** Have the planner emit `edge_type_filter` per query intent. "What yogas does Mercury participate in" → `edge_type_filter=['YOGA_MEMBERSHIP']`. "What dispositors govern my Saturn" → `edge_type_filter=['DISP', 'OWNERSHIP']`. "What activates in Saturn dasha" → `edge_type_filter=['DASHA_ACTIVATION']`.

**Acceptance criterion.** After F3.1–F3.4, the median number of CGM nodes returned per query rises from ~0 (current) to ≥ 5; tool's `zero_result_runs` rate over 20 queries falls below 30%.

### §2.4 `temporal` — works, but corpus is shallow

**Current state.** HTTP calls to Python sidecar `/transits` (always) and `/ephemeris` (when `forward_looking=true`). Sidecar is healthy after the CORS fix. Returns today's planetary positions and (if predictive) ephemeris.

**Bottlenecks.** (ii) sidecar response covers today only; the rich timing substrate in DB (660,726 ephemeris_daily rows over 1900–2100, 46 sade_sati_phases, 2,462 retrograde stations, 913 eclipses) is not exposed to the tool. (i) Classifier rarely supplies a `time_window` parameter.

**Fixes.**

- **F4.1 (M, sidecar).** Add `/dasha` endpoint to compute MD/AD/PD for an arbitrary date or date range. The current Vimshottari machinery exists; expose it.
- **F4.2 (S, sidecar + tool).** Add `/sade_sati` endpoint that returns the phase active on a given date (or returns the next N phases from today). `temporal.ts` exposes a `sade_sati` flag.
- **F4.3 (M, sidecar + tool).** Add `/ephemeris_range` endpoint for a (start_date, end_date, planets[]) query against `ephemeris_daily`. `temporal.ts` exposes `time_window={start,end}`.
- **F4.4 (S, sidecar).** Add `/eclipses` and `/retrograde_stations` endpoints over the existing tables, parameterized by date window and planet.
- **F4.5 (M, classifier).** Have the planner emit `time_window` for queries that mention years, ages ("at 47"), dates, or date-relative phrases ("in the next two years").

**Acceptance criterion.** A query "what's coming up over the next three years for my career" returns dasha+bhukti for those years, eclipses falling on the chart's career-significator points, and any sade-sati phases active.

### §2.5 `pattern_register` — corpus thin, filter blunt

**Current state.** 22 patterns in JSON, filtered only by `domain` (exact match), no LIMIT, no confidence threshold, forward-looking sorts but does not filter.

**Bottlenecks.** (ii) corpus thin (22 patterns over 17-year+ dasha arc; PAT count per domain is 1–5); (iii) filter blunt — no confidence threshold, no full-text search on `claim_text` or `mechanism`, no severity/significance threshold.

**Fixes.**

- **F5.1 (L, data, highest leverage of the four registers).** Expand from 22 → 70+ patterns over the next two M2A discovery sessions. Generate systematically: 10 patterns covering the Mercury MD remainder (2026–2027), 20 covering Saturn MD (2027–2046), 5 covering Ketu MD (2046+), plus 10–15 cross-dasha patterns and 10–15 chronic-pattern entries. Each pattern must declare AK/AmK function, time-indexed falsifier, and verification window. This is a discovery-session output, not a code task.
- **F5.2 (S, filter).** Add `confidence_min`, `significance_min`, `forward_looking_only` filters. Add `LIMIT` parameter (default 20).
- **F5.3 (M, filter).** Add full-text search over `claim_text + mechanism` so a domain-empty query can still hit relevant patterns. Use the same BM25 path planned for F2.5.
- **F5.4 (S, classifier).** Have the planner emit pattern-relevant signals: when query mentions a date range, set `forward_looking_only=true` AND set the verification-window predicate.

**Acceptance criterion.** After F5.1, register has ≥ 60 patterns; after F5.2/F5.3, queries that previously returned 1 pattern now return 3–8 ranked by confidence × significance.

### §2.6 `resonance_register` — sparsely covers cross-domain space

**Current state.** 12 cross-domain bridges (out of 36 possible domain pairs in a 9-domain chart). Filter is exact match on `domains_bridged` intersection. No LIMIT.

**Bottlenecks.** (ii) corpus thinness — 33% domain-pair coverage; (iii) no confidence/forward-looking filtering.

**Fixes.**

- **F6.1 (M, data).** Expand to 24+ resonances. Specifically: bridges between every adjacency pair currently uncovered (career↔parents, wealth↔relationships, health↔children, mind↔family, etc.). Discovery session output.
- **F6.2 (S, filter).** Add `confidence_min`, `forward_looking`, `LIMIT`.

**Acceptance criterion.** Coverage ≥ 24/36 pairs; queries on uncovered pairs no longer return empty.

### §2.7 `cluster_atlas` — only 34% of MSR signals are in any cluster

**Current state.** 12 clusters housing 170 signals. The MSR has 499 signals — meaning **329 signals are orphaned from any cluster** (66%). Filter exposes `dominant_domain` and `sub_domains`, plus `graph_seed_hints` for ranking.

**Bottlenecks.** (ii) corpus thinness — coverage is the headline issue; (iii) no confidence threshold; (i) `graph_seed_hints` (cluster IDs) rarely supplied.

**Fixes.**

- **F7.1 (L, data, very high leverage).** Re-cluster the MSR with target ≥ 80% coverage (≥ 400 signals housed). Cluster generation is a discovery-session task; suggested approach: cluster by (domain × planet × signal_type) tuple with semantic merging, target 25–35 clusters total. Each cluster's `signal_ids` becomes a high-confidence retrieval bundle for any query touching its domain or its dominant planet.
- **F7.2 (S, filter).** Add `confidence_min`, `significance_min`, `cluster_size_min` filters; add LIMIT.
- **F7.3 (S, planner).** Have the per-tool planner (§3) emit `graph_seed_hints` (cluster IDs) when a query maps onto a known cluster theme.

**Acceptance criterion.** Cluster coverage ≥ 80% of MSR; queries on a domain return ≥ 2 clusters.

### §2.8 `contradiction_register` — actively under-built

**Current state.** 8 contradictions, 4 contradiction classes. Filter is `domains_implicated` intersection only. Confidence and significance are hard-coded constants regardless of the entry's actual confidence.

**Bottlenecks.** (ii) thin corpus; (iii) hard-coded confidence/significance is wrong (entries carry their own; the tool is overwriting them).

**Fixes.**

- **F8.1 (M, data).** Systematic red-team pass per dasha epoch and per karaka role to surface 20+ contradictions. Each new contradiction resolves a tension elsewhere in the corpus (and may invalidate / refine an MSR signal).
- **F8.2 (S, filter).** Replace hard-coded confidence/significance with the entry's own. Add `severity_min` filter (HIGH/MEDIUM/LOW). Add `contradiction_class` filter.

**Acceptance criterion.** ≥ 20 contradictions; severity-filtered queries return only the requested severity.

### §2.9 `query_msr_aggregate` — park it

Always returns `{ status: 'multi_native_not_deployed' }` with confidence=1.0 and significance=1.0 — i.e., it currently injects a one-sentence noise message into every bundle while occupying a tool slot.

**Fix F9.1 (S).** Until multi-native deployment is in scope (post-M10 per Macro Plan), remove `query_msr_aggregate` from the default `tools_authorized` list emitted by the classifier. It can remain in code as a stub but should not fire. Alternative: the classifier emits it only when `query_class='cross_native'` (which currently only the `crossNativeMetaRule` covers).

### §2.10 `manifest_query` — keep but de-emphasize for content

Works correctly (deterministic keyword scoring against CAPABILITY_MANIFEST). But it returns artifact metadata, not astrological content.

**Fix F10.1 (S).** Tag manifest_query as a "meta" tool in trace UI. Down-rank its results in the synthesis-step context-budget allocator (per-token budget for meta tools should be at most 5% of total). Keep it for plan-building (the LLM can use its results to decide which artifacts to deeply consult), but don't let it crowd content tools.

### §2.11 NEW: `domain_report_query` (L3) — does not exist; build it

**Why.** The nine REPORT_* files (REPORT_FINANCIAL_v2_1, REPORT_CAREER_DHARMA, REPORT_HEALTH_LONGEVITY, REPORT_RELATIONSHIPS_MARRIAGE, REPORT_CHILDREN_LEGACY, REPORT_SPIRITUAL_MOKSHA, REPORT_PARENTS_FAMILY_KARMA, REPORT_PSYCHOLOGY_MIND, REPORT_TRAVEL_FOREIGN) are acharya-grade narrative built specifically to be served to queries on their domain. They are the single most valuable L3 asset and currently invisible.

**Fix F11.1 (M).** New tool `domain_report_query`, reads CAPABILITY_MANIFEST for `path LIKE '03_DOMAIN_REPORTS/REPORT_*'`, filters by intersection with `plan.domains`, returns whole-document or section excerpts. Two implementation options: (a) section-level — the tool reads the .md files from disk/GCS and parses by `## Section` boundary, returns sections matching keywords; (b) embedding-backed — F2.3 chunks the L3 reports with `domain` tags, this tool wraps a `vector_search` call with a `doc_type='l3_domain_report'` filter. Option (b) reuses infra and is preferred.

**Composition rule.** Add `domainReportRule`: fires when `plan.domains.length > 0`; adds the matching REPORT_* canonical_ids by domain.

### §2.12 NEW: `remedial_codex_query` (L4) — does not exist; build it

**Fix F12.1 (M).** Register the four REMEDIAL_CODEX files in CAPABILITY_MANIFEST as a new layer L4. Build `remedial_codex_query` tool with the same options as F11.1. Add `remedialRule` to composition_rules.ts (fires when `query_class='remedial'`).

### §2.13 NEW: `timeline_query` (L5) — does not exist; build it

**Fix F13.1 (M).** Register LIFETIME_TIMELINE_v1_0, HEATMAP_VARSHPHAL_v1_0, and any other 05_TEMPORAL_ENGINES files in CAPABILITY_MANIFEST as L5. Build `timeline_query` tool that reads them and accepts a `time_window` parameter (overlapping with F4.5 from `temporal`). Add `timelineRule` (fires when `forward_looking=true` AND `time_window` is set).

### §2.14 Composition rule fixes (Chokepoint A)

In `platform/src/lib/bundle/composition_rules.ts`, add:

- `remedialRule` — fires for `query_class='remedial'`, adds REMEDIAL_CODEX entries.
- `domainReportRule` — fires when `plan.domains.length > 0`, adds matching REPORT_* by domain.
- `timelineRule` — fires when `plan.forward_looking=true`, adds 05_TEMPORAL_ENGINES entries.

These are 30-line additions each. The contributing tools must exist (§2.11–§2.13) for the rules to be useful.

### §2.15 Trace UI fixes

- Render `data_summary.result` prominently for `classify` and `compose_bundle` so they don't appear empty.
- Add a "metadata-only" badge to those step rows.
- Have `compose_bundle` populate `payload.items` with the bundle's canonical_id list (one item per composed artifact, with role tag) so the user can see which artifacts were composed in.

### §2.16 The `chart_facts` table is not reached by any tool today

PROBE 9 will confirm `chart_facts` has 589 rows of structured L1 (placements, dignities, dasha chara, sahams, yogas). None of the 10 retrieval tools touch this table — the LLM sees this content only via FORENSIC chunks (vector_search) and via downstream MSR signals. A purpose-built `chart_facts_query` tool would let the planner ask precise structural questions ("what are the dignities of Mars?") and get crisp tabular answers. This is **F-NEW-CHART_FACTS (M)** — a recommended addition but not strictly required if F2.1 chunks the FORENSIC effectively.

## §3 — Task 2: LLM-driven per-asset query construction

### §3.1 Why the current single-classifier design hits a ceiling

The current design has **one** LLM stage (the router) emitting **one** generic QueryPlan whose fields (domains, planets, graph_seed_hints, forward_looking, time_window, query_text) are then passed to all 10 tools. The tools' input schemas are not aligned: some accept domains and planets only (the four registers), some accept seed_hints (cgm_graph_walk, cluster_atlas), some accept top_k (vector_search), some accept question text (manifest_query). When the classifier doesn't know a tool needs a particular field, that tool gets nothing.

The native's instinct — "I want the LLM to determine what is going to be retrieved from what" — is exactly the right shift. The fix is a second LLM stage between `compose_bundle` and `retrieve(parallel)`: a **per-tool query planner**.

### §3.2 New pipeline stage: `plan_per_tool`

```
classify  →  compose_bundle  →  plan_per_tool  →  retrieve(parallel)  →  context_assembly  →  synthesize  →  audit
                                       NEW
```

**Inputs to `plan_per_tool`:** the user's `query_text`, the high-level `QueryPlan` from `classify`, the bundle composed by `compose_bundle` (so the planner knows which artifacts will already be in context), and the list of `tools_authorized`.

**Output:** a map `{ tool_name → toolSpecificParams }` — one entry per authorized tool, each containing the precise filter values that tool needs.

**Implementation.** A new file `platform/src/lib/router/per_tool_planner.ts`. For each authorized tool, call Haiku (`claude-haiku-4-5-20251001`) with a tool-specific prompt template. Calls run in parallel (max 10 concurrent). Each call's output is JSON validated against the tool's input schema (re-use `@/lib/schemas`).

**Cost.** Haiku is roughly $0.80 per million input tokens + $4 per million output. A typical per-tool prompt is 800 input tokens (system + question + tool spec) and ~150 output tokens. Ten parallel calls per query: 8K input + 1.5K output ≈ $0.013 per query. At 50 queries/day, $0.65/day. Latency: 10 parallel × ~250ms ≈ 250ms added to the pipeline.

### §3.3 Per-tool prompt templates

Each prompt has the same scaffold but tool-specific content:

```
SYSTEM:
You are crafting the optimal input for the {tool_name} retrieval tool.

The tool reads from: {data_source_description}
The tool's filter logic is: {filter_summary}
The tool's input schema is: {input_schema_json}
The tool returns its richest results when: {optimal_input_pattern}

Examples of optimal inputs for this tool:
{three_or_four_example_pairs}

USER:
Question: "{query_text}"
Already-classified domains: {plan.domains}
Already-classified query_class: {plan.query_class}
Bundle artifacts already composed: {bundle_canonical_ids}

Emit a single JSON object matching the tool's input schema.
Be specific. Prefer narrow, well-targeted filters over broad catches.
```

**Example for `cgm_graph_walk`:**

```
SYSTEM:
You are crafting the optimal input for the cgm_graph_walk retrieval tool.
The tool walks a directed graph of 234 nodes and 21 valid edges describing
the native's chart relationships. Nodes are typed: PLN.* (planets, e.g.
PLN.MERCURY), HSE.* (houses, e.g. HSE.7), YOG.* (yogas, e.g. YOG.SARASWATI),
KRK.* (karakas, e.g. KRK.C8.DARA), SEN.* (sensitive points, e.g. SEN.GULIKA),
DSH.* (dashas, e.g. DSH.MD.MERCURY), DVS.* (divisional positions, e.g.
DVS.D9.MOON). Edge types: DISP, NAK_LORDSHIP, ASPECTS_3RD, ASPECTS_4TH,
ASPECTS_8TH (the only currently valid types).

The tool returns its richest results when graph_seed_hints contains 1–3
node IDs that are central to the question, and edge_type_filter narrows
to the relationship type the question asks about.

EXAMPLES:
"How does Mercury's exaltation support my work?" →
  { graph_seed_hints: ['PLN.MERCURY'], graph_traversal_depth: 2,
    edge_type_filter: ['DISP', 'NAK_LORDSHIP'] }

"What does the 7th house contain in my chart?" →
  { graph_seed_hints: ['HSE.7'], graph_traversal_depth: 1,
    edge_type_filter: null }

"Which yogas does my chart form?" →
  { graph_seed_hints: ['YOG.SARASWATI', 'YOG.LAKSHMI'],
    graph_traversal_depth: 1, edge_type_filter: null }

USER: ...
```

### §3.4 What changes per tool

- `msr_sql` planner: extracts planet hints, signal_type, temporal_activation, valence; sets confidence_floor adaptive (0.4 for exploratory, 0.6 for default, 0.8 for high-confidence answers).
- `vector_search` planner: rewrites the query into 1–2 paraphrased forms (the embedding-friendly form is rarely the user's natural-language form); picks `doc_type` filter and `top_k`.
- `cgm_graph_walk` planner: per §3.3 example.
- `temporal` planner: extracts `time_window`; sets `dasha_required`, `transits_required`, `eclipses_required`, etc.
- Four register planners: extract domains; set confidence/significance thresholds; set forward_looking; set graph_seed_hints (cluster IDs) when relevant for cluster_atlas.
- `manifest_query` planner: composes a keyword-rich question from the user's query; sets `top_n`.
- New L3/L4/L5 planners (post §2.11–§2.13): same shape.

### §3.5 Evaluation harness

This is non-negotiable infrastructure. Without it the per-tool planner is unverifiable.

- **Eval set.** 30 representative queries × 10 tools = 300 (query, tool) pairs. For each pair, a human-graded `ideal_set` of top-5 results (by canonical_id or signal_id). Build during M2A using domain expertise + ground-truth from the FORENSIC and MSR.
- **Metrics.** Recall@5, Precision@5, MRR, plus a "diversity" score (how many distinct entity types appear in the top-K).
- **A/B framework.** Same query goes through (a) classifier-only QueryPlan and (b) classifier + per-tool planner. Compare metrics. Expected 2–4× recall on cgm_graph_walk and pattern_register; smaller gains on msr_sql and vector_search.
- **Prospective logging.** Per Macro Plan §Cross-cutting, every retrieval against the eval set is logged with predicted relevance scores BEFORE the human grade is revealed. This builds the calibration ledger over time.

### §3.6 Phasing

- **Phase 11C-α (week 1).** SQL probes run + diagnosed (this document's §4 is conditional on probe results). Trace UI fixes (§2.15). Composition-rule additions for `remedial`, `domainReport`, `timeline` (§2.14) — but no-ops until §2.11–§2.13 tools exist.
- **Phase 11C-β (weeks 2–3).** F2.1 + F2.2 + F2.3 (L2.5 + L3 chunking and embedding) — the highest-leverage data move. F3.1 + F3.2 (CGM 339→full ingest, orphan resolution). New tools `domain_report_query` (F11.1) and `remedial_codex_query` (F12.1). Schema additions for msr_sql filters (F1.2, F1.3, F1.4, F1.6).
- **Phase 11C-γ (week 4).** `plan_per_tool` stage shipped for top-3 highest-leverage tools (msr_sql, cgm_graph_walk, vector_search). Eval harness built and the first A/B run executed.
- **Phase 11C-δ (weeks 5–6).** `plan_per_tool` extended to remaining tools. Hybrid BM25+vector (F2.5). `timeline_query` (F13.1). Sidecar endpoint expansions (F4.1–F4.4).
- **Discovery sessions in parallel (M2A track).** F5.1 (pattern register expansion), F6.1 (resonance expansion), F7.1 (cluster atlas re-cluster), F8.1 (contradiction red-team). These are M2 corpus work and run alongside platform work, not blocked by it.

## §4 — SQL probes — what to verify before doing any code

`platform/scripts/retrieval_diagnostic_probes.sql` provides 10 probes. The findings that materially change the plan:

- **PROBE 2** confirms or refutes whether `signal_type` and `temporal_activation` are populated columns in `msr_signals`. If unpopulated, F1.2/F1.3 require an ETL fix first; if populated, they are pure SQL/code wiring.
- **PROBE 4** confirms the orphan-edge target distribution. If `UCN.*` dominates, F3.2 path (a) (ingest UCN section nodes) yields ≥ 60 valid edges with one ingest pass.
- **PROBE 5** confirms whether `rag_chunks` already contains anything beyond `(L1, l1_fact, ~102)`. If non-trivial L2.5 chunks already exist, F2.1 is partly done.
- **PROBE 6** is the single most diagnostic: which tools are firing zero-result over the last 20 queries. Tools with `zero_result_runs ≥ 15/20` are de facto dead today, regardless of what the source code says.
- **PROBE 7** confirms what fields the classifier is actually populating. If `planets[]` and `graph_seed_hints[]` are consistently empty in `query_plans`, the classifier-side fixes (F1.1, F3.3, F3.4) are unlocked-by definition.

Run the probes, paste output back in, and the §3.6 phasing gets re-prioritized in light of the actual findings. Specifically: if PROBE 5 shows L2.5 already partly chunked, Phase 11C-β re-orders.

## §5 — Highest-leverage three actions if only three are done

If the native picks only three from the 30+ fixes catalogued above, the order is:

1. **F2.1 + F2.3 (week-2 corpus move).** Chunk and embed UCN, CDLM, RM, and the nine L3 domain reports. This single change makes vector_search the dominant content path and immediately gives the LLM access to L2.5 narrative + L3 acharya-grade reports — the largest visible-content uplift achievable.
2. **F3.1 + F3.2 (week-2 graph move).** Close the CGM 339→127 ingest gap and resolve the 105 orphan edges by ingesting UCN section nodes. This converts cgm_graph_walk from a 21-edge skeleton to a 339-edge knowledge graph. Per §2.3, this combined with F3.3/F3.4 in §3 is what makes graph traversal contributing.
3. **`plan_per_tool` LLM stage for msr_sql + cgm_graph_walk + vector_search (week 3–4).** With #1 and #2 done, the per-tool planner becomes the multiplier: it can now address rich tools rather than starved ones. Without #1 and #2 it would be planning over empty data; with them, it converts the data into reach.

Items #1 and #2 are corpus/infra moves; item #3 is the LLM-driven planner the native asked for. The order matters: #3 without #1 and #2 underperforms; #1 and #2 without #3 still help — but the marginal lift from adding #3 atop #1+#2 is the highest in the project.

## §6 — Open decisions for the native

Before promotion to CURRENT, the native should confirm:

- **D1.** Whether L4 (Remedial Codex) and L5 (Temporal Engines) are in or out of scope for Phase 11C. If out of scope, defer §2.12, §2.13, F12.1, F13.1, and the corresponding composition rule additions to a later phase. If in scope, proceed as specified.
- **D2.** Whether discovery-session output (F5.1, F6.1, F7.1, F8.1) is in scope as M2A work running parallel to Phase 11C, or whether the user prefers to ship Phase 11C platform work first and re-run the discovery passes after the new tooling is live. The latter is safer (eval harness will measure the corpus-expansion lift); the former is faster.
- **D3.** Whether to run the SQL probes first, then re-prioritize, or kick off the highest-leverage work in §5 in parallel with the probes.
- **D4.** Disposition of this draft document: promote to CURRENT (and into CAPABILITY_MANIFEST) as a Phase 11C plan? Add to PHASE_B_PLAN as M2-supportive infra? Or remain a planning artifact until decisions D1–D3 settle?

---

*End of RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT. Next action: native review of §6 decisions; SQL probes execution to validate §1 and §2 hypotheses.*
