-- Migration 337: phala_phaladesa — Domain Result Declaration (L4 Phala wave 7)
-- Final synthesis asset. Depends on all preceding phala_* migrations.
--
-- B.11 WHOLE-CHART-READ gate: writer must route through the full L2 Bodha
-- synthesis (MSR + CDLM + CGM + RM) before producing domain-level declarations.
--
-- DETERMINISTIC-FIRST: all structure, selection, ranking, and precedent
-- logic is done in Python before any narration step.
--
-- MODEL POLICY (hard): narration_model must NOT be any Anthropic model.
-- Permitted: gemini-pro, gemini-ultra, deepseek-chat, deepseek-r1, gpt-4o.
-- The DB CHECK enforces this at insert time.
-- The writer produces deterministic structure only; narration is a separate
-- async step that calls an external LLM (never Anthropic's API).

CREATE TABLE IF NOT EXISTS phala_phaladesa (
    phaladesa_id        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id            uuid        NOT NULL,

    -- Domain synthesis (one row per domain × chart)
    domain              text        NOT NULL CHECK (domain IN (
                                        'career', 'financial', 'health',
                                        'relationship', 'spiritual',
                                        'psychological', 'transition'
                                    )),

    -- Anchor inventory for this domain
    anchor_count            smallint    NOT NULL DEFAULT 0,
    clean_anchor_count      smallint    NOT NULL DEFAULT 0,
    staged_revision_count   smallint    NOT NULL DEFAULT 0,
    anomaly_flag_count      smallint    NOT NULL DEFAULT 0,

    -- Top anchor (highest-confidence clean anchor for this domain)
    top_anchor_id           uuid,           -- FK-free; references phala_anchors.anchor_id
    prediction_window_start date,
    prediction_window_end   date,
    peak_date               date,
    magnitude               text    CHECK (magnitude IN ('pivotal','major','moderate','minor')),
    confidence_low          double precision,
    confidence_high         double precision,
    malleability            text    CHECK (malleability IN ('fated','semi_influenceable','influenceable')),

    -- Cross-domain synthesis (from phala_sankrama)
    spillover_domains_jsonb jsonb,          -- [{target_domain, relationship_type, spillover_confidence}]
    incoming_spillover_count smallint DEFAULT 0,  -- domains that spill into this one

    -- Intervention availability
    mitigation_available    boolean NOT NULL DEFAULT false,
    muhurta_available       boolean NOT NULL DEFAULT false,

    -- Falsifiability status (from phala_pramana)
    pramana_window_status   text    CHECK (pramana_window_status IN ('pending','open','past_window')),
    evidence_type           text,

    -- Cross-layer precedent + contradiction (inherited from anchor)
    precedent_refs_jsonb    jsonb,
    contradiction_summary_jsonb jsonb,

    -- Deterministic synthesis structure (built by writer in Python)
    derivation_summary_jsonb jsonb  NOT NULL,

    -- Narration (separate async step; writer sets status='pending' only)
    narration_status        text    NOT NULL DEFAULT 'pending'
                                    CHECK (narration_status IN ('pending', 'ready', 'failed')),
    narration_requested_at  timestamptz,
    narration_model         text    CHECK (narration_model IS NULL OR narration_model IN (
                                        'gemini-pro', 'gemini-ultra', 'gemini-2.0-flash',
                                        'deepseek-chat', 'deepseek-r1',
                                        'gpt-4o', 'gpt-4-turbo'
                                        -- ANTHROPIC MODELS ARE NOT IN THIS LIST (model policy)
                                    )),
    narration_jsonb         jsonb,  -- {language, text, generated_at, model, prompt_hash}

    -- Provenance
    derivation_ledger_jsonb jsonb   NOT NULL,
    source_citation         text    NOT NULL,
    computed_at             timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS phala_phaladesa_natural_key
    ON phala_phaladesa (chart_id, domain);

CREATE INDEX IF NOT EXISTS phala_phaladesa_chart_id ON phala_phaladesa (chart_id);
CREATE INDEX IF NOT EXISTS phala_phaladesa_narration ON phala_phaladesa (chart_id, narration_status);

COMMENT ON TABLE phala_phaladesa IS
'L4 Phala Domain Result Declaration. One row per domain per chart. '
'Writer produces deterministic structure only (B.11 + DETERMINISTIC-FIRST). '
'Narration is a separate async step via Gemini/DeepSeek (Anthropic BANNED per model policy). '
'narration_model CHECK constraint enforces approved models at the DB level.';

COMMENT ON COLUMN phala_phaladesa.narration_model IS
'MODEL POLICY: Gemini/DeepSeek only. Any Anthropic model ID here is a policy violation. '
'The DB CHECK constraint enforces the approved model list. The writer never calls narration — '
'it sets narration_status=pending and narration_model=NULL only.';
