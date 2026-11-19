"""Disposable-Postgres fixture for the orphan-receipts executor tests.

Table definitions are copied from the production catalog as read by `suvarna_reader` (`\\d`, 2026-10-02):
asset_provenance_receipts, asset_freshness, build_runs, build_run_assets, asset_output_digest_specs are mirrored
column-for-column with their PK, CHECK, FK and index definitions (the build_runs manifest-immutability trigger is not
mirrored: it does not touch these columns). Two tables are deliberately MINIMAL:
  * charts: only `id uuid PRIMARY KEY` (the real table carries birth data; none is reproduced here);
  * asset_registry: the columns the executor reads/writes plus the real natural_key_partition CHECKs
    (the real table has ~45 columns and a registry-edit invalidation trigger, irrelevant to a receipt DELETE).
Roles mirror production: `amjis_app` owns every table (no RLS, no policies); `data_plane_builder` holds arw on the two
receipt tables; `suvarna_reader` holds r; `adm` is a NON-superuser LOGIN CREATEROLE role standing in for the Cloud SQL
`postgres` admin (it is NOT a member of amjis_app, so the executor's transient GRANT/REVOKE path is exercised).
"""
import uuid

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "cb73cd3d-0000-4000-8000-000000000001"
W = "__whole_asset__"
DECL = "chart_facts|fact_category,ayanamsha|declared-partition-fixture"  # a declared natural_key_partition

ROLES_SQL = """
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='amjis_app') THEN CREATE ROLE amjis_app NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='data_plane_builder') THEN CREATE ROLE data_plane_builder NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='suvarna_reader') THEN CREATE ROLE suvarna_reader NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='drift_target') THEN CREATE ROLE drift_target NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='drift_member') THEN CREATE ROLE drift_member NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='adm') THEN CREATE ROLE adm LOGIN CREATEROLE; END IF;
END $$;
"""

