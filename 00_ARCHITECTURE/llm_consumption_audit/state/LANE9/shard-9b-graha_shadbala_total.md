# Shard 9b — graha_shadbala_total

shard_id: 9b-graha_shadbala_total
charts: Abhisek 482012f1 · Abhinandan 1c826d5a

## Exact SQL: proven 9b 5-cell recipe, <CAT>=graha_shadbala_total.

## Verbatim results
chart_facts baseline: Abhisek=52, Abhinandan=52.
- cell1: Abhinandan=69, Abhisek=70
- cell2_salience: Abhinandan `background=16, major=34, supporting=19`; Abhisek `major=40, supporting=30`
- cell3_attr: Abhinandan `69/69`, Abhisek `70/70`
- cell4_domains: BOTH `career|wealth`
- cell5_type: Abhinandan `composite_state=69`, Abhisek `composite_state=70`

## 5-cell verdicts
1. Consumed? YES, well (69-70).
2. Salience: major-heavy but DEFENSIBLE — total shadbala IS the decisive strength aggregate an acharya weighs.
3. Attribution: 100% non-empty — sound.
4. Domains: `career|wealth` — broader than the components (which are character|career), but still misses health/relationship where lord strength is decisive.
5. Emergence: composite_state.

## design_correctness_verdict: WEAK

## Findings
- **Total shadbala domain-mapped to career|wealth only — misses health/relationship.** shadbala_total is the aggregate strength that determines whether ANY house lord can deliver (6th/8th lord → health, 7th lord → relationship). Mapping it only to `career|wealth` means a health or relationship domain-filtered query cannot retrieve "is the governing lord strong?". This is the best-mapped member of the shadbala family yet still narrow. failure_class=2 (WRONG). severity=MED. suspected layer: L-writer domain-mapping. evidence: cell4 both = `career|wealth`. NOTE (affirmative): salience (major-heavy) and attribution (69/69, 70/70) are SOUND for the aggregate — the defect is domain reach, not salience or attribution.
