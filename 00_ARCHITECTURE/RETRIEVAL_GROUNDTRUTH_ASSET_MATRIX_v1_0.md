---
artifact: RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX
canonical_id: RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX
version: 1.0
status: DRAFT
created: 2026-06-27
author: Cowork (repo audit synthesis) — for native Abhisek Mohanty
classification: D-GROUNDTRUTH deliverable (2 of 4) — the asset-facing face
parent: RETRIEVAL_SYSTEM_DESIGN_APPROACH (§B.2.1)
sourcing: live repo audit (asset_registry seed, CAPABILITY_MANIFEST.json, migration 325, L2_BODHA_RETRIEVAL_STRATEGY, writer code)
changelog:
  - v1.0 (2026-06-27): Initial asset comprehension matrix across L0–L5. Two-catalog reconciliation; per-asset surface (L0/L1/L2 in full, L3/L4/L5 by family); relational/graph spine; dedup/completeness/retrievability doctrine; 8 retrieval archetypes. Built from live repo audit.
---

# RETRIEVAL GROUND-TRUTH — ASSET COMPREHENSION MATRIX (v1.0)

> **What this is.** A thorough comprehension of every asset across L0–L5 — what it is, what it stores, its
> queryable surface, standalone value, cross-asset synergy, and the relational/graph structure — with the
> dedup / completeness / retrievability requirements per asset. It is the asset-facing input to tool-topology
> design (deliverable 2 of 4 of D-GROUNDTRUTH; see `RETRIEVAL_SYSTEM_DESIGN_APPROACH §B.2.1`). This is
> comprehension, not design.

---

## §0 — Two-catalog reconciliation (the first trap)

There are **two distinct catalogs that answer different questions** and are NOT interchangeable:

| Source | What it is | Count | Key |
|---|---|---|---|
| `asset_registry` (seed: `platform/scripts/seed/asset_registry_seed.ts`) | the **operational build catalog** — buildable/queryable runtime assets the orchestrator drives | **81** (bg=22, ga=16, bo=10, ka=12, ph=9, mi=12) | `asset_id` (lowercase `bg_*`…) |
| `CAPABILITY_MANIFEST.json` | the **docs + capability + retrieval-tool catalog** (governance docs, scripts, `*_DB` pointers, tools) | **137** (root, live) | `canonical_id` (UPPERCASE) |

**Two flagged drift risks the design must resolve:**
1. **Two manifest copies disagree** — root `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` = **137 (live)**;
   `platform/00_ARCHITECTURE/` copy = **117 (stale)**. (Earlier "117 assets" readings came from the stale copy.)
2. The classic synthesis artifacts (**MSR/CGM/CDLM/UCN/RM**) are marked **SUPERSEDED** in the manifest —
   they were prose/markdown **rebased into live `bodha_*` DB tables**. The synthesis spine now lives in
   Postgres, not in `025_HOLISTIC_SYNTHESIS/` markdown.

**Rule:** use the **seed** for the queryable surface (count_sql/scope/target_table/depends_on); use the
**manifest** for the docs + retrieval-tool catalog + `expose_to_chat`. They are different sources of truth.

**Build-reality caveat [SUPERSEDED v1.3 — see `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION §1.5 / E1,E2`]:** this
section originally read "L0/L1/L2 built; L3/L4/L5 registered-but-unbuilt." **Code validation REFUTED that:**
writers exist for every ka_*/ph_*/mi_* asset, `transit_search.py` is substantive, and L3/L4/L5 CLOSE seals
exist — the source of that "unbuilt" claim (loaded MEMORY.md) is STALE. The correct framing: **all six layers
have writers**; the real distinction is "L0–L2 mature vs L3–L5 recently-sealed," and the true unknowns are
**runtime/data-population** (has the writer run on the native chart) — a data-plane question deferred to a
controlled prod session, not a code-existence question. NULL floors on `service`-type assets are by design.

---

## §1 — Layer totals (from seed)

- **L0 Brahmagyan (22):** 20 `postgres_table` (global) + 2 `service` (bg_panchanga, bg_ephemeris_engine). Classical/reference substrate, chart-independent.
- **L1 Ganita (16):** all `postgres_table`, all `per_chart`; central store **`chart_facts`** (positions/panchanga/nakshatra write here). Big tables: `chart_dashas` (536,471), `chart_divisionals` (21,635), `ga_structural` emit (77,821).
- **L2 Bodha (10):** `postgres_table` + `pgvector` (bo_bimba, bo_samskara, bo_upaya) + 1 `postgres_view` (bo_samvada=UCD). Writes 26 `bodha_*` tables (migration 325). The synergy spine.
- **L3 Kala (12):** 6 `service` (live-compute) + 6 `postgres_table` (`kala_*`). Floors NULL.
- **L4 Phala (9):** all `postgres_table`, `per_chart`, `phala_*`. Floors NULL.
- **L5 Mimamsa (12):** 10 `postgres_table` + 2 `service`. Floors NULL.

