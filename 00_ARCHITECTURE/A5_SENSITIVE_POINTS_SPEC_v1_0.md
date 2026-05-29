---
artifact: A5_SENSITIVE_POINTS_SPEC_v1_0.md
document: A5 — Sensitive Points Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed full classical + esoteric + Nadi + Tajik + KP + Lal Kitab + Maharsi scope)
intended_for: Claude Code sub-agents implementing the A5 per-chart sensitive-points writer
prime_directive: Only computed facts. No narrative, no opinion. Two-pass verification MANDATORY for every row.
depends_on: A1 engine output, A3 schema, A4 (uses sunrise from A4), G14 Saham library (extended), G20 ayanamsha registry, G24 nakshatra lord, G41 Lal Kitab corpus, G44 Nadi tables
---

# A5 — Sensitive Points Specification

## §0 — Mission

Compute every classical, esoteric, Tajik, KP, Nadi, and Lal Kitab sensitive point at the native's birth instant per ayanamsha. All values deterministic; all rows two-pass verified. Output extends chart_facts with the non-graha, non-panchanga computed positions used by every Vedic + KP + Tajik tradition.

## §1 — Locked decisions (from native sign-off rounds)

- All 14 baseline categories from A3 §3 esoteric+sensitive group
- All 10 surgical-accuracy additions (A.1–A.10)
- All 6 schema enrichments (B) applied universally
- Per-category two-pass methodology (C) declared in `CHART_FACTS_SCHEMA.json`
- 8-karaka system (Atmakaraka through Strikaraka)
- Extended 70+ Saham catalogue (Hellenistic-Tajik full set)
- Both Yogi/Avayogi formula variants (93°20' AND 96°40')
- Both Panchasphuta variants (Saturn AND Rahu)
- Esoteric/Nadi: Jaimini Brahma + Vishnu + Shiva + Sri Yantra + Maharsi-specific + Pranapada sphuta (all in)
- Tajik additional: Hadda + Triraashipathi + Vargottama-specific (all in)

## §2 — Fact categories emitted (30 total, all ayanamsha-DEPENDENT — 5 rows per key per chart)

