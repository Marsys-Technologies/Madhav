"""SR-K9B-TRIAGE (S5): a candidate-bound ka_gochara run writes ONLY its candidate's partition of `kala_gochara_windows_v2` / `kala_gochara_v2_build_state`.

Evidence (K9 round B, X-20261023T011907Z-k9-round-b): the kit clears the chart's generation-'2.0' rows of both tables before every repetition
(kitlib.reset_gochara_state), so "served/legacy rows" read 0 before the run and 72 after the teardown, in 4 of 4 repetitions: the 72 rows were written by the
candidate run into the ordinary '2.0' partition, which the teardown (generation-scoped) cannot reach. They are not legacy rows.
Rule (SR-K9-WRITE-SCOPE, DECISIONS_SURROGATE.jsonl 2026-10-22; SR-K9B-TRIAGE (b)): rows the candidate run wrote outside its generation scope are a defect.
Source for the scoping itself: root CLAUDE.md §N.3 (L1+ delete-then-insert scoped to the natural key; a rebuild replaces, never accretes) and the sibling pattern of
`gochara_resonance_map` (migration 1404, rebuild_control.GENERATION_SCOPED_WRITES).

Claims, each with ONE planted reversion (CLAUDE.md §N.8: a detector that can read false):
G1 a candidate-bound run inserts its windows and its build-state ledger under the candidate generation, writes nothing at '2.0', and deletes none of the '2.0' rows
G2 an ordinary (unbound) run keeps writing generation '2.0'
G3 the candidate's delete-then-insert replaces its own partition only (a second run of the same candidate does not accrete)
G4 a candidate-bound plan is not skipped because the ORDINARY '2.0' ledger holds the same class fingerprint (the candidate must be built, not assumed)
G5 the teardown removes the run's windows and ledger rows, names ka_gochara in the receipt, and leaves every '2.0' row byte-identical
"""
import importlib.util
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara as gochara_mod
from services.kala_core import rebuild_control
from services.w2g.fingerprint import class_fingerprint
from services.w2g.materialize import GRAMMAR_VERSION, MaterializeResult
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, REVERTED  # noqa: F401
from tests.l3.kala_db.manifest.test_k9_writer_grains import BIRTH, BUILD, CAND, CHART, conn  # noqa: F401  (conn is a fixture)
from tests.l3.kala_db.manifest.test_w56_k9_cancel_teardown import OTHER_CHART  # noqa: F401
from tests.l3.kala_db.manifest.test_publication_ops import db  # noqa: F401  (a fixture the ctl fixture needs)
from tests.l3.kala_db.manifest.test_rebuild_control import CHART as CANONICAL_CHART, ctl, make_run  # noqa: F401  (ctl is a fixture)

EVENT_CLASS = 'career'
NEXT_ROWS: list = []
SERVED = '2.0'

WINDOWS_DDL = """CREATE TABLE kala_gochara_windows_v2 (
    id bigserial PRIMARY KEY, chart_id uuid NOT NULL, event_class text NOT NULL, temporal_shape text NOT NULL, window_start date, window_end date,
    peak_date date NOT NULL, milestone_id text, is_irreversibility_milestone boolean, signed_intensity numeric, raw_intensity numeric, valence text,
    is_adverse boolean, active_sentences jsonb, contributing_systems jsonb, suppression_state jsonb, peak_basis text, calibration_state text, source text,
    generation text NOT NULL DEFAULT '2.0', term_breakdown jsonb, lambda_v3_ci_low numeric, lambda_v3_ci_high numeric, ci_source text)"""
BUILD_STATE_DDL = """CREATE TABLE kala_gochara_v2_build_state (
    chart_id uuid NOT NULL, event_class text NOT NULL, generation text NOT NULL DEFAULT '2.0', class_fingerprint text NOT NULL, grammar_version text NOT NULL,
    arc_engine_version text NOT NULL, bodies_scope text[] NOT NULL DEFAULT '{}', horizon_start_date date NOT NULL, horizon_end_date date NOT NULL,
    horizon_status text NOT NULL, contacts_evaluated integer NOT NULL DEFAULT 0, rows_written integer NOT NULL DEFAULT 0, skipped_reason text, build_id text,
    computed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (chart_id, event_class, generation))"""


