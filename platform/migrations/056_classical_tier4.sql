-- Migration 056: Add tier 4 (Nadi/BNN) to classical_texts tier constraint.
-- M8-F-S1: Nadi + BNN texts use tier = 4.

ALTER TABLE classical_texts DROP CONSTRAINT IF EXISTS classical_texts_tier_check;
ALTER TABLE classical_texts ADD CONSTRAINT classical_texts_tier_check CHECK (tier IN (1, 2, 3, 4));
COMMENT ON COLUMN classical_texts.tier IS '1=mandatory, 2=high priority, 3=standard priority, 4=nadi/bnn';
