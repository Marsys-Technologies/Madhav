# Shard 9b — graha_centrality

**Shard id:** `9b-graha_centrality`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_centrality'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 1305.
- cell1: Abhisek 1284, Abhinandan 1271 → CONSUMED (largest consumer in shard).
- cell2 salience: Abhisek `background=5, chart_defining=83, major=893, supporting=303`; Abhinandan `background=318, chart_defining=83, major=718, supporting=152`.
- cell3 attribution: Abhisek 1284/1284, Abhinandan 1271/1271 → 100%.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES — heavily (1271–1284 signals from ONE fact_category).
2. Salience: SEVERELY inflated — Abhisek 976/1284 signals (83 chart_defining + 893 major) at major-or-above; 83 chart_defining alone from a single computed centrality metric floods the top tier.
3. Attribution: 100%. PASS (attribution is not the failure here).
4. Domain: mono `character|career` — a structural/graph-centrality metric that is inherently domain-agnostic is confined to one domain pair, under-serving wealth/health/relationship queries.
5. Emergence: 1271–1284 signals, all composite_state — dominates aggregate MSR volume.

## design_correctness_verdict: BROKEN
Extreme salience inflation + drowning (defect b + class 7). A single graph-derived centrality metric emits ~1280 signals per chart, of which ~976 (Abhisek) sit at major-or-above and 83 at `chart_defining`. This alone can saturate the `chart_defining`/`major` tiers, making those tiers un-trustworthy as a findability signal for a consuming LLM — genuine chart-defining findings (yogas, doshas) are diluted by centrality restatements. Fully attributed but un-findable-by-tier and mono-domain-confined.

## Findings
- **F1 (class 7 DROWNED / salience inflation) — HIGH.** graha_centrality emits 1284 signals (Abhisek) / 1271 (Abhinandan); 83 chart_defining + 893 major (Abhisek) at major-or-above from one computed metric. This saturates the top salience tiers and drowns genuinely chart-defining findings. Evidence: cell1 1284 + cell2 Abhisek `background=5, chart_defining=83, major=893, supporting=303`. Repro: 5-cell recipe, fact_category='graha_centrality'. Suspected layer: ranking (bo_laksana signature_tier) + ingestion-design (one signal per centrality fact row).
- **F2 (class 3 INCONSISTENT — cross-chart tier divergence) — MED.** Tiering diverges sharply between charts: Abhisek `background=5, major=893` vs Abhinandan `background=318, major=718`. Same category, ~180-signal swing between major and background across charts suggests unstable/threshold-sensitive tier assignment. Evidence: cell2 both charts.
- **F3 (class 2 domain mis-mapping) — MED.** A domain-agnostic structural centrality metric mono-mapped to `character|career`; cannot surface under wealth/health/relationship domain filters despite structural relevance to all. Evidence: cell4 `character|career`. Suspected layer: L-writer domain mapping.
