---
artifact: A6_VARGAS_SPEC_v1_0.md
document: A6 — Vargas (Divisional Charts) Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed full classical varga scope across 30 vargas + all surgical additions A-K)
intended_for: Claude Code sub-agents implementing the A6 per-chart vargas writer
prime_directive: Only computed facts. No narrative, no opinion. Per-category two-pass verification declared in CHART_FACTS_SCHEMA.json.
depends_on: A1 engine, A3 schema, G16 Varga formula library, G41 Lal Kitab corpus, G44 Nadi tables
---

# A6 — Vargas (Divisional Charts) Specification

## §0 — Mission

For each chart per ayanamsha, compute every classical divisional position across 30 vargas with full deity/devata/quality attribution, formula variants, cross-varga harmonics, per-varga strength contributions, and Lal Kitab-specific emissions. All values deterministic; per-category two-pass methodology declared in schema.

## §1 — Varga set (30 vargas locked)

**Parashari 16 (Shodasavarga):** D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.
**Supplementary Parashari (11):** D5, D6, D8, D11, D14, D15, D21, D32, D33, D50, D54.
**Nadi (3):** D108, D150, D2700.

## §2 — Locked decisions (from 8 clarification answers + 11 additions A–K)

| # | Decision | Locked answer |
|---|---|---|
| Q1 | Karaka per varga scope | **(c) All 8 karakas in all 30 vargas** |
| Q2 | Per-varga aspects | **(c) Every varga aspect matrix** |
| Q3 | Per-varga ashtakavarga | **(c) Every varga (BAV computed per varga where formula applies)** |
| Q4 | D60 Shashtiamsa deity attribution | **(a) Yes — 60 named deities per amsa** |
| Q5 | D150 Nadiamsa rishi attribution | **(a) Yes — 27-rishi attribution** |
| Q6 | D2700 sub-rishi attribution | **(a) Yes — finest Nadi sub-attribution** |
| Q7 | Pushkara generalization | **(b) D9-only (Pushkara navamsa + Pushkara bhaga split into 2 categories)** |
| Q8 | D2 Hora variants | **(a) Both Parashari + Jaimini formula_id variants** |
| A | Per-varga deity/devata/quality attribution (D2-D108) | **INCLUDED** |
| B | Formula-variant emissions (D3 Drekkana 3 variants; D30 Trimsamsa 5-lord per-amsa explicit) | **INCLUDED** |
| C | Cross-varga harmonics (Super-vargottama, Trikona vargottama, Trans-vargottama count) | **INCLUDED** |
| D | Per-varga Vimsopaka contribution + Saptavargaja bala component | **INCLUDED** (consumed by A8) |
| E | Pushkara split: Pushkara navamsa flag + Pushkara bhaga flag (2 categories) | **INCLUDED** |
| F | D27 Bhamsa directional emission (N/S/E/W quadrants) | **INCLUDED** |
| G | D9 Lagna-specific flags (Pushkara Lagna + Vargottama Lagna) | **INCLUDED** |
| H | Karya-bhava per varga (e.g., D10 Karya = 10th from D10 Sun) | **INCLUDED** |
| I | Lal Kitab varga-specific (D9 + D12 Pakka Ghar reading) | **INCLUDED** |
| J | D9 sub-amsa (D81) | **SKIPPED** per discussion |
| K | Bhinashtakavarga per varga | **Subsumed by Q3=c** |

## §3 — Fact categories A6 emits (all ayanamsha-DEPENDENT, ~25 categories)

