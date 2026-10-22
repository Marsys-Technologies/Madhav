"""SR-K9-PUBLISHABLE D3: ka_sangam, ka_vighnakara and ka_gochara attest their
`<writer>:inputs` grain under the CANDIDATE generation and read the candidate's
predicates, never the published head's.

Sources. The grain contract is `services/kala_core/publication.py:52-68`
(every planned writer, exactly the planned keys, state rows|zero_rows) and
`manifest.attest_grain`; the key shape `<writer>:inputs` is ka_yojaka's
(`ka_yojaka:inputs`). Generation scoping is ORCHESTRATOR_CONVERGENCE_CLOSE §7.1
(planning is a read-only call). Nothing here restates a classical value: the
signal ids, dates and generations are PLANTED labels (B.10), and every
expectation is a label consequence, not a captured output.

Every case drives the writer through the REAL `_drive_substeps` with the
context the runner builds (`config` = chart_id + birth_params only).
"""
from datetime import date
from types import SimpleNamespace
import uuid

import psycopg
from psycopg.rows import dict_row
import pytest

from pipeline.orchestrator import asset_runner
from pipeline.orchestrator.writers import ContextSpec, WriterResult
from pipeline.orchestrator.writers import ka_gochara as gochara_mod
from pipeline.orchestrator.writers import ka_sangam as sangam_mod
from pipeline.orchestrator.writers import ka_vighnakara as vighnakara_mod

CHART = '00000000-0000-0000-0000-0000000000a1'
BUILD = '00000000-0000-0000-0000-0000000000b1'
CAND = 'candidate:' + BUILD
HEAD = 'published-head-1'
BIRTH = {'datetime_iso': '1984-02-05T10:43:00+05:30'}
RULE = '{"peak": "%s"}'


@pytest.fixture
def conn(kala_db_dsn):
    with psycopg.connect(kala_db_dsn, row_factory=dict_row) as c:
        schema = 'k9wg_' + uuid.uuid4().hex
        c.execute(f'CREATE SCHEMA "{schema}"')
        c.execute(f'SET search_path TO "{schema}", public')
        c.execute('CREATE TABLE kala_layer_candidate (chart_id uuid, generation text, build_id uuid, state text, '
                  'conventions jsonb, PRIMARY KEY(chart_id, generation))')
        c.execute('CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY, generation text)')
        c.execute('CREATE TABLE kala_layer_candidate_grain (chart_id uuid, generation text, grain_key text, '
                  'result_state text, input_vector text, recorded_at timestamptz DEFAULT now(), '
                  'PRIMARY KEY(chart_id, generation, grain_key))')
        c.execute('CREATE TABLE asset_throughput (chart_id uuid, asset_id text, last_built_at timestamptz, '
                  'rows_written integer)')
        c.execute('CREATE TABLE kala_activation_predicates (id serial, chart_id uuid, ayanamsha_id text, '
                  'signal_id text, signature_class text, dasha_eligibility_rule_jsonb jsonb, '
                  'transit_trigger_jsonb jsonb, strength_affliction_hook_jsonb jsonb, '
                  'derivation_ledger_jsonb jsonb, generation text, mechanism_route text, '
                  'conclusion_state_jsonb jsonb)')
        c.execute('CREATE TABLE bodha_msr_signals (signal_id text, dignity_score numeric, '
                  'configuration_jsonb jsonb, domains_affected_array text[])')
        c.execute('CREATE TABLE build_substep_progress (chart_id uuid, asset_id text, substep_key text, '
                  'build_fingerprint text, rows_written integer, completed_at timestamptz, '
                  'PRIMARY KEY(chart_id, asset_id, substep_key))')
        c.execute('CREATE TABLE kala_convergence (convergence_id serial, chart_id uuid, signal_id text, mode text, '
                  'peak_date date, convergence_score numeric, orb_strength numeric, window_start date, '
                  'window_end date, horizon_tier text)')
        c.execute('CREATE TABLE kala_obstruction (id serial, chart_id uuid, convergence_id integer, signal_id text, '
                  'obstruction_type text, severity text, severity_score numeric, override_score numeric, '
                  'obstruction_detail jsonb, source_citation text, generation text)')
        c.execute("INSERT INTO kala_layer_candidate VALUES (%s, %s, %s, 'building', '{}'::jsonb)",
                  (CHART, CAND, BUILD))
        c.execute("INSERT INTO kala_layer_candidate VALUES (%s, %s, %s, 'published', '{}'::jsonb)",
                  (CHART, HEAD, str(uuid.uuid4())))
        c.execute('INSERT INTO kala_layer_head VALUES (%s, %s)', (CHART, HEAD))
        try:
            yield c
        finally:
            c.rollback()


