-- migration 491: kala_field_weight_versions + kala_field_weights + the `v0_classical` seed
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W2 ("the field as science") · Lane C.
-- Build spec: 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--             KALA_W2_FIELD_DESIGN_v1_0.md §7.5 (weights versioning + the
--             WEIGHTS-VERSION ACYCLICITY MECHANISM) and §9.3 row 476.
--
-- ── WHY THIS MIGRATION IS THE ACYCLICITY KEYSTONE (read before touching it) ───
-- `ka_kshetra` (L3) must read a FITTED weights version. `mi_bhara` (L5) FITS it.
-- The naive way to express that is `ka_kshetra.depends_on = [... 'mi_bhara']`,
-- which — combined with the necessary `mi_bhara.depends_on = ['ka_kshetra']` —
-- forms the cycle `ka_kshetra → mi_bhara → ka_kshetra`. `resolveBuildPlan`'s
-- topoSort rejects a cyclic plan, so that edge would break EVERY chart build,
-- not merely this wave's. (§7.5, stated exactly:
--   "The rule, stated exactly: `ka_kshetra` NEVER lists `mi_bhara` in depends_on.")
--
-- The loop closes ACROSS builds instead of AROUND the DAG, and THIS MIGRATION is
-- step 1 of the four that make that work:
--   1. weights v0 is seeded BY MIGRATION (here), not by a writer — so every
--      chart's very first `ka_kshetra` build finds an ACTIVE weights version and
--      there is no NULL-weights code path and no build order in which
--      `ka_kshetra` needs `mi_bhara` to have run. THIS MIGRATION MUST LAND
--      BEFORE `ka_kshetra` EVER RUNS.
--   2. `ka_kshetra` READS the newest active version (a DATA dependency, never a
--      build edge).
--   3. `mi_bhara` INSERTs a NEW version row (never UPDATEs an existing one —
--      weights are versioned artifacts; silent mutation is a drift failure).
--   4. the NEXT `ka_kshetra` rebuild pins the newer version.
--
-- ── WHAT THE SEEDED v0_classical VALUES ARE, AND WHAT THEY ARE NOT (B.10) ────
-- `v0_classical` is the STRUCTURAL PRIOR vector θ⁰ — the starting point of the
-- §7.2 shrinkage estimator, not an empirical claim. Every value below is a
-- STRUCTURAL choice made by the design document itself, and each is traceable:
--   • `w_s:<system>`  — the Law-2 proportional-hazards clock exponents. Seeded
--     from `bg_dasha_systems.seniority_rank` doctrine as a monotone ladder
--     (Vimśottarī the seniormost = 1.00), NOT from any fit. `w_s = 0` collapses
--     a clock's factor to exactly 1, which is why `naisargika` is seeded 0.0:
--     §5.1 rule C-4 makes `competence_class='life_stage'` NON-PREDICTIVE BY
--     CONSTRUCTION, not by fitting — the fitter is never given this parameter.
--   • `beta:x1..x12` — the twelve frozen log-linear covariate coefficients
--     (§5.1 C-5's table). Seeded at the classical sign of each covariate's
--     traditional effect with a deliberately SMALL magnitude (|β⁰| ≤ 0.40): a
--     structural prior must be weak enough that ~20 events of real data
--     (τ = 20, §7.2) can move it, and must never assert an effect size nobody
--     has measured. `moorti_tamra` is negative and `loha` is the reference
--     level with no dummy (§5.1 C-5 note).
--   • `rho:<vighna_class>` — MULTIPLICATIVE THINNING strengths (§5.1 C-6),
--     bounded [0, 0.95] BY THE MODEL so that S_e(t) ≥ 0.05^|vighna| > 0 and λ
--     is strictly positive by construction (the whole point of the Elevation §3
--     stage-4 amendment: suppression THINS, it never subtracts).
--   • `d:<level>` — the level-depth weights of §5.1 C-3's r_{s,e}(t)
--     (MD 1.0 · AD 0.7 · PD 0.5 · SD 0.3 · PrD 0.15), verbatim from the design.
-- `prior_value` on every row equals `weight_value` here BY DEFINITION: at v0 the
-- fitted value IS the prior (n_eff = 0 ⇒ φ̂ = φ⁰ exactly, §7.2 — the LEL-absent
-- scenario falling out of the shrinkage formula rather than being special-cased).
--
-- ── IDEMPOTENCY ──────────────────────────────────────────────────────────────
-- CREATE TABLE IF NOT EXISTS + ON CONFLICT DO NOTHING on the seed rows. DO
-- NOTHING (not DO UPDATE) is deliberate: re-running this migration must never
-- silently overwrite a weight value that a later `mi_bhara` release or a manual
-- correction changed — that is exactly the "silent weight mutation is a drift
-- failure" rail (§1 rail 8). A genuine change to v0 is a NEW version row.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_field_weight_versions (
  version_id            TEXT PRIMARY KEY,          -- 'v0_classical', 'v1_2026-08-14_abhisek', …
  status                TEXT NOT NULL CHECK (status IN ('active','superseded','rejected')),
  fitted_from_chart_id  UUID,                      -- NULL for v0_classical (global structural prior)
  scope                 TEXT NOT NULL CHECK (scope IN ('global','per_chart')),
  x_schema_version      TEXT NOT NULL,
  n_events_used         INT  NOT NULL DEFAULT 0,
  n_prospective_used    INT  NOT NULL DEFAULT 0,
  tau_shrinkage         DOUBLE PRECISION NOT NULL,
  any_clipped           BOOLEAN NOT NULL DEFAULT FALSE,
  fit_loglik            DOUBLE PRECISION,
  holdout_loglik        DOUBLE PRECISION,
  activated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes                 TEXT
);

