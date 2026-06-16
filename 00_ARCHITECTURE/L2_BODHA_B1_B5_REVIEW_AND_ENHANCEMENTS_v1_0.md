---
artifact: L2_BODHA_B1_B5_REVIEW_AND_ENHANCEMENTS_v1_0.md
canonical_id: L2_BODHA_B1_B5_REVIEW
version: 1.0
status: REVIEW (companion to CLAUDECODE_BRIEF_BODHA_B1_FULL_PROJECTION_v1_0.md)
authored_by: Cowork 2026-06-16
purpose: >
  Elaborate, phase-by-phase narration of the Bodha B1–B5 build — what each phase does, which assets
  and tables it creates, derived volumetric estimates with confidence flags, and a prioritized set of
  enhancements. Every recommendation is driven by ONE objective: the synthesis LLM, querying these
  assets through retrieval tools, must receive the deepest, most thorough, most relevant information
  possible. Volumetrics are DERIVED (basis stated); the load-bearing unknown is B1's true signal count
  under full-enumeration parity (the spec's ~800–1,250/ayanamsha predates that decision).
volumetric_anchor: ga_structural = 74,644 facts (live, native chart 482012f1, all vargas × 5 ayanamshas)
---

# L2 Bodha — B1→B5 Review, Assets, Volumetrics & Enhancements

## §0 — How to read the volumetrics (confidence discipline)
- **HARD** = a live or schema-fixed number (e.g. `ga_structural = 74,644`).
- **DERIVED-HIGH** = computed from a hard number × a fixed grain (e.g. nodes = entities × snapshots).
- **DERIVED-LOW** = depends on B1's true signal count, which is the open variable until B1 runs.
- The single number that drives the whole layer is **B1's signal count under full-enumeration parity.**
  The A10 spec's "~800–1,250 per ayanamsha (~4–6k per chart)" was written for the *curated subset*.
  Full projection of ga_structural's relational fabric makes the realistic B1 count **far higher** —
  see §B1. Every downstream estimate is given as a band BECAUSE of this.

---

## §B1 — bo_laksana (MSR): the root projection
**What it does.** Projects every L1 `ga_structural` relational fact (+ the named sensitive / sade-sati
/ panchanga signal categories) into one `bodha_msr_signals` row per fact, for the native chart across
5 ayanamshas. It does NOT re-fire predicates and does NOT re-derive strength — it inherits the L1
`fact_id` by reference (`constituent_facts_array`) and ADDS the population-level enrichment:
`computed_salience` (via `salience_formula_v1`), `top_k_salience_rank` (across the full population),
domain tagging, tradition tagging, epistemic tier carried from L1. Strength is a COLUMN, never a
filter — the weak tail is kept (no-threshold-drop).

**Assets / tables created.**
- `bodha_msr_signals` (~50 columns) — the keystone signal store. One row per projected fact.
- 3 materialized views (A10 §11): `mv_msr_top_signals_per_chart` (top-100 by salience per ayanamsha),
  `mv_msr_recurring_patterns_per_chart`, `mv_msr_domain_summary`.

**Volumetrics.**
- ga_structural facts projected: **74,644 HARD** (the relational fabric — every aspect/conjunction/
  dispositor/parivartana/argala/composite/avastha across 30 vargas × 5 ayanamshas, nodes in every loop).
- Plus sensitive/sade-sati/panchanga signal categories: **~12–15k DERIVED-LOW** (ga_sade_sati alone is
  11,019; sensitive + panchanga add the rest).
- **`bodha_msr_signals` total ≈ 85,000–90,000 rows DERIVED-LOW.** (Contrast: the curated-subset build
  the spec assumed would have been ~4–6k. Full parity is ~15–20× that — this is the intended jump.)
- Per ayanamsha ≈ 17,000–18,000 signals.
- 3 MVs: top_signals = 100/ayanamsha × 5 = 500; domain_summary = 7 domains × 5 = 35; recurring_patterns
  = small (DERIVED-HIGH, all small).

**The acceptance that gates everything:** every signal's `constituent_facts_array` resolves to a real
`chart_facts.fact_id` (zero unresolved), and the MSR count *tracks* the projected ga_structural count
(parity). Proven on bo_laksana ALONE before any fan-out.

---

## §B2 — the fan-out (5 assets, parallel on bo_laksana)

### bo_sangati (CDLM, A11) — cross-domain linkage + convergence
**What it does.** Aggregates MSR signals by the life-domains they touch into a domain×domain linkage
structure: a static natal 9×9 (+ 27×27 sub-domain) grid, dynamic 9×9 snapshots per (Maha-lord,
Antar-lord) across 3 dasha systems, per-tradition views, chart summary, detected pattern clusters,
evolution gradients — PLUS the first-class `bodha_convergence` (convergence-density-per-domain:
N independent signals → one domain = weight of evidence, via `convergence_formula_v1`).

**Tables:** `bodha_cdlm_cells`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_chart_summary`,
`bodha_cdlm_pattern_clusters`, `bodha_cdlm_evolution_gradients`, **`bodha_convergence`** + 5 MVs.

**Volumetrics (per chart, summed over 5 ayanamshas):**
- `bodha_cdlm_cells`: static 9×9=81 + sub-domain 27×27=729, × dynamic snapshots (≈ Maha×Antar combos
  across 3 systems → hundreds of snapshots × 81 cells). **≈ 40,000–80,000 cells DERIVED-LOW** (dynamic
  snapshot count is the driver; bounded by dasha-period combinatorics).
- `bodha_convergence`: 7 domains × snapshot set × 5 ayanamshas → **~2,000–5,000 rows DERIVED-LOW.**
- rollups/summary/clusters/gradients: **~3,000–8,000 combined DERIVED-LOW.**
- **bo_sangati summed count ≈ 50,000–95,000 rows.**

### bo_karanajala (CGM edges) — the graph (invest deepest)
**What it does.** Builds the structural graph in-memory (igraph) and materializes it: nodes' and edges'
graph-theoretic metrics (PageRank, eigenvector/betweenness/harmonic centrality via
`centrality_formula_v1`), sub-graphs, ~30–50 classical motifs, topology summaries, the §13.1
`bodha_cgm_paths` (significator path-analysis, final-dispositor convergence), and the first-class
`bodha_contradictions` (signals in structural tension — the drift guardrail).

**Tables:** `bodha_cgm_edges`, `bodha_cgm_sub_graphs`, `bodha_cgm_motifs`,
`bodha_cgm_chart_topology_summary`, **`bodha_cgm_paths`**, **`bodha_contradictions`**.

**Volumetrics (per (chart, ayanamsha), × 5, × snapshots):**
- Edges: ~500–1,500 per snapshot (HARD-ish from spec). static_natal ≈ 1,000. With the snapshot family
  (static + dynamic-maha + tradition + sade-sati-phase), **≈ 30,000–90,000 edges DERIVED-LOW.**
- Motifs: 30–50 library × snapshots → ~1,500–3,000. Sub-graphs: ~hundreds. Topology summaries: ~45/aya.
- `bodha_cgm_paths`: significator pairs × paths → ~2,000–6,000 DERIVED-LOW.
- `bodha_contradictions`: contradiction-pairs over the signal population → ~500–3,000 DERIVED-LOW.
- **bo_karanajala summed count ≈ 35,000–100,000 rows.**

### bo_bimba (CGM nodes) — the node face on the same igraph compute
**What it does.** The nodes-only registry over the same graph: grahas, houses, signs, special points
(Sahams/Arudhas/Karakas/midpoints), configurations (one node per fired MSR signal), domains, dasha
lords, pattern-cluster refs — each carrying its centrality columns.

**Tables:** `bodha_cgm_nodes`.
**Volumetrics:** ~200–300 nodes per snapshot (HARD from spec §3). × snapshot family × 5 ayanamshas →
**≈ 8,000–20,000 nodes DERIVED-LOW.**

### bo_samskara (embeddings) — 1:1 with MSR signals
**What it does.** One embedding row per MSR signal for vector retrieval. **Current writer uses a
deterministic `placeholder_hash_v1` (768-dim), NOT real semantic embeddings.**

**Tables:** `bodha_signal_embeddings` (pgvector).
**Volumetrics:** exactly 1:1 with `bodha_msr_signals` → **≈ 85,000–90,000 rows DERIVED-LOW** (tracks B1).

### bo_samvada (UCD, A14) — read-side join, NOT a writer
**What it does.** A unified chart-digest read surface: `vw_chart_digest` view + `query_ucd` tool.
Joins the chart_summary rows from the other assets into one digest the LLM can pull in a single call.
**Tables:** none written (a VIEW + a tool). **Volumetrics:** N/A (read surface).

---

## §B3 — bo_upaya (RM): remedies, grounded to L0
**What it does.** Computes the resonance map of weakest grahas (via `resonance_score_v1`), then
per-tradition × per-category remedy prescriptions (via `resonance_match_score_v1`), dasha-windowed
temporal calibration, per-dosha bundles, pattern/motif remedy themes, chart-level priority + intensity
profile + chronobiology timing. Every remedy is labelled from `brahma_remedy_corpus` (L0, 260
remedies) and carries a classical citation — grounded, never invented.

**Tables (6):** `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`,
`bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies`,
+ the 6th (chart-level priority/sequence). Includes an HNSW vector index on prescription embeddings.

**Volumetrics (per chart, × 5 ayanamshas):**
- resonances: ~9 grahas × 5 = ~45 (HARD-ish).
- prescriptions: weakest targets × 6 traditions × 18 categories → **~3,000–8,000 DERIVED-LOW.**
- dasha-windowed: prescriptions × active windows across 3 systems → **~10,000–30,000 DERIVED-LOW** (the
  driver; bounded by dasha-period count).
- dosha bundles + pattern remedies + priority: **~1,000–3,000 combined.**
- **bo_upaya summed count ≈ 15,000–40,000 rows.**

---

## §B4 — bo_pramana_mapa (scorecard) + UCD read surface
**What it does.** A global `synthesis_quality_scorecard` measuring the layer's own integrity — with the
**Trap-1 audit baked in** (re-checks that every `constituent_facts_array` resolves, turning the
anti-drift spine into a standing metric, not a one-time check). Confirms the UCD read surface returns
the unified digest.
**Tables:** `synthesis_quality_scorecard` (global, small). **Volumetrics:** tens of rows (HARD-small).

---

## §B5 — orchestrator full-layer build + cockpit verify + retrieval tools + seal
**What it does.** One orchestrator run (`POST /api/cockpit/runs scope=layer/bodha`) builds the whole DAG
in dependency order; cockpit/Atlas light all 8 `bo_*` assets with true summed counts; `target_floor` =
achieved; ≥1 retrieval tool per `bodha_*` table is added to the existing retrieval layer + the CI
coverage gate; the 8 registry rows flip DRAFT→CURRENT; `L2_BODHA_CLOSE` is sealed with the L3 onboarding
contract; CURRENT_STATE + SESSION_LOG updated.
**Assets created:** none new — this is the integration/verification/seal phase.

---

## §SUMMARY — the whole layer at a glance
| Phase | Asset(s) | New tables | Est. rows (native chart, all 5 ayanamshas) | Confidence |
|---|---|---|---|---|
| B1 | bo_laksana | bodha_msr_signals + 3 MVs | **~85,000–90,000** | DERIVED-LOW (the driver) |
| B2 | bo_sangati | 6 tables + 5 MVs | ~50,000–95,000 | DERIVED-LOW |
| B2 | bo_karanajala | 6 tables | ~35,000–100,000 | DERIVED-LOW |
| B2 | bo_bimba | bodha_cgm_nodes | ~8,000–20,000 | DERIVED-LOW |
| B2 | bo_samskara | bodha_signal_embeddings | ~85,000–90,000 (1:1 w/ MSR) | DERIVED-LOW |
| B2 | bo_samvada | vw_chart_digest (view) + tool | n/a (read surface) | — |
| B3 | bo_upaya | 6 RM tables | ~15,000–40,000 | DERIVED-LOW |
| B4 | bo_pramana_mapa | synthesis_quality_scorecard | tens | HARD-small |
| B5 | (integration) | none | — | — |
| **TOTAL** | **8 assets** | **~25 bodha_* tables + 8 MVs** | **≈ 280,000–440,000 rows** | **DERIVED-LOW** |

The layer's total is dominated by B1 and its two 1:1/aggregate dependents (embeddings, cells, edges).
**The single most important number to capture at B1 run time is the real signal count** — it
re-anchors every band above. Set `target_floor` = achieved for each, per the floors-aspirational rule.

---

## §ENHANCEMENTS — driven by ONE goal: the synthesis LLM gets the deepest, most relevant context
The objective is not "store data" — it is that an LLM, at query time, retrieves through tools the
deepest, most thorough, most RELEVANT slice of this corpus and synthesizes acharya-grade narrative.
Ranked by leverage toward that goal.

### E1 — Real semantic embeddings (highest leverage; currently a placeholder) **[recommend: do before seal]**
`bo_samskara` writes `placeholder_hash_v1` (deterministic hash, NOT semantic). Semantic similarity
retrieval — "find signals related to *career instability* even if they don't share keywords" — is the
single biggest lever on RELEVANCE, and it's the one thing currently faked. Recommendation: generate a
natural-language descriptor per signal deterministically (template over the structured columns), embed
it with a real model (the embedding step is a deterministic transform — allowed under deterministic-
first), store in `bodha_signal_embeddings`. Until then, retrieval is keyword/column-filter only and the
LLM cannot find conceptually-near signals. **This is the gap most likely to cap synthesis quality.**

### E2 — A retrieval-shaped "signal narration" column on every MSR signal **[recommend: high]**
The LLM synthesizes from rows; a row of 50 numeric/coded columns is hard to reason over. Add a
deterministic, template-generated `signal_summary_text` (e.g. "Jupiter–Venus conjunction in D1
Sagittarius (Lahiri), within 2° orb, salience 0.81, top-12 in chart, supports career+spirituality,
two-pass verified, cites Phaladeepika 6.12"). Deterministic (no LLM in the build), but gives the
synthesis LLM a dense, citable sentence per signal — dramatically better than reconstructing meaning
from columns. Doubles as the embedding source for E1.

### E3 — Make convergence + contradiction the PRIMARY retrieval surface, not a side table **[recommend: high]**
The acharya-grade move is "weight of evidence," not isolated rules. Ensure the retrieval tools expose
`bodha_convergence` and `bodha_contradictions` as FIRST-CLASS query targets with rich return shapes:
"the 5 strongest convergences in this chart, each with its N constituent signals and their citations,"
and "the active contradictions, each with both sides and the deterministic tension basis." This is
where the LLM stops sounding like a rule-lookup and starts sounding like an acharya weighing evidence.
Add a tool: `query_chart_convergences(chart_id, domain?, top_k)` and
`query_chart_contradictions(chart_id, domain?)`.

### E4 — A single "deep digest" retrieval tool over UCD (one call → the whole skeleton) **[recommend: high]**
`bo_samvada`/`query_ucd` already joins chart summaries. Make it the LLM's *first* call: one tool that
returns the chart's skeleton — top-N salient signals, the domain convergence map, the active
contradictions, the graph's center-of-gravity (final dispositor + top-centrality nodes), and the
weakest-graha resonance targets — each as a citable summary with drill-down IDs. This gives the LLM
orientation before it drills, so its follow-up queries are targeted (relevant) instead of scattershot.

### E5 — Provenance + epistemic tier in EVERY tool return (never strip it) **[recommend: medium-high]**
For the LLM to say "high-confidence" vs "classical-but-unverified," every retrieval return must carry
`epistemic_tier`, `salience`, `citation_human`, and the constituent `fact_id`s. The brief already says
"don't strip tier" — make it an explicit retrieval-contract test: a tool that returns a signal without
its tier + citation fails CI. This is what lets the LLM be honest about confidence (a core project value).

### E6 — Graph path-analysis as a narratable "reasoning chain" tool **[recommend: medium]**
`bodha_cgm_paths` holds significator→significator paths. Expose a tool that returns the path between two
domains/significators as an ordered, citable chain ("10th-lord → dispositor Saturn → aspected by Jupiter
→ ...") so the LLM can narrate the *mechanism*, not just the conclusion. This is "reveals things I
wouldn't have seen on first pass" territory — the deterministic graph hands the LLM a reasoning spine.

### E7 — Cross-ayanamsha consistency as a relevance/confidence signal **[recommend: medium]**
A signal firing 5/5 ayanamshas is more robust than one firing 2/5. Ensure `cross_ayanamsha_consistency_
score` is computed at B1 (it's a column already) and exposed in retrieval, so the LLM can prioritize
ayanamsha-stable signals and caveat the unstable ones. Within-chart, deterministic — squarely L2, not L5.

### E8 — Weak-tail retrievability proof (don't just keep it — prove the LLM can reach it) **[recommend: medium]**
Keeping the weak tail (no-threshold-drop) only helps if retrieval can *reach* it. Add a test: a known
low-salience signal is returnable via pagination (never LIMIT-dropped). Completeness without
retrievability is dead storage — the project's two pillars must meet here.

### Sequencing recommendation
- **Before L2 seal:** E1 (real embeddings), E2 (narration column), E3 + E4 (convergence/contradiction
  + deep-digest tools), E5 (provenance contract test). These define whether the synthesis LLM gets
  acharya-grade context or column-soup.
- **Fast-follow (post-seal, pre-L3):** E6 (path tool), E7 (cross-ayanamsha), E8 (weak-tail proof).
- E1 + E2 are coupled (E2 feeds E1's text) — do them together.

---
*End of L2_BODHA_B1_B5_REVIEW v1.0. Volumetrics derived from ga_structural=74,644 HARD; the layer is
~280k–440k rows, dominated by B1 and its 1:1/aggregate dependents; the load-bearing unknown is B1's
true signal count under full-enumeration parity. Enhancements are ranked by leverage toward the single
goal: the synthesis LLM, querying through retrieval tools, receives the deepest, most relevant,
provenance-bearing, semantically-reachable context the deterministic corpus can offer.*
