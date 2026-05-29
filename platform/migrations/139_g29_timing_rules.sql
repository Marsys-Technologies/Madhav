-- Migration 139: G29 Classical Timing Rule Catalog
-- Stream C [BUILD-ORCH-STREAM-C-G29-S1]

CREATE TABLE IF NOT EXISTS g29_timing_rules (
    rule_id              TEXT        PRIMARY KEY,
    source_text          TEXT        NOT NULL,
    rule_category        TEXT        NOT NULL,
    timing_system        TEXT        NOT NULL,
    trigger_predicate    TEXT        NOT NULL,
    predicted_outcome    TEXT        NOT NULL,
    activation_window    TEXT        NOT NULL,
    strength_qualifier   TEXT        NOT NULL DEFAULT 'moderate',
    classical_citation   TEXT,
    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Constraint: source_text must be a known classical text
ALTER TABLE g29_timing_rules
    ADD CONSTRAINT g29_source_check
    CHECK (source_text IN (
        'bphs','phaladeepika','jaimini_sutram','tajik','kp','saravali','nadi'
    ));

-- Constraint: timing_system must be recognised
ALTER TABLE g29_timing_rules
    ADD CONSTRAINT g29_timing_system_check
    CHECK (timing_system IN (
        'vimshottari','jaimini','tajik','kp_sub','transit','yogini',
        'ashtottari','general','nadi'
    ));

-- Constraint: strength_qualifier
ALTER TABLE g29_timing_rules
    ADD CONSTRAINT g29_strength_check
    CHECK (strength_qualifier IN ('strong','moderate','weak','conditional'));

-- Indexes
CREATE INDEX IF NOT EXISTS g29_source_idx    ON g29_timing_rules(source_text);
CREATE INDEX IF NOT EXISTS g29_category_idx  ON g29_timing_rules(rule_category);
CREATE INDEX IF NOT EXISTS g29_timing_idx    ON g29_timing_rules(timing_system);

COMMENT ON TABLE g29_timing_rules IS
    'G29 Classical Timing Rule Catalog: ~200 falsifiable timing rules from BPHS + Phaladeepika + Jaimini + Tajik + KP + Saravali + Nadi. Feeds A16 Phase-Locked Anchors and retrieval engine.';
