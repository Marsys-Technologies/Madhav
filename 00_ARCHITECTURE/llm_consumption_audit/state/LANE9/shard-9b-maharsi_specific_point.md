# Shard 9b-maharsi_specific_point

shard_id: 9b-maharsi_specific_point
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='maharsi_specific_point'. chart_facts census: 140 rows combined.

## Verbatim results
- cell1: 482=10, 1c8=10 → CONSUMED (thin)
- cell2_salience: 482=supporting=10 ; 1c8=supporting=10
- cell3_attr: 482=10/10 ; 1c8=10/10 (100%)
- cell4_domains: 482=character|relationship ; 1c8=character|relationship
- cell5_type: 482=composite_state=10 ; 1c8=composite_state=10

## 5-cell verdicts
1. Consumed? YES but thin — 10 signals vs ~70 chart_facts rows/chart (~7:1 narrowing).
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: uniform character|relationship. Maharshi special points (special lagnas/upagrahas per various rishis) carry longevity/career/spiritual significations; character|relationship-only drops those.
5. Emergence: 10 signals, single type class.

## design_correctness_verdict: WEAK

## Findings
- summary: maharsi_specific_point narrows ~7:1 from chart_facts (140 combined) to 10 MSR signals/chart and maps uniformly to character|relationship, omitting longevity/career/spiritual domains these points serve.
  failure_class: 1 (UNREACHABLE — funnel-narrowing + domain omission)
  severity: LOW
  suspected_layer: L-writer
  evidence: chart_facts=140 combined vs cell1=10/10; cell4="character|relationship" only.
  reproducible_call: SQL recipe cell1/cell4 + census COUNT.
