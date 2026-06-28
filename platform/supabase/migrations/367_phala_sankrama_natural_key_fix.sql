-- Migration 367: fix phala_sankrama natural key — add cdlm_cell_id to unique constraint.
--
-- Problem: the old index (chart_id, source_anchor_id, target_domain, relationship_type)
-- collapses all rows from different CDLM cells that share the same
-- (anchor, target_domain, relationship_type) triple to the first one seen.
-- When the same anchor has multiple CDLM cells linking it to the same target domain
-- via distinct bridge paths, ON CONFLICT silently drops all but the first.
--
-- Fix: include cdlm_cell_id so each distinct CDLM cell produces its own row.
-- The natural unit of a spillover is one anchor × one CDLM cell × one target × one relationship.
--
-- Note: this uses ALTER TABLE ADD CONSTRAINT (not CREATE UNIQUE INDEX) so that the
-- writer's ON CONFLICT ON CONSTRAINT phala_sankrama_natural_key clause is honoured.
-- PostgreSQL only resolves ON CONFLICT ON CONSTRAINT for named constraints, not bare indexes.

DROP INDEX IF EXISTS phala_sankrama_natural_key;

ALTER TABLE phala_sankrama
    DROP CONSTRAINT IF EXISTS phala_sankrama_natural_key;

ALTER TABLE phala_sankrama
    ADD CONSTRAINT phala_sankrama_natural_key
    UNIQUE (chart_id, source_anchor_id, cdlm_cell_id, target_domain, relationship_type);