SCHEMA_SQL = """
CREATE TABLE charts (id uuid PRIMARY KEY);
CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY,
  layer text NOT NULL,
  target_table text,
  natural_key_partition text,
  CONSTRAINT asset_registry_natural_key_partition_needs_table CHECK (natural_key_partition IS NULL OR target_table IS NOT NULL),
  CONSTRAINT asset_registry_natural_key_partition_nonblank CHECK (natural_key_partition IS NULL OR btrim(natural_key_partition) <> '')
);
CREATE TABLE asset_output_digest_specs (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
  spec_sha256 text NOT NULL,
  spec jsonb NOT NULL,
  reviewed_at timestamptz NOT NULL DEFAULT now(),
  retired_at timestamptz,
  PRIMARY KEY (asset_id, spec_sha256),
  CHECK (retired_at IS NULL OR retired_at >= reviewed_at),
  CHECK (jsonb_typeof(spec) = 'object'),
  CHECK (spec_sha256 ~ '^[a-f0-9]{64}$')
);
CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
CREATE TABLE build_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id uuid NOT NULL REFERENCES charts(id),
  scope text NOT NULL,
  scope_target text,
  action text NOT NULL,
  state text NOT NULL DEFAULT 'planned',
  plan jsonb NOT NULL,
  current_asset_id text,
  triggered_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  ended_at timestamptz,
  pause_requested_at timestamptz,
  stop_requested_at timestamptz,
  last_error text,
  plan_manifest jsonb,
  plan_manifest_digest text,
  CONSTRAINT build_runs_action_check CHECK (action = ANY (ARRAY['build','update','rebuild','cascade'])),
  CONSTRAINT build_runs_plan_manifest_digest_check CHECK (plan_manifest_digest IS NULL OR plan_manifest_digest ~ '^[0-9a-f]{64}$'),
  CONSTRAINT build_runs_plan_manifest_object_check CHECK (plan_manifest IS NULL OR jsonb_typeof(plan_manifest) = 'object'),
  CONSTRAINT build_runs_plan_manifest_pair_check CHECK ((plan_manifest IS NULL) = (plan_manifest_digest IS NULL)),
  CONSTRAINT build_runs_scope_check CHECK (scope = ANY (ARRAY['global','layer','asset','asset_set'])),
  CONSTRAINT build_runs_state_check CHECK (state = ANY (ARRAY['planned','running','paused','completed','stopped','failed']))
);
CREATE INDEX build_runs_chart_state_planned_idx ON build_runs (chart_id, created_at DESC) WHERE state = ANY (ARRAY['planned','running','paused']);
CREATE UNIQUE INDEX build_runs_one_active_per_chart_idx ON build_runs (chart_id) WHERE state = ANY (ARRAY['planned','running','paused']);
CREATE TABLE build_run_assets (
  run_id uuid NOT NULL REFERENCES build_runs(id) ON DELETE CASCADE,
  asset_id text NOT NULL,
  position integer NOT NULL,
  state text NOT NULL DEFAULT 'queued',
  started_at timestamptz,
  ended_at timestamptz,
  error text,
  output_changed boolean,
  disposition text,
  blocked_by_asset_id text,
  PRIMARY KEY (run_id, asset_id),
  CONSTRAINT build_run_assets_disposition_check CHECK (disposition IS NULL OR disposition = ANY (ARRAY['build','skip_no_delta','deferred_no_writer','withheld_protected','dormant','out_of_domain','blocked_dependency'])),
  CONSTRAINT build_run_assets_state_check CHECK (state = ANY (ARRAY['queued','building','complete','skipped','error','aborted']))
);
CREATE TABLE asset_provenance_receipts (
  asset_id text NOT NULL,
  chart_id uuid,
  scope_key text GENERATED ALWAYS AS (COALESCE(chart_id::text, '__global__')) STORED NOT NULL,
  partition_key text NOT NULL,
  receipt_version text NOT NULL,
  code_digest text,
  config_digest text,
  upstream_digest text,
  partition_digest text,
  output_digest text,
  upstream_receipts jsonb NOT NULL DEFAULT '[]'::jsonb,
  receipt_state text NOT NULL,
  unknown_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  observed_at timestamptz NOT NULL DEFAULT now(),
  build_id uuid,
  output_digest_spec_sha256 text,
  CONSTRAINT asset_provenance_receipts_pkey PRIMARY KEY (asset_id, scope_key, partition_key),
  CONSTRAINT asset_provenance_receipts_output_digest_spec_sha256_check CHECK (output_digest_spec_sha256 IS NULL OR output_digest_spec_sha256 ~ '^[a-f0-9]{64}$'),
  CONSTRAINT asset_provenance_receipts_partition_key_check CHECK (btrim(partition_key) <> ''),
  CONSTRAINT asset_provenance_receipts_receipt_state_check CHECK (receipt_state = ANY (ARRAY['proven','unknown'])),
  CONSTRAINT asset_provenance_receipts_unknown_reasons_check CHECK (jsonb_typeof(unknown_reasons) = 'array'),
  CONSTRAINT asset_provenance_receipts_upstream_receipts_check CHECK (jsonb_typeof(upstream_receipts) = 'array'),
  CONSTRAINT asset_provenance_receipts_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
  CONSTRAINT asset_provenance_receipts_build_id_fkey FOREIGN KEY (build_id) REFERENCES build_runs(id) ON DELETE SET NULL,
  CONSTRAINT asset_provenance_receipts_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE,
  CONSTRAINT asset_provenance_receipts_output_digest_spec_fk FOREIGN KEY (asset_id, output_digest_spec_sha256) REFERENCES asset_output_digest_specs(asset_id, spec_sha256) ON DELETE RESTRICT
);
CREATE INDEX asset_provenance_receipts_scope_idx ON asset_provenance_receipts (chart_id, asset_id);
CREATE TABLE asset_freshness (
  asset_id text NOT NULL,
  chart_id uuid,
  scope_key text GENERATED ALWAYS AS (COALESCE(chart_id::text, '__global__')) STORED NOT NULL,
  partition_key text NOT NULL,
  freshness_state text NOT NULL,
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  receipt_version text NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT asset_freshness_pkey PRIMARY KEY (asset_id, scope_key, partition_key),
  CONSTRAINT asset_freshness_freshness_state_check CHECK (freshness_state = ANY (ARRAY['fresh','stale','unknown'])),
  CONSTRAINT asset_freshness_partition_key_check CHECK (btrim(partition_key) <> ''),
  CONSTRAINT asset_freshness_reasons_check CHECK (jsonb_typeof(reasons) = 'array'),
  CONSTRAINT asset_freshness_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES asset_registry(asset_id) ON DELETE CASCADE,
  CONSTRAINT asset_freshness_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
);
CREATE INDEX asset_freshness_scope_state_idx ON asset_freshness (chart_id, freshness_state, asset_id);

-- ownership + grants as in production (relacl read 2026-10-02): amjis_app owns; no RLS; no policies
ALTER TABLE charts OWNER TO amjis_app;
ALTER TABLE asset_registry OWNER TO amjis_app;
ALTER TABLE asset_output_digest_specs OWNER TO amjis_app;
ALTER TABLE build_runs OWNER TO amjis_app;
ALTER TABLE build_run_assets OWNER TO amjis_app;
ALTER TABLE asset_provenance_receipts OWNER TO amjis_app;
ALTER TABLE asset_freshness OWNER TO amjis_app;
GRANT SELECT ON asset_provenance_receipts, asset_freshness, build_runs, build_run_assets, asset_registry, asset_output_digest_specs TO suvarna_reader;
GRANT SELECT, INSERT, UPDATE ON asset_provenance_receipts, asset_freshness TO data_plane_builder;
"""


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "orphan-receipts-fixture/" + name))


