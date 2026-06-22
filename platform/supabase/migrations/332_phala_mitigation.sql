-- Migration 332: ph_pratikara — Mitigation / Remedy Program (L4 Phala wave 4)
-- Two-174 trap: ALL L4 migrations stay in supabase/migrations/ ONLY

CREATE TABLE IF NOT EXISTS phala_mitigation (
    mitigation_id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                        uuid NOT NULL,

    -- source references (anti-drift)
    obstruction_id                  bigint,   -- ka_vighnakara obstruction (no cross-layer FK; ledger carries it)
    linked_anchor_id                uuid REFERENCES phala_anchors(anchor_id) ON DELETE SET NULL,
    afflicting_graha                text,
    obstruction_severity            text,

    -- P2: ordered, non-conflicting remedy schedule
    program_jsonb                   jsonb NOT NULL,   -- [{prescription_id, order, prereq_ids}]

    -- P5: cross-tradition options + corroboration
    tradition_options_jsonb         jsonb NOT NULL,   -- {vedic: [...], tantra: [...], ...}
    cross_tradition_corroboration   smallint CHECK (cross_tradition_corroboration >= 0 AND cross_tradition_corroboration <= 6),

    -- P1: cost/time/feasibility tiers
    recommended_tier_jsonb          jsonb,   -- {free: {...}, low_cost: {...}, high_investment: {...}}

    -- P4: proportionality
    intensity_tier                  text CHECK (intensity_tier IN ('light','moderate','intensive')),
    proportionality_basis           text,

    -- P3: muhurta-timed initiation
    initiation_muhurta_ref          uuid REFERENCES phala_muhurta(muhurta_id) ON DELETE SET NULL,

    -- time scope + outcome loop (P4)
    window_start                    date,
    window_end                      date,
    re_evaluation_date              date NOT NULL,
    outcome_hook_jsonb              jsonb NOT NULL,   -- falsifiable did-it-help, for L5

    -- audit trail
    classical_citation              text NOT NULL,
    derivation_ledger_jsonb         jsonb NOT NULL,
    source_citation                 text NOT NULL,
    computed_at                     timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS phala_mitigation_natural_key
    ON phala_mitigation (chart_id, COALESCE(obstruction_id, -1), intensity_tier);

CREATE INDEX IF NOT EXISTS phala_mitigation_chart_idx
    ON phala_mitigation (chart_id);
CREATE INDEX IF NOT EXISTS phala_mitigation_anchor_idx
    ON phala_mitigation (linked_anchor_id) WHERE linked_anchor_id IS NOT NULL;
