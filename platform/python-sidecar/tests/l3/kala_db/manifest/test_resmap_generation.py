"""SR-K9-RESONANCE-MAP branch B (migration 1404): gochara_resonance_map is generation-scoped, so a K9 candidate run never touches the rows serving reads.

One doctrine-grounded oracle per distinct production claim, each with ONE planted reversion that fails (root CLAUDE.md §N.8). Source of the rules: §N.3
(L1+ idempotency is a per-chart delete-then-insert scoped to the natural key: with a generation in the key, the scope is (chart, generation)), §N.6.3 (a served
verdict layer is never empty when grounding data exists; an honest gap is reported), the sealed K9 teardown rule that served rows survive a failed candidate
(SR-K9-PUBLISHABLE D8; rebuild_control.py), and the measurement RESONANCE_MAP_READERS.md (verdict READ). The migration under test is the REAL file (see _resmap_1404.py).

  M1  backfill: existing rows are stamped with the MEASURED producing generation (a published candidate's ka_gochara_resonance build window contains the rows' computed_at);
      rows no published candidate produced stay 'legacy'; a re-run stamps nothing, not even a row written later as 'legacy'
  M2  the backfill refuses on ambiguity (two producers match one computed_at; one chart's rows have different producers) and changes nothing
  M3  key: the same natural key may exist in two generations of one chart; inside one generation it still conflicts
  S1  served view: an unpublished candidate generation is never served
  S2  served view: the chart head generation, when it holds rows, is served (even when a newer published generation exists)
  S3  served view: a head without resonance rows falls back to the latest published generation that has rows; with none, to 'legacy'
  G1  the view is readable by every grantee of the base table
  R1  registry: count_sql counts the served rows; R2 the output-digest spec is replaced by a valid one that covers every generation
  W1  writer: a candidate-bound run replaces only its own partition (served rows byte-identical; a second run is idempotent)
  W2  writer: a run bound to the published head is refused; W3 a run bound to no candidate writes the 'legacy' partition
  W4  writer: the prior-build yoga set of a first candidate run is the served set (a yoga that stopped firing is still named)
  P1  reader: fetch_resonance_targets / event_classes_query return the served rows; with a generation, that generation's own rows (the candidate build)
  P2  reader: the ka_kshetra corpus pin fingerprints the served rows only
"""
import json
import types
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from tests.l3.kala_db.manifest._resmap_1404 import PRE_1404_DDL, migration_sql, reverted_sql
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, REAL, REVERTED  # noqa: F401
from tests.l3.kala_db.manifest.test_publication_ops import db, prepare  # noqa: F401  (db is a fixture)

T0 = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
MIN = timedelta(minutes=1)
CHART_A, CHART_B, CHART_C, CHART_D, CHART_X = (str(uuid.uuid4()) for _ in range(5))


@pytest.fixture
def pre(db):
    """The schema as it is before 1404 (migrations 459/550/1080 + the orchestrator's run tables)."""
    db.execute(PRE_1404_DDL)
    db.commit()
    return db


def apply(conn, sql=None):
    """Apply the migration; a database error is an AssertionError of the oracle (a reverted migration that cannot run is a failed oracle, not a harness crash)."""
    try:
        conn.execute(sql if sql is not None else migration_sql())
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise AssertionError(f'migration 1404 did not apply: {exc}') from exc


def refuses(conn, sql, word):
    """The migration must raise a refusal naming ``word``; a migration that applies is an AssertionError of the oracle."""
    try:
        apply(conn, sql)
    except AssertionError as exc:
        assert word in str(exc), f'refused for another reason: {exc}'
        return
    raise AssertionError('the migration applied where it must refuse')