def verdict(reverted, oracle, module, tmp_path, old, new, *args):
    """As test_k9_publication_hardening.verdict, but the copy keeps the module's last name segment: the writer registry accepts a re-import only under it."""
    if not reverted:
        return oracle(module, *args)
    source = Path(module.__file__).read_text()
    assert source.count(old) == 1, f'reversion anchor is not unique: {old!r}'
    path = tmp_path / 'reverted_copy' / Path(module.__file__).name
    path.parent.mkdir()
    path.write_text(source.replace(old, new))
    spec = importlib.util.spec_from_file_location('reverted_copy.' + module.__name__.rsplit('.', 1)[-1], path)
    copy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(copy)
    if hasattr(copy, 'materialize_event_class'):
        copy.materialize_event_class = module.materialize_event_class       # the fixture's stub (monkeypatched on the real module) also stands in the copy
    with pytest.raises(AssertionError):
        oracle(copy, *args)


def window_row(peak):
    return {'event_class': EVENT_CLASS, 'temporal_shape': 'point', 'window_start': peak, 'window_end': peak, 'peak_date': peak, 'milestone_id': None,
            'is_irreversibility_milestone': False, 'signed_intensity': 0.5, 'raw_intensity': 0.5, 'valence': 'favourable', 'is_adverse': False,
            'active_sentences': [], 'contributing_systems': [], 'suppression_state': {}, 'peak_basis': 'test', 'calibration_state': 'structural_prior', 'source': 'live'}


@pytest.fixture
def world(conn, monkeypatch):                                                # noqa: F811
    conn.execute(WINDOWS_DDL)
    conn.execute(BUILD_STATE_DDL)
    conn.execute('CREATE TABLE bg_gochara_arcs (body text, arc_fingerprint text, substrate_version text)')
    conn.execute("CREATE TABLE gochara_resonance_map (chart_id uuid, generation text NOT NULL DEFAULT 'legacy', event_class text)")
    conn.execute("CREATE VIEW gochara_resonance_map_served AS SELECT * FROM gochara_resonance_map WHERE generation = 'legacy'")
    conn.execute("INSERT INTO gochara_resonance_map VALUES (%s, 'legacy', %s), (%s, %s, %s)", (CHART, EVENT_CLASS, CHART, CAND, EVENT_CLASS))
    monkeypatch.setattr(gochara_mod.RM, 'fetch_resonance_targets', lambda c, chart, ec, generation=None: [SimpleNamespace(target_ref=f'{ec}:t1')])
    conn.execute('CREATE UNIQUE INDEX uq_gochara_v2_test_natural_key ON kala_gochara_windows_v2 (chart_id, event_class, peak_date, generation)')
    NEXT_ROWS[:] = [window_row(date(2027, 3, 1)), window_row(date(2027, 9, 1))]
    monkeypatch.setattr(gochara_mod, 'materialize_event_class',
                        lambda *a, **k: MaterializeResult(rows=list(NEXT_ROWS), contacts_evaluated=2, targets_resolved=1))
    return conn


def seed_served(conn):
    """The ordinary partition: windows and ledger the next successful ordinary rebuild replaces (and a candidate run must never touch)."""
    conn.execute("INSERT INTO kala_gochara_windows_v2 (chart_id, event_class, temporal_shape, peak_date, generation) "
                 "VALUES (%s, %s, 'point', '2026-01-01', %s), (%s, %s, 'point', '2026-02-01', %s)", (CHART, EVENT_CLASS, SERVED, CHART, EVENT_CLASS, SERVED))
    conn.execute("INSERT INTO kala_gochara_v2_build_state (chart_id, event_class, generation, class_fingerprint, grammar_version, arc_engine_version, "
                 "horizon_start_date, horizon_end_date, horizon_status) VALUES (%s, %s, %s, 'served-fp', 'g', 'a', '2026-01-01', '2027-01-01', 'full_backfill')",
                 (CHART, EVENT_CLASS, SERVED))


def served_state(conn, table, chart=CHART):
    """Every column of every '2.0' row of the chart: the byte-level state a candidate run must leave alone."""
    return conn.execute(f'SELECT count(*), md5(coalesce(string_agg(t::text, $$|$$ ORDER BY t::text), $$$$)) FROM {table} t WHERE chart_id = %s AND generation = %s',
                        (chart, SERVED)).fetchone()


