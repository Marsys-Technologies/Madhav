"""Codex round 2, blocker 3(a) (steward MB-CODEX-2): `station_at` of a station_seam is the instant the STORED station row carries (`t_exact`, the ephemeris-refined
instant of `SkyEventStore.build_boundary_substrate`), never the arc index's own spline extremum (13.09 s apart for Mercury, February 2026). Real ephemeris, no database
(the substrate's own FakeConn captures the rows it would insert)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel.knots import refine_station
from services.gochara_kernel.substrate import jd_to_utc, production_arc_index

from .conftest import EPHE_PATH, requires_swieph
from .test_station_refine import _stored_rows

pytestmark = requires_swieph
UTC = timezone.utc


@pytest.mark.parametrize("body", ["Mercury", "Mars"])
def test_the_sinks_station_instants_equal_the_stored_station_rows_t_exact_for_every_station_of_a_real_span(body):
    _idx, _counts, stations, _objects = _stored_rows(body)               # the rows the substrate would store for 1998-2012: ev[6] is t_exact
    assert len(stations) > 10
    for ev in stations:
        t_exact = ev[6]
        got = writer_mod._station_instants_in(body.lower(), t_exact - timedelta(days=1), t_exact + timedelta(days=1), EPHE_PATH)
        assert got == [t_exact.isoformat()], f"{body}: the sink's station_at must equal the stored t_exact {t_exact.isoformat()}, got {got}"


def test_mercury_february_2026_is_the_stored_instant_not_the_spline_extremum():
    t0, t1 = datetime(2026, 2, 25, tzinfo=UTC), datetime(2026, 2, 28, tzinfo=UTC)
    (got,) = writer_mod._station_instants_in("mercury", t0, t1, EPHE_PATH)
    idx = production_arc_index("Mercury", EPHE_PATH)
    (jd,) = [j for j in idx.stations if t0 <= jd_to_utc(j) < t1]
    stored = jd_to_utc(refine_station("Mercury", jd, EPHE_PATH).jd)         # the very expression the substrate stores
    spline = jd_to_utc(jd)
    assert got == stored.isoformat() == "2026-02-26T06:47:30.707813+00:00"
    assert abs((stored - spline).total_seconds()) > 10 and got != spline.isoformat(), "the old value (the spline extremum) was 13.09 s away"


def test_a_station_whose_spline_instant_is_inside_the_window_but_whose_stored_instant_is_outside_is_not_inside():
    """Membership is decided on the STORED instant, the one B checks against `full_interval`: a window ending between the two instants excludes the station."""
    t0 = datetime(2026, 2, 25, tzinfo=UTC)
    stored = datetime.fromisoformat(writer_mod._station_instants_in("mercury", t0, t0 + timedelta(days=3), EPHE_PATH)[0])
    assert writer_mod._station_instants_in("mercury", t0, stored, EPHE_PATH) == []                       # half-open: the stored instant itself is outside [t0, stored)
    assert writer_mod._station_instants_in("mercury", t0, stored + timedelta(microseconds=1), EPHE_PATH) == [stored.isoformat()]
