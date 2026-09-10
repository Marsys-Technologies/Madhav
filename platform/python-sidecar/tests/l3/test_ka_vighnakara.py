"""Tests for ka_vighnakara writer — obstruction/counter-indicator detector."""
import subprocess
from datetime import date
import pytest
import sys
from pathlib import Path

# Add the sidecar root so pipeline.orchestrator.writers is importable
_SIDECAR = str(Path(__file__).parent.parent.parent)
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from pipeline.orchestrator.writers.ka_vighnakara import (
    _severity,
    _detect_obstructions,
    _check_malefic_transit,
    _check_panchanga_obstruction,
    _check_gandanta,
    _check_papakartari,
    SEVERITY_MAP,
    MALEFICS,
)

VALID_OBSTRUCTION_TYPES = {
    'malefic_transit',
    'dasha_lord_afflicted',
    'panchanga_obstruction',
    'rashi_dristi_conflict',
    'combustion',
    'gandanta',
    'papakartari',
}

WRITER_PATH = Path(__file__).parent.parent.parent / "pipeline/orchestrator/writers/ka_vighnakara.py"

# F-VIGHNA-6 (CR-87 contamination pattern): this constant used to live as a module-level
# global inside the WRITER (ka_vighnakara.py), hardcoded to this one native's own Saturn
# transits, even though it is genuinely unreachable in production (run() hard-raises
# before ever calling _check_malefic_transit without a real swe module). Moved here —
# the test module is exactly where test-only fixture data belongs — and injected
# explicitly via _check_malefic_transit's `_test_proxy_windows` parameter below.
_SATURN_PROXY_WINDOWS = [
    (date(2025, 3, 1),  date(2027, 6, 30)),   # Saturn in Pisces (sade-sati close)
    (date(2030, 4, 1),  date(2032, 6, 30)),   # Saturn in Gemini (3rd — upachaya/adversarial by proximity)
]


# --- severity() tests ---

def test_severity_mild():
    assert _severity(0.0) == 'mild'
    assert _severity(0.1) == 'mild'
    assert _severity(0.39) == 'mild'


def test_severity_moderate():
    assert _severity(0.4) == 'moderate'
    assert _severity(0.5) == 'moderate'
    assert _severity(0.69) == 'moderate'


def test_severity_severe():
    assert _severity(0.7) == 'severe'
    assert _severity(0.85) == 'severe'
    assert _severity(1.0) == 'severe'


# --- malefic transit tests ---

def test_malefic_transit_saturn_aq_in_window():
    # Window updated to Saturn/Gemini approx 2030-04-01..2032-06-30 (wave4 update)
    result = _check_malefic_transit(date(2031, 6, 15), _test_proxy_windows=_SATURN_PROXY_WINDOWS)
    assert result is not None
    assert result['obstruction_type'] == 'malefic_transit'


def test_malefic_transit_saturn_aq_outside_window_before():
    result = _check_malefic_transit(date(2028, 1, 1), _test_proxy_windows=_SATURN_PROXY_WINDOWS)
    assert result is None


def test_malefic_transit_saturn_aq_end_boundary():
    # 2032-07-01 is AFTER the window (end is 2032-06-30)
    result = _check_malefic_transit(date(2032, 7, 1), _test_proxy_windows=_SATURN_PROXY_WINDOWS)
    assert result is None


def test_malefic_transit_saturn_aq_start_boundary():
    # 2030-04-01 is the START of the window (inclusive)
    result = _check_malefic_transit(date(2030, 4, 1), _test_proxy_windows=_SATURN_PROXY_WINDOWS)
    assert result is not None
    assert result['obstruction_type'] == 'malefic_transit'


def test_malefic_transit_saturn_aq_end_inclusive():
    # 2032-06-30 is still IN the window (inclusive end)
    result = _check_malefic_transit(date(2032, 6, 30), _test_proxy_windows=_SATURN_PROXY_WINDOWS)
    assert result is not None
    assert result['obstruction_type'] == 'malefic_transit'


def test_malefic_transit_accepts_string_date():
    result = _check_malefic_transit('2031-06-15', _test_proxy_windows=_SATURN_PROXY_WINDOWS)
    assert result is not None
    assert result['obstruction_type'] == 'malefic_transit'


def test_malefic_transit_no_proxy_windows_returns_none_without_swe():
    """F-VIGHNA-6: without swe AND without test-injected proxy windows (the genuine
    production shape — this parameter is never populated outside tests), the function
    must return None rather than raising or fabricating a result."""
    result = _check_malefic_transit(date(2031, 6, 15))
    assert result is None


# --- panchanga obstruction tests ---

def test_panchanga_rikta_tithi_day4():
    # day=4, day_mod = 4 % 15 = 4 → hit
    result = _check_panchanga_obstruction(date(2024, 6, 4))
    assert result is not None
    assert result['obstruction_type'] == 'panchanga_obstruction'


