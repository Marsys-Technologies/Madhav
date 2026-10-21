"""SR-W56-S3 — the settled build's Tājika mudda years overlap their successor by minutes (K9 r5 finding N7). L1 is NOT changed and no
boundary is invented (B.1 / §N.5): the dasha readers treat an overlap as a NAMED L1 defect ONLY when it is the same chart, the same
mudda level, CONSECUTIVE years and 0 < overlap <= 86,400 s. Inside that interval the mudda lord is UNRESOLVED and every dependent value
is blank with reason `l1_mudda_boundary_overlap`; anything else still raises `DashaReadConflict`.

Doctrine for the oracles: a Tājika varṣa runs from one varṣa-praveśa (solar return) to the next, so consecutive years are contiguous by
definition (Tājikanīlakaṇṭhī, varṣaphala; the K9 r5 report's classical basis for N7). A stored overlap therefore contradicts its own
rule — and a sub-day one is a rounding-scale boundary defect, not a different year. The rule itself is the surrogate ruling SR-W56-S3.
Each test below has ONE planted reversion in the production code that fails it (recorded in the job's revert proofs)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from services.gochara_grammar import dasha_data as DD
from services.gochara_kernel import dasha_read, seal_brief

CHART = "00000000-0000-4000-8000-00000000c0de"          # synthetic — not the native's chart
OTHER_CHART = "00000000-0000-4000-8000-00000000c0df"
BUILD = "11111111-1111-4111-8111-111111111111"
Y0 = datetime(2001, 3, 1, tzinfo=timezone.utc)           # synthetic instants, not any chart value
YEAR = timedelta(days=365)


def year(i, *, overlap=timedelta(0), system="mudda", level=1, chart=CHART, lord=None, parent=None):
    """The i-th consecutive varṣa: it ends `overlap` AFTER the next one begins."""
    start = Y0 + i * YEAR
    return {"dasha_row_id": f"{system}-{level}-{i}", "chart_id": chart, "system_id": system, "level_n": level,
            "parent_row_id": parent, "lord_graha": lord or ("Sun", "Moon", "Mars", "Mercury", "Jupiter")[i % 5],
            "start_iso": start, "end_iso": start + YEAR + overlap, "build_id": BUILD,
            "verification_pass_status": DD.READ_CONTRACT_TIER}


def iso(dt):
    return dt.isoformat()


def covering(rows, dt):
    return [r["lord_graha"] for r in rows if DD.period_contains(r, iso(dt))]


# ── (a) a 10-minute consecutive overlap: blank ONLY inside the interval, resolved outside ──────────────────────────────

def test_ten_minute_consecutive_overlap_is_blank_only_inside_the_interval():
    rows = DD.canonicalize_multilevel_rows([year(0, overlap=timedelta(minutes=10), lord="Sun"), year(1, lord="Moon")])
    seam = Y0 + YEAR                                       # year 1 starts here; year 0's stored end is 10 min later
    inside = seam + timedelta(minutes=5)
    # inside: neither year claims the instant, and the overlap is named with its reason and length
    assert covering(rows, inside) == []
    named = DD.unresolved_mudda_overlap_at(rows, iso(inside))
    assert named["reason"] == "l1_mudda_boundary_overlap" and named["seconds"] == 600
    # the interval is half-open [seam, seam+10min): its first instant is blank, its end instant is year 1's
    assert DD.unresolved_mudda_overlap_at(rows, iso(seam)) is not None and covering(rows, seam) == []
    assert DD.unresolved_mudda_overlap_at(rows, iso(seam + timedelta(minutes=10))) is None
    assert covering(rows, seam + timedelta(minutes=10)) == ["Moon"]
    # outside: both years resolve exactly as before, with no overlap named
    before, after = seam - timedelta(seconds=1), seam + timedelta(minutes=11)
    assert covering(rows, before) == ["Sun"] and DD.unresolved_mudda_overlap_at(rows, iso(before)) is None
    assert covering(rows, after) == ["Moon"] and DD.unresolved_mudda_overlap_at(rows, iso(after)) is None


def test_the_stored_bounds_stay_on_the_row_for_audit_and_the_census_counts_each_overlap_once():
    rows = DD.canonicalize_multilevel_rows([year(0, overlap=timedelta(minutes=10)), year(1, overlap=timedelta(minutes=3)), year(2)])
    first = next(r for r in rows if r["dasha_row_id"] == "mudda-1-0")
    assert first["end_iso_stored"] == Y0 + YEAR + timedelta(minutes=10)
    census = DD.mudda_overlap_census(rows)
    assert census == {"reason": "l1_mudda_boundary_overlap", "overlaps_named": 2, "overlap_seconds_total": 780}


# ── (b) a 2-day overlap raises ──────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("order", [(0, 1), (1, 0)])
def test_a_two_day_consecutive_overlap_still_raises(order):
    rows = [year(0, overlap=timedelta(days=2)), year(1)]
    with pytest.raises(DD.DashaReadConflict, match="overlap"):
        DD.canonicalize_multilevel_rows([rows[i] for i in order])


def test_the_limit_is_exactly_one_day():
    named = DD.canonicalize_multilevel_rows([year(0, overlap=timedelta(seconds=86_400)), year(1)])
    assert DD.mudda_overlap_census(named)["overlap_seconds_total"] == 86_400
    with pytest.raises(DD.DashaReadConflict):
        DD.canonicalize_multilevel_rows([year(0, overlap=timedelta(seconds=86_401)), year(1)])


def test_a_touching_boundary_is_not_an_overlap_at_all():
    rows = DD.canonicalize_multilevel_rows([year(0), year(1)])
    assert DD.mudda_overlap_census(rows)["overlaps_named"] == 0 and all(DD.MUDDA_OVERLAP_KEY not in r for r in rows)


# ── (c) a non-consecutive overlap raises ────────────────────────────────────────────────────────────────────────────────

def test_a_year_overlapping_a_non_adjacent_year_raises():
    """Each adjacent pair overlaps by minutes (10 and 13), but year 0 ALSO reaches year 2 (8 minutes): that is no seam between
    consecutive years, so it is the conflict it always was."""
    y0 = year(0, lord="Sun")
    y1 = dict(year(1, lord="Moon"), start_iso=y0["end_iso"] - timedelta(minutes=10), end_iso=y0["end_iso"] + timedelta(minutes=5))
    y2 = dict(year(2, lord="Mars"), start_iso=y0["end_iso"] - timedelta(minutes=8))
    with pytest.raises(DD.DashaReadConflict):
        DD.canonicalize_multilevel_rows([y0, y1, y2])


# ── every other dimension of the rule: still the conflict it always was ─────────────────────────────────────────────────

@pytest.mark.parametrize("a, b", [
    pytest.param(year(0, overlap=timedelta(minutes=10), system="yogini"), year(1, system="yogini"), id="other-system"),
    pytest.param(year(0, overlap=timedelta(minutes=10), level=2, parent="p"), year(1, level=2, parent="p"), id="other-level"),
    pytest.param(year(0, overlap=timedelta(minutes=10)), year(1, chart=OTHER_CHART), id="other-chart"),
])
def test_the_exception_is_only_for_the_same_chart_the_mudda_system_and_its_year_level(a, b):
    with pytest.raises(DD.DashaReadConflict):
        DD.canonicalize_multilevel_rows([a, b])


def test_a_year_nested_inside_its_predecessor_raises():
    outer = year(0, lord="Sun")
    inner = dict(year(1, lord="Moon"), start_iso=outer["end_iso"] - timedelta(hours=2), end_iso=outer["end_iso"] - timedelta(hours=1))
    with pytest.raises(DD.DashaReadConflict):
        DD.canonicalize_multilevel_rows([outer, inner])


# ── the shared read path: what ka_gochara (and everything on the governed reader) goes through ──────────────────────────

class _Conn:
    """Serves chart_dashas rows in the SELECT's column order (`DD._MULTILEVEL_KEYS`)."""
    def __init__(self, rows):
        self.rows = [[r[k] for k in DD._MULTILEVEL_KEYS] for r in rows]

    def execute(self, sql, params):
        rows = self.rows

        class _Cur:
            def fetchall(self_inner):
                return rows
        return _Cur()


