---
artifact: M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT
canonical_id: M1_M2_ACTIVATION_MASTER_PLAN
version: 0.1-DRAFT
status: DRAFT_PLANNING
authored_by: Claude (Cowork) 2026-04-29
authored_for: Native review + native decision on M2-completion scope
related:
  - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md (M1 + M2 macro definitions)
  - 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md (B.0–B.10 execution arc; this plan is B.6.1+ enhancement)
  - 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md (predecessor, partially superseded by completed 11C_a/b/c briefs)
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md (M1 source-of-truth)
  - 025_HOLISTIC_SYNTHESIS/{MSR_v3_0, UCN_v4_0, CDLM_v1_1, CGM_v9_0, RM_v2_0}.md (L2.5 source-of-truth)
predecessor_briefs_complete:
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES (diagnostic baseline)
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_a (CGM topology: 21 → 126 valid edges)
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_b (classifier real seeds: 1/17 → 60% fire)
  - CLAUDECODE_BRIEF_RETRIEVAL_11C_c (L2.5/L3 chunks: 941 → 1005)
intended_disposition: |
  After native review, this draft becomes the canonical M1/M2 completion plan.
  Each phase below decomposes into one or more CLAUDECODE_BRIEFs. The plan
  itself stays as a living planning artifact through M2 close; sub-briefs are
  versioned and tracked. This is the document we'll point to when we say
  "good job done."
---

# M1/M2 Activation Master Plan v0.1 (DRAFT)

## §0 — Why this plan

The native's instruction is unambiguous: **every single piece of data in the M1 corpus should be accessible, activated, and fully utilized by the time M2 closes.** FORENSIC v8.0 is acharya-grade — 1,936 lines, 27 sections, 660K+ derived rows in Cloud SQL. M2's retrieval pipeline currently exposes a fraction of it. This plan inventories every L1 facet, identifies its activation status, and lays out the surgical work to close every gap.

Implementing this plan to its quality bar means: a query about any chart entity, classical system, dasha period, ashtakavarga cell, KP cusp lord, divisional placement, yoga, saham, sensitive point, or longevity indicator routes through the right tool, retrieves authentic structured data, and reaches the LLM with classical-grade citation. No layer is dark. No dimension is dropped by ETL. No retrieval tool returns empty when the data exists in source.

When that's true, M2 closes with confidence. When it's not yet true, this plan tells us exactly what's left.

## §1 — The quality bar ("good job done")

We will say "good job done" when all of the following hold simultaneously:

1. **Source-to-tool coverage = 100%.** Every section of FORENSIC v8.0 (§1–§27) has at least one retrieval path the LLM can invoke. No section is invisible.
2. **ETL preserves every source field.** No column dropped between source markdown and Cloud SQL. PROBE 2/9-class errors are gone.
3. **Quantitative substrate is structured.** Shadbala, ashtakavarga (BAV+SAV), KP cusp chains, all 36 sahams, divisional placements D1–D60 — each queryable as structured data, not as parsed text.
4. **L2.5 graph is complete.** All 339 source CGM edges in DB (current: 126). All 15 source edge types valid (current: 5). Chunker coverage matches structural extractor counts.
5. **Classifier is L1-aware.** Per-tool query planning is in place; the LLM picks the right tool with the right parameters per query class. Empty-result rate drops below 10% for entity-named queries.
6. **Synthesis cites authentically.** When the LLM cites BPHS / Saravali / Phaladeepika, the citation comes from MSR's `classical_source` field, not invention. When it asserts a falsifier, it comes from MSR's `falsifier` field.
7. **Provenance audit passes.** ≥95% of MSR signals trace to specific FORENSIC fact IDs. ≥90% of UCN paragraphs cite specific MSR signal IDs. ≥95% of CGM SUPPORTS edges derive from named MSR signals.
8. **Eval harness exists and runs.** B.9's golden 50-query eval set runs end-to-end with measured Recall@K, Precision@K, MRR, and per-doc-type retrieval coverage.
9. **Observability is live.** `audit_events` and `query_plans` tables exist and are populated. Every query writes a complete audit trail.
10. **Red-team passes M2 final.** B.10's red-team probes find no class-of-finding regressions vs the existing M2A_Exec audit baselines.

A single failure on any of (1)–(10) is "more work to do." Unanimous pass is "good job done."

## §2 — Current state (verified 2026-04-29)

### M1 corpus (FORENSIC v8.0 + L2.5 synthesis layer)

