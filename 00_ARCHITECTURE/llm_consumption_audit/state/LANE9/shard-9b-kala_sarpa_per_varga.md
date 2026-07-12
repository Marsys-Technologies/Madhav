# Shard 9b — kala_sarpa_per_varga

shard_id: 9b-kala_sarpa_per_varga
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=kala_sarpa_per_varga`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=145, Abhisek=145 (both >0).
- cell1 (signals): Abhinandan=145, Abhisek=145
- cell2_salience: supporting=145 / supporting=145
- cell5_type: configuration=145 / configuration=145
- cell3_attr: 145/145, 145/145 (100% attributed)
- cell4_domains: character|career|wealth (both charts)

## Five-cell verdicts
1. Consumed? YES — 1:1 (145 facts → 145 signals) on both charts.
2. Salience: uniformly `supporting` (145 identical-tier rows) — an identical-score wall (charter §7.4 metric 2).
3. Attribution: 100%, resolving. OK on attribution.
4. Domain: {character, career, wealth} — broader than the character|career default, acceptable.
5. Emergence: 145 per-varga signals for what is fundamentally ONE whole-chart nodal-axis dosha, restated once per varga at a flat tier — a duplication wall.

## design_correctness_verdict: WEAK

## Findings
- summary: kala_sarpa (a single whole-chart Rahu–Ketu-axis dosha) is emitted as 145 flat `supporting` per-varga signals per chart, a duplication/identical-score wall that dilutes the funnel and buries the one decision-relevant fact (is Kala Sarpa present, and unbroken?) under 145 near-identical rows.
  failure_class: 7 (DROWNED — duplication wall / identical-score wall)
  severity: MED
  suspected_layer: ranking / L-writer (indiscriminate per-varga 1:1 emission)
  evidence: cell1=145/145 both charts equals chart_facts=145/145 (pure 1:1); cell2 = "supporting=145" (single flat tier, no discrimination); cell5="configuration=145".
  dedupe: R-44a/b-family indiscriminate-ingestion pattern; per-varga dosha-replication specimen.