def test_the_governed_row_reader_names_a_ten_minute_overlap_and_still_raises_on_two_days():
    ok = dasha_read._fetch_dasha_periods_multilevel(
        _Conn([year(0, overlap=timedelta(minutes=10)), year(1), year(2)]), CHART, systems=["mudda"], levels=(1,), level_tier_policy=True)
    assert DD.mudda_overlap_census(ok)["overlaps_named"] == 1
    with pytest.raises(DD.DashaReadConflict):
        dasha_read._fetch_dasha_periods_multilevel(
            _Conn([year(0, overlap=timedelta(days=2)), year(1)]), CHART, systems=["mudda"], levels=(1,), level_tier_policy=True)


def test_ka_sangam_and_ka_vighnakara_read_dashas_by_projection_so_they_never_met_the_conflict():
    """Their readers (`execute_governed_dasha_query`, `load_dasha_timeline`) return stored rows and never call the canonicalizer;
    N7 reached them only because ka_gochara failed upstream. Pinned so a future canonicalizing reader there is a visible change."""
    import inspect
    from pipeline.orchestrator.writers import ka_sangam, ka_vighnakara
    from services.ka_temporal import date_resolver
    for module in (ka_sangam, ka_vighnakara, date_resolver):
        assert "canonicalize_multilevel_rows" not in inspect.getsource(module)


# ── every dependent value is blank, with the reason ─────────────────────────────────────────────────────────────────────

def _periods(overlap):
    rows = DD.canonicalize_multilevel_rows([year(0, overlap=overlap, lord="Sun"), year(1, lord="Moon")])
    for r in rows:
        r["start_iso"], r["end_iso"] = iso(r["start_iso"]), iso(r["end_iso"])
        for i in r.get(DD.MUDDA_OVERLAP_KEY, ()):
            i["start_iso"], i["end_iso"] = iso(i["start_iso"]), iso(i["end_iso"])
    return rows


