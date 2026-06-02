BEGIN;

CREATE TABLE IF NOT EXISTS query_plans (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  query_plan_id         UUID        UNIQUE NOT NULL,
  query_id              UUID        NOT NULL,
  query_text            TEXT        NOT NULL,
  query_class           TEXT        NOT NULL,
  domains               TEXT[],
  planets               TEXT[],
  houses                INTEGER[],
  forward_looking       BOOLEAN     NOT NULL DEFAULT FALSE,
  audience_tier         TEXT,
  tools_authorized      TEXT[],
  history_mode          TEXT,
  panel_mode            BOOLEAN     NOT NULL DEFAULT FALSE,
  expected_output_shape TEXT,
  graph_seed_hints      TEXT[],
  graph_traversal_depth INTEGER,
  edge_type_filter      TEXT[],
  vector_search_filter  JSONB,
  dasha_context_required BOOLEAN,
  bundle_directives     JSONB,
  router_model_id       TEXT,
  router_confidence     NUMERIC,
  manifest_fingerprint  TEXT,
  schema_version        TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_plans_query_id    ON query_plans(query_id);
CREATE INDEX IF NOT EXISTS idx_query_plans_created_at  ON query_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_plans_query_class ON query_plans(query_class);
CREATE INDEX IF NOT EXISTS idx_query_plans_domains     ON query_plans USING GIN(domains);

COMMIT;