CREATE TABLE IF NOT EXISTS kala_field_weights (
  version_id    TEXT NOT NULL REFERENCES kala_field_weight_versions(version_id),
  weight_id     TEXT NOT NULL,                     -- 'w_s:vimshottari' | 'beta:x4' | 'rho:vedha' | 'd:AD'
  weight_value  DOUBLE PRECISION NOT NULL,
  prior_value   DOUBLE PRECISION NOT NULL,         -- φ⁰
  n_eff         INT NOT NULL DEFAULT 0,
  clipped       BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (version_id, weight_id)
);

-- The §7.5 step-2 read is `WHERE status='active' ORDER BY activated_at DESC,
-- version_id DESC LIMIT 1` — index it so the pin resolution stays O(1) as
-- versions accumulate release by release.
CREATE INDEX IF NOT EXISTS idx_kala_field_weight_versions_active
  ON kala_field_weight_versions (status, activated_at DESC, version_id DESC);

CREATE INDEX IF NOT EXISTS idx_kala_field_weight_versions_chart
  ON kala_field_weight_versions (fitted_from_chart_id, scope, activated_at DESC);

COMMENT ON TABLE kala_field_weight_versions IS
  'ṢAḌ-DARŚANA W2 §7.5: versioned weight artifacts for the kala_field hazard '
  'model. THE ACYCLICITY KEYSTONE — v0_classical is seeded by THIS MIGRATION, '
  'never by a writer, so ka_kshetra (L3) never needs mi_bhara (L5) to have run '
  'and therefore never lists it in depends_on. Rows are INSERT-ONLY; a changed '
  'weight is a NEW version, never an UPDATE (silent mutation = drift failure).';

COMMENT ON COLUMN kala_field_weights.weight_value IS
  'The value ka_kshetra USES. At v0_classical this equals prior_value by '
  'definition (n_eff=0 ⇒ φ̂ = φ⁰ exactly, §7.2 shrinkage — the LEL-absent '
  'scenario falling out of the formula rather than being special-cased).';

-- ── v0_classical — the structural-prior version row ──────────────────────────

INSERT INTO kala_field_weight_versions (
  version_id, status, fitted_from_chart_id, scope, x_schema_version,
  n_events_used, n_prospective_used, tau_shrinkage, any_clipped,
  fit_loglik, holdout_loglik, notes
) VALUES (
  'v0_classical', 'active', NULL, 'global', 'x12_v0',
  0, 0, 20.0, FALSE,
  NULL, NULL,
  'Structural classical priors θ⁰ seeded by migration 491 (KALA_W2_FIELD_DESIGN '
  '§7.5 acyclicity keystone). NOT a fit: fit_loglik/holdout_loglik are honestly '
  'NULL because no fitting has occurred. n_events_used=0 ⇒ every parameter sits '
  'exactly at its prior under the §7.2 shrinkage estimator.'
) ON CONFLICT (version_id) DO NOTHING;

