-- Migration 139: G29 Classical Timing Rule Catalog
-- Stream C [BUILD-ORCH-STREAM-C-G29-S1]
-- Idempotent: CREATE TABLE IF NOT EXISTS with inline CHECK constraints

CREATE TABLE IF NOT EXISTS g29_timing_rules (
    rule_id              TEXT        PRIMARY KEY,
    source_text          TEXT        NOT NULL
                             CHECK (source_text IN (
                                 'bphs','phaladeepika','jaimini_sutram',
                                 'tajik','kp','saravali','nadi'
                             )),
    rule_category        TEXT        NOT NULL,
    timing_system        TEXT        NOT NULL
                             CHECK (timing_system IN (
                                 'vimshottari','jaimini','tajik','kp_sub',
                                 'transit','yogini','ashtottari','general','nadi'
                             )),
    trigger_predicate    TEXT        NOT NULL,
    predicted_outcome    TEXT        NOT NULL,
    activation_window    TEXT        NOT NULL,
    strength_qualifier   TEXT        NOT NULL DEFAULT 'moderate'
                             CHECK (strength_qualifier IN (
                                 'strong','moderate','weak','conditional'
                             )),
    classical_citation   TEXT,
    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes (all IF NOT EXISTS — idempotent)
CREATE INDEX IF NOT EXISTS g29_source_idx    ON g29_timing_rules(source_text);
CREATE INDEX IF NOT EXISTS g29_category_idx  ON g29_timing_rules(rule_category);
CREATE INDEX IF NOT EXISTS g29_timing_idx    ON g29_timing_rules(timing_system);

COMMENT ON TABLE g29_timing_rules IS
    'G29 Classical Timing Rule Catalog: ~220 falsifiable timing rules from BPHS + Phaladeepika + Jaimini + Tajik + KP + Saravali + Nadi. Feeds A16 Phase-Locked Anchors and retrieval engine.';
