"""SR-K9-WRITE-SCOPE, item k9-obstruction-scope: the registry and schema facts that assumed ONE partition of ``kala_obstruction``.

The migration under test is drafted (its number is allocated and the file placed by the cockpit): ``$KALA_OBSTRUCTION_SCOPE_SQL``, else
``platform/migrations/*_kala_obstruction_generation_scope.sql``. One oracle per distinct production claim, each with a "before" leg that
shows the detector can read false (root CLAUDE.md §N.8; D-OWNER-TESTS-20261016):

  M1  the migration leaves migration 245's ON DELETE CASCADE foreign key and every obstruction row (``convergence_id`` included) as it
      found them. The SET NULL switch was WITHDRAWN (review of #3864): it left served orphans that no reader can filter out and that
      turned the 670 clause (e) RED for every later build. Migration 1405 (scoped ka_sangam delete) is the prerequisite that keeps the
      cascade away from served rows
  M2  the ka_vighnakara integrity contract (migration 670, accretion clause (a)) reads TRUE when a served and a candidate partition hold
      the same windows, and still reads FALSE for a real duplicate inside ONE partition
  M3  ``count_sql`` counts the served partition only (head's generation when it holds rows, else the legacy rows)
  M4  the digest spec is replaced (1212 retired, one current spec), validates through the real ``_validate_spec`` and hashes the legacy
      partition and each generation separately: a candidate row never moves the legacy digest
  M5  the migration is idempotent and refuses a live registry text it was not written against
  M6  ph_pratikara's 1:1 tiling (migration 1259) reads the SERVED obstruction partition only, and still reads FALSE for a served gap
  M7  ka_kala_darshana's clause (e) (migration 670, live through 1356/1375) counts the SERVED obstruction partition only, and still
      reads FALSE for a summary that disagrees with it
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


def pratikara_1259():
    text = (MIGRATIONS / '1259_integrity_checks_claim_only_own_output.sql').read_text()
    match = re.search(r"SET integrity_check_sql = \$rk\$(.*?)\$rk\$\nWHERE asset_id = 'ph_pratikara'", text, re.S)
    assert match, 'migration 1259 ph_pratikara integrity text not found'
    return match.group(1)


def darshana_statement(filename):
    """The one ``UPDATE ... SET integrity_check_sql`` of ``ka_kala_darshana`` in a K6 migration (the registry is the fixture's table)."""
    chunks = [c for c in (MIGRATIONS / filename).read_text().split('\nUPDATE ')
              if 'SET integrity_check_sql' in c and "asset_id='ka_kala_darshana'" in c]
    assert len(chunks) == 1, filename
    return 'UPDATE ' + chunks[0].replace('public.asset_registry', 'asset_registry')


def darshana_670():
    text = (MIGRATIONS / '670_nirmana_l3_w3_integrity_contracts.sql').read_text()
    match = re.search(r"-- ka_kala_darshana\nUPDATE asset_registry SET integrity_check_sql = \$ck\$(.*?)\$ck\$\n WHERE asset_id = 'ka_kala_darshana';", text, re.S)
    assert match, 'migration 670 ka_kala_darshana integrity text not found'
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
        # the two downstream checks that read kala_obstruction, at their LIVE text: 1259 for ph_pratikara; for ka_kala_darshana the
        # 670 text wrapped by 1354, 1356 and 1375 (replayed from the real migration files)
        conn.execute('INSERT INTO asset_registry VALUES (%s, %s, NULL)', ('ph_pratikara', pratikara_1259()))
        conn.execute('INSERT INTO asset_registry VALUES (%s, %s, NULL)', ('ka_kala_darshana', darshana_670()))
        for filename in ('1354_k6_darshana_candidate.sql', '1356_k6_read_model_build_scoped_detectors.sql'):
            conn.execute(darshana_statement(filename))
        conn.execute((MIGRATIONS / '1375_k6_integrity_chart_build_binding.sql').read_text()
                     .replace("ARRAY['ka_kalasutra','ka_kala_darshana','ka_jivana_parva']", "ARRAY['ka_kala_darshana']")
                     .replace('public.asset_registry', 'asset_registry'))
        conn.execute('CREATE TABLE phala_anchors (anchor_id bigserial PRIMARY KEY)')
        conn.execute('CREATE TABLE phala_mitigation (mitigation_id bigserial PRIMARY KEY, chart_id uuid, obstruction_id bigint, '
                     'obstruction_severity text, linked_anchor_id bigint)')
        conn.execute('CREATE TABLE kala_darshana (chart_id uuid, convergence_id bigint, obstruction_summary jsonb, narrative jsonb)')
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

FULL_ROWS = 'SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id'      # every column: convergence_id is the one a convergence-side change moves
FK_ACTION = "SELECT confdeltype FROM pg_constraint WHERE conrelid = 'kala_obstruction'::regclass AND contype = 'f'"


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


def test_m1_the_migration_keeps_the_cascade_and_changes_no_obstruction_row(mdb):
    conv = served_world(mdb)
    before = [r[0] for r in mdb.execute(FULL_ROWS).fetchall()]
    assert {row['convergence_id'] for row in before} == {conv}, 'the served rows must be convergence-anchored or the comparison is vacuous'
    mdb.execute(migration_sql())
    assert [r[0] for r in mdb.execute(FULL_ROWS).fetchall()] == before, 'the migration rewrote or deleted an obstruction row'
    assert mdb.execute(FK_ACTION).fetchall() == [('c',)], 'the convergence foreign key must stay ON DELETE CASCADE (SET NULL was withdrawn)'


def test_m1_after_the_migration_a_convergence_delete_leaves_no_served_orphan(mdb):
    served_world(mdb)
    mdb.execute(migration_sql())
    mdb.execute('DELETE FROM kala_convergence WHERE chart_id = %s', (CHART,))
    served = mdb.execute("SELECT count(*) FROM kala_obstruction WHERE convergence_id IS NULL AND source_citation LIKE '%%:conv=%%'").fetchone()[0]
    assert served == 0, 'a convergence-anchored row survived with a NULL link and a citation of the deleted window'


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
    snapshot = "SELECT asset_id, integrity_check_sql, count_sql FROM asset_registry ORDER BY asset_id"
    state = mdb.execute(snapshot).fetchall()
    mdb.execute(migration_sql())                                              # a re-run changes nothing, for all three assets
    assert mdb.execute(snapshot).fetchall() == state
    assert mdb.execute('SELECT count(*) FROM asset_output_digest_specs WHERE retired_at IS NULL').fetchone()[0] == 1
    mdb.execute("UPDATE asset_registry SET count_sql = 'SELECT 1'")
    with pytest.raises(psycopg.errors.RaiseException, match='count_sql'):
        mdb.execute(migration_sql())


@pytest.mark.parametrize('asset', ['ph_pratikara', 'ka_kala_darshana'])
def test_m5_a_downstream_check_text_the_migration_was_not_written_against_is_refused_not_skipped(mdb, asset):
    mdb.execute("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || ' ' WHERE asset_id = %s", (asset,))
    with pytest.raises(psycopg.errors.RaiseException, match=asset):
        mdb.execute(migration_sql())


# ── M6 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def pratikara_world(conn):
    """A served legacy obstruction row with its mitigation: the 1:1 tiling holds."""
    conv = convergence(conn)
    obstruction(conn, None, conv)
    legacy = conn.execute('SELECT id FROM kala_obstruction').fetchone()[0]
    conn.execute("INSERT INTO phala_mitigation (chart_id, obstruction_id, obstruction_severity) VALUES (%s, %s, 'high')", (CHART, legacy))
    return conv


def pratikara_check(conn):
    return conn.execute(conn.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'ph_pratikara'").fetchone()[0]).fetchone()[0]


def test_m6_before_the_migration_an_unserved_candidate_row_reads_as_an_unmitigated_obstruction(mdb):
    conv = pratikara_world(mdb)
    assert pratikara_check(mdb) is True
    obstruction(mdb, CAND, conv)            # what a candidate-bound ka_vighnakara writes; ph_pratikara mitigates the served partition only
    assert pratikara_check(mdb) is False, 'the premise: 1259 tiles every partition'


def test_m6_after_the_migration_the_tiling_reads_the_served_partition_only_and_still_detects_a_served_gap(mdb):
    conv = pratikara_world(mdb)
    mdb.execute(migration_sql())
    obstruction(mdb, CAND, conv)
    assert pratikara_check(mdb) is True, 'an unserved candidate row has no mitigation by design'
    obstruction(mdb, None, conv, otype='gandanta')           # a SERVED row nobody mitigated
    assert pratikara_check(mdb) is False, 'a genuine tiling gap in the served partition must still be detected'


# ── M7 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def darshana_world(conn):
    """One window, one served legacy obstruction row, and the darshana row whose summary mirrors it entry for entry (670 clause (e))."""
    conv = convergence(conn)
    obstruction(conn, None, conv)
    summary = [{'type': 'malefic_transit', 'severity': 'severe', 'override_score': 0.36}]
    conn.execute('INSERT INTO kala_darshana VALUES (%s, %s, %s, %s)',
                 (CHART, conv, Jsonb(summary), Jsonb({'caution': 'beware the malefic_transit window'})))
    return conv


def clause_e(conn):
    """Clause (e) of the LIVE ka_kala_darshana text, executed on its own (the full text also needs the K6 candidate tables)."""
    text = conn.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'ka_kala_darshana'").fetchone()[0]
    start = text.index('  AND NOT EXISTS (\n    SELECT 1 FROM kala_darshana d\n    WHERE jsonb_array_length')
    return conn.execute('SELECT true\n' + text[start:text.index('  -- (f)')]).fetchone()[0]


def test_m7_before_the_migration_a_candidate_row_on_a_shared_window_reads_as_a_summary_mismatch(mdb):
    conv = darshana_world(mdb)
    assert clause_e(mdb) is True
    obstruction(mdb, CAND, conv)            # a candidate-bound ka_vighnakara re-detected the same window
    assert clause_e(mdb) is False, 'the premise: 670 clause (e) counts every partition'


def test_m7_after_the_migration_clause_e_counts_the_served_partition_only_and_still_detects_a_summary_mismatch(mdb):
    conv = darshana_world(mdb)
    mdb.execute(migration_sql())
    obstruction(mdb, CAND, conv)
    assert clause_e(mdb) is True, 'a candidate row is not part of the served summary'
    obstruction(mdb, None, conv, otype='gandanta')           # a SERVED row the summary does not mirror
    assert clause_e(mdb) is False, 'a served summary that disagrees with the served rows must still be detected'