| Layer | Source artifact | Status |
|---|---|---|
| L1 facts | FORENSIC_v8_0.md | ✅ Acharya-grade. 27 sections. 1,936 lines. All major classical systems present (Shadbala, Ashtakavarga, KP, 36 Sahams, D1–D60, Yogini, Chara, Tajika). |
| L2.5 signals | MSR_v3_0.md | ✅ 499 signals. Source has rich metadata (signal_type, classical_source, falsifier, etc.) |
| L2.5 narrative | UCN_v4_0.md | ✅ 17K+ words. Foundation Signatures FS1–FS5 + Parts VI–X. |
| L2.5 cross-domain | CDLM_v1_1.md | ✅ 82 cells, asymmetric strength scalars. |
| L2.5 graph | CGM_v9_0.md | ✅ 234 nodes + 339 edges across 15 edge types. |
| L2.5 resonance | RM_v2_0.md | ✅ 28 elements with constructive + destructive resonance. |
| L1 events | LEL_v1_2.md | ✅ 36 events + 5 period summaries + 6 chronic patterns. |

### M2 ingestion (Cloud SQL state)

| Table | Rows | Status |
|---|---|---|
| msr_signals | 499 | ✅ rows ingested; ❌ ETL drops signal_type, temporal_activation, classical_source, falsifier |
| chart_facts | 589 | ⚠️ rows ingested; column inventory unverified (PROBE 9 errored on `confidence`) |
| l25_cgm_nodes | 369 | ✅ post-11C_a; includes 134 UCN.SEC.* + 1 KARAKA |
| l25_cgm_edges | 127 (126 valid, 0 orphan, 1 self_loop) | ⚠️ source has 339 edges; 213 still missing across 10 edge types |
| l25_ucn_sections | ~134 (extractor count) | ✅ structured table |
| l25_cdlm_links | ~80 | ✅ |
| l25_rm_resonances | ~28 | ✅ |
| rag_chunks | 1,005 | ⚠️ ucn_section underchunked (25 vs ~134); cgm_node not including UCN.SEC.* |
| rag_embeddings | 1,021 | ✅ 1:1 with chunks (16 stale from prior build) |
| life_events | 36 | ✅ |
| sade_sati_phases | 46 | ✅ |
| ephemeris_daily | 660,726 | ✅ 1900–2100 daily, 9 planets |
| eclipses | 913 | ✅ |
| retrogrades | 2,462 | ✅ |
| audit_events | DOES NOT EXIST | ❌ table missing per PROBE 6 |
| query_plans | DOES NOT EXIST | ❌ table missing per PROBE 7 |
| query_trace_steps | populated | ✅ trace working post-11C_b |

### M2 retrieval surface (TypeScript tools)

| Tool | What it queries | Status |
|---|---|---|
| msr_sql | msr_signals (filtered by domain, planet, forward_looking, confidence) | ✅ workhorse; only 4 of ~10 source filter axes exposed |
| vector_search | rag_embeddings + rag_chunks (cosine, top_k) | ✅ now sees 7 doc_types post-11C_c |
| cgm_graph_walk | l25_cgm_nodes + l25_cgm_edges (BFS) | ✅ 60% fire post-11C_b; needs richer graph (M2-B) |
| temporal | Python sidecar (/transits, /ephemeris) | ⚠️ 300s timeout signature in PROBE 8 — needs investigation |
| pattern_register | 22 patterns JSON | ✅ thin corpus, exact-match filter |
| resonance_register | 12 resonances JSON | ✅ thin corpus |
| cluster_atlas | 12 clusters JSON | ⚠️ 66% of MSR signals not in any cluster |
| contradiction_register | 8 contradictions JSON | ✅ thin |
| query_msr_aggregate | hardcoded stub | ⛔ park (M7 work) |
| manifest_query | CAPABILITY_MANIFEST.json keyword scoring | ✅ meta-tool, marginal for content |
| **chart_facts_query** | **DOES NOT EXIST** | ❌ THE biggest gap — 589 rows of L1 structure unread |
| **ashtakavarga_query** | **DOES NOT EXIST** | ❌ §7 has full BAV+SAV; no tool surfaces it |
| **kp_query** | **DOES NOT EXIST** | ❌ §4 has 12 cusps × 3 lords; no tool surfaces it |
| **saham_query** | **DOES NOT EXIST** | ❌ §12.2 has 36 sahams; no dedicated tool |
| **divisional_query** | **DOES NOT EXIST** | ❌ §3 has D2–D60; only sparse via CGM DVS nodes |
| **shadbala_query** | **DOES NOT EXIST** | ❌ §6 has 6-component table + ranking; no tool |

## §3 — The audit-first principle (Phase α)

Before any implementation, three audits must run. Each is cheap (≤30 minutes) and prevents downstream waste.

### Phase α.1 — `chart_facts` schema introspection (30 min)

Question: what's actually in the 589-row `chart_facts` table?

