"""A2.5 (steward M20261001T194030-8c0f, Suvarṇa SS N-28; ASTRA v1.2 R3): the kernel's Swiss
backend gate must not trust the Moon's returned flag — and must not REMEMBER a success.

Measured on pyswisseph (real, checksum-pinned .se1): with `semo_*.se1` missing,
`calc_ut(MOON, FLG_SWIEPH)` returns the Moshier Moon (0.087″ off) while the returned flag
STILL carries SWIEPH (`retflag & 2`); TRUE_NODE — computed from the same Moon file —
reports the substitution honestly (`retflag & 4`). The kernel therefore gates every Moon
calc with a file-level TRUE_NODE probe at the call's OWN instant
(`knots._assert_moon_file_backend`), uncached.

Why uncached (v1.2 R3): a success cache keyed on a calendar-year block and a directory stamp
is unsound — `semo_18.se1` actually ends in January 2400 (JD 2597656.46), not at a block
boundary, and directory metadata is not file identity. The real-library tests below pin the
REAL coverage edges; the faked-library layer models coverage as an explicit JD interval (the
measured one), never the implementation's own approximation.

Two layers:
  * REAL library (skipped NOT_RUN when the pinned .se1 files are absent);
  * FAKED library (always runs in CI): only the C library is faked.
"""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest
import swisseph as real_swe

from panchang_engine.swiss_state import swiss_state_scope
from services.gochara_kernel import contacts as kernel_contacts
from services.gochara_kernel import knots
from services.gochara_kernel.contacts import swiss_bisect
from services.gochara_kernel.knots import EphemerisBackendError, calc_sidereal_lon, sample_knots

from .conftest import EPHE_PATH, requires_swieph

J2000 = 2451545.0
# the MEASURED coverage edges of semo_18.se1 (this machine, real library)
SEMO_18_FIRST_JD = 2378487.555370702
SEMO_18_LAST_JD = 2597656.4574524714       # January 2400
JD_INSIDE_JAN_2400 = 2597643.0             # 2400-01-02: real TRUE_NODE flag = SWIEPH
JD_OUTSIDE_JAN_2400 = 2597661.0            # 2400-01-20: past the file — real flag = MOSEPH
JD_BEFORE_1800 = 2378466.0                 # 1799-12-01: before the file — real flag = MOSEPH


# ── REAL library ─────────────────────────────────────────────────────────────

@pytest.fixture
def sepl_only_dir(tmp_path, monkeypatch):
    """The production failure shape: planets present, Moon file absent.

    C22 isolation: the Swiss C library ALSO searches the SE_EPHE_PATH environment
    variable after ``set_ephe_path(<dir>)`` (the measured caveat in
    panchang_engine/swiss_backend.py), so a process-level corpus would serve the
    Moon anyway and the "missing semo" simulation would silently not be one.
    Both legacy path variables are pinned at the sepl-only directory for the
    duration of the test (monkeypatch restores them afterwards).
    """
    d = tmp_path / "sepl_only"
    d.mkdir()
    shutil.copy(Path(EPHE_PATH) / "sepl_18.se1", d / "sepl_18.se1")
    monkeypatch.setenv("SE_EPHE_PATH", str(d))
    monkeypatch.setenv("SWE_EPHE_PATH", str(d))
    return str(d)


def _assert_no_moon_file_open() -> None:
    """Detector for the simulation itself: with semo absent, no Moon file may be
    open after the calc — otherwise some search path leaked the corpus back in.
    (On a failed open the C library still reports the ATTEMPTED path with zero
    coverage dates, so the check is whether the reported path actually exists.)"""
    path = real_swe.get_current_file_data(1)[0]
    assert not (path and Path(path).exists()), (
        f"the missing-semo simulation is broken: Moon file {path!r} was opened "
        "(SE_EPHE_PATH leaked a second search path into the test)"
    )


@requires_swieph
def test_real_moon_flag_lies_but_the_kernel_fails_closed(sepl_only_dir):
    with swiss_state_scope():
        real_swe.set_ephe_path(sepl_only_dir)
        real_swe.set_sid_mode(real_swe.SIDM_LAHIRI)
        _lon, raw_flag = real_swe.calc_ut(J2000, real_swe.MOON, knots.EPHE_FLAGS)
    assert raw_flag & 2 and not raw_flag & 4, (
        "precondition (the SS N-28 measurement): without semo the Moon's own "
        "flag still says SWIEPH — if this stops holding the probe is redundant"
    )
    _assert_no_moon_file_open()
    with pytest.raises(EphemerisBackendError) as excinfo:
        calc_sidereal_lon("Moon", J2000, sepl_only_dir)
    assert excinfo.value.body == "Moon"
    assert excinfo.value.retflag & 4
    assert "file-level probe" in str(excinfo.value)
    _assert_no_moon_file_open()


