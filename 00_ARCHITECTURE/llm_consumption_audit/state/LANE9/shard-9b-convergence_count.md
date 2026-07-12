# shard-9b-convergence_count

**Shard id:** 9b-convergence_count
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='convergence_count' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 3045 (Abhisek) / 3045 (Abhinandan)
- cell1 signals: Abhisek=2359, Abhinandan=2309
- cell2 salience: Abhisek `background=2, chart_defining=48, major=449, supporting=1860`; Abhinandan `background=144, chart_defining=42, major=320, supporting=1803`
- cell3 attribution: 2359/2359, 2309/2309
- cell4 domains: both `career|character`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — very large volume (2300+)
2. Salience: HAS tier discrimination (chart_defining/major/supporting/background) — a positive
3. Attribution: 100%
4. Domains: rigid `career|character`
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Best-in-shard salience behaviour (genuine 4-tier discrimination, ~48 elevated to chart_defining out of 2359), fully attributed. But sheer volume (2359 signals from one fact_category) plus a rigid two-domain `career|character` mapping keep it DROWNED-adjacent and domain-starve non-career/character convergence queries.

## Findings
- summary: convergence_count emits 2300+ signals uniformly domain-mapped to career|character; volume + fixed domain suppresses convergence findings relevant to other life domains. failure_class 7 (DROWNED). severity MED. evidence: cell1=2359/2309, cell4=`career|character` uniform; mitigated by cell2 real tiering.
