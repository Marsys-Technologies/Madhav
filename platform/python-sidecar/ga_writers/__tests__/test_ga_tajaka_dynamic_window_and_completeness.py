"""
NIR-08 regression tests — dynamic ga_tajaka window expectations & pre-insert completeness.

Covers:
1. Dynamic expected row counts across younger (`2020-02-29` -> 12*5 = 60), leap-day
   (`1996-02-29` -> 36*5 = 180), and observed adult (`1984-02-05` -> 48*5 = 240,
   `1971-04-21` -> 61*5 = 305) chart windows without triggering a static 240-floor warning.
2. Complete narrower explicit windows (e.g. `min_varsha=2, max_varsha=5`) succeed cleanly.
3. Pre-insert completeness/contiguity gate rejects missing frames, gapped varsha years,
   or duplicate varsha years *before* calling `replace_prior_tajik_varsha` or `_insert_rows`,
   naming the specific calculation frame and gap.
4. Orchestrator readiness probe with `target_floor = None` marks younger charts `lit`
   without false `below target_floor` warnings while keeping 0-row fail-closed `dormant`.
"""
from __future__ import annotations

import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ga_writers.ga_tajaka_writer as sut  # noqa: E402
from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator.writers import WriterBase, WriterResult  # noqa: E402


_SE1_AVAILABLE = bool(os.environ.get("SE_EPHE_PATH")) and os.path.isdir(os.environ["SE_EPHE_PATH"])


def _stub_row(chart_id: str, aya: str, v: int) -> dict:
    return {
        "varsha_id": f"{chart_id}:{aya}:{v}",
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": "test-build",
        "varsha_year": v,
        "varsha_start_iso": f"{2000 + v}-01-01T00:00:00+00:00",
        "varsha_end_iso": f"{2001 + v}-01-01T00:00:00+00:00",
        "muntha_sign": "Aries",
        "muntha_house": 1,
        "muntha_lord": "Mars",
        "muntha_position_jsonb": {},
        "year_lord": "Sun",
        "year_lord_method": "tajik_classical",
        "candidate_lord_jsonb": {},
        "tajik_yogas_jsonb": [],
        "verification_pass_status": "single",
        "source_citation": "test",
        "classical_source_citation": "Tajika Nilakanthi",
        "citation_human": f"Varsha {v}",
        "ephemeris_audit_jsonb": {},
        "engine_version": sut.ENGINE_VERSION,
        "computed_at": "2026-11-21T00:00:00+00:00",
    }


@pytest.mark.parametrize(
    ("birth_year", "expected_max", "expected_total"),
    [
        (2020, 12, 60),   # younger 2020-02-29 fixture
        (1996, 36, 180),  # observed leap-day 1996-02-29 fixture
        (1984, 48, 240),  # observed Abhisek 1984-02-05 chart
        (1971, 61, 305),  # observed Kiran 1971 chart
    ],
)
def test_dynamic_window_scales_with_chart_birth_year(birth_year, expected_max, expected_total):
    spec = sut.compute_expected_tajaka_window(birth_year, reference_year=2026)
    assert spec["min_varsha"] == 1
    assert spec["max_varsha"] == expected_max
    assert spec["years_per_frame"] == expected_max
    assert len(spec["ayanamshas"]) == 5
    assert spec["expected_target_floor"] == expected_total


def test_younger_2020_leap_and_adult_windows_build_complete_offline(monkeypatch):
    monkeypatch.setattr(sut, "compute_chart", lambda inputs, ayanamsha_id: {
        "grahas": [{"name": "Sun", "longitude": 315.0}],
    })
    monkeypatch.setattr(sut, "replace_prior_tajik_varsha", lambda conn, rows: 0)

    for birth_iso, exp_max, exp_total in [
        ("2020-02-29T08:15:00", 12, 60),
        ("1996-02-29T05:30:00", 36, 180),
        ("1984-02-05T10:43:00", 48, 240),
        ("1971-04-21T06:00:00", 61, 305),
    ]:
        written: list[dict] = []
        monkeypatch.setattr(
            sut, "_compute_one",
            lambda conn, cid, aya, adapter, v, natal, natal_sun, build_id, birth=None: _stub_row(cid, aya, v),
        )
        monkeypatch.setattr(sut, "_insert_rows", lambda conn, rows: (written.extend(rows), len(rows))[1])

        summary = sut.build_ga_tajaka(
            "11111111-1111-4111-8111-111111111111",
            "build-nir08",
            conn=object(),
            birth_params={"datetime_iso": birth_iso, "latitude_deg": 20.27, "longitude_deg": 85.84, "tz_offset_hours": 5.5},
            reference_year=2026,
        )
        assert summary["status"] == "PASS"
        assert summary["total_rows_written"] == exp_total
        assert summary["expected_target_floor"] == exp_total
        assert summary["window"]["max_varsha"] == exp_max
        assert all(c == exp_max for c in summary["per_ayanamsha_counts"].values())
        assert f"varsha 1..{exp_max} precomputed per frame" in summary["storage_strategy"]
        assert len(written) == exp_total


