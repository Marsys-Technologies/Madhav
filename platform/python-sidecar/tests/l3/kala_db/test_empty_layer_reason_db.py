"""SR-EMPTY-REASON (root CLAUDE.md §N.6 rule 4, §N.7.6, §N.8): the Python readers of the Kāla convergence / obstruction layers
say WHY a layer is empty instead of reading an empty layer as a positive "none". Real SQL on the disposable lane database.

One doctrine-grounded oracle per distinct production claim (D-OWNER-TESTS-20261016). Nothing here restates a classical value:
generations, counts and asset states are PLANTED labels (B.10).

  R1  ``read_empty_layer`` measures the four empties from the table, its served partition and ``asset_throughput.state``:
      never computed / computed and found none / rows only in an unserved partition / served rows the reader's condition dropped
  R2  a probe that cannot run is ``layer_state_unreadable`` and leaves the writer's transaction usable (SAVEPOINT)
  R3  ``ph_muhurta`` names the empty obstruction layer (no windows) instead of silently reporting "no overlap": undatable served rows
      are told apart from a layer nobody built; a populated layer reports no reason; a read that errors is ``obstruction_read_failed``,
      never the state probe's "computed_found_none"
  R4  ``ka_kala_darshana`` with convergence windows but an empty obstruction layer stamps every window's narrative "not checked"
      (not an unobstructed score), unless ka_vighnakara actually ran; a populated layer's narrative is unchanged
"""
from datetime import date
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import ka_kala_darshana as darshana_mod
from pipeline.orchestrator.writers import ph_muhurta as muhurta_mod
from services.kala_core.empty_layer_reason import read_empty_layer
from tests.l3.kala_db.manifest.test_k9_obstruction_scope import obs, readers_world, serve_convergence
from tests.l3.kala_db.manifest.test_k9_writer_grains import CAND, CHART, HEAD, conn  # noqa: F401  (conn is a fixture)


@pytest.fixture
def world(conn):  # noqa: F811
    """The lane fixture's asset_throughput has no ``state`` column (it predates this reader); the real table has one."""
    conn.execute('ALTER TABLE asset_throughput ADD COLUMN state text')
    return conn


def light(conn, asset):
    conn.execute("INSERT INTO asset_throughput (chart_id, asset_id, state) VALUES (%s, %s, 'lit')", (CHART, asset))


def reading(conn, table):
    return read_empty_layer(conn, CHART, table, savepoint='sp_test_state')


@pytest.mark.parametrize('table,asset', [('kala_obstruction', 'ka_vighnakara'), ('kala_convergence', 'ka_sangam')])
def test_r1_the_four_empties_are_told_apart(world, table, asset):
    conn = world
    assert reading(conn, table)['empty_reason'] == 'layer_not_computed'
    conn.execute("INSERT INTO asset_throughput (chart_id, asset_id, state) VALUES (%s, %s, 'stale')", (CHART, asset))
    stale = reading(conn, table)
    assert stale['empty_reason'] == 'layer_not_computed' and stale['layer_state']['asset_state'] == 'stale'
    conn.execute('DELETE FROM asset_throughput')
    light(conn, asset)
    lit = reading(conn, table)
    assert lit['empty_reason'] == 'computed_found_none'
    assert lit['layer_state'] == {'rows_any_partition': 0, 'rows_served_unfiltered': 0, 'asset_state': 'lit'}
    # a private candidate's rows exist in the table but are not what readers are served
    if table == 'kala_obstruction':
        obs(conn, CAND, 'candidate_row')
    else:
        conn.execute("INSERT INTO kala_convergence (chart_id, signal_id, mode, peak_date, convergence_score, generation) "
                     "VALUES (%s, 'S', 'C', '2030-03-03', 0.8, %s)", (CHART, CAND))
    outside = reading(conn, table)
    assert outside['empty_reason'] == 'rows_outside_served_generation'
    assert outside['layer_state']['rows_any_partition'] == 1 and outside['layer_state']['rows_served_unfiltered'] == 0
    # served rows exist (the reader's own condition is what emptied its result)
    if table == 'kala_obstruction':
        obs(conn, None, 'legacy_row')
    else:
        conn.execute("INSERT INTO kala_convergence (chart_id, signal_id, mode, peak_date, convergence_score, generation) "
                     "VALUES (%s, 'S', 'C', '2030-03-03', 0.8, %s)", (CHART, HEAD))
    served = reading(conn, table)
    assert served['empty_reason'] == 'filters_excluded_all_rows' and served['layer_state']['rows_served_unfiltered'] == 1


def test_r2_an_unreadable_state_is_named_and_the_transaction_survives(conn):  # noqa: F811
    # the lane fixture's asset_throughput has no ``state`` column, so the asset-state read fails
    got = reading(conn, 'kala_obstruction')
    assert got['empty_reason'] == 'layer_state_unreadable'
    assert got['layer_state'] == {'rows_any_partition': None, 'rows_served_unfiltered': None, 'asset_state': None}
    assert conn.execute('SELECT 1 AS ok').fetchone()['ok'] == 1, 'the failed probe aborted the writer transaction'


