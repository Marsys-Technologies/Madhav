"""SR-MUDDA-HORIZON -- the legacy PERMISSION path read mudda past its table end as `inactive`, silently (DASH_READBACK §3: mudda L1 ends
2032-02-05 on every ayanamsha, ~60 % of the century lies past it). A dasha table is finite; at an instant at or after the last end of every
row a system holds, NOTHING WAS MEASURED, and "inactive" ("checked, did not fire") would assert a measured negative for an unmeasured span.
CLAUDE.md §N.7.6 (an honest null beats an invented judgment) and §N.8 (a signal needs a detector that can read false) govern: the system
reads `unavailable` with reason `dasha_horizon_exhausted` and the table end it ran out at. Today's permission VALUE does not move
(inactive and unavailable both add 0, DR-14 is silent on the denominator -- the same stance as the no-rows case).

Doctrine: a daśā period is the half-open interval [start, end) (GOCHARA_DESIGN_SPECS_v1_4 §4.0, the daśā read contract), so t == end is
already past the table. Fixture dates only -- synthetic periods that end at E; no chart value is read.
Each test carries ONE planted reversion in production code that fails it (recorded in the job's revert proofs)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import swisseph as swe

from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity import permission as perm

E = datetime(2032, 2, 5, tzinfo=timezone.utc)            # the fixture table end (the mudda L1 end the ruling names)
REASON = "dasha_horizon_exhausted"


def iso(dt):
    return dt.isoformat()


def row(system="mudda", lord="Mars", start=E - timedelta(days=3650), end=E, level=1):
    return {"system_id": system, "level_n": level, "lord_graha": lord, "start_iso": iso(start), "end_iso": iso(end)}


def _paths():
    from services.gochara_v3.engine import _dasha_contributions_from_context
    return [
        pytest.param(lambda rows, t, grahas: perm._dasha_contributions(rows, t, grahas, set()), id="gochara_intensity.permission"),
        pytest.param(lambda rows, t, grahas: _dasha_contributions_from_context(
            SimpleNamespace(dasha_periods=tuple(rows), relevant_grahas=frozenset(grahas), relevant_signs=frozenset()), t),
            id="gochara_v3.engine"),
    ]


@pytest.mark.parametrize("contributions", _paths())
def test_before_the_table_end_the_real_state_is_read_and_from_it_on_the_named_blank(contributions):
    """The oracle on BOTH sides of the end: t < E reads its measured state (active, or a checked negative); t >= E -- including
    t == E (half-open) and fifty years on -- reads unavailable with the reason and the table end, never `inactive`."""
    rows = [row()]
    just_before = contributions(rows, iso(E - timedelta(seconds=1)), {"Mars"})["mudda"]
    assert just_before["active"] is True and just_before.get("state", "active") == "active"
    # a covering row whose lord misses is a CHECKED negative: still inactive, never the blank
    miss = contributions(rows, iso(E - timedelta(days=30)), {"Venus"})["mudda"]
    assert miss["active"] is False and miss.get("state", "inactive") == "inactive" and "reason" not in miss["detail"]
    for after in (E, E + timedelta(days=1), E + timedelta(days=365 * 50)):
        got = contributions(rows, iso(after), {"Mars"})["mudda"]
        assert got["active"] is False and got["state"] == "unavailable", after
        assert got["detail"]["reason"] == REASON and got["detail"]["table_end_iso"] == iso(E)
        assert got["detail"]["levels"] == [1]


@pytest.mark.parametrize("contributions", _paths())
def test_a_gap_inside_the_table_is_still_a_measured_negative_not_a_horizon(contributions):
    """t < E with no covering row (a gap between two rows) is not past the table: it keeps reading inactive."""
    rows = [row(start=E - timedelta(days=3650), end=E - timedelta(days=2000)), row(start=E - timedelta(days=1000), end=E)]
    gap = contributions(rows, iso(E - timedelta(days=1500)), {"Mars"})["mudda"]
    assert gap["active"] is False and gap.get("state", "inactive") == "inactive" and "reason" not in gap["detail"]


@pytest.mark.parametrize("contributions", _paths())
def test_each_system_runs_out_at_its_own_end_and_the_others_are_untouched(contributions):
    rows = [row("mudda"), row("narayana", end=E + timedelta(days=3650), start=E - timedelta(days=3650))]
    t = iso(E + timedelta(days=100))
    out = contributions(rows, t, {"Mars"})
    assert out["mudda"]["detail"]["reason"] == REASON
    assert out["narayana"]["active"] is True            # its table runs on: untouched


def test_a_system_with_no_rows_keeps_its_own_unavailable_reason():
    """The no-rows case is a different honest statement (nothing stored) and keeps its reason; it is not renamed a horizon."""
    out = perm._dasha_contributions([row()], iso(E + timedelta(days=10)), {"Mars"}, set())
    assert out["yogini"]["state"] == "unavailable" and out["yogini"]["detail"]["reason"] == perm.REASON_NO_READABLE_ROWS
    assert out["mudda"]["detail"]["reason"] == REASON


def test_compute_permission_counts_the_exhausted_systems_marks_partial_and_moves_no_value():
    rows = [row(s) for s in perm.DASHA_SYSTEM_IDS]

    def run(t):
        jd = swe.julday(t.year, t.month, t.day, 12.0)
        return perm.compute_permission(swe, None, "c", "career", [], jd, dasha_periods=rows)
    value_in, detail_in = run(E - timedelta(days=100))
    value_out, detail_out = run(E + timedelta(days=100))
    assert detail_in["dasha_horizon_exhausted"] == []
    assert {e["system_id"] for e in detail_out["dasha_horizon_exhausted"]} == set(perm.DASHA_SYSTEM_IDS)
    assert {e["table_end_iso"] for e in detail_out["dasha_horizon_exhausted"]} == {iso(E)}
    assert detail_out["permission_partial"] is True
    assert {u["system_id"]: u["reason"] for u in detail_out["systems_unavailable"]} == {s: REASON for s in perm.DASHA_SYSTEM_IDS}
    # the exhausted systems add 0, exactly as the silent `inactive` always did: the value is the active weight over the unchanged denominator
    assert all(not x["active"] for x in detail_out["systems"] if x["system_id"] in perm.DASHA_SYSTEM_IDS)
    assert value_out == pytest.approx(
        sum(x["weight"] for x in detail_out["systems"] if x["active"]) / sum(perm.SYSTEM_WEIGHTS.values()))
    assert value_out <= value_in


def test_the_per_run_count_names_the_candidates_past_the_table_end():
    """The K9 per-run receipt: of the candidates a class evaluated, how many read a system `dasha_horizon_exhausted`, per system."""
    from services.w2g.materialize import horizon_exhausted_note, materialize_event_class
    from services.w2g.solver import InMemoryArcSource
    from tests.test_w2g_materialize import JD0, _direct_arcs, _target, _FakeIntensityResult

    source = InMemoryArcSource({"Saturn": _direct_arcs("Saturn", 400, 1.0, lon0=0.0)})
    table_end = datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=175)       # candidates fall at +100 and +250 days
    periods = [row(start=table_end - timedelta(days=3650), end=table_end)]

    def scorer(swe_, conn, chart_id, event_class, t_jd, **kwargs):
        _v, detail = perm.compute_permission(swe_, None, chart_id, event_class, [], t_jd, dasha_periods=kwargs["dasha_periods"])
        return _FakeIntensityResult(raw_lambda=0.0, signed_lambda=0.0, valence="gain", is_adverse=False,
                                    permission_detail=detail, suppression_detail={"suppressed": False})
    result = materialize_event_class(
        swe, conn=None, chart_id="c1", event_class="marriage", arc_source=source,
        horizon_start_jd=JD0, horizon_end_jd=JD0 + 399, bodies=["Saturn"],
        fetch_resonance_targets=lambda *a, **k: [_target("Saturn", 100.0), _target("Venus", 250.0)],
        fetch_dasha_periods=lambda *a, **k: periods, compute_lambda_e_fn=scorer,
        fetch_temporal_shape_fn=lambda *a, **k: "point",
    )
    assert result.contacts_evaluated == 2
    assert result.dasha_horizon_exhausted == {"reason": REASON, "candidates_exhausted": 1, "by_system": {"mudda": 1}}
    assert horizon_exhausted_note(result) == (
        f"; {REASON}=1 of 2 candidates (systems named blank past their table end: mudda:1)")
