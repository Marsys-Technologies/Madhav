# Shard 9b — graha_pada_join

shard_id: 9b-graha_pada_join
charts: Abhisek 482012f1 · Abhinandan 1c826d5a

## Exact SQL: proven 9b 5-cell recipe, <CAT>=graha_pada_join.

## Verbatim results
chart_facts baseline: Abhisek=200, Abhinandan=200.
- cell1: Abhinandan=131, Abhisek=131
- cell2_salience: Abhinandan `background=37, major=11, supporting=83`; Abhisek `background=12, major=25, supporting=94`
- cell3_attr: `131/131` both charts
- cell4_domains: BOTH `character|relationship`
- cell5_type: `composite_state=131` both

## 5-cell verdicts
1. Consumed? YES (131).
2. Salience: mostly supporting/background — proportionate.
3. Attribution: 100% non-empty — sound.
4. Domains: character|relationship only — mildly narrow (pada drives D9/navamsha → relationship is defensible, but pada also carries dharma/career signification that never surfaces).
5. Emergence: composite_state.

## design_correctness_verdict: WEAK

## Findings
- **Pada signals domain-mono-mapped to character|relationship.** All 131 graha_pada_join signals per chart map only to `character|relationship`. Pada (nakshatra-pada → navamsha sign) is the D9 backbone and carries career/dharma signification, not solely relationship; a career/dharma domain-filtered query cannot retrieve pada signals. failure_class=2 (WRONG). severity=LOW (relationship mapping is partially defensible for pada). suspected layer: L-writer domain-mapping. evidence: cell4 both charts = `character|relationship` over 131/131 signals.
