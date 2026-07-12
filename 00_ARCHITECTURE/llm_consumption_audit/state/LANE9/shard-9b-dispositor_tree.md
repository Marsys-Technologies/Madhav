# shard-9b-dispositor_tree

**Shard id:** 9b-dispositor_tree
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='dispositor_tree' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 1450 (Abhisek) / 1450 (Abhinandan)
- cell1 signals: Abhisek=1277, Abhinandan=1268
- cell2 salience: Abhisek `background=3, chart_defining=84, major=843, supporting=347`; Abhinandan `background=249, chart_defining=82, major=687, supporting=250`
- cell3 attribution: 1277/1277, 1268/1268
- cell4 domains: both `character|career`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — near-full (1268–1277 of 1450)
2. Salience: 687–843 at `major` — salience inflation of structural dispositor-tree nodes
3. Attribution: 100%
4. Domains: rigid `character|career`
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Same profile as dispositor_chain_per_varga: full attribution but (b) salience inflation (843 tree nodes at major tier) and (c) uniform `character|career` domain. Structural dispositor-tree membership is rarely chart-decisive at the volume seen; promoting ~800 to major dilutes the major tier.

## Findings
- summary: 687–843 dispositor_tree signals at `major` tier — structural tree nodes inflated to decision-relevant salience, diluting the major tier. failure_class 7 (DROWNED via salience inflation). severity MED. evidence: cell2 Abhisek `major=843` of 1277; cell4 uniform `character|career`.