def test_panchanga_rikta_tithi_day9():
    result = _check_panchanga_obstruction(date(2024, 6, 9))
    assert result is not None
    assert result['obstruction_type'] == 'panchanga_obstruction'


def test_panchanga_rikta_tithi_day14():
    result = _check_panchanga_obstruction(date(2024, 6, 14))
    assert result is not None
    assert result['obstruction_type'] == 'panchanga_obstruction'


def test_panchanga_rikta_tithi_day15():
    # day=15, day_mod = 15 % 15 = 0 → hit (catches day=15)
    result = _check_panchanga_obstruction(date(2024, 6, 15))
    assert result is not None
    assert result['obstruction_type'] == 'panchanga_obstruction'


def test_panchanga_clear_day():
    # day=1, day_mod = 1 % 15 = 1 → no hit
    result = _check_panchanga_obstruction(date(2024, 6, 1))
    assert result is None


def test_panchanga_clear_day_7():
    # day=7, day_mod = 7 → no hit
    result = _check_panchanga_obstruction(date(2024, 6, 7))
    assert result is None


def test_panchanga_accepts_string_date():
    result = _check_panchanga_obstruction('2024-06-04')
    assert result is not None
    assert result['obstruction_type'] == 'panchanga_obstruction'


# --- detect_obstructions() tests ---

def test_detect_obstructions_none_if_no_peak():
    result = _detect_obstructions(peak_date=None, convergence_score=0.8, signal_id=None)
    assert result == []


def test_detect_obstructions_returns_list():
    result = _detect_obstructions(peak_date=date(2024, 6, 15), convergence_score=0.8, signal_id=None)
    assert isinstance(result, list)


def test_detect_obstructions_never_raises():
    # Test multiple dates to ensure no exceptions
    test_dates = [
        date(2020, 1, 1),
        date(2023, 6, 15),
        date(2025, 12, 31),
        date(2026, 3, 9),
    ]
    for d in test_dates:
        result = _detect_obstructions(peak_date=d, convergence_score=0.5, signal_id=None)
        assert isinstance(result, list)


def test_obstruction_override_score_range():
    result = _detect_obstructions(peak_date=date(2024, 6, 4), convergence_score=0.7, signal_id=None)
    for obs in result:
        assert 0.0 <= obs['override_score'] <= 1.0, f"override_score out of range: {obs['override_score']}"


def test_obstruction_severity_score_range():
    result = _detect_obstructions(peak_date=date(2024, 6, 4), convergence_score=0.7, signal_id=None)
    for obs in result:
        assert 0.0 <= obs['severity_score'] <= 1.0, f"severity_score out of range: {obs['severity_score']}"


def test_obstruction_type_valid_enum():
    result = _detect_obstructions(peak_date=date(2024, 6, 4), convergence_score=0.7, signal_id=None)
    for obs in result:
        assert obs['obstruction_type'] in VALID_OBSTRUCTION_TYPES, \
            f"Invalid obstruction_type: {obs['obstruction_type']}"


def test_detail_has_reason_key():
    result = _detect_obstructions(peak_date=date(2024, 6, 4), convergence_score=0.7, signal_id=None)
    for obs in result:
        assert 'reason' in obs['detail'], f"Missing 'reason' key in detail: {obs['detail']}"


# --- writer contract tests ---

def test_writer_contract_no_commit():
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    assert '.commit()' not in content, "Found .commit() in writer — violates frozen orchestrator contract"


def test_writer_contract_no_rollback():
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    assert '.rollback()' not in content, "Found .rollback() in writer — violates frozen orchestrator contract"


def test_writer_contract_no_l2_writes():
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    import re
    # Check for writes to bodha_ or ganita_ tables
    forbidden = re.findall(r'INSERT INTO (bodha_|ganita_)\w+|UPDATE (bodha_|ganita_)\w+', content)
    assert not forbidden, f"Found forbidden L2/L1 writes: {forbidden}"


def test_writer_contract_no_hardcoded_native_transit_data():
    """F-VIGHNA-6 (CR-87 contamination pattern): no native-specific hardcoded transit
    window data may live in the writer module — that data belongs in the test module
    that actually needs it (this file's own _SATURN_PROXY_WINDOWS)."""
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    assert '_SATURN_PROXY_WINDOWS' not in content, (
        "the proxy-window constant must live in the test module, not the writer"
    )


# --- SEVERITY_MAP ordering test ---

def test_severity_map_ordering():
    thresholds = [threshold for threshold, _ in SEVERITY_MAP]
    assert thresholds == sorted(thresholds, reverse=True), \
        f"SEVERITY_MAP thresholds should be in descending order: {thresholds}"


# --- Valid obstruction type coverage ---

def test_obstruction_type_set_complete():
    """All 7 valid CHECK constraint types are declared in code."""
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    for otype in VALID_OBSTRUCTION_TYPES:
        assert otype in content, f"obstruction_type '{otype}' not referenced in writer"


