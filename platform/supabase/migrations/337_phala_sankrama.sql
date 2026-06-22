-- Migration 335: ph_sankrama — Cross-Domain Spillover (L4 Phala wave 4)
-- Two-174 trap: ALL L4 migrations stay in supabase/migrations/ ONLY

CREATE TABLE IF NOT EXISTS phala_sankrama (
    sankrama_id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                    uuid NOT NULL,

    -- source references (anti-drift FKs — cross-layer refs via ledger for Bodha)
    source_anchor_id            uuid REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE,
    cdlm_cell_id                uuid,   -- bodha_cdlm_cells.cell_id (no cross-layer FK; ledger carries it)

    -- spillover axis
    source_domain               text NOT NULL,
    target_domain               text NOT NULL,
    relationship_type           text NOT NULL CHECK (relationship_type IN ('contagion','conflict')),  -- SK3

    -- SK1: grounded timing + graph mechanism
    linkage_strength            double precision,
    asymmetry_score             double precision,
    bridge_path_jsonb           jsonb,   -- {graha, house, path_ids, mechanism}
    mechanism_text              text,    -- "career stress loads onto health VIA Saturn→Moon bridge"

    source_window_start         date,
    source_window_end           date,
    projected_window_start      date,   -- DERIVED from activation windows, not a formula (SK1)
    projected_window_end        date,
    projected_peak_date         date,

    -- SK2: multi-hop cascade (A→B→C, ≤3 hops)
    cascade_chain_jsonb         jsonb,  -- [{domain, cell_id, window}]
    cascade_depth               smallint CHECK (cascade_depth >= 1 AND cascade_depth <= 3),

    -- SK4: evolution trajectory + mitigation routing
    trajectory                  text CHECK (trajectory IN ('strengthening','stable','weakening')),
    mitigation_ref              uuid REFERENCES phala_mitigation(mitigation_id) ON DELETE SET NULL,

    -- confidence (inherits from source anchor; structural only)
    spillover_confidence        double precision CHECK (spillover_confidence >= 0 AND spillover_confidence <= 0.80),
    confidence_basis            text NOT NULL DEFAULT 'structural_not_yet_empirical',

    -- falsifier + audit trail
    falsifier                   text NOT NULL,
    derivation_ledger_jsonb     jsonb NOT NULL,
    source_citation             text NOT NULL,
    computed_at                 timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS phala_sankrama_natural_key
    ON phala_sankrama (chart_id, source_anchor_id, target_domain, relationship_type);

CREATE INDEX IF NOT EXISTS phala_sankrama_chart_idx
    ON phala_sankrama (chart_id);
CREATE INDEX IF NOT EXISTS phala_sankrama_source_anchor_idx
    ON phala_sankrama (source_anchor_id);