def add_rows(conn, chart, refs, at, *, generation=None, event_class='career'):
    columns = 'chart_id, event_class, target_type, target_ref, weight, classical_citation, computed_at'
    marks = '%s, %s, %s, %s, %s, %s, %s'
    for ref in refs:
        values = [chart, event_class, 'bhava', ref, 1, 'BPHS', at]
        if generation is not None:
            conn.execute(f'INSERT INTO gochara_resonance_map ({columns}, generation) VALUES ({marks}, %s)', values + [generation])
        else:
            conn.execute(f'INSERT INTO gochara_resonance_map ({columns}) VALUES ({marks})', values)
    conn.commit()


def window(conn, run_id, start, end, *, state='complete'):
    conn.execute("INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at, ended_at) VALUES (%s, 'ka_gochara_resonance', 1, %s, %s, %s)",
                 (run_id, state, start, end))
    conn.commit()


def candidate(conn, chart, generation, *, state='published'):
    c = prepare(conn, generation, chart=chart)
    if state != 'building':
        conn.execute('UPDATE kala_layer_candidate SET state = %s WHERE chart_id = %s AND generation = %s', (state, chart, generation))
        conn.commit()
    return c


def ordinary_run(conn, chart):
    run_id = str(uuid.uuid4())
    conn.execute("INSERT INTO build_runs VALUES (%s, %s, 'layer', 'L3', 'rebuild', '[]'::jsonb, 'completed', NULL, NULL)", (run_id, chart))
    conn.commit()
    return run_id


def generations(conn, chart):
    return sorted(r[0] for r in conn.execute('SELECT DISTINCT generation FROM gochara_resonance_map WHERE chart_id = %s', (chart,)).fetchall())


def dump(conn):
    """Every column of every row except the new one, in a total order: the byte-level state of the existing content."""
    cols = 'id, chart_id, event_class, target_type, target_ref, weight, classical_citation, uncited_extension, source_rule_id, computed_at, target_resolution_state, target_qualifier'
    return conn.execute(f'SELECT {cols} FROM gochara_resonance_map ORDER BY id').fetchall()


# ---------------------------------------------------------------- M1: the measured backfill


def m1(sql, conn, tmp_path=None):
    a = candidate(conn, CHART_A, 'gen_a')                  # published candidate: its build window contains the rows
    window(conn, a.build_id, T0, T0 + 10 * MIN)
    add_rows(conn, CHART_A, ['1', '2', '3'], T0 + MIN)
    run_b = ordinary_run(conn, CHART_B)                     # an ordinary rebuild (no candidate) produced these
    window(conn, run_b, T0, T0 + 10 * MIN)
    add_rows(conn, CHART_B, ['1', '2'], T0 + MIN)
    c = candidate(conn, CHART_C, 'gen_c', state='complete')  # a candidate that was never published produced these
    window(conn, c.build_id, T0, T0 + 10 * MIN)
    add_rows(conn, CHART_C, ['1'], T0 + MIN)
    add_rows(conn, CHART_D, ['1', '2'], T0 + MIN)           # no build record at all
    before = dump(conn)
    apply(conn, sql)
    assert generations(conn, CHART_A) == ['gen_a'], 'rows produced by a published candidate are not stamped with its generation'
    assert [generations(conn, ch) for ch in (CHART_B, CHART_C, CHART_D)] == [['legacy']] * 3
    assert dump(conn) == before, 'the backfill changed something other than the generation'
    # re-run: nothing changes; a row written later as 'legacy' inside the same window is not re-stamped
    add_rows(conn, CHART_A, ['9'], T0 + 2 * MIN, generation='legacy')
    snapshot = conn.execute('SELECT id, generation FROM gochara_resonance_map ORDER BY id').fetchall()
    apply(conn, sql)
    assert conn.execute('SELECT id, generation FROM gochara_resonance_map ORDER BY id').fetchall() == snapshot


@BOTH
def test_m1_existing_rows_are_stamped_with_the_measured_producing_generation(pre, reverted):
    # reversion: every row is stamped 'legacy' whatever produced it
    if reverted:
        with pytest.raises(AssertionError):
            m1(reverted_sql('SET generation = o.generation', "SET generation = 'legacy'"), pre)
    else:
        m1(migration_sql(), pre)