def sha(name):
    import hashlib
    return hashlib.sha256(name.encode()).hexdigest()


def seed_asset(cur, asset, *, declares=True, spec_active=True):
    """Register the asset (declaring a natural_key_partition or not) and give it one active digest spec."""
    cur.execute("INSERT INTO asset_registry (asset_id, layer, target_table, natural_key_partition) VALUES (%s,'ganita','chart_facts',%s)",
                (asset, DECL if declares else None))
    cur.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec, reviewed_at, retired_at) VALUES (%s,%s,'{}',%s,%s)",
                (asset, sha(asset + "/spec"), "2026-09-01T00:00:00Z", None if spec_active else "2026-09-10T00:00:00Z"))


def seed_build(cur, build, chart, created, *, state="completed", assets=(), disposition="build", asset_state="complete"):
    """One build_runs row (+ a build_run_assets row per asset). created = ISO ts; started = +10s; ended = +20s (None if in flight)."""
    cur.execute("INSERT INTO build_runs (id, chart_id, scope, action, state, plan, triggered_by, created_at, started_at, ended_at) "
                "VALUES (%s,%s,'asset','rebuild',%s,'{}','fixture', %s::timestamptz, %s::timestamptz + interval '10 seconds', "
                "CASE WHEN %s IN ('completed','failed','stopped') THEN %s::timestamptz + interval '20 seconds' END)",
                (uid(build), chart, state, created, created, state, created))
    for pos, a in enumerate(assets):
        cur.execute("INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at, ended_at, disposition) "
                    "VALUES (%s,%s,%s,%s, %s::timestamptz + interval '10 seconds', %s::timestamptz + interval '20 seconds', %s)",
                    (uid(build), a, pos, asset_state, created, created, disposition))


