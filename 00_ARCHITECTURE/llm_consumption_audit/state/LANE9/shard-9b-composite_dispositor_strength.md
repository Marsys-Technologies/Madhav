# shard-9b-composite_dispositor_strength

**Shard id:** 9b-composite_dispositor_strength
**Charts:** Abhisek 482012f1-710e-4a25-994a-93821f5871aa · Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a

## SQL run
Standard 5-cell recipe (CHARTER 9b, `bodha_msr_signals` ⋈ unnest(constituent_facts_array) ⋈ chart_facts on fact_category='composite_dispositor_strength'), plus chart_facts baseline count.

## Verbatim results
- chart_facts baseline: 45 (Abhisek) / 45 (Abhinandan)
- cell1 (signals): Abhisek=5, Abhinandan=10
- cell2 salience: Abhisek `chart_defining=1, major=4`; Abhinandan `background=2, chart_defining=1, major=6, supporting=1`
- cell3 attribution: Abhisek 5/5, Abhinandan 10/10
- cell4 domains: both `character|career`
- cell5 type: both `composite_state=5 / =10`

## Cell verdicts
1. Consumed: YES (5 / 10 signals)
2. Salience: concentrated at major/chart_defining
3. Attribution: 100% resolvable
4. Domains: rigid `character|career` on every signal regardless of which dispositor
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Consumed and fully attributed, but (a) only ~5–10 signals emerge from 45 facts (funnel narrowing) and (b) a dispositor-**strength** metric is mapped uniformly to `character|career`, starving domain-filtered queries (finance/health) that dispositor strength materially informs.

## Findings
- summary: Dispositor-strength signals uniformly domain-mapped to character|career regardless of the dispositor's house/karaka relevance. failure_class 2 (WRONG-mapping). severity MED. evidence: cell4 `character|career` for all 5/10 signals on both charts.
