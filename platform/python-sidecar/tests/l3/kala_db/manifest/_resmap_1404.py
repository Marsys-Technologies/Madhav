"""Shared fixture pieces for the SR-K9-RESONANCE-MAP tests (migration 1404, branch B).

Migration 1404 is placed by the cockpit (platform/migrations is not writable by the job that authored it). Until then the SQL lives outside the
repository and the tests find it through the environment variable KALA_MIGRATION_1404_SQL; once placed, the file under platform/migrations is found
by its number. No migration text is copied into a test: every test applies the real file.
"""
import os
from pathlib import Path

import pytest

MIGRATIONS = Path(__file__).resolve().parents[5] / 'migrations'
ENV = 'KALA_MIGRATION_1404_SQL'

# Shape of the table before 1404, as migrations 459 (table, citation check), 550 (event_class foreign key) and 1080 (resolution state, qualifier)
# define it, with the stand-ins for their parents. The 901 digest spec is the one 1404 replaces.
SPEC_901_SHA = '06beb342ce8c3a88cf0df7d8d7a489abb99db40b520979d6ac9783a61970dd0a'
SPEC_901 = ('{"version":"nirmana-output-digest-spec-v1","components":[{"name":"gochara_resonance_map","relation":"gochara_resonance_map","where_equals":'
            '{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","event_class","target_type","target_ref"],"value_columns":'
            '["chart_id","event_class","target_type","target_ref","weight","classical_citation","uncited_extension","source_rule_id"]}]}')

PRE_1404_DDL_TEMPLATE = """
CREATE TABLE bg_transit_rules (id integer PRIMARY KEY);
CREATE TABLE brahma_event_ontology (event_class_id text PRIMARY KEY);
INSERT INTO brahma_event_ontology VALUES ('career'), ('wealth'), ('marriage');
CREATE TABLE gochara_resonance_map (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  weight NUMERIC NOT NULL,
  classical_citation TEXT,
  uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
  source_rule_id INTEGER REFERENCES bg_transit_rules(id),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  target_resolution_state TEXT NOT NULL DEFAULT 'resolved',
  target_qualifier TEXT,
  UNIQUE(chart_id, event_class, target_type, target_ref),
  CONSTRAINT gochara_resonance_map_citation_or_flag CHECK (classical_citation IS NOT NULL OR uncited_extension = true),
  CONSTRAINT gochara_resonance_map_event_class_fk FOREIGN KEY (event_class) REFERENCES brahma_event_ontology (event_class_id)
);
CREATE INDEX idx_gochara_resonance_chart_event ON gochara_resonance_map(chart_id, event_class);
CREATE TABLE build_run_assets (
  run_id uuid NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL, position integer, state text NOT NULL,
  started_at timestamptz, ended_at timestamptz, PRIMARY KEY (run_id, asset_id)
);
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text);
INSERT INTO asset_registry VALUES ('ka_gochara_resonance', 'SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=$1');
CREATE TABLE asset_output_digest_specs (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
  spec_sha256 text NOT NULL CHECK (spec_sha256 ~ '^[a-f0-9]{64}$'),
  spec jsonb NOT NULL CHECK (jsonb_typeof(spec) = 'object'),
  reviewed_at timestamptz NOT NULL DEFAULT now(),
  retired_at timestamptz,
  PRIMARY KEY (asset_id, spec_sha256),
  CHECK (retired_at IS NULL OR retired_at >= reviewed_at)
);
CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL;
INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ka_gochara_resonance', '{SPEC_901_SHA}', '{SPEC_901}'::jsonb);
"""
PRE_1404_DDL = PRE_1404_DDL_TEMPLATE.replace('{SPEC_901_SHA}', SPEC_901_SHA).replace('{SPEC_901}', SPEC_901)

# What migration 1404 needs besides the resonance table, for a schema that does not already carry it (the builder-role suite builds the resonance
# schema from the real 459/550/1080 files and has asset_registry from 459's own INSERT): the orchestrator's run tables, the layer head/candidate
# tables migration 1330 creates (only the columns the served view reads) and the output-digest registry holding the 901 spec.
BUILDER_WORLD_STUBS = f"""
CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY, generation text NOT NULL);
CREATE TABLE kala_layer_candidate (chart_id uuid NOT NULL, generation text NOT NULL, build_id uuid NOT NULL, state text NOT NULL DEFAULT 'building',
                                   created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (chart_id, generation));
CREATE TABLE build_runs (id uuid PRIMARY KEY, chart_id uuid);
CREATE TABLE build_run_assets (run_id uuid, asset_id text, state text, started_at timestamptz, ended_at timestamptz);
CREATE TABLE asset_output_digest_specs (
  asset_id text NOT NULL REFERENCES asset_registry(asset_id), spec_sha256 text NOT NULL, spec jsonb NOT NULL,
  reviewed_at timestamptz NOT NULL DEFAULT now(), retired_at timestamptz, PRIMARY KEY (asset_id, spec_sha256));
INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ka_gochara_resonance', '{SPEC_901_SHA}', '{SPEC_901}'::jsonb);
"""


def migration_sql() -> str:
    """The real migration 1404 text: the file named by KALA_MIGRATION_1404_SQL, else platform/migrations/1404_*.sql once the cockpit has placed it."""
    named = os.environ.get(ENV)
    if named:
        return Path(named).read_text()
    placed = sorted(MIGRATIONS.glob('1404_*.sql'))
    if placed:
        return placed[0].read_text()
    if os.environ.get('KALA_REQUIRE_DB') == '1':
        pytest.fail(f'KALA_REQUIRE_DB=1 but migration 1404 is neither placed under platform/migrations nor named by {ENV}')
    pytest.skip(f'NOT_RUN: migration 1404 is neither placed under platform/migrations nor named by {ENV}')


def reverted_sql(old: str, new: str) -> str:
    """The migration with ONE statement reverted (the planted reversion)."""
    sql = migration_sql()
    assert sql.count(old) == 1, f'reversion anchor is not unique: {old!r}'
    return sql.replace(old, new)
