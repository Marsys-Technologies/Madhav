# shard-9b-ashtakavarga_pinda_bhinna

**shard_id:** 9b-ashtakavarga_pinda_bhinna
**charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## Reproducible call
Proven 9b 5-cell recipe, `fact_category='ashtakavarga_pinda_bhinna'`, both charts; plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: Abhisek=40, Abhinandan=40
- cell1: Abhisek=40, Abhinandan=25
- cell2_salience: Abhisek `major=35, supporting=5`; Abhinandan `background=1, major=19, supporting=5`
- cell3_attr: Abhisek `40/40`; Abhinandan `25/25`
- cell4_domains: both `character|career`
- cell5_type: both `composite_state` (=40 / =25)

## Five-cell verdicts
1. Consumed: YES — Abhisek 40/40 chart_facts pass through as signals (100% indiscriminate ingestion).
2. Salience: `major` dominates (35/40 Abhisek; 19/25 Abhinandan). Bhinna pinda (per-graha totals) are summary-ish so SOME major is defensible, but 35/40 at major is high; and note the cross-chart swing (major share 88% vs 76%). Marginal FAIL.
3. Attribution: full. PASS.
4. Domain: `character|career` — drops `wealth` (relevant for pinda strength). KP-4-analog note.
5. Emergence: 40 facts → 40 (Abhisek, 100%) / 25 signals — near-total pass-through = indiscriminate ingestion signature.

## design_correctness_verdict: WEAK
Fully attributed, but two consumer-facing concerns: (a) 100% pass-through of chart_facts into signals with the majority at `major` tier is indiscriminate ingestion + salience inflation; (b) cross-chart inconsistency — Abhisek 40/40 all ingested vs Abhinandan 25/40, and major-share 88% vs 76% — the salience/ingestion decision is not chart-stable.

## Findings
- summary: bhinna-pinda signals dominated by `major` tier (35/40 Abhisek) with 100% chart_facts→signal pass-through — indiscriminate ingestion + salience inflation; failure_class 7 (DROWNED); severity MED; evidence: cell1 `40` = denominator `40`; cell2 `major=35, supporting=5`. Rationale: promoting nearly all bhinna-pinda rows to major crowds top-K. Suspected layer: ranking + ingestion-design.
- summary: cross-chart instability — Abhisek ingests 40/40 (major=35) vs Abhinandan 25/40 (major=19); same category, divergent ingestion+salience; failure_class 3 (INCONSISTENT); severity LOW; evidence: cell1 `40` vs `25`, cell2 major share 88% vs 76%. Suspected layer: L-writer.