@requires_swieph
def test_real_other_bodies_are_not_gated_on_the_moon_file(sepl_only_dir):
    for body in ("Sun", "Mars", "Rahu", "Ketu"):
        lon, retflag = calc_sidereal_lon(body, J2000, sepl_only_dir)
        assert retflag & 2 and not retflag & 4, body
        assert 0.0 <= lon < 360.0


@requires_swieph
def test_real_full_directory_passes_and_matches_the_ungated_moon():
    lon, retflag = calc_sidereal_lon("Moon", J2000, EPHE_PATH)
    raw, _ = real_swe.calc_ut(J2000, real_swe.MOON, knots.EPHE_FLAGS)
    assert retflag & 2 and not retflag & 4
    assert lon == pytest.approx(float(raw[0]), abs=1e-12)


@requires_swieph
def test_real_entry_points_all_fail_closed_for_the_moon(sepl_only_dir):
    with pytest.raises(EphemerisBackendError):
        sample_knots("Moon", date(2000, 1, 1), date(2000, 1, 6), ephe_path=sepl_only_dir)
    with pytest.raises(EphemerisBackendError):
        swiss_bisect("Moon", J2000, J2000 + 0.5, 199.0, sepl_only_dir)
    _assert_no_moon_file_open()


@requires_swieph
@pytest.mark.parametrize("jd,ok", [
    (JD_INSIDE_JAN_2400, True),       # inside the file's REAL coverage
    (JD_OUTSIDE_JAN_2400, False),     # 18 days later, same calendar "block": past the file
    (JD_BEFORE_1800, False),          # before the file
    (2378528.0, True),                # 1800-02-01: first covered months
    (2461042.0, True),                # 2026-01-01
])
def test_real_coverage_edges_decide_each_calls_own_probe(jd, ok):
    """No block approximation: the file that serves the Moon AT THAT JD is the file
    proven. 2400-01-02 passes and 2400-01-20 raises although a calendar-block rule would
    treat them as the same block (the v1.2 R3 reproduction, on the real library)."""
    assert SEMO_18_FIRST_JD < 2378528.0 < SEMO_18_LAST_JD
    if ok:
        _lon, retflag = calc_sidereal_lon("Moon", jd, EPHE_PATH)
        assert retflag & 2 and not retflag & 4
    else:
        with pytest.raises(EphemerisBackendError) as excinfo:
            calc_sidereal_lon("Moon", jd, EPHE_PATH)
        assert "file-level probe" in str(excinfo.value)


@requires_swieph
def test_real_a_warm_in_coverage_call_never_vouches_for_a_later_out_of_coverage_one():
    calc_sidereal_lon("Moon", JD_INSIDE_JAN_2400, EPHE_PATH)          # warm "the same block"
    with pytest.raises(EphemerisBackendError):
        calc_sidereal_lon("Moon", JD_OUTSIDE_JAN_2400, EPHE_PATH)


# ── FAKED library (CI) ───────────────────────────────────────────────────────

class _FakeSwe:
    """Models the measured pyswisseph behaviour. File coverage is an explicit JD interval
    (the measured semo_18 one) — NOT a calendar block. Moon without a covering semo:
    Moshier value, SWIEPH flag (the lie). TRUE_NODE without one: MOSEPH flag (honest).
    `semo_ok` can be flipped at any time without touching any directory."""

    def __init__(self, semo_ranges=((SEMO_18_FIRST_JD, SEMO_18_LAST_JD),),
                 sepl_ok=True):
        self.semo_ranges = list(semo_ranges)
        self.semo_ok = True
        self.sepl_ok = sepl_ok
        self.calls: list[tuple[int, float]] = []

    def __getattr__(self, name):          # constants / julday etc. from the real module
        return getattr(real_swe, name)

    def set_ephe_path(self, path):
        return None

    def set_sid_mode(self, *_a, **_k):
        return None

    def _has_semo(self, jd):
        return self.semo_ok and any(a <= jd <= b for a, b in self.semo_ranges)

    def calc_ut(self, jd, body, flags):
        self.calls.append((body, jd))
        base = int(flags) & ~(real_swe.FLG_SWIEPH | real_swe.FLG_MOSEPH)
        swieph, moseph = base | real_swe.FLG_SWIEPH, base | real_swe.FLG_MOSEPH
        out = (100.0, 0.0, 0.0, 0.0)
        if body == real_swe.MOON:
            return (out, swieph)                               # served either way — the lie
        if body == real_swe.TRUE_NODE:
            return (out, swieph if self._has_semo(jd) else moseph)
        if body == real_swe.MEAN_NODE:
            return (out, swieph)                               # analytic
        return (out, swieph if self.sepl_ok else moseph)

    def true_node_probes(self) -> int:
        return sum(1 for b, _ in self.calls if b == real_swe.TRUE_NODE)


