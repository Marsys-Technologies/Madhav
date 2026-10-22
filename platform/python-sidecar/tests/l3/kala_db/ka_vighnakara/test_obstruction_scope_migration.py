"""SR-K9-WRITE-SCOPE, item k9-obstruction-scope: the registry and schema facts that assumed ONE partition of ``kala_obstruction``.

The migration under test is drafted (its number is allocated and the file placed by the cockpit): ``$KALA_OBSTRUCTION_SCOPE_SQL``, else
``platform/migrations/*_kala_obstruction_generation_scope.sql``. One oracle per distinct production claim, each with a "before" leg that
shows the detector can read false (root CLAUDE.md §N.8; D-OWNER-TESTS-20261016):

  M1  after the migration a K9 run's whole-chart delete of ``kala_convergence`` no longer deletes the served obstruction rows through
      the foreign key (migration 245 made it ON DELETE CASCADE); the rows survive with a NULL link
  M2  the ka_vighnakara integrity contract (migration 670, accretion clause (a)) reads TRUE when a served and a candidate partition hold
      the same windows, and still reads FALSE for a real duplicate inside ONE partition
  M3  ``count_sql`` counts the served partition only (head's generation when it holds rows, else the legacy rows)
  M4  the digest spec is replaced (1212 retired, one current spec), validates through the real ``_validate_spec`` and hashes the legacy
      partition and each generation separately: a candidate row never moves the legacy digest
  M5  the migration is idempotent and refuses a live registry text it was not written against
"""
import os
import re
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[4]          # platform/python-sidecar
MIGRATIONS = ROOT.parent / 'migrations'
CHART = '482012f1-710e-4a25-994a-93821f5871aa'      # the digest spec is pinned to the canonical chart
HEAD, CAND = 'published-head-1', 'candidate:00000000-0000-0000-0000-0000000000b1'
OLD_COUNT_SQL = 'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1'


def migration_sql():
    path = os.environ.get('KALA_OBSTRUCTION_SCOPE_SQL')
    found = [Path(path)] if path else sorted(MIGRATIONS.glob('*_kala_obstruction_generation_scope.sql'))
    if not found or not found[0].exists():
        pytest.skip('NOT_RUN: the kala_obstruction generation-scope migration is not placed (set KALA_OBSTRUCTION_SCOPE_SQL)')
    return found[0].read_text()


def integrity_670():
    text = (MIGRATIONS / '670_nirmana_l3_w3_integrity_contracts.sql').read_text()
    match = re.search(r"-- ka_vighnakara\nUPDATE asset_registry SET integrity_check_sql = \$ck\$(.*?)\$ck\$\n WHERE asset_id = 'ka_vighnakara';", text, re.S)
    assert match, 'migration 670 ka_vighnakara integrity text not found'
    return match.group(1)


def spec_1212():
    text = (MIGRATIONS / '1212_nirmana_l3_ka_vighnakara_output_digest_spec.sql').read_text()
    return re.search(r"'ka_vighnakara',\n  '([0-9a-f]{64})',\n  '(\{.*?\})'::jsonb", text, re.S).groups()


@pytest.fixture
def mdb(kala_db_dsn):
    # The digest reader and the migration name their relations `public.<table>`: the fixture lives in the session's disposable
    # database and is rolled back, never committed (as the 1399 tests do).
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute('CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text, count_sql text)')
        conn.execute('CREATE TABLE build_runs (id uuid PRIMARY KEY, state text)')
        conn.execute('CREATE TABLE build_run_assets (run_id uuid, asset_id text)')
        conn.execute('CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY, generation text)')
        conn.execute('CREATE TABLE kala_convergence (convergence_id bigserial PRIMARY KEY, chart_id uuid NOT NULL, peak_date date)')
        # migration 245's table shape (+ the K0a generation column of 1338): the FK is ON DELETE CASCADE
        conn.execute('''CREATE TABLE kala_obstruction (id bigserial PRIMARY KEY, chart_id uuid NOT NULL,
            convergence_id bigint REFERENCES kala_convergence(convergence_id) ON DELETE CASCADE, signal_id uuid,
            obstruction_type text NOT NULL, severity text NOT NULL, severity_score double precision NOT NULL,
            override_score double precision NOT NULL DEFAULT 0, obstruction_detail jsonb NOT NULL DEFAULT '{}',
            source_citation text NOT NULL DEFAULT 'ka_vighnakara:v1.0', generation text)''')
        conn.execute('''CREATE TABLE asset_output_digest_specs (asset_id TEXT NOT NULL, spec_sha256 TEXT NOT NULL, spec JSONB NOT NULL,
            reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(), retired_at TIMESTAMPTZ, PRIMARY KEY (asset_id, spec_sha256))''')
        conn.execute('CREATE UNIQUE INDEX asset_output_digest_specs_one_current ON asset_output_digest_specs (asset_id) WHERE retired_at IS NULL')
        conn.execute('INSERT INTO asset_registry VALUES (%s, %s, %s)', ('ka_vighnakara', integrity_670(), OLD_COUNT_SQL))
        sha, spec = spec_1212()
        conn.execute('INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES (%s, %s, %s::text::jsonb)', ('ka_vighnakara', sha, spec))
        yield conn
        conn.rollback()