@pytest.mark.skipif(not _SE1_AVAILABLE, reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_younger_2020_leap_chart_real_ephemeris_end_to_end(monkeypatch):
    """Real PyJHora ephemeris build for a 2020-02-29 younger chart (12 years x 5 = 60 rows)."""
    written: list[dict] = []
    monkeypatch.setattr(sut, "_read_trirashipathi", lambda conn, cid, aya: None)
    monkeypatch.setattr(sut, "replace_prior_tajik_varsha", lambda conn, rows: 0)
    monkeypatch.setattr(sut, "_insert_rows", lambda conn, rows: (written.extend(rows), len(rows))[1])

    summary = sut.build_ga_tajaka(
        "20200229-0000-4000-8000-000000000001",
        "build-younger-real",
        conn=object(),
        birth_params={
            "datetime_iso": "2020-02-29T08:15:00",
            "latitude_deg": 20.27,
            "longitude_deg": 85.84,
            "tz_offset_hours": 5.5,
        },
        reference_year=2026,
    )
    assert summary["status"] == "PASS"
    assert summary["window"]["min_varsha"] == 1
    assert summary["window"]["max_varsha"] == 12
    assert summary["expected_target_floor"] == 60
    assert summary["total_rows_written"] == 60
    for aya in sut.CANONICAL_AYANAMSHAS:
        years = [r["varsha_year"] for r in written if r["ayanamsha_id"] == aya]
        assert years == list(range(1, 13)), aya


def test_narrower_explicit_window_completes_cleanly(monkeypatch):
    written: list[dict] = []
    monkeypatch.setattr(sut, "compute_chart", lambda inputs, ayanamsha_id: {
        "grahas": [{"name": "Sun", "longitude": 315.0}],
    })
    monkeypatch.setattr(
        sut, "_compute_one",
        lambda conn, cid, aya, adapter, v, natal, natal_sun, build_id, birth=None: _stub_row(cid, aya, v),
    )
    monkeypatch.setattr(sut, "replace_prior_tajik_varsha", lambda conn, rows: 0)
    monkeypatch.setattr(sut, "_insert_rows", lambda conn, rows: (written.extend(rows), len(rows))[1])

    summary = sut.build_ga_tajaka(
        "11111111-1111-4111-8111-111111111111",
        "build-narrow",
        conn=object(),
        birth_params={"datetime_iso": "2020-02-29T08:15:00", "latitude_deg": 20.27, "longitude_deg": 85.84, "tz_offset_hours": 5.5},
        reference_year=2026,
        min_varsha=2,
        max_varsha=5,
    )
    assert summary["status"] == "PASS"
    assert summary["years_per_frame"] == 4
    assert summary["expected_target_floor"] == 20
    assert summary["total_rows_written"] == 20
    assert f"varsha 2..5 precomputed per frame" in summary["storage_strategy"]


def test_gapped_varsha_halts_before_delete_or_insert_and_names_frame_and_gap(monkeypatch):
    monkeypatch.setattr(sut, "compute_chart", lambda inputs, ayanamsha_id: {
        "grahas": [{"name": "Sun", "longitude": 315.0}],
    })

    def bad_compute_one(conn, cid, aya, adapter, v, natal, natal_sun, build_id, birth=None):
        row = _stub_row(cid, aya, v)
        if aya == "raman" and v == 4:
            # Simulates a corrupted/shifted year causing a gap at year 4 and duplicate at 5
            row["varsha_year"] = 5
        return row

    db_calls: list[str] = []
    monkeypatch.setattr(sut, "_compute_one", bad_compute_one)
    monkeypatch.setattr(sut, "replace_prior_tajik_varsha", lambda conn, rows: db_calls.append("delete") or 0)
    monkeypatch.setattr(sut, "_insert_rows", lambda conn, rows: db_calls.append("insert") or len(rows))

    with pytest.raises(RuntimeError, match=r"frame=raman.*duplicate varsha_year\(s\) \[5\]"):
        sut.build_ga_tajaka(
            "11111111-1111-4111-8111-111111111111",
            "build-dup",
            conn=object(),
            birth_params={"datetime_iso": "2020-02-29T08:15:00", "latitude_deg": 20.27, "longitude_deg": 85.84, "tz_offset_hours": 5.5},
            reference_year=2026,
            min_varsha=1,
            max_varsha=5,
        )
    assert db_calls == [], f"completeness halt must fire before DB writes; saw {db_calls}"


def test_missing_varsha_gap_validator_names_specific_frame_and_missing_years():
    frames = list(sut.CANONICAL_AYANAMSHAS.keys())
    complete_rows = [
        {"ayanamsha_id": aya, "varsha_year": v}
        for aya in frames
        for v in range(1, 6)
    ]
    gapped = [r for r in complete_rows if not (r["ayanamsha_id"] == "krishnamurti" and r["varsha_year"] in (2, 4))]
    with pytest.raises(RuntimeError, match=r"frame=krishnamurti.*missing varsha_year\(s\) \[2, 4\]"):
        sut._validate_tajaka_window_completeness(gapped, frames, 1, 5)

    missing_frame = [r for r in complete_rows if r["ayanamsha_id"] != "true_chitra"]
    with pytest.raises(RuntimeError, match=r"frame=true_chitra.*missing varsha_year\(s\) \[1, 2, 3, 4, 5\]"):
        sut._validate_tajaka_window_completeness(missing_frame, frames, 1, 5)


def test_invalid_window_bounds_rejected_explicitly():
    with pytest.raises(ValueError, match="min_varsha"):
        sut.compute_expected_tajaka_window(2020, reference_year=2026, min_varsha=0, max_varsha=5)
    with pytest.raises(ValueError, match="max_varsha"):
        sut.compute_expected_tajaka_window(2030, reference_year=2020)


def _drive_orchestrator_tajaka(monkeypatch, caplog, *, target_floor_value, simulate_zero_rows=False):
    """Drive `asset_runner._run_data_writer` through the real `ga_tajaka` adapter."""
    ar.discover_all()

    class _FakeCur:
        def __init__(self):
            self.executed: list[tuple[str, object]] = []
            self._last_sql = ""

        def execute(self, sql, params=None):
            self._last_sql = sql
            self.executed.append((sql, params))

        def fetchall(self):
            return []

        def fetchone(self):
            if "SELECT target_floor FROM asset_registry" in self._last_sql:
                return {"target_floor": target_floor_value}
            return None

    class _FakeConn:
        def commit(self):
            pass

        def rollback(self):
            pass

        def cursor(self):
            return _FakeCur()

    class _ZeroRowsWriter(WriterBase):
        asset_id = "ga_tajaka"

        def run(self, ctx):
            return WriterResult(asset_id="ga_tajaka", rows_inserted=0)

    cur = _FakeCur()
    conn = _FakeConn()
    if simulate_zero_rows:
        monkeypatch.setattr(ar, "get_writer", lambda asset_id: _ZeroRowsWriter)
        monkeypatch.setattr(ar, "_data_rows_present", lambda c, cu, aid, cid: 0)
    else:
        monkeypatch.setattr(sut, "_effective_reference_year", lambda ry: 2026)
        monkeypatch.setattr(sut, "compute_chart", lambda inputs, ayanamsha_id: {
            "grahas": [{"name": "Sun", "longitude": 315.0}],
        })
        monkeypatch.setattr(
            sut, "_compute_one",
            lambda c, cid, aya, adapter, v, natal, natal_sun, bid, birth=None: _stub_row(cid, aya, v),
        )
        monkeypatch.setattr(sut, "replace_prior_tajik_varsha", lambda c, rows: 0)
        monkeypatch.setattr(sut, "_insert_rows", lambda c, rows: len(rows))
        monkeypatch.setattr(ar, "_data_rows_present", lambda c, cu, aid, cid: 60)

    monkeypatch.setattr(ar, "fetch_birth_params", lambda c, cid: {
        "datetime_iso": "2020-02-29T08:15:00",
        "latitude_deg": 20.27,
        "longitude_deg": 85.84,
        "tz_offset_hours": 5.5,
    })
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda *a, **k: "h-up")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda *a, **k: "h-wr")
    monkeypatch.setattr(ar, "compute_downstream_closure", lambda *a, **k: [])
    monkeypatch.setattr(ar, "_duration_columns_present", lambda cu: False)

    with caplog.at_level(logging.WARNING, logger=ar.__name__):
        ok = ar._run_data_writer(
            conn, cur, "build-nir08", "20200229-0000-4000-8000-000000000001", "ga_tajaka"
        )
    tp_updates = [p for sql, p in cur.executed if "UPDATE asset_throughput" in sql and "state =" in sql]
    return ok, tp_updates, [r.message for r in caplog.records]