| # | Category | Subjects | Notes |
|---|---|---|---|
| 1 | `upagraha_position` | DHUMA, VYATIPATA, PARIVESHA, INDRACHAPA, UPAKETU, KALA | 6 classical shadow grahas |
| 2 | `saturn_derived_point` | GULIKA_LAHIRI, GULIKA_HINDU, MANDI, YAMAGANDA_SPHUTA, MAANDI | both reckonings emitted |
| 3 | `esoteric_point_bhrigu_bindu` | BHRIGU_BINDU | midpoint(Moon, Rahu) |
| 4 | `esoteric_point_yogi` | YOGI_POINT | 2 formula_id variants: `bphs_93_20`, `alt_96_40` |
| 5 | `esoteric_point_avayogi` | AVAYOGI_POINT | 2 formula_id variants matching Yogi |
| 6 | `esoteric_point_mrityu` | MRITYU_SPHUTA | 3 formula_id variants: `bphs_ch39`, `saravali`, `tajik_aapamrityu` |
| 7 | `esoteric_point_trisphuta` | TRISPHUTA | Lagna + Moon + Hora-lagna |
| 8 | `esoteric_point_chatushphuta` | CHATUSHPHUTA | Trisphuta + Sun |
| 9 | `esoteric_point_panchasphuta` | PANCHASPHUTA | 2 formula_id variants: `with_saturn`, `with_rahu` |
| 10 | `esoteric_point_pranapada_sphuta` | PRANAPADA_SPHUTA | distinct from Pranapada Lagna (A3 §lagna group) |
| 11 | `esoteric_point_trikona_dasha_sphuta` | TRIKONA_DASHA_SPHUTA | Jaimini alternate dasha-starting point |
| 12 | `esoteric_point_sri_yantra_position` | SRI_YANTRA_SUN, SRI_YANTRA_MOON, SRI_YANTRA_LAGNA | Tantric angular positions |
| 13 | `esoteric_point_brahma` | BRAHMA_POINT | Jaimini tri-deva |
| 14 | `esoteric_point_vishnu` | VISHNU_POINT | Jaimini |
| 15 | `esoteric_point_shiva` | SHIVA_POINT | Jaimini |
| 16 | `saham_position` | SAHAM_PUNYA ... SAHAM_APAMRITYU (70+ entries) | extended Hellenistic-Tajik catalogue per Q3=B |
| 17 | `karaka_chara_position` | ATMAKARAKA, AMATYAKARAKA, BHRATRIKARAKA, MATRIKARAKA, PUTRAKARAKA, GNATIKARAKA, DARAKARAKA, STRIKARAKA | 8-karaka system |
| 18 | `karakamsa_position` | KARAKAMSA | AK's D9 sign |
| 19 | `swamsa_position` | SWAMSA_HOUSE_1 ... SWAMSA_HOUSE_12 | 12 rows; map from karakamsa |
| 20 | `arudha_pada` | ARUDHA_A1 ... ARUDHA_A12 + ARUDHA_SU, ARUDHA_MO, ... ARUDHA_SA | 12 + 7 = 19 rows; aliases UL/GL/DP retained |
| 21 | `midpoint` | SUN-MARS, MOON-JUP, ASC-SAT, MC-VEN, ... | 36 graha-graha + 9 ASC-graha + 9 MC-graha = 54 |
| 22 | `kp_ruling_planets_natal` | RP_ASC_LORD, RP_ASC_SUB_LORD, RP_MOON_SIGN_LORD, RP_MOON_STAR_LORD, RP_DAY_LORD | 5 entries; foundational KP |
| 23 | `kp_cuspal_significators` | CUSP_1 ... CUSP_12 | 12 cusps × significator-array fields |
| 24 | `aprakasha_position` | DHWAJA, PATALA, KANDANGA, PIDAA, VIGHNI | 5 invisible grahas distinct from upagrahas |
| 25 | `tajik_hadda_lord` | HADDA_1 ... HADDA_60 (5 per sign × 12) | 5-fold sign division |
| 26 | `tajik_triraashipathi` | TRIRAASHIPATHI | Tajik year-lord |
| 27 | `tajik_vargottama_specific` | TAJIK_VARGOTTAMA | Tajik vargottama-specific calc |
| 28 | `lal_kitab_special_point` | PAKKA_GHAR, LAL_KITAB_ARUDHA_*, LAL_KITAB_GRAHA_HOUSE_* | uses G41 Lal Kitab corpus |
| 29 | `maharsi_specific_point` | VASISHTHA_SPHUTA, ATRI_SPHUTA, BHARADWAJA_SPHUTA, AGASTYA_SPHUTA, GAUTAMA_SPHUTA, KASHYAPA_SPHUTA, VISHWAMITRA_SPHUTA, etc. | per 27-Nadi-rishi tradition; correlates with G44 |
| 30 | `bhrigu_nadi_point` | BHRIGU_CHAKRA_*, BHRIGU_SPECIFIC_* | Bhrigu Nadi-specific positions beyond Bhrigu Bindu |

## §3 — Common row fields (universal — Section B locked)

Every A5 row carries the standard chart_facts shape PLUS these 6 enrichment fields:

```sql
-- A3 standard fields (recap)
longitude_sidereal     NUMERIC     -- in degrees (where applicable)
longitude_tropical     NUMERIC
sign                   TEXT
sign_lord              TEXT
nakshatra              TEXT
nakshatra_lord         TEXT
pada                   INT
kp_star_lord           TEXT
kp_sub_lord            TEXT
kp_sub_sub_lord        TEXT
nadiamsa_d150_lord     TEXT
nadiamsa_d150_rishi    TEXT
house_d1               INT
house_classification_d1 TEXT
formula_id             TEXT        -- which formula was used (links to classical citation)

-- A5 universal enrichments (Section B locked)
tolerance_arcsec                   NUMERIC     -- propagated orbital uncertainty
near_sign_boundary_flag            BOOLEAN     -- true if within 0°30' of sign edge
near_nakshatra_boundary_flag       BOOLEAN     -- true if within 0°48' of nakshatra edge
vargottama_flag_at_point           BOOLEAN     -- same sign in D1 + D9
formula_provenance_text            TEXT        -- classical-source-citation form
cross_ayanamsha_divergence_arcsec  NUMERIC     -- spread of this point across 5 ayanamshas (research signal)
```

Boundary flags + tolerance enable the LLM panel to caveat: "Note: this sensitive point sits 5′ from a sign boundary; ayanamsha choice flips its sign in 2 of 5 schools." That kind of surgical accuracy is the goal.

## §4 — Per-category two-pass verification methodology (Section C — declared in CHART_FACTS_SCHEMA.json per category)