| # | Category | Subjects |
|---|---|---|
| 1 | `varga_position` | Per body (25: 23 grahas/Lilith/asteroids + Lagna + MC) per varga. Subject = `<VARGA_ID>.<BODY>` |
| 2 | `varga_dignity` | Per body per varga (Exalted/Debilitated/Own/MT/Friend/Enemy/Neutral) |
| 3 | `varga_vargottama_flag` | Per body per varga (vs D1) |
| 4 | `varga_super_vargottama_flag` | Per body — true if same sign in ≥3 vargas (major strength multiplier) |
| 5 | `varga_trikona_vargottama_flag` | Per body — true if 1/5/9 sign relationship across vargas (Jaimini-relevant) |
| 6 | `varga_trans_vargottama_count` | Per body — count of how many of 30 vargas retain D1 sign |
| 7 | `varga_pushkara_navamsa_flag` | Per body — D9 pushkara navamsa positions only |
| 8 | `varga_pushkara_bhaga_flag` | Per body — D1 degree-point pushkara (Taurus 21°, Cancer 14°, etc.) |
| 9 | `varga_house_lord` | Per house per varga (12 × 30 = 360 × 5 ay = 1,800 rows) |
| 10 | `varga_house_occupant` | Per varga per house: occupants |
| 11 | `varga_aspect_matrix` | Aspect matrix in EVERY varga (Parashari + Jaimini) |
| 12 | `varga_ashtakavarga` | BAV computed in every varga where formula applies |
| 13 | `varga_rollup` | Per-varga rollups: vargottama_count, super_vargottama_count, pushkara_count, exalted_count, debilitated_count, own_sign_count, friendly_count, enemy_count, overall_dignity_score |
| 14 | `varga_deity_attribution` | Per body per varga — deity per amsa where classical attribution exists (D60 60 deities + 12-class quality, D40 40 devatas, D45 45 devatas, D30 5-lord regions, D20 20 deities, D24 24 deities, D16 16 devatas, D9 navamsa deity, D3 Mukha/Madhya/Pucha + deity, D2 Surya/Chandra hora, D50/D54 amsa qualities, D108 karma-type) |
| 15 | `varga_formula_variant_position` | Same body-varga position computed under alternate formula_id; emitted as separate rows for D3 Drekkana (Parashari/Jaimini/Mooltrikona), D2 Hora (Parashari/Jaimini) |
| 16 | `varga_d30_lord_per_amsa` | D30 Trimsamsa specific: 5-lord chain (Mars/Saturn/Jupiter/Mercury/Venus) per amsa with odd/even sign variation |
| 17 | `varga_vimsopaka_contribution` | Per-varga dignity-score contribution feeding A3 graha_vimsopaka_* rollups |
| 18 | `varga_saptavargaja_bala_component` | Per-graha per-varga Sthana-bala contribution (consumed by A8 shadbala) |
| 19 | `varga_d27_directional_quadrant` | D27 Bhamsa: per body, which directional quadrant (N/S/E/W) |
| 20 | `varga_d9_lagna_special` | Vargottama Lagna flag + Pushkara Lagna flag (D9-specific) |
| 21 | `varga_karya_bhava_per_varga` | Per-varga karya-bhava derivation (e.g., D10 Karya = 10th from D10 Sun for career) |
| 22 | `karaka_per_varga` | 8 Jaimini Chara karakas (AK/AmK/BK/MK/PK/GK/DK/SK) × 30 vargas — assigned graha, sign, dignity in that varga |
| 23 | `varga_lal_kitab_special` | D9 Pakka Ghar reading + D12 Lal Kitab interpretation (uses G41 corpus) |
| 24 | `varga_d108_karma_attribution` | D108 Ashtottaramsa: per body per amsa karma-type attribution |
| 25 | `varga_d150_rishi` + `varga_d2700_sub_rishi` | Rishi + sub-rishi per body per amsa (joins G44) |

## §4 — Per-row standard fields

A3 §6 standard + 6 universal enrichments from A5 §3 (tolerance_arcsec, near_sign_boundary_flag, near_nakshatra_boundary_flag, vargottama_flag_at_point, formula_provenance_text, cross_ayanamsha_divergence_arcsec).

Per `varga_position` row: `longitude_within_varga`, `sign`, `sign_lord`, `nakshatra` (where varga has nakshatra resolution), `pada`, `decanate_position`, `house_d1_equivalent`, `formula_id` (links to G16).

## §5 — Verification methodology (per-category, declared in CHART_FACTS_SCHEMA.json)

