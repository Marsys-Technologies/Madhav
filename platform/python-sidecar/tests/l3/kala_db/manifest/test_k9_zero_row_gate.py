"""SR-K9-ADMITTED-ZERO / SR-SANGAM-FLOOR-ZERO: the K9 publish gate (services/kala_core/publication.py `_candidate`, applied by `publish` only) is the
compensating detector for ka_sangam and ka_vighnakara declaring target_floor = 0 (migration 1409). Outside the FROZEN asset_runner path (CLAUDE.md §N.8).

A zero-row grain of these two writers publishes only when (1) the emptiness is explained by a named reason the gate MEASURES from the candidate's own rows and
(2) the asset's registered integrity_check_sql passes now. Claims:
G1 an UNEXPLAINED zero-row completion refuses (the upstream holds windows / the signal-bearing input exists, yet the writer wrote none). For ka_sangam only
   SR-SANGAM-SIGNAL-UNRESOLVED's two honest nulls (nothing admitted; every admitted predicate signal-less) are vacuous: admitted SIGNAL-BEARING in-force
   predicates that wrote 0 windows are the silent failure floor 0 stopped the orchestrator detecting, so they refuse;
G2 an explained (vacuous, named reason) zero-row completion with a passing integrity check passes;
G3 an explained zero-row completion whose integrity check does not pass (or is absent) refuses;
G4 a non-empty (`rows`) grain, and a zero-row grain of any OTHER writer, are unaffected;
G5 `publish` (through `_candidate`) applies the detector: an unexplained zero-row candidate raises CandidateNotPublishable, a labelled one is returned;
G6 `verify` does NOT: it runs as the narrow verifier_principal (migration 1330 grants it the grain and verification tables only), so it must read no layer table or registry.
"""
import pytest

from services.kala_core import publication as pub


class _Result:
    def __init__(self, row, rows=None):
        self._row, self._rows = row, rows

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Conn:
    """Scripted read-only connection: answers by SQL fragment; every statement is recorded."""

    def __init__(self, *, convergence=0, peak=0, admitted=0, unresolved=0, integrity='SELECT true', verdict=(True,), grains=()):
        self.convergence, self.peak, self.admitted, self.unresolved = convergence, peak, admitted, unresolved
        self.grains = list(grains)
        self.integrity, self.verdict = integrity, verdict
        self.sql = []
        self.savepoints = 0

    def transaction(self):
        conn = self

        class _Savepoint:
            def __enter__(self):
                conn.savepoints += 1

            def __exit__(self, *exc):
                return False
        return _Savepoint()

    def execute(self, sql, params=()):
        self.sql.append(sql)
        if 'FROM kala_layer_candidate_grain' in sql:
            return _Result(None, self.grains)
        if 'FROM kala_layer_candidate WHERE build_id' in sql:
            writers = sorted({g[0].split(':')[0] for g in self.grains})
            return _Result(('chart', 'build', None, 'building', {'publication_grains': {w: [f'{w}:inputs'] for w in writers}}))
        if 'FROM kala_convergence' in sql:
            return _Result((self.peak if 'peak_date IS NOT NULL' in sql else self.convergence,))
        if 'FROM kala_activation_predicates' in sql:
            return _Result((self.admitted, self.unresolved))
        if 'integrity_check_sql FROM asset_registry' in sql:
            return _Result(None if self.integrity is None else (self.integrity,))
        return _Result(self.verdict)                     # the integrity statement itself


def check(conn, *grains):
    return pub._unexplained_zero_rows(conn, 'chart', 'candidate:g', list(grains))


# ── G1 ──────────────────────────────────────────────────────────────────────

def test_g1_vighnakara_zero_rows_with_a_non_empty_upstream_refuses():
    problems = check(_Conn(peak=7, convergence=7), 'ka_vighnakara:inputs')
    assert len(problems) == 1 and 'ka_vighnakara:inputs' in problems[0] and 'not vacuous' in problems[0]


def test_g1_sangam_zero_windows_that_exist_in_the_candidate_refuses():
    problems = check(_Conn(convergence=3, admitted=5), 'ka_sangam:inputs')        # the grain says zero_rows, the table says otherwise
    assert len(problems) == 1 and 'not vacuous' in problems[0]


@pytest.mark.parametrize('admitted,unresolved', [(4, 1), (4, 0)], ids=['mixed', 'all_signal_bearing'])
def test_g1_sangam_admitted_signal_bearing_predicates_that_wrote_no_window_refuse(admitted, unresolved):
    """The silent failure floor 0 hides: in-force admitted predicates carry a signal, yet 0 windows. Not one of SR-SANGAM-SIGNAL-UNRESOLVED's honest nulls."""
    conn = _Conn(admitted=admitted, unresolved=unresolved)
    problems = check(conn, 'ka_sangam:inputs')
    assert len(problems) == 1 and 'ka_sangam:inputs' in problems[0] and 'not vacuous' in problems[0]
    assert not any('asset_registry' in sql for sql in conn.sql), 'a refused grain never reaches the integrity check'


