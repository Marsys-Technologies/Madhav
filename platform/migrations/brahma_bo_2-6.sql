-- brahma_bo_2-6.sql — bodha.remediation schema
-- Layer L2 · Wave 2 · Asset BO-2-6
--
-- Creates bodha_remediation: per-contradiction-hub remedy map citing L0 concordance.
--
-- Depends on (upstream must exist before applying):
--   - bodha_signals  (BO-2-1 bodha.signals)
--   - bodha_graph    (BO-2-2 bodha.graph)
--   - concordance_lookup  (BG-0-7 brahmagyan.concordance)
--
-- FORENSIC ground: Abhisek Mohanty 1984-02-05 10:43 IST Bhubaneswar.
-- Every remedy row carries a source_citation tracing to BPHS or L0 concordance rule_id.
--
-- Idempotent: safe to re-run (CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS).

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  bodha_remediation
-- ─────────────────────────────────────────────────────────────────────────────
-- One row per (chart_id, contradiction_hub_id):
--   contradiction_hub_id  — signal_id of the node that is the hub of a
--                           contradiction cluster in bodha_graph
--   hub_label             — human-readable label of the hub signal
--   domain                — Jyotish domain (career / health / relationship /…)
--   edge_count            — number of contradicting edges from this hub
--   contradicting_signal_ids — array of signal_ids contradicted by this hub
--   remedy_type           — classical remedy category: mantra | charity | gemstone | ritual
--   remedy_text           — full remedy prescription (cited)
--   source_l0_rule_id     — the L0 concordance rule_id (or BPHS-FALLBACK-* when concordance
--                           is pre-seeded): traces to a specific rule in concordance_lookup
--   source_citation       — BPHS chapter.verse reference (e.g. BPHS.25.41-56) or
--                           concordance_lookup.source_citation value
--   build_id              — build provenance
--   asset_version         — BO-2-6 writer version
--   computed_at           — UTC timestamp of computation

CREATE TABLE IF NOT EXISTS public.bodha_remediation (
    id                        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                  UUID        NOT NULL,
    contradiction_hub_id      TEXT        NOT NULL,   -- signal_id from bodha_signals
    hub_label                 TEXT,
    domain                    TEXT,
    edge_count                INTEGER     NOT NULL DEFAULT 0,
    contradicting_signal_ids  TEXT[]      NOT NULL DEFAULT '{}',
    remedy_type               TEXT        NOT NULL
                              CHECK (remedy_type IN ('mantra', 'charity', 'gemstone', 'ritual')),
    remedy_text               TEXT        NOT NULL,
    source_l0_rule_id         TEXT        NOT NULL,   -- concordance rule_id or BPHS-FALLBACK-*
    source_citation           TEXT        NOT NULL,   -- e.g. BPHS.25.41-56
    build_id                  TEXT        NOT NULL,
    asset_version             TEXT        NOT NULL DEFAULT '1.0',
    computed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique per hub per chart — one remedy per contradiction hub
    CONSTRAINT uq_bodha_remediation_hub UNIQUE (chart_id, contradiction_hub_id)
);

COMMENT ON TABLE public.bodha_remediation IS
    'L2 Bodha Wave-2 (BO-2-6): per-contradiction-hub remedy map. '
    'Each row maps one contradiction hub from bodha_graph to a classical remedy '
    'cited from L0 concordance (BG-0-7) or BPHS. '
    'source_citation always traces to a specific BPHS chapter/verse or L0 rule_id.';

COMMENT ON COLUMN public.bodha_remediation.source_l0_rule_id IS
    'L0 concordance rule ID or BPHS-FALLBACK-<topic>. '
    'Traces to concordance_lookup.id or is a BPHS chapter pointer pre-seeded in the fallback map.';

COMMENT ON COLUMN public.bodha_remediation.source_citation IS
    'BPHS chapter.verses or concordance_lookup.source_citation. '
    'Format: BPHS.<chapter>.<verses>  e.g. BPHS.25.41-56.';

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Indexes
-- ─────────────────────────────────────────────────────────────────────────────

-- Primary access pattern: all remedies for a chart
CREATE INDEX IF NOT EXISTS idx_bodha_remediation_chart
    ON public.bodha_remediation (chart_id);

-- Domain filter (e.g. query_remediation(chart_id, domain='career'))
CREATE INDEX IF NOT EXISTS idx_bodha_remediation_domain
    ON public.bodha_remediation (chart_id, domain);

-- Remedy type filter
CREATE INDEX IF NOT EXISTS idx_bodha_remediation_remedy_type
    ON public.bodha_remediation (remedy_type);

-- L0 rule lookup (reverse lookup: which charts does a rule apply to?)
CREATE INDEX IF NOT EXISTS idx_bodha_remediation_l0_rule
    ON public.bodha_remediation (source_l0_rule_id);

-- Signal coverage (does a given signal appear as a hub?)
CREATE INDEX IF NOT EXISTS idx_bodha_remediation_hub_id
    ON public.bodha_remediation (contradiction_hub_id);

-- GIN index on contradicting_signal_ids array
CREATE INDEX IF NOT EXISTS idx_bodha_remediation_signal_ids
    ON public.bodha_remediation USING GIN (contradicting_signal_ids);

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Staging table (for atomic swap builds)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.bodha_remediation_staging
    (LIKE public.bodha_remediation INCLUDING ALL);

COMMENT ON TABLE public.bodha_remediation_staging IS
    'Staging copy of bodha_remediation for atomic swap builds (BO-2-6).';

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  Tool registration (capability_tool_registry)
-- ─────────────────────────────────────────────────────────────────────────────
-- Register query_remediation as a live retrieval tool.
-- Idempotent — ON CONFLICT DO UPDATE.

INSERT INTO public.capability_tool_registry (
    tool_name,
    description,
    expose_to_planner,
    linked_data_asset_ids,
    created_at
)
VALUES (
    'query_remediation',
    'Returns per-contradiction-hub classical remedies for a chart (bodha.remediation / BO-2-6). '
    'Each remedy is cited to a BPHS chapter/verse or L0 concordance rule_id (BG-0-7). '
    'Optional domain parameter narrows to a single Jyotish domain (career/health/relationship/…). '
    'source_citation format: BPHS.<chapter>.<verses>.',
    TRUE,
    ARRAY['bodha.remediation'],
    NOW()
)
ON CONFLICT (tool_name) DO UPDATE SET
    description           = EXCLUDED.description,
    expose_to_planner     = EXCLUDED.expose_to_planner,
    linked_data_asset_ids = EXCLUDED.linked_data_asset_ids;

-- Also bind to capability_asset_tool_bindings
INSERT INTO public.capability_asset_tool_bindings (
    asset_canonical_id,
    tool_name,
    binding_source
)
VALUES (
    'bodha.remediation',
    'query_remediation',
    'manifest'
)
ON CONFLICT (asset_canonical_id, tool_name) DO NOTHING;

COMMIT;
