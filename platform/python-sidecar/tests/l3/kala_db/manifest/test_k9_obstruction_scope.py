"""SR-K9-WRITE-SCOPE, item k9-obstruction-scope: a K9 build never rewrites or deletes the SERVED rows of ``kala_obstruction``.

The table mixes three kinds of rows for one chart: the legacy partition (``generation IS NULL``, rewritten in place by an ordinary
``ka_vighnakara`` rebuild), the published head's generation, and the ``candidate:<build>`` generations a K9 build is still writing.
One doctrine-grounded oracle per distinct production claim (D-OWNER-TESTS-20261016; root CLAUDE.md §N.8: each is a detector that can
read false). Nothing here restates a classical value: obstruction types, scores and generations are PLANTED labels (B.10).

  O1  a candidate-bound ``ka_vighnakara`` build writes ONLY under its candidate generation; the served rows (legacy NULL and the head's
      generation) are byte-identical afterwards (``write_generation`` in ka_vighnakara.py; ORCHESTRATOR_CONVERGENCE_CLOSE §N.3: a rebuild
      replaces its OWN partition)
  O2  an ordinary (unbound) rebuild still replaces the legacy NULL partition in place and touches no generation
  O3  a candidate that is no longer ``building``, or that is the published head, cannot have its obstruction rows replaced
  O4  a K9 teardown of a run deletes exactly that run's ``kala_obstruction`` generation and leaves every served row byte-identical
      (the table has NO foreign key to the candidate, so ``UNLINKED_CANDIDATE_TABLES`` is the only way teardown finds the rows)
  O5  the SERVED partition is the head's generation when it holds rows, else the legacy partition; never a candidate, never both
      (services/kala_core/served_generation.py; pinned to the TypeScript twin by the shared literal below)
  O6  the three Python readers (``ph_pratikara``, ``ph_muhurta``, ``ka_kala_darshana``) consume the served partition only
  O7  the K5 G1 suppression reader (``ka_kshetra.g1_inputs.load_suppression``) reads negative-space ASSERTION rows only: the legacy-detector
      rows the K9 build now writes under the candidate generation (no assertion_id, no interval) are not negative-space assertions
"""
import uuid
from datetime import date
from types import SimpleNamespace

import psycopg
import pytest

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers import ka_kala_darshana as darshana_mod
from pipeline.orchestrator.writers import ph_muhurta as muhurta_mod
from pipeline.orchestrator.writers import ph_pratikara as pratikara_mod
from services.kala_core import rebuild_control
from services.kala_core.served_generation import served_obstruction_predicate
from tests.l3.kala_db.manifest.test_k9_writer_grains import (  # noqa: F401  (conn, vighnakara are fixtures)
    BIRTH, BUILD, CAND, CHART, HEAD, conn, convergence, drive, vighnakara,
)
from tests.l3.kala_db.manifest.test_publication_ops import db  # noqa: F401  (a fixture)
from tests.l3.kala_db.manifest.test_rebuild_control import CHART as CANONICAL, ctl, make_run  # noqa: F401  (ctl is a fixture)

# The twin of platform/src/lib/retrieval/registry/layers/L3_kala/served_obstruction.test.ts (same literal there).
SERVED_PREDICATE_O = ('o.generation IS NOT DISTINCT FROM (SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = o.chart_id '
                      'AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))')


def obs(conn, generation, otype, *, chart=CHART, conv=None, score=0.5):
    conn.execute("INSERT INTO kala_obstruction (chart_id, convergence_id, signal_id, obstruction_type, severity, severity_score, "
                 "override_score, obstruction_detail, source_citation, generation) "
                 "VALUES (%s, %s, 'S-SEED', %s, 'mild', %s, 0.1, '{}'::jsonb, 'seed', %s)",
                 (chart, conv, otype, score, generation))


def snapshot_of(conn, where, *params):
    return [r['j'] if isinstance(r, dict) else r[0] for r in
            conn.execute(f'SELECT to_jsonb(o) AS j FROM kala_obstruction o WHERE {where} ORDER BY id', params).fetchall()]


# The served rows are convergence-anchored: ``snapshot_of`` compares the WHOLE row (``to_jsonb``), so a NULL link here would make the
# "byte-identical" claim vacuous for ``convergence_id``, the one column a convergence-side delete or rewrite changes (N.8).
SERVED_CONV = 4242


