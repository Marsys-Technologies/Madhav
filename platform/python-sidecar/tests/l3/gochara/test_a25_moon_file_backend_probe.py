"""A2.5 (steward M20261001T194030-8c0f, Suvarṇa SS N-28): the kernel's Swiss
backend gate must not trust the Moon's returned flag.

Measured on pyswisseph (this machine, real .se1): with `semo_*.se1` missing,
`calc_ut(MOON, FLG_SWIEPH)` returns the Moshier Moon (0.087″ off) while the
returned flag STILL carries SWIEPH (`retflag & 2`); TRUE_NODE — computed from
the same Moon file — reports the substitution honestly (`retflag & 4`). The
kernel therefore gates every Moon calc with a file-level TRUE_NODE probe at the
same instant (`knots._assert_moon_file_backend`).

Two layers:
  * REAL library (skipped NOT_RUN when the pinned .se1 files are absent): a
    directory holding `sepl` only — the exact production failure — must make the
    Moon fail closed through every kernel entry point.
  * FAKED library (always runs): a stand-in `swe` that models the measured
    behaviour as a function of which files are in a real temp directory, so the
    probe's own logic (block selection, cache scope, invalidation, ambient path)
    is exercised in CI, where the pinned files are not present. Only the C
    library is faked; the code under test is the kernel's.
"""
from __future__ import annotations

import os
import shutil
from datetime import date
from pathlib import Path

import pytest
import swisseph as real_swe

from services.gochara_kernel import knots
from services.gochara_kernel.contacts import swiss_bisect
from services.gochara_kernel.knots import EphemerisBackendError, calc_sidereal_lon, sample_knots

from .conftest import EPHE_PATH, requires_swieph

J2000 = 2451545.0
JD_2500 = 2451545.0 + 500 * 365.2425  # year 2500 → the semo_24 block


@pytest.fixture(autouse=True)
def _fresh_probe_cache(monkeypatch):
    knots._MOON_FILE_PROBE_OK.clear()
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    yield
    knots._MOON_FILE_PROBE_OK.clear()


# ── REAL library ─────────────────────────────────────────────────────────────

@pytest.fixture
def sepl_only_dir(tmp_path):
    """The production failure shape: planets present, Moon file absent."""
    d = tmp_path / "sepl_only"
    d.mkdir()
    shutil.copy(Path(EPHE_PATH) / "sepl_18.se1", d / "sepl_18.se1")
    return str(d)


@requires_swieph
def test_real_moon_flag_lies_but_the_kernel_fails_closed(sepl_only_dir):
    real_swe.set_ephe_path(sepl_only_dir)
    real_swe.set_sid_mode(real_swe.SIDM_LAHIRI)
    _lon, raw_flag = real_swe.calc_ut(J2000, real_swe.MOON, knots.EPHE_FLAGS)
    assert raw_flag & 2 and not raw_flag & 4, (
        "precondition (the SS N-28 measurement): without semo the Moon's own "
        "flag still says SWIEPH — if this stops holding the probe is redundant"
    )
    with pytest.raises(EphemerisBackendError) as excinfo:
        calc_sidereal_lon("Moon", J2000, sepl_only_dir)
    assert excinfo.value.body == "Moon"
    assert excinfo.value.retflag & 4
    assert "file-level probe" in str(excinfo.value)


@requires_swieph
def test_real_other_bodies_are_not_gated_on_the_moon_file(sepl_only_dir):
    # Sun (sepl) and the analytic mean node (Rahu/Ketu) are honest/independent of semo.
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


# ── FAKED library (CI) ───────────────────────────────────────────────────────