# ---------------------------------------------------------------- M2: refusal on ambiguity


def m2(sql, conn):
    for generation in ('x1', 'x2'):                          # two published candidates whose ka_gochara_resonance windows both contain the rows' computed_at
        c = candidate(conn, CHART_X, generation)
        window(conn, c.build_id, T0, T0 + 10 * MIN)
    add_rows(conn, CHART_X, ['1', '2'], T0 + MIN)
    before = dump(conn)
    refuses(conn, sql, 'ambiguous')
    assert not conn.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'gochara_resonance_map' AND column_name = 'generation'").fetchone(), \
        'the refused migration left the column behind'
    assert dump(conn) == before


def m2_split(sql, conn):
    c = candidate(conn, CHART_X, 'x1')
    window(conn, c.build_id, T0, T0 + 10 * MIN)
    add_rows(conn, CHART_X, ['1'], T0 + MIN)                 # produced by the published candidate
    add_rows(conn, CHART_X, ['2'], T0 + 3 * 60 * MIN)        # produced by nothing the build records know
    refuses(conn, sql, 'ambiguous')


@BOTH
def test_m2_two_producers_for_one_computed_at_refuse_the_migration(pre, reverted):
    # reversion: the ambiguity refusal is removed
    if reverted:
        with pytest.raises(AssertionError):
            m2(reverted_sql('IF v_ambiguous IS NOT NULL THEN', 'IF false THEN'), pre)
    else:
        m2(migration_sql(), pre)


@BOTH
def test_m2_a_chart_whose_rows_have_different_producers_refuses_the_migration(pre, reverted):
    # reversion: the per-chart single-outcome rule is removed (HAVING ... count(DISTINCT generation) > 1)
    if reverted:
        with pytest.raises(AssertionError):
            m2_split(reverted_sql(' OR count(DISTINCT generation) > 1', ''), pre)
    else:
        m2_split(migration_sql(), pre)


# ---------------------------------------------------------------- M3: the widened key


def m3(sql, conn):
    apply(conn, sql)
    add_rows(conn, CHART_A, ['1'], T0, generation='legacy')
    try:
        add_rows(conn, CHART_A, ['1'], T0, generation='cand_1')          # the same natural key in a second generation
    except psycopg.errors.UniqueViolation as exc:
        conn.rollback()
        raise AssertionError(f'the natural key cannot exist in two generations: {exc}') from exc
    with pytest.raises(psycopg.errors.UniqueViolation):                  # inside one generation it still conflicts
        add_rows(conn, CHART_A, ['1'], T0, generation='cand_1')
    conn.rollback()


@BOTH
def test_m3_the_same_natural_key_may_exist_in_two_generations_but_not_twice_in_one(pre, reverted):
    # reversion: the superseded 4-column unique key is kept
    if reverted:
        with pytest.raises(AssertionError):
            m3(reverted_sql("EXECUTE format('ALTER TABLE gochara_resonance_map DROP CONSTRAINT %I', v_old.conname);", 'NULL;'), pre)
    else:
        m3(migration_sql(), pre)


# ---------------------------------------------------------------- S1-S3: the served view


