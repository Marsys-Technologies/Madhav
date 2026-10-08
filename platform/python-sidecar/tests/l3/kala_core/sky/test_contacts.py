"""KA-1e contact solver: the judge's O-AD-1…4 and O-RX-1 oracles against the
public contact result; stations always Swiss-refined; no substitute answer."""
from __future__ import annotations

import math

import pytest

from services.gochara_kernel import contacts as kernel_contacts
from services.gochara_kernel import knots
from services.gochara_kernel.arcs import build_arc_index
from services.gochara_kernel.substrate import contact_identity_bytes
from services.kala_core.sky import solve_contacts, stations
from services.kala_core.sky.contacts import STATION_METHOD
from services.kala_core.vocab import NullReason

T0 = 2461042.0                     # 2026-01-01 12:00 UT
CONVENTION = "c0"
TIGHT_ARCSEC = 1e-7
SWEEP_RATE = 0.5                   # °/day
TIME_TOL_DAYS = (1.0 / 60.0) / SWEEP_RATE     # ±1 arcmin of longitude


def index_over(days: int, curve, body: str):
    jds = [T0 + k for k in range(days + 1)]
    return build_arc_index(body, jds, [curve(j) % 360.0 for j in jds],
                           tolerance_arcsec=TIGHT_ARCSEC)


def sweep(jd: float) -> float:
    return SWEEP_RATE * (jd - T0)


def looping(jd: float) -> float:
    t = jd - T0
    return 193.0 + 0.05 * t + 6.0 * math.sin(2.0 * math.pi * t / 120.0)


# (oracle, body, target, aspect, body longitude at contact) — GOCHARA_TEST_ORACLES_v1_4
OAD_CASES = [
    ("O-AD-1", "Mars", 0.0, 90.0, 270.0),
    ("O-AD-2", "Mars", 0.0, 210.0, 150.0),
    ("O-AD-3", "Saturn", 0.0, 60.0, 300.0),
    ("O-AD-4", "Saturn", 0.0, 270.0, 90.0),
]


@pytest.mark.parametrize("oracle,body,target,aspect,body_lon", OAD_CASES,
                         ids=[c[0] for c in OAD_CASES])
def test_oad_aspect_direction(oracle, body, target, aspect, body_lon) -> None:
    index = index_over(3 * 365, sweep, body)
    result = solve_contacts(index, body, "drishti_contact", target,
                            (T0, T0 + 3 * 365), CONVENTION, refine=False)
    hits = [c for c in result.values if c.aspect_deg == aspect]
    assert hits, f"{oracle}: no {aspect}° contact"
    assert all(c.level_deg == pytest.approx((target - aspect) % 360.0) for c in hits)
    assert any(abs(c.jd - (T0 + body_lon / SWEEP_RATE)) < TIME_TOL_DAYS for c in hits)
    mirrored = T0 + ((target + aspect) % 360.0) / SWEEP_RATE
    assert not any(abs(c.jd - mirrored) < TIME_TOL_DAYS for c in hits), oracle


def test_nodes_have_no_drishti_contacts() -> None:
    index = index_over(3 * 365, sweep, "Rahu")
    result = solve_contacts(index, "Rahu", "drishti_contact", 0.0,
                            (T0, T0 + 3 * 365), CONVENTION, refine=False)
    assert result.available and result.values == ()


def test_orx1_occurrence_ordinals_under_one_physical_object() -> None:
    """Mars | conjunction | point:198.52 crossed direct, retrograde, direct;
    extending the partition appends ordinals and never renumbers."""
    short = index_over(150, looping, "Mars")
    first = solve_contacts(short, "Mars", "conjunction", 198.52, (T0, T0 + 150),
                           CONVENTION, refine=False).values
    assert len(first) == 3
    assert [c.direction for c in first] == [1, -1, 1]
    assert [c.ordinal for c in first] == [1, 2, 3]
    assert len({c.physical_object for c in first}) == 1
    assert [contact_identity_bytes(_as_contact(c)) for c in first] == [
        f"mars|conjunction|point:198.52|c0|{n}" for n in (1, 2, 3)]
    extended = solve_contacts(index_over(300, looping, "Mars"), "Mars", "conjunction", 198.52,
                              (T0, T0 + 300), CONVENTION, refine=False).values
    assert len(extended) > 3
    assert [c.event_id for c in extended[:3]] == [c.event_id for c in first]
    assert extended[3].ordinal == 4


def _as_contact(c):
    from services.gochara_kernel.substrate import SubstrateContact
    contact = SubstrateContact(c.physical_object, c.ordinal, None)
    assert contact.contact_id == c.event_id
    return contact


def test_each_drishti_angle_is_its_own_physical_relation() -> None:
    index = index_over(3 * 365, sweep, "Mars")
    result = solve_contacts(index, "Mars", "drishti_contact", 0.0,
                            (T0, T0 + 3 * 365), CONVENTION, refine=False)
    by_angle = {c.aspect_deg: c.physical_object for c in result.values}
    assert len(set(by_angle.values())) == len(by_angle) == 3


def test_station_root_always_receives_swiss_refinement(monkeypatch) -> None:
    index = index_over(300, looping, "Mars")
    assert index.stations
    refined: list[float] = []

    def refine(body, jd_spline, _path, **_kw):
        refined.append(jd_spline)
        return knots.StationFix(jd_spline + 0.003, 200.0, 1e-6)

    monkeypatch.setattr(knots, "refine_station", refine)
    result = stations(index, "Mars", (T0, T0 + 300), CONVENTION)
    assert refined == list(index.stations)
    assert len(result.values) == len(index.stations)
    for station, spline_jd in zip(result.values, index.stations):
        assert station.solver_method == STATION_METHOD
        assert station.spline_jd == spline_jd
        assert station.jd == pytest.approx(spline_jd + 0.003, abs=1e-6)     # the refined fix
        assert station.jd != station.spline_jd                              # never the bracket
        assert station.delta_t_days == knots.station_delta_t_bound_days("Mars")


def test_missing_backend_data_is_unavailable_not_substituted(monkeypatch) -> None:
    index = index_over(150, looping, "Mars")
    monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", lambda body, jd, path: (0.0, 4))
    result = solve_contacts(index, "Mars", "conjunction", 198.52, (T0, T0 + 150), CONVENTION)
    assert result.values == ()
    assert result.null_reason is NullReason.INFORMATION_UNAVAILABLE

    def no_files(body, jd_spline, _path, **_kw):
        raise knots.EphemerisBackendError(body, 4)

    monkeypatch.setattr(knots, "refine_station", no_files)
    assert stations(index, "Mars", (T0, T0 + 150), CONVENTION).null_reason \
        is NullReason.INFORMATION_UNAVAILABLE


def test_one_solver_imported_in_place() -> None:
    from services.kala_core.sky import contacts as sky_contacts
    assert sky_contacts.find_roots is kernel_contacts.find_roots
    with pytest.raises(ValueError, match="not a contact relation"):
        solve_contacts(index_over(10, sweep, "Mars"), "Mars", "sign_ingress", 0.0,
                       (T0, T0 + 10), CONVENTION)