def predicate(conn, generation, signal, peak):
    conn.execute(
        "INSERT INTO kala_activation_predicates (chart_id, ayanamsha_id, signal_id, signature_class, "
        "dasha_eligibility_rule_jsonb, transit_trigger_jsonb, strength_affliction_hook_jsonb, "
        "derivation_ledger_jsonb, generation, mechanism_route, conclusion_state_jsonb) "
        "VALUES (%s, 'lahiri_chitrapaksha', %s, 'YOGA', %s::jsonb, '{}', '{}', '{}', %s, 'admitted', "
        """'{"effective_state":"in_force","scored":"true"}')""",
        (CHART, signal, RULE % peak, generation))


def drive(conn, writer, asset_id, build=BUILD, dry_run=False):
    ctx = ContextSpec(asset_id=asset_id, build_id=build, db_conn=conn, dry_run=dry_run,
                      config={'chart_id': CHART, 'birth_params': BIRTH})
    with conn.cursor() as cur:
        return asset_runner._drive_substeps(conn, cur, build, CHART, asset_id, writer, ctx, defer_commits=True), ctx


def grains(conn):
    return {(r['generation'], r['grain_key']): (r['result_state'], r['input_vector'])
            for r in conn.execute('SELECT generation, grain_key, result_state, input_vector '
                                  'FROM kala_layer_candidate_grain').fetchall()}


# ── ka_sangam ───────────────────────────────────────────────────────────────

@pytest.fixture
def sangam(conn, monkeypatch):
    cls = sangam_mod._LegacyKaSangamWriter
    monkeypatch.setattr(sangam_mod, 'KaDashaKalaService', lambda c: object())
    monkeypatch.setattr(cls, '_build_enrichment_context', lambda self, c, ch: None)
    monkeypatch.setattr(cls, '_resolve_native_chart_context', lambda self, c, ch, bp: None)
    monkeypatch.setattr(cls, '_derive_birth_year', lambda self, c, ch: 1984)
    monkeypatch.setattr(cls, '_build_house_lord_map', lambda self, c, ch: {})
    # The windowing itself is not under test: each class/lifetime substep is a no-op.
    def near(self, c, ch, dry):
        # Stands in for the windowing: it only leaves the rows the test plants.
        for _ in range(getattr(self, 'planted_rows', 0)):
            c.execute("INSERT INTO kala_convergence (chart_id, signal_id, peak_date, horizon_tier) "
                      "VALUES (%s, 'S-CAND', '2032-02-02', 'near')", (ch,))
        return WriterResult('ka_sangam', getattr(self, 'planted_rows', 0))
    monkeypatch.setattr(cls, '_substep_near', near)
    monkeypatch.setattr(cls, '_substep_lifetime', lambda self, c, ch, i, dry: WriterResult('ka_sangam', 0))
    predicate(conn, HEAD, 'S-HEAD', '2031-01-01')
    predicate(conn, CAND, 'S-CAND', '2032-02-02')
    return sangam_mod.KaSangamWriter()


def test_sangam_reads_the_candidate_predicates_and_attests_under_the_candidate(conn, sangam):
    (_, _, _), _ = drive(conn, sangam, 'ka_sangam')
    assert {p['signal_id'] for p in sangam._pred_dicts} == {'S-CAND'}, 'predicates read from the head, not the candidate'
    held = grains(conn)
    assert set(held) == {(CAND, 'ka_sangam:inputs')}, 'sangam must attest exactly its grain under the candidate generation'
    assert held[(CAND, 'ka_sangam:inputs')][0] == 'zero_rows'


def test_sangam_grain_is_rows_once_convergence_exists_and_binds_the_candidate_inputs(conn, sangam):
    sangam.planted_rows = 1
    drive(conn, sangam, 'ka_sangam')
    state, vector = grains(conn)[(CAND, 'ka_sangam:inputs')]
    assert state == 'rows' and len(vector) == 64
    # A different candidate predicate set must change the attested input vector.
    conn.execute('DELETE FROM kala_layer_candidate_grain')
    conn.execute("UPDATE kala_activation_predicates SET dasha_eligibility_rule_jsonb = %s::jsonb WHERE signal_id = 'S-CAND'",
                 (RULE % '2040-04-04',))
    drive(conn, sangam_mod.KaSangamWriter(), 'ka_sangam')
    assert grains(conn)[(CAND, 'ka_sangam:inputs')][1] != vector


