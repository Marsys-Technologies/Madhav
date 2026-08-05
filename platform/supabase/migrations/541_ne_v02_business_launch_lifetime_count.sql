-- Migration 541: ne_v02 corpus widening (Tranche-2) — `business_launch` N_e prior
--                into `brahma_class_priors` at the reserved lifetime-count coordinate.
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Tranche-2 N_e corpus widening.
-- Governing rulings (native, ratified 2026-08-06, interactive session, record-faithful):
--   R1 — scoreboard scope: baselines are per (chart × scope); first publication for a
--        scope is permanent FOR THAT SCOPE; later corpus versions (ne_v02…) EXTEND the
--        scoreboard as new scoped entries, never retroactively altering earlier ones.
--   R2 — Gate W2 closes SCOPED for the ne_v01-covered scope; non-vacuous 482012f1
--        re-verification is a named successor obligation bound to Tranche-2.
--   R3 — Tranche-2 widening DELEGATED, fully autonomous; native involvement waived by
--        the native directly. Quality rails preserved: real citable sources only,
--        recorded conversion assumptions, adversarial verification, honest attrition.
-- Source hierarchy in force: SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0 §ADJUDICATION-2
-- (Tier N-i / N-ii only; classical-text counts and cohort/LEL-derived counts FORECLOSED;
-- the CIRCULARITY GUARD holds — nothing here reads, or was selected by, the LEL).
--
-- ── SCOPE OF ne_v02, STATED HONESTLY ─────────────────────────────────────────
-- ne_v02 adds exactly ONE class: business_launch. Adversarial verification verdict:
-- CONFIRMED (independent re-fetch of the EDII GEM India 2023/24 PDF, the GEM 2023/2024
-- Global Report Annex Table A2, and the MOSPI 6th Economic Census Highlights; prod
-- re-query of bodha_pratijna for chart 482012f1 confirming business_launch is a
-- non-denied (conditional) class with zero overlap with the 6 ne_v01-covered classes).
--
-- Evaluated, not widened: none this tranche — no researched class was refused
-- (attrition list empty). HONEST COVERAGE NOTE, so absence cannot be read as
-- adjudication: the other 8 non-denied candidate classes for 482012f1
-- (career_advancement, career_change, career_entry, career_setback,
-- financial_deception, major_gain, major_loss, psychological_arc) were NOT evaluated
-- in this tranche (the candidate-class dispatch payload arrived truncated at its
-- first row; only business_launch was researched and verified). They remain Tier
-- N-iii `not_computed` — ka_kshetra keeps skipping each with `no_class_prior_row`,
-- the shippable honest-empty default, until a future tranche sources or refuses them.
--
-- ── WHY A PARTIAL ne_v02 ROW SET IS SAFE (verified before authoring) ─────────
-- `ka_kshetra.load_class_lifetime_count` (services/ka_kshetra/stage4_field.py) pins
-- the class (`signal_type_class = %s`) and takes `ORDER BY prior_version DESC …
-- LIMIT 1` PER CLASS. So business_launch resolves to ne_v02 while the six
-- ne_v01-covered classes keep resolving to ne_v01 — EXTEND semantics, exactly what
-- ruling R1 ratifies. Proven in tests/l3/ka_kshetra/test_stage4_field.py (the
-- version-precedence case asserts provenance `ne_v02|…` wins per class). The two
-- legacy consumers (`bo_laksana._load_class_priors`, `mi_kula._load_registry_priors`)
-- filter `prior_version='1.0'` and cannot see this row. The `bg_class_lifetime_counts`
-- writer upserts only at `prior_version='ne_v01'` and never deletes — a rebuild
-- cannot clobber this row. The live test in test_bg_class_lifetime_counts.py counts
-- rows at `prior_version='ne_v01'` only — unaffected.
--
-- ── VERSIONING ───────────────────────────────────────────────────────────────
-- `prior_version = 'ne_v02'` — ZERO-PADDED, mandatory (string sort; unpadded `ne_v10`
-- would sort below `ne_v2`). The corpus version marker IS the `prior_version` column —
-- the table carries no separate version column and none is invented here (the
-- codebase distinguishes N_e corpus versions by `prior_version` alone; it rides into
-- field provenance as `ne_v02|lifetime_count_per_100y|business_launch`).
--
-- ── IDEMPOTENCY (§N.3, L0) ───────────────────────────────────────────────────
-- Global reference data: INSERT … ON CONFLICT (PK) DO UPDATE, same as the ne_v01
-- seed path (`brahmagyan/l0_class_lifetime_counts.py`). Fully re-runnable.
-- Migration 522's columns (`prior_basis`, `source_ref`) and its CHECK
-- `brahma_class_priors_lifetime_basis_ck` precede this file in migration order; this
-- INSERT deliberately satisfies the CHECK the honest way (basis + source present) and
-- would fail LOUDLY, not silently, if 522 had not applied.
--
-- ── REVERSIBILITY: HIGH ──────────────────────────────────────────────────────
-- One row at one PK. See the DOWN block at the foot. Retraction convention per the
-- ne_v01 module docstring: a retraction is a new corpus version without the row —
-- but since ne_v02 is this single row, the DOWN delete reverts business_launch to
-- honest-skip automatically.
-- =============================================================================

