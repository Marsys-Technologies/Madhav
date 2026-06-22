-- Migration 331: ph_muhurta — Auspicious Windows (L4 Phala wave 4)
-- Two-174 trap: ALL L4 migrations stay in supabase/migrations/ ONLY

CREATE TABLE IF NOT EXISTS phala_muhurta (
    muhurta_id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                        uuid NOT NULL,

    action_class                    text NOT NULL,  -- e.g. start_business, marriage, medical, travel
    window_start                    timestamptz,
    window_end                      timestamptz,

    -- panchanga quality from ka_muhurta_seva (REUSED — not reimplemented)
    hora_lord                       text,
    panchanga_score                 double precision CHECK (panchanga_score >= 0 AND panchanga_score <= 1),
    panchanga_snapshot_jsonb        jsonb,  -- tithi/vara/nakshatra/yoga/karana/panchaka/homa

    -- M1: chart-personalized scoring
    chart_personalization_score     double precision CHECK (chart_personalization_score >= 0 AND chart_personalization_score <= 1),
    personalization_graha           text,   -- which graha it keyed on

    -- M2: personal danger-window avoidance
    personal_adversity_penalty      double precision CHECK (personal_adversity_penalty >= 0 AND personal_adversity_penalty <= 1),
    overlapping_obstruction_id      bigint,   -- ka_vighnakara ref (nullable; no FK — cross-layer)

    -- M3: prediction-fused muhurta (rides ph_nimitta window)
    linked_anchor_id                uuid REFERENCES phala_anchors(anchor_id) ON DELETE SET NULL,

    -- composite quality + honest verdict (M4)
    composite_quality               double precision CHECK (composite_quality >= 0 AND composite_quality <= 1),
    window_quality_verdict          text CHECK (window_quality_verdict IN ('strong','adequate','mediocre','none_genuine')),
    verdict_reason                  text,  -- M4: plain reason for mediocre/none_genuine

    -- audit trail (B.3)
    classical_citation              text,
    derivation_ledger_jsonb         jsonb NOT NULL,
    source_citation                 text NOT NULL,
    computed_at                     timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS phala_muhurta_natural_key
    ON phala_muhurta (chart_id, action_class, window_start);

CREATE INDEX IF NOT EXISTS phala_muhurta_chart_idx
    ON phala_muhurta (chart_id);
CREATE INDEX IF NOT EXISTS phala_muhurta_anchor_idx
    ON phala_muhurta (linked_anchor_id) WHERE linked_anchor_id IS NOT NULL;
