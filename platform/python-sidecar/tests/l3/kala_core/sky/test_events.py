"""KA-1e boundary events: half-open partitions, occurrence order across a
station, and one canonical identity per physical event."""
from __future__ import annotations

import math

import pytest

from services.gochara_kernel.arcs import build_arc_index
from services.gochara_kernel.substrate import IdentityCollisionError
from services.kala_core.sky import boundary_events, event_object, merge_events
from services.kala_core.vocab import GrahaId

T0 = 2460000.0
CONVENTION = "sha256:test-convention"
TIGHT_ARCSEC = 1e-7     # synthetic curves: the spline root is the exact root


def looping(jd: float) -> float:
    """Slow drift with retrograde loops: 30° is crossed direct, retro, direct."""
    t = jd - T0
    return 25.0 + 0.05 * t + 6.0 * math.sin(2.0 * math.pi * t / 120.0)


def index_over(days: int, curve=looping, body: str = "Sun"):
    jds = [T0 + k for k in range(days + 1)]
    return build_arc_index(body, jds, [curve(j) % 360.0 for j in jds],
                            tolerance_arcsec=TIGHT_ARCSEC)


def signs(index, horizon, body="Sun"):
    result = boundary_events(index, body, ["sign_ingress"], horizon, CONVENTION, refine=False)
    assert result.available
    return result.values


def test_occurrence_order_across_a_station() -> None:
    index = index_over(400)
    events = [e for e in signs(index, (T0, T0 + 400)) if e.level_deg == 30.0]
    assert len(events) >= 3
    assert [e.ordinal for e in events] == list(range(1, len(events) + 1))
    assert [e.jd for e in events] == sorted(e.jd for e in events)
    directions = [e.direction for e in events]
    assert directions[:3] == [1, -1, 1]
    assert all(a != b for a, b in zip(directions, directions[1:]))
    # Half-open cells: a direct crossing of 30° enters Taurus (1), a retrograde
    # one re-enters Aries (0).
    assert [e.cell_after for e in events[:3]] == [1, 0, 1]
    assert len({e.physical_object for e in events}) == 1


def test_partition_edge_event_belongs_to_one_partition_with_its_identity() -> None:
    index = index_over(400)
    full = signs(index, (T0, T0 + 400))
    edge = full[1]
    left = signs(index, (T0, edge.jd))
    right = signs(index, (edge.jd, T0 + 400))
    assert edge.event_id not in {e.event_id for e in left}
    assert edge.event_id in {e.event_id for e in right}
    assert [e.event_id for e in left + right] == [e.event_id for e in full]
    assert next(e for e in right if e.event_id == edge.event_id).ordinal == edge.ordinal


def test_seam_and_body_spellings_name_one_physical_object() -> None:
    a = event_object("Sun", "sign_ingress", 0.0, CONVENTION)
    assert a == event_object(GrahaId.SUN, "sign_ingress", 360.0, CONVENTION)
    assert a == event_object("sun", "sign_ingress", 0.0, CONVENTION)
    assert a.identity_bytes == f"sun|sign_ingress|point:0.0|{CONVENTION}"
    assert a != event_object("Sun", "sign_ingress", 0.0, "sha256:other")
    with pytest.raises(ValueError, match="mean-node"):
        event_object(GrahaId.RAHU_TRUE, "sign_ingress", 0.0, CONVENTION)


def test_same_event_through_two_source_paths_has_one_identity() -> None:
    index = index_over(400)
    by_kernel_name = signs(index, (T0, T0 + 400), body="Sun")
    by_vocab_id = signs(index, (T0, T0 + 400), body=GrahaId.SUN)
    assert [e.event_id for e in by_kernel_name] == [e.event_id for e in by_vocab_id]
    merged = merge_events(by_kernel_name, by_vocab_id)
    assert len(merged) == len(by_kernel_name)
    assert len({e.event_id for e in merged}) == len(merged)


def test_one_id_at_two_instants_is_a_collision() -> None:
    index = index_over(400)
    events = signs(index, (T0, T0 + 400))
    from dataclasses import replace
    moved = replace(events[0], jd=events[0].jd + 2.0)
    with pytest.raises(IdentityCollisionError):
        merge_events(events, [moved])


def test_seam_crossing_and_all_three_grids() -> None:
    index = index_over(60, curve=lambda jd: 355.0 + 0.5 * (jd - T0))
    result = boundary_events(index, "Sun", ["sign_ingress", "nakshatra_ingress",
                                            "kakshya_cell_crossing"],
                             (T0, T0 + 60), CONVENTION, refine=False)
    seam = [e for e in result.values if e.level_deg == 0.0]
    assert sorted(e.relation for e in seam) == [
        "kakshya_cell_crossing", "nakshatra_ingress", "sign_ingress"]
    assert all(e.cell_after == 0 for e in seam)
    assert result.coverage.complete and result.coverage.backend == "arc_spline_unrefined"