def test_sangam_input_drift_inside_one_candidate_needs_a_new_candidate(conn, sangam):
    drive(conn, sangam, 'ka_sangam')
    conn.execute("UPDATE kala_activation_predicates SET dasha_eligibility_rule_jsonb = %s::jsonb WHERE signal_id = 'S-CAND'",
                 (RULE % '2040-04-04',))
    with pytest.raises(ValueError, match='new candidate required'):
        drive(conn, sangam_mod.KaSangamWriter(), 'ka_sangam')


def test_sangam_unbound_build_keeps_the_head_read_and_attests_nothing(conn, sangam):
    drive(conn, sangam, 'ka_sangam', build=str(uuid.uuid4()))
    assert {p['signal_id'] for p in sangam._pred_dicts} == {'S-HEAD'}
    assert grains(conn) == {}


def test_sangam_planning_is_read_only(conn, sangam):
    ctx = ContextSpec(asset_id='ka_sangam', build_id=BUILD, db_conn=conn,
                      config={'chart_id': CHART, 'birth_params': BIRTH})
    steps = sangam.plan_substeps(ctx)
    assert steps[-1].key == 'grain:inputs'
    assert grains(conn) == {}, 'plan_substeps must not attest (CONVERGENCE_CLOSE §7.1: read-only planning)'


# ── ka_vighnakara ───────────────────────────────────────────────────────────

@pytest.fixture
def vighnakara(conn, monkeypatch):
    cls = vighnakara_mod._LegacyKaVighnakaraWriter
    monkeypatch.setattr(cls, '_resolve_native_location', staticmethod(lambda c, ch, bp: {}))
    monkeypatch.setattr(cls, '_fetch_combustion_orbs', lambda self, c: {})
    monkeypatch.setattr(cls, '_fetch_natal_lagna_lon', lambda self, c, ch: None)
    monkeypatch.setattr(cls, '_fetch_natal_moon_lon', lambda self, c, ch: None)
    monkeypatch.setattr(vighnakara_mod, 'resolve_birth_date', lambda c, ch: date(1984, 2, 5))
    monkeypatch.setattr(vighnakara_mod, 'load_dasha_timeline', lambda c, ch, ayanamsha_id, birth_date: {})
    monkeypatch.setattr(vighnakara_mod, 'resolve_activation_windows', lambda rule, tl, birth_date: SimpleNamespace(
        activation_peak=date.fromisoformat(rule['peak'])))
    monkeypatch.setattr(vighnakara_mod, '_detect_all', lambda **kw: [{
        'obstruction_type': 'planted', 'severity': 'low', 'severity_score': 0.1, 'override_score': 0.0, 'detail': {}}])
    predicate(conn, HEAD, 'S-HEAD', '2031-01-01')
    predicate(conn, CAND, 'S-CAND', '2032-02-02')
    return vighnakara_mod.KaVighnakaraWriter()


def convergence(conn):
    conn.execute("INSERT INTO kala_convergence (chart_id, signal_id, mode, peak_date, convergence_score) "
                 "VALUES (%s, 'S-CONV', 'A', '2030-03-03', 0.9)", (CHART,))


def test_vighnakara_reads_candidate_predicates_and_attests_under_the_candidate(conn, vighnakara):
    convergence(conn)
    drive(conn, vighnakara, 'ka_vighnakara')
    signals = {r['signal_id'] for r in conn.execute('SELECT signal_id FROM kala_obstruction').fetchall()}
    assert signals == {'S-CONV', 'S-CAND'}, 'dasha-anchor obstruction must come from the candidate predicates'
    held = grains(conn)
    assert set(held) == {(CAND, 'ka_vighnakara:inputs')}
    assert held[(CAND, 'ka_vighnakara:inputs')][0] == 'rows'


def test_vighnakara_without_convergence_still_attests_an_honest_zero(conn, vighnakara):
    drive(conn, vighnakara, 'ka_vighnakara')
    assert conn.execute('SELECT count(*) AS n FROM kala_obstruction').fetchone()['n'] == 0
    assert grains(conn)[(CAND, 'ka_vighnakara:inputs')][0] == 'zero_rows'


def test_vighnakara_unbound_build_keeps_the_head_read_and_attests_nothing(conn, vighnakara):
    convergence(conn)
    drive(conn, vighnakara, 'ka_vighnakara', build=str(uuid.uuid4()))
    assert {r['signal_id'] for r in conn.execute('SELECT signal_id FROM kala_obstruction').fetchall()} == {'S-CONV', 'S-HEAD'}
    assert grains(conn) == {}


# ── ka_gochara ──────────────────────────────────────────────────────────────