| Category | Verification minimum |
|---|---|
| `varga_position` D1-D60 standard 16 | `single` (G16 + Swiss Ephemeris authoritative) |
| `varga_position` D60 Shashtiamsa | `two_pass_verified` (most consequential per Parashara) |
| `varga_position` D108 / D150 / D2700 Nadi | `two_pass_verified` (small errors compound) |
| `varga_dignity` | `two_pass_verified` |
| `varga_vargottama_flag` + super + trikona + trans | `two_pass_verified` |
| `varga_pushkara_navamsa_flag` + `varga_pushkara_bhaga_flag` | `two_pass_verified` |
| `varga_deity_attribution` (all vargas) | `two_pass_verified` (table-driven; double-pass against classical text + G44 cross-reference) |
| `varga_formula_variant_position` | `two_pass_verified` (each formula variant independently re-derived) |
| `varga_d30_lord_per_amsa` | `two_pass_verified` |
| `varga_aspect_matrix` (every varga) | `two_pass_verified` |
| `varga_ashtakavarga` (every varga) | `two_pass_verified` |
| `varga_vimsopaka_contribution` + `saptavargaja_bala_component` | `two_pass_verified` (feeds downstream A8) |
| `varga_karya_bhava_per_varga` | `two_pass_verified` |
| `karaka_per_varga` | `two_pass_verified` (with school variant Rahu in/out per A5) |
| `varga_lal_kitab_special` | `two_pass_verified` (against G41 corpus) |
| `varga_d108_karma_attribution` | `two_pass_verified` |
| `varga_d150_rishi` + `varga_d2700_sub_rishi` | `two_pass_verified` (cross-check G44 rishi-attribution table) |
| `varga_house_lord` + `varga_house_occupant` | `single` |
| `varga_d27_directional_quadrant` | `single` |
| `varga_d9_lagna_special` | `two_pass_verified` |

Divergent_flagged halts build per A3 §17.

## §6 — Citations (dual form per A3 §6)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Sun's D9 sign (Lahiri) | `varga_position.D9.SUN.sign@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Sun's Navamsa (D9) sign: Aries (Lahiri)." |
| Saturn vargottama in D60 | `varga_vargottama_flag.D60.SAT.vargottama@chart=...:ay=lahiri:...` | "Saturn is vargottama in D60 Shashtiamsa (Lahiri)." |
| Sun's D60 deity (Lahiri) | `varga_deity_attribution.D60.SUN.deity@chart=...:ay=lahiri:...` | "Sun's D60 amsa deity: Yaksha (Lahiri)." |
| AK in D10 (Lahiri) | `karaka_per_varga.D10.ATMAKARAKA.assigned_graha@chart=...:ay=lahiri:...` | "Atmakaraka's D10 position: Capricorn (career-significator placement, Lahiri)." |
| D27 directional quadrant — Moon | `varga_d27_directional_quadrant.D27.MOON.quadrant@chart=...:ay=lahiri:...` | "Moon's D27 Bhamsa quadrant: East (Lahiri)." |
| D150 rishi — Mercury | `varga_d150_rishi.D150.MER.rishi@chart=...:ay=lahiri:...` | "Mercury's D150 Nadiamsa rishi: Vasishtha (Lahiri)." |

## §7 — Row count projection per (chart, ayanamsha)

