# shard-9b-dispositor_chain_per_varga

**Shard id:** 9b-dispositor_chain_per_varga
**Charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## SQL run
Standard 5-cell recipe on fact_category='dispositor_chain_per_varga' + chart_facts baseline.

## Verbatim results
- chart_facts baseline: 1305 (Abhisek) / 1305 (Abhinandan)
- cell1 signals: Abhisek=1305, Abhinandan=1305  (full 1:1)
- cell2 salience: Abhisek `background=5, chart_defining=85, major=905, supporting=310`; Abhinandan `background=326, chart_defining=85, major=732, supporting=162`
- cell3 attribution: 1305/1305 both
- cell4 domains: both `character|career`
- cell5 type: both `composite_state`

## Cell verdicts
1. Consumed: YES — full 1:1
2. Salience: 732–905 promoted to `major` — dispositor-chain links are structural plumbing, mostly supporting-weight; 900 at major = salience inflation
3. Attribution: 100%
4. Domains: rigid `character|career`
5. Emergence: composite_state only

## design_correctness_verdict: WEAK
Full consumption and attribution, but two defect patterns: (b) salience inflation — 905 dispositor-chain-link signals at `major` tier where a chain hop is low-decision-weight structural detail; and (c) domain rigidity — all 1305 mapped to `character|career`.

## Findings
- summary: 732–905 dispositor_chain_per_varga signals sit at `major` tier despite being low-weight structural chain-links, inflating salience and drowning genuinely major findings. failure_class 7 (DROWNED via salience inflation, charter §7.4 metric 3). severity MED. evidence: cell2 Abhisek `major=905` of 1305; cell4 uniform `character|career`.