-- ── w_s — Law-2 clock exponents (§5.1 C-3) ───────────────────────────────────
-- naisargika is 0.0 BY CONSTRUCTION (rule C-4: competence_class='life_stage' is
-- declared NON-PREDICTIVE; its hazard factor is identically 1 and the fitter is
-- never given this parameter). Every other value is a seniority-ordered
-- structural prior, not a measurement.

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'w_s:vimshottari', 1.00, 1.00, 0, FALSE),
  ('v0_classical', 'w_s:yogini',      0.60, 0.60, 0, FALSE),
  ('v0_classical', 'w_s:kalachakra',  0.60, 0.60, 0, FALSE),
  ('v0_classical', 'w_s:chara',       0.60, 0.60, 0, FALSE),
  ('v0_classical', 'w_s:mudda',       0.40, 0.40, 0, FALSE),
  ('v0_classical', 'w_s:conditional', 0.40, 0.40, 0, FALSE),
  ('v0_classical', 'w_s:naisargika',  0.00, 0.00, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;

-- ── d — level depth weights (§5.1 C-3, verbatim from the design) ─────────────

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'd:MD',  1.00, 1.00, 0, FALSE),
  ('v0_classical', 'd:AD',  0.70, 0.70, 0, FALSE),
  ('v0_classical', 'd:PD',  0.50, 0.50, 0, FALSE),
  ('v0_classical', 'd:SD',  0.30, 0.30, 0, FALSE),
  ('v0_classical', 'd:PrD', 0.15, 0.15, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;

-- ── beta — the twelve FROZEN log-linear covariates (§5.1 C-5) ────────────────
-- x1  contact_moon_ref          x2  contact_lagna_ref
-- x3  dual_reference_agreement  x4  av_kaksha_gate
-- x5  moorti_svarna             x6  moorti_rajata
-- x7  moorti_tamra              x8  station_band
-- x9  sandhi_band               x10 syzygy_band
-- x11 eclipse_contact           x12 panchanga_affinity
-- Signs follow classical doctrine (svarṇa auspicious → tāmra inauspicious, with
-- loha as the un-dummied reference level); magnitudes are deliberately small so
-- ~20 real events can move them. Adding a THIRTEENTH covariate is a
-- weights-version-BREAKING change requiring a new x_schema_version (§7.3, §11.2).

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'beta:x1',   0.40,  0.40, 0, FALSE),
  ('v0_classical', 'beta:x2',   0.30,  0.30, 0, FALSE),
  ('v0_classical', 'beta:x3',   0.30,  0.30, 0, FALSE),
  ('v0_classical', 'beta:x4',   0.35,  0.35, 0, FALSE),
  ('v0_classical', 'beta:x5',   0.30,  0.30, 0, FALSE),
  ('v0_classical', 'beta:x6',   0.15,  0.15, 0, FALSE),
  ('v0_classical', 'beta:x7',  -0.20, -0.20, 0, FALSE),
  ('v0_classical', 'beta:x8',   0.20,  0.20, 0, FALSE),
  ('v0_classical', 'beta:x9',   0.25,  0.25, 0, FALSE),
  ('v0_classical', 'beta:x10',  0.15,  0.15, 0, FALSE),
  ('v0_classical', 'beta:x11',  0.20,  0.20, 0, FALSE),
  ('v0_classical', 'beta:x12',  0.10,  0.10, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;

-- ── rho — vighna (obstruction) thinning strengths (§5.1 C-6) ─────────────────
-- Bounded [0, 0.95] BY THE MODEL, not merely by the fitter's box constraint:
-- ρ_max = 0.95 is what guarantees S_e(t) ≥ 0.05^|vighna(e)| > 0, i.e. λ stays
-- STRICTLY POSITIVE however many obstructors fire. Suppression thins the
-- process; it never subtracts from it.

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'rho:vedha',        0.40, 0.40, 0, FALSE),
  ('v0_classical', 'rho:latta',        0.25, 0.25, 0, FALSE),
  ('v0_classical', 'rho:moorti_loha',  0.20, 0.20, 0, FALSE),
  ('v0_classical', 'rho:av_kaksha_low',0.30, 0.30, 0, FALSE),
  ('v0_classical', 'rho:default',      0.25, 0.25, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM kala_field_weights        WHERE version_id = 'v0_classical';
--   DELETE FROM kala_field_weight_versions WHERE version_id = 'v0_classical';
--   DROP TABLE IF EXISTS kala_field_weights;
--   DROP TABLE IF EXISTS kala_field_weight_versions;
--   COMMIT;
-- NOTE: dropping these tables makes every ka_kshetra build fail its weights-pin
-- resolution. That is CORRECT behaviour (§1 rail 8 — a field build PINS its
-- weights version; there is deliberately no unpinned code path), not a defect.
-- =============================================================================