@pytest.fixture
def gochara(conn, monkeypatch):
    conn.execute("CREATE TABLE gochara_resonance_map (chart_id uuid, generation text NOT NULL DEFAULT 'legacy', event_class text)")
    # stand-in for the served view of migration 1404 (its real definition is tested in test_resmap_generation.py): an unbound build reads the served partition
    conn.execute("CREATE VIEW gochara_resonance_map_served AS SELECT * FROM gochara_resonance_map WHERE generation = 'legacy'")
    conn.execute('CREATE TABLE kala_gochara_windows_v2 (chart_id uuid, generation text)')
    conn.execute('CREATE TABLE bg_gochara_arcs (body text, arc_fingerprint text, substrate_version text)')
    conn.execute('CREATE TABLE kala_gochara_v2_build_state (chart_id uuid, event_class text, generation text, '
                 'class_fingerprint text)')
    monkeypatch.setattr(gochara_mod.RM, 'fetch_resonance_targets',
                        lambda c, chart, ec, generation=None: [SimpleNamespace(target_ref=f'{ec}:t1')])
    monkeypatch.setattr(gochara_mod.KaGocharaWriter, 'run_substep', _class_substep(gochara_mod.KaGocharaWriter.run_substep))
    return gochara_mod.KaGocharaWriter()


def _class_substep(real):
    """Event-class windowing is not under test; the grain substep is the real one."""
    def run_substep(self, ctx, step):
        if step.key == 'grain:inputs':
            return real(self, ctx, step)
        return WriterResult('ka_gochara', 0)
    return run_substep


def test_gochara_empty_plan_still_attests_a_zero_rows_grain_under_the_candidate(conn, gochara):
    (rows, _, _), _ = drive(conn, gochara, 'ka_gochara')
    assert rows == 0
    held = grains(conn)
    assert set(held) == {(CAND, 'ka_gochara:inputs')}
    assert held[(CAND, 'ka_gochara:inputs')][0] == 'zero_rows'


def test_gochara_with_windows_attests_rows_and_every_class_fingerprint_is_in_the_vector(conn, gochara):
    conn.execute("INSERT INTO gochara_resonance_map VALUES (%s, %s, 'career'), (%s, %s, 'health')", (CHART, CAND, CHART, CAND))     # the candidate's own partition (migration 1404)
    conn.execute("INSERT INTO kala_gochara_windows_v2 VALUES (%s, '2.0')", (CHART,))
    drive(conn, gochara, 'ka_gochara')
    state, vector = grains(conn)[(CAND, 'ka_gochara:inputs')]
    assert state == 'rows'
    # A third populated class changes the writer's own input identity.
    conn.execute('DELETE FROM kala_layer_candidate_grain')
    conn.execute("INSERT INTO gochara_resonance_map VALUES (%s, %s, 'wealth')", (CHART, CAND))
    drive(conn, gochara_mod.KaGocharaWriter(), 'ka_gochara')
    assert grains(conn)[(CAND, 'ka_gochara:inputs')][1] != vector


def test_gochara_candidate_bound_build_plans_from_its_own_resonance_rows_not_the_served_ones(conn, gochara):
    # SR-K9-RESONANCE-MAP: the served partition ('legacy') holds a class the candidate does not; the candidate-bound plan ignores it (the candidate pairs its windows with its own targets)
    conn.execute("INSERT INTO gochara_resonance_map VALUES (%s, 'legacy', 'marriage'), (%s, %s, 'career')", (CHART, CHART, CAND))
    ctx = ContextSpec(asset_id='ka_gochara', build_id=BUILD, db_conn=conn, config={'chart_id': CHART, 'birth_params': BIRTH})
    assert [s.key for s in gochara._plan_event_classes(ctx)] == ['career']
    unbound = ContextSpec(asset_id='ka_gochara', build_id=str(uuid.uuid4()), db_conn=conn, config={'chart_id': CHART, 'birth_params': BIRTH})
    assert [s.key for s in gochara._plan_event_classes(unbound)] == ['marriage']      # an ordinary rebuild reads what is served


def test_gochara_unbound_build_attests_nothing_and_plans_as_before(conn, gochara):
    drive(conn, gochara, 'ka_gochara', build=str(uuid.uuid4()))
    assert grains(conn) == {}


def test_gochara_dry_run_neither_plans_nor_attests_the_grain(conn, gochara):
    _, ctx = drive(conn, gochara, 'ka_gochara', dry_run=True)
    assert all(s.key != 'grain:inputs' for s in gochara.plan_substeps(ctx))
    assert grains(conn) == {}


def test_once_attested_the_plan_is_complete_so_noop_completion_can_promote(conn, gochara):
    drive(conn, gochara, 'ka_gochara')
    ctx = ContextSpec(asset_id='ka_gochara', build_id=BUILD, db_conn=conn, config={'chart_id': CHART})
    assert gochara.plan_substeps(ctx) == [], 'a finished candidate-bound plan must be empty (D-1.6 probe)'