| Group | Rows |
|---|---|
| varga_position (25 × 30 × ~6) | ~4,500 |
| varga_dignity (25 × 30) | ~750 |
| varga_vargottama_flag (25 × 30) | ~750 |
| varga_super_vargottama_flag (25) | 25 |
| varga_trikona_vargottama_flag (25 × 30 sign-relationships) | ~750 |
| varga_trans_vargottama_count (25 × 1) | 25 |
| varga_pushkara_navamsa_flag + varga_pushkara_bhaga_flag (25 × 2) | 50 |
| varga_house_lord (12 × 30 × 4) | 1,440 |
| varga_house_occupant (12 × 30 × ~3) | 1,080 |
| varga_aspect_matrix (every varga × ~36 pairs) | ~1,080 |
| varga_ashtakavarga (every varga × BAV details) | ~2,400 |
| varga_rollup (30 × 9 fields) | 270 |
| varga_deity_attribution (avg 25 × ~10 vargas with deity attribution × ~3 keys) | ~750 |
| varga_formula_variant_position (3 D3 variants + 2 D2 variants × 25 bodies × ~4 fields) | ~500 |
| varga_d30_lord_per_amsa (30 amsas × 12 signs) | 360 |
| varga_vimsopaka_contribution (25 × 30) | 750 |
| varga_saptavargaja_bala_component (7 grahas × 7 vargas in Saptavarga) | 49 |
| varga_d27_directional_quadrant (25) | 25 |
| varga_d9_lagna_special (2 flags) | 2 |
| varga_karya_bhava_per_varga (30 vargas × ~3 karyas each) | 90 |
| karaka_per_varga (8 × 30 × ~4 fields) | 960 |
| varga_lal_kitab_special (~20) | 20 |
| varga_d108_karma_attribution (25 × 108 amsas? no — per body, 1 amsa per body) | 25 |
| varga_d150_rishi (25 bodies × 1 rishi each) | 25 |
| varga_d2700_sub_rishi (25 × 1) | 25 |

**Total A6 per (chart, ayanamsha): ~15,750 rows. × 5 ayanamshas = ~78,750 varga rows per chart.**

Largest writer in A1-A14. Within Postgres comfort zone at internal scale.

## §8 — Materialized view

`mv_chart_vargas_summary` — joins per-(chart, ayanamsha, body, varga) into one wide row for fast "show me Saturn's full picture across all 30 vargas" queries. Refreshed synchronously at build close per A3 §10.

`mv_chart_super_vargottama_bodies` — bodies that are super-vargottama; small but high-signal MV for tools that want to find super-strong bodies quickly.

## §9 — Tool retrieval contract

`query_vargas(chart_id, ayanamsha_ids[], scope_filter=['all' | 'parashari_16' | 'supplementary' | 'nadi' | 'd9_only' | 'd10_only' | <varga_id>])` → rows.

`query_varga_specific(chart_id, ayanamsha_id, varga_id, body)` → 1 row from mv_chart_vargas_summary.

`query_super_vargottama(chart_id, ayanamsha_id)` → list from mv_chart_super_vargottama_bodies.

## §10 — Implementation notes

1. G16 Varga formula library must support every varga formula with formula_id taxonomy (Parashari standard, Jaimini variants, Mooltrikona D3, etc.).
2. D60 named deities table: 60 entries (Ghora/Rakshasa/Deva/Kubera/Yaksha/Kinnara/Bhrashta/Kulagna/Garala/Vahni/Mritu/Sudha cycle — 5 cycles of 12 = 60, BUT classical assignment isn't strict cyclical; embed exact BPHS Ch.7 table).
3. D40 + D45 devata lists embedded as constants in engine code.
4. D108 karma-type attribution table embedded; cross-reference with G44 for consistency.
5. Cross-varga harmonics compute super-vargottama AFTER all per-varga positions are written (post-pass).
6. Lal Kitab D9 Pakka Ghar reading uses G41 corpus rules; pre-compile into Python dict.
7. Per-varga aspect matrix in Q2=c every varga is a heavy emit; consider caching per-varga sign-relationship matrix.
8. Two-pass verification: implement independent formula re-derivation paths per category in CHART_FACTS_SCHEMA.json declarations.

## §11 — Locked decisions (final committed surface)

1. 30 vargas (16 Parashari + 11 supplementary + 3 Nadi)
2. ~25 fact_categories
3. All 8 question answers locked per §2
4. All 11 additions A-K locked (J skipped, K subsumed by Q3=c)
5. Per-category two-pass verification methodology in CHART_FACTS_SCHEMA.json
6. 6 universal enrichment fields per row (per A5 §3)
7. ~78,750 varga rows per chart (5 ayanamshas)
8. 2 MVs: mv_chart_vargas_summary + mv_chart_super_vargottama_bodies (natal-fixed; refresh at build close)

A3 enum must absorb the ~25 new A6 categories. Running A3 enum count: ~131 (initial) + 16 (A5 additions) + 25 (A6 additions) = ~172 fact_categories total.

---

*End of A6_VARGAS_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
