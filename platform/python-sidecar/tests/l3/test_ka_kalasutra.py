"""Tests for ka_kalasutra bounded activation artifact builder."""
import re
import pytest
from datetime import date, timedelta
from pathlib import Path

# Import the helper functions directly (not the writer class which needs DB)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestrator.writers.ka_kalasutra import (
    _derive_dasha_periods,
    _derive_activation_dates,
    _derive_proximity_score,
    _compute_activation_start,
    _compute_activation_end,
)

WRITER_PATH = Path(__file__).parent.parent.parent / "pipeline/orchestrator/writers/ka_kalasutra.py"


class TestDeriveDashaPeriods:
    def test_derive_dasha_periods_with_lords(self):
        """rule has constituent_lords -> output list has graha entries"""
        rule = {'constituent_lords': ['Sun', 'Moon', 'Mars']}
        result = _derive_dasha_periods(rule)
        assert len(result) == 3
        assert all('graha' in entry for entry in result)
        assert result[0]['graha'] == 'Sun'
        assert result[0]['level'] == 'mahadasha'
        assert result[0]['source'] == 'dasha_eligibility_rule'

    def test_derive_dasha_periods_empty(self):
        """empty rule -> []"""
        assert _derive_dasha_periods({}) == []
        assert _derive_dasha_periods(None) == []

    def test_derive_dasha_periods_with_explicit_periods(self):
        """rule with explicit periods -> combined output"""
        rule = {
            'constituent_lords': ['Jupiter'],
            'periods': [{'graha': 'Venus', 'level': 'antardasha', 'source': 'explicit'}]
        }
        result = _derive_dasha_periods(rule)
        assert len(result) == 2
        assert result[0]['graha'] == 'Jupiter'
        assert result[1]['graha'] == 'Venus'


class TestDeriveActivationDates:
    def test_derive_activation_dates_with_peak(self):
        """peak_date given -> 7-element list (+-3 days)"""
        peak = date(2026, 6, 15)
        transit_rule = {'type': 'transit_conjunction'}
        result = _derive_activation_dates(transit_rule, peak)
        assert len(result) == 7

    def test_derive_activation_dates_no_peak(self):
        """peak=None -> []"""
        result = _derive_activation_dates({'type': 'transit'}, None)
        assert result == []

    def test_derive_activation_dates_strength_decay(self):
        """strength 1.0 at peak, decreasing outward"""
        peak = date(2026, 6, 15)
        transit_rule = {'type': 'transit'}
        result = _derive_activation_dates(transit_rule, peak)
        # Sort by date to find peak (middle element)
        strengths = [entry['strength'] for entry in result]
        # Peak should be index 3 (delta=0)
        assert strengths[3] == 1.0
        # Outward entries should have lower strength
        assert strengths[2] < strengths[3]
        assert strengths[4] < strengths[3]
        assert strengths[0] < strengths[1]

    def test_activation_dates_are_sorted(self):
        """dates in output are in ascending order"""
        peak = date(2026, 6, 15)
        result = _derive_activation_dates({'type': 'transit'}, peak)
        dates = [entry['date'] for entry in result]
        assert dates == sorted(dates)

    def test_derive_activation_dates_no_transit_rule(self):
        """No transit rule -> []"""
        result = _derive_activation_dates(None, date(2026, 6, 15))
        assert result == []


class TestDeriveProximityScore:
    def test_proximity_score_range(self):
        """result always in [0,1]"""
        for dignity in [0.0, 0.5, 1.0, 1.5]:
            for non_aff in [0.0, 0.5, 1.0]:
                score = _derive_proximity_score({'dignity_score': dignity}, {'non_affliction': non_aff}, date(2026, 1, 1))
                assert 0.0 <= score <= 1.0

    def test_proximity_score_high_dignity(self):
        """dignity=1.0, non_affliction=1.0 -> score ~1.0"""
        score = _derive_proximity_score(
            {'dignity_score': 1.0},
            {'non_affliction': 1.0},
            date(2026, 6, 15)
        )
        assert abs(score - 1.0) < 0.001

    def test_proximity_score_no_peak(self):
        """peak=None -> 0.5"""
        score = _derive_proximity_score({}, {}, None)
        assert score == 0.5


