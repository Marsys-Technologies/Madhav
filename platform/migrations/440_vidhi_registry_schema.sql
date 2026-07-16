-- Migration 440: Vidhi Engine registry schema — D-2 Lane V-1 (Vidhi registry + compiler)
-- L0 Brahmagyan global reference tables: the ~30-primitive vidhi registry + per-intent-
-- class acharya floor / machine band. Chart-agnostic; seeded by bg_vidhi_primitives.py
-- and bg_vidhi_floors.py (writers, this same lane).
--
-- Design: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3 ("Vidhi = grammar + compiler, NOT a fixed
-- checklist"). Source drafts: 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/
-- track3/ (Track-3 authoring, absorbed into this lane per BRIEF_D2.md).
--
-- §N.3 L0 idempotency: ON CONFLICT DO UPDATE (global, not per-chart) — see writers.
--
-- ROLLBACK:
--   DELETE FROM asset_registry WHERE asset_id IN ('bg_vidhi_primitives','bg_vidhi_floors');
--   DROP TABLE IF EXISTS vidhi_floor_items;
--   DROP TABLE IF EXISTS vidhi_intent_floors;
--   DROP TABLE IF EXISTS vidhi_primitives;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — vidhi_primitives ────────────────────────────────────────────────────
-- One row per versioned primitive atom (bhava_condition, varga_ratification, ...).

CREATE TABLE IF NOT EXISTS vidhi_primitives (
    primitive_id       TEXT NOT NULL,
    version            INTEGER NOT NULL DEFAULT 1,
    definition         TEXT NOT NULL,
    category           TEXT NOT NULL
                        CHECK (category IN ('structural','strength','temporal','signal','doctrine','remedy','utility')),
    live_tool          TEXT NOT NULL,                 -- real MCP tool name (mcp__marsys-jis-direct__<live_tool>)
    tool_args          JSONB NOT NULL DEFAULT '{}'::JSONB,
    fallback_face      TEXT,                           -- secondary/degraded-mode face, nullable
    known_gap          TEXT,                           -- CR-N register pointer, nullable; NEVER a CLOSED CR
    mandatory_tags     TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],  -- §B0.4 mandatory-surface tags satisfied
    cr27_prevents      TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],  -- CR-27 corpus instance(s) prevented
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (primitive_id)
);

COMMENT ON TABLE vidhi_primitives IS
    'L0 Brahmagyan: Vidhi Engine primitive registry (D-2 Lane V-1). ~30 versioned atoms, '
    'each with a live-tool mapping + fallback face + known_gap CR pointer. Global, not '
    'per-chart. Mirrored in platform/src/lib/vidhi/registry_data.ts for compiler testing.';

-- ── §2 — vidhi_intent_floors ─────────────────────────────────────────────────
-- One row per intent class (wealth_deepdive, career_deepdive, ...).

CREATE TABLE IF NOT EXISTS vidhi_intent_floors (
    intent             TEXT NOT NULL,
    version            INTEGER NOT NULL DEFAULT 1,
    cr27_coverage      TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    notes              TEXT,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (intent)
);

COMMENT ON TABLE vidhi_intent_floors IS
    'L0 Brahmagyan: per-intent-class acharya floor + machine band header row. Floor items '
    'live in vidhi_floor_items. Every intent class the compiler recognizes MUST have a row '
    'here (floor-coverage test enforces this on the TS mirror).';

-- ── §3 — vidhi_floor_items ───────────────────────────────────────────────────
-- Ordered floor-item rows per intent (band + primitive + optional arg overrides).

CREATE TABLE IF NOT EXISTS vidhi_floor_items (
    id                 SERIAL PRIMARY KEY,
    intent             TEXT NOT NULL REFERENCES vidhi_intent_floors(intent) ON DELETE CASCADE,
    primitive_id       TEXT NOT NULL REFERENCES vidhi_primitives(primitive_id) ON DELETE RESTRICT,
    item_order         INTEGER NOT NULL,
    band               TEXT NOT NULL CHECK (band IN ('acharya_floor','machine_band')),
    args_override      JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT vidhi_floor_items_intent_order_unique UNIQUE (intent, item_order)
);

COMMENT ON TABLE vidhi_floor_items IS
    'L0 Brahmagyan: ordered per-intent floor items. intent×item_order is unique so a floor '
    'compiles deterministically. band=acharya_floor is the non-skippable classical checklist; '
    'band=machine_band is computation-only differentiator content (design §3).';

CREATE INDEX IF NOT EXISTS idx_vidhi_floor_items_intent ON vidhi_floor_items (intent);
CREATE INDEX IF NOT EXISTS idx_vidhi_floor_items_primitive ON vidhi_floor_items (primitive_id);
CREATE INDEX IF NOT EXISTS idx_vidhi_primitives_known_gap ON vidhi_primitives (known_gap) WHERE known_gap IS NOT NULL;

-- ── §4 — asset_registry entries ──────────────────────────────────────────────

INSERT INTO asset_registry (asset_id, display_name, layer, scope, asset_type, depends_on,
    count_sql, target_floor, sort_order, has_substeps)
VALUES (
    'bg_vidhi_primitives',
    'Vidhi Registry — Primitives (bg_vidhi_primitives)',
    'L0',
    'global',
    'brahmagyan',
    ARRAY[]::TEXT[],
    '(SELECT COUNT(*) FROM vidhi_primitives)',
    25,
    68,
    false
) ON CONFLICT (asset_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    count_sql    = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor;

INSERT INTO asset_registry (asset_id, display_name, layer, scope, asset_type, depends_on,
    count_sql, target_floor, sort_order, has_substeps)
VALUES (
    'bg_vidhi_floors',
    'Vidhi Registry — Intent Floors (bg_vidhi_floors)',
    'L0',
    'global',
    'brahmagyan',
    ARRAY['bg_vidhi_primitives']::TEXT[],
    '(SELECT COUNT(*) FROM vidhi_floor_items)',
    8,
    69,
    false
) ON CONFLICT (asset_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    count_sql    = EXCLUDED.count_sql,
    target_floor = EXCLUDED.target_floor,
    depends_on   = EXCLUDED.depends_on;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id IN ('bg_vidhi_primitives','bg_vidhi_floors');
--   DROP TABLE IF EXISTS vidhi_floor_items;
--   DROP TABLE IF EXISTS vidhi_intent_floors;
--   DROP TABLE IF EXISTS vidhi_primitives;
--   COMMIT;
-- =============================================================================
