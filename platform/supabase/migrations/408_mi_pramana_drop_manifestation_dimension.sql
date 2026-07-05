-- Migration 408: JL-018 (BA Phase 2.5 J8) — drop mi_pramana's manifestation
-- scoring dimension; renormalize remaining 4 weights; register the drop.
--
-- _score_manifestation() in mi_pramana.py has no real scorer behind it
-- (hardcoded 0.5/None for every match — B.10 forbids fabricating one to keep
-- 5 dimensions). Updates 'mi_pramana_scoring_weights' to the 4 remaining
-- weights, proportionally renormalized to sum to 1.0. Adds
-- 'mi_pramana_dropped_dimensions' documenting the drop so a future P6 pass
-- (MIMAMSA_V2 S4) knows to re-add it once a real scorer exists.
--
-- score_manifestation remains a NOT NULL column (migration 348) and is still
-- written by the writer — only its weight is removed from the composite.
--
-- mi_pariksha_attribution_weights is documented as "must mirror
-- mi_pramana_scoring_weights sum=1.0" (migration 400) but is intentionally
-- NOT touched here — mi_pariksha's own attribution-credit use of the
-- manifestation dimension is a separate code path (out of scope for J8,
-- which names mi_pramana specifically) and is flagged below as a known,
-- deliberate divergence pending a symmetric follow-up.

BEGIN;

DO $$
BEGIN
    UPDATE brahma_formula_constants
    SET value_jsonb = '{"timing":0.333333,"magnitude":0.222222,"domain":0.277778,"falsifier":0.166667}',
        citation_or_ratification =
          'BA-P6 C6 weight unification: mi_pramana scoring dimension weights retired from inline code to registry. '
          'Sum must = 1.0. L5-calibratable within bounds. '
          'JL-018 (2026-07-05): manifestation dimension dropped (no real scorer '
          'existed behind it — see mi_pramana_dropped_dimensions); remaining 4 '
          'weights proportionally renormalized to sum=1.0.',
        bounds = '{"timing":[0.22,0.44],"magnitude":[0.15,0.33],"domain":[0.18,0.39],"falsifier":[0.06,0.28]}',
        version = '2.0'
    WHERE constant_id = 'mi_pramana_scoring_weights';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'migration 408: mi_pramana_scoring_weights row not found in brahma_formula_constants — expected to be seeded by migration 400';
    END IF;
END $$;

INSERT INTO brahma_formula_constants
  (constant_id, value_jsonb, class, consumer_assets, citation_or_ratification, calibratable, bounds, version)
VALUES
  ('mi_pramana_dropped_dimensions',
    '{"manifestation":{"dropped_at":"2026-07-05","reason":"_score_manifestation() hardcoded (0.5, None) for every match — no real scorer, B.10 forbids fabricating one","original_weight":0.10,"re_add_target":"MIMAMSA_V2 S4","judgment_ledger_entry":"JL-018"}}',
    'engineering',
    ARRAY['mi_pramana'],
    'JL-018 (BA Phase 2.5 J8): registry of dimensions dropped from mi_pramana''s '
    'composite scoring so a future pass (MIMAMSA_V2 S4) knows what to re-add and why.',
    false,
    NULL,
    '1.0')
ON CONFLICT (constant_id)
DO UPDATE SET
    value_jsonb              = EXCLUDED.value_jsonb,
    consumer_assets          = EXCLUDED.consumer_assets,
    citation_or_ratification = EXCLUDED.citation_or_ratification,
    calibratable             = EXCLUDED.calibratable,
    bounds                   = EXCLUDED.bounds,
    version                  = EXCLUDED.version;

COMMIT;
