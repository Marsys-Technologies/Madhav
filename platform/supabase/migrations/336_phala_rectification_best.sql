-- Migration 334: phala_rectification_best — Staged best rectification candidate
-- Separate from 334_phala_suddha_sodhana (cleansed anchor disposition); both apply via migrate.ts filename keying.
-- NO-AUTO-OVERRIDE gate (D43): auto_action ALWAYS 'stage_for_review'. Canonical chart NEVER auto-mutated.
CREATE TABLE IF NOT EXISTS phala_rectification_best (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                uuid NOT NULL UNIQUE REFERENCES charts(id) ON DELETE CASCADE,
    best_candidate_id       uuid REFERENCES phala_rectification(id),
    candidate_birth_utc     timestamptz,
    offset_minutes          integer,           -- signed offset from recorded 10:43 IST
    best_lagna_sign         text,
    best_lagna_longitude    numeric(8,4),
    best_lel_fit_score      numeric(6,4),
    confidence_low          numeric(6,4),
    confidence_high         numeric(6,4),
    confidence_label        text CHECK (confidence_label IN ('decisive','probable','unresolved')),
    win_margin              numeric(6,4),       -- score gap between best and second-best
    competing_candidates    jsonb,              -- top-3 candidates with scores for transparency
    lel_training_events     integer,
    lel_training_matched    integer,
    leakage_firewall_note   text,
    auto_action             text NOT NULL DEFAULT 'stage_for_review'
        CHECK (auto_action = 'stage_for_review'),  -- D43 hard gate
    scored_at               timestamptz NOT NULL DEFAULT NOW(),
    native_adopted          boolean NOT NULL DEFAULT false,  -- set by native on adoption
    adopted_at              timestamptz
);