@pytest.fixture
def fake(monkeypatch):
    f = _FakeSwe()
    monkeypatch.setattr(knots, "swe", f)
    return f


def test_fake_precondition_models_the_measured_lie(fake):
    fake.semo_ok = False
    assert fake.calc_ut(J2000, real_swe.MOON, real_swe.FLG_SWIEPH)[1] & 2
    assert fake.calc_ut(J2000, real_swe.TRUE_NODE, real_swe.FLG_SWIEPH)[1] & 4


def test_missing_semo_moon_fails_closed_but_the_sun_is_not_gated(fake):
    fake.semo_ok = False
    with pytest.raises(EphemerisBackendError) as excinfo:
        calc_sidereal_lon("Moon", J2000, "/x")
    assert excinfo.value.body == "Moon" and excinfo.value.retflag & 4
    assert "file-level probe" in str(excinfo.value)
    lon, retflag = calc_sidereal_lon("Sun", J2000, "/x")
    assert retflag & 2 and not retflag & 4


@pytest.mark.parametrize("entry", ["calc", "sample_knots", "swiss_bisect"])
def test_missing_semo_fails_closed_through_every_entry_point(fake, entry):
    fake.semo_ok = False
    with pytest.raises(EphemerisBackendError):
        if entry == "calc":
            calc_sidereal_lon("Moon", J2000, "/x")
        elif entry == "sample_knots":
            sample_knots("Moon", date(2000, 1, 1), date(2000, 1, 6), ephe_path="/x")
        else:
            swiss_bisect("Moon", J2000, J2000 + 0.5, 100.0, "/x")


def test_every_moon_calc_probes_its_own_instant_nothing_is_remembered(fake):
    for _ in range(3):
        _lon, retflag = calc_sidereal_lon("Moon", J2000, "/x")
        assert retflag & 2
    assert fake.true_node_probes() == 3


def test_a_backend_loss_under_an_unchanged_directory_is_caught_on_the_very_next_call(fake):
    """The v1.2 R3 counterexample: warm the gate, then lose the Moon file while the
    directory metadata is untouched (file contents / a symlink target changed). A cache
    keyed on directory identity would keep vouching; an uncached probe refuses at once."""
    calc_sidereal_lon("Moon", J2000, "/x")             # warm
    fake.semo_ok = False                                # the file is gone; no directory touched
    with pytest.raises(EphemerisBackendError):
        calc_sidereal_lon("Moon", J2000, "/x")


def test_coverage_is_the_files_real_interval_not_a_calendar_block(fake):
    """Modelled on the measured edges: a call 18 days apart in the same calendar-year
    'block' is on the other side of the file's end."""
    calc_sidereal_lon("Moon", JD_INSIDE_JAN_2400, "/x")
    with pytest.raises(EphemerisBackendError):
        calc_sidereal_lon("Moon", JD_OUTSIDE_JAN_2400, "/x")
    with pytest.raises(EphemerisBackendError):
        calc_sidereal_lon("Moon", JD_BEFORE_1800, "/x")


def test_a_directory_with_several_semo_files_covers_the_union_of_their_intervals(monkeypatch):
    f = _FakeSwe(semo_ranges=((SEMO_18_FIRST_JD, SEMO_18_LAST_JD),
                              (SEMO_18_LAST_JD, SEMO_18_LAST_JD + 600_000.0)))
    monkeypatch.setattr(knots, "swe", f)
    calc_sidereal_lon("Moon", JD_INSIDE_JAN_2400, "/x")
    calc_sidereal_lon("Moon", JD_OUTSIDE_JAN_2400, "/x")       # semo_24 covers it


def test_the_probe_is_a_registered_serialized_owner_and_the_cache_is_gone():
    assert getattr(knots._assert_moon_file_backend, "__swiss_state_serialized__", False)
    assert not hasattr(knots, "_MOON_FILE_PROBE_OK")
    assert not hasattr(knots, "_ephe_dirs_stamp") and not hasattr(knots, "_moon_file_block")