def cells(row):
    """A result row as a tuple, whichever row factory the connection uses (the writer fixture uses dict rows, the teardown fixture tuples)."""
    return tuple(row.values()) if isinstance(row, dict) else tuple(row)


def generations(conn, table, chart=CHART):
    return dict(cells(r) for r in conn.execute(f'SELECT generation, count(*) FROM {table} WHERE chart_id = %s GROUP BY generation', (chart,)).fetchall())


def run_class(conn, build_id):
    ctx = ContextSpec(asset_id='ka_gochara', build_id=build_id, db_conn=conn, config={'chart_id': CHART, 'birth_params': BIRTH, 'now_date': '2026-06-01'})
    return gochara_mod.KaGocharaWriter(), ctx


def g1(module, conn):
    seed_served(conn)
    before = (served_state(conn, 'kala_gochara_windows_v2'), served_state(conn, 'kala_gochara_v2_build_state'))
    writer, ctx = run_class(conn, BUILD)
    result = module.KaGocharaWriter().run_substep(ctx, SubStep(EVENT_CLASS))
    assert result.rows_inserted == 2
    assert generations(conn, 'kala_gochara_windows_v2') == {SERVED: 2, CAND: 2}, 'the candidate run wrote outside its own generation'
    assert generations(conn, 'kala_gochara_v2_build_state') == {SERVED: 1, CAND: 1}
    assert (served_state(conn, 'kala_gochara_windows_v2'), served_state(conn, 'kala_gochara_v2_build_state')) == before, 'a candidate run changed a served row'


@BOTH
def test_g1_a_candidate_run_writes_only_its_own_partition_and_leaves_the_served_rows_byte_identical(world, tmp_path, reverted):
    # reversion: the writer's generation resolver ignores the bound candidate (the pre-change behaviour: always '2.0')
    verdict(reverted, g1, gochara_mod, tmp_path, 'return GENERATION_V2 if candidate is None else candidate.generation', 'return GENERATION_V2', world)


def test_g2_an_ordinary_run_keeps_writing_the_2_0_partition(world):
    writer, ctx = run_class(world, str(uuid.uuid4()))                         # a build bound to no candidate
    assert writer.run_substep(ctx, SubStep(EVENT_CLASS)).rows_inserted == 2
    assert generations(world, 'kala_gochara_windows_v2') == {SERVED: 2}
    assert generations(world, 'kala_gochara_v2_build_state') == {SERVED: 1}


def g3(module, conn):
    writer, ctx = run_class(conn, BUILD)
    module.KaGocharaWriter().run_substep(ctx, SubStep(EVENT_CLASS))
    conn.execute("UPDATE kala_gochara_v2_build_state SET class_fingerprint = 'stale' WHERE chart_id = %s AND generation = %s", (CHART, CAND))     # inputs changed: not a delta skip
    NEXT_ROWS[:] = [window_row(date(2028, 1, 1))]                                  # the same candidate, rebuilt with a different result: replace, never accrete (§N.3)
    module.KaGocharaWriter().run_substep(ctx, SubStep(EVENT_CLASS))
    assert [cells(r)[0] for r in conn.execute('SELECT peak_date FROM kala_gochara_windows_v2 WHERE chart_id = %s AND generation = %s', (CHART, CAND)).fetchall()] == [date(2028, 1, 1)]


@BOTH
def test_g3_a_second_run_of_the_same_candidate_replaces_its_partition(world, tmp_path, reverted):
    # reversion: the delete-then-insert is aimed at the ordinary partition, so the candidate's earlier rows pile up
    verdict(reverted, g3, gochara_mod, tmp_path,
            '[chart_id, event_class, generation],\n            )\n\n        inserted = 0', '[chart_id, event_class, GENERATION_V2],\n            )\n\n        inserted = 0', world)


def g4(module, conn):
    ledger_fp = class_fingerprint(EVENT_CLASS, GRAMMAR_VERSION, [f'{EVENT_CLASS}:t1'], gochara_mod.BODIES, {})
    conn.execute("INSERT INTO kala_gochara_v2_build_state (chart_id, event_class, generation, class_fingerprint, grammar_version, arc_engine_version, "
                 "horizon_start_date, horizon_end_date, horizon_status) VALUES (%s, %s, %s, %s, 'g', 'a', '2026-01-01', '2027-01-01', 'full_backfill')",
                 (CHART, EVENT_CLASS, SERVED, ledger_fp))                          # the ORDINARY ledger already holds exactly this fingerprint
    writer, ctx = run_class(conn, BUILD)
    assert [s.key for s in module.KaGocharaWriter()._plan_event_classes(ctx)] == [EVENT_CLASS], 'the candidate build was skipped on the ordinary ledger'
    unbound_writer, unbound = run_class(conn, str(uuid.uuid4()))
    assert module.KaGocharaWriter()._plan_event_classes(unbound) == []      # an ordinary rebuild still skips what its own ledger holds


