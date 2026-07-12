# Shard 9b-lord_in_house_per_varga

shard_id: 9b-lord_in_house_per_varga
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='lord_in_house_per_varga'. chart_facts census: 3480 rows combined.

## Verbatim results
- cell1: 482=1740, 1c8=1740 → CONSUMED (highest volume in shard)
- cell2_salience: 482=supporting=1740 ; 1c8=supporting=1740
- cell3_attr: 482=1740/1740 ; 1c8=1740/1740 (100%)
- cell4_domains: 482=career|wealth|relationship ; 1c8=career|wealth|relationship
- cell5_type: 482=composite_state=1740 ; 1c8=composite_state=1740

## 5-cell verdicts
1. Consumed? YES — 1740 signals/chart from one fact_category.
2. Salience: 100% supporting — DISCIPLINED (correctly NOT inflated despite volume). PASS on inflation.
3. Attribution: 100%. PASS.
4. Domain: career|wealth|relationship — 3 domains INCLUDING wealth (better than most in this shard); still uniform per signal and omits health/character.
5. Emergence: 1740 signals — sheer volume from a single fact_category is a drowning-by-count risk even at supporting tier: any consumer pulling "supporting" signals for a domain floods on lord-in-house-per-varga.

## design_correctness_verdict: WEAK

## Findings
- summary: lord_in_house_per_varga emits 1740 signals/chart — even correctly held at 'supporting' tier, this single-category volume dominates the supporting pool and drowns other supporting-tier signals by count when a consumer retrieves a domain's supporting evidence.
  failure_class: 7 (DROWNED — by volume, not by tier-inflation)
  severity: MED
  suspected_layer: architecture / serving-query (no per-category cap or dedup on retrieval)
  evidence: cell1=1740 both charts, all cell5 composite_state=1740, all cell2 supporting=1740; 3480 chart_facts combined → near-1:1 pass-through with no consolidation.
  reproducible_call: SQL recipe, cell1/cell2/cell5 rows.

## Positive note: salience discipline is CORRECT here (0 inflated to major/chart_defining) and domain mapping includes wealth — contrast with karaka_web/lord_aspects_per_varga which inflate the same class of per-varga descriptive data.