def served_world(sql, conn):
    """Three charts. Returns {chart: sorted served generations}."""
    apply(conn, sql)
    # chart A: head = g1 (older) with rows, g2 published later with rows, legacy rows
    g1, g2 = candidate(conn, CHART_A, 'g1'), candidate(conn, CHART_A, 'g2')
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART_A, 'g1'))
    for gen in ('legacy', 'g1', 'g2'):
        add_rows(conn, CHART_A, ['1', '2'], T0, generation=gen)
    # chart B: head = g3 published with NO rows; g1b published earlier with rows; g2b still building with rows
    candidate(conn, CHART_B, 'g1b')
    candidate(conn, CHART_B, 'g3')
    candidate(conn, CHART_B, 'g2b', state='building')
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART_B, 'g3'))
    for gen in ('legacy', 'g1b', 'g2b'):
        add_rows(conn, CHART_B, ['1', '2'], T0, generation=gen)
    # chart C: no head, no published candidate; legacy rows plus an unpublished candidate's rows
    candidate(conn, CHART_C, 'g1c', state='complete')
    for gen in ('legacy', 'g1c'):
        add_rows(conn, CHART_C, ['1', '2'], T0, generation=gen)
    conn.commit()
    return {ch: sorted(r[0] for r in conn.execute('SELECT DISTINCT generation FROM gochara_resonance_map_served WHERE chart_id = %s', (ch,)).fetchall())
            for ch in (CHART_A, CHART_B, CHART_C)}


def s1(sql, conn):
    served = served_world(sql, conn)
    assert served[CHART_C] == ['legacy'], f'an unpublished candidate generation is served: {served[CHART_C]}'
    assert 'g2b' not in served[CHART_B]


def s2(sql, conn):
    assert served_world(sql, conn)[CHART_A] == ['g1'], 'the head generation is not what is served'


def s3(sql, conn):
    assert served_world(sql, conn)[CHART_B] == ['g1b'], 'a head without resonance rows does not fall back to the latest published generation with rows'


JOIN_ON = ') s ON s.generation = m.generation;'


@BOTH
def test_s1_an_unpublished_candidate_generation_is_never_served(pre, reverted):
    # reversion: the view serves every generation
    if reverted:
        with pytest.raises(AssertionError):
            s1(reverted_sql(JOIN_ON, ') s ON true;'), pre)
    else:
        s1(migration_sql(), pre)


@BOTH
def test_s2_the_head_generation_is_served_when_it_holds_rows(pre, reverted):
    # reversion: the head is no longer consulted (the latest published generation is served instead)
    if reverted:
        with pytest.raises(AssertionError):
            s2(reverted_sql('WHERE h.chart_id = m.chart_id\n          AND EXISTS', 'WHERE false AND EXISTS'), pre)
    else:
        s2(migration_sql(), pre)


@BOTH
def test_s3_a_head_without_rows_falls_back_to_the_latest_published_generation_with_rows(pre, reverted):
    # reversion: no published fallback, a head without rows serves 'legacy'
    if reverted:
        with pytest.raises(AssertionError):
            s3(reverted_sql("WHERE c.chart_id = m.chart_id AND c.state = 'published'", 'WHERE false AND c.state = \'published\''), pre)
    else:
        s3(migration_sql(), pre)


# ---------------------------------------------------------------- G1: grants


def g1(sql, conn):
    conn.execute('GRANT SELECT ON gochara_resonance_map TO PUBLIC')
    conn.commit()
    apply(conn, sql)
    holders = conn.execute("SELECT DISTINCT a.grantee FROM pg_class c, aclexplode(c.relacl) a WHERE c.oid = 'gochara_resonance_map_served'::regclass AND a.privilege_type = 'SELECT'").fetchall()
    assert (0,) in holders, 'a grantee of the base table cannot read the served view'


@BOTH
def test_g1_the_view_is_readable_by_every_grantee_of_the_base_table(pre, reverted):
    # reversion: the grant on the view is not made
    if reverted:
        with pytest.raises(AssertionError):
            g1(reverted_sql('GRANT SELECT ON gochara_resonance_map_served TO PUBLIC;', 'NULL;'), pre)
    else:
        g1(migration_sql(), pre)


# ---------------------------------------------------------------- R1, R2: registry


