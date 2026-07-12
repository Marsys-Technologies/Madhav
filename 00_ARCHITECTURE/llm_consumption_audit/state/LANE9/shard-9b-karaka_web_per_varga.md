# Shard 9b-karaka_web_per_varga

shard_id: 9b-karaka_web_per_varga
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: proven 9b 5-cell recipe with f.fact_category='karaka_web_per_varga'. chart_facts census: 2156 rows combined.

## Verbatim results
- cell1: 482=1049, 1c8=1107 → CONSUMED (very high volume)
- cell2_salience: 482=background=8, chart_defining=192, major=662, supporting=187 ; 1c8=background=121, chart_defining=89, major=806, supporting=91
- cell3_attr: 482=1049/1049 ; 1c8=1107/1107 (100% attributed)
- cell4_domains: 482=character|career ; 1c8=character|career
- cell5_type: 482=karaka_alignment=1049 ; 1c8=karaka_alignment=1107

## 5-cell verdicts
1. Consumed? YES — extreme volume (~1050-1100 signals from ONE fact_category).
2. Salience: on 482, 192 chart_defining + 662 major = 854 signals at major-or-above from a single per-varga descriptive relational category; on 1c8, 895 at major-or-above. SALIENCE INFLATION / DROWNING. Per-varga karaka-web relations are fine-grained descriptive data; promoting hundreds to chart_defining/major buries genuinely chart-defining signals under a duplication wall (R-44b / R-37 pattern).
3. Attribution: 100%. PASS.
4. Domain: uniform character|career. Domain narrowing (karaka web spans multiple life domains).
5. Emergence: ~1050-1100 signals, single type class.

## design_correctness_verdict: WEAK

## Findings
- summary: karaka_web_per_varga emits ~1050-1100 signals from one fact_category with 854+ (chart 482) / 895 (chart 1c8) at major-or-chart_defining tier — a per-varga descriptive relational category promoted to top salience tiers at scale, drowning findable signal.
  failure_class: 7 (DROWNED)
  severity: HIGH
  suspected_layer: ranking (signature_tier assignment in bo_laksana)
  evidence: cell2_salience 482 = "chart_defining=192, major=662"; 1c8 = "chart_defining=89, major=806". No reasonable acharya read treats ~850 per-varga karaka-web relations as chart-defining/major-weight.
  reproducible_call: SQL recipe, cell2_salience row.
- summary: karaka_web_per_varga uniformly domain-mapped to character|career across all ~1050-1100 signals, blocking domain-filtered retrieval.
  failure_class: 2 (WRONG — domain mis-mapping)
  severity: MED
  suspected_layer: L-writer
  evidence: cell4 = single distinct value "character|career" for all signals both charts.
  reproducible_call: SQL recipe, cell4_domains row.