def seed_served(conn):
    obs(conn, None, 'legacy_a', conv=SERVED_CONV)
    obs(conn, None, 'legacy_b', conv=SERVED_CONV)
    obs(conn, HEAD, 'head_a', conv=SERVED_CONV)


# ── O1, O2, O3: the writer ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_o1_candidate_bound_build_writes_only_its_generation_and_leaves_served_rows_byte_identical(conn, vighnakara):
    convergence(conn, CAND)      # a candidate-bound build reads only its own candidate's convergence rows (SR-K9-BIND B1a)
    seed_served(conn)
    served = snapshot_of(conn, 'generation IS DISTINCT FROM %s', CAND)
    assert len(served) == 3 and {row['convergence_id'] for row in served} == {SERVED_CONV}
    drive(conn, vighnakara, 'ka_vighnakara')
    assert snapshot_of(conn, 'generation IS DISTINCT FROM %s', CAND) == served, 'a served row was changed or deleted'
    written = snapshot_of(conn, "obstruction_type = 'planted'")
    assert written and {row['generation'] for row in written} == {CAND}, 'the build wrote outside its candidate generation'


def test_o1_a_second_candidate_build_replaces_its_own_partition_instead_of_accreting(conn, vighnakara):
    convergence(conn, CAND)
    drive(conn, vighnakara, 'ka_vighnakara')
    first = len(snapshot_of(conn, 'generation = %s', CAND))
    drive(conn, vighnakara, 'ka_vighnakara')
    assert first > 0 and len(snapshot_of(conn, 'generation = %s', CAND)) == first


def test_o2_an_ordinary_rebuild_replaces_the_legacy_partition_in_place_and_touches_no_generation(conn, vighnakara):
    conn.execute('DELETE FROM kala_layer_head')      # an unbound rewrite is refused once a generation is published (SR-K9-BIND B1b): the ordinary path is the pre-publication one
    convergence(conn, 'legacy')
    seed_served(conn)
    obs(conn, CAND, 'candidate_seed')
    kept = snapshot_of(conn, 'generation IS NOT NULL')
    drive(conn, vighnakara, 'ka_vighnakara', build=str(uuid.uuid4()))
    assert snapshot_of(conn, 'generation IS NOT NULL') == kept, 'an ordinary rebuild touched a generation'
    legacy = snapshot_of(conn, 'generation IS NULL')
    assert legacy and {row['obstruction_type'] for row in legacy} == {'planted'}, 'the legacy partition was not replaced in place'


@pytest.mark.parametrize('defect', ['complete', 'head'])
def test_o3_a_candidate_that_is_not_building_or_is_the_head_cannot_have_its_rows_replaced(conn, vighnakara, defect):
    convergence(conn, CAND)
    seed_served(conn)
    obs(conn, CAND, 'candidate_seed')
    if defect == 'complete':
        conn.execute("UPDATE kala_layer_candidate SET state = 'complete' WHERE generation = %s", (CAND,))
    else:
        conn.execute('UPDATE kala_layer_head SET generation = %s WHERE chart_id = %s', (CAND, CHART))
    before = snapshot_of(conn, 'TRUE')
    ctx = ContextSpec(asset_id='ka_vighnakara', build_id=BUILD, db_conn=conn, config={'chart_id': CHART, 'birth_params': BIRTH})
    with pytest.raises(ValueError, match='building candidate'):
        vighnakara.run(ctx)
    assert snapshot_of(conn, 'TRUE') == before


# ── O4: the teardown ────────────────────────────────────────────────────────────────────────────────────────────────────────────

OTHER_CHART = str(uuid.uuid4())


def publish_head(conn, generation, *, chart=CANONICAL):
    head = make_run(conn, 'completed', generation=generation, chart=chart)
    conn.execute("UPDATE kala_layer_candidate SET state = 'published' WHERE chart_id = %s AND generation = %s", (chart, generation))
    conn.execute('INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s, %s)', (chart, generation))
    conn.commit()
    return head