def r1(sql, conn):
    apply(conn, sql)
    assert conn.execute("SELECT count_sql FROM asset_registry WHERE asset_id = 'ka_gochara_resonance'").fetchone()[0] == \
        'SELECT COUNT(*) FROM gochara_resonance_map_served WHERE chart_id=$1'
    # the cockpit runs count_sql with $1 -> the served rows only
    add_rows(conn, CHART_A, ['1', '2'], T0, generation='legacy')
    add_rows(conn, CHART_A, ['1', '2', '3'], T0, generation='cand_1')
    count = conn.execute("SELECT count_sql FROM asset_registry WHERE asset_id = 'ka_gochara_resonance'").fetchone()[0].replace('$1', '%s')
    assert conn.execute(count, (CHART_A,)).fetchone()[0] == 2


def r2(sql, conn):
    from pipeline.orchestrator.output_digest import _validate_spec
    apply(conn, sql)
    rows = conn.execute("SELECT spec_sha256, spec, retired_at FROM asset_output_digest_specs WHERE asset_id = 'ka_gochara_resonance' ORDER BY reviewed_at, spec_sha256").fetchall()
    current = [r for r in rows if r[2] is None]
    assert len(current) == 1 and len(rows) == 2, 'exactly one current spec, the 901 spec retired (not deleted)'
    sha, spec = current[0][0], current[0][1]
    try:
        _validate_spec('ka_gochara_resonance', spec, sha)   # the real validator: the recorded sha256 IS the canonical digest of the spec
    except ValueError as exc:
        raise AssertionError(f'the recorded digest spec is not valid: {exc}') from exc
    component = spec['components'][0]
    assert 'generation' in component['key_columns'] and 'generation' in component['value_columns']
    assert component['relation'] == 'gochara_resonance_map'  # the base table, so a candidate run's own rows enter the digest (a served-view digest would not see them)


@BOTH
def test_r1_count_sql_counts_the_served_rows(pre, reverted):
    # reversion: count_sql keeps counting the whole base table
    if reverted:
        with pytest.raises(AssertionError):
            r1(reverted_sql("SET count_sql = v_new_count WHERE", "SET count_sql = v_old_count WHERE"), pre)
    else:
        r1(migration_sql(), pre)


@BOTH
def test_r2_the_output_digest_spec_is_replaced_by_a_valid_one_that_covers_every_generation(pre, reverted):
    # reversion: the recorded sha256 is not the digest of the spec text
    sha = json.loads(open_spec_sha())
    if reverted:
        with pytest.raises(AssertionError):
            r2(reverted_sql(sha, sha[:-1] + ('0' if sha[-1] != '0' else '1')), pre)
    else:
        r2(migration_sql(), pre)


def open_spec_sha() -> str:
    """The sha256 the migration records for its new spec: the 64-hex constant after v_new_sha."""
    import re
    found = re.search(r"v_new_sha\s+constant text := '([a-f0-9]{64})'", migration_sql())
    assert found, 'the migration does not record a new spec sha256'
    return json.dumps(found.group(1))


def r2_unseeded(sql, conn):
    conn.execute("DELETE FROM asset_output_digest_specs WHERE asset_id = 'ka_gochara_resonance'")      # a database whose spec registry never held 901's spec
    conn.commit()
    apply(conn, sql)
    current = conn.execute("SELECT spec_sha256 FROM asset_output_digest_specs WHERE asset_id = 'ka_gochara_resonance' AND retired_at IS NULL").fetchall()
    assert len(current) == 1, 'the replacement spec was not recorded as the single current one'


@BOTH
def test_r2_a_registry_with_no_current_spec_receives_the_replacement(pre, reverted):
    # reversion: the refusal also fires when there is no current spec
    if reverted:
        with pytest.raises(AssertionError):
            r2_unseeded(reverted_sql('IF v_cur_specs > 1 OR (v_cur_specs = 1 AND (v_old_specs + v_new_specs) <> 1) THEN', 'IF v_cur_specs <> 1 OR (v_old_specs + v_new_specs) <> 1 THEN'), pre)
    else:
        r2_unseeded(migration_sql(), pre)