def test_orchestrator_marks_younger_chart_lit_without_false_warning_when_floor_is_null(monkeypatch, caplog):
    ok, tp_updates, warn_msgs = _drive_orchestrator_tajaka(
        monkeypatch, caplog, target_floor_value=None
    )
    assert ok is True
    assert tp_updates and tp_updates[-1][0] == "lit"
    assert not any("below target_floor" in m for m in warn_msgs), warn_msgs

    # Control: static floor 240 reproduces the historical false warning on 60 rows.
    ok_old, _tp_old, old_warns = _drive_orchestrator_tajaka(
        monkeypatch, caplog, target_floor_value=240
    )
    assert ok_old is True
    assert any("rows_written=60 below target_floor=240" in m for m in old_warns), old_warns


def test_orchestrator_still_marks_zero_rows_dormant_when_floor_is_null(monkeypatch, caplog):
    ok, tp_updates, _warns = _drive_orchestrator_tajaka(
        monkeypatch, caplog, target_floor_value=None, simulate_zero_rows=True
    )
    assert ok is True
    assert tp_updates and tp_updates[-1][0] == "dormant"


def test_exact_zero_solar_return_diff_passes_cross_check(monkeypatch):
    """Exact diff_deg == 0.0 must not be coerced to 99.0 by Python falsy `or`."""
    from datetime import datetime

    monkeypatch.setattr(
        sut,
        "_solar_return",
        lambda *a, **k: (
            datetime(2022, 2, 28, 12, 0, 0),
            {"converged": True, "diff_deg": 0.0, "bracket_days": 2, "iterations": 13},
        ),
    )
    monkeypatch.setattr(
        sut,
        "compute_chart",
        lambda *a, **k: {
            "ascendant": {"sign_id": 4, "longitude_deg": 95.0},
            "grahas": [
                {"name": g, "longitude": 10.0 * (i + 1), "house": 10 if g == "Sun" else 1}
                for i, g in enumerate(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"])
            ],
        },
    )
    monkeypatch.setattr(sut, "_read_trirashipathi", lambda *a, **k: "Sun")
    row = sut._compute_one(
        conn=None,
        chart_id="11111111-1111-4111-8111-202002290001",
        canonical_aya="lahiri_chitrapaksha",
        aya_adapter="lahiri",
        varsha_year=2,
        natal_chart={"ascendant": {"sign_id": 1, "degree_in_sign": 5.0}},
        natal_sun_long=315.931905,
        build_id="build-zero-diff",
        birth={"birth_date": "2020-02-29", "birth_time": "10:15:00", "lat": 28.6139, "lon": 77.2090, "tz": 5.5},
    )
    assert row["ephemeris_audit_jsonb"]["solar_return_cross_check_pass"] is True
    assert row["verification_pass_status"] != "divergent_flagged"

    # Control: missing diff_deg=None still fails closed.
    monkeypatch.setattr(
        sut,
        "_solar_return",
        lambda *a, **k: (
            datetime(2022, 2, 28, 12, 0, 0),
            {"converged": True, "diff_deg": None, "bracket_days": 2, "iterations": 13},
        ),
    )
    row_none = sut._compute_one(
        conn=None,
        chart_id="11111111-1111-4111-8111-202002290001",
        canonical_aya="lahiri_chitrapaksha",
        aya_adapter="lahiri",
        varsha_year=2,
        natal_chart={"ascendant": {"sign_id": 1, "degree_in_sign": 5.0}},
        natal_sun_long=315.931905,
        build_id="build-none-diff",
        birth={"birth_date": "2020-02-29", "birth_time": "10:15:00", "lat": 28.6139, "lon": 77.2090, "tz": 5.5},
    )
    assert row_none["ephemeris_audit_jsonb"]["solar_return_cross_check_pass"] is False
    assert row_none["verification_pass_status"] == "divergent_flagged"
