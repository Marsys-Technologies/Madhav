---
artifact: L2_BODHA_OVERALL_APPROACH_v1_0.md
canonical_id: L2_BODHA_OVERALL_APPROACH
version: 1.0
status: APPROACH_FOR_NATIVE_REVIEW
authored_by: Cowork (grounded in live code + the v2.0 build) 2026-06-19
purpose: >
  The single overall approach for the ENTIRE L2 Bodha layer, grounded in the ACTUAL built state
  (ga_structural v2.0 = 106,103 rows / 69–72 categories; 14 L1 assets; the real bodha_* schemas; the
  live L0/L1 retrieval registry). Written so the layer is addressed end-to-end with no miss, structured
  efficiently, and adheres to the two pillars (completeness + retrievability) — and so its outcome
  dovetails with the L0 → L1 → L2 arc. NOT a per-asset brief; this is the governing approach the
  per-asset briefs will implement.
grounded_against:
  - ga_structural v2.0 — GA_STRUCTURAL_REBUILD_VERIFY_v2_1 (build a712b250, 106,103 rows, 72 cats, L1-authority-clean)
  - 14 L1 ga_ assets (positions/vargas/strength/sensitive/sade_sati/panchanga/dashas/tajaka/condition/structural/medical/vastu/prashna/yoga)
  - bodha_* schemas — migration 226 (22 tables + 8 MVs); bodha_msr_signals real column set
  - L0/L1 retrieval registry — platform/src/lib/retrieval/registry/layers/{L0_brahmagyan,L1_ganita}
  - L2_BODHA_MASTER_PLAN_v3_0 (dual-capture) + L2_BODHA_ASSET_TABLE_BRIEF_MAP_v1_0 (asset↔table↔brief)
---

# L2 Bodha — Overall Approach v1.0 (grounded in the live build)