Probe:
```sql
\d chart_facts
SELECT category, COUNT(*) FROM chart_facts WHERE is_stale=false GROUP BY category ORDER BY COUNT(*) DESC;
SELECT * FROM chart_facts WHERE is_stale=false LIMIT 5;
```

What it tells us: which FORENSIC §-sections were ETL'd into chart_facts. Determines whether `chart_facts_query` (M2-C.1) can be a direct wrap or needs an ETL-augment-first pass.

### Phase α.2 — `msr_signals` column inventory (10 min)

Question: which MSR source fields actually became columns in `msr_signals`?

Probe:
```sql
\d msr_signals
SELECT column_name FROM information_schema.columns WHERE table_name='msr_signals';
```

What it tells us: scope of the ETL-completion task in M2-A.1. Best case: only `signal_type` and `temporal_activation` are missing. Worst case: `classical_source`, `falsifier`, `entities_involved`, `valence`, `supporting_rules`, `rpt_deep_dive` are also dropped.

### Phase α.3 — FORENSIC source-vs-database round-trip (45 min)

Question: for each FORENSIC v8.0 section §1–§27, what's the database representation?

For each section, fill this matrix:
- Has structured table representation? (chart_facts? msr_signals? l25_*?)
- Has rag_chunks representation?
- Has retrieval tool? Which one?
- Coverage % vs source content?

Output: an `M1_M2_ACTIVATION_MATRIX.md` artifact that becomes the M2-close acceptance gate. Every row green = done.

**The audit is a session-zero deliverable.** Until α.1/α.2/α.3 land, scoping the implementation phases below is partially blind.

## §4 — Phase M2-A: L1 activation (the largest gap)

### M2-A.1 — Complete `msr_signals` ETL (1 day)

**Scope.** Add columns the source has but ETL drops: `signal_type`, `temporal_activation`, `valence`, `classical_source`, `falsifier`, `supporting_rules`, `rpt_deep_dive`, `entities_involved`, `v6_ids_consumed`, `prior_id`. Re-run MSR ingest with full preservation.

**Acceptance.** PROBE 2 (signal_type × temporal_activation) returns a populated breakdown across all 499 signals; classical_source is non-NULL on ≥90% of signals; falsifier is non-NULL on ≥80% of signals.

**Effort.** 1 day (ETL fix + migration + re-ingest). Backend only.

**Predecessor.** Phase α.2.

### M2-A.2 — Complete `chart_facts` ETL (2 days)

**Scope.** Whatever FORENSIC sections didn't make it into `chart_facts`, get them in. Per α.1 finding, this is likely §6 Shadbala (6-component table + JH ranking), §7 BAV (84 cells) + SAV (12 cells), §4 KP cusps (36 entries), §12.2 36 Sahams, §3 D2–D60 placements (~150 cells), §11.3 Yogi/Avayogi, §13 Arudhas, §14 Navatara, §15 Panchang, §16 Aspects matrix, §22 Varshphal Muntha, §24 Longevity, §26 Yogas register.

**Acceptance.** `chart_facts` row count rises from 589 to estimated 1,800–2,500 (depends on which sections were missing). Every numbered FORENSIC § that contains FACT (vs DERIVED) data has corresponding rows. PROBE 9 returns a clean category breakdown spanning ≥15 distinct categories.

**Effort.** 2 days (ETL extension; possibly migration to add columns; re-ingest).

**Predecessor.** Phase α.1, α.3.

### M2-A.3 — Vimshottari sub-period extension (½ day)

**Scope.** §5.1 currently shows MD/AD per the grep. Below AD, classical Vimshottari has Pratyantardasha (PD), Sookshma (SD), Prana (PD2). For M3 readiness, all five levels should be computable for any date. If Vimshottari computation is in the Python sidecar, expose `/dasha_chain(date)` returning all five levels. If not yet implemented, add it.

**Acceptance.** A query like "what was my dasha chain on 2024-12-12" returns MD=Mercury, AD=Saturn, PD=<computed>, SD=<computed>, PD2=<computed> from the sidecar.

**Effort.** ½ day (sidecar function + endpoint).

**Predecessor.** None.

### M2-A.4 — Pada ETL completion (½ day)

**Scope.** §2.1 D1 placements have a Pada column. If pada didn't survive ETL into chart_facts, add it. For each planet, `chart_facts` should have `nakshatra` AND `pada` (1–4) as separate columns or fields.

**Acceptance.** `SELECT planet, nakshatra, pada FROM chart_facts WHERE category='placement'` returns all 9 planets + Lagna with non-NULL pada.

**Effort.** ½ day.

### M2-A.5 — Bhava chalit dual-house exposure (½ day)

