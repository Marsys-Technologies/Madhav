# Shard 9b — karaka_bhava_concordance

shard_id: 9b-karaka_bhava_concordance
charts: 482012f1 (Abhisek), 1c826d5a (Abhinandan)

## Exact SQL run
5-cell recipe with `<CAT>=karaka_bhava_concordance`, plus chart_facts existence count.

## Verbatim results
chart_facts rows: Abhinandan=4350, Abhisek=4350 (both >0).
- cell1 (signals): Abhinandan=4350, Abhisek=4350
- cell2_salience: supporting=4350 / supporting=4350
- cell5_type: karaka_alignment=4350 / karaka_alignment=4350
- cell3_attr: 4350/4350, 4350/4350 (100% attributed)
- cell4_domains: character|career (both charts, ONLY distinct value)

## Five-cell verdicts
1. Consumed? YES — but 1:1 at 4350 signals PER CHART: this single fact_category alone floods the MSR funnel.
2. Salience: uniformly `supporting` — a 4350-row identical-score wall (charter §7.4 metric 2), the single largest flat-tier block seen in this shard.
3. Attribution: 100% resolving (technically attributed) — but attribution is meaningless when 4350 rows are indistinguishable.
4. Domain: uniform {character, career} default collapse across all 4350 rows.
5. Emergence: 4350 signals from ONE category — pure indiscriminate 1:1 ingestion.

## design_correctness_verdict: WEAK

## Findings
- summary: karaka_bhava_concordance is ingested 1:1 as 4350 flat `supporting` signals per chart — the largest single-category flood in the shard — creating a 4350-row identical-score/duplication wall that drowns the funnel; compounded by uniform {character,career} default domain-mapping.
  failure_class: 7 (DROWNED — indiscriminate mass ingestion / identical-score wall)
  severity: HIGH
  suspected_layer: L-writer (bo_laksana ingestion policy) / ranking
  evidence: cell1=4350/4350 = chart_facts 4350/4350 (pure 1:1); cell2="supporting=4350" (one flat tier); cell4="character|career" ONLY distinct value.
  dedupe: R-44a/b indiscriminate-ingestion anchor family; karaka_bhava_concordance is a fresh, extreme specimen (4350 rows/chart).
- summary (secondary): same signals also uniformly domain-mapped to default {character, career} despite karaka×bhava concordance spanning all life domains (DK→relationship, PiK/PK→children, AmK→career, etc.).
  failure_class: 2 (WRONG; class-1 consequence for domain-filtered queries)
  severity: MED
  suspected_layer: L-writer (domain-mapping)
  evidence: cell4_domains = "character|career" only, across 4350 signals both charts.
  dedupe: KP-4-family default-domain-mapping.
