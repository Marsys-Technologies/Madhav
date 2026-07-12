# shard-9b-saham_position

**shard_id:** 9b-saham_position · charts 482012f1 / 1c826d5a

## SQL: proven 9b 5-cell recipe with `<CAT>`='saham_position' + chart_facts count.

## Verbatim results
- chart_facts rows: 482=2800, 1c=2800
- cell1: 482=634, 1c=637 → CONSUMED (funnel 2800→~635)
- cell2_salience: 482=`supporting=634`, 1c=`supporting=637`
- cell5_type: 482=`composite_state=634`, 1c=`composite_state=637`
- cell3_attr: 482=`634/634`, 1c=`637/637` (100%)
- cell4_domains: `character|relationship` (both, all)

## Five-cell verdicts
1. Consumed YES. 2. Salience 100% `supporting`. 3. Attribution SOUND (100%). 4. Domain COLLAPSED to `character|relationship` for ALL saham signals — but sahams span the FULL life-theme space (Punya/Vidya, Artha/wealth, Roga/disease, Mrityu/death, Vivaha/marriage, Karma/career...). Mapping every saham to `character|relationship` EXCLUDES wealth, health, longevity, career. 5. All `composite_state`.

## design_correctness_verdict: BROKEN
This is a direct **KP-4-class** domain-collapse rediscovery. A wealth saham (Artha/Labha) or a disease saham (Roga) can NEVER surface under a wealth-domain or health-domain query because its `domains_affected_array` is forced to `character|relationship`. The signals are consumed and attributed, but the domain mapping makes an entire category of decision-relevant sahams un-findable and therefore un-trustworthy for domain-filtered synthesis.

## Findings
- **F1 [class 2 WRONG, HIGH]** All 634/637 saham signals domain-mapped to `character|relationship` regardless of the individual saham's signification; sahams centrally include wealth/health/longevity/career, which are excluded → domain-filtered queries in those areas cannot reach these sahams (class-1 UNREACHABLE consequence). Identical across two distinct charts → hardcoded template. Suspected layer: L-writer (bo_laksana domain assignment). Evidence: cell4 `character|relationship` for 100% of signals, both charts.
- **F2 [class 7 DROWNED, MED]** 634/637 signals all `supporting`, no discrimination among 2800 underlying facts. Evidence: cell2.
