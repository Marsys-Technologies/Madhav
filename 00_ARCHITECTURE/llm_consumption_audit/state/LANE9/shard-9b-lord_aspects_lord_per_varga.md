# Shard 9b-lord_aspects_lord_per_varga

shard_id: 9b-lord_aspects_lord_per_varga
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='lord_aspects_lord_per_varga'. chart_facts census: 1788 rows combined.

## Verbatim results
- cell1: 482=889, 1c8=899 → CONSUMED (high volume)
- cell2_salience: 482=chart_defining=114, major=730, supporting=45 ; 1c8=background=224, chart_defining=42, major=611, supporting=22
- cell3_attr: 482=889/889 ; 1c8=899/899 (100%)
- cell4_domains: 482=character|career ; 1c8=character|career
- cell5_type: 482=composite_state=889 ; 1c8=composite_state=899

## 5-cell verdicts
1. Consumed? YES — ~890-900 signals from one fact_category.
2. Salience: 482 has 114 chart_defining + 730 major = 844 signals at major-or-above; 1c8 has 653 at major-or-above. SALIENCE INFLATION / DROWNING — per-varga lord-aspects-lord is fine-grained relational grid data, not chart-defining. Note cross-chart inconsistency: 482 pushes far more to chart_defining (114) than 1c8 (42) and 1c8 alone uses 'background' (224) while 482 uses none — salience assignment is unstable across charts for the same category.
3. Attribution: 100%. PASS.
4. Domain: uniform character|career. Domain narrowing.
5. Emergence: ~890-900 signals, single type class.

## design_correctness_verdict: WEAK

## Findings
- summary: lord_aspects_lord_per_varga emits ~890-900 signals from one fact_category with 844 (chart 482) at major-or-chart_defining tier — per-varga aspect-grid trivia promoted to top tiers, drowning findable signal.
  failure_class: 7 (DROWNED)
  severity: HIGH
  suspected_layer: ranking (signature_tier)
  evidence: cell2_salience 482 = "chart_defining=114, major=730"; 1c8 = "chart_defining=42, major=611, background=224".
  reproducible_call: SQL recipe, cell2_salience row.
- summary: lord_aspects_lord_per_varga salience tiering is inconsistent across charts (482: 114 chart_defining / no background; 1c8: 42 chart_defining / 224 background) for the same descriptive category.
  failure_class: 3 (INCONSISTENT)
  severity: MED
  suspected_layer: ranking
  evidence: cell2_salience differs structurally between the two charts (see above).
  reproducible_call: SQL recipe, cell2_salience row both charts.
- summary: lord_aspects_lord_per_varga uniformly domain-mapped to character|career across all ~890-900 signals.
  failure_class: 2 (WRONG — domain mis-mapping)
  severity: MED
  suspected_layer: L-writer
  evidence: cell4 single distinct value "character|career" both charts.
  reproducible_call: SQL recipe, cell4_domains row.