def test_o4_teardown_deletes_exactly_the_runs_obstruction_generation_and_no_served_row(ctl):
    ctl.execute('CREATE TABLE kala_obstruction (id serial PRIMARY KEY, chart_id uuid NOT NULL, convergence_id integer, signal_id text, '
                'obstruction_type text, severity text, severity_score numeric, override_score numeric, obstruction_detail jsonb, '
                'source_citation text, generation text)')
    publish_head(ctl, 'head')
    failed = make_run(ctl, 'failed', generation='a')
    later = make_run(ctl, 'completed', generation='b')
    make_run(ctl, 'completed', generation='a', chart=OTHER_CHART)
    for chart, generation, count in ((CANONICAL, None, 3), (CANONICAL, 'head', 2), (CANONICAL, 'a', 2), (CANONICAL, 'b', 2), (OTHER_CHART, 'a', 1)):
        for index in range(count):
            obs(ctl, generation, f'{generation}-{index}', chart=chart, conv=SERVED_CONV)
    ctl.commit()
    served = snapshot_of(ctl, 'generation IS NULL OR generation = %s', 'head')
    others = snapshot_of(ctl, "generation = 'b' OR chart_id = %s", OTHER_CHART)
    assert len(served) == 5 and {row['convergence_id'] for row in served} == {SERVED_CONV}
    assert rebuild_control.census(ctl, failed.build_id)['kala_obstruction'] == 2

    result = rebuild_control.teardown(ctl, run_id=failed.build_id)

    assert result['status'] == 'TORN_DOWN' and result['deleted']['kala_obstruction'] == 2
    assert snapshot_of(ctl, 'generation IS NULL OR generation = %s', 'head') == served, 'a served obstruction row was touched by the teardown'
    assert snapshot_of(ctl, "generation = 'b' OR chart_id = %s", OTHER_CHART) == others, 'another run or another chart was touched'
    assert snapshot_of(ctl, "generation = 'a' AND chart_id = %s", CANONICAL) == []
    assert later.build_id and ctl.execute('SELECT count(*) FROM kala_layer_head').fetchone()[0] == 1


# ── O5: the served partition ────────────────────────────────────────────────────────────────────────────────────────────────────

def served_types(conn):
    return sorted(r['t'] if isinstance(r, dict) else r[0] for r in conn.execute(
        'SELECT o.obstruction_type AS t FROM kala_obstruction o WHERE o.chart_id = %s AND ' + served_obstruction_predicate('o'), (CHART,)).fetchall())


def test_o5_the_predicate_text_is_the_one_the_typescript_twin_pins():
    assert served_obstruction_predicate('o') == SERVED_PREDICATE_O


def test_o5_served_partition_is_the_head_when_it_holds_rows_else_legacy_and_never_a_candidate(conn):
    seed_served(conn)
    obs(conn, CAND, 'candidate_seed')
    assert served_types(conn) == ['head_a'], 'the head holds rows: it replaces the legacy rows, a candidate is never served'
    conn.execute("UPDATE kala_obstruction SET generation = 'retained-empty' WHERE generation = %s", (HEAD,))
    assert served_types(conn) == ['legacy_a', 'legacy_b'], 'the head holds no rows: the legacy partition is served'
    conn.execute('DELETE FROM kala_layer_head')
    assert served_types(conn) == ['legacy_a', 'legacy_b'], 'no head at all: the legacy partition is served'


# ── O6: the Python readers ──────────────────────────────────────────────────────────────────────────────────────────────────────

def serve_convergence(conn, *, drop_only=False):
    """(Re)create the served view as the writers' fixture defines it (migration 1405): ``SELECT k.*`` is expanded when the view is created, so a column added
    to or retyped on kala_convergence afterwards needs the view dropped first and created again."""
    conn.execute('DROP VIEW IF EXISTS kala_convergence_served')
    if not drop_only:
        conn.execute('CREATE VIEW kala_convergence_served AS SELECT k.* FROM kala_convergence k WHERE k.generation = '
                     "COALESCE((SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = k.chart_id), 'legacy')")


