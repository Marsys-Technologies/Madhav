"""
test_ph_nimitta_measured_robustness.py -- SS N-391 (definition ratified N-394).

The previous commit (N-341 B5) made ph_nimitta store NULL for
phala_anchors.ayanamsha_robustness because nothing measured it. All five ayanamshas are kept,
so it is now MEASURED per anchor:

  an ayanamsha X SUPPORTS an anchor (MSR signal S, ayanamsha A, key T = (signal_type_id,
  varga_id), event class E, own pratijna status P) iff X has >= 1 bodha_msr_signals row for the
  chart with the same key T AND bodha_pratijna (chart, X, E).status == P. robustness = number of
  supporting ayanamshas among the five canonical ones (own included). X is "built" iff the chart
  has >= 1 bodha_msr_signals row for X; if fewer than all five canonical ayanamshas are built the
  value is None (the 0..5 scale cannot tell "not built" from "disagrees").

Layers pinned here:
  * the pure function services.ph_nimitta.engine.measure_ayanamsha_robustness (named cases),
  * the writer path (fake connection feeding five built ayanamshas) down to the stored anchor
    value, the lift-vector modifier and the posterior,
  * a failed query leaves None (never a number),
  * an ast guard that the writer no longer passes a literal for ayanamsha_robustness.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS
from services.ph_nimitta.engine import (
    NimittaContext,
    _robustness_modifier,
    compute_posterior,
    derive_anchor_from_convergence,
    measure_ayanamsha_robustness,
)

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_WRITER = _SIDECAR / 'pipeline' / 'orchestrator' / 'writers' / 'ph_nimitta.py'

FIVE = list(CANONICAL_AYANAMSHAS)
OWN = FIVE[0]
KEY = ('SIG_TYPE_A', 'D1')
EVENT = 'EC_CAREER'


def _measure(signals_by_aya, status_by_aya_event, own=OWN, key=KEY, event=EVENT, own_status='conditional',
             canonical=None):
    return measure_ayanamsha_robustness(
        own, key, event, own_status, signals_by_aya, status_by_aya_event,
        FIVE if canonical is None else canonical,
    )


def _all_built(extra_key=('SIG_TYPE_FILLER', 'D1')):
    """Every canonical ayanamsha is built (has a row); each also has an unrelated filler row."""
    return {a: {KEY, extra_key} for a in FIVE}


def _all_conditional():
    return {(a, EVENT): 'conditional' for a in FIVE}


# ----------------------------------------------------------------- pure function


class TestMeasureAyanamshaRobustnessPure:
    def test_canonical_five_is_the_repo_constant(self):
        assert len(FIVE) == 5 and OWN in FIVE

    def test_case1_all_five_agree_is_5(self):
        assert _measure(_all_built(), _all_conditional()) == 5

    def test_case2_one_ayanamsha_has_the_signal_but_a_different_pratijna_status_is_4(self):
        status = _all_conditional()
        status[(FIVE[3], EVENT)] = 'contradicted'          # has the signal, DISAGREES on status
        assert _measure(_all_built(), status) == 4

    def test_case3_signal_missing_under_one_built_ayanamsha_is_4(self):
        sigs = _all_built()
        sigs[FIVE[2]] = {('SIG_TYPE_FILLER', 'D1')}        # IS built (has a row), no matching signal
        assert FIVE[2] in sigs and sigs[FIVE[2]]
        assert _measure(sigs, _all_conditional()) == 4

    def test_case4_fewer_than_five_built_is_none(self):
        sigs = _all_built()
        del sigs[FIVE[4]]                                   # not built at all
        assert _measure(sigs, _all_conditional()) is None
        sigs2 = _all_built()
        sigs2[FIVE[4]] = set()                              # an empty set is also not built
        assert _measure(sigs2, _all_conditional()) is None

    def test_only_own_supports_is_1(self):
        sigs = {a: {('SIG_TYPE_FILLER', 'D1')} for a in FIVE}
        sigs[OWN] = {KEY}
        assert _measure(sigs, _all_conditional()) == 1

    def test_all_built_but_status_disagrees_everywhere_but_own_is_1(self):
        status = {(a, EVENT): 'denied' for a in FIVE}
        status[(OWN, EVENT)] = 'conditional'
        assert _measure(_all_built(), status) == 1

    def test_varga_is_part_of_the_signal_key(self):
        sigs = _all_built()
        sigs[FIVE[1]] = {('SIG_TYPE_A', 'D9'), ('SIG_TYPE_FILLER', 'D1')}   # same type, other varga
        assert _measure(sigs, _all_conditional()) == 4

    def test_null_varga_matches_only_null_varga(self):
        key = ('SIG_TYPE_A', None)
        sigs = {a: {key} for a in FIVE}
        status = _all_conditional()
        assert _measure(sigs, status, key=key) == 5
        sigs[FIVE[1]] = {('SIG_TYPE_A', 'D1')}
        assert _measure(sigs, status, key=key) == 4

    def test_a_missing_pratijna_row_does_not_match_a_present_status(self):
        status = _all_conditional()
        del status[(FIVE[1], EVENT)]
        assert _measure(_all_built(), status) == 4

    def test_unknown_own_status_or_event_or_key_is_none_not_a_match_of_absences(self):
        status = {}
        assert _measure(_all_built(), status, own_status=None) is None
        assert _measure(_all_built(), _all_conditional(), event=None) is None
        assert _measure(_all_built(), _all_conditional(), key=None) is None

    def test_non_canonical_own_ayanamsha_is_none(self):
        assert _measure(_all_built(), _all_conditional(), own='not_a_canonical_aya') is None

    def test_result_is_never_zero_or_a_default_when_unmeasurable(self):
        sigs = _all_built()
        del sigs[FIVE[1]]
        assert _measure(sigs, _all_conditional()) is None


# ----------------------------------------------------------------- writer path

_SIGNAL_ID = '11111111-1111-1111-1111-111111111111'
_CHART = 'chart-test'
_ROW = {'convergence_id': 7, 'signal_id': _SIGNAL_ID}


class _Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.pending = []

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def execute(self, sql, params=None):
        self.pending = []
        self.conn.executed.append(sql)
        if sql.startswith(('SAVEPOINT', 'RELEASE', 'ROLLBACK')):
            return
        if 'FROM bodha_msr_signals' in sql and 'GROUP BY' in sql:
            if self.conn.fail_grouped_query:
                raise RuntimeError('simulated: bodha_msr_signals grouped query failed')
            groups = {}
            for aya, key_list in self.conn.signals_by_aya.items():
                for (stype, varga) in key_list:
                    groups.setdefault((aya, stype, varga), [])
            # the anchor signal belongs to OWN under KEY
            groups.setdefault((OWN, KEY[0], KEY[1]), []).append(_SIGNAL_ID)
            self.pending = [
                {'ayanamsha_id': a, 'signal_type_id': t, 'varga_id': v, 'anchor_signal_ids': ids}
                for (a, t, v), ids in groups.items()
            ]
        elif 'FROM bodha_msr_signals' in sql:
            self.pending = [{
                'signal_id': _SIGNAL_ID, 'ayanamsha_id': OWN, 'domain': 'career',
                'signature_class': 'SUBSYSTEM', 'salience_score': 0.8,
            }]
        elif 'FROM brahma_event_ontology' in sql:
            self.pending = [{'event_class_id': EVENT, 'domain': 'career', 'base_rate_by_age': {}}]
        elif 'FROM bodha_pratijna' in sql:
            self.pending = [
                {'ayanamsha_id': a, 'event_class_id': e, 'status': s, 'grade': 5.0}
                for (a, e), s in self.conn.status_by_aya_event.items()
            ]
        elif 'FROM kala_activation_predicates' in sql:
            self.pending = [{'signal_id': _SIGNAL_ID, 'mscc': 2}]

    def fetchall(self):
        return self.pending


class _Conn:
    def __init__(self, signals_by_aya, status_by_aya_event, fail_grouped_query=False):
        self.signals_by_aya = signals_by_aya
        self.status_by_aya_event = status_by_aya_event
        self.fail_grouped_query = fail_grouped_query
        self.executed = []

    def cursor(self, *_a, **_k):
        return _Cursor(self)


def _anchor_via_writer(conn):
    from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
    w = PhNimittaWriter()
    w._resolve_base_rate = lambda row, post: 0.10     # fixed base: nothing here may hit the 0.95 clamp
    signal_meta = w._load_signal_meta(conn, [_SIGNAL_ID])
    posterior_m = w._load_posterior_meta(conn, _CHART, signal_meta)
    ctx = w._build_ctx(dict(_ROW), signal_meta, {}, {}, {}, posterior_m)
    return derive_anchor_from_convergence(dict(_ROW), ctx, n_independent=4), ctx


def _fixture_signals():
    return {a: {KEY, ('SIG_TYPE_FILLER', 'D1')} for a in FIVE}


class TestWriterPathMeasuresRobustness:
    def test_five_agree_stores_5(self):
        a, ctx = _anchor_via_writer(_Conn(_fixture_signals(), _all_conditional()))
        assert ctx.ayanamsha_robustness == 5
        assert a.ayanamsha_robustness == 5
        assert a.lift_vector['ayanamsha_robustness_status'] == 'measured'

    def test_exactly_one_ayanamsha_disagrees_stores_4_and_scales_the_posterior_by_exactly_the_modifier(self):
        disagree = _all_conditional()
        disagree[(FIVE[3], EVENT)] = 'contradicted'
        a4, ctx4 = _anchor_via_writer(_Conn(_fixture_signals(), disagree))
        a5, _ctx5 = _anchor_via_writer(_Conn(_fixture_signals(), _all_conditional()))

        assert a4.ayanamsha_robustness == 4
        assert a5.ayanamsha_robustness == 5
        # lift-vector modifier equals the engine's modifier for the measured value
        assert a4.lift_vector['ayanamsha_robustness_modifier'] == pytest.approx(_robustness_modifier(4), abs=1e-4)
        assert a5.lift_vector['ayanamsha_robustness_modifier'] == pytest.approx(_robustness_modifier(5), abs=1e-4)
        assert a4.lift_vector['ayanamsha_robustness_status'] == 'measured'

        # no clamp involved, so the two posteriors differ by exactly the modifier ratio
        assert 0.02 < a4.posterior < 0.95 and 0.02 < a5.posterior < 0.95
        unrounded5 = ctx4.base_rate * a5.lift_vector['promise_lift'] * a5.lift_vector['activation_lift'] \
            * a5.lift_vector['trigger_lift'] * _robustness_modifier(5)
        assert a5.posterior == pytest.approx(round(unrounded5, 4), abs=1e-4)
        assert a4.posterior == pytest.approx(a5.posterior * _robustness_modifier(4) / _robustness_modifier(5),
                                             abs=1.5e-4)
        assert a4.posterior < a5.posterior
        # and it is exactly what compute_posterior returns for the measured value
        expected, _ = compute_posterior(
            ctx4.base_rate, ctx4.pratijna_grade, ctx4.pratijna_status,
            ctx4.multi_system_confirmation_count, ctx4.av_transit_potency, ayanamsha_robustness=4,
        )
        assert a4.posterior == expected

    def test_signal_missing_under_one_built_ayanamsha_stores_4(self):
        sigs = _fixture_signals()
        sigs[FIVE[2]] = {('SIG_TYPE_FILLER', 'D1')}
        a, _ = _anchor_via_writer(_Conn(sigs, _all_conditional()))
        assert a.ayanamsha_robustness == 4

    def test_fewer_than_five_built_stores_none_and_skips_the_term(self):
        sigs = _fixture_signals()
        del sigs[FIVE[4]]
        a, _ = _anchor_via_writer(_Conn(sigs, _all_conditional()))
        assert a.ayanamsha_robustness is None
        assert a.lift_vector['ayanamsha_robustness_modifier'] is None
        assert a.lift_vector['ayanamsha_robustness_status'] == 'not_measured'

    def test_failed_query_leaves_none_not_a_number_and_rolls_back_its_savepoint(self):
        conn = _Conn(_fixture_signals(), _all_conditional(), fail_grouped_query=True)
        a, ctx = _anchor_via_writer(conn)
        assert ctx.ayanamsha_robustness is None
        assert a.ayanamsha_robustness is None
        assert a.lift_vector['ayanamsha_robustness_status'] == 'not_measured'
        assert 'ROLLBACK TO SAVEPOINT sp_nimitta_robustness' in conn.executed
        # the rest of the posterior inputs still loaded (the failure did not take the loader down)
        assert ctx.event_class_id == EVENT

    def test_a_malformed_grouped_row_leaves_none_not_a_crash_or_a_guess(self):
        class _BadRowsCursor(_Cursor):
            def execute(self, sql, params=None):
                super().execute(sql, params)
                if 'FROM bodha_msr_signals' in sql and 'GROUP BY' in sql:
                    self.pending = [{'ayanamsha_id': OWN}]      # no signal_type_id / varga_id

        class _BadRowsConn(_Conn):
            def cursor(self, *_a, **_k):
                return _BadRowsCursor(self)

        conn = _BadRowsConn(_fixture_signals(), _all_conditional())
        a, ctx = _anchor_via_writer(conn)
        assert ctx.ayanamsha_robustness is None and a.ayanamsha_robustness is None
        assert 'ROLLBACK TO SAVEPOINT sp_nimitta_robustness' in conn.executed

    def test_the_grouped_query_is_one_query_over_the_chart_with_the_real_columns(self):
        conn = _Conn(_fixture_signals(), _all_conditional())
        _anchor_via_writer(conn)
        grouped = [q for q in conn.executed if 'GROUP BY' in q]
        assert len(grouped) == 1
        q = grouped[0]
        for col in ('ayanamsha_id', 'signal_type_id', 'varga_id', 'chart_id'):
            assert col in q
        assert 'FROM bodha_msr_signals' in q

    def test_build_ctx_without_posterior_meta_supplies_none(self):
        from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
        ctx = PhNimittaWriter()._build_ctx({'signal_id': 'sig-1'}, {}, {}, {}, {})
        assert ctx.ayanamsha_robustness is None
        assert NimittaContext().ayanamsha_robustness is None


# ----------------------------------------------------------------- ast guard


class TestWriterPassesNoLiteral:
    def _keywords(self):
        tree = ast.parse(_WRITER.read_text(), feature_version=(3, 11))
        return [n for n in ast.walk(tree) if isinstance(n, ast.keyword) and n.arg == 'ayanamsha_robustness']

    def test_writer_passes_a_computed_value_never_a_literal(self):
        kws = self._keywords()
        assert kws, 'guard is vacuous: writer no longer passes ayanamsha_robustness at all'
        for kw in kws:
            assert not isinstance(kw.value, ast.Constant), (
                'ph_nimitta writer passes a literal (number, None, bool or str) as ayanamsha_robustness; '
                'it must pass the measured value from posterior meta (SS N-391)'
            )
            # the value is read from the measured posterior meta, not constructed in place
            assert isinstance(kw.value, ast.Call) and isinstance(kw.value.func, ast.Attribute) \
                and kw.value.func.attr == 'get' and ast.unparse(kw.value.func.value) == 'post'

    def test_writer_loads_through_the_pure_function(self):
        src = _WRITER.read_text()
        assert 'measure_ayanamsha_robustness(' in src
        assert 'sp_nimitta_robustness' in src
