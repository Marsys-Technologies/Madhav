# Shard 9b-kp_ruling_planets_natal

shard_id: 9b-kp_ruling_planets_natal
stream: 9b
charts: 482012f1, 1c826d5a

## Exact SQL: 9b 5-cell recipe with f.fact_category='kp_ruling_planets_natal'. chart_facts census: 100 rows combined.

## Verbatim results
- cell1: 482=39, 1c8=40 → CONSUMED
- cell2_salience: 482=supporting=39 ; 1c8=supporting=40
- cell3_attr: 482=39/39 ; 1c8=40/40 (100%)
- cell4_domains: 482=character|relationship ; 1c8=character|relationship
- cell5_type: 482=tradition_specific=39 ; 1c8=tradition_specific=40

## 5-cell verdicts
1. Consumed? YES (39/40).
2. Salience: 100% supporting — proportionate. PASS.
3. Attribution: 100%. PASS.
4. Domain: uniform character|relationship. DEFECT — KP Ruling Planets (day/hora/lagna/moon-star lords) are KP's event-TIMING instrument used across ALL domains (wealth acquisition, career events, marriage). Mapping only to character|relationship means a wealth or career query can NEVER surface KP ruling-planet signals. This is a direct instance of the KP-4 pattern (KP method domain-defaulted away from wealth).
5. Emergence: ~40 signals, single type class.

## design_correctness_verdict: WEAK

## Findings
- summary: kp_ruling_planets_natal signals domain-mapped only to character|relationship — omitting wealth and career, the very domains KP ruling planets are used to time; renders them unreachable under wealth/career domain queries.
  failure_class: 1 (UNREACHABLE — domain-omission blocks retrieval; KP-4 anchor rediscovery)
  severity: MED
  suspected_layer: L-writer (domain mapping)
  evidence: cell4 = "character|relationship" only, both charts, all ~40 signals; no wealth/career domain present.
  reproducible_call: SQL recipe, cell4_domains row.

## Anchor note (KP-4): REDISCOVERED / CONFIRMED for kp_ruling_planets_natal — KP category domain-mapped so it cannot surface in wealth/career queries.
