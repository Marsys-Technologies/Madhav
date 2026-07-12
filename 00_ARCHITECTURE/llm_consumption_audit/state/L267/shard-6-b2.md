# Lane 6 — RANKED-SURFACE-QUALITY — shard-6-b2

Charter §7.4 (raw-metrics-always). Chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan). Deployed MCP connector, read-only. Raw values reported for every metric even when within tolerance.

---

## SURFACE 1 — `get_chart_orientation` (top_k = 10 `top_signals`)

### Verbatim top-K (rank shown = `top_k_salience_rank` field, sal = `computed_salience`)
```
1  sal=2.00 rank=188  navamsha_d9_cross_check:venus  facts=[985ad66f58943277] val=benefic
     "D9 cross-check: Venus D1=exalted × D9=Friend → concordant_strong"
2  sal=1.38 rank=547  graha_tara_bala:tara_count           "tara count = 22 [ga_sensitive]"
3  sal=1.38 rank=525  graha_nakshatra_join:presiding_deity "presiding deity = Pushan [ga_sensitive]"
4  sal=1.38 rank=524  graha_nakshatra_join:pakshi          "pakshi = Elephant [ga_sensitive]"
5  sal=1.38 rank=532  graha_pada_join:akshara              "akshara = Cha [ga_sensitive]"
6  sal=1.38 rank=533  graha_pada_join:navamsa_sign         "navamsa sign = Aquarius [ga_sensitive]"
7  sal=1.38 rank=519  graha_nakshatra_join:guna            "guna = Sattva [ga_sensitive]"
8  sal=1.38 rank=523  graha_nakshatra_join:nakshatra_lord  "nakshatra lord = mercury [ga_sensitive]"
9  sal=1.38 rank=535  graha_pada_join:pada_number_ref      "pada number ref = 3 [ga_sensitive]"
10 sal=1.38 rank=557  nakshatra_cross_ayanamsha:stable_nakshatra_id "stable nakshatra id = 27 [ga_sensitive]"
```
Digest: msr_signal_count=13369, yoga_count=13, dosha_count=22, contradiction_count=0.
Entity profiles (3 total): UNATTRIBUTED agg=84.7971 n=298 · VENUS agg=1.0457 n=1 · JUPITER agg=0.6375 n=1.

### RAW METRICS
1. **duplication_rate** = 0% exact-id (10 distinct ids) / **70% near-duplicate** — rows 2–10 are 9 facets of the *same* Moon-nakshatra placement (7 nakshatra/pada attribute joins + tara_bala + cross-ayanamsha), not 9 distinct chart signals.
2. **identical_score_walls** = YES — one **9-wide wall at salience 1.38** (rows 2–10). 3+ co-tied triggered massively; ranking cannot discriminate among 9 of 10 rows.
3. **descriptive_trivia_share** = **90% (9/10)** — presiding deity, pakshi, akshara, navamsa sign, guna, nakshatra lord, pada number, tara count, stable nakshatra id are pure descriptive attribute lookups (classical canon weight ~0). Only row 1 (Venus exalted D1×D9 concordant_strong) is chart-defining.
4. **family_collapse_coverage** = **~2 families / severe collapse** — top-10 collapses onto {nakshatra-attribute cluster, 1 varga_pattern}. 0 of 13 yogas and 0 of 22 doshas surface in top-K.
5. **UNATTRIBUTED_share** = **98.05%** by entity-aggregate dominance (84.7971 / 86.4803); **100%** at envelope (`grounding.fact_ids=[]`, `grounding_score=null`) — R-44a anchor re-derived blind and confirmed. Row-level constituent_facts present (0/10 blank) but never surfaced into envelope grounding.

**drowned_verdict = DROWNED (class 7) — YES.** Nine descriptive nakshatra-trivia rows on a flat 1.38 wall bury the single interpretive signal; the entity ranking is 98% an UNATTRIBUTED bucket. Note also `top_k_salience_rank` (188 vs 519–557) contradicts the presented order and `computed_salience` — internal ranking inconsistency. `trim_report=null` and `pagination.total=null` despite only 10 of 13369 shown — non-disclosed trim.

---

## SURFACES 2–4 — `get_domain_reading` career / wealth / relationship (top_k = 20 per lens)

### CROSS-DOMAIN COLLAPSE (headline finding)
Top-10 signal_ids are **100% identical** across career, wealth, AND relationship (a7b7703a, f7666527, b94f4cd0, a46549f8, 3dcec353, 7e169d1d, a8f0ac01, 400b8425, aa4abe58, 9ffc2479 — all composite_state, salience 2.99→2.346). A marriage question returns the exact same "chart-defining" rows as a career question.
```
career vs wealth        top10 overlap = 10/10   top20 = 10/20
career vs relationship  top10 overlap = 10/10   top20 = 10/20
wealth vs relationship  top10 overlap = 10/10   top20 = 19/20
ALL THREE common top10  = 10/10
```

### RAW METRICS (identical structure across all three domains)
| metric | career | wealth | relationship |
|---|---|---|---|
| duplication_rate (within, exact-id) | 0% | 0% | 0% |
| duplication_rate (cross-domain, top10) | **100%** | **100%** | **100%** |
| identical_score_walls (3+ co-tied) | YES: 2.76×4, **2.3×10** | YES: 2.76×4, **2.3×10** | YES: 2.76×4, **2.3×10** |
| co-tied rows in top20 | 14/20 (70%) | 14/20 | 14/20 |
| descriptive_trivia_share | ~0% (all composite_state) | ~0% | ~0% |
| family_collapse_coverage (distinct type-classes) | 3 (composite_state 17, varga 2, karaka 1) | **1 (composite_state 20)** | **1 (composite_state 20)** |
| source_l1_asset diversity | 1 (ga_structural ×20) | 1 (ga_structural ×20) | 1 (ga_structural ×20) |
| UNATTRIBUTED_share (envelope) | **100%** (`grounding` absent) | 100% | 100% |

Verbatim top-20 saliences (identical vector all three): `[2.99, 2.76, 2.76, 2.76, 2.76, 2.645, 2.645, 2.415, 2.415, 2.346, 2.3, 2.3, 2.3, 2.3, 2.3, 2.3, 2.3, 2.3, 2.3, 2.3]`.

**drowned_verdict = DROWNED (class 7) — YES (all three domains).** The ranking is domain-blind: the same 10 ga_structural composite_states dominate every question, positions 11–20 sit on a flat 10-wide 2.3 wall, and every row is a single signal_type_class from a single L1 asset. Domain-specific signals (the whole point of a domain reading) never reach top-K.

### Receipt honesty (captured)
- All three domains disclose trimming honestly: `signal_id_refs_capped=true`, refs_returned=200 of totals **12378 (career) / 1984 (wealth) / 7012 (relationship)**; `token_safety_note`="Bounded to 3 lenses × 20 signals."
- `provenance.model_mismatch_note`: lenses have no domain column — filtered at query-time via `DOMAIN_TO_QUESTION_TYPES`; "unmapped domains return all lenses (no filter)". `provenance.defect_001` DEFECT-001 = MOSTLY_RESOLVED (constituent_facts resolution). These disclosures are honest but confirm the domain filter is coarse (question_type mapping, not true per-domain ranking) — the mechanistic root of the cross-domain collapse.
- `grounding`, `pagination`, `trim_report`, `ranking_basis` all `null` on domain envelopes — no fact-level attribution surfaced (rows carry `source_l1_asset` only).
