-- K0a-2: stage-3 clock rows are keyed by L1's canonical system identifiers.
-- Migration 491's historical 'chara' and 'conditional' keys remain immutable;
-- these additive v0 rows are the keys the serving hazard actually reads.

INSERT INTO kala_field_weights (version_id, weight_id, weight_value, prior_value, n_eff, clipped) VALUES
  ('v0_classical', 'w_s:chara_karaka',  0.60, 0.60, 0, FALSE),
  ('v0_classical', 'w_s:ashtottari',    0.40, 0.40, 0, FALSE),
  ('v0_classical', 'w_s:vimshottari_kp', 0.40, 0.40, 0, FALSE)
ON CONFLICT (version_id, weight_id) DO NOTHING;
