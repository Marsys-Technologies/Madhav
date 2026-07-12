# shard-9b-ashtakavarga_pinda_sarva_per_varga

**shard_id:** 9b-ashtakavarga_pinda_sarva_per_varga
**charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## Reproducible call
Proven 9b 5-cell recipe, `fact_category='ashtakavarga_pinda_sarva_per_varga'`, both charts; plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: Abhisek=560, Abhinandan=560
- cell1: Abhisek=490, Abhinandan=490
- cell2_salience: Abhisek `major=219, supporting=271`; Abhinandan `background=84, major=165, supporting=241`
- cell3_attr: Abhisek `490/490`; Abhinandan `490/490`
- cell4_domains: both `character|career`
- cell5_type: both `composite_state` (=490)

## Five-cell verdicts
1. Consumed: YES — 560 facts → 490 signals (~88% pass-through = near-indiscriminate ingestion).
2. Salience: **219 (Abhisek) / 165 (Abhinandan) at `major`** for per-varga SAV totals — salience inflation. Per-varga SAV is not a primary weighting instrument (unlike D1 SAV); 165-219 major-tier rows will crowd top-K. FAIL.
3. Attribution: full (490/490 both). PASS.
4. Domain: `character|career` — drops `wealth` that the D1 sarva category carries; per-varga SAV unreachable in wealth queries. KP-4-analog gap.
5. Emergence: ~88% pass-through, single `composite_state` type.

## design_correctness_verdict: WEAK
Perfect attribution, but the per-varga SAV surface repeats the per-varga bindu defect pattern: (a) ~165-219 signals promoted to `major` despite low decision-weight (class 7 DROWNED / salience inflation); (b) `wealth` domain dropped relative to the parent `ashtakavarga_pinda_sarva` (`career|wealth`), producing a wealth-query reachability gap.

## Findings
- summary: ~165-219 per-varga sarva-pinda signals at `major` tier despite niche decision-weight — salience inflation / DROWNED; failure_class 7; severity HIGH; evidence: cell2 `major=219` (Abhisek), `major=165` (Abhinandan) of 490. Rationale (§7.4 amendment): per-varga SAV is not a primary acharya weighting surface; 165+ major rows exceed tolerance. Suspected layer: ranking.
- summary: per-varga sarva-pinda domain-mapped `character|career`, dropping `wealth` present on parent `ashtakavarga_pinda_sarva` — wealth-query reachability gap; failure_class 2 (WRONG domain, class-1 consequence); severity MED; evidence: cell4 `character|career` vs parent `career|wealth`. Suspected layer: L-writer.
