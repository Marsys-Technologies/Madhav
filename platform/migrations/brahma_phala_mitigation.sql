-- brahma_phala_mitigation.sql — phala.mitigation schema
-- Layer L4 · Phala (Predictive Engine) · Asset PH-4-2
-- BRAHMA-PH-4-2
--
-- Creates phala_mitigation: per-anchor classical remedy map.
--
-- Contract:
--   anchor_id TEXT — FK reference to phala_anchors.anchor_id (deferred; phala_anchors is PH-4-1)
--   mitigation_type TEXT CHECK IN ('mantra','charity','gemstone','ritual','timing')
--   mitigation_text TEXT NOT NULL
--   source_l0_rule_id TEXT — concordance rule_id or BPHS-FALLBACK-* (BG-0-7 L0 concordance)
--   source_citation TEXT NOT NULL — BPHS chapter.verse or L2 remediation reference (BO-2-6)
--
-- Every mitigation row carries a non-null source_citation tracing to:
--   - BPHS.<chapter>.<verses> — from L0 concordance (BG-0-7)
--   - BO-2-6.BPHS.<chapter>.<verses> — cross-referenced from L2 bodha.remediation
--
-- Grounding: Abhisek Mohanty 1984-02-05 10:43 IST Bhubaneswar.
--
-- Depends on (upstream must exist before applying):
--   - phala_anchors  (PH-4-1: phala.anchors) — FK reference
--   - concordance_lookup (BG-0-7) — L0 rule grounding
--   - bodha_remediation  (BO-2-6) — L2 remediation cross-reference
--
-- Idempotent: safe to re-run (CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS).

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  phala_mitigation
-- ─────────────────────────────────────────────────────────────────────────────
-- One row per (chart_id, anchor_id, mitigation_type):
--   anchor_id        — event anchor from phala_anchors (PH-4-1)
--   chart_id         — the native's chart UUID
--   theme            — copy of the anchor's predicted theme (denormalised for query performance)
--   mitigation_type  — classical remedy category:
--                      mantra | charity | gemstone | ritual | timing
--   mitigation_text  — full cited remedy prescription
--   source_l0_rule_id — L0 concordance rule_id (BG-0-7) or BPHS-FALLBACK-<topic>
--   source_citation  — BPHS chapter.verse or BO-2-6 cross-reference (NON-NULL, enforced)
--   l2_remediation_hub_id — optional back-link to bodha_remediation.contradiction_hub_id (BO-2-6)
--   build_id         — build provenance
--   asset_version    — PH-4-2 writer version
--   computed_at      — UTC timestamp

CREATE TABLE IF NOT EXISTS public.phala_mitigation (
    id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                 UUID        NOT NULL,
    anchor_id                TEXT        NOT NULL,   -- ref to phala_anchors.anchor_id (PH-4-1)
    theme                    TEXT,                   -- denormalised anchor theme for display
    mitigation_type          TEXT        NOT NULL
                             CHECK (mitigation_type IN ('mantra', 'charity', 'gemstone', 'ritual', 'timing')),
    mitigation_text          TEXT        NOT NULL,
    source_l0_rule_id        TEXT        NOT NULL,   -- concordance rule_id or BPHS-FALLBACK-*
    source_citation          TEXT        NOT NULL,   -- BPHS.<ch>.<vv> or BO-2-6 ref — NEVER NULL
    l2_remediation_hub_id    TEXT,                   -- optional FK to bodha_remediation.contradiction_hub_id
    build_id                 TEXT        NOT NULL,
    asset_version            TEXT        NOT NULL DEFAULT '1.0',
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One mitigation-type per anchor per chart
    CONSTRAINT uq_phala_mitigation_anchor_type UNIQUE (chart_id, anchor_id, mitigation_type)
);

COMMENT ON TABLE public.phala_mitigation IS
    'L4 Phala (PH-4-2): per-anchor classical mitigation map. '
    'Each row maps one event anchor (phala_anchors / PH-4-1) to a classical remedy '
    'cited from L0 concordance (BG-0-7) + L2 bodha.remediation (BO-2-6). '
    'source_citation is NON-NULL: always traces to a specific BPHS chapter/verse. '
    'mitigation_type: mantra | charity | gemstone | ritual | timing.';

