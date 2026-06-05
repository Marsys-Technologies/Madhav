-- Migration 070: capability_tool_registry + capability_asset_tool_bindings
--
-- Creates two tables for manifest tool-binding metadata surfaced by COV-S2.
-- Populated by platform/scripts/governance/seed_tool_registry.ts (upsert semantics).
--
-- capability_tool_registry : one row per wired retrieval tool (30 rows post-COV-S2)
-- capability_asset_tool_bindings : many-to-many join between asset canonical_ids and tool_names

CREATE TABLE IF NOT EXISTS capability_tool_registry (
  tool_name            text        PRIMARY KEY,
  expose_to_planner    boolean     NOT NULL DEFAULT false,
  description          text        NOT NULL DEFAULT '',
  query_schema         jsonb,
  output_schema        jsonb,
  cost_weight          numeric,
  linked_data_asset_ids text[]     NOT NULL DEFAULT '{}',
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE capability_tool_registry IS
  'One row per wired RETRIEVAL_TOOLS[] entry. Seeded from CAPABILITY_MANIFEST.json + manifest_overrides.yaml by seed_tool_registry.ts. Re-seed after any manifest change.';

COMMENT ON COLUMN capability_tool_registry.tool_name IS
  'Canonical tool name matching TOOL_NAME constant in retrieve/*.ts and RETRIEVAL_TOOLS[].name.';

COMMENT ON COLUMN capability_tool_registry.expose_to_planner IS
  'Whether the planner may route queries to this tool. Mirrors expose_to_planner field in manifest_overrides.yaml.';

COMMENT ON COLUMN capability_tool_registry.linked_data_asset_ids IS
  'Canonical asset IDs this tool reads (e.g. MSR, FORENSIC, PANCHANGA_DAILY). From linked_data_asset_ids[] in manifest_overrides.yaml.';

CREATE TABLE IF NOT EXISTS capability_asset_tool_bindings (
  asset_canonical_id text        NOT NULL,
  tool_name          text        NOT NULL REFERENCES capability_tool_registry(tool_name) ON DELETE CASCADE,
  binding_source     text        NOT NULL CHECK (binding_source IN ('manifest', 'override', 'inferred')),
  created_at         timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_canonical_id, tool_name)
);

COMMENT ON TABLE capability_asset_tool_bindings IS
  'Many-to-many join between asset canonical_ids and tool_names. Denormalized from linked_data_asset_ids[] for efficient reverse lookup (which tools read asset X?).';

CREATE INDEX IF NOT EXISTS idx_capability_asset_tool_bindings_asset
  ON capability_asset_tool_bindings (asset_canonical_id);

CREATE INDEX IF NOT EXISTS idx_capability_asset_tool_bindings_tool
  ON capability_asset_tool_bindings (tool_name);

-- updated_at trigger for capability_tool_registry
CREATE OR REPLACE FUNCTION update_capability_tool_registry_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_capability_tool_registry_updated_at ON capability_tool_registry;
CREATE TRIGGER trg_capability_tool_registry_updated_at
  BEFORE UPDATE ON capability_tool_registry
  FOR EACH ROW EXECUTE FUNCTION update_capability_tool_registry_updated_at();
