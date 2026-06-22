-- Migration 336: phala_pramana — Falsifiability Evidence Registry
-- Part of L4 Phala Wave 6. Depends on migrations 330 (phala_anchors) + 333 (phala_sodhana).
--
-- D5 / L4-L5 BOUNDARY (hard gate): ph_pramana is STRICTLY NON-SCORING.
-- It collects falsifiability structure, observable criteria, and evidence
-- linkage. It NEVER assigns calibration_score, posterior_probability, or
-- any empirical accuracy metric — those are exclusively L5 Mimamsa territory.
--
-- What ph_pramana stores:
--   1. evidence_type: what kind of observable event could confirm/refute this anchor
--   2. observable_criteria_jsonb: the machine-evaluable REFUTED/CONFIRMED criteria
--   3. lel_entry_id: LEL entries that are candidate evidence (by lel.id)
--   4. window_status: 'pending' | 'open' | 'past_window' (time-indexed, not outcome-scored)
--   5. evidence_strength_label: 'direct' | 'indirect' | 'proxy' — structural taxonomy ONLY
--      (NOT a score; describes the relationship between evidence and prediction)
--   6. falsification_ledger_jsonb: derivation chain from anchor → criteria → evidence
--
-- WHAT ph_pramana NEVER stores:
--   calibration_score, accuracy_rate, posterior_probability, hit_rate,
--   precision, recall, Brier_score, or any numerical accuracy metric.
--   The ph_pramana writer raises D5ViolationError if any scoring attempt.

CREATE TABLE IF NOT EXISTS phala_pramana (
    pramana_id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            uuid        NOT NULL,
    anchor_id           uuid        NOT NULL REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE,

    -- Evidence taxonomy (structural labels only; NO scoring)
    evidence_type       text        NOT NULL CHECK (evidence_type IN (
                                        'life_event_match',     -- LEL record in window
                                        'life_event_miss',      -- window passed, no LEL match
                                        'proxy_indicator',      -- indirect observable
                                        'self_report',          -- native-reported outcome
                                        'pending_observation'   -- window not yet open/closed
                                    )),
    evidence_strength_label text    NOT NULL CHECK (evidence_strength_label IN (
                                        'direct',    -- observable directly tied to prediction
                                        'indirect',  -- related but mediated
                                        'proxy'      -- surrogate indicator only
                                    )),

    -- Observable criteria (from ph_nimitta falsifier field)
    falsifier_text      text        NOT NULL,
    observable_criteria_jsonb jsonb NOT NULL,   -- {criterion, observable_by, deadline}
    window_status       text        NOT NULL CHECK (window_status IN (
                                        'pending',       -- window not yet started
                                        'open',          -- inside prediction window
                                        'past_window'    -- window closed; outcome observable
                                    )),

    -- Evidence links (cross-refs; no FK to LEL — different schema)
    lel_entry_id        bigint,     -- life_event_log.id if evidence from LEL (NULL if pending)
    lel_entry_jsonb     jsonb,      -- snapshot of LEL entry at time of linkage
    linked_sodhana_id   uuid,       -- phala_sodhana flag that prompted review (optional)

    -- D5 NO-SCORING: calibration_score, posterior_probability DO NOT EXIST in this table.
    -- Any writer that adds these columns here is a critical D5 violation.

    -- Provenance
    derivation_ledger_jsonb jsonb   NOT NULL,
    source_citation     text        NOT NULL,
    computed_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS phala_pramana_chart_id ON phala_pramana (chart_id);
CREATE INDEX IF NOT EXISTS phala_pramana_anchor_id ON phala_pramana (anchor_id);
CREATE INDEX IF NOT EXISTS phala_pramana_window_status ON phala_pramana (chart_id, window_status);

-- Natural key: one evidence_type per anchor, per optional lel_entry_id
CREATE UNIQUE INDEX IF NOT EXISTS phala_pramana_natural_key
    ON phala_pramana (anchor_id, evidence_type,
                      COALESCE(lel_entry_id, -1));

COMMENT ON TABLE phala_pramana IS
'L4 Phala Falsifiability Evidence Registry. Strictly non-scoring per D5 / L4-L5 boundary. '
'Collects observable criteria and evidence linkage per phala_anchors entry. '
'Calibration scores (accuracy, Brier, posterior) are L5 Mimamsa territory only.';