---

## §2 — Per-asset comprehension (condensed; full tables in source audit)

### L0 Brahmagyan (global, chart-independent)
Flat classical reference + prose corpora. Key assets: **bg_ephemeris** (`ephemeris_daily`, Swiss DE441),
**bg_reference** ("holy grail" — 15 typed classical-concept tables), **bg_texts** (`classical_text_chunks`,
indexed verse chunks w/ `embedding` — the prose/citation corpus), **bg_rules** (`sutravali_rules`,
verse-traceable), **bg_yogas/bg_doshas/bg_dasha_systems** (definitions+citations), **bg_remedies**,
**bg_concordance/bg_compendium_index** (cross-school indices), **bg_nakshatra**, **bg_dignity_reference**,
**bg_medical_mappings/bg_nakshatra_medical**, **bg_prashna_rules**, **bg_vastu_directions**,
**bg_transit_engine/bg_transit_rules**, **bg_ontology**, services **bg_panchanga**/**bg_ephemeris_engine**.
*Retrievability:* L0 retrieval tools exposed to chat (read/search classical text, query/read rules) + MCP
resource templates (`…_BY_PLANET`/`…_BY_HOUSE`); the data tables themselves are tool-mediated.

### L1 Ganita (per_chart; count_sql uses `WHERE chart_id=$1`)
Computed chart facts; **`chart_facts` is the spine atom store**; §N.5 authority (L2+ references `fact_id`,
never restates). Root **ga_positions**→`chart_facts`. **ga_structural** = the L1 relational spine (aspects
Parashari/Jaimini/Tajik, yogas, doshas, avasthas, argala, dispositor chains, karaka roles; emit 77,821).
Others: **ga_vargas** (`chart_divisionals`), **ga_dashas** (`chart_dashas`, time-windowed), **ga_strength**
(shadbala/ashtakavarga), **ga_condition** (`ga_condition_composite`, per-graha 0–1), **ga_nakshatra** (KP
sub-lords, dispositor graph), **ga_yoga** (`ga_yoga_firings` + constituent fact_ids), **ga_sensitive**,
**ga_panchanga**, **ga_sade_sati** (time), **ga_tajaka** (varshaphal), **ga_transit_anchors** (gate-1 of
transit subsystem), **ga_vastu**, **ga_medical** (`not_diagnosis=TRUE`), **ga_prashna**.

### L2 Bodha (per_chart; 26 `bodha_*` tables; the synergy/graph spine)
The richest layer. **bo_laksana** = MSR grounded signal store (`bodha_msr_signals`, floor 66,738) — projects
whole-of-L1, one signal per derived fact, THE spine. **bo_bimba** = CGM nodes (pgvector, centrality metrics).
**bo_karanajala** = CGM edges (valenced directed, igraph metrics) — the traversal graph. **bo_samskara** =
signal embeddings (Vertex 768-dim, pgvector). **bo_sangati** = CDLM cross-domain linkage cells (asymmetry +
contradiction flags). **bo_upaya** = RM remediation (6 traditions × 18 categories, pgvector). **bo_samvada** =
UCD unified chart digest (postgres_view — the de-duplicated first-call orientation surface). **bo_drishti** =
question lenses (template + graph-sweep per domain). **bo_anveshana** = discovery engine (non-obviousness,
graph-mining, embedding outliers). **bo_pramana_mapa** = synthesis quality scorecard.

**MSR signal row (`bodha_msr_signals`) — the cross-asset hydration atom.** Carries: `signal_id` (UUID PK),
`chart_id`, `ayanamsha_id`; provenance `source_l1_asset`/`source_subsystem`/**`constituent_facts_array`**
(→ L1 `chart_facts.fact_id`)/**`classical_sources_jsonb`** (→ L0 catalog/rule/chunk ids — the L0 bridge);
salience inputs → `computed_salience`+`salience_formula_version`+CI; `domains_affected_array`/
`domain_salience_jsonb`; graph hooks `graph_edge_pattern_jsonb`; **`contradicts_signals_array`**;
`signal_summary_text` (lossless NL, embedding input); governance `lel_origin`/`epistemic_tier`/
`signature_tier`(chart_defining|major|supporting|background)/`valence`.

### L3/L4/L5 by family (intent, not yet reality)
**L3 Kala (temporal):** services ka_gochara/ka_graha_sancara/ka_dasha_kala/ka_muhurta_seva/ka_tulana (live-
compute); tables ka_yojaka (**the L2→L3 activation hinge** — classifies each L2 signal), ka_sangam
(convergence), ka_vighnakara (obstruction), ka_kalasutra (bounded activation), ka_kala_darshana (view),
ka_jivana_parva (life-arc), ka_bhavishya_lekha (probabilistic projections). *Time-window/dasha-period indexed.*
**L4 Phala (prediction):** ph_nimitta (root, 8 axes), ph_muhurta, ph_sodhana/ph_suddha_sodhana (anomaly +
leakage firewall), ph_pratikara (remedy program), ph_sankrama (spillover cascades), ph_pramana
(falsifiability), ph_phaladesa (7-domain result, B.11), ph_rectification. *Per-domain, per-prediction,
falsifier-keyed.*
**L5 Mimamsa (calibration):** mi_jivanaghatana (held-out LEL ground truth, provenance-isolated), mi_kula
(signal families + negative controls), mi_bhavisya (predictions+falsifiers), mi_pramana (calibration),
mi_gunanaka (learned multipliers), mi_adhilepa (learned-weight overlay L1–L4), mi_sambandha, mi_pariksha
(QA), mi_darshana (pgvector — LLM-ready insight units), mi_seva (serve gateway), mi_abhilekha, mi_vistara.
*Calibration records / learned overlays / insight-unit semantic retrieval.*

---

## §3 — The relational / graph structure (where synergy lives)

Synergy is concentrated in **L2 Bodha**; the linkage primitive is the shared **`signal_id`** (capture-once,
reference-many). Every L2 asset *annotates* signals rather than re-storing them:
- **CGM** (bo_bimba nodes carry `msr_signal_id`; bo_karanajala edges carry `underlying_msr_signal_ids_array`)
  = the traversal graph: directed valenced edges with `relationship_basis`, cross-subsystem flags + L0-grounded
  mapping refs, precomputed metrics (pagerank, betweenness, articulation points, motifs, paths).
- **CDLM** (bo_sangati cells: `shared_signal_ids_array` + `contradicting_signal_pairs_jsonb` +
  `asymmetric_linkage_flag`) = domain×domain synergy/tension matrix.
- **Embeddings** (bo_samskara: one VECTOR(768) per signal_id).
- **Contradictions** (`bodha_contradictions`: FK `signal_a_id`/`signal_b_id`, `tension_class`,
  `resolution_hint_jsonb`) = first-class.
- **Cross-layer resolution (F3 "L2 points DOWN"):** `constituent_facts_array`→L1 `chart_facts.fact_id`
  (exact value); `classical_sources_jsonb`→L0 ids (citation). One hydrated answer = L2 meaning + L1 value +
  L0 citation.

**Spine assets others hang off:** (1) `chart_facts` (L1 atom store), (2) `ga_structural` (L1 relational
source), (3) `bo_laksana`/`bodha_msr_signals` (L2 spine), (4) `bo_bimba`/`bo_karanajala` (CGM traversal
graph), (5) `ka_yojaka` (L2→L3 hinge).

---

## §4 — Dedup / completeness / retrievability doctrine (already load-bearing)

Authoritative: `00_ARCHITECTURE/L2_BODHA_RETRIEVAL_STRATEGY_v1_0.md`.

- **Dedup — F1 "reference-don't-repeat":** the risk is one question hitting msr+cdlm+cgm+ucd+rm and the same
  fact reaching the LLM N× (token bloat AND weighting distortion — a fact seen 5× looks 5× important,
  re-introducing banned double-counting). Rule: **emit each fact ONCE with perspectives attached.** Three
  mechanisms: (1) lens/digest as primary surface + natural de-duplicator (query UCD/lenses first, not 5 raw
  tools); (2) hydration return shape (raw tools return signal_id references + that asset's delta; composition
  resolves each signal_id once); (3) the "reference don't repeat" contract, tested by B6 (same fact_id N× in
  one answer = FAIL).
- **Completeness — full-enumeration parity + aspirational floors:** bo_laksana projects the WHOLE of L1
  (salience is a column never a filter; weak tail kept). `target_floor` aspirational, not a gate (floor =
  achieved count; never fabricate; integrity is the only hard gate). Coverage gate: every `bodha_*` table /
  `source_subsystem` / cross-subsystem edge / discovery reachable; B6 semantic gate above the syntactic gate.
- **Retrievability — hybrid:** `bg_texts.embedding` + `bodha_signal_embeddings`/`bodha_cgm_nodes` 768-dim
  (HNSW) for semantic; `classical_sources_jsonb`+`constituent_facts_array` for structured cross-layer
  hydration. Canonical pattern: **query UCD (de-duplicated orientation) first → drill via zoom/lens/
  domain-evidence**, "targeted, not five scattershot asset calls." No tier gating.
- **LEL toggle (provenance firewall):** every L2 tool + serve layer accepts `lel_enabled` (default FALSE =
  pure deterministic, zero `lel_origin` elements; ON = additive calibration overlay, stated in provenance).
  Hard transitive filter keyed on `lel_origin`.

---

## §5 — Asset families by retrieval character (8 archetypes → topology input)

This grouping (not a tool design) tells topology what each asset *needs*:

1. **Flat-fact emitters (single keyed lookup)** — L0 reference tables; most L1 per-graha/point facts
   (ga_positions, ga_strength, ga_condition, ga_panchanga, ga_transit_anchors). Exact lookup by key
   (chart_id + graha|house|sign|point|direction|body-part). Global (L0) vs per_chart (L1) split matters.
2. **Prose / citation corpora (hybrid vector)** — bg_texts, bg_rules, bg_concordance, bg_compendium_index,
   bg_remedies; mi_darshana. Semantic + keyword + topic-tag; carry embeddings; tool-mediated, never raw dumps.
3. **Rich relational / multi-view assets** — ga_structural (L1), bo_laksana/MSR (L2). Filter by
   source_subsystem / signature_tier / domains / valence; one signal carries dozens of facets. The F1
   "one entry, many perspectives" assets.
4. **Graph / traversal assets** — bo_bimba + bo_karanajala + CGM motif/path/subgraph. Node-fetch by
   centrality, edge-fetch by relationship_basis/valence, recursive traversal, motif/path retrieval, +
   VECTOR(768) node similarity. The synergy/contradiction substrate.
5. **Cross-domain / linkage + contradiction assets** — bo_sangati (CDLM), bodha_contradictions, ph_sankrama.
   By (domain×domain), asymmetry/contradiction flags, shared-signal sets. "How does A relate to / conflict with B."
6. **Temporal / time-indexed assets** — L3 Kala family + L1 ga_dashas/ga_tajaka/ga_sade_sati + L3 services.
   Time-window / dasha-period / date-range; services are call-not-query.
7. **Orientation / digest + discovery assets (the de-dup surface)** — bo_samvada (UCD, first-call gestalt),
   bo_drishti (lenses), bo_anveshana (discoveries). "Whole picture" / "answer domain-question" / "surprise me."
   The PRIMARY surfaces; raw asset tools are secondary hydration.
8. **Calibration / governance / quality assets** — bo_pramana_mapa + L5 mi_* family + mi_seva/mi_vistara.
   By build_id / prediction_id / outcome; overlays applied at serve-time; held-out LEL provenance-isolated.

---

## §6 — Cautions for tool-topology design

- Use the **seed** for queryable surface, the **manifest** for docs/tools/`expose_to_chat`; they are not
  interchangeable, and the two manifest copies disagree (root 137 live vs platform 117 stale) — resolve.
- **L0/L1/L2 = reality; L3/L4/L5 = intent.** Design built layers deeply; clean extension hooks for the rest.
- The dedup/retrieval doctrine (F1 reference-don't-repeat, F3 layer-resolution-DOWN, UCD-first orientation,
  LEL toggle) is **already specified and load-bearing** — topology must honor it: one signal once with
  perspectives attached; resolve DOWN the layers; default deterministic. **This means the umbrella-then-drill
  topology is already doctrine for L2 (`query_ucd` first → drill) — topology work extends a proven pattern,
  not a blank slate.**

**Files of record (absolute):**
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (live, 137);
`platform/scripts/seed/asset_registry_seed.ts` (81 assets);
`platform/migrations/325_l2_bodha_enriched_schema.sql` (26 `bodha_*` schemas);
`00_ARCHITECTURE/L2_BODHA_RETRIEVAL_STRATEGY_v1_0.md` (F1/F3/LEL/tool set);
`platform/python-sidecar/ga_writers/` (L1 writer code).

*End of RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX v1.0 — D-GROUNDTRUTH deliverable 2 of 4.*
