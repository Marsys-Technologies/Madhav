# shard-9b-ashtakavarga_bindu_per_varga

**shard_id:** 9b-ashtakavarga_bindu_per_varga
**charts:** Abhisek 482012f1 · Abhinandan 1c826d5a

## Reproducible call
Proven 9b 5-cell recipe, `fact_category='ashtakavarga_bindu_per_varga'`, both charts; plus chart_facts denominator count.

## Verbatim results
- chart_facts denominator: Abhisek=6720, Abhinandan=6720
- cell1: Abhisek=1134, Abhinandan=1159
- cell2_salience: Abhisek `major=281, supporting=853`; Abhinandan `background=73, major=207, supporting=879`
- cell3_attr: Abhisek `1134/1134`; Abhinandan `1159/1159`
- cell4_domains: both `character|career`
- cell5_type: both `composite_state` (=1134 / =1159)

## Five-cell verdicts
1. Consumed: YES (heavily).
2. Salience: **281 (Abhisek) / 207 (Abhinandan) signals at `major` tier** for per-varga per-house bindu counts — SALIENCE INFLATION. Classical acharyas weight Rasi (D1) ashtakavarga primarily; per-varga (D9/D10/…) ashtakavarga bindu is niche and rarely chart-weighting. 200+ per-varga bindu rows at `major` = R-44b pattern. FAIL.
3. Attribution: full (1134/1134, 1159/1159). PASS.
4. Domain: `character|career` — note WEALTH dropped vs the D1 `ashtakavarga_bindu` category (which maps `career|wealth`). Per-varga bindu cannot surface in a wealth query. KP-4-analog domain gap.
5. Emergence: 6720 facts → ~1150 signals (~17% pass-through), single type.

## design_correctness_verdict: WEAK
Attribution is perfect, but two consumer-facing defects: (a) 200-280 per-varga bindu signals promoted to `major` tier will crowd genuine chart-defining findings in any top-K a consumer pulls (class 7 DROWNED / salience inflation); (b) domain set drops `wealth` relative to the parent bindu category, making per-varga bindu un-findable in wealth-domain queries (class 2/1).

## Findings
- summary: ~200-280 per-varga ashtakavarga bindu signals sit at `major` tier despite being niche, low-decision-weight granular data — salience inflation / DROWNED; failure_class 7; severity HIGH; evidence: cell2 `major=281` (Abhisek), `major=207` (Abhinandan) out of ~1150 signals. Rationale (charter §7.4 amendment): 200+ major-tier per-varga bindu rows exceed acharya tolerance because per-varga ashtakavarga is not a primary weighting instrument. Suspected layer: ranking (bo_laksana signature_tier).
- summary: ashtakavarga_bindu_per_varga domain-mapped `character|career`, dropping `wealth` present on the parent `ashtakavarga_bindu` — per-varga bindu unreachable in wealth queries; failure_class 2 (WRONG domain mapping, with class-1 consequence for wealth-filtered retrieval); severity MED; evidence: cell4 `character|career` vs parent `career|wealth`. Suspected layer: L-writer (domains_affected_array).
