# shard-9b-significator_path

**shard_id:** 9b-significator_path · charts 482012f1 / 1c826d5a

## SQL: proven 9b 5-cell recipe with `<CAT>`='significator_path' + chart_facts count.

## Verbatim results
- chart_facts rows: 482=360, 1c=360
- cell1: 482=360, 1c=360 → CONSUMED (1:1 full ingestion, 360=360)
- cell2_salience: 482=`supporting=360`, 1c=`supporting=360`
- cell5_type: 482=`composite_state=360`, 1c=`composite_state=360`
- cell3_attr: 482=`360/360`, 1c=`360/360` (100%)
- cell4_domains: `character|career` (both, all)

## Five-cell verdicts
1. Consumed YES (full 1:1). 2. Salience 100% `supporting`. 3. Attribution SOUND. 4. Domain COLLAPSED to `character|career` for ALL significator paths. Significator paths (KP-style significator chains) point to house significations across ALL 12 bhavas — 2nd/11th (wealth), 6th (health/debt), 7th (marriage), 5th (progeny), etc. Forcing every path to `character|career` excludes wealth, health, marriage, progeny. 5. All `composite_state`.

## design_correctness_verdict: BROKEN
Direct **KP-4** rediscovery. Significator paths are the mechanism by which KP produces domain-specific predictions; collapsing them all to `character|career` means a 2nd/11th-house wealth significator path is un-findable under a wealth query, a 6th-house health path un-findable under health, etc. Consumed and fully attributed, but domain mapping defeats the category's entire purpose.

## Findings
- **F1 [class 2 WRONG, HIGH]** All 360 significator-path signals (both charts) mapped to `character|career` irrespective of which house-significations the path targets → the KP significator-to-domain link is severed; wealth/health/marriage significators cannot surface in their domains (class-1 UNREACHABLE consequence). Chart-invariant template. Suspected layer: L-writer (bo_laksana domain assignment). Evidence: cell4 `character|career` 360/360 both charts.
- **F2 [class 7 DROWNED, MED]** 360/360 flat `supporting`; a domain-decisive category ranked no higher than trivia. Evidence: cell2.