def readers_world(conn):
    """Two windows (the head's convergence rows, which the readers join through the served view); legacy rows on window 1, the head's rows on window 2, a candidate's rows on window 1."""
    conn.execute('ALTER TABLE kala_convergence ADD COLUMN domain text, ADD COLUMN constituent_factors jsonb, '
                 'ADD COLUMN confidence_label text, ADD COLUMN rarity_years numeric')
    serve_convergence(conn)
    for peak, start, end in (('2030-03-03', '2030-03-01', '2030-03-05'), ('2031-04-04', '2031-04-01', '2031-04-07')):
        conn.execute("INSERT INTO kala_convergence (chart_id, signal_id, mode, peak_date, window_start, window_end, convergence_score, orb_strength, generation) "
                     "VALUES (%s, 'S-CONV', 'C', %s, %s, %s, 0.8, 0.5, %s)", (CHART, peak, start, end, HEAD))
    first, second = [r['convergence_id'] if isinstance(r, dict) else r[0]
                     for r in conn.execute('SELECT convergence_id FROM kala_convergence ORDER BY convergence_id').fetchall()]
    obs(conn, None, 'legacy_row', conv=first)
    obs(conn, HEAD, 'head_row', conv=second)
    obs(conn, CAND, 'candidate_row', conv=first)


def test_o6_ph_pratikara_reads_the_served_partition_only(conn):
    readers_world(conn)
    rows = pratikara_mod.PhPratikaraWriter()._load_obstructions(conn, CHART)
    assert [r['obstruction_type'] for r in rows] == ['head_row']


def test_o6_ph_muhurta_reads_the_served_partition_only(conn):
    readers_world(conn)
    windows = muhurta_mod.PhMuhurtaWriter()._load_obstruction_windows(conn, CHART)
    assert sorted(windows) == [(date(2031, 4, 1), date(2031, 4, 7))]


def test_o6_ka_kala_darshana_consumes_the_served_partition_only(conn):
    readers_world(conn)
    conn.execute('ALTER TABLE kala_obstruction ALTER COLUMN override_score TYPE double precision, ALTER COLUMN severity_score TYPE double precision')
    serve_convergence(conn, drop_only=True)
    conn.execute('ALTER TABLE kala_convergence ALTER COLUMN convergence_score TYPE double precision')
    serve_convergence(conn)
    conn.execute('CREATE TABLE kala_darshana (id serial PRIMARY KEY, chart_id uuid, convergence_id integer, signal_id text, effective_score numeric, '
                 'net_label text, peak_date text, window_start text, window_end text, obstruction_summary jsonb, narrative jsonb, '
                 'source_citation text, generation text)')
    darshana_mod._LegacyKaKalaDarshanaWriter().run(SimpleNamespace(db_conn=conn, config={'chart_id': CHART}))
    summaries = {r['convergence_id']: [o['type'] for o in r['obstruction_summary']]
                 for r in conn.execute('SELECT convergence_id, obstruction_summary FROM kala_darshana').fetchall()}
    by_peak = {r['peak_date'].isoformat(): r['convergence_id']
               for r in conn.execute('SELECT convergence_id, peak_date FROM kala_convergence_served').fetchall()}
    assert summaries[by_peak['2030-03-03']] == [], 'a legacy or candidate row leaked into the served read'
    assert summaries[by_peak['2031-04-04']] == ['head_row']


# ── O7: the G1 suppression reader ───────────────────────────────────────────────────────────────────────────────────────────────

def test_o7_the_g1_suppression_reader_ignores_legacy_detector_rows_under_a_candidate_generation(conn, monkeypatch):
    from services.kala_core.overlays import contested_reader
    from services.ka_kshetra import g1_inputs
    monkeypatch.setattr(contested_reader, 'load_candidate_payload', lambda *a, **k: None)
    conn.execute('ALTER TABLE kala_obstruction ADD COLUMN assertion_id text, ADD COLUMN assertion jsonb, ADD COLUMN effective_state text, '
                 'ADD COLUMN event_class_id text, ADD COLUMN interval_start timestamptz, ADD COLUMN interval_end timestamptz')
    conn.execute('CREATE TABLE kala_vedha_gochara_interval (chart_id uuid, generation text, ayanamsha_id text, vedha_kind text, graha text, t_in timestamptz)')
    obs(conn, CAND, 'legacy_detector_row')          # exactly what ka_vighnakara writes for a candidate-bound K9 build
    prims, gaps = g1_inputs.load_suppression(conn, CHART, CAND, date(1984, 2, 5))
    assert [p for p in prims if getattr(p, 'source_table', None) == 'kala_obstruction'] == []
    reasons = {(g['source_ref'], g['reason']) for g in gaps}
    assert ('negative_space', 'information_unavailable') in reasons, 'no negative-space assertion exists: an honest gap, not a row'
    assert not any(reason == 'negative_space_binding_not_admitted' for _, reason in reasons)