def seed_receipt(cur, asset, chart, partition, build, observed, *, state, fresh, spec=True):
    """A receipt + its freshness twin under `partition` (W receipts carry no digest spec, like production's W rows)."""
    unknown = [] if state == "proven" else ["output_digest_spec_unavailable", "partition_undeclared"]
    cur.execute("INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, code_digest, config_digest, "
                "upstream_digest, partition_digest, output_digest, upstream_receipts, receipt_state, unknown_reasons, observed_at, build_id, "
                "output_digest_spec_sha256) VALUES (%s,%s,%s,'nirmana-provenance-receipt-v2',%s,%s,%s,%s,%s,'[]',%s,%s::jsonb,%s,%s,%s)",
                (asset, chart, partition, sha("c" + asset), sha("g" + asset), sha("u" + asset),
                 sha("p" + asset + partition) if state == "proven" else None,
                 sha("o" + asset + partition) if state == "proven" else None,
                 state, __import__("json").dumps(unknown), observed, uid(build) if build else None,
                 sha(asset + "/spec") if (spec and state == "proven") else None))
    cur.execute("INSERT INTO asset_freshness (asset_id, chart_id, partition_key, freshness_state, reasons, receipt_version, observed_at) "
                "VALUES (%s,%s,%s,%s,%s::jsonb,'nirmana-provenance-receipt-v2',%s)",
                (asset, chart, partition, fresh, "[]" if fresh == "fresh" else '["partition_undeclared","registry_changed"]', observed))


# Timeline of the base scenario (mirrors production's shape: W row from an early build, an old declared row, then the S-L1 rebuild)
MIN_AFTER = "2026-10-05T09:00:00+00:00"   # the S-L1 dispatch instant (the --min-build-after the operator passes)


def seed_base(cur, asset="ga_positions", *, d_build="b_new", d_created="2026-10-05T10:00:00Z", d_obs="2026-10-05T10:00:30Z"):
    """The canonical scenario for `asset`: registry declares a partition; an orphan W row (unknown/stale) from an old build; a
    PROVEN+fresh declared-partition receipt from the later S-L1 rebuild. Resolver verdict before: receipt_not_proven; after: RESOLVED."""
    seed_asset(cur, asset)
    seed_build(cur, asset + "/b_w", CANON, "2026-09-07T01:07:21Z", assets=[asset])
    seed_receipt(cur, asset, CANON, W, asset + "/b_w", "2026-09-07T01:07:39Z", state="unknown", fresh="stale", spec=False)
    seed_build(cur, asset + "/" + d_build, CANON, d_created, assets=[asset])
    seed_receipt(cur, asset, CANON, DECL, asset + "/" + d_build, d_obs, state="proven", fresh="fresh")


def seed_world(cur):
    """canonical chart + another chart; ga_positions and bo_laksana as two orphan cases; bystanders that must never move:
    ga_vargas (W is the right key, RESOLVED), ga_strength (spec retired: stays unresolved), ga_gochara_like (not fresh)."""
    cur.execute("INSERT INTO charts (id) VALUES (%s), (%s)", (CANON, OTHER))
    seed_base(cur, "ga_positions")
    seed_base(cur, "bo_laksana")
    seed_asset(cur, "ga_vargas", declares=False)
    seed_build(cur, "ga_vargas/b", CANON, "2026-09-07T11:03:00Z", assets=["ga_vargas"])
    seed_receipt(cur, "ga_vargas", CANON, W, "ga_vargas/b", "2026-09-07T11:03:30Z", state="proven", fresh="fresh")
    seed_asset(cur, "ga_strength", declares=False, spec_active=False)
    seed_build(cur, "ga_strength/b", CANON, "2026-09-07T12:04:00Z", assets=["ga_strength"])
    seed_receipt(cur, "ga_strength", CANON, W, "ga_strength/b", "2026-09-07T12:04:30Z", state="proven", fresh="fresh")
    seed_asset(cur, "ka_stale_like", declares=False)
    seed_build(cur, "ka_stale_like/b", CANON, "2026-09-08T12:04:00Z", assets=["ka_stale_like"])
    seed_receipt(cur, "ka_stale_like", CANON, W, "ka_stale_like/b", "2026-09-08T12:04:30Z", state="proven", fresh="stale")
    # a W-only asset on the OTHER chart (must be untouched; exercises chart scoping)
    seed_build(cur, "ga_vargas/other", OTHER, "2026-09-07T11:03:00Z", assets=["ga_vargas"])
    seed_receipt(cur, "ga_vargas", OTHER, W, "ga_vargas/other", "2026-09-07T11:03:30Z", state="proven", fresh="fresh")