def convergence(conn, peak='2030-03-03'):
    return conn.execute('INSERT INTO kala_convergence (chart_id, peak_date) VALUES (%s, %s) RETURNING convergence_id', (CHART, peak)).fetchone()[0]


def obstruction(conn, generation, conv, *, signal=None, otype='malefic_transit', score=0.8, override=0.36, peak='2030-03-03'):
    """A row exactly as the legacy writer shapes it (migration 670 clauses (c)-(e)): conv-anchored when ``conv`` is set, dasha-anchored otherwise."""
    detail = {'peak_date': peak} if conv is not None else {'peak_date': peak, 'anchor': 'dasha_timeline'}
    citation = f'ka_vighnakara:v2.0:conv={conv}' if conv is not None else 'ka_vighnakara:v2.0:dasha_anchor'
    severity = 'severe' if score >= 0.70 else 'moderate' if score >= 0.40 else 'mild'
    conn.execute('INSERT INTO kala_obstruction (chart_id, convergence_id, signal_id, obstruction_type, severity, severity_score, override_score, '
                 'obstruction_detail, source_citation, generation) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                 (CHART, conv, signal, otype, severity, score, override, Jsonb(detail), citation, generation))


def integrity(conn):
    return conn.execute(conn.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'ka_vighnakara'").fetchone()[0]).fetchone()[0]


# ── M1 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def served_world(conn):
    conv = convergence(conn)
    conn.execute('INSERT INTO kala_layer_head VALUES (%s, %s)', (CHART, HEAD))
    obstruction(conn, None, conv)
    obstruction(conn, HEAD, conv, otype='gandanta')
    return conv


def test_m1_before_the_migration_the_convergence_delete_cascades_into_the_served_rows(mdb):
    conv = served_world(mdb)
    mdb.execute('DELETE FROM kala_convergence WHERE convergence_id = %s', (conv,))
    assert mdb.execute('SELECT count(*) FROM kala_obstruction').fetchone()[0] == 0, 'the premise: migration 245 cascades'


def test_m1_after_the_migration_the_convergence_delete_leaves_every_served_row(mdb):
    conv = served_world(mdb)
    mdb.execute(migration_sql())
    before = mdb.execute("SELECT id, chart_id, signal_id, obstruction_type, severity, severity_score, override_score, obstruction_detail, "
                         "source_citation, generation FROM kala_obstruction ORDER BY id").fetchall()
    mdb.execute('DELETE FROM kala_convergence WHERE chart_id = %s', (CHART,))     # ka_sangam's whole-chart delete
    after = mdb.execute("SELECT id, chart_id, signal_id, obstruction_type, severity, severity_score, override_score, obstruction_detail, "
                        "source_citation, generation FROM kala_obstruction ORDER BY id").fetchall()
    assert after == before and len(after) == 2, 'a served obstruction row was deleted or changed by the convergence delete'
    assert mdb.execute('SELECT count(*) FROM kala_obstruction WHERE convergence_id IS NOT NULL').fetchone()[0] == 0
    assert conv


# ── M2 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def two_partitions(conn):
    conv = convergence(conn)
    obstruction(conn, None, conv)
    obstruction(conn, CAND, conv)          # the candidate build re-detected the same window
    obstruction(conn, None, None, signal=str(uuid.uuid4()), peak='2031-01-01')
    obstruction(conn, CAND, None, signal=conn.execute('SELECT signal_id FROM kala_obstruction WHERE convergence_id IS NULL').fetchone()[0], peak='2031-01-01')


def test_m2_before_the_migration_two_partitions_read_as_accretion(mdb):
    two_partitions(mdb)
    assert integrity(mdb) is False, 'the premise: migration 670 groups across partitions'


def test_m2_after_the_migration_two_partitions_pass_and_a_real_duplicate_still_fails(mdb):
    two_partitions(mdb)
    mdb.execute(migration_sql())
    assert integrity(mdb) is True
    conv = mdb.execute('SELECT convergence_id FROM kala_convergence').fetchone()[0]
    obstruction(mdb, CAND, conv)           # the same window twice inside ONE partition
    assert integrity(mdb) is False, 'accretion inside one partition must still be detected'


# ── M3 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def served_count(conn):
    text = conn.execute("SELECT count_sql FROM asset_registry WHERE asset_id = 'ka_vighnakara'").fetchone()[0]
    return conn.execute(text.replace('$1', f"'{CHART}'::uuid")).fetchone()[0]


def test_m3_count_sql_counts_the_served_partition(mdb):
    conv = convergence(mdb)
    for generation in (None, None, CAND):
        obstruction(mdb, generation, conv)
    assert served_count(mdb) == 3, 'the premise: the old count adds every partition'
    mdb.execute(migration_sql())
    assert served_count(mdb) == 2                                            # no head: the legacy rows
    mdb.execute('INSERT INTO kala_layer_head VALUES (%s, %s)', (CHART, HEAD))
    assert served_count(mdb) == 2                                            # a head with no obstruction rows: still the legacy rows
    obstruction(mdb, HEAD, conv)
    assert served_count(mdb) == 1                                            # the head holds rows: it replaces the legacy rows


# ── M4 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def digest(conn):
    from pipeline.orchestrator.output_digest import compute_output_digest
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        return compute_output_digest(cur, asset_id='ka_vighnakara')


def test_m4_the_new_digest_spec_replaces_1212_validates_and_keeps_the_legacy_partition_apart(mdb):
    from pipeline.orchestrator.output_digest import _validate_spec
    old_sha, _ = spec_1212()
    mdb.execute(migration_sql())
    rows = mdb.execute("SELECT spec_sha256, spec, retired_at IS NULL FROM asset_output_digest_specs WHERE asset_id = 'ka_vighnakara' "
                       "ORDER BY retired_at IS NULL").fetchall()
    assert [(sha == old_sha, current) for sha, _, current in rows] == [(True, False), (False, True)], '1212 must be retired, not edited'
    sha, spec, _ = rows[1]
    _validate_spec('ka_vighnakara', spec, sha)                                # the real validator and canonical digest
    assert [c['name'] for c in spec['components']] == ['kala_obstruction_legacy', 'kala_obstruction_candidate']
    conv = convergence(mdb)
    sig = str(uuid.uuid4())
    obstruction(mdb, None, None, signal=sig)
    legacy_only = digest(mdb)
    obstruction(mdb, CAND, None, signal=sig)                                  # a candidate row appears
    after_candidate = digest(mdb)
    assert after_candidate != legacy_only, 'the digest must be sensitive to the candidate rows'
    assert mdb.execute('SELECT 1').fetchone() and conv
    # ...but the LEGACY component, on its own, is byte-identical with or without candidate rows
    from pipeline.orchestrator.output_digest import _component_statement
    legacy_component = spec['components'][0]
    statement = _component_statement(legacy_component)
    with mdb.cursor() as cur:
        cur.execute(statement, [CHART])
        with_candidate = cur.fetchall()
        cur.execute('DELETE FROM kala_obstruction WHERE generation IS NOT NULL')
        cur.execute(statement, [CHART])
        assert cur.fetchall() == with_candidate, 'a candidate row moved the legacy partition digest'


# ── M5 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_m5_the_migration_is_idempotent_and_refuses_a_registry_text_it_was_not_written_against(mdb):
    mdb.execute(migration_sql())
    state = mdb.execute("SELECT integrity_check_sql, count_sql FROM asset_registry").fetchone()
    mdb.execute(migration_sql())                                              # a re-run changes nothing
    assert mdb.execute("SELECT integrity_check_sql, count_sql FROM asset_registry").fetchone() == state
    assert mdb.execute('SELECT count(*) FROM asset_output_digest_specs WHERE retired_at IS NULL').fetchone()[0] == 1
    mdb.execute("UPDATE asset_registry SET count_sql = 'SELECT 1'")
    with pytest.raises(psycopg.errors.RaiseException, match='count_sql'):
        mdb.execute(migration_sql())
