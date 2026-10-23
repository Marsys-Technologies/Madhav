"""Migration 1400 (ka_yojaka output-digest spec v3) installed for real, on top of 1024 and 1399.

K9 round 4, D6: an identical rebuild must not read as a changed output. test_k9_digest_generation_scope.py proves the reader
(`newest_candidate_generation`) against a planted spec; this file proves the SHIPPED migration installs the spec that
reader needs, retires v2 without editing it, is idempotent, and that the digest it governs behaves as D6 requires.

Claims, one oracle each (the property is the owner's requirement OWNER-K9-RESTORE-20261021 D6; row values are PLANTED
labels, B.10):
  M1 1400 leaves exactly one current ka_yojaka spec; 1024 and 1399 are retired, their content untouched
  M2 the installed spec is the one the reader validates, its sha is the real canonical digest, and the generation is scope
  M3 re-running 1400 changes nothing (idempotent)
  M4 1400 refuses to run when the live spec is neither v2 nor v3 (it never replaces a spec it did not review)
  D1 under the installed spec an identical rebuild (new generation, same rows) digests identically
  D2 under the installed spec a real content change digests differently
"""
import json
import os
import re
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
import pytest

from pipeline.orchestrator import output_digest
from pipeline.orchestrator.provenance import canonical_digest

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
MIGRATIONS = Path(__file__).resolve().parents[5] / 'migrations'
V1 = MIGRATIONS / '1024_nirmana_l3_ka_yojaka_output_digest_spec.sql'


def _migration(env: str, name: str) -> str:
    """The migration text: $<env> (a draft not yet placed), else the placed file under platform/migrations."""
    path = Path(os.environ.get(env) or MIGRATIONS / name)
    if not path.exists():
        pytest.skip(f'NOT_RUN: {name} absent (set {env})')
    return path.read_text()


def v2_sql() -> str:
    return _migration('KA_YOJAKA_DIGEST_V2_SQL', '1399_ka_yojaka_output_digest_v2.sql')


def v3_sql() -> str:
    return _migration('KA_YOJAKA_DIGEST_V3_SQL', '1400_ka_yojaka_output_digest_v3.sql')


def spec_in(sql: str) -> dict:
    return json.loads(re.search(r"'(\{\"version\".*?\})'::jsonb", sql, re.S).group(1))