## §0 — Where we actually are (verified against code + DB, not the handoffs)
- **L1-E is DONE.** The ga_structural v2.0 rebuild (build `a712b250`, PR #301 merged, HEAD past it) already
  delivered the enrichment we were designing: **106,103 rows, 72 categories, all 30 vargas × 5 ayanamshas**,
  graph-theoretic layer present + per-varga (`graha_centrality`, `dispositor_tree`, `chart_center_of_gravity`,
  `significator_path`, `convergence_count`, `karaka_bhava_concordance`, `virupa_drishti`, `sambandha_grade`,
  `bhava_significance_link`, `net_argala_per_varga`), FORENSIC 7/7, **L1-authority-clean** (all refs resolve).
  → The L1-E brief is SUPERSEDED-BY-REALITY; archive it.
- **The bodha_* tables are BUILT** (migration 226: 22 tables + 8 MVs). The schemas are rich (bodha_msr_signals
  ~50 cols, with explicit hook-columns for every downstream asset — graph hooks, resonance hooks, UCN/digest
  hooks). **The tables are empty — no writer has run.**
- **0 of 8 writer briefs exist.** This is the work: author the 8 per-asset build briefs, in DAG order.
- **2 seed fixes pending** (bo_upaya owns resonances + summed count_sql; bo_samvada → UCD/none).
- **L1 is 14 assets, not 5** (positions, vargas, strength, sensitive, sade_sati, panchanga, dashas, tajaka,
  condition, structural, medical, vastu, prashna, yoga) — "project the whole of L1" means ALL of these at
  native grain, plus ga_structural's relational surface. This is bigger than earlier framing.
- **The retrieval registry is real + layered** (`registry/layers/L0_brahmagyan`, `L1_ganita`). L2 EXTENDS it
  (a new `L2_bodha` layer of tools), never builds a parallel one.

## §1 — The two pillars, restated as the acceptance for the whole layer
Everything below serves exactly two things; if a design choice serves neither, it is out.
1. **COMPLETENESS** — every deterministic fact + every deterministic relationship + every population-level
   pattern (convergence/contradiction/graph property) is CAPTURED. No curation, no threshold-drop; weak tail
   kept and ranked. Completeness is measured against the full L1 population (14 assets + ga_structural), not
   a subset.
2. **RETRIEVABILITY** — every captured thing is REACHABLE by the synthesis LLM through a retrieval tool, WITH
   its provenance (L1 fact_id), its classical citation (L0), its epistemic tier, and its salience — and
   semantically (embeddings), not just by column filter. Retrievability is proven by the B6 eval harness, not
   assumed from per-table coverage.

## §2 — The dovetail: how L2 completes the L0 → L1 → L2 arc
The instrument is one spine; L2 is the layer where the lower two become *answerable*.
- **L0 (Brahmagyan)** = global classical knowledge (catalogs, rules, 8,193 text chunks + Vertex embeddings).
  *Today it is an island* — only bo_upaya touches it. **L2's job: bridge every signal to L0** so retrieval
  returns the fact WITH its classical voice. The L0 retrieval tools already exist; L2 connects them to chart
  signals via `classical_sources_array` + shared embedding space (same Vertex model L0 uses).
- **L1 (Gaṇita)** = this chart's deterministic facts (14 assets) + ga_structural's relational fabric.
  *Today it is complete but flat* — facts and relationships, no significance. **L2's job: project ALL of it
  and add the population-level meaning** (rank, convergence, contradiction, domain-salience, graph centrality)
  that no single L1 fact can know about itself.
- **L2 (Bodha)** = the projection + significance + classical-grounding + retrieval surface. Its output is what
  L3 Kāla (time) activates, L4 Phala (prediction) reasons over, and L5 Mīmāṃsā (learning) corrects. So L2's
  table/column shapes must be **stable contracts** the upper layers depend on — designed once, versioned.
- **The clean line (three-tier boundary, already ratified):** 1 entity, no meaning → L1 value-asset;
  2+ entities + fixed rule + no life-meaning → ga_structural; 2+ entities + LIFE-MEANING/domain/salience → L2.
  L2 is where MEANING is assigned to ga_structural's meaning-free relationships. L2 never re-computes an L1
  value (Trap 1) and never lets human/LLM judgment into what fires (Trap 2).

## §3 — The architecture in one picture
```
L0 Brahmagyan  ─┐  (catalogs, bg_rules, bg_texts+embeddings; retrieval tools exist)
                │        ▲ classical bridge (classical_sources_array + shared embedding space)
L1 Gaṇita ──────┤        │
  14 value-assets│       │   project whole of L1 (native grain) ┐
  + ga_structural│───────┼──────────────────────────────────────┤
   v2.0 (106k,   │       │   project relational surface (refs)   │
   graph-theoretic)      │                                       ▼
                 └──────────────────────►  L2 BODHA  ┌─ bo_laksana (MSR) = the root projection + significance
                                                     ├─ bo_sangati (CDLM)      domain linkage + convergence
                                                     ├─ bo_bimba/bo_karanajala (CGM)  the graph (invest deepest)
                                                     ├─ bo_samskara            real Vertex embeddings (1:1)
                                                     ├─ bo_upaya (RM)          remedies grounded to L0
                                                     ├─ bo_samvada (UCD)       read-side digest (view+tool)
                                                     └─ bo_pramana_mapa        quality scorecard + Trap-1 audit
                                                            │
                                                            ▼  retrieval tools (extend the registry) + B6 eval gate
                                                     L3 Kāla → L4 Phala → L5 Mīmāṃsā
```

## §4 — The build sequence (DAG order; one closed, verified brief per asset)
**Batch 1 — the root (everything depends on it; prove it before fan-out):**
- **bo_laksana (MSR)** — projects the WHOLE of L1 (ga_structural relational surface — reading refs from
  `fact_value_jsonb.constituent_fact_ids` ∪ base ∪ D1-per_varga — AND the 14 value-assets at native grain).
  Adds salience (salience_formula_v1), rank, domain/tradition tags, fact_kind typing, the L0 classical bridge,
  and a lossless signal_summary_text. **Gate: the anti-drift spine** — every `constituent_facts_array` element
  resolves to a real L1 fact_id; count parity vs the full L1 signal population; FORENSIC anchors inherit L1
  values. Proven on bo_laksana ALONE before Batch 2.

**Batch 2 — the fan-out (parallel on bo_laksana):**
- **bo_sangati (CDLM)** — domain×domain linkage + `bodha_convergence` (convergence-density-per-domain).
- **bo_karanajala (CGM edges) + bo_bimba (CGM nodes)** — the graph; **invest deepest**. ga_structural ALREADY
  computed centrality/dispositor-tree/paths per-varga — bo_karanajala/bimba PROJECT + extend these into the
  CGM tables (nodes with centrality, edges with the full value vector, motifs, paths, `bodha_contradictions`).
  This is the highest-leverage asset for synthesis.
- **bo_samskara (embeddings)** — REAL Vertex AI `text-multilingual-embedding-002` (768-dim, the SAME model L0
  bg_texts uses → signals share the classical-text vector space → signal↔citation similarity bridge). 1:1 with
  MSR signals. (The merged scaffold uses a hash placeholder — replace it.)
- **bo_samvada (UCD)** — Option A read-side: `vw_chart_digest` view + `query_ucd` tool. Not a writer.

**Batch 3 — dependents + scorecard:**
- **bo_upaya (RM)** — 6 tables; remedies grounded to L0 `brahma_remedy_corpus` (every remedy cited).
- **bo_pramana_mapa** — global `synthesis_quality_scorecard` with the standing Trap-1 audit baked in.

**Then:** extend the retrieval registry with an `L2_bodha` tool layer (≥1 tool per bodha_* table + the
convergence/contradiction/digest/path tools) + the coverage gate; flip DRAFT→CURRENT; **B6 semantic-
completeness eval harness GATES the seal**; author L2_BODHA_CLOSE with the L3 Kāla onboarding contract.

## §5 — The cross-cutting design rules (apply to EVERY asset — this is what prevents a miss)
1. **Read refs from `fact_value_jsonb.constituent_fact_ids`** (ga_structural v2.0 reality — NOT a chart_facts
   column). Every Bodha writer that cites L1 uses this path. (bodha_msr_signals' OWN `constituent_facts_array`
   column is where L2 STORES the refs it read — distinct from L1's storage.)
2. **Dedup by ownership (capture-once, reference-many).** L1 values owned by their asset; relationships owned
   by ga_structural; significance owned by L2. Two L2 signals are duplicates iff same fact_kind + same
   constituents + same configuration. Weak-but-real never dropped.
3. **fact_kind typing end-to-end** (relationship / magnitude / position / time_window / birth_moment) so the
   LLM knows what KIND of fact each signal is.
4. **L0 classical bridge on every matchable signal** (classical_sources_array from catalogs + bg_rules +
   bg_texts) — the dovetail that ends L0's island status.
5. **Real embeddings, shared vector space** (Vertex model = L0's) — semantic retrievability + signal↔citation.
6. **Lossless signal_summary_text** (deterministic template, iterate ALL configuration_jsonb keys) — the dense
   surface the LLM reasons over + the embedding input.
7. **Versioned deterministic formulas only** (Trap 2). No narrative in the asset. Provenance + tier on every
   row and every retrieval return.
8. **FROZEN orchestrator contract** + **floors aspirational** + **no silent drops** + **verify against PROD +
   per-category evidence + acharya correctness, never raw counts**.

## §6 — Why this is efficient AND complete (the structure choice)
- **One root, fan-out, dependents** — the DAG means each asset is built once on a verified upstream; no asset
  re-derives another's work (CGM projects ga_structural's pre-computed graph; CDLM reads MSR; embeddings read
  MSR's summary text). No duplication of compute or storage.
- **The hook-columns already exist** in bodha_msr_signals (graph hooks, resonance hooks, digest hooks) — the
  schema was designed for this fan-out, so each downstream asset reads a ready-made hook rather than recomputing.
- **Completeness is bounded by L1's finite combinatorics** (projection, not generation), so "capture everything"
  is achievable, not open-ended.
- **Retrievability is proven, not assumed** — the eval harness (B6) is the gate, so we cannot declare done on
  syntactic coverage alone.

## §7 — The open decisions to settle before authoring Batch 1 (for native)
1. **Brief granularity** — one brief per asset (8 briefs, max review control) vs batched (3 briefs). Recommend
   per-asset for the root + graph; batched for the rest.
2. **bo_laksana projection breadth** — confirm ALL 14 L1 value-assets are in-scope for MSR projection (not just
   the original 5). My read: yes, per "whole of L1" — but medical/vastu/prashna are newer; confirm they project.
3. **Seed fixes timing** — apply the 2 pending seed fixes (bo_upaya/bo_samvada) before or with Batch 1.
4. **bo_bimba/bo_karanajala split** — one heavy CGM writer emitting both, or two? (A12 is one igraph compute.)
5. **Eval harness scope** — the known-complete answer-sets for B6: which domains/questions define "complete."

---
*End of L2_BODHA_OVERALL_APPROACH v1.0. Grounded in the live build (ga_structural v2.0 = 106,103 rows / 72
cats / L1-authority-clean; 14 L1 assets; real bodha_* schemas; layered retrieval registry). The approach:
project the WHOLE of L1 (relational surface + 14 value-assets) into MSR as the root, fan out to CDLM + the
CGM graph (deepest) + real embeddings + UCD, ground every signal to L0's classical corpus, prove the
anti-drift spine + semantic completeness, and shape every table as a stable contract for L3→L4→L5. Two
pillars (completeness + retrievability) are the whole-layer acceptance; the eval harness gates the seal.*
