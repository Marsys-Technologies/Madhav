# shard-9b-aspect_parashari_per_varga

**Shard id:** aspect_parashari_per_varga (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `aspect_parashari_per_varga`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 2755 / 2755
- cell1 (signals): 2118 (Abhisek `482012f1`) / 2025 (Abhinandan `1c826d5a`)
- cell2_salience:
  - Abhisek `482012f1`: `background=5, chart_defining=229, major=1317, supporting=567`
  - Abhinandan `1c826d5a`: `background=645, chart_defining=49, major=1048, supporting=283`
- cell5_type: `composite_state=2118` / `composite_state=2025`
- cell3_attr: 2118/2118 / 2025/2025
- cell4_domains: `career|relationship|wealth` (both)

## 5-cell verdicts
1. Consumed? YES — near-1:1 (2755 facts → ~2000 signals/chart).
2. Salience: INFLATED — 1317 `major` + 229 `chart_defining` (Abhisek) from ONE fact_category of per-VARGA (divisional-chart) aspects. A D-varga graha aspect being "chart_defining" 229 times is disproportionate to its decision weight.
3. Attribution: full (2118/2118, 2025/2025) — SOUND on this axis.
4. Domain: fixed `career|relationship|wealth`.
5. Emergence: ~2000 signals/chart — a second flood-tier fact_category (after aspect_jaimini_per_varga).

## design_correctness_verdict: BROKEN
Per-varga Parashari aspects emit ~2,000 signals/chart with 1,317 at `major` and 229 at `chart_defining` (Abhisek). Promoting divisional-chart aspect granularity to major/chart_defining in the thousands buries genuine chart-defining findings — a DROWNED surface plus salience inflation. The per-chart salience distributions also diverge wildly (Abhisek chart_defining=229 vs Abhinandan chart_defining=49; Abhisek background=5 vs Abhinandan background=645), suggesting the tier assignment is unstable/uncalibrated rather than a principled read.

## Findings
- **F1 (class 7 DROWNED, HIGH):** 1317 `major` + 229 `chart_defining` signals (Abhisek) from a single per-varga aspect category swamp the top salience tiers. Rationale for exceeding acharya tolerance (CHARTER §7.4): an acharya would treat at most a handful of divisional aspects as chart-defining; 229 chart_defining + 1317 major renders the top tiers non-discriminating. Evidence: cell2 Abhisek `chart_defining=229, major=1317`.
- **F2 (class 3 INCONSISTENT, MED):** salience distribution is wildly chart-divergent (Abhisek chart_defining=229/background=5 vs Abhinandan chart_defining=49/background=645) for the same fact_category and rule set — indicates uncalibrated tier assignment. Evidence: cell2 both charts quoted above.