def _permission_paths():
    from services.gochara_intensity.permission import _dasha_contributions
    from services.gochara_v3.engine import _dasha_contributions_from_context
    return [
        pytest.param(lambda rows, t, grahas: _dasha_contributions(rows, t, grahas, set()), id="gochara_intensity.permission"),
        pytest.param(lambda rows, t, grahas: _dasha_contributions_from_context(
            SimpleNamespace(dasha_periods=tuple(rows), relevant_grahas=frozenset(grahas), relevant_signs=frozenset()), t), id="gochara_v3.engine"),
    ]


@pytest.mark.parametrize("contributions", _permission_paths())
def test_inside_the_overlap_the_mudda_vote_is_unavailable_with_the_reason_and_outside_it_is_unchanged(contributions):
    rows = _periods(timedelta(minutes=10))
    seam = Y0 + YEAR
    inside = contributions(rows, iso(seam + timedelta(minutes=5)), {"Moon", "Sun"})["mudda"]
    assert inside["active"] is False and inside["state"] == "unavailable"
    assert inside["detail"]["reason"] == "l1_mudda_boundary_overlap" and inside["detail"]["overlap_seconds"] == 600
    after = contributions(rows, iso(seam + timedelta(minutes=11)), {"Moon", "Sun"})["mudda"]
    assert after["active"] is True and after["detail"]["lord_graha"] == "Moon"
    before = contributions(rows, iso(seam - timedelta(minutes=1)), {"Moon", "Sun"})["mudda"]
    assert before["active"] is True and before["detail"]["lord_graha"] == "Sun"
    # a checked negative stays a checked negative: outside the overlap a non-matching lord is `inactive`, not blank
    other = contributions(rows, iso(seam + timedelta(days=30)), {"Mars"})["mudda"]
    assert other["active"] is False and other.get("state", "inactive") == "inactive" and "reason" not in other["detail"]


def test_the_class_context_document_keeps_the_named_overlap_through_its_json_round_trip():
    import json
    from scripts.kala_gochara_cutover.step06a_class_context import _jsonable_period
    rows = [json.loads(json.dumps(_jsonable_period(r))) for r in _periods(timedelta(minutes=10))]
    named = DD.unresolved_mudda_overlap_at(rows, iso(Y0 + YEAR + timedelta(minutes=5)))
    assert named is not None and named["reason"] == "l1_mudda_boundary_overlap"


# ── the count: seal brief and K9 receipt ────────────────────────────────────────────────────────────────────────────────

class _Savepointed:
    def transaction(self):
        import contextlib
        return contextlib.nullcontext()


def test_the_disclosure_counts_the_overlaps_of_the_governed_read(monkeypatch):
    rows = DD.canonicalize_multilevel_rows([year(i, overlap=timedelta(minutes=i + 1) if i < 3 else timedelta(0)) for i in range(5)])
    seen = {}

    def governed(conn, chart_id, **kw):
        seen.update(kw)
        return rows
    monkeypatch.setattr(dasha_read, "load_governed_dasha_periods", governed)
    found = dasha_read.mudda_overlap_disclosure(_Savepointed(), CHART)
    assert found == {"status": "counted", "reason": "l1_mudda_boundary_overlap", "overlaps_named": 3, "overlap_seconds_total": 6 * 60}
    assert seen["systems"] == ["mudda"] and seen["levels"] == (1,)


def test_an_unreadable_chart_is_a_typed_null_never_a_zero(monkeypatch):
    def refuse(*a, **k):
        raise dasha_read.DashaBuildRefused("chart_not_settled", "no settlement entry")
    monkeypatch.setattr(dasha_read, "load_governed_dasha_periods", refuse)
    assert dasha_read.mudda_overlap_disclosure(_Savepointed(), CHART) == {"status": "not_readable", "reason": "chart_not_settled"}


def test_the_seal_brief_carries_the_count_only_when_there_is_something_to_disclose(monkeypatch):
    counted = {"status": "counted", "reason": "l1_mudda_boundary_overlap", "overlaps_named": 38, "overlap_seconds_total": 4560}
    monkeypatch.setattr(dasha_read, "mudda_overlap_disclosure", lambda conn, chart: counted)
    assert seal_brief._mudda_overlap_entry(None, CHART) == {"mudda_boundary_overlap": counted}
    monkeypatch.setattr(dasha_read, "mudda_overlap_disclosure", lambda conn, chart: dict(counted, overlaps_named=0, overlap_seconds_total=0))
    assert seal_brief._mudda_overlap_entry(None, CHART) == {}          # byte-identical to every brief before this field existed
    unreadable = {"status": "not_readable", "reason": "chart_not_settled"}
    monkeypatch.setattr(dasha_read, "mudda_overlap_disclosure", lambda conn, chart: unreadable)
    assert seal_brief._mudda_overlap_entry(None, CHART) == {"mudda_boundary_overlap": unreadable}