**Scope.** §2.1 has both `Rashi House` and `Chalit House` per planet. ETL should preserve both. The retrieval surface (chart_facts_query) should expose both, with a flag to select which is queried.

**Acceptance.** A query about Mars's house can return both "rashi_house: 8, chalit_house: 9" with a note on the dual-house convention from §0.

**Effort.** ½ day.

## §5 — Phase M2-B: L2.5 substrate completion

### M2-B.1 — CGM edge expansion to 339 (2 days)

**Scope.** Source CGM v9.0 declares 339 typed edges across 15 types. Currently 126 in DB across 5 types. Missing: GRAHA_ASPECT, BHAV_ASPECT, JAIMINI_ASPECT, OWNERSHIP, TENANCY, EXALT_DEBIL_AFFINITY, KARAKA_ROLE, **YOGA_MEMBERSHIP**, DASHA_ACTIVATION, DIVISIONAL_CONFIRMATION, COMBUST_WAR, KAKSHYA_ZONE, SAHAM_COMPOSITION. Each edge type's spec is in CGM v9.0 source; the cgm_extractor needs to compute or read each.

**Acceptance.** `SELECT edge_type, COUNT(*) FROM l25_cgm_edges WHERE status='valid' GROUP BY edge_type` returns ≥10 edge types each with non-zero count. Total valid edges ≥ 320 (allowing for some self-loops and orphans). YOGA_MEMBERSHIP edges ≥ 60 (per CGM source declaration).

**Effort.** 2 days. Highest-leverage item in this phase — unlocks the full graph traversal capability.

**Predecessor.** None (independent).

### M2-B.2 — Chunker coverage completion (1.5 days)

**Scope.** Two known gaps from 11C_c closing summary:
- `ucn_section` chunker emits 25 chunks (H2 boundaries) vs ~134 ideal (H2+H3). Update chunker to emit H3 sub-section chunks.
- `cgm_node` chunker reads CGM_v9_0.md base (234 nodes) but doesn't include the 134 UCN.SEC.* nodes that 11C_a added to `l25_cgm_nodes`. Update chunker to read from `l25_cgm_nodes` after the swap, OR to also chunk UCN section nodes from UCN_v4_0.md.
- Plus: LEL period summaries (5) and chronic patterns (6) are not chunked at all. Add these.

**Acceptance.** `rag_chunks` count rises from 1,005 to ≥ 1,250. ucn_section count ≥ 100. cgm_node count ≥ 350.

**Effort.** 1.5 days.

**Predecessor.** None.

### M2-B.3 — MSR cluster atlas re-cluster (1 day)

**Scope.** Currently 12 clusters house 170 of 499 MSR signals (34% coverage). Re-cluster targeting ≥80% MSR coverage. Probable approach: cluster by (domain × dominant_planet × signal_type) with semantic merging; target 25–35 clusters.

**Acceptance.** Σ cluster_size_n across all clusters ≥ 400. Every domain has ≥ 2 clusters. Every planet has ≥ 1 cluster centered on it.

**Effort.** 1 day. Discovery-session output (Gemini → Claude two-pass per the existing protocol).

### M2-B.4 — Pattern register expansion to 70+ (3 days, discovery sessions)

**Scope.** Currently 22 patterns across 17-year+ dasha arc. Per Retrieval Productivity Plan §2.5, expand to 70+ patterns. Systematic approach:
- 10 patterns covering Mercury MD remainder (2026–2027)
- 20 patterns covering Saturn MD (2027–2046)
- 5 patterns covering Ketu MD (2046+)
- 10–15 cross-dasha patterns
- 10–15 chronic-pattern entries

Each pattern: AK/AmK function declared, time-indexed falsifier, verification window.

**Acceptance.** ≥ 70 patterns. Every domain has ≥ 5 patterns. ≥ 50% are forward-looking with explicit verification windows.

**Effort.** 3 days across multiple discovery sessions (Gemini-led).

### M2-B.5 — Resonance + contradiction expansion (2 days, discovery sessions)

**Scope.** Currently 12 resonances (33% domain-pair coverage), 8 contradictions. Expand to 24+ resonances and 20+ contradictions.

**Acceptance.** Resonances cover ≥ 24 of 36 possible domain pairs. Contradictions cover all 4 contradiction_class values with ≥ 5 each.

**Effort.** 2 days across discovery sessions.

## §6 — Phase M2-C: Retrieval surface expansion (the new tools)

This phase adds the missing TypeScript retrieval tools. Each is a small, focused tool. Building all five together in one push is more efficient than fragmenting; estimate is 5 days total for tool code + tests + classifier prompt updates.

### M2-C.1 — `chart_facts_query` (1.5 days, highest leverage)