def test_r2_a_current_spec_that_is_neither_901s_nor_the_new_one_is_refused(pre):
    pre.execute("UPDATE asset_output_digest_specs SET retired_at = now() WHERE asset_id = 'ka_gochara_resonance'")
    pre.execute("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ka_gochara_resonance', %s, '{}'::jsonb)", ('a' * 64,))
    pre.commit()
    refuses(pre, migration_sql(), 'neither the 901 spec')


def test_r2_a_foreign_count_sql_or_spec_is_refused_not_overwritten(pre):
    pre.execute("UPDATE asset_registry SET count_sql = 'SELECT 1' WHERE asset_id = 'ka_gochara_resonance'")
    pre.commit()
    with pytest.raises(AssertionError, match='refusing to overwrite'):
        apply(pre)


# ---------------------------------------------------------------- W: the writer


CHART = '482012f1-710e-4a25-994a-93821f5871aa'


def canned_row(ref):
    return {'event_class': 'career', 'target_type': 'bhava', 'target_ref': ref, 'weight': 1, 'classical_citation': 'BPHS',
            'uncited_extension': False, 'source_rule_id': None, 'target_resolution_state': 'resolved', 'target_qualifier': None}


@pytest.fixture
def writer(monkeypatch):
    """The real ka_gochara_resonance writer run() with its fact readers replaced by canned rows; the DELETE/INSERT and the generation resolution are the real ones."""
    from services.ka_gochara_resonance import writer as module
    refs = ['1', '2']
    monkeypatch.setattr(module, 'TARGET_EVENT_CLASSES', ('career',))
    monkeypatch.setattr(module, 'M6_EVENT_CLASSES', ())
    monkeypatch.setattr(module, '_fetch_chart_resolution_context', lambda conn, chart: {'sign_lords': None})
    monkeypatch.setattr(module, '_fetch_event_class_rows', lambda conn, chart, event_class, report=None: [canned_row(r) for r in refs])
    monkeypatch.setattr(module, '_fetch_m6_context', lambda conn, chart: {})
    monkeypatch.setattr(module, '_stamp_target_resolution', lambda rows, ctx, report: None)
    monkeypatch.setattr(module, '_build_wp3c_notes', lambda report, rows, prior: json.dumps({'prior': prior}))
    module.refs = refs
    return module


def run_writer(module, conn, build_id, chart=CHART):
    ctx = types.SimpleNamespace(db_conn=conn, config={'chart_id': chart}, dry_run=False, build_id=build_id)
    return module.KaGocharaResonanceWriter().run(ctx)


def served_dump(conn, chart, generation):
    return conn.execute('SELECT id, chart_id, generation, event_class, target_type, target_ref, weight, computed_at FROM gochara_resonance_map '
                        'WHERE chart_id = %s AND generation = %s ORDER BY id', (chart, generation)).fetchall()


def w1(module, conn, monkeypatch, old_delete=None):
    apply(conn)
    candidate(conn, CHART, 'served_gen')
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART, 'served_gen'))
    c = prepare(conn, 'cand_gen', chart=CHART)
    add_rows(conn, CHART, ['7', '8', '9'], T0, generation='served_gen')
    add_rows(conn, CHART, ['5'], T0, generation='legacy')
    before = (served_dump(conn, CHART, 'served_gen'), served_dump(conn, CHART, 'legacy'))
    if old_delete is not None:
        monkeypatch.setattr(module, '_DELETE_SQL', old_delete)
    first = run_writer(module, conn, c.build_id)
    conn.commit()
    assert first.rows_inserted == 2
    assert (served_dump(conn, CHART, 'served_gen'), served_dump(conn, CHART, 'legacy')) == before, 'a candidate-bound run changed rows it does not own'
    own = [r[5] for r in served_dump(conn, CHART, 'cand_gen')]
    assert own == ['1', '2']
    run_writer(module, conn, c.build_id)                     # idempotent: the candidate's partition is replaced, not accreted
    conn.commit()
    assert [r[5] for r in served_dump(conn, CHART, 'cand_gen')] == ['1', '2']
    assert (served_dump(conn, CHART, 'served_gen'), served_dump(conn, CHART, 'legacy')) == before


