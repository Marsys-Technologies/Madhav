-- Migration 363: change phala_anchors.convergence_id FK from ON DELETE SET NULL
-- to ON DELETE CASCADE.
--
-- Rationale: when kala_convergence rows are deleted during L3 (Kāla) rebuild,
-- the SET NULL cascade accumulated NULL convergence_id rows that violated the
-- phala_anchors_natural_key unique index (COALESCE(convergence_id,-1) colliding).
-- CASCADE deletes the phala_anchors rows derived from that convergence instead of
-- NULLing them — architecturally correct (L4 rows derived from a deleted L3
-- convergence are stale; L4 rebuild regenerates them from the new L3 data).
-- This also preserves the layer-separation invariant: ka_sangam (L3) never needs
-- to explicitly touch phala_* (L4) tables.

ALTER TABLE phala_anchors
    DROP CONSTRAINT IF EXISTS phala_anchors_convergence_id_fkey;

ALTER TABLE phala_anchors
    ADD CONSTRAINT phala_anchors_convergence_id_fkey
    FOREIGN KEY (convergence_id)
    REFERENCES kala_convergence(convergence_id)
    ON DELETE CASCADE;