**Scope.** New TypeScript tool that queries the (post-M2-A.2) `chart_facts` table. Parameters: `category` (enum: placement, shadbala, ashtakavarga_bav, ashtakavarga_sav, kp_cusp, saham, divisional, aspect, longevity, …), `planet?`, `house?`, `sign?`, `nakshatra?`, `pada?`, plus `rank_by?` and `limit?`. Returns structured rows.

**Acceptance.** A query "rank my planets by Shadbala" routes through `chart_facts_query(category='shadbala', rank_by='total', limit=9)` and returns the 7 planets in JH-authoritative order. A query "what is the BAV of my Mars in Capricorn" returns `bindu=2`.

**Effort.** 1.5 days (tool + classifier integration + 8 tests).

**Predecessor.** M2-A.2.

### M2-C.2 — `kp_query` (½ day)

**Scope.** Tool that queries §4 KP Cusp Mirror — for cusp N (1–12), return cusp degree, sign, Star Lord, Sub Lord, Sub-Sub Lord. Optionally filter to specific planet roles.

**Acceptance.** "What is the sub-lord of my 7th cusp?" returns "Saturn" (or whatever the actual value is).

**Effort.** ½ day.

**Predecessor.** M2-A.2 (depends on KP rows being in chart_facts).

### M2-C.3 — `saham_query` (½ day)

**Scope.** Tool that queries the 36-Saham register (§12.2). Parameters: `name?` (one of 36) or `domain?` (returns sahams in that domain) or `house?` (sahams falling in that house). Returns longitude, nakshatra, sign, house, meaning per saham.

**Acceptance.** "What is my Saham Mahatmya?" returns "11°24′11″ Sg, Moola, Sagittarius, 9H, Greatness."

**Effort.** ½ day.

### M2-C.4 — `divisional_query` (1 day)

**Scope.** Tool that queries any of D2–D60 placements. Parameters: `varga` (D1–D60), `planet?`. Returns sign occupancy per planet for that varga. Optionally returns the varga lagna.

**Acceptance.** "What does my D27 (Bhamsha) chart show for Mars?" returns the D27 sign for Mars + the D27 lagna position.

**Effort.** 1 day.

**Predecessor.** M2-A.2.

### M2-C.5 — `temporal` extension (1 day)

**Scope.** Existing temporal tool currently returns today's transits + forward-looking ephemeris. Extend with:
- `dasha_chain(date)` for full 5-level Vimshottari (M2-A.3).
- `sade_sati_status(date)` returning current phase from sade_sati_phases.
- `ephemeris_range(start, end, planets[])` for date-window queries.
- `eclipses_in(start, end)` and `retrograde_stations_in(start, end, planet?)` from existing tables.

Plus: investigate the 300s timeout signature from PROBE 8 — almost certainly a hard timeout that's silently degrading. Fix the underlying call latency or batch behaviour.

**Acceptance.** No `temporal` trace step exceeds 30s. All four new endpoints respond within 2s. The dasha_chain endpoint correctly returns MD/AD/PD/SD/PD2 for any date 1900–2100.

**Effort.** 1 day (sidecar endpoints + tool wrapping + timeout investigation).

**Predecessor.** M2-A.3.

### M2-C.6 — `vector_search` filter expansion (F2.2) (½ day)

**Scope.** Add `doc_type[]` and `layer` filter parameters to `vector_search.ts`. Update classifier prompt so the LLM picks doc_type filter per query class (factual → l1_fact only; interpretive → l1_fact + ucn_section + msr_signal + cdlm_cell; etc.).

**Acceptance.** A factual query returns top-K from layer='L1' only; an interpretive query returns mixed L1+L2.5; a discovery query includes domain_report. Trace data shows the filter being applied.

**Effort.** ½ day.

**Predecessor.** None.

## §7 — Phase M2-D: Synthesis surface completion

### M2-D.1 — Composition rules for L3 / L4 / L5 (1 day)

**Scope.** Per the original Retrieval Productivity Plan §2.14, add:
- `domainReportRule` — fires when `plan.domains.length > 0`, adds matching REPORT_* canonical_ids by domain.
- `remedialRule` — fires when `query_class='remedial'`, adds REMEDIAL_CODEX entries (currently no rule fires for this class).
- `timelineRule` — fires when `forward_looking=true`, adds 05_TEMPORAL_ENGINES entries.

These rules are no-ops until the corresponding tools exist (M2-D.2/D.3).

**Acceptance.** The rules are added; `compose_bundle` trace data shows them firing on the right query classes.

**Effort.** 1 day (composition_rules.ts changes + tests).

### M2-D.2 — `domain_report_query` tool for L3 (1.5 days)

