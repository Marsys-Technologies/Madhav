# Shard 9b — graha_avastha_baladi

**Shard id:** `9b-graha_avastha_baladi`
**Charts:** Abhisek `482012f1-710e-4a25-994a-93821f5871aa`, Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`

## Exact SQL run
9b 5-cell recipe (WITH sig … UNION ALL cell1..cell4) with `f.fact_category = 'graha_avastha_baladi'`; plus `SELECT COUNT(*) FROM chart_facts WHERE fact_category='graha_avastha_baladi'`.

## Verbatim results
- chart_facts rows: Abhisek 45, Abhinandan 45.
- cell1 (consumed): Abhisek 17, Abhinandan 20 → CONSUMED both charts.
- cell2 salience: Abhisek `chart_defining=1, major=13, supporting=3`; Abhinandan `background=4, chart_defining=1, major=14, supporting=1`.
- cell3 attribution: Abhisek 17/17, Abhinandan 20/20 → 100% attributed.
- cell4 domains: both `character|career`.
- cell5 type: both `composite_state` only.

## Five-cell verdicts
1. Consumed? YES both charts.
2. Salience: skewed to `major` (13/17 Abhisek, 14/20 Abhinandan) + 1 chart_defining each — HIGH for a descriptive baladi (infant/youth/adult/old/dead) strength-state.
3. Attribution: full (100%). PASS.
4. Domain: mono-mapped `character|career` — default; no domain differentiation.
5. Emergence: 17–20 signals, all `composite_state`.

## design_correctness_verdict: WEAK
Salience inflation (defect b): a per-graha degree-based avastha state sits predominantly at `major` with a chart_defining instance. Baladi does modulate delivered strength, so `major` is partly defensible, but 13–14 signals at major over-weights descriptive state facts. Attribution is exemplary.

## Findings
- **F1 (class 7 DROWNED / salience inflation) — MED.** graha_avastha_baladi: 13/17 (Abhisek) and 14/20 (Abhinandan) signals at `major` tier plus a `chart_defining` instance, for a descriptive per-graha avastha. Evidence: cell2 Abhisek `chart_defining=1, major=13, supporting=3`. Repro: 5-cell recipe with fact_category='graha_avastha_baladi'. Suspected layer: ranking (bo_laksana signature_tier assignment).
- **F2 (class 2 WRONG / domain mis-mapping) — MED (shared).** Mono-domain `character|career` regardless of relevance. Evidence: cell4 `character|career` both charts.
