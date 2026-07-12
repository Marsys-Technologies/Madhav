# LANE10 — Promise-vs-Delivery — shard-1 (7 L1 ga_* assets)

Charter §7.5 decision tree. Charts: PRIMARY `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek),
SECONDARY `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan). Retrieval via DEPLOYED MCP channel
(amjis-mcp Cloud Run). Status: COMPLETE (7/7 graded).

## Data-plane counts (both charts, DB SELECT via count_sql predicates)

| asset | table | count_sql cats | 482012f1 | 1c826d5a | target_floor |
|---|---|---|---|---|---|
| ga_sade_sati | chart_facts (15 cats) | sade_sati_* + shani periods | 6287 | 6280 | 11019 |
| ga_sensitive | chart_facts (upagraha/saham/kp/tajik/…) | — | 8565 | 8565 | 8610 |
| ga_strength | chart_facts (shadbala/av/vimsopaka) | — | 12046 | 12046 | 11936 |
| ga_structural | chart_facts JOIN fact_category_ownership | owning=ga_structural | 98554 | 98674 | 77821 |
| ga_tajaka | l1_tajik_varsha_year_lords | — | 240 | 235 | 240 |
| ga_transit_anchors | ga_transit_anchors | — | 45 | 45 | 45 |
| ga_vargas | chart_divisionals | — | 21992 | 21992 | 20877 |

All 7 data-plane PRESENT on both charts. Floors are aspirational-not-gates (CLAUDE.md §N.4);
ga_sade_sati sits ~57% of its floor and ga_sensitive ~99.5% — noted, not a shortfall by itself.

## Retrieval-plane (DEPLOYED channel) — fronting tool per asset

- ga_sade_sati → `ganita_sade_sati_get` : LEN 34877, envelope v1, all 15 categories, real rows. REACHABLE.
- ga_strength → `ganita_strength_get` : LEN 31659, shadbala+vimsopaka+ishta/kashta+bhava rows. REACHABLE.
- ga_structural → `ganita_structural_get` (facet-parameterized, 10 facets enumerated in schema;
  facet=aspects → LEN 24500, aspect_parashari/jaimini/tajik rows). REACHABLE.
- ga_tajaka → `ganita_tajaka_get` : structuredContent large payload, tajik_hadda_lord/triraashipathi
  two_pass_verified rows. REACHABLE.
- ga_transit_anchors → `ganita_transit_anchors_get` : LEN 11710, 45 anchors (natal_sign/house_from_moon/
  degree_absolute × 5 ayanamsha × 9 graha). REACHABLE.
- ga_vargas → NO dedicated tool; `query_chart_facts` advertises "divisional charts"; pivoted planet=Moon
  returns D1..D2700 keys (LEN 121770). REACHABLE + advertised.
- ga_sensitive → NO dedicated tool. Reachable ONLY via generic `query_chart_facts` by EXACT
  fact_category string (kp_cuspal_significators→60 rows, saham_position→100, esoteric_point_yogi→14,
  lal_kitab_special_point→20, upagraha_position→rows). keyword="kp" → returned_count 0.
  query_chart_facts description lists "planet positions, dignities, strengths, house placements,
  divisional charts, yogas, doshas, and more" — does NOT name upagraha/saham/KP/tajik/nadi/lal-kitab.
  Discovery requires prior knowledge of internal category strings not implied by any tool description.

## Verdicts

- AP-008 ga_sade_sati — DELIVERS (data+retrieval+form clear; modest promise met).
- AP-009 ga_sensitive — PARTIAL, shortfall=retrieval-plane. Data present, no fronting tool, families
  named in the promise (KP/Tajik/Nadi/Lal Kitab/esoteric) reachable only by guessing exact category
  strings. Finding: class 1 (effectively unreachable/undiscoverable) + class 9 (undocumented sequence).
- AP-010 ga_strength — DELIVERS.
- AP-011 ga_structural — DELIVERS (EXHAUSTIVE-ENUMERATION promise; 98k rows > floor; all 10 facets serve).
- AP-012 ga_tajaka — DELIVERS.
- AP-013 ga_transit_anchors — DELIVERS, promise re-sourced (no build brief exists; promise declared by
  asset_registry english_description + MCP tool description → 2 of 4 sources; NOT undeclared).
- AP-014 ga_vargas — DELIVERS (no dedicated tool but reachable + explicitly advertised as "divisional charts").
