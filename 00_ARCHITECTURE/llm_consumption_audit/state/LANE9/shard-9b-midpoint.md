# Shard 9b-midpoint

shard_id: 9b-midpoint
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='midpoint'. chart_facts census: 2160 rows combined.

## Verbatim results
- cell1: 482=385, 1c8=388 → CONSUMED
- cell2_salience: 482=supporting=385 ; 1c8=supporting=388
- cell3_attr: 482=385/385 ; 1c8=388/388 (100%)
- cell4_domains: 482=character|relationship ; 1c8=character|relationship
- cell5_type: 482=composite_state=385 ; 1c8=composite_state=388

## 5-cell verdicts
1. Consumed? YES (~385-388 signals) — ~5.6:1 narrowing from 2160 chart_facts.
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: uniform character|relationship. Planetary midpoints (a sensitive-point technique) can implicate career/wealth/health depending on the pair; blanket character|relationship narrows retrieval.
5. Emergence: ~385-388 signals, single type class.

## design_correctness_verdict: WEAK

## Findings
- summary: midpoint signals uniformly domain-mapped to character|relationship regardless of the planetary pair, blocking career/wealth/health domain retrieval of midpoint evidence.
  failure_class: 2 (WRONG — domain mis-mapping)
  severity: LOW
  suspected_layer: L-writer
  evidence: cell4 single distinct value "character|relationship" across all ~385-388 signals both charts.
  reproducible_call: SQL recipe, cell4_domains row.
