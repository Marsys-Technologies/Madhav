# shard-9b-aspect_tajik

**Shard id:** aspect_tajik (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `aspect_tajik`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 20 (Abhisek `482012f1`) / 11 (Abhinandan `1c826d5a`)
- cell1 (signals): 20 / 11
- cell2_salience: `supporting=20` / `supporting=11`
- cell5_type: `annual=20` / `annual=11`
- cell3_attr: 20/20 / 11/11
- cell4_domains: `character|career` (both)

## 5-cell verdicts
1. Consumed? YES.
2. Salience: `supporting` — proportionate for annual/varshaphala technique.
3. Attribution: full — SOUND.
4. Domain: fixed `character|career`.
5. Emergence: correctly typed `signal_type_class=annual` (Tajik = varshaphala/annual method) — a CORRECT type classification, unlike the generic `composite_state` most aspect categories get.

## design_correctness_verdict: WEAK
Consumed, fully attributed, proportionate salience, and CORRECTLY typed `annual` (affirmative positive: the system recognizes Tajik as annual-chart technique). Only defect: fixed `character|career` domain — Tajik ithasala/muthashila yogas are frequently used for specific year-domain prashna (wealth, marriage timing) and the default domain hides them.

## Findings
- **F1 (class 2 WRONG, LOW):** aspect_tajik fixed to `character|career` despite Tajik annual aspects being applied to specific-domain year questions. Evidence: cell4=`character|career`, cell5=`annual` (both charts).
