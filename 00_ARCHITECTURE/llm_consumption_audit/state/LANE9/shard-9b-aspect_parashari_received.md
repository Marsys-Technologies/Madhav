# shard-9b-aspect_parashari_received

**Shard id:** aspect_parashari_received (Lane 9b, MSR ingestion 5-cell)

## Exact SQL run
9b 5-cell recipe with `<CAT>` = `aspect_parashari_received`, both charts. Plus chart_facts denominator.

## Verbatim results
- chart_facts denominator: 95 / 95
- cell1 (signals): 45 / 45
- cell2_salience: `supporting=45` (both)
- cell5_type: `composite_state=45` (both)
- cell3_attr: 45/45 (both)
- cell4_domains: `character|career` (both)

## 5-cell verdicts
1. Consumed? YES (45/chart).
2. Salience: flat `supporting` — but see F1: the mirror category `aspect_parashari_given` (same 95 facts, same aspect relation viewed from the other end) is DIFFERENTIATED across four tiers and mapped to `career|relationship|wealth`. Received is flat + narrower domain.
3. Attribution: 45/45 — SOUND.
4. Domain: fixed `character|career` (narrower than the `career|relationship|wealth` its `given` mirror gets).
5. Emergence: 95 facts → 45 signals.

## design_correctness_verdict: WEAK
Consumed and fully attributed, but treated ASYMMETRICALLY versus its mirror `aspect_parashari_given`: given gets 4-tier chart-specific salience + 3 domains; received gets flat `supporting` + `character|career`. An aspect RECEIVED (e.g. Moon receiving Saturn's aspect) is often the more decision-relevant end, yet it is uniformly demoted to supporting.

## Findings
- **F1 (class 3 INCONSISTENT, MED):** aspect_parashari_received flat-stamped `supporting` + `character|career` while its mirror aspect_parashari_given is differentiated across chart_defining/major/supporting/background + `career|relationship|wealth`. Same underlying aspect relation, incompatible ingestion treatment. Evidence: this shard cell2=`supporting=45`/cell4=`character|career` vs given-shard cell2 four tiers / cell4 `career|relationship|wealth`.