def test_r3_muhurta_names_why_there_are_no_obstruction_windows(world):
    conn = world
    writer = muhurta_mod.PhMuhurtaWriter()
    windows, layer = writer._read_obstruction_layer(conn, CHART)
    assert windows == {} and layer['empty_reason'] == 'layer_not_computed' and layer['windows'] == 0
    light(conn, 'ka_vighnakara')
    assert writer._read_obstruction_layer(conn, CHART)[1]['empty_reason'] == 'computed_found_none'
    # served obstruction rows that no served convergence window dates: not "none", not "never built"
    obs(conn, None, 'dasha_anchored_row', conv=None)
    undated = writer._read_obstruction_layer(conn, CHART)[1]
    assert undated['empty_reason'] == 'served_rows_without_convergence_window'
    assert undated['layer_state']['rows_served_unfiltered'] == 1
    # the wrapper keeps its dict contract
    assert writer._load_obstruction_windows(conn, CHART) == {}


def test_r3_muhurta_populated_layer_reports_windows_and_no_reason(world):
    conn = world
    readers_world(conn)
    windows, layer = muhurta_mod.PhMuhurtaWriter()._read_obstruction_layer(conn, CHART)
    assert sorted(windows) == [(date(2031, 4, 1), date(2031, 4, 7))]
    assert layer == {'windows': 1, 'empty_reason': None, 'layer_state': None}


def test_r3_muhurta_a_failed_obstruction_read_is_named_not_read_as_no_overlap(world):
    conn = world
    light(conn, 'ka_vighnakara')  # a built layer: were the failure reclassified by the state probe it would read "computed_found_none"
    serve_convergence(conn, drop_only=True)  # the served convergence view the read joins through is gone: the SELECT errors
    windows, layer = muhurta_mod.PhMuhurtaWriter()._read_obstruction_layer(conn, CHART)
    assert windows == {} and layer == {'windows': 0, 'empty_reason': 'obstruction_read_failed', 'layer_state': None}
    assert conn.execute('SELECT 1 AS ok').fetchone()['ok'] == 1, 'the failed read aborted the writer transaction'


def _darshana_table(conn):
    conn.execute('CREATE TABLE kala_darshana (id serial PRIMARY KEY, chart_id uuid, convergence_id integer, signal_id text, effective_score numeric, '
                 'net_label text, peak_date text, window_start text, window_end text, obstruction_summary jsonb, narrative jsonb, '
                 'source_citation text, generation text)')


def _run_darshana(conn):
    conn.execute('ALTER TABLE kala_obstruction ALTER COLUMN override_score TYPE double precision, ALTER COLUMN severity_score TYPE double precision')
    serve_convergence(conn, drop_only=True)
    conn.execute('ALTER TABLE kala_convergence ALTER COLUMN convergence_score TYPE double precision')
    serve_convergence(conn)
    _darshana_table(conn)
    result = darshana_mod._LegacyKaKalaDarshanaWriter().run(SimpleNamespace(db_conn=conn, config={'chart_id': CHART}))
    return result, [r['narrative'] for r in conn.execute('SELECT narrative FROM kala_darshana ORDER BY convergence_id').fetchall()]


def _convergence_only(conn):
    conn.execute('ALTER TABLE kala_convergence ADD COLUMN domain text, ADD COLUMN constituent_factors jsonb, '
                 'ADD COLUMN confidence_label text, ADD COLUMN rarity_years numeric')
    serve_convergence(conn)
    conn.execute("INSERT INTO kala_convergence (chart_id, signal_id, mode, peak_date, window_start, window_end, convergence_score, orb_strength, generation) "
                 "VALUES (%s, 'S-CONV', 'C', '2030-03-03', '2030-03-01', '2030-03-05', 0.8, 0.5, %s)", (CHART, HEAD))


def test_r4_darshana_does_not_present_an_unchecked_window_as_unobstructed(world):
    _convergence_only(world)
    _, narratives = _run_darshana(world)
    assert len(narratives) == 1
    layer = narratives[0]['obstruction_layer']
    assert layer['assessed'] is False and layer['empty_reason'] == 'layer_not_computed'
    assert 'Not checked against obstructions' in narratives[0]['caution'] and 'layer_not_computed' in narratives[0]['caution']


def test_r4_darshana_measured_clear_when_the_obstruction_writer_ran(world):
    _convergence_only(world)
    light(world, 'ka_vighnakara')
    _, narratives = _run_darshana(world)
    layer = narratives[0]['obstruction_layer']
    assert layer['assessed'] is True and layer['empty_reason'] == 'computed_found_none'
    assert narratives[0]['caution'] is None


def test_r4_darshana_populated_obstruction_layer_narrative_is_unchanged(world):
    readers_world(world)
    _, narratives = _run_darshana(world)
    assert narratives and all('obstruction_layer' not in n for n in narratives)


def test_r4_darshana_empty_convergence_names_its_reason(world):
    world.execute('ALTER TABLE kala_convergence ADD COLUMN domain text, ADD COLUMN constituent_factors jsonb, '
                  'ADD COLUMN confidence_label text, ADD COLUMN rarity_years numeric')
    serve_convergence(world)
    _darshana_table(world)
    result = darshana_mod._LegacyKaKalaDarshanaWriter().run(SimpleNamespace(db_conn=world, config={'chart_id': CHART}))
    assert result.rows_inserted == 0 and result.notes == 'No convergence windows (layer_not_computed) — run ka_sangam first'
    light(world, 'ka_sangam')
    result = darshana_mod._LegacyKaKalaDarshanaWriter().run(SimpleNamespace(db_conn=world, config={'chart_id': CHART}))
    assert result.notes == 'No convergence windows (computed_found_none)'