**Scope.** New tool reading the 9 REPORT_* files (or, post-11C_c, querying rag_chunks with `doc_type='domain_report'`). Filter by `plan.domains`. Return whole-document or section excerpts.

**Acceptance.** A query about career retrieves REPORT_CAREER_DHARMA content; cross-checked via trace.

**Effort.** 1.5 days.

**Predecessor.** None (rag_chunks already has domain_report chunks post-11C_c).

### M2-D.3 — `remedial_codex_query` tool for L4 (1 day)

**Scope.** Register the REMEDIAL_CODEX files in CAPABILITY_MANIFEST. Build retrieval tool. Wire through composition rule (M2-D.1).

**Acceptance.** A `query_class='remedial'` query retrieves remedial codex content.

**Effort.** 1 day.

### M2-D.4 — `timeline_query` tool for L5 (1 day)

**Scope.** Register LIFETIME_TIMELINE_v1_0, HEATMAP_VARSHPHAL_v1_0 in CAPABILITY_MANIFEST. Build retrieval tool with `time_window` parameter.

**Acceptance.** A predictive query with time hints retrieves timeline file content.

**Effort.** 1 day.

### M2-D.5 — `audit_events` table + writer wiring (1 day)

**Scope.** PROBE 6 confirmed the table doesn't exist despite `AUDIT_ENABLED=true` per the platform feature flags. Either (a) find the migration that should have created it and apply, or (b) write the migration. Then ensure the audit writer in the new query pipeline actually populates it. Schema should match what the audit writer was designed against — find by grep.

**Acceptance.** `audit_events` table exists and rows accumulate as queries flow through production. PROBE 6 returns clean per-tool result counts over recent queries.

**Effort.** 1 day.

### M2-D.6 — `query_plans` table + writer (½ day)

**Scope.** PROBE 7 confirmed the table doesn't exist. The classifier output is currently only persisted in `query_trace_steps.payload` JSONB. Add a flat `query_plans` table that mirrors the QueryPlan schema for direct query.

**Acceptance.** PROBE 7 returns recent classifier outputs with each field flat-queryable.

**Effort.** ½ day.

### M2-D.7 — Per-tool query planner (LLM stage, F2.7 of original plan) (3 days)

**Scope.** Add a new pipeline stage `plan_per_tool` between `compose_bundle` and `retrieve(parallel)` per Retrieval Productivity Plan §3. Haiku-driven, parallel, per-tool prompt template, ~250ms added latency, ~$0.013/query.

This is the highest-leverage classifier upgrade after M2-A and M2-B land. With richer data behind every tool, per-tool planning unlocks precision retrieval.

**Acceptance.** A/B test shows ≥ 30% Recall@5 improvement vs single-classifier baseline on the 50-query golden set.

**Effort.** 3 days.

**Predecessor.** M2-A.1, M2-A.2, M2-B.1 (the planner needs rich data behind every tool to be worth its cost).

## §8 — Phase M2-E: Integrity + close (the M2 acceptance gates)

### M2-E.1 — Provenance integrity audit (1 day)

**Scope.** Three audits, each run as SQL probes, results captured to a markdown report:

1. **MSR → FORENSIC traceability.** Of 499 MSR signals, how many have a valid `v6_ids_consumed` chain to specific FORENSIC fact IDs that exist in chart_facts? Target ≥ 95%.
2. **UCN → MSR traceability.** Of UCN paragraphs (chunked), how many cite specific MSR signal IDs in their text? Target ≥ 90%.
3. **CGM SUPPORTS → MSR traceability.** Of SUPPORTS edges, how many derive from a named MSR signal? Target ≥ 95%.

Each audit is a SQL probe + a small Python script that parses the source text and verifies cross-references.

**Acceptance.** All three audits report ≥ target percentages. Sub-target rows are listed for retroactive cleanup as B.10 work.

**Effort.** 1 day.

### M2-E.2 — B.9 Eval Harness (1 day, the original B.9 scope)

**Scope.** Per PHASE_B_PLAN_v1_0.md §G Phase B.9. Build the eval harness that consumes `golden.jsonl` (50 queries with expected signals) and `golden_router_queries.json` (20 router classification queries). Runs the full pipeline; computes Recall@K, Precision@K, MRR, plus per-doc-type retrieval coverage and per-tool zero-result rate.

**Acceptance.** Harness runs end-to-end. Baseline metrics captured. A/B framework supports comparing classifier-only vs per-tool planner (M2-D.7).

**Effort.** 1 day (per the original B.9 plan).

### M2-E.3 — B.10 Red-Team + Thin UI + Handoff (1 day, the original B.10 scope)

**Scope.** Per PHASE_B_PLAN_v1_0.md §G Phase B.10. Final red-team probes against the eval set. Thin validation UI for human inspection. M2 handoff to M3.

