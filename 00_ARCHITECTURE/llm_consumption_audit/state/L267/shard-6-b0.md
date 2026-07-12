# Lane 6 — RANKED-SURFACE-QUALITY — shard-6-b0

Charter §7.4 (RATIFIED, raw-metrics-always amendment). Read-only DEPLOYED MCP connector.
Requested chart (all 4 surfaces): `482012f1-710e-4a25-994a-93821f5871aa` (native Abhisek Mohanty).

## CROSS-CUTTING RECEIPT-HONESTY FINDINGS (apply to all 4 surfaces)

- **WRONG CHART SILENTLY SUBSTITUTED.** Every surface was called with `chart_id=482012f1-…` but every returned envelope carries `content.chart_id = 1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan Mohanty, the L1-operator demo chart). No error, no warning — the connector answered a *different* chart than requested on all 4 calls. Digest identical across calls: `msr_signal_count=13369, yoga_count=13, dosha_count=22, avg_salience=0.5971, max_salience=2.99, weakest_graha=Saturn, contradiction_count=0`.
- **ENVELOPE GROUNDING EMPTY (R-44a confirmed live).** `get_chart_orientation` returns `grounding = {fact_ids: [], citations: [], grounding_score: null}`. The consumer-facing grounding block is 100% empty even though every underlying signal row carries a `constituent_facts_array`.
- **PAGINATION NULLED.** Orientation `pagination = {offset:0, limit:0, total:null, next_cursor:null}` — `total` is null, so a consumer cannot know how many signals were suppressed. `trim_report: null` despite only 10 of 13,369 signals surfaced.
- **DOMAIN TRIM/CAP.** `get_domain_reading` `signal_id_refs_total=12378`, `signal_id_refs_capped=true`, only 200 returned; `token_safety_note: "Bounded to 3 lenses × 20 signals."` Ranked rows capped at 20 of `total_count≈12398`. `provenance.defect_001`: "845/67508 references orphaned (1.3%)".

---

## SURFACE 1 — get_chart_orientation  (top_signals, K=10)

Verbatim top-10 (rank shown is `top_k_salience_rank`; note it is NON-monotonic — 188, 547, 525, 524, 532, 533, 519, 523, 535, 557 — the "top" list is not even sorted by the stored rank):

| idx | computed_salience | final_rank | signal_type_id | headline |
|---|---|---|---|---|
| 0 | 2.00 | 1.04567 | navamsha_d9_cross_check:venus | D9 cross-check: Venus D1=exalted × D9=Friend → concordant_strong (tier=chart_defining) |
| 1 | 1.38 | 0.78796 | graha_tara_bala:tara_count | graha tara bala: tara count = 22 |
| 2 | 1.38 | 0.78796 | graha_nakshatra_join:presiding_deity | presiding deity = Pushan |
| 3 | 1.38 | 0.78796 | graha_nakshatra_join:pakshi | pakshi = Elephant |
| 4 | 1.38 | 0.78796 | graha_pada_join:akshara | akshara = Cha |
| 5 | 1.38 | 0.78796 | graha_pada_join:navamsa_sign | navamsa sign = Aquarius |
| 6 | 1.38 | 0.78796 | graha_nakshatra_join:guna | guna = Sattva |
| 7 | 1.38 | 0.78796 | graha_nakshatra_join:nakshatra_lord | nakshatra lord = mercury |
| 8 | 1.38 | 0.78796 | graha_pada_join:pada_number_ref | pada number ref = 3 |
| 9 | 1.38 | 0.78796 | nakshatra_cross_ayanamsha:stable_nakshatra_id | stable nakshatra id = 27 |

RAW METRICS:
- **duplication_rate = 0.50** (exact signal_id dup = 0; family-category collapse: `graha_nakshatra_join` ×4 + `graha_pada_join` ×3 → 5 redundant rows / 10).
- **identical_score_walls = 1 wall of 9** rows co-tied (idx1–9) at `computed_salience=1.38 / composite=0.7875`. 9/10 rows in a single tie-wall. final_rank differs only in the ~10th decimal (jitter, not signal).
- **descriptive_trivia_share = 0.90** (9/10). idx1–9 are almanac lookups (tara-count, presiding-deity, pakshi/bird, akshara/syllable, guna, pada number, stable-nakshatra-id) — pure descriptive placement, NOT chart-defining under classical canon. Only idx0 (Venus D1-exalted × D9 concordance) is genuinely chart-shaping.
- **family_collapse_coverage = 1/9 grahas, 0/13 yogas, 0/22 doshas.** Top-K touches only Venus as a real graha entity; 0 yogas and 0 doshas surface. The single highest-scoring *entity* in the chart is literally `UNATTRIBUTED` (aggregate_score 84.80, 298 signals) vs Venus 1.05, Jupiter 0.64.
- **UNATTRIBUTED_share (re-derived blind) = envelope 100% (0 fact_ids in grounding block); row-attribution 9/10 = 0.90** (idx1–9 all belong to the `UNATTRIBUTED` entity bucket; its `top_signal_ids` = [0149a427(tara), 998cdfbb(presiding_deity), 79b44c1b(pakshi)] = exactly idx1–3).
- **drowned_verdict = DROWNED (class 7).** The one chart-defining interpretive signal (Venus D9) is immediately buried under a 9-row wall of identical-scored almanac trivia; plus wrong-chart substitution.

## SURFACE 2 — get_domain_reading:career  (lens qtype=career, K=20)

salience = [2.99, 2.76, 2.76, 2.76, 2.76, 2.645, 2.645, 2.415, 2.415, 2.346, 2.3×10]
Top row: `a7b7703a-…` salience 2.99, ga_structural, composite_state, in_template=true.

RAW METRICS:
- **duplication_rate: within-lens = 0; CROSS-DOMAIN = 0.50** (career∩wealth top-20 = 10/20 identical signal_ids). Ranking is domain-invariant at the top.
- **identical_score_walls = 2 walls (4 + 10)**: `2.76`×4 and `2.3`×10. 14/20 rows in 3+ tie-walls.
- **descriptive_trivia_share = NOT DIRECTLY ASSESSABLE** — domain payload omits `signal_summary_text`/headline for ranked rows (only salience + id + class). Receipt-honesty gap. Classes: composite_state 17, varga_pattern 2, karaka_alignment 1.
- **family_collapse_coverage:** 20/20 rows `source_l1_asset = ga_structural` — a single L1 asset supplies the entire domain top-K.
- **UNATTRIBUTED_share = 20/20 = 1.00 at row level** (ranked rows carry no inline fact_ids; no envelope grounding block on domain payload; provenance flags 1.3% orphaned).
- **drowned_verdict = DROWNED (class 7).** Domain-invariant salience distribution + 10-row wall means the "career reading" does not surface career-*specific* chart-defining structure.

## SURFACE 3 — get_domain_reading:wealth  (lens qtype=wealth, K=20)

salience = [2.99, 2.76, 2.76, 2.76, 2.76, 2.645, 2.645, 2.415, 2.415, 2.346, 2.3×10] — **byte-identical distribution to career and relationship.**
Top row: same `a7b7703a-…` @ 2.99 (here `in_template=false, non_template_significant=true`).

RAW METRICS:
- **duplication_rate (cross-domain) = 0.50 vs career; 0.95 vs relationship** (wealth∩relationship = 19/20 identical ids).
- **identical_score_walls = 2 walls (4 + 10)**: 2.76×4, 2.3×10. 14/20 in walls.
- **descriptive_trivia_share = NOT ASSESSABLE** (text omitted). classes: composite_state 20/20.
- **family_collapse_coverage:** 20/20 `ga_structural`; in_template True/False = 10/10.
- **UNATTRIBUTED_share = 20/20 = 1.00** (row level).
- **drowned_verdict = DROWNED (class 7).** wealth top-K is 95% identical to relationship top-K — the surface is not discriminating between two orthogonal life domains.

## SURFACE 4 — get_domain_reading:relationship  (lens qtype=marriage, K=20)

salience = [2.99, 2.76, 2.76, 2.76, 2.76, 2.645, 2.645, 2.415, 2.415, 2.346, 2.3×10] — identical distribution again.

RAW METRICS:
- **duplication_rate (cross-domain) = 0.95 vs wealth; 0.50 vs career.**
- **identical_score_walls = 2 walls (4 + 10)**: 2.76×4, 2.3×10. 14/20 in walls.
- **descriptive_trivia_share = NOT ASSESSABLE** (text omitted). classes: composite_state 20/20.
- **family_collapse_coverage:** 20/20 `ga_structural`.
- **UNATTRIBUTED_share = 20/20 = 1.00** (row level).
- **drowned_verdict = DROWNED (class 7).**

---
## Tolerance rationale (inline, no silent thresholds)
- Score-wall flagged at 3+ co-tied (charter §7.4 definition). A wall of 9–10 with only ~10th-decimal jitter is a genuine ranking collapse, not a display rounding artifact — the underlying `computed_salience` values are exactly equal (1.38, 2.3), so consumers get no ordering signal within the wall.
- descriptive_trivia weighted by classical canon: nakshatra-almanac attributes (pakshi/bird, syllable, presiding deity, guna, pada number, tara-count) are lookup facts, not chart-defining yogas/dignities — hence counted as trivia despite carrying a resolvable fact_id.
- "NOT ASSESSABLE" for domain trivia is itself reported as a receipt-honesty defect, not silently skipped.
