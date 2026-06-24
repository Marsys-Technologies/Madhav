-- Migration 330: Add variant_traditions JSONB column to bg_dignity_reference
--
-- Purpose: Implements the SOURCE-AUTHORITY-WEIGHTED disclosure model for
-- classical positions where one dominant text (BPHS) provides the canonical value
-- and minority traditions document alternative positions.
--
-- The exaltation_sign column remains the BPHS-authoritative canonical value at
-- full confidence. variant_traditions carries structured disclosure of alternatives
-- with explicit authority tagging ('primary' vs 'minority') and source citations.
--
-- Currently populated for Rahu and Ketu only (the only grahas with documented
-- tradition disagreement on exaltation sign). Rahu=Taurus, Ketu=Scorpio = BPHS
-- primary; Gemini/Sagittarius = minority Kerala school; null = exclusionist minority.
--
-- The bg_dignity_reference writer (bg_dignity_reference.py) populates this column
-- via its ON CONFLICT DO UPDATE upsert on writer rebuild.
--
-- Supersedes: prior "reduce-confidence" interim approach (where minority positions
-- were treated as confidence-diluters on the BPHS value — incorrect for this model).

BEGIN;

ALTER TABLE bg_dignity_reference
    ADD COLUMN IF NOT EXISTS variant_traditions JSONB DEFAULT NULL;

COMMIT;
