"""The two composite_shift_check pins that need PyJHora and the sidecar writers (moved out of the governance test suite).

platform/scripts/governance/__tests__/test_composite_shift_check.py runs in the governance CI job, which has no PyJHora / swisseph, so it cannot
import `jhora` or `ga_writers` (a skip would earn nothing, N.8). These two tests keep the same assertions here, where the sidecar CI selection
(`pytest tests/`) has both: (1) the longevity full-slope tables the hand-check embeds are PyJHora's own constants; (2) the CS6 label boundaries
(varga sign edges, mrityu tolerances, pushkara navamsa starts/arc/orb, ayus class edges) are the writers' own values.
The module under test is evidence/composite_shift_check.py (HOOKS_W7_HAND_READBACK H24); the governance fixture/helpers are not needed.
"""
from __future__ import annotations

import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO / "00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/composite_shift_check.py"
spec = importlib.util.spec_from_file_location("composite_shift_check", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

SIDECAR = REPO / "platform/python-sidecar"


def _writers():
    from ga_writers import ga_ayurdaya_writer, ga_sensitive_degree_writer, ga_vargas_writer
    return ga_vargas_writer, ga_sensitive_degree_writer, ga_ayurdaya_writer


def test_the_longevity_slopes_are_the_pyjhora_constants_the_writer_delegates_to():
    from jhora import const
    assert tuple(const.pindayu_full_longevity_of_planets) == M.PINDAYU_FULL
    assert tuple(const.nisargayu_full_longevity_of_planets) == M.NISARGAYU_FULL


def test_CS6_label_boundaries_are_the_writers_own():
    """The model: every varga's sign changes exactly at multiples of 30/n of the D1 longitude, nowhere else; the mrityu tolerances,
    pushkara navamsa starts / arc / bhaga orb and the ayus class edges are the writers' (PyJHora const) values."""
    from jhora import const
    gv, gs, ga = _writers()

    def sign(n, lam):
        return gv._compute_d2_hora(lam) if n == 2 else gv._compute_d3_drekkana(lam) if n == 3 else \
            int(lam / 30.0) % 12 if n == 1 else gv._compute_general_varga(lam, n)
    eps = 1e-7
    for n in (int(v[1:]) for v in M.VARGAS):
        step = 30.0 / n
        for k in (1, 7, n + 3, 11 * n - 1):                        # boundaries inside and at the edges of signs
            b = k * step
            assert sign(n, b - eps) != sign(n, b + eps), (n, k)    # a boundary flips the label...
            assert sign(n, b + eps) == sign(n, b + step - eps), (n, k)   # ...and nothing flips it inside one amsa
    assert {g: M.MRITYU_TOL[g] for g in M.MRITYU_TOL} == {g: gs.mrityu_bhaga_tolerance(g) for g in M.MRITYU_TOL}
    assert tuple(const.pushkara_navamsa) == M.PUSHKARA_NAVAMSA_START and gs.PUSHKARA_NAVAMSA_ARC == M.PUSHKARA_NAVAMSA_ARC
    assert "bhaga_orb <= 0.5" in (SIDECAR / "ga_writers/ga_sensitive_degree_writer.py").read_text() and M.PUSHKARA_BHAGA_ORB == 0.5
    for edge in M.AYUS_BOUNDARIES:
        assert ga.classify_ayus(edge - 1e-9) != ga.classify_ayus(edge)
    assert [ga.classify_ayus(x) for x in (0.0, 31.9, 32.0, 63.9, 64.0, 120.0)] == ["alpayu", "alpayu", "madhyayu", "madhyayu", "purnayu", "purnayu"]
