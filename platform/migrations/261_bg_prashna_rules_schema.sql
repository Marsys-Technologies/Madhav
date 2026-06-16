-- Migration 261: Prashna (Horary) static rule tables — L0 Brahmagyan layer
-- These tables are chart-agnostic static reference data only.
-- No per-chart computation at this layer.

-- Prashna Lagna derivation methods
CREATE TABLE IF NOT EXISTS bg_prashna_lagna_methods (
    id SERIAL PRIMARY KEY,
    method_id TEXT NOT NULL UNIQUE,
    method_name TEXT NOT NULL,
    method_name_sa TEXT,
    derivation_rule TEXT NOT NULL,
    derivation_rule_jsonb JSONB,
    classical_citation TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    tradition TEXT NOT NULL CHECK (tradition IN ('tajika','kp','parashari','prashna_marga','swara'))
);

-- Tajik horary yoga set
CREATE TABLE IF NOT EXISTS bg_prashna_tajik_yogas (
    id SERIAL PRIMARY KEY,
    yoga_id TEXT NOT NULL UNIQUE,
    yoga_name TEXT NOT NULL,
    yoga_name_sa TEXT,
    judgment_meaning TEXT NOT NULL,
    formation_rule TEXT NOT NULL,
    formation_rule_jsonb JSONB,
    classical_citation TEXT NOT NULL,
    is_fructification_indicator BOOLEAN DEFAULT FALSE
);

-- Significator derivation rules
CREATE TABLE IF NOT EXISTS bg_prashna_significators (
    id SERIAL PRIMARY KEY,
    question_class TEXT NOT NULL,
    querent_house INTEGER,
    querent_planet TEXT,
    quesited_house INTEGER NOT NULL,
    quesited_planet TEXT,
    significator_rule TEXT NOT NULL,
    classical_citation TEXT NOT NULL,
    UNIQUE (question_class)
);

-- Fructification timing rules
CREATE TABLE IF NOT EXISTS bg_prashna_fructification_rules (
    id SERIAL PRIMARY KEY,
    rule_id TEXT NOT NULL UNIQUE,
    time_unit TEXT NOT NULL CHECK (time_unit IN ('hours','days','weeks','months','years')),
    degree_conversion_rule TEXT NOT NULL,
    applicable_when TEXT NOT NULL,
    classical_citation TEXT NOT NULL
);

-- Special prashna techniques
CREATE TABLE IF NOT EXISTS bg_prashna_special_techniques (
    id SERIAL PRIMARY KEY,
    technique_id TEXT NOT NULL UNIQUE,
    technique_name TEXT NOT NULL,
    technique_name_sa TEXT,
    application_rule TEXT NOT NULL,
    classical_citation TEXT NOT NULL
);
