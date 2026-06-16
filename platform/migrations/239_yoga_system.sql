-- Migration 239: Yoga system — family taxonomy, interaction rules, catalog extensions
-- Yoga Subsystem Gate-1 — 2026-06-17

-- 1. yoga_families: hierarchical family taxonomy
CREATE TABLE IF NOT EXISTS yoga_families (
    id SERIAL PRIMARY KEY,
    family_id TEXT NOT NULL UNIQUE,
    parent_family_id TEXT REFERENCES yoga_families(family_id),
    name_en TEXT NOT NULL,
    name_sa TEXT,
    description TEXT,
    classical_citation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. yoga_family_members: many-to-many yoga ↔ family
CREATE TABLE IF NOT EXISTS yoga_family_members (
    yoga_canonical_id TEXT NOT NULL,
    family_id TEXT NOT NULL REFERENCES yoga_families(family_id),
    PRIMARY KEY (yoga_canonical_id, family_id)
);

-- 3. yoga_interaction_rules: how yogas modulate each other
CREATE TABLE IF NOT EXISTS yoga_interaction_rules (
    id SERIAL PRIMARY KEY,
    primary_yoga_id TEXT NOT NULL,
    secondary_yoga_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('strengthens','weakens','cancels','supersedes','compounds')),
    condition_text TEXT NOT NULL,
    classical_citation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Extend brahma_yoga_catalog with new columns (if not already present)
ALTER TABLE brahma_yoga_catalog
    ADD COLUMN IF NOT EXISTS bhanga_rules_jsonb JSONB,
    ADD COLUMN IF NOT EXISTS partial_formation_threshold NUMERIC,
    ADD COLUMN IF NOT EXISTS strength_formula_ref TEXT,
    ADD COLUMN IF NOT EXISTS result_class TEXT CHECK (result_class IN ('benefic','malefic','mixed','neutral'));