BEGIN;

-- ── ne_v02 · business_launch ─────────────────────────────────────────────────
-- Tier: N-i (prior_basis='demographic_structural'), with the tier caveat recorded
-- verbatim in `citation` (single-year APS N=3,005 pushes toward the N-i/N-ii
-- boundary; GEM is the standard international survey programme but not official
-- statistics; cross-checked against MOSPI official statistics on an establishment
-- basis). Value: N_e = 0.124 per 100y (first-launch prevalence convention).
-- Uncertainty range [0.085, 0.25] recorded in `citation` (the table carries no
-- uncertainty column; the range and its construction are part of the audit string,
-- as with the ne_v01 rows' sensitivity notes).

INSERT INTO brahma_class_priors
  (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition,
   class_prior, prior_basis, source_ref, citation, ratified_by)
VALUES
  ('ne_v02', 'business_launch', 'lifetime_count_per_100y', '*', '*',
   0.124,
   'demographic_structural',
   -- source_ref: the six Tier N-i citation elements, in the ruling''s own order
   -- (publisher · edition/survey round · year · indicator/table id · geography+cohort
   -- · retrievable URL), composed exactly as compose_source_ref() composes the
   -- ne_v01 rows.
   'GEM India Team (Lead Institution: Entrepreneurship Development Institute of '
   'India (EDII), Ahmedabad; National Team Leader Prof. Sunil Shukla; fieldwork by '
   'Kantar India) · Global Entrepreneurship Monitor India Report 2023/24 (Routledge, '
   '2025; authors Shukla/Bharti/Dwivedi) · 2024 (Adult Population Survey fieldwork '
   '2023-24; PDF published 2025) · Table 3.1 ''GEM India snapshot'', row ''The '
   'established business ownership rate (EBO) 2023-24'' = 12.4 (rank 7/46); '
   'operational definitions in the report''s §2.5; trend Figure 5.1 ''Trends of TEA '
   'and EBO in India'': EBO 11.9 (2019-20), 8.5 (2021-22), 12.4 (2023-24) · India '
   '(national); adults 18-64; GEM Adult Population Survey N=3,005, 2023-24 · '
   'https://ediindia.org/wp-content/uploads/2025/04/GEM_2023-24-1.pdf',
   -- citation: raw figure | inclusion criteria | conversion — compose_citation() format.
   'raw_figure: Established Business Ownership rate (EBO) 2023-24 = 12.4% of adults '
   '18-64 currently owner-manager of a business that has paid salaries/wages or any '
   'payments to owners for MORE THAN 42 MONTHS (GEM India Report §2.5 definition, '
   'verbatim discriminator). Companion rates same table: TEA 2023-24 = 12.0 (rank '
   '22/46), TEA 2022-23 = 11.5, TEA 2021-22 = 14.4. CORROBORATION (same APS, '
   'independent publication): GEM 2023/2024 Global Report ''25 Years and Growing'', '
   'Annex Table A2 ''Entrepreneurial activity (% of adults aged 18-64)'', row India: '
   'TEA 12.0 (rank 22), EBO 12.4 (rank 7) — https://www.gemconsortium.org/report/'
   'global-entrepreneurship-monitor-gem-20232024-global-report-25-years-and-growing '
   '(mirror verified: https://nyforetagarcentrum.se/wp-content/uploads/2024/05/'
   'gem-global-report-2023-2024-1707774434-2.pdf). CROSS-CHECK on a different '
   'definition (official statistics, establishment basis): MOSPI, Government of '
   'India, ''Highlights of the Sixth Economic Census'' — 58.5 million establishments '
   '(41.97M / 71.74% own-account; 16.53M / 28.26% with >=1 hired worker); against '
   'Census 2011 population 1,210,854,977 that is 4.83 establishments per 100 persons '
   '(all ages) — same order of magnitude as ~12% adult owner-prevalence once '
   'co-ownership, multi-establishment owners, the EC''s exclusion of crop production '
   'and the all-age vs 18-64 denominator are accounted — https://www.mospi.gov.in/'
   'sites/default/files/economic-census/sixth_economic_census/all_india/'
   '5_Highlights_6ecRep.pdf '
   '| inclusion_criteria: class restricted to FIRST business launch, making it '
   'at-most-once BY CONSTRUCTION (mirrors the ne_v01 marriage/relocation/separation '
   'first-event convention) -> N_e = p, never > 1. EBO proxies p: the >42-month '
   'payment history is the durability discriminator standing in for the class''s '
   '''significant'' magnitude_floor — analogous to the anaesthesia discriminator in '
   'the ne_v01 surgery row. Nascent entrepreneurs (actively starting, no payments '
   '>3 months) deliberately EXCLUDED — a nascent attempt is not yet a launch; '
   'conservative by construction. New Business Owners (payments 3-42 months) are '
   'genuine launches but EXCLUDED because neither the GEM India 2023/24 report nor '
   'the GEM 2023/24 Global Report annex publishes India''s nascent/NBO split — '
   'disclosed undercount, direction down. Point-prevalence-as-lifetime-prevalence: '
   'EBO is a stock among adults 18-64, not a completed-cohort lifetime-ever measure; '
   'exited founders are not counted (discontinuation is a separate GEM flow) and '
   'younger adults have not yet launched — both push p down for a completed '
   '1955-1985 cohort; India publishes no ''ever started a business'' lifetime '
   'statistic (structurally unmeasured, as with relocation''s repeat-move count). '
   'Repeat launches unmeasured: E[count|>=1] unpublished for India — N_e is '
   'per-FIRST-launch and a LOWER BOUND on total launch events. THREE DISCLOSED '
   'OVERCOUNT channels prevent labelling the row a strict lower bound: (1) '
   'OWNERSHIP vs LAUNCH-EVENT — EBO counts current owner-managers including '
   'inherited/family-succession ownership without a personal launch event (the '
   'report''s own motivation table reports ''continue family tradition'' = 75.2% of '
   'TEA; report prose frames it as a youth-cohort motivation — noted, immaterial to '
   'the value); (2) NO SIZE FLOOR — includes micro/subsistence own-account '
   'businesses (cf. 6th EC: 71.74% of establishments have zero hired workers), '
   'possibly below the class''s ''significant'' floor as the jyotish signature '
   '(7/10/11 lords, D10, Mercury/Jupiter karakas) frames it; a stricter ''employer'' '
   'reading would be several-fold smaller but no person-level lifetime employer '
   'statistic exists for India; (3) CO-OWNERS each count as owner-managers. Net '
   'direction of overcounts vs undercounts UNKNOWN — served as a best-available '
   'point estimate with a deliberately wide uncertainty range [0.085, 0.25]: lower '
   'bound = India''s own COVID-trough EBO (8.5%, 2021-22, same instrument); upper '
   'bound = current TEA+EBO stacking (12.0 + 12.4 = 24.4%), the ceiling a '
   'completed-cohort ever-launched prevalence could plausibly approach (verification '
   'note: the tighter defensible upper bound is 0.244; 0.25 is the rounded judgment '
   'ceiling). SOURCE QUALITY TIER: N-i/N-ii boundary — GEM is the standard '
   'international survey programme for person-level business founding (25 years, 46 '
   'economies, consortium incl. London Business School/Babson; India team led by '
   'EDII, a Government-of-India-promoted national institute); caveat pushing toward '
   'N-ii: single-year APS sample N=3,005, so sampling error on a 12.4% point '
   'estimate is material (~±1.2pp at 95%), and GEM is not official statistics; '
   'cross-checked against official statistics (MOSPI 6th Economic Census) on an '
   'establishment basis. INDIA ADJUSTMENT: none needed — source fully '
   'India-specific (GEM India APS, national sample); no western-cohort import, no '
   'cultural-variance adjustment applied or required; era caveat disclosed rather '
   'than adjusted: the native cohort (b. 1984) lived its prime launch years '
   '2005-2025, within which the same instrument measured EBO 8.5-12.4 and TEA '
   '11.5-15.0 — the uncertainty range spans this. '
   '| conversion: CONVENTION — first-launch restriction makes the class '
   'at-most-once -> N_e = p, never > 1. NO annual-rate scaling: EBO is a '
   'PREVALENCE, not an incidence, so the per-person-year rule N_e = 100*r does NOT '
   'apply. p = EBO 2023-24 = 12.4% -> N_e = 0.124 (3 s.f., exact). Flat-over-'
   'horizon per the ruling''s lambda-zero convention (100-year horizon assuming '
   'survival); the ontology''s own base_rate_by_age handles within-life age-shaping '
   'downstream. Verified: independent two-pass adversarial re-derivation CONFIRMED '
   '(all cited figures re-fetched verbatim from the primary PDF, the Global Report '
   'annex mirror, and the MOSPI Highlights; arithmetic exact; nascent/NBO-split '
   'absence spot-checked in both fetched documents).',
   'SHAD_DARSHANA native rulings 2026-08-06 (R3 Tranche-2 delegation, '
   'native-autonomy waived by the native directly) · '
   'SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0 §ADJUDICATION-2 source hierarchy · '
   'adversarial verification verdict: CONFIRMED')
ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
DO UPDATE SET class_prior = EXCLUDED.class_prior,
              prior_basis = EXCLUDED.prior_basis,
              source_ref  = EXCLUDED.source_ref,
              citation    = EXCLUDED.citation,
              ratified_by = EXCLUDED.ratified_by;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM brahma_class_priors
--    WHERE prior_version = 'ne_v02'
--      AND signal_type_class = 'business_launch'
--      AND fact_kind = 'lifetime_count_per_100y'
--      AND source_subsystem = '*'
--      AND signal_tradition = '*';
--   COMMIT;
-- business_launch reverts to honest-skip (`no_class_prior_row`) automatically;
-- nothing at ne_v01 or prior_version='1.0' is touched in either direction.
-- =============================================================================
