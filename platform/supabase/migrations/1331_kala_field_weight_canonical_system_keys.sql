-- K0a-2: stage-3 clock rows are keyed by L1's canonical system identifiers.
-- Migration 491's historical 'chara' key is the governed structural prior for
-- Cara (491 §w_s, Law-2 C-3). The Stage-3 canonical identifier is
-- 'chara_karaka', so this additive alias preserves that declared 0.60 prior
-- without editing the applied historical seed. Aṣṭottarī and vimshottari_kp
-- remain unseeded: F-A3 does not permit inferring an independent KP weight.

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'w_s:chara_karaka', 0.60, 0.60, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;
