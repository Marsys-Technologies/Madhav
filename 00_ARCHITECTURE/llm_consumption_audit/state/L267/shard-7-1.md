# Shard 7-1 — SYNTHESIS-CEILING (Lane 7)

**Charter §4 class 8 — UN-SYNTHESIZABLE AT SCALE**
**Heavy question:** "Whole-chart contradictions synthesis across all signals — L2"
**Chart:** 482012f1-710e-4a25-994a-93821f5871aa (Abhisek)
**Channel:** deployed MCP connector (read-only), 130 tools enumerated.
**Verdict:** CEILING HIT. No served path composes the factors this question needs. The contradiction-synthesis capability does not exist end-to-end; every serving path degrades to a flat top-K digest over a ~300-signal candidate window, and the one full-payload escape hatch does not honor its own documented limit.

---

## 1. Factor budget the question actually requires

To answer "whole-chart contradictions across ALL signals" at acharya grade, the composer must reach and reconcile:

| Corpus | Count (from live digest) | Why needed |
|---|---|---|
| MSR signals | **13,364** | contradiction = two signals of opposing valence bearing on the same domain/entity/topic; you must scan the whole set, not a top-K |
| Yogas | 15 | promise-side of promise/denial tensions |
| Doshas | 22 | denial/affliction side |
| Convergence domains | 6 (career 12,364 conv; character 7,294; relationship 7,014; spirituality 3,338; wealth 2,003; health 748) | valence-weighted convergence vs. contradiction per domain |
| CDLM cross-domain cells | ≥5 per domain | cross-domain contradiction (a signal benefic for career, malefic for health) |
| Topic verdicts | 74 (deep brief) | many already carry `[CONTRADICTORY RAW STATEMENT]` flags resolved *conservatively per-topic*, never aggregated |
| Dashas | 536k dasha rows (L1) | temporal contradiction: promise-timing vs denial-timing collision |

**factors_needed_est:** the base corpus is **~13,400 signals**; contradiction detection over it is inherently pairwise/clustering (group by domain × entity × valence, then flag opposing-valence collisions), so the composition touches **the full 13.4k set plus ~120 structural rows (yogas+doshas+domain+CDLM+topic verdicts)**. Order of magnitude: **low-thousands of factors composed, not the ~10–50 any served path returns.**

## 2. What each serving path actually returns (ceiling walls)

**`get_signals(chart_id)` — flat top-K digest wall.**
- `provenance` receipt: "300 atomic candidate signals → 67 family-collapsed rows → top_k=10 cut." So the digest reasons over **300 of 13,364 signals (2.2%)**.
- `digest.contradiction_count = "0"` — hardcoded/derived over the 300-window, presented as a whole-chart fact.
- `top_signals: []` — EMPTY. Even the top-K it promises is not delivered.
- `pagination.total = null`, `next_cursor = null` — no way to page the full set; the client cannot even self-drive a map-reduce because totals/cursors are withheld.

**`get_domain_reading(relationship)` — capped-dump wall + dishonest full-payload note.**
- `signal_id_refs_total = 7014`, returned = **200**, `signal_id_refs_capped = true`.
- `token_safety_note`: "Bounded to 3 lenses × 20 signals. Pass max_lenses=12 + max_signals_per_lens=100 for full payload."
- **RECEIPT-HONESTY DEFECT:** re-called with `max_lenses=12, max_signals_per_lens=100` — note updated to "Bounded to 12 lenses × 100 signals" (advertising a 1,200-signal payload) but **still returned exactly 200 `signal_id_refs`, still `capped=true`.** The advertised full payload (1,200) is 6× larger than what the tool delivers (200), and even 1,200 is <17% of the domain's 7,014. The escape hatch is a no-op.

**`traverse_graph(relationship="contradiction")` — no contradiction mode exists.**
- Silently ignored `relationship=contradiction`; returned `mode="convergence", top_k=10` hub nodes (all Moon/graha convergence hubs). There is **no contradiction-edge traversal in the graph**; the graph only models convergence.

**`get_cgm_subgraph(chart_id)` — returns the same orientation digest**, `contradiction_count = "0"`. The only occurrence of the token "contradiction" in the payload is that hardcoded zero.

**`synth_chart_brief_get(depth=deep)` — dissent detected only over a 5-signal "fetched insight set".**
- `topics_covered = 74`, but only **5 load_bearing_signals** and **5 top_discoveries**.
- `dissent_flags: []`, `dissent_note: "No cross-signal tension recorded in the fetched insight set for this depth/domain selection."` — dissent detection is scoped to the tiny fetched set, not the 13,364-signal corpus.
- Meanwhile `ranked_themes.weaknesses` literally contain `[CONTRADICTORY RAW STATEMENT — status resolved conservatively]` per topic — proving contradictions EXIST in the data but are resolved locally/per-topic and **never surfaced as a chart-wide synthesis**.

**`synth_tail_divergence_get`** — returns statistical *tail* signals (low-salience doshas at `salience_pctl=0`); "divergence" here = distributional tail, NOT cross-signal contradiction. Wrong axis.

**`bodha_discoveries_get`** — returns `distributional_anomaly` discoveries (σ-deviation outliers), not contradictions. Also an anomaly axis, not a tension axis.

## 3. Why this is class-8 (un-synthesizable at scale), not a query bug