**Plus the M2-close obligation** (per MACRO_PLAN_v2_0.md lines 509–511): scaffold `07_PROSPECTIVE_TESTING/PROSPECTIVE_PREDICTION_LOG_v1_0.md` so M5/M6 prospective testing has its substrate ready.

**Acceptance.** Red-team passes. Thin UI deployed. PROSPECTIVE_PREDICTION_LOG scaffolded. M2 close artifact (`M2_CLOSE_BASELINE_v1_0.md` or equivalent) created. CURRENT_STATE updated with `active_macro_phase: M3`.

**Effort.** 1 day.

### M2-E.4 — M2 close gates re-verified (½ day)

**Scope.** Re-run all 10 quality bar checks from §1. Document each as PASS or FAIL with evidence. If any FAIL, that's an exception to the M2 close — either fix in scope or formally defer to M3 with native sign-off.

**Acceptance.** All 10 quality bar checks PASS, documented with evidence in `M2_CLOSE_BASELINE_v1_0.md`.

**Effort.** ½ day.

## §9 — Sequencing + parallel paths

The work is largely parallelizable. The dependency graph:

```
Phase α (audits) ──┬─→ M2-A.1 (msr_signals ETL) ──→ M2-D.7 (per-tool planner)
                   ├─→ M2-A.2 (chart_facts ETL) ──→ M2-C.1/.2/.3/.4 (new tools)
                   └─→ M2-A.3 (Vimshottari) ─────→ M2-C.5 (temporal extension)

Independent (can start any time after audits):
  M2-B.1 (CGM 339 edges) — independent
  M2-B.2 (chunker fixes) — independent
  M2-B.3 (re-cluster) — discovery session
  M2-B.4 (pattern expansion) — discovery sessions
  M2-B.5 (resonance/contradiction) — discovery sessions
  M2-C.6 (vector_search filter) — independent
  M2-D.5 (audit_events table) — independent
  M2-D.6 (query_plans table) — independent

Downstream (require upstream):
  M2-D.1 (composition rules) — after M2-D.2/.3/.4 tools exist (or in parallel)
  M2-D.2/.3/.4 (L3/L4/L5 tools) — independent
  M2-D.7 (per-tool planner) — after M2-A + M2-B + M2-C land
  M2-E.1 (integrity audit) — after M2-A.1 lands
  M2-E.2 (eval harness) — after M2-C.* tools land
  M2-E.3 (red-team + close) — after M2-E.1 + M2-E.2
  M2-E.4 (M2 close gates) — last
```

**Critical path:** Phase α → M2-A.1 + M2-A.2 → M2-C.* tools → M2-D.7 planner → M2-E eval/red-team/close.

**Estimated total effort:** 25–30 working sessions (~5–6 weeks of single-stream daily sessions; less if multiple streams run in parallel).

**Parallelization opportunity:** Up to three streams concurrent — (1) corpus/discovery sessions for M2-B.3/.4/.5, (2) backend/ETL for M2-A + M2-D.5/.6, (3) TypeScript/tools for M2-C + M2-D.1–.4.