@pytest.fixture(scope='module')
def database(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as c:
        c.execute((MIGRATIONS / '1330_kala_layer_manifest_candidates.sql').read_text()
                  .split('-- A separately dispatched verifier')[0])
        c.execute('CREATE TABLE asset_output_digest_specs (asset_id TEXT NOT NULL, spec_sha256 TEXT NOT NULL, '
                  'spec JSONB NOT NULL, reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(), retired_at TIMESTAMPTZ, '
                  'PRIMARY KEY (asset_id, spec_sha256))')
        c.execute('CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) '
                  'WHERE retired_at IS NULL')
        c.execute('CREATE TABLE kala_activation_predicates (chart_id uuid, ayanamsha_id text, signal_id text, '
                  'signature_class text, dasha_eligibility_rule_jsonb jsonb, transit_trigger_jsonb jsonb, '
                  'strength_affliction_hook_jsonb jsonb, derivation_ledger_jsonb jsonb, generation text, '
                  'mechanism_route text, conclusion_state_jsonb jsonb, mechanism_id text, event_class_id text)')
    return isolated_kala_db_dsn


@pytest.fixture
def cur(database):
    with psycopg.connect(database, row_factory=dict_row) as c:
        c.execute('TRUNCATE kala_activation_predicates, kala_layer_candidate_grain, kala_layer_candidate CASCADE')
        c.execute('TRUNCATE asset_output_digest_specs')
        yield c.cursor()
        c.rollback()


def specs(cur):
    cur.execute("SELECT spec_sha256, spec, retired_at IS NULL AS current FROM asset_output_digest_specs "
                "WHERE asset_id = 'ka_yojaka' ORDER BY spec_sha256")
    return cur.fetchall()


def install_1024_and_1399(cur):
    cur.execute(V1.read_text())
    cur.execute(v2_sql())


def install_all(cur):
    install_1024_and_1399(cur)
    cur.execute(v3_sql())


def test_1400_leaves_one_current_spec_and_retires_1024_and_1399_untouched(cur):
    v1_spec, v2_spec = spec_in(V1.read_text()), spec_in(v2_sql())
    install_all(cur)
    rows = specs(cur)
    assert len(rows) == 3 and [r['current'] for r in rows].count(True) == 1
    by_sha = {r['spec_sha256']: r for r in rows}
    assert by_sha[canonical_digest(v1_spec)]['current'] is False and by_sha[canonical_digest(v1_spec)]['spec'] == v1_spec
    assert by_sha[canonical_digest(v2_spec)]['current'] is False and by_sha[canonical_digest(v2_spec)]['spec'] == v2_spec
    assert by_sha[canonical_digest(spec_in(v3_sql()))]['current'] is True


def test_the_installed_spec_is_valid_hashed_by_the_real_function_and_scopes_the_generation(cur):
    install_all(cur)
    loaded = output_digest.load_output_digest_spec(cur, 'ka_yojaka')
    assert loaded.spec_sha256 == canonical_digest(spec_in(v3_sql()))
    components = loaded.spec['components']
    assert [c['name'] for c in components] == ['kap_candidate_classed', 'kap_candidate_classless']
    assert all(c['newest_candidate_generation'] == 'generation' for c in components)
    assert all('generation' not in c['key_columns'] + c['value_columns'] for c in components)


def test_running_1400_again_changes_nothing(cur):
    install_all(cur)
    before = specs(cur)
    cur.execute('SELECT retired_at FROM asset_output_digest_specs ORDER BY spec_sha256')
    retired = cur.fetchall()
    cur.execute(v3_sql())
    assert specs(cur) == before
    cur.execute('SELECT retired_at FROM asset_output_digest_specs ORDER BY spec_sha256')
    assert cur.fetchall() == retired


@pytest.mark.parametrize('live', ['only_1024', 'foreign_spec'])
def test_1400_refuses_when_the_live_spec_is_neither_v2_nor_v3(cur, live):
    if live == 'only_1024':
        cur.execute(V1.read_text())
    else:
        cur.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) "
                    "VALUES ('ka_yojaka', %s, '{}'::jsonb)", ('f' * 64,))
    cur.connection.commit()        # the refusal rolls the migration back; the setup must survive it
    before = specs(cur)
    with pytest.raises(psycopg.errors.RaiseException, match='neither v2'):
        cur.execute(v3_sql())
    cur.connection.rollback()
    cur.execute('SELECT 1')
    assert specs(cur) == before


# --- the digest the installed spec governs --------------------------------------------------------------------

ROWS = [('M1', 'EC1', 'sig-a', 'YOGA'), ('M2', 'EC1', None, 'CLASSIFY_RESIDUAL'), ('M3', None, 'sig-c', 'YOGA')]


def write_generation(cur, generation, *, minutes, change=None):
    cur.execute("INSERT INTO kala_layer_candidate (chart_id, generation, build_id, model_digest, rule_registry_version, "
                "conventions, created_at) VALUES (%s,%s,%s,'fixture','fixture','{}'::jsonb, now() + %s * interval '1 minute')",
                (CHART, generation, uuid.uuid4(), minutes))
    for mechanism, event_class, signal, signature in ROWS:
        ledger = {'mechanism': mechanism, 'witness': 'changed' if change == mechanism else 'planted'}
        cur.execute("INSERT INTO kala_activation_predicates (chart_id, ayanamsha_id, signal_id, signature_class, "
                    "dasha_eligibility_rule_jsonb, transit_trigger_jsonb, strength_affliction_hook_jsonb, "
                    "derivation_ledger_jsonb, generation, mechanism_route, conclusion_state_jsonb, mechanism_id, "
                    "event_class_id) VALUES (%s,'lahiri',%s,%s,'{}','{}','{}',%s::jsonb,%s,'admitted','{}',%s,%s)",
                    (CHART, signal, signature, json.dumps(ledger), generation, mechanism, event_class))


def digest(cur):
    value, _ = output_digest.compute_output_digest(cur, asset_id='ka_yojaka')
    return value


def test_an_identical_rebuild_digests_identically_under_the_installed_spec(cur):
    install_all(cur)
    write_generation(cur, 'candidate:first', minutes=1)
    before = digest(cur)
    write_generation(cur, 'candidate:second', minutes=2)
    assert digest(cur) == before


def test_a_real_change_digests_differently_under_the_installed_spec(cur):
    install_all(cur)
    write_generation(cur, 'candidate:first', minutes=1)
    before = digest(cur)
    write_generation(cur, 'candidate:second', minutes=2, change='M2')
    assert digest(cur) != before
