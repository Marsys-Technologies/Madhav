# shard-9b-graha_tara_bala

Lane: 9b MSR ingestion. Charts: Abhisek `482012f1`, Abhinandan `1c826d5a`.

## Reproducible call
9b 5-cell recipe with `<CAT>='graha_tara_bala'`. chart_facts denominator: **150 / 150**.

## Verbatim results
- cell1: 1c826d5a=**114**, 482012f1=**121**
- cell2_salience: 1c826d5a="background=37, major=9, supporting=68"; 482012f1="background=13, major=20, supporting=88"
- cell5_type: composite_state (114 / 121)
- cell3_attr: "114/114", "121/121"
- cell4_domains: both "character|relationship"

## 5-cell verdicts
1. Consumed? **YES** — 114 / 121 signals (150 chart_facts → ~80%).
2. Salience: supporting-dominant (68 / 88) with modest major and background — proportionate spread, no inflation.
3. Attribution: **100%** (114/114, 121/121). PASS.
4. Domain: uniform "character|relationship". Tara bala is a nakshatra-based transit/prognostic strength (janma/sampat/vipat taras etc.); mapping it to **relationship** is semantically wrong — tara bala has nothing intrinsically to do with the relationship domain.
5. Emergence: composite_state, 114–121 signals.

## design_correctness_verdict: WEAK
Consumed, fully attributed, salience proportionate — but domain mapping is semantically incorrect: tara bala (a timing/transit-strength construct) is uniformly tagged character|relationship, so it both mis-surfaces under relationship queries and is absent from the timing/prognostic contexts where it belongs.

## Findings
- **F1 (class 2 WRONG, HIGH):** all 114–121 tara_bala signals mapped to "character|relationship"; tara bala is a transit/muhurta prognostic-strength metric with no intrinsic relationship semantics. Evidence: cell4="character|relationship" both charts. Rationale: an acharya reads tara bala for timing/favorability, never as relationship evidence; the mapping is a category error, not a defensible generalization.
- **F2 (class 7 DROWNED, LOW):** 114–121 signals from a 150-row transit-strength table is high volume; salience spread is acceptable so severity is low, but the population size compounds the shard-wide funnel-width concern.
