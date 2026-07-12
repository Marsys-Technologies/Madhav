# shard-9b-nakshatra_cross_ayanamsha

**shard_id:** 9b-nakshatra_cross_ayanamsha
**lane:** 9b (MSR ingestion coverage + fidelity)

## Exact SQL run
5-cell recipe with `f.fact_category = 'nakshatra_cross_ayanamsha'` over charts `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek) + `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan). Plus denominator: `SELECT COUNT(*) FROM chart_facts WHERE fact_category='nakshatra_cross_ayanamsha' AND chart_id IN (...)`.

## Verbatim results
- chart_facts denominator: Abhisek=17, Abhinandan=19.
- cell1 (consumed): Abhisek=45, Abhinandan=50 signals.
- cell2_salience: Abhisek `background=5, major=15, supporting=25`; Abhinandan `background=19, major=5, supporting=26`.
- cell3_attr: Abhisek `45/45`; Abhinandan `50/50` (100% attributed).
- cell4_domains: both `character|relationship`.
- cell5_type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES (45/50).
2. Salience: spread across background/major/supporting; **15 signals at `major` tier for Abhisek**.
3. Attribution: 100% resolvable (SOUND on attribution axis).
4. Domain: uniformly `character|relationship`.
5. Emergence: 45–50 signals from 17–19 facts (composite_state).

## design_correctness_verdict: WEAK
`nakshatra_cross_ayanamsha` is a diagnostic/QC category (which nakshatra the Moon/points fall in under each of the 5 ayanamshas — a technical robustness fact, near-zero decision weight for a life reading). Yet 15 of its signals sit at `major` tier for Abhisek (salience inflation, R-44b pattern). It is also mapped uniformly to `character|relationship`, but an ayanamsha-sensitivity diagnostic is not intrinsically a character/relationship fact — this is category-family default mapping, not content-driven mapping.

## Findings
- **F1** — salience inflation. class 7 (DROWNED). severity MED. Evidence: cell2 Abhisek `major=15`. A pure ayanamsha-diagnostic category presenting 15 `major`-tier signals promotes low-decision-weight trivia to the tier a consuming LLM treats as chart-shaping.
- **F2** — default domain mapping. class 2 (WRONG). severity LOW. Evidence: cell4 both charts `character|relationship` for an ayanamsha-comparison fact; mapping is by nakshatra-family default, not by the fact's actual relevance.
