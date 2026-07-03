-- Migration 394: bodha_cgm_edges typed edge columns — BA-P3B Step 4
-- Adds valence / relationship_basis / affected_domains to bodha_cgm_edges.
-- Written by bo_karanajala via _typed_edge_fields(); consumed by P4 verdict assembly.

BEGIN;

ALTER TABLE bodha_cgm_edges
    ADD COLUMN IF NOT EXISTS valence             TEXT
        CHECK (valence IN ('harmonious', 'antagonistic', 'neutral')),
    ADD COLUMN IF NOT EXISTS relationship_basis  TEXT,
    ADD COLUMN IF NOT EXISTS affected_domains    TEXT[];

COMMENT ON COLUMN bodha_cgm_edges.valence IS
  'Edge polarity: harmonious | antagonistic | neutral. '
  'Set by bo_karanajala._typed_edge_fields() per edge_type at build time. '
  'argala_virodha overrides the default harmonious to antagonistic.';

COMMENT ON COLUMN bodha_cgm_edges.relationship_basis IS
  'Classical rule basis for this edge type: yoga_activation, dosha_impairment, '
  'parashari_aspect, planetary_conjunction, sign_lordship, argala_intervention, sade_sati_transit.';

COMMENT ON COLUMN bodha_cgm_edges.affected_domains IS
  'Domains this edge propagates influence to (mirrors domains_affected_array of the source signal). '
  'NULL for graha→graha edges that are domain-independent.';

COMMIT;