@BOTH
def test_g4_a_candidate_plan_is_not_skipped_on_the_ordinary_ledger(world, tmp_path, reverted):
    # reversion: the plan reads the ordinary '2.0' ledger for a candidate-bound build
    verdict(reverted, g4, gochara_mod, tmp_path,
            'self._stored_fingerprint(query, chart_id, event_class, window_generation)', 'self._stored_fingerprint(query, chart_id, event_class, GENERATION_V2)', world)


def g5(module, ctl):                                                            # noqa: F811
    ctl.execute(WINDOWS_DDL)
    ctl.execute(BUILD_STATE_DDL)
    a = make_run(ctl, 'failed', generation='a', plan=('ka_gochara',))
    for generation in ('a', SERVED, 'legacy'):
        ctl.execute("INSERT INTO kala_gochara_windows_v2 (chart_id, event_class, temporal_shape, peak_date, generation) VALUES (%s, %s, 'point', '2026-01-01', %s), "
                    "(%s, %s, 'point', '2026-02-01', %s)", (CANONICAL_CHART, EVENT_CLASS, generation, CANONICAL_CHART, EVENT_CLASS, generation))
        ctl.execute("INSERT INTO kala_gochara_v2_build_state (chart_id, event_class, generation, class_fingerprint, grammar_version, arc_engine_version, "
                    "horizon_start_date, horizon_end_date, horizon_status) VALUES (%s, %s, %s, 'fp', 'g', 'a', '2026-01-01', '2027-01-01', 'full_backfill')",
                    (CANONICAL_CHART, EVENT_CLASS, generation))
    ctl.execute("INSERT INTO kala_gochara_windows_v2 (chart_id, event_class, temporal_shape, peak_date, generation) VALUES (%s, %s, 'point', '2026-01-01', 'a')",
                (OTHER_CHART, EVENT_CLASS))                                         # another chart that reuses the generation name
    ctl.commit()
    kept = {t: ctl.execute(f'SELECT md5(coalesce(string_agg(x::text, $$|$$ ORDER BY x::text), $$$$)) FROM {t} x WHERE NOT (chart_id = %s AND generation = %s)',
                           (CANONICAL_CHART, 'a')).fetchone()[0] for t in ('kala_gochara_windows_v2', 'kala_gochara_v2_build_state')}
    result = module.teardown(ctl, run_id=a.build_id)
    assert result['deleted'].get('kala_gochara_windows_v2') == 2 and result['deleted'].get('kala_gochara_v2_build_state') == 1
    assert generations(ctl, 'kala_gochara_windows_v2', CANONICAL_CHART) == {SERVED: 2, 'legacy': 2} and generations(ctl, 'kala_gochara_v2_build_state', CANONICAL_CHART) == {SERVED: 1, 'legacy': 1}
    assert {t: ctl.execute(f'SELECT md5(coalesce(string_agg(x::text, $$|$$ ORDER BY x::text), $$$$)) FROM {t} x WHERE NOT (chart_id = %s AND generation = %s)',
                           (CANONICAL_CHART, 'a')).fetchone()[0] for t in kept} == kept, 'the teardown changed a row that is not the run\'s own'
    assert result['generation_scoped_writes_removed'] == [{'asset_id': 'ka_gochara', 'table': 'kala_gochara_windows_v2', 'generation': 'a',
                                                           'rows_deleted': 2, 'writer_run_id': a.build_id}]


@BOTH
def test_g5_the_teardown_removes_the_runs_gochara_partition_and_nothing_else(ctl, tmp_path, reverted):                  # noqa: F811
    # reversion: the teardown list no longer names the windows table (the pre-change list)
    verdict(reverted, g5, rebuild_control, tmp_path, "'gochara_resonance_map', 'kala_gochara_windows_v2',\n", "'gochara_resonance_map',\n", ctl)
