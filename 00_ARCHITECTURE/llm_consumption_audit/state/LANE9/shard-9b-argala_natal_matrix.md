# shard-9b-argala_natal_matrix

**shard_id:** 9b-argala_natal_matrix
**charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## Reproducible call
Proven 9b 5-cell recipe, `fact_category='argala_natal_matrix'`, both charts; plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: Abhisek=20880, Abhinandan=20880
- cell1: Abhisek=1300, Abhinandan=1228
- cell2_salience: Abhisek `supporting=1300`; Abhinandan `supporting=1228`
- cell3_attr: Abhisek `1300/1300`; Abhinandan `1228/1228`
- cell4_domains: both `career|character|relationship`
- cell5_type: both `composite_state` (=1300 / =1228)

## Five-cell verdicts
1. Consumed: YES (heavily).
2. Salience: all `supporting` — appropriately NOT promoted; keeps 1300 rows out of top-K. PASS.
3. Attribution: full (1300/1300, 1228/1228). PASS.
4. Domain: `career|character|relationship` — broad but argala (intervention on all houses) is genuinely cross-domain. PASS-with-note.
5. Emergence: 20,880 facts → 1300/1228 signals (~6% pass-through), single `composite_state` type.

## design_correctness_verdict: WEAK
Attribution and tier-placement are correct. Defect risk: a SINGLE fact_category emits ~1300 same-tier (`supporting`), same-type (`composite_state`), same-domain-set signals. If any consumer pulls the supporting tier for this domain, these 1300 near-homogeneous argala rows form a duplication/near-duplication wall (charter §7.1 signal-to-trivia, class 7 DROWNED risk). Mitigated only by the tier gate — not by intra-category discrimination.

## Findings
- summary: argala_natal_matrix emits ~1300 signals per chart at one uniform tier/type/domain-set — a latent duplication wall if the supporting tier is consumed; failure_class 7 (DROWNED, latent); severity MED; evidence: cell1=1300/1228, cell2 `supporting=1300`/`=1228`, cell5 `composite_state=1300`, single domain-set `career|character|relationship`. Suspected layer: ranking (bo_laksana salience/dedup within category).