COMMENT ON COLUMN public.phala_mitigation.anchor_id IS
    'Reference to phala_anchors.anchor_id (PH-4-1). '
    'Soft FK (no hard REFERENCES constraint — phala_anchors builds in PH-4-1, which may deploy after PH-4-2).';

COMMENT ON COLUMN public.phala_mitigation.source_l0_rule_id IS
    'L0 concordance rule_id (BG-0-7) or BPHS-FALLBACK-<topic>. '
    'Traces to concordance_lookup.id or a canonical BPHS chapter pointer.';

COMMENT ON COLUMN public.phala_mitigation.source_citation IS
    'NON-NULL. BPHS.<chapter>.<verses> or BO-2-6 cross-reference. '
    'Format: BPHS.<chapter>.<verses>  e.g. BPHS.25.41-56.';

COMMENT ON COLUMN public.phala_mitigation.l2_remediation_hub_id IS
    'Optional back-link to bodha_remediation.contradiction_hub_id (BO-2-6). '
    'Present when the anchor maps directly to an existing L2 contradiction hub.';

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Indexes
-- ─────────────────────────────────────────────────────────────────────────────

-- Primary access: all mitigations for a chart
CREATE INDEX IF NOT EXISTS idx_phala_mitigation_chart
    ON public.phala_mitigation (chart_id);

-- Per-anchor lookup (fetch all mitigation types for one anchor)
CREATE INDEX IF NOT EXISTS idx_phala_mitigation_anchor
    ON public.phala_mitigation (chart_id, anchor_id);

-- Mitigation type filter
CREATE INDEX IF NOT EXISTS idx_phala_mitigation_type
    ON public.phala_mitigation (mitigation_type);

-- L0 rule reverse lookup
CREATE INDEX IF NOT EXISTS idx_phala_mitigation_l0_rule
    ON public.phala_mitigation (source_l0_rule_id);

-- L2 cross-reference
CREATE INDEX IF NOT EXISTS idx_phala_mitigation_l2_hub
    ON public.phala_mitigation (l2_remediation_hub_id)
    WHERE l2_remediation_hub_id IS NOT NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Staging table (for atomic swap builds)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.phala_mitigation_staging
    (LIKE public.phala_mitigation INCLUDING ALL);

COMMENT ON TABLE public.phala_mitigation_staging IS
    'Staging copy of phala_mitigation for atomic swap builds (PH-4-2).';

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  Tool registration (capability_tool_registry)
-- ─────────────────────────────────────────────────────────────────────────────
-- Register mitigation_map as a live retrieval tool.
-- Idempotent — ON CONFLICT DO UPDATE.

INSERT INTO public.capability_tool_registry (
    tool_name,
    description,
    expose_to_planner,
    linked_data_asset_ids,
    created_at
)
VALUES (
    'mitigation_map',
    'Returns per-anchor classical mitigations for a chart (phala.mitigation / PH-4-2). '
    'Each mitigation is cited to a BPHS chapter/verse or L0 concordance rule_id (BG-0-7), '
    'cross-referenced with L2 bodha.remediation (BO-2-6). '
    'Optional anchor_id parameter narrows to a single event anchor. '
    'mitigation_type: mantra | charity | gemstone | ritual | timing. '
    'source_citation format: BPHS.<chapter>.<verses>. '
    'surgical: true — pure retrieval, no LLM synthesis.',
    TRUE,
    ARRAY['phala.mitigation'],
    NOW()
)
ON CONFLICT (tool_name) DO UPDATE SET
    description           = EXCLUDED.description,
    expose_to_planner     = EXCLUDED.expose_to_planner,
    linked_data_asset_ids = EXCLUDED.linked_data_asset_ids;

-- Asset-tool binding
INSERT INTO public.capability_asset_tool_bindings (
    asset_canonical_id,
    tool_name,
    binding_source
)
VALUES (
    'phala.mitigation',
    'mitigation_map',
    'manifest'
)
ON CONFLICT (asset_canonical_id, tool_name) DO NOTHING;

COMMIT;
