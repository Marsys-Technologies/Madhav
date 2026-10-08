-- K0a-2: stage-3 clock rows are keyed by L1's canonical system identifiers.
-- Migration 491's historical 'chara' key is the governed structural prior for
-- Cara (491 §w_s, Law-2 C-3). The Stage-3 canonical identifier is
-- 'chara_karaka', so this additive alias preserves that declared 0.60 prior
-- without editing the applied historical seed. Aṣṭottarī and vimshottari_kp
-- remain unseeded: F-A3 does not permit inferring an independent KP weight.

-- Some historical databases carry the 491 tables but not its v0 row.  Preserve
-- 491's governed structural prior verbatim in that recovery case so this
-- additive alias is FK-safe on a replay; an existing version is never changed.
INSERT INTO kala_field_weight_versions (
  version_id, status, fitted_from_chart_id, scope, x_schema_version,
  n_events_used, n_prospective_used, tau_shrinkage, any_clipped,
  fit_loglik, holdout_loglik, notes
) VALUES (
  'v0_classical', 'active', NULL, 'global', 'x12_v0',
  0, 0, 20.0, FALSE,
  NULL, NULL,
  'Structural classical priors theta0 seeded by migration 491; restored only when the historical version row is absent.'
)
ON CONFLICT (version_id) DO NOTHING;

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'w_s:chara_karaka', 0.60, 0.60, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;