class _FakeSwe:
    """Models the measured pyswisseph behaviour from the files in the path dir:
    planets need `sepl_<block>`; the Moon AND TRUE_NODE need `semo_<block>`; the
    mean node is analytic. Moon without semo: Moshier value, SWIEPH flag (the
    lie). TRUE_NODE without semo: MOSEPH flag (honest)."""

    def __init__(self):
        self.files: set[str] = set()
        self.calls: list[tuple[int, float]] = []

    def __getattr__(self, name):          # constants / julday etc. from the real module
        return getattr(real_swe, name)

    def set_ephe_path(self, path):
        self.files = set(os.listdir(path)) if path and os.path.isdir(path) else set()

    def set_sid_mode(self, *_a, **_k):
        return None

    @staticmethod
    def _suffix(jd: float) -> int:
        year = 2000.0 + (jd - 2451545.0) / 365.2425
        return 18 + 6 * int((year - 1800.0) // 600.0)

    def calc_ut(self, jd, body, flags):
        self.calls.append((body, jd))
        suffix = self._suffix(jd)
        has_pl = f"sepl_{suffix}.se1" in self.files
        has_mo = f"semo_{suffix}.se1" in self.files
        base = int(flags) & ~(real_swe.FLG_SWIEPH | real_swe.FLG_MOSEPH)
        swieph, moseph = base | real_swe.FLG_SWIEPH, base | real_swe.FLG_MOSEPH
        lon = 100.0
        if body == real_swe.MOON:
            return ((lon, 0.0, 0.0, 0.0), swieph)          # served either way — the lie
        if body == real_swe.TRUE_NODE:
            return ((lon, 0.0, 0.0, 0.0), swieph if has_mo else moseph)
        if body == real_swe.MEAN_NODE:
            return ((lon, 0.0, 0.0, 0.0), swieph)          # analytic
        return ((lon, 0.0, 0.0, 0.0), swieph if has_pl else moseph)

    def true_node_probes(self) -> int:
        return sum(1 for b, _ in self.calls if b == real_swe.TRUE_NODE)


@pytest.fixture
def fake(monkeypatch):
    f = _FakeSwe()
    monkeypatch.setattr(knots, "swe", f)
    return f


def _dir(tmp_path, *names, label="eph"):
    d = tmp_path / label
    d.mkdir()
    for n in names:
        (d / n).write_bytes(b"x")
    return str(d)


def test_fake_precondition_models_the_measured_lie(tmp_path, fake):
    d = _dir(tmp_path, "sepl_18.se1")
    fake.set_ephe_path(d)
    assert fake.calc_ut(J2000, real_swe.MOON, real_swe.FLG_SWIEPH)[1] & 2
    assert fake.calc_ut(J2000, real_swe.TRUE_NODE, real_swe.FLG_SWIEPH)[1] & 4


def test_missing_semo_moon_fails_closed_but_the_sun_is_not_gated(tmp_path, fake):
    d = _dir(tmp_path, "sepl_18.se1")
    with pytest.raises(EphemerisBackendError) as excinfo:
        calc_sidereal_lon("Moon", J2000, d)
    assert excinfo.value.body == "Moon" and excinfo.value.retflag & 4
    assert "file-level probe" in str(excinfo.value)
    lon, retflag = calc_sidereal_lon("Sun", J2000, d)
    assert retflag & 2 and not retflag & 4


@pytest.mark.parametrize("entry", ["calc", "sample_knots", "swiss_bisect"])
def test_missing_semo_fails_closed_through_every_entry_point(tmp_path, fake, entry):
    d = _dir(tmp_path, "sepl_18.se1")
    with pytest.raises(EphemerisBackendError):
        if entry == "calc":
            calc_sidereal_lon("Moon", J2000, d)
        elif entry == "sample_knots":
            sample_knots("Moon", date(2000, 1, 1), date(2000, 1, 6), ephe_path=d)
        else:
            swiss_bisect("Moon", J2000, J2000 + 0.5, 100.0, d)


def test_full_directory_passes_and_the_probe_is_cached(tmp_path, fake):
    d = _dir(tmp_path, "sepl_18.se1", "semo_18.se1")
    for _ in range(3):
        _lon, retflag = calc_sidereal_lon("Moon", J2000, d)
        assert retflag & 2
    assert fake.true_node_probes() == 1


def test_probe_reruns_when_the_directory_changes_underneath_a_cached_success(tmp_path, fake):
    d = _dir(tmp_path, "sepl_18.se1", "semo_18.se1")
    calc_sidereal_lon("Moon", J2000, d)
    os.remove(os.path.join(d, "semo_18.se1"))
    st = os.stat(d)
    os.utime(d, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))  # force a distinct stamp
    with pytest.raises(EphemerisBackendError):
        calc_sidereal_lon("Moon", J2000, d)


def test_a_cached_block_does_not_vouch_for_another_block(tmp_path, fake):
    d = _dir(tmp_path, "sepl_18.se1", "semo_18.se1")   # covers 1800–2399 only
    calc_sidereal_lon("Moon", J2000, d)                 # block 0 cached
    with pytest.raises(EphemerisBackendError):
        calc_sidereal_lon("Moon", JD_2500, d)           # block 1 needs semo_24
    d2 = _dir(tmp_path, "sepl_18.se1", "semo_18.se1", "semo_24.se1", label="eph2")
    calc_sidereal_lon("Moon", J2000, d2)
    calc_sidereal_lon("Moon", JD_2500, d2)               # both blocks present → passes


def test_an_unstatable_ambient_path_is_never_cached(fake):
    fake.files = {"sepl_18.se1", "semo_18.se1"}          # ambient state: no explicit path
    for _ in range(3):
        calc_sidereal_lon("Moon", J2000, None)
    assert fake.true_node_probes() == 3


def test_a_failed_probe_is_not_cached(tmp_path, fake):
    d = _dir(tmp_path, "sepl_18.se1")
    for _ in range(2):
        with pytest.raises(EphemerisBackendError):
            calc_sidereal_lon("Moon", J2000, d)
    assert fake.true_node_probes() == 2