@BOTH
def test_w1_a_candidate_bound_run_replaces_only_its_own_partition(pre, writer, monkeypatch, reverted):
    # reversion: the DELETE is scoped to the chart only (the second parameter, the generation, is ignored)
    if reverted:
        with pytest.raises(AssertionError):
            w1(writer, pre, monkeypatch, old_delete='DELETE FROM gochara_resonance_map WHERE chart_id = %s AND %s::text IS NOT NULL')
    else:
        w1(writer, pre, monkeypatch)


def w2(module, conn, monkeypatch, head_sql=None):
    apply(conn)
    c = candidate(conn, CHART, 'head_gen')
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART, 'head_gen'))
    conn.commit()
    if head_sql is not None:
        monkeypatch.setattr(module, '_FETCH_HEAD_SQL', head_sql)
    try:
        run_writer(module, conn, c.build_id)
    except ValueError as exc:
        conn.rollback()
        # Only the writer's own refusal counts: another ValueError (e.g. the candidate-grain step refusing a candidate that is not building) is a
        # different reason and must not let a run that skipped the head check pass as refused.
        assert 'immutable' in str(exc), f'refused for another reason: {exc}'
        return
    raise AssertionError('a run bound to the published head rewrote its resonance rows')


@BOTH
def test_w2_a_run_bound_to_the_published_head_is_refused(pre, writer, monkeypatch, reverted):
    # reversion: the head is not consulted
    if reverted:
        with pytest.raises(AssertionError):
            w2(writer, pre, monkeypatch, head_sql='SELECT generation FROM kala_layer_head WHERE chart_id = %s AND false')
    else:
        w2(writer, pre, monkeypatch)


def w3(module, conn, monkeypatch):
    apply(conn)
    c = prepare(conn, 'cand_gen', chart=CHART)
    add_rows(conn, CHART, ['4'], T0, generation='cand_gen')
    run_writer(module, conn, str(uuid.uuid4()))              # a build with no candidate bound
    conn.commit()
    assert [r[5] for r in served_dump(conn, CHART, 'legacy')] == ['1', '2'], 'a run bound to no candidate did not write the legacy partition'
    assert [r[5] for r in served_dump(conn, CHART, 'cand_gen')] == ['4'], 'a run bound to no candidate touched a candidate partition'


@BOTH
def test_w3_a_run_bound_to_no_candidate_writes_the_legacy_partition(pre, writer, monkeypatch, reverted):
    # reversion: the legacy partition is named differently
    if reverted:
        monkeypatch.setattr(writer, 'LEGACY_GENERATION', 'ordinary')
        with pytest.raises(AssertionError):
            w3(writer, pre, monkeypatch)
    else:
        w3(writer, pre, monkeypatch)


def w4(module, conn, monkeypatch, served_sql=None):
    apply(conn)
    add_rows(conn, CHART, ['yoga_a'], T0, generation='legacy')
    conn.execute("UPDATE gochara_resonance_map SET target_type = 'yoga_constituent'")
    conn.commit()
    if served_sql is not None:
        monkeypatch.setattr(module, '_FETCH_SERVED_YOGA_REFS_SQL', served_sql)
    assert module._fetch_prior_yoga_refs(conn, CHART, 'cand_new') == ['yoga_a'], 'a first candidate run does not see the served yoga set as its prior build'
    assert module._fetch_prior_yoga_refs(conn, CHART, 'legacy') == ['yoga_a']


@BOTH
def test_w4_a_first_candidate_run_takes_the_served_set_as_its_prior_build(pre, writer, monkeypatch, reverted):
    # reversion: a candidate's prior build is only its own (empty) partition
    if reverted:
        with pytest.raises(AssertionError):
            w4(writer, pre, monkeypatch, served_sql="SELECT target_ref FROM gochara_resonance_map_served WHERE chart_id = %s AND false")
    else:
        w4(writer, pre, monkeypatch)


