"""ga_condition reports every row its partition writes (TI-l1-writer-fixes-001, finding F4).

Data-plane rehearsal: ``ga_condition`` failed partition completion with "reported 9 rows but
protected capture contains 594".  A substep writes the 9 ``ga_condition_composite`` rows AND the
per-varga + D1 avastha ``chart_facts`` rows (two ``_insert_per_varga_avastha_rows`` calls), all
inside one L1 partition, but only the composite insert was added to ``rows_inserted``.

These tests drive the REAL registered writer (``GaConditionWriter.run_substep`` behind the real
``l1_producer_contract`` runtime boundary) on a SYNTHETIC chart.  The connection is a recording
double that models the protected capture the way ``complete_l1_data_plane_partition`` counts it
(composite rows + distinct ``chart_facts`` identities written in the partition) and rejects a
mismatch with the SAME message.  The real SQL function was exercised against a disposable
Postgres in the PR evidence (reported == captured, 54 rows on a chart with no varga upstream);
this double keeps the contract in the unit suite.
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ContextSpec, discover_all, list_writers
from pyjhora_adapter.compute import compute_chart

CHART = "aaaaaaaa-1111-4222-8333-000000000001"  # synthetic: not a real chart id
BUILD = "bbbbbbbb-1111-4222-8333-000000000001"
SYNTHETIC_BP = {
    "datetime_iso": "1991-07-19T06:20:00",
    "latitude_deg": 18.52,
    "longitude_deg": 73.86,
    "tz_offset_hours": 5.5,
    "place_name": "synthetic",
    "subject_label": "syn",
}
_SUBJECT = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER", "Jupiter": "JUP",
    "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
}
VARGAS = ("D1", "D9", "D10")


class _Result:
    def __init__(self, rows=(), rowcount=0):
        self._rows = list(rows)
        self.rowcount = rowcount

    def fetchall(self):
        return self._rows


class _CaptureConn:
    """Recording double: serves the writer's reads from the real adapter and models the capture."""

    _l1_contract_test_double = True

    def __init__(self, chart_output, *, drop_avastha_count=False):
        self.chart = chart_output
        self.composite = 0
        self.facts: dict[str, str] = {}
        self.reported = None
        self.statements: list[str] = []

    # -- reads -------------------------------------------------------------------------------
    def _positions(self):
        rows = []
        for g in self.chart["grahas"]:
            subject = _SUBJECT.get(g["name"])
            if subject is None:
                continue
            rows += [
                (subject, "sign", g["sign"], None),
                (subject, "degree_in_sign", None, g["degree_in_sign"]),
                (subject, "longitude_sidereal", None, g["longitude_deg"]),
                (subject, "house_d1", None, g["house"]),
                (subject, "retrograde_flag", "retrograde" if g.get("retrograde") else "direct", None),
            ]
        return rows

    def _divisionals(self):
        rows = []
        for g in self.chart["grahas"]:
            if g["name"] not in _SUBJECT:
                continue
            for i, varga in enumerate(VARGAS):
                rows.append((g["name"], varga, "degree_in_sign", None, (g["degree_in_sign"] + i) % 30.0))
                rows.append((g["name"], varga, "dignity", "Neutral", None))
        return rows

    # -- cursor / execute --------------------------------------------------------------------
    def cursor(self, *args, **kwargs):
        return _Cursor(self)

    def execute(self, sql, params=None):
        return self._run(sql, params)

    def _run(self, sql, params):
        self.statements.append(sql)
        if "FROM chart_facts" in sql and "graha_sign_attributes" in sql:
            return _Result(self._positions())
        if "FROM chart_divisionals" in sql and "fact_category IN" in sql:
            # _load_varga_dignity_spread: (varga, fact_key, fact_value_text, fact_value_num) for ONE graha.
            # The stored chart_divisionals dignity label is Title-Case ("Neutral": F-C8 / the writer's
            # _DIVISIONAL_DIGNITY_NORMALIZE); a lower-case label scores nothing, which would make the
            # composite fall back to D1 and trip the X2 fallback guard (#2890) on this double.
            graha = params[2]
            return _Result(
                (varga, "dignity", "Neutral", None) for varga in VARGAS if graha in _SUBJECT
            )
        if "FROM chart_divisionals" in sql:
            return _Result(self._divisionals())
        if "INSERT INTO ga_condition_composite" in sql:
            self.composite += 1
            return _Result(rowcount=1)
        if "INSERT INTO chart_facts" in sql:
            # columns: fact_id first; ON CONFLICT is not used by this writer (plain INSERT)
            fid = params[0]
            assert fid not in self.facts, f"duplicate fact_id {fid!r}: plain INSERT would raise"
            self.facts[fid] = params[4]
            return _Result(rowcount=1)
        if "complete_l1_data_plane_partition" in sql:
            self.reported = params[-1]
            captured = self.composite + len(self.facts)
            if self.reported != captured:
                raise RuntimeError(
                    f"L1 partition {params[3]} reported {self.reported} rows but protected capture "
                    f"contains {captured}"
                )
        return _Result()


class _Cursor:
    def __init__(self, conn):
        self._conn = conn
        self._last = _Result()
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._last = self._conn._run(sql, params)
        self.rowcount = self._last.rowcount
        return self._last

    def fetchall(self):
        return self._last.fetchall()


@pytest.fixture(scope="module")
def chart_output():
    return compute_chart(inputs=SYNTHETIC_BP, ayanamsha_id="lahiri")


def _run_substep(conn):
    discover_all()
    writer = list_writers()["ga_condition"]()
    ctx = ContextSpec(
        asset_id="ga_condition", build_id=BUILD, db_conn=conn, config={"chart_id": CHART},
    )
    step = writer.plan_substeps(ctx)[0]
    return writer.run_substep(ctx, step)


def test_substep_reports_composite_and_avastha_rows_and_matches_capture(chart_output):
    conn = _CaptureConn(chart_output)
    result = _run_substep(conn)  # raises "reported N rows but protected capture contains M" on a mismatch
    assert conn.composite == 9
    assert len(conn.facts) > 9, "the synthetic chart must exercise the avastha chart_facts inserts"
    assert result.rows_inserted == conn.composite + len(conn.facts)
    assert conn.reported == result.rows_inserted


def test_avastha_rows_cover_per_varga_and_d1_categories(chart_output):
    conn = _CaptureConn(chart_output)
    _run_substep(conn)
    categories = set(conn.facts.values())
    assert {"graha_avastha_baladi_per_varga", "graha_avastha_deeptaadi_per_varga"} <= categories
    assert {"graha_avastha_sayanadi", "graha_avastha_lajjitadi"} <= categories


def test_reporting_only_the_composite_rows_fails_the_partition(chart_output, monkeypatch):
    """Mutation guard: the pre-fix behaviour (avastha inserts not counted) is exactly the failure."""
    import ga_writers.ga_condition_writer as gc

    real = gc._insert_per_varga_avastha_rows

    def uncounted(conn, rows):
        real(conn, rows)
        return 0

    monkeypatch.setattr(gc, "_insert_per_varga_avastha_rows", uncounted)
    with pytest.raises(RuntimeError, match=r"reported 9 rows but protected capture contains \d+"):
        _run_substep(_CaptureConn(chart_output))