- The **contradiction primitive is absent from the serving layer**: `contradiction_count` is a hardcoded 0 in every digest; no graph edge type; no `dissent` over the full set; no contradiction index/table exposed.
- Every path is a **top-K or fixed cap** (10 / 200) with **no map-reduce and no staged retrieval** that fans over signal families and reduces. `pagination.total`/`next_cursor` are null, so a caller cannot even reconstruct the corpus to synthesize client-side.
- The data *does* contain the raw material (per-topic `[CONTRADICTORY RAW STATEMENT]` flags, opposing-valence signals across 6 domains) — so this is a **composition/serving gap, not a data gap.** The system stores contradictions atomically and discards them at read time.

## 4. P-11 REQUIREMENTS SPEC — what the system would need to answer this

**Capability: chart-wide contradiction synthesis with narrative-plus-ledger.** Four staged components:

1. **A contradiction index (build-time, L2).** Precompute a `bodha_contradictions` relation: for each (domain × topic × entity) cluster, detect opposing-valence signal pairs/groups (yoga-promise vs dosha-denial, benefic-in-domain-A vs malefic-in-domain-B via CDLM, promise-timing vs denial-timing via dasha). Store `{contradiction_id, domain, poles: [signal_ids+], valence_a/b, salience_a/b, resolution_status, constituent_facts}`. This turns an O(13k²) read-time scan into a bounded stored set. The `[CONTRADICTORY RAW STATEMENT]` flags already emitted per-topic prove the detection logic exists — it must be *promoted to a first-class, chart-wide, queryable asset* instead of being resolved-and-discarded per topic.

2. **Staged retrieval (map).** A `get_contradictions(chart_id[, domain])` tool that returns the index rows with honest `pagination.total` and real cursors — so a composer can fan over all contradiction clusters, not a top-10 slice. Fix the `get_domain_reading` cap to honor `max_signals_per_lens` (currently returns 200 regardless), or expose the total + cursor so the client can map-reduce.

3. **Map-reduce over families (reduce).** A reducer that consumes the contradiction clusters + the 6 convergence-domain aggregates + the 74 topic verdicts and ranks tensions by salience-weighted severity and cross-domain reach. Output: a bounded set of ~10–30 *load-bearing contradictions* with each pole's signal_ids retained.

4. **Narrative-with-ledger composition.** A synthesis tool that renders the ranked contradictions as acharya-grade prose, each claim carrying a `DERIVATION_LEDGER` back to `chart_facts.fact_id` (B.3), with `[UNVERIFIED n_support=0]` / calibration flags preserved (STRUCTURAL-mode honesty). This is the layer that `synth_chart_brief_get` gestures at with `dissent_flags` but never fills, because its input is a 5-signal set instead of the contradiction index.

**Minimum viable fix for honesty (independent of the full capability):** stop reporting `contradiction_count: 0` as a whole-chart fact when it is computed over a 300-signal window; and make `token_safety_note` truthful (the 12×100 escape hatch must actually return >200 rows or the note must state the real 200-row ceiling).

## 5. Receipts (raw)

- `get_signals` provenance: `"300 atomic candidates → 67 family-collapsed rows → top_k=10 cut"`; `top_signals:[]`; `digest.msr_signal_count:"13364"`, `contradiction_count:"0"`; `pagination.total:null`.
- `get_domain_reading(relationship)`: `signal_id_refs_total:7014`, returned 200, `capped:true`; with `max_lenses=12,max_signals_per_lens=100` → still 200, still capped (note claimed 1,200).
- `traverse_graph(relationship=contradiction)` → `mode:convergence, top_k:10` (param ignored).
- `synth_chart_brief_get(deep)`: `topics_covered:74`, `load_bearing_signals:5`, `dissent_flags:[]`, dissent scoped to "fetched insight set"; `ranked_themes` carry `[CONTRADICTORY RAW STATEMENT — resolved conservatively]`.
- `get_cgm_subgraph` → orientation digest, `contradiction_count:"0"`.

## 6. Corroborating receipts (independent re-probe, `bodha_*` id-naming variants)

Confirms §2/§5 from the underscore-prefixed tool surface and adds two new honesty/whole-chart defects:

- `bodha_signals_get(chart_id)`: `total_matching_filters:13364`, internal `top_k:50`, `returned_count:50`, but `trim_report:[{path:"signals", original_count:50, kept_count:20, reason:"signals: trimmed to 20", recover_via:{...paginate via offset}}]` — **and top-level `truncated:false` at the same time.** The honesty flag directly contradicts the trim receipt. Re-calling with `limit:500` returned the identical 20 rows (limit param ignored; wall is fixed).
- With no `domain`, `bodha_signals_get.ranking_basis.mode:"salience_fallback"` + provenance note "composite ranking requires domain" — whole-chart queries **cannot composite-rank**, only salience-sort.
- `judgment_query(chart_id, query="whole-chart contradictions across all signals")` → hard fail `{"class":"validation","message":"either domain or bhava is required"}`. **There is no whole-chart judgment path**; the composer is forced to fragment into per-domain/per-bhava calls with no reconciler.
- `bodha_graph_traverse_get(edge_type="contradicts")` → param silently ignored, returned `mode:convergence`, 10 hub_nodes / 53 hub_edges of types `aspect`(45)+`dispositor`(8) only. No contradiction edge type exists.
- `bodha_discoveries_get`: `total:2392, returned:30`, array length **15** — silent 30→15 drop with **no trim_report** (second receipt-honesty gap).
- `bodha_chart_digest_get` aggregation receipts: "300 atomic candidate signals → 2 entity profiles" and "300 atomic candidates → 67 family-collapsed rows" = **2.2% sample** of 13,364, salience-picked; not a fold over the population.