class TestComputeActivationWindow:
    def test_compute_activation_window_yoga(self):
        """YOGA -> 7-day window each side"""
        peak = date(2026, 6, 15)
        start = _compute_activation_start(peak, 'YOGA')
        end = _compute_activation_end(peak, 'YOGA')
        assert start == peak - timedelta(days=7)
        assert end == peak + timedelta(days=7)

    def test_compute_activation_window_dosha(self):
        """DOSHA -> 14-day window"""
        peak = date(2026, 6, 15)
        start = _compute_activation_start(peak, 'DOSHA')
        end = _compute_activation_end(peak, 'DOSHA')
        assert start == peak - timedelta(days=14)
        assert end == peak + timedelta(days=14)

    def test_compute_activation_window_no_peak(self):
        """no peak -> None/None"""
        assert _compute_activation_start(None, 'YOGA') is None
        assert _compute_activation_end(None, 'YOGA') is None

    def test_compute_start_before_end(self):
        """start < end for any non-None peak"""
        peak = date(2026, 6, 15)
        for sig_class in ['YOGA', 'DOSHA', 'DIGNITY', 'SENSITIVE_POINT', 'SUBSYSTEM']:
            start = _compute_activation_start(peak, sig_class)
            end = _compute_activation_end(peak, sig_class)
            assert start < end

    def test_signature_class_window_default(self):
        """unknown sig_class -> 5-day default window"""
        peak = date(2026, 6, 15)
        start = _compute_activation_start(peak, 'UNKNOWN_CLASS')
        end = _compute_activation_end(peak, 'UNKNOWN_CLASS')
        assert start == peak - timedelta(days=5)
        assert end == peak + timedelta(days=5)


