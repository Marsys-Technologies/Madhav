-- Migration 330: ph_nimitta — Predictive Anchors (L4 Phala SPINE)
-- Also DROPs kala_timeline (CF.L3.2 — placeholder never built; safely removable)
-- Two-174 trap: ALL L4 migrations stay in supabase/migrations/ ONLY

-- ── DROP legacy placeholder (CF.L3.2) ────────────────────────────────────────
DROP TABLE IF EXISTS kala_timeline;

-- ── phala_anchors — the predictive anchor spine ───────────────────────────────
CREATE TABLE IF NOT EXISTS phala_anchors (
    anchor_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                uuid NOT NULL,

    -- source provenance (exactly one of convergence/discovery/bhavishya/subsystem is non-null)
    anchor_source           text NOT NULL CHECK (anchor_source IN ('convergence','discovery','bhavishya','subsystem')),
    convergence_id          bigint REFERENCES kala_convergence(convergence_id) ON DELETE SET NULL,
    discovery_id            uuid,   -- bodha_discoveries.id (no FK across layers per B.1; derivation_ledger carries it)
    bhavishya_id            bigint REFERENCES kala_bhavishya(id) ON DELETE SET NULL,   -- D37 inherit
    signal_id               uuid,   -- bodha_msr_signals.signal_id (no FK; Bodha-layer ref)
    subsystem_source        text CHECK (subsystem_source IN ('medical','vastu','nakshatra','yoga','sade_sati','tajaka')),

    -- Axis 1: structural derivation
    event_type              text,
    direction               text NOT NULL CHECK (direction IN ('elevated','suppressed','mixed')),
    domain                  text NOT NULL CHECK (domain IN ('career','relationship','financial','spiritual','health','transition','psychological')),
    horizon_tier            text CHECK (horizon_tier IN ('near','lifetime')),

    -- time coordinates (V2 range)
    window_start            date,
    peak_date               date,
    window_end              date,

    -- V1: magnitude (independent of confidence)
    magnitude               text CHECK (magnitude IN ('minor','moderate','major','pivotal')),
    magnitude_basis         text,

    -- Axis 2 / V2: confidence RANGE, not point (G-LADDER, D21)
    confidence_low          double precision CHECK (confidence_low  >= 0.0 AND confidence_low  <= 0.80),
    confidence_high         double precision CHECK (confidence_high >= 0.0 AND confidence_high <= 0.80),
    confidence_basis        text NOT NULL DEFAULT 'structural_not_yet_empirical',   -- D5

    -- V3: karmic-arc framing
    karmic_frame            text,
    karmic_note             text,

    -- V4: actionability + counterfactual
    malleability            text CHECK (malleability IN ('fated','semi_influenceable','influenceable')),
    counterfactual_jsonb    jsonb,

    -- V5: contradiction carry (bodha_contradictions → anchor's uncertainty)
    contradiction_jsonb     jsonb,

    -- Axis 3: graph-traced causal chain (CGM paths)
    causal_chain_jsonb      jsonb,

    -- Axis 5: embedding precedent (nearest past activations)
    precedent_refs_jsonb    jsonb,

    -- Axis 6: dual consensus (U1 + U4)
    dasha_consensus_count   smallint,
    school_consensus_jsonb  jsonb,  -- {n_of_7, per_school, sigma, disagreement_type}

    -- Axis 7: multi-ayanamsha robustness (0-5)
    ayanamsha_robustness    smallint CHECK (ayanamsha_robustness >= 0 AND ayanamsha_robustness <= 5),

    -- falsifier + audit trail (B.3)
    falsifier               text NOT NULL,
    derivation_ledger_jsonb jsonb NOT NULL,
    source_citation         text NOT NULL,
    computed_at             timestamptz NOT NULL DEFAULT now()
);

-- Natural-key dedup index using COALESCE to treat NULLs as sentinel values
-- (SQL UNIQUE constraint cannot reference expressions; use a unique index)
CREATE UNIQUE INDEX IF NOT EXISTS phala_anchors_natural_key ON phala_anchors (
    chart_id,
    anchor_source,
    domain,
    COALESCE(convergence_id, -1),
    COALESCE(discovery_id, '00000000-0000-0000-0000-000000000000'::uuid),
    COALESCE(bhavishya_id, -1)
);

-- Covering indexes for cockpit count_sql and common read paths
CREATE INDEX IF NOT EXISTS phala_anchors_chart_idx    ON phala_anchors (chart_id);
CREATE INDEX IF NOT EXISTS phala_anchors_domain_idx   ON phala_anchors (chart_id, domain);
CREATE INDEX IF NOT EXISTS phala_anchors_peak_date_idx ON phala_anchors (chart_id, peak_date);
CREATE INDEX IF NOT EXISTS phala_anchors_malleability_idx ON phala_anchors (chart_id, malleability) WHERE malleability = 'influenceable';