## §10 — Risk register

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Phase α audits surface unexpected ETL gaps that grow M2-A scope | M | M | Phase α explicitly named — surface gaps before scoping. Native review gate after α. |
| CGM 339-edge ingest exposes computational gaps in cgm_extractor (e.g., it can't compute GRAHA_ASPECT from source) | M | M | Test on a sample edge type first. If extractor needs new logic, scope as M2-B.1+ |
| Per-tool planner cost grows beyond projected $0.013/query | L | L | Latency-budget the Haiku call; cap at 500 input + 200 output tokens. Fall back to classifier-only if cost spikes |
| Discovery sessions produce thinner corpora than estimated | M | M | Targets in M2-B.3/.4/.5 are floors, not ceilings. If we hit floor, that's "good enough" for M2 close; expansion continues in M3 |
| Provenance integrity audits reveal sub-target percentages | M | M | Document gaps, fix what's tractable in M2, defer the rest to B.10 cleanup |
| Phase 14 (deployment / build) regressions interfere | L | M | Existing platform stream (R-redesigns, UI/UX) is parallel; coordinate via branch hygiene per existing convention |
| Native bandwidth: 25–30 sessions is significant | M | M | Phasing supports incremental wins; M2-A + M2-B alone deliver "complete L1 activation" even before M2-C/D extend the surface |

## §11 — What "good job done" looks like — concrete close criteria

When M2 closes, the following artifacts will exist and the following queries will work:

**Artifacts:**
- `M1_M2_ACTIVATION_MATRIX.md` — every FORENSIC § green
- `M2_CLOSE_BASELINE_v1_0.md` — sealed, with all 10 quality-bar checks passing
- `chart_facts` table at ~2,000+ rows
- `l25_cgm_edges` at ~339 valid edges across 10+ types
- `rag_chunks` at ~1,250+ chunks across 7+ doc_types
- `audit_events` and `query_plans` tables populated
- `PROSPECTIVE_PREDICTION_LOG_v1_0.md` scaffolded
- 17 retrieval tools live (10 existing + 7 new: chart_facts_query, kp_query, saham_query, divisional_query, domain_report_query, remedial_codex_query, timeline_query)
- Per-tool LLM planner stage live

**Queries that work:**
- "Rank my planets by Shadbala" → numerical answer with citations
- "What is the BAV of my Mars in Capricorn?" → "2 bindu (FORENSIC §7.1)"
- "What is the Sub Lord of my 7th cusp?" → "<actual value> (FORENSIC §4.1)"
- "What is my Saham Mahatmya?" → "11°24′11″ Sagittarius (FORENSIC §12.2)"
- "What does my D27 chart show for Mars?" → varga sign + lagna
- "Which yogas does Mercury participate in?" → graph traversal returns YOG.SARASWATI etc.
- "What does BPHS Ch. 26 say about my Saturn?" → cited from MSR.classical_source
- "What's the falsifier for my Sasha Yoga?" → cited from MSR.falsifier
- "What remedies for my Saturn?" → remedial_codex_query returns prescriptive content
- "What does my chart say about life direction" → no entity seeds, generic synthesis still substantive

**Eval metrics at M2 close:**
- Recall@5 ≥ 0.70 on the 50-query golden set
- Precision@5 ≥ 0.60
- MRR ≥ 0.55
- Per-tool zero_result_rate ≤ 15% on entity-named queries
- temporal latency p95 ≤ 5s (no more 300s timeouts)
- Per-query L2.5 doc_type retrieval ≥ 1 doc_type beyond l1_fact

**Provenance metrics:**
- ≥ 95% MSR → FORENSIC traceability
- ≥ 90% UCN → MSR citation rate
- ≥ 95% CGM SUPPORTS → MSR derivation rate

When all of the above is true, we say "good job done" and M3 opens.

## §12 — What this plan does NOT cover (explicitly out of scope)

Items deferred to later macro-phases per MACRO_PLAN_v2_0.md:

- **M3 work**: Vimshottari sub-period activation in the runtime (M2-A.3 only computes; M3 indexes time-windowed activation). Yogini/Chara/Narayana dasha temporal projection. Tajika annual chart computation for arbitrary years. Transit signal lighting.
- **M4 work**: LEL → signal-activation calibration tables. Per-signal accuracy scoring against life events. Learning loops LL.1–LL.7.
- **M5+ work**: Probabilistic Bayesian network. Confidence-interval-bearing predictions. Population extension. Classical text indexing.

These are real work items; they are simply not in M1/M2 scope per the macro plan.

The L3 → L5 gap (audit_events, query_plans tables) IS in M2-D scope because it's observability infrastructure that M3+ needs to build on. The actual L3 reports, L4 codex, L5 timelines as content already exist; only their retrieval surfaces are scoped here.

## §13 — Open decisions for native review

Before this plan promotes to CURRENT (and into CAPABILITY_MANIFEST), the native should confirm:

- **D1.** Phasing acceptance — does M2-A → M2-B → M2-C → M2-D → M2-E sequencing match expectation, or does the native want to re-order?
- **D2.** Effort estimate acceptance — 25–30 sessions over 5–6 weeks is the working estimate. Is that pace acceptable, or does it need compression / extension?
- **D3.** Quality bar acceptance — the 10 criteria in §1 are the "good job done" definition. Any item the native wants stricter or more relaxed?
- **D4.** Discovery session bandwidth — M2-B.3/.4/.5 require ~5 discovery sessions (Gemini-led with Claude review per existing two-pass protocol). Native-time investment per session is real; confirm appetite.
- **D5.** Parallelization — does the native want all three streams concurrent (faster, more coordination overhead) or single-stream (slower, lower coordination cost)?
- **D6.** Disposition of existing UI/UX stream — the portal redesign is on its own arc (R0–R6 per the redesign tracker). This M1/M2 plan is parallel and disjoint. Confirm: continue UI/UX parallel, or pause until M2 closes?
- **D7.** Promotion path — should this draft become a numbered subphase set (B.6.1, B.6.2, …, B.10.1) of PHASE_B_PLAN, or a sibling planning artifact that augments without renumbering?

---

*End of M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT. Next action: native review of §13 decisions; Phase α audits as the unblocker for everything downstream.*