# ---------------------------------------------------------------- P: readers


def p1(sql, conn, monkeypatch, relation=None):
    from services.gochara_grammar import resonance_map as RM
    apply(conn, sql)
    candidate(conn, CHART, 'served_gen')
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART, 'served_gen'))
    prepare(conn, 'cand_gen', chart=CHART)
    add_rows(conn, CHART, ['1'], T0, generation='served_gen', event_class='career')
    add_rows(conn, CHART, ['1'], T0, generation='cand_gen', event_class='wealth')    # a class only the candidate holds
    add_rows(conn, CHART, ['2'], T0, generation='cand_gen', event_class='career')
    conn.commit()
    if relation is not None:
        monkeypatch.setattr(RM, 'SERVED_RELATION', relation)
    served = RM.fetch_resonance_targets(conn, CHART)
    assert sorted((t.event_class, t.target_ref) for t in served) == [('career', '1')], 'the served read returns rows that are not served'
    own = RM.fetch_resonance_targets(conn, CHART, generation='cand_gen')
    assert sorted((t.event_class, t.target_ref) for t in own) == [('career', '2'), ('wealth', '1')]
    assert [r[0] for r in conn.execute(*RM.event_classes_query(CHART)).fetchall()] == ['career']
    assert [r[0] for r in conn.execute(*RM.event_classes_query(CHART, 'cand_gen')).fetchall()] == ['career', 'wealth']


@BOTH
def test_p1_readers_see_the_served_rows_and_a_candidate_build_sees_its_own(pre, monkeypatch, reverted):
    # reversion: the shared reader reads the base table
    if reverted:
        with pytest.raises(AssertionError):
            p1(migration_sql(), pre, monkeypatch, relation='gochara_resonance_map')
    else:
        p1(migration_sql(), pre, monkeypatch)


def reverted_pin(old, new):
    """ka_kshetra's _gochara_corpus_pin with ONE statement reverted (the writer module registers an asset, so a source copy cannot be imported twice)."""
    import inspect
    import textwrap
    from services.ka_kshetra import writer as kshetra
    source = textwrap.dedent(inspect.getsource(kshetra.KaKshetraWriter._gochara_corpus_pin))
    assert source.count(old) == 1
    namespace = dict(vars(kshetra))
    exec(source.replace(old, new), namespace)
    return namespace['_gochara_corpus_pin'].__func__


def p2(conn, pin_of):
    from services.ka_kshetra import writer as kshetra
    apply(conn)
    conn.execute('CREATE TABLE kala_gochara_authority (chart_id uuid, authoritative_generation text)')
    conn.execute('CREATE TABLE kala_gochara_windows (chart_id uuid, generation text, calibration_state text)')
    candidate(conn, CHART, 'served_gen')
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (CHART, 'served_gen'))
    add_rows(conn, CHART, ['1', '2'], T0, generation='served_gen')
    conn.commit()
    pin = pin_of(conn, CHART)['gochara_corpus_digest']
    assert pin != 'digest_unavailable'
    add_rows(conn, CHART, ['3', '4', '5'], T0 + MIN, generation='cand_gen')          # a candidate's rows change nothing the pin fingerprints
    assert pin_of(conn, CHART)['gochara_corpus_digest'] == pin, 'the corpus pin moved when only a candidate generation changed'


@BOTH
def test_p2_the_kshetra_corpus_pin_fingerprints_only_the_served_rows(pre, reverted):
    # reversion: the pin fingerprints the base table
    from services.ka_kshetra import writer as kshetra
    if reverted:
        with pytest.raises(AssertionError):
            p2(pre, reverted_pin('" FROM gochara_resonance_map_served WHERE chart_id = %s"', '" FROM gochara_resonance_map WHERE chart_id = %s"'))
    else:
        p2(pre, kshetra.KaKshetraWriter._gochara_corpus_pin)