| Category | Primary | Secondary | Match tolerance |
|---|---|---|---|
| `upagraha_position` | Swiss Ephemeris longitude derivation | Independent BPHS-formula classical re-derivation | ≤ 10″ |
| `saturn_derived_point` | Lahiri reckoning | Hindu reckoning emitted as separate `formula_id`; cross-formula divergence captured | Variance stored, not a halt-condition |
| `saham_position` | G14 library formula lookup | Direct-formula re-computation in engine; day/night-birth adjustment validated explicitly | ≤ 1″ |
| `karaka_chara_position` | Degree-sort with Rahu excluded (Parashari school) | Degree-sort with Rahu included (KN Rao school); BOTH emitted if Rahu position changes karaka order | Variance halts only if AK assignment differs |
| `esoteric_point_yogi` + `_avayogi` | BPHS 93°20' formula | Alternate 96°40' formula; both emitted as separate `formula_id` rows per Q5 | Variance always logged |
| `esoteric_point_panchasphuta` | Chatushphuta + Saturn | Chatushphuta + Rahu (both per Q6) | Variance always logged |
| `esoteric_point_mrityu` | BPHS Ch.39 formula | Saravali variant + Tajik Aapamrityu variant; 3 rows | Variance logged |
| `esoteric_point_trisphuta` family | Hora Lagna primary derivation | Hora Lagna independent re-derivation from sunrise + time | ≤ 1″ |
| `esoteric_point_brahma`/`vishnu`/`shiva` | Jaimini Sutram chapter formulas | Independent algebraic re-derivation | ≤ 30″ |
| `esoteric_point_sri_yantra_position` | Tantric angular mapping table | Re-projection from natal Sun longitude | ≤ 30″ |
| `esoteric_point_pranapada_sphuta` | Classical Moon-derived formula | Independent re-derivation from sunrise + Moon longitude | ≤ 30″ |
| `kp_ruling_planets_natal` | KP Reader formula | Independent re-derivation via star/sub-lord lookup tables | Exact match required |
| `kp_cuspal_significators` | KP Reader cuspal significator rules | Independent significator-graph traversal | Exact match required |
| `aprakasha_position` | Classical formula per Brihat Parashara Hora Shastra | Variant formula from Sage Parashara's Hora Shastra | ≤ 30″ |
| `tajik_hadda_lord` | Tajik Neelakanthi formula | Independent classical-table re-derivation | Exact (5-zone classification) |
| `tajik_triraashipathi` + `tajik_vargottama_specific` | Tajik Neelakanthi primary | Independent re-derivation | ≤ 1° |
| `lal_kitab_special_point` | Lal Kitab corpus formula | Independent re-derivation per Pandit Roop Chand's text | Exact match required |
| `maharsi_specific_point` | G44 Nadi-rishi lookup | Classical Nadi-text formula | Exact (rishi-assignment lookup) |
| `bhrigu_nadi_point` | Bhrigu Nadi formula | Cross-reference with Bhrigu Bindu position | ≤ 1′ |

Verification_pass_status set to:
- `two_pass_verified` if all checks pass
- `divergent_flagged` if any variance exceeds tolerance → halt build, escalate

## §5 — Citations (dual form per A3 §6)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Bhrigu Bindu (Lahiri) | `esoteric_point_bhrigu_bindu.BHRIGU_BINDU.longitude_sidereal@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Bhrigu Bindu at birth: 247°33′ in Sagittarius (Lahiri, ±2″)." |
| Punya Saham (KP) | `saham_position.SAHAM_PUNYA.sign@chart=362f9f17:ay=krishnamurti:eng=natal_engine/0.2.0` | "Punya Saham at birth: Capricorn (KP)." |
| Atmakaraka (Lahiri) | `karaka_chara_position.ATMAKARAKA.assigned_graha@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Atmakaraka: Sun (25°23′ in Capricorn, Lahiri)." |
| KP RP Asc Lord | `kp_ruling_planets_natal.RP_ASC_LORD.graha@chart=362f9f17:ay=krishnamurti:eng=natal_engine/0.2.0` | "KP Ruling Planet — Ascendant lord: Jupiter (KP)." |
| Upapada (Lahiri) | `arudha_pada.ARUDHA_A12.sign@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Upapada (A12) at birth: Pisces (Lahiri)." |
| Yogi 93°20' variant (Lahiri) | `esoteric_point_yogi.YOGI_POINT.longitude_sidereal@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` (formula_id=bphs_93_20) | "Yogi point (BPHS 93°20'): 198°45′ in Libra (Lahiri)." |
| Hadda lord (Lahiri) | `tajik_hadda_lord.HADDA_15.lord@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Hadda zone 15 lord: Mercury (Lahiri)." |
| Pakka Ghar Lal Kitab (Lahiri) | `lal_kitab_special_point.PAKKA_GHAR.house@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Pakka Ghar (Lal Kitab) for Sun: 5th house (Lahiri)." |

