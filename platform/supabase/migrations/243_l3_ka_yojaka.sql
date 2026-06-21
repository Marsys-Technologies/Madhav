-- Migration 243 — L3 ka_yojaka: kala_activation_predicates table
-- Stores bound activation predicates; one per (chart_id × signal_id × ayanamsha_id)

CREATE TABLE IF NOT EXISTS kala_activation_predicates (
    id                              BIGSERIAL PRIMARY KEY,
    chart_id                        UUID NOT NULL,
    ayanamsha_id                    TEXT NOT NULL DEFAULT 'true_chitra',
    signal_id                       UUID NOT NULL,
    signature_class                 TEXT NOT NULL CHECK (signature_class IN (
                                        'YOGA','DOSHA','DIGNITY','DISPOSITOR_RELATIONAL',
                                        'SENSITIVE_POINT','CONJUNCTION_ASPECT','SUBSYSTEM','CLASSIFY_RESIDUAL'
                                    )),
    dasha_eligibility_rule_jsonb    JSONB NOT NULL DEFAULT '{}',
    transit_trigger_jsonb           JSONB NOT NULL DEFAULT '{}',
    strength_affliction_hook_jsonb  JSONB NOT NULL DEFAULT '{}',
    derivation_ledger_jsonb         JSONB NOT NULL DEFAULT '{}',
    template_version                TEXT NOT NULL DEFAULT 'v1.0',
    bound_at                        TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_kap_chart_signal_ayan
    ON kala_activation_predicates (chart_id, signal_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS idx_kap_chart ON kala_activation_predicates (chart_id);
CREATE INDEX IF NOT EXISTS idx_kap_class ON kala_activation_predicates (signature_class);