# --- gandanta and papakartari return explicit stub dicts (v1.1 — silent None replaced) ---

def test_gandanta_returns_stub_dict():
    result = _check_gandanta(date(2024, 6, 15))
    assert result is not None, "_check_gandanta must return stub dict, not None"
    assert result['obstruction_type'] == 'gandanta'
    assert result['detail']['stub'] is True


def test_papakartari_returns_stub_dict():
    result = _check_papakartari(date(2024, 6, 15))
    assert result is not None, "_check_papakartari must return stub dict, not None"
    assert result['obstruction_type'] == 'papakartari'
    assert result['detail']['stub'] is True


# --- MALEFICS set test ---

def test_malefics_set_contains_classical():
    assert 'Saturn' in MALEFICS
    assert 'Mars' in MALEFICS
    assert 'Rahu' in MALEFICS
    assert 'Ketu' in MALEFICS


# ── WP-2.1 / F-L10-018: dasha-anchored obstruction reachability ───────────────
from datetime import date as _vd


class _VCursor:
    def __init__(self, script, calls):
        self._script = script
        self._calls = calls
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._calls.append(s)
        for matcher, rows in self._script:
            if matcher in s:
                self._result = list(rows)
                return
        self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None


class _VConn:
    def __init__(self, script):
        self._script = script
        self.calls = []

    def cursor(self, *a, **k):
        return _VCursor(self._script, self.calls)


def test_dasha_anchor_peaks_dedupes_and_skips_covered():
    """Uncovered predicates resolve to distinct dasha-derived anchor peaks;
    covered signals are skipped; each peak claimed by one representative signal."""
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter

    chart_id = "482012f1-710e-4a25-994a-93821f5871aa"
    script = [
        ("FROM chart_dashas", [
            {"lord_graha": "Saturn", "level_n": 1, "start_date": _vd(2010, 1, 1), "end_date": _vd(2029, 1, 1)},
            {"lord_graha": "Venus", "level_n": 1, "start_date": _vd(2029, 1, 1), "end_date": _vd(2049, 1, 1)},
        ]),
        ("FROM kala_activation_predicates", [
            {"signal_id": "aaaaaaaa-0000-0000-0000-000000000001", "ayanamsha_id": "lahiri_chitrapaksha",
             "dasha_eligibility_rule_jsonb": {"constituent_lords": ["Saturn"]}},
            {"signal_id": "aaaaaaaa-0000-0000-0000-000000000002", "ayanamsha_id": "lahiri_chitrapaksha",
             "dasha_eligibility_rule_jsonb": {"constituent_lords": ["Venus"]}},
            {"signal_id": "covered-0000-0000-0000-000000000003", "ayanamsha_id": "lahiri_chitrapaksha",
             "dasha_eligibility_rule_jsonb": {"constituent_lords": ["Saturn"]}},
        ]),
    ]
    conn = _VConn(script)
    covered = {"covered-0000-0000-0000-000000000003"}
    anchors = KaVighnakaraWriter()._dasha_anchor_peaks(conn, chart_id, covered)

    # Two distinct lords -> two distinct MD-midpoint anchors; covered one skipped.
    peaks = [p for p, _ in anchors]
    assert len(anchors) == 2
    assert len(set(peaks)) == 2
    assert all(isinstance(p, _vd) for p in peaks)
    sig_ids = {s for _, s in anchors}
    assert "covered-0000-0000-0000-000000000003" not in sig_ids


def test_dasha_anchor_peaks_empty_timeline():
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter
    conn = _VConn([("FROM chart_dashas", [])])
    assert KaVighnakaraWriter()._dasha_anchor_peaks(conn, "cid", set()) == []


def test_dasha_anchor_peaks_predicate_query_has_total_order_by_signal_id():
    """F-VIGHNA-3 (§N.7 item 2): the predicate fetch must carry a total ORDER BY over a
    stable key. Without it, which signal represents a given peak date (setdefault's
    "first one wins") and which peaks survive the _MAX_DASHA_ANCHORS cap are both
    undefined by Postgres row-order guarantees — a build-to-build nondeterminism the
    fake in-memory cursor below cannot itself exercise (it doesn't actually sort), so
    this test pins the query TEXT rather than simulating Postgres's row order."""
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter

    conn = _VConn([("FROM kala_activation_predicates", [])])
    KaVighnakaraWriter()._dasha_anchor_peaks(conn, "482012f1-710e-4a25-994a-93821f5871aa", set())

    predicate_calls = [c for c in conn.calls if "FROM kala_activation_predicates" in c]
    assert len(predicate_calls) == 1
    sql = predicate_calls[0]
    assert "ORDER BY signal_id" in sql
    # The ORDER BY must scope the whole predicate set for this chart, not just a
    # tie-break clause bolted onto some other ordering — assert it is the ONLY
    # ORDER BY clause on this query (a total order, not a partial one).
    assert sql.count("ORDER BY") == 1