## §6 — Row count projection per (chart, ayanamsha)

| Group | ~Rows |
|---|---|
| Upagrahas (6 × 14 fields) | ~84 |
| Saturn-derived (5 × 14) | ~70 |
| Esoteric bindus (9 categories × ~14 keys, with formula variants doubling some) | ~180 |
| Sahams (70 × ~10) | ~700 |
| Karakas (8 × 9) | ~72 |
| Karakamsa + Swamsa (1 + 12 × 5) | ~65 |
| Arudhas (19 × 9) | ~170 |
| Midpoints (54 × 6) | ~325 |
| KP Ruling Planets (5 × 6) | ~30 |
| KP Cuspal Significators (12 × ~6 significator categories × ~5 graha entries) | ~360 |
| Aprakasha (5 × 14) | ~70 |
| Hadda (60 × 4) | ~240 |
| Triraashipathi + Vargottama-specific Tajik (2 × ~8) | ~16 |
| Lal Kitab special points (~10 × 6) | ~60 |
| Maharsi sphutas (~10 × 6) | ~60 |
| Bhrigu Nadi points (~8 × 8) | ~64 |
| Sri Yantra (3 × 4) | ~12 |
| Pranapada sphuta + Trikona dasha sphuta + Brahma/Vishnu/Shiva (5 × 14) | ~70 |

**Total A5 emission per (chart, ayanamsha): ~2,600 rows. × 5 ayanamshas = ~13,000 sensitive-point rows per chart.** Within Postgres comfort zone at internal scale.

## §7 — Materialized view

`mv_chart_sensitive_points_summary` — joins all A5 categories into one wide row per (chart, ayanamsha, point_subject) for fast "show me all my sensitive points" + "show me all Sahams" + "what's my Atmakaraka" type queries. Refreshed synchronously at build close.

## §8 — Tool retrieval contract

`query_sensitive_points(chart_id, ayanamsha_ids[], scope_filter=['all'\|'upagrahas'\|'sahams'\|'karakas'\|'arudhas'\|'kp_rp'\|'kp_cuspal'\|'tajik'\|'lal_kitab'\|'maharsi'\|'bhrigu_nadi'\|'esoteric'])` → rows.

For specific lookups: `query_sensitive_point(chart_id, ayanamsha_id, category, subject, key)` → 1 row.

## §9 — Implementation notes

1. Existing `natal_engine/sensitive_points.py` covers ~6 categories — A5 extends to all 30.
2. G14 Saham library extension from 50 → 70+ formulas is a global asset bump; do it before A5 writer can complete.
3. KP cuspal significators require house cusps + per-cusp star-lord lookup chain; engine extension needed.
4. Aprakasha grahas use BPHS-specific formulas; document each in code comments with chapter+verse.
5. Lal Kitab points consume G41 Lal Kitab corpus rules at writer time; pre-compile rules into a Python dict for performance.
6. Maharsi-specific points join with G44 Nadi-rishi attribution table at writer time.
7. Hadda 60-zone lookup table embedded as constant in engine (5 zones × 12 signs, with classical lord assignment).
8. Two-pass verification runs per category; on divergence, halt build with `verification_pass_status='divergent_flagged'` + diagnostic to CONDUCTOR_HALT_LOG.md.

## §10 — Locked decisions (final committed surface)

1. 30 fact_categories (14 baseline + 10 surgical-accuracy + 6 esoteric/Nadi/Tajik)
2. Universal Section B enrichment fields: tolerance_arcsec, near_sign_boundary_flag, near_nakshatra_boundary_flag, vargottama_flag_at_point, formula_provenance_text, cross_ayanamsha_divergence_arcsec
3. Per-category two-pass verification methodology declared in CHART_FACTS_SCHEMA.json
4. 8-karaka system (with school-variant Rahu inclusion/exclusion both emitted on order divergence)
5. Extended 70+ Saham catalogue
6. Yogi/Avayogi 2 formula variants (93°20' + 96°40')
7. Panchasphuta 2 formula variants (Saturn + Rahu)
8. Mrityu sphuta 3 formula variants (BPHS Ch.39 + Saravali + Tajik Aapamrityu)
9. `verification_pass_status='divergent_flagged'` halts build for in-tolerance violations
10. ~13,000 sensitive-point rows per chart total

A3 enum must be updated to include the new 16 categories (16-30 from §2). Adding to the running A3 enum count: was ~131, now ~147.

---

*End of A5_SENSITIVE_POINTS_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