# ── G2 ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('conn,writer', [
    (_Conn(peak=0), 'ka_vighnakara'),                                              # empty upstream
    (_Conn(admitted=0), 'ka_sangam'),                                              # no admitted predicate (the K4-2b unadmitted state)
    (_Conn(admitted=4, unresolved=4), 'ka_sangam'),                                # every admitted predicate signal-less
], ids=['vighnakara_empty_upstream', 'sangam_no_admitted', 'sangam_all_signal_unresolved'])
def test_g2_a_vacuous_zero_row_completion_with_a_passing_integrity_check_passes(conn, writer):
    assert check(conn, f'{writer}:inputs') == []
    assert any(sql == 'SELECT true' for sql in conn.sql), 'the integrity statement must actually have run'


def test_g2_each_vacuous_state_has_its_own_named_reason():
    named = lambda c, w: pub._vacuous_reason(c, w, 'chart', 'candidate:g')
    assert named(_Conn(peak=0), 'ka_vighnakara') == 'empty_upstream_convergence'
    assert named(_Conn(admitted=0), 'ka_sangam') == 'no_admitted_predicates'
    assert named(_Conn(admitted=3, unresolved=3), 'ka_sangam') == 'all_admitted_signal_unresolved'
    assert named(_Conn(admitted=3, unresolved=2), 'ka_sangam') is None               # signal-bearing predicates, no window: not vacuous


# ── G3 ──────────────────────────────────────────────────────────────────────

def test_g3_vacuous_but_integrity_false_refuses():
    problems = check(_Conn(peak=0, verdict=(False,)), 'ka_vighnakara:inputs')
    assert len(problems) == 1 and 'integrity_check_sql did not pass' in problems[0]


def test_g3_vacuous_but_integrity_returns_no_row_refuses():
    assert 'did not pass' in check(_Conn(admitted=0, verdict=None), 'ka_sangam:inputs')[0]


def test_g3_vacuous_but_no_registered_integrity_sql_refuses():
    assert 'no integrity_check_sql' in check(_Conn(admitted=0, integrity=None), 'ka_sangam:inputs')[0]


def test_g3_integrity_sql_runs_inside_a_savepoint():
    conn = _Conn(admitted=0)
    assert check(conn, 'ka_sangam:inputs') == [] and conn.savepoints == 1


# ── G4 ──────────────────────────────────────────────────────────────────────

def test_g4_no_zero_row_grain_means_nothing_is_measured():
    conn = _Conn(peak=9)
    assert check(conn) == [] and conn.sql == []


def test_g4_another_writers_zero_row_grain_is_unaffected():
    conn = _Conn(peak=9, convergence=9)
    assert check(conn, 'ka_gochara:inputs', 'ka_yojaka') == [] and conn.sql == []


# ── G5 ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def entry(monkeypatch):
    monkeypatch.setattr(pub, 'lock_candidate_inputs', lambda conn, c: None)
    monkeypatch.setattr(pub, '_run', lambda conn, run_id: {'chart_id': 'chart', 'state': 'completed', 'plan': ['ka_vighnakara']})
    return lambda conn: pub._candidate(conn, 'build', 'candidate:g', enforce_zero_rows=True)


def test_g5_candidate_refuses_an_unexplained_zero_row_grain(entry):
    conn = _Conn(peak=4, convergence=4, grains=[('ka_vighnakara:inputs', 'zero_rows')])
    with pytest.raises(pub.CandidateNotPublishable, match='zero-row completion without a measured vacuous reason'):
        entry(conn)


def test_g5_candidate_returns_a_labelled_vacuous_zero_row_grain_and_a_non_empty_one(entry):
    c, detail = entry(_Conn(peak=0, grains=[('ka_vighnakara:inputs', 'zero_rows')]))
    assert detail['grains'] == ('ka_vighnakara:inputs',)
    conn = _Conn(peak=4, convergence=4, grains=[('ka_vighnakara:inputs', 'rows')])            # non-empty: the detector measures nothing
    assert entry(conn)[1]['grains'] == ('ka_vighnakara:inputs',)
    assert not any('FROM kala_convergence' in sql for sql in conn.sql)


# ── G6 ──────────────────────────────────────────────────────────────────────

def test_g6_verify_reads_no_layer_table_or_registry(entry):
    conn = _Conn(peak=4, convergence=4, grains=[('ka_vighnakara:inputs', 'zero_rows')])           # unexplained, but verify only binds a digest
    pub._candidate(conn, 'build', 'candidate:g')                                                     # the verify path: no enforce_zero_rows
    assert not any(t in sql for sql in conn.sql for t in ('FROM kala_convergence', 'kala_activation_predicates', 'asset_registry'))