class TestWriterContractGrep:
    def test_writer_contract_no_commit(self):
        """grep writers/ka_kalasutra.py for .commit() -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'\.commit\(\)', source)
        assert len(matches) == 0, f"Found .commit() calls: {matches}"

    def test_writer_contract_no_rollback(self):
        """grep for .rollback() -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'\.rollback\(\)', source)
        assert len(matches) == 0, f"Found .rollback() calls: {matches}"

    def test_writer_contract_no_l2_writes(self):
        """grep for INSERT INTO bodha_ -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'INSERT INTO bodha_|UPDATE bodha_', source)
        assert len(matches) == 0, f"Found L2 write attempts: {matches}"

    def test_writer_contract_no_kala_timeline_writes(self):
        """grep for INSERT INTO kala_timeline -> 0 matches"""
        source = WRITER_PATH.read_text()
        matches = re.findall(r'INSERT INTO kala_timeline', source)
        assert len(matches) == 0, f"Found kala_timeline write attempts: {matches}"

    def test_source_citation_format(self):
        """source_citation starts with 'ka_kalasutra:v1.0:'"""
        source = WRITER_PATH.read_text()
        # Find the source_citation format string in the writer
        assert 'ka_kalasutra:v1.0:' in source

    def test_l2_hooks_are_l3_only(self):
        """assert that L2 table (bodha_msr_signals) is NEVER written"""
        source = WRITER_PATH.read_text()
        l2_writes = re.findall(r'(INSERT INTO|UPDATE)\s+bodha_msr_signals', source)
        assert len(l2_writes) == 0, f"Found writes to bodha_msr_signals: {l2_writes}"


# ── WP-2.1 / R-45: writer-level date-population regression (DB-free) ───────────
from datetime import date as _d


class _KalaCursor:
    """Script-matched fake cursor. Captures executemany rows for assertions."""
    def __init__(self, script, sink):
        self._script = script
        self._sink = sink
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        for matcher, rows in self._script:
            if matcher in s:
                self._result = list(rows)
                return
        self._result = []

    def executemany(self, sql, rows):
        if "INSERT INTO kala_activation" in " ".join(sql.split()):
            self._sink.extend(rows)

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None


class _KalaConn:
    def __init__(self, script, sink):
        self._script = script
        self._sink = sink

    def cursor(self, *a, **k):
        return _KalaCursor(self._script, self._sink)


class _Ctx:
    def __init__(self, conn, chart_id):
        self.db_conn = conn
        self.config = {"chart_id": chart_id}


def test_writer_populates_real_dates_from_dasha_timeline_without_convergence():
    """R-45 LANE0 regression: a predicate whose lord is in the dasha timeline
    gets NON-NULL activation_start/end/peak even with NO convergence peak.

    WP-S4-fix2 (Gate Ś #8/#9): the writer calls resolve_activation_windows with
    NO explicit as_of_date, so it defaults to date.today() — the fixture below
    uses dates RELATIVE to date.today() (not hardcoded 2010-2029) so this test
    deterministically exercises the "current tier" selection regardless of the
    real wall-clock date the suite runs on, and so it would have caught the
    fix-2 defect (the writer dating everything to the earliest-ever period —
    e.g. a 2010-2029 MD — instead of the AD actually straddling "now").
    """
    from pipeline.orchestrator.writers.ka_kalasutra import KaKalasutraWriter

    today = date.today()
    ad_start = today - timedelta(days=365 * 2)      # AD straddles "now"
    ad_end = today + timedelta(days=365 * 2)
    md_start = today - timedelta(days=365 * 12)     # wider co-current MD (coarser level)
    md_end = today + timedelta(days=365 * 12)

    chart_id = "482012f1-710e-4a25-994a-93821f5871aa"
    sink = []
    script = [
        ("FROM charts", [{"birth_date": _d(1984, 2, 5)}]),  # §8.4: life-index anchor
        ("FROM kala_activation_predicates", [{
            "signal_id": "11111111-1111-1111-1111-111111111111",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "signature_class": "YOGA",
            "dasha_eligibility_rule_jsonb": {"constituent_lords": ["Saturn"], "dignity_score": 0.7},
            "transit_trigger_jsonb": {"type": "benefic_transit"},
            "strength_affliction_hook_jsonb": {"non_affliction": 1.0},
        }]),
        ("FROM chart_dashas", [
            # §8.4 regression: a PRE-BIRTH Saturn AD (1951) precedes the in-life one.
            # The global-earliest selector would have picked this — the fix must not.
            {"lord_graha": "Saturn", "level_n": 2, "start_date": _d(1951, 4, 14), "end_date": _d(1952, 5, 23)},
            # WP-S4-fix2 regression: a co-current, COARSER (MD) period that spans an even
            # wider range than the AD — the pre-fix2 "earliest matched[0]" selector would
            # have picked whichever of these two sorted first by start date (in practice
            # whichever period started first chronologically), NOT the one relevant to
            # "now". The fix must select the AD (finer level, also current) over this MD.
            {"lord_graha": "Saturn", "level_n": 1, "start_date": md_start.isoformat(), "end_date": md_end.isoformat()},
            {"lord_graha": "Saturn", "level_n": 2, "start_date": ad_start.isoformat(), "end_date": ad_end.isoformat()},
        ]),
        ("FROM kala_convergence", []),  # NO convergence peak — the 99% case
    ]
    conn = _KalaConn(script, sink)
    result = KaKalasutraWriter().run(_Ctx(conn, chart_id))

    # CR-109 fix (D-4a Lane A-0): the predicate matches 2 in-life periods (the
    # current Saturn AD + the wider co-current Saturn MD) — the writer now emits
    # one row PER matched period instead of collapsing to a single row. The AD
    # (finer level, sorted first — same primary-selection order as before) is
    # still sink[0], so every existing content assertion below is unchanged.
    assert result.rows_inserted == 2
    row = sink[0]
    # tuple layout: (..., proximity, activation_start, activation_end, peak, ...)
    activation_start, activation_end, activation_peak = row[7], row[8], row[9]
    assert activation_start is not None, "activation_start must NOT be NULL (R-45 fix)"
    assert activation_end is not None
    assert activation_peak is not None
    # WP-S4-fix2: the resolved window is the CURRENT (straddles "today") Saturn AD,
    # finer level preferred within the current tier — NOT the pre-birth 1951 AD, and
    # NOT simply whichever in-life period happened to start earliest chronologically.
    assert activation_start == ad_start.isoformat()
    assert activation_end == ad_end.isoformat()
    assert activation_start >= "1984-02-05"
    assert activation_peak >= "1984-02-05"
    # every predicted date is in-life; no pre-birth leak
    import json as _json
    predicted = _json.loads(row[5])
    assert len(predicted) > 0
    assert all(p["date"] >= "1984-02-05" for p in predicted)
    # active_dasha_periods carry no pre-birth window
    periods = _json.loads(row[4])
    dated = [p for p in periods if p.get("match_kind") == "exact_lord"]
    assert all(p["start"] >= "1984-02-05" for p in dated)
    # citation records the resolution source
    assert "src=dasha_timeline" in row[12]


def test_writer_uses_convergence_peak_when_present():
    """When a convergence peak exists it refines the window (legacy path)."""
    from pipeline.orchestrator.writers.ka_kalasutra import KaKalasutraWriter

    chart_id = "482012f1-710e-4a25-994a-93821f5871aa"
    sink = []
    script = [
        ("FROM charts", [{"birth_date": _d(1984, 2, 5)}]),
        ("FROM kala_activation_predicates", [{
            "signal_id": "22222222-2222-2222-2222-222222222222",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "signature_class": "YOGA",
            "dasha_eligibility_rule_jsonb": {"constituent_lords": ["Saturn"]},
            "transit_trigger_jsonb": {"type": "benefic_transit"},
            "strength_affliction_hook_jsonb": {},
        }]),
        ("FROM chart_dashas", [
            {"lord_graha": "Saturn", "level_n": 1, "start_date": _d(2010, 1, 1), "end_date": _d(2029, 1, 1)},
        ]),
        ("FROM kala_convergence", [{
            "signal_id": "22222222-2222-2222-2222-222222222222",
            "mode": "A", "peak_date": _d(2013, 6, 15),
            "orb_strength": 0.8, "convergence_score": 0.9,
        }]),
    ]
    conn = _KalaConn(script, sink)
    result = KaKalasutraWriter().run(_Ctx(conn, chart_id))
    assert result.rows_inserted == 1
    row = sink[0]
    assert row[7] == "2013-06-08"   # peak - 7 (YOGA)
    assert row[9] == "2013-06-15"   # peak
    assert "src=convergence" in row[12]
