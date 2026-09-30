"""A5.4 per_instant_permission — proof battery for the T0-6 repair of
step06b's PERMISSION factor.

Sealed doctrine FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0, findings #2/#3
(T0-6): the plurality evaluation (DR-14) is inherently time-varying, but the
pre-repair wiring collapsed it to one static per-class constant (union over
the class's candidate t_exact instants) and served that constant at every
instant of every window. The repair evaluates
gochara_intensity.permission.compute_permission AT EACH PROJECTION INSTANT
over multi-level (MD/AD/PD) dasha rows carried by the class-context
document, memoized per class × UTC day, with the N-15 sade-sāti weight
stripped (testimony renormalization). Old documents / rehearsal keep the
pinned static fallback.

Every test here is pure arithmetic or stub-conn SQL plumbing — no Swiss
calls, no real DB. Each test would FAIL against the pre-repair shape (the
static-constant mutation is made explicit in
test_lambda_varies_with_instant_permission_mutation).
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .test_step06b_windows_projection import (  # noqa: E402
    WRITER_PATH, _ctx, _open_gates)
from .test_step06b_angular_m1 import _contact  # noqa: E402

UTC = timezone.utc


def _pos_fn(t_exact_jd, speed=0.5):
    """Linear motion anchored ON the contact target (100°) at t_exact, so
    the angular kernel is at its peak there. 0.5°/day puts the 5° orb
    crossings exactly on the ±10-day span edges."""
    return lambda body, jd: (100.0 + speed * (jd - t_exact_jd)) % 360.0


def _load_writer():
    spec = importlib.util.spec_from_file_location(
        "step06b_windows_projection_t06", WRITER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


w = _load_writer()

from services.gochara_grammar import dasha_data as DD  # noqa: E402


# ── dasha_data.fetch_dasha_periods_multilevel (§4.0 duplicate rules) ────────


class _StubCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _StubConn:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, _sql, _params):
        return _StubCursor(self._rows)


def _row(rid, lord, start, end, system="vimshottari", level=1,
         parent=None, build="b1", tier="two_pass_verified"):
    return [rid, system, level, parent, lord, start, end, build, tier]


def test_identical_duplicates_collapse_and_record_source_ids():
    conn = _StubConn([
        _row("r1", "Jupiter", "2020-01-01", "2030-01-01"),
        _row("r2", "Jupiter", "2020-01-01", "2030-01-01"),
    ])
    rows = DD.fetch_dasha_periods_multilevel(conn, "chart-x")
    assert len(rows) == 1
    assert sorted(rows[0]["merged_row_ids"]) == ["r1", "r2"]


def test_conflicting_duplicates_raise_never_silently_pick():
    """Mutation check: the pre-§4.0 behaviour (silently keeping the first
    row) would return one row here instead of raising."""
    conn = _StubConn([
        _row("r1", "Jupiter", "2020-01-01", "2030-01-01"),
        _row("r2", "Saturn", "2020-01-01", "2030-01-01"),  # lord differs
    ])
    with pytest.raises(DD.DashaReadConflict):
        DD.fetch_dasha_periods_multilevel(conn, "chart-x")


def test_db_shape_surprise_is_honest_empty_not_crash():
    class _BrokenConn:
        def execute(self, *_a):
            raise RuntimeError("relation chart_dashas does not exist")

    assert DD.fetch_dasha_periods_multilevel(_BrokenConn(), "chart-x") == []


def test_distinct_levels_and_parents_survive():
    conn = _StubConn([
        _row("md1", "Jupiter", "2020-01-01", "2030-01-01", level=1),
        _row("ad1", "Saturn", "2020-01-01", "2021-06-01", level=2,
             parent="md1"),
    ])
    rows = DD.fetch_dasha_periods_multilevel(conn, "chart-x")
    assert {r["dasha_row_id"] for r in rows} == {"md1", "ad1"}
    assert rows[1]["parent_row_id"] == "md1"


# ── N-15 sade-sāti testimony renormalization ─────────────────────────────────


def test_sade_sati_weight_stripped_when_active():
    detail = {"systems": [
        {"system_id": "sade_sati", "weight": 2.0, "active": True},
        {"system_id": "vimshottari", "weight": 1.0, "active": True},
        {"system_id": "narayana", "weight": 1.0, "active": False},
    ]}
    raw = (2.0 + 1.0) / (2.0 + 1.0 + 1.0)  # 0.75 with sade-sāti weighted
    newp, d2 = w._sade_sati_testimony_renormalize(raw, detail)
    assert newp == pytest.approx(1.0 / 2.0)  # 1 active / 2 total, ss removed
    assert d2["sade_sati_testimony"]["active"] is True
    assert (d2["sade_sati_testimony"]
            ["legacy_permission_including_sade_sati"]) == pytest.approx(0.75)


def test_sade_sati_inactive_removed_from_denominator_only():
    detail = {"systems": [
        {"system_id": "sade_sati", "weight": 2.0, "active": False},
        {"system_id": "vimshottari", "weight": 1.0, "active": True},
    ]}
    raw = 1.0 / 3.0
    newp, _ = w._sade_sati_testimony_renormalize(raw, detail)
    assert newp == pytest.approx(1.0)


def test_no_sade_sati_is_identity():
    detail = {"systems": [
        {"system_id": "vimshottari", "weight": 1.0, "active": True}]}
    newp, d2 = w._sade_sati_testimony_renormalize(0.5, detail)
    assert newp == 0.5 and d2 is detail


# ── ClassContext per-instant mode ────────────────────────────────────────────


def test_per_instant_context_carries_no_constant_stand_in():
    fn = lambda t: (0.4, {"systems_active": ["vimshottari"]})  # noqa: E731
    ctx = _ctx()
    ctx_fn = w.ClassContext(
        "marriage", [0.9], {"vimshottari": True},
        weight_by_target_ref={"Venus": 0.9}, permission_fn=fn)
    assert ctx_fn.permission is None
    assert ctx_fn.permission_mode == "per_instant_md_ad_pd"
    rec = ctx_fn.factors_record()
    assert rec["permission"] is None
    assert rec["permission_mode"] == "per_instant_md_ad_pd"
    assert rec["permission_systems_active"] is None
    # static fallback unchanged (pre-repair shape)
    assert ctx.permission_mode == "static_systems_active"
    assert isinstance(ctx.factors_record()["permission"], float)


def test_lambda_varies_with_instant_permission_mutation():
    """THE mutation check: pre-repair, PERMISSION was the per-class constant
    leg.compute_permission(permission_systems) at every instant — lambda at
    two dates would differ ONLY through activity. Here activity is pinned
    identical at both instants (same angular separation) while the instant
    permission differs 0.9 vs 0.1; lambda_raw must differ. Against the
    removed constant this difference vanishes."""
    t_exact = 2460100.0
    contacts = [_contact("c1", t_exact - 10, t_exact, t_exact + 10)]
    pos_fn = _pos_fn(t_exact)

    def fn(t_jd):  # licensed before t_exact, unlicensed after
        p = 0.9 if t_jd < t_exact else 0.1
        return p, {"systems_active": ["vimshottari"] if p > 0.5 else []}

    ctx_static = _ctx()
    ctx_fn = w.ClassContext(
        "marriage", [0.9], {"vimshottari": True},
        weight_by_target_ref={"Venus": 0.9}, permission_fn=fn)
    eval_fn = w.make_eval_fn(ctx_fn, contacts, _open_gates,
                             planet_pos_fn=pos_fn)
    eval_static = w.make_eval_fn(ctx_static, contacts, _open_gates,
                                 planet_pos_fn=pos_fn)
    # symmetric points about t_exact: identical angular separation, hence
    # identical activity under the pinned linear motion
    e_a, e_b = eval_fn(t_exact - 2.0), eval_fn(t_exact + 2.0)
    s_a, s_b = eval_static(t_exact - 2.0), eval_static(t_exact + 2.0)
    assert e_a["activity"] == pytest.approx(e_b["activity"])
    assert e_a["permission"] == pytest.approx(0.9)
    assert e_b["permission"] == pytest.approx(0.1)
    assert e_a["lambda_raw"] > e_b["lambda_raw"]
    # static control: the pre-repair shape — lambda moves only via activity
    assert s_a["permission"] == s_b["permission"]
    assert s_a["lambda_raw"] == pytest.approx(s_b["lambda_raw"])


def test_permission_fn_actually_drives_lambda():
    """Direct form: permission 0.9 vs 0.1 at the SAME instant (activity held
    fixed) must move lambda_raw — proving the evaluator consumes the instant
    value, not a constructor constant."""
    t_exact = 2460100.0
    contacts = [_contact("c1", t_exact - 10, t_exact, t_exact + 10)]
    pos_fn = _pos_fn(t_exact)
    lambdas = {}
    for p in (0.9, 0.1):
        fn = lambda _t, p=p: (p, {"systems_active": ["vimshottari"]})  # noqa: E731
        ctx_fn = w.ClassContext(
            "marriage", [0.9], {"vimshottari": True},
            weight_by_target_ref={"Venus": 0.9}, permission_fn=fn)
        evaluate = w.make_eval_fn(ctx_fn, contacts, _open_gates,
                                  planet_pos_fn=pos_fn)
        lambdas[p] = evaluate(t_exact)["lambda_raw"]
    assert lambdas[0.9] > lambdas[0.1]
    assert lambdas[0.9] - lambdas[0.1] > 0.1


def test_permission_at_static_mode_returns_pinned_constant():
    ctx = _ctx(perms={"vimshottari": True, "narayana": False})
    p, detail = ctx.permission_at(2460100.0)
    assert p == ctx.permission
    assert detail["mode"] == "static_systems_active"
    assert detail["systems_active"] == ["vimshottari"]


# ── step06a document payload ─────────────────────────────────────────────────


def test_jsonable_period_round_trips_datetimes_and_uuids():
    import uuid
    spec = importlib.util.spec_from_file_location(
        "step06a_class_context_t06",
        WRITER_PATH.parent / "step06a_class_context.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    row = {"dasha_row_id": uuid.uuid4(),
           "start_iso": datetime(2020, 1, 1, tzinfo=UTC),
           "end_iso": datetime(2030, 1, 1, tzinfo=UTC),
           "merged_row_ids": [uuid.uuid4(), uuid.uuid4()],
           "level_n": 1, "lord_graha": "Jupiter", "extra_none": None}
    out = mod._jsonable_period(row)
    assert out["start_iso"] == "2020-01-01T00:00:00+00:00"
    assert all(isinstance(x, str) for x in out["merged_row_ids"])
    assert out["level_n"] == 1 and out["extra_none"] is None
    assert isinstance(out["dasha_row_id"], str)


# ── ASTRA_REVIEW_A5_4 P1-2: the FROZEN C5 permission on the executable path ──
#
# GOCHARA_DESIGN_SPECS_v1_4 §4.0/§4.1 with O-PP-2's literal rows (the B5.1
# pinned reference rows in services.gochara_rules.permission, re-shaped as
# the L1 chart_dashas rows step06a emits: dasha_row_id / level_n /
# parent_row_id / lord_graha / start_iso / end_iso / build_id / tier).

import ast  # noqa: E402
import inspect  # noqa: E402

from services.gochara_rules import permission as RP  # noqa: E402
from tests.l3.gochara_rules.conftest import LAGNA_DEG, NATAL  # noqa: E402

CHART = {"lagna_deg": LAGNA_DEG, "natal": dict(NATAL),
         "day_birth": True, "paksha": "Shukla",
         "chart_id": RP.DASHA_READ_CONTRACT["chart_id"]}
BUILD = RP.DASHA_READ_CONTRACT["build_id"]
TIER = RP.DASHA_READ_CONTRACT["tier"]
T1 = datetime(2019, 8, 1, tzinfo=UTC)             # MD Mercury / AD Mars / PD Saturn
T2 = datetime(2021, 1, 1, tzinfo=UTC)             # MD Mercury / AD Rahu / PD Saturn
BOUNDARY = datetime(2020, 2, 14, 11, 47, 23, tzinfo=UTC)  # Mars→Rahu AD, half-open


def _l1_rows(*, build=BUILD, tier=TIER, extra=()):
    rows = []
    for level, src in ((1, RP.MD_ROWS), (2, RP.AD_ROWS), (3, RP.PD_ROWS)):
        for r in src:
            rows.append({"dasha_row_id": r["row_id"], "system_id": "vimshottari",
                         "level_n": level, "parent_row_id": r["parent_row_id"],
                         "lord_graha": r["lord"], "start_iso": r["start_iso"],
                         "end_iso": r["end_iso"], "build_id": build,
                         "verification_pass_status": tier})
    rows.extend(extra)
    return rows


def _c5(rows, t, event_class="marriage", **kw):
    return w.frozen_c5_permission_context(
        rows, w.jd_of(t), event_class, CHART,
        pinned_build_id=kw.pop("pinned_build_id", BUILD),
        tier=kw.pop("tier", TIER))


def test_o_pp_2_per_level_licences_at_t1_and_t2():
    rows = _l1_rows()
    p1 = _c5(rows, T1)["period_context"]
    p2 = _c5(rows, T2)["period_context"]
    assert (p1["md"]["lord"], p1["ad"]["lord"], p1["pd"]["lord"]) == ("Mercury", "Mars", "Saturn")
    assert (p2["md"]["lord"], p2["ad"]["lord"], p2["pd"]["lord"]) == ("Mercury", "Rahu", "Saturn")
    # AD: Mars occupies Libra (7th) ⇒ scored; Rahu ⇒ testimony (node-dispositor
    # chain via Venus, D-PADMIT), never scored
    assert p1["ad"]["licence"] == "scored" and p1["ad"]["relation"] == "occupancy"
    assert p2["ad"]["licence"] == "testimony" and p2["ad"]["relation"] == "dispositorship"
    # PD Saturn occupies the 7th ⇒ scored at both; MD identical at both
    assert p1["pd"]["licence"] == p2["pd"]["licence"] == "scored"
    assert p1["md"]["licence"] == p2["md"]["licence"]
    # row ids are the printed §4.0 / O-PP-2 rows
    assert p1["ad"]["row_id"] == "b1e4d515-6a94-4054-89ff-1ed2487f66ae"
    assert p2["ad"]["row_id"] == "25a4b815-39bb-4b4a-b922-84a71778bb4f"
    assert p1["pd"]["row_id"] == "a4cf46db-fcb5-479c-8aab-ca87bcb551ff"
    assert p2["pd"]["row_id"] == "73eea5c0-631f-4b48-8c8f-483c910c6fde"
    # class-level licence is the SAME at t₁ and t₂ (the AD level is the only
    # level that differs; the PD keeps the class licensed)
    assert _c5(rows, T1)["class_licence"] == _c5(rows, T2)["class_licence"] == "scored"
    assert _c5(rows, T1)["admitted_paths"] == ["P1"]
    # Aṣṭottarī absent with BOTH failed conditions named (O-PP-3)
    app = p1["applicability"]
    assert app["system"] == "ashtottari" and app["state"] == "absent"
    assert len(app["failed_conditions"]) == 2


def test_o_pp_2_boundary_instant_belongs_to_rahu_half_open():
    rows = _l1_rows()
    at_boundary = _c5(rows, BOUNDARY)["period_context"]
    before = _c5(rows, BOUNDARY - timedelta(seconds=1))["period_context"]
    assert at_boundary["ad"]["lord"] == "Rahu"
    assert before["ad"]["lord"] == "Mars"
    assert at_boundary["t_utc"].startswith("2020-02-14T11:47:23")


def test_memoization_is_by_exact_instant_not_date(monkeypatch):
    """The reviewer's mutation: a per-date cache returns the 00:00 (Mars AD)
    licence for the 11:47:23 boundary instant (Rahu). The factory must not
    bucket by date."""
    rows = _l1_rows()
    calls = []

    def fake_compute_permission(swe, conn, chart_id, cls, targets, t_jd, **kw):
        calls.append(t_jd)
        return 0.0, {"systems": [{"system_id": "vimshottari", "weight": 0.16,
                                   "active": False}], "systems_active": []}

    from services.gochara_intensity import permission as perm
    from services.gochara_intensity import enrichment
    from services.gochara_grammar import resonance_map
    monkeypatch.setattr(perm, "compute_permission", fake_compute_permission)
    monkeypatch.setattr(enrichment, "enrich_targets", lambda conn, t: ["target"])
    monkeypatch.setattr(resonance_map, "fetch_resonance_targets", lambda *a: ["target"])
    monkeypatch.setitem(sys.modules, "swisseph", type("swe", (), {})())
    fn = w.make_per_instant_permission_fn(
        None, CHART["chart_id"], "marriage", rows, CHART,
        pinned_build_id=BUILD, tier=TIER)
    day_start = datetime(2020, 2, 14, tzinfo=UTC)
    _, d0 = fn(w.jd_of(day_start))
    _, d1 = fn(w.jd_of(BOUNDARY))
    assert d0["period_context"]["ad"]["lord"] == "Mars"
    assert d1["period_context"]["ad"]["lord"] == "Rahu"
    assert len(calls) == 2  # two instants on one date ⇒ two evaluations
    fn(w.jd_of(BOUNDARY))
    assert len(calls) == 2  # exact-instant memo hit


def test_orphan_pd_is_ignored_never_accepted():
    """A PD row covering t₁ whose parent is NOT the covering AD row (an
    orphan) must be ignored and reported; the reviewer's probe accepted it."""
    orphan = {"dasha_row_id": "orphan-pd", "system_id": "vimshottari",
              "level_n": 3, "parent_row_id": "not-the-mars-ad",
              "lord_graha": "Venus", "start_iso": "2019-06-01T00:00:00Z",
              "end_iso": "2019-09-01T00:00:00Z", "build_id": BUILD,
              "verification_pass_status": TIER}
    ctx = _c5(_l1_rows(extra=[orphan]), T1)["period_context"]
    assert ctx["pd"]["lord"] == "Saturn"
    assert ctx["pd"]["row_id"] == "a4cf46db-fcb5-479c-8aab-ca87bcb551ff"
    assert [o["dasha_row_id"] for o in ctx["orphans_ignored"]] == ["orphan-pd"]
    # an orphan AD (parent not the covering MD) is likewise ignored
    orphan_ad = dict(orphan, dasha_row_id="orphan-ad", level_n=2,
                     parent_row_id="not-the-md", lord_graha="Jupiter")
    ctx2 = _c5(_l1_rows(extra=[orphan_ad]), T1)["period_context"]
    assert ctx2["ad"]["lord"] == "Mars"
    assert "orphan-ad" in [o["dasha_row_id"] for o in ctx2["orphans_ignored"]]


def test_conflicting_rows_for_one_period_identity_raise():
    """Two equally-qualified covering rows at one level under one parent
    that differ on a contract field (lord / end) ⇒ reject both, fail loudly
    — never silently pick one (§4.0). The reviewer's probe retained
    conflicting starts."""
    conflict = {"dasha_row_id": "ad-conflict", "system_id": "vimshottari",
                "level_n": 2, "parent_row_id": "58afa482-4bce-42df-9c0d-0b5a2e02305e",
                "lord_graha": "Jupiter", "start_iso": "2019-02-17T06:50:23Z",
                "end_iso": "2020-02-14T11:47:23Z", "build_id": BUILD,
                "verification_pass_status": TIER}
    with pytest.raises(DD.DashaReadConflict):
        _c5(_l1_rows(extra=[conflict]), T1)
    # identical duplicate (every contract field equal) collapses, ids recorded
    dup = dict(conflict, dasha_row_id="ad-dup", lord_graha="Mars")
    ctx = _c5(_l1_rows(extra=[dup]), T1)["period_context"]
    assert ctx["ad"]["lord"] == "Mars"
    assert set(ctx["ad"]["merged_row_ids"]) == {
        "b1e4d515-6a94-4054-89ff-1ed2487f66ae", "ad-dup"}


def test_pinned_build_and_tier_exclude_other_rows():
    other = _l1_rows(build="00000000-0000-0000-0000-000000000000")
    ctx = _c5(other, T1)
    assert ctx["period_context"]["md"]["lord"] is None
    assert ctx["class_licence"] == "none"
    assert ctx["period_context"]["rows_excluded"]["other_build"] == len(other)
    ctx_t = _c5(_l1_rows(tier="single_pass"), T1)
    assert ctx_t["period_context"]["rows_excluded"]["other_tier"] == len(other)
    # unpinned document (no contract) reads every row
    assert _c5(other, T1, pinned_build_id=None)["class_licence"] == "scored"


def test_testimony_licence_never_licenses_or_activates_vimshottari():
    """Only testimony relations at every level ⇒ class licence 'testimony',
    admitted_paths [], Vimśottarī INACTIVE in the λ factor. Mutation: an
    implementation promoting testimony to scored fails."""
    md = {"dasha_row_id": "md-rahu", "system_id": "vimshottari", "level_n": 1,
          "parent_row_id": None, "lord_graha": "Rahu",
          "start_iso": "2000-01-01T00:00:00Z", "end_iso": "2030-01-01T00:00:00Z",
          "build_id": BUILD, "verification_pass_status": TIER}
    c5 = _c5([md], T1)
    assert c5["period_context"]["md"]["licence"] == "testimony"
    assert c5["class_licence"] == "testimony" and c5["admitted_paths"] == []
    legacy = {"systems": [
        {"system_id": "vimshottari", "weight": 0.16, "active": True},
        {"system_id": "narayana", "weight": 0.08, "active": True},
        {"system_id": "sade_sati", "weight": 0.10, "active": True},
        {"system_id": "ashtottari", "weight": 0.07, "active": True},
    ], "systems_active": ["vimshottari", "narayana", "sade_sati", "ashtottari"]}
    value, d = w.frozen_permission_value(legacy, c5)
    # vimshottari overridden to inactive; sade_sati (testimony) and
    # ashtottari (absent on this chart) leave numerator AND denominator
    assert value == pytest.approx(0.08 / (0.16 + 0.08))
    assert d["systems_active"] == ["narayana"]
    assert {e["system_id"] for e in d["systems_excluded"]} == {"sade_sati", "ashtottari"}
    assert d["class_licence"] == "testimony"
    # scored licence ⇒ vimshottari active, same exclusions
    value_s, d_s = w.frozen_permission_value(legacy, _c5(_l1_rows(), T1))
    assert value_s == pytest.approx(1.0)
    assert d_s["systems_active"] == ["vimshottari", "narayana"]


def test_main_installs_the_per_instant_permission_on_the_executable_path(monkeypatch):
    """The reviewer's mutation: the real factory raising never failed a test
    because main() never called it. The builder main() routes through must
    call the factory with the document's rows/chart/contract and INSTALL its
    result; a raising factory now propagates."""
    doc = {"_dasha_periods": _l1_rows(), "_chart": CHART,
           "_dasha_read_contract": {"build_id": BUILD, "tier": TIER},
           "_av_donor_matrix": {"available_keys": []}}
    ctx_dict = {"permission_systems": {"vimshottari": True},
                "class_valence": "neutral", "class_is_adverse": False}
    seen = {}

    def factory(conn, chart_id, cls, rows, chart, *, pinned_build_id, tier):
        seen.update(rows=rows, chart=chart, build=pinned_build_id, tier=tier)
        return lambda t: (0.42, {"systems_active": ["vimshottari"]})

    ctx = w.build_projection_class_context(
        None, CHART["chart_id"], "marriage", ctx_dict, doc,
        weights=[0.9], weight_by_target_ref={"Venus": 0.9},
        context_source="test", permission_factory=factory)
    assert ctx.permission_mode == "per_instant_md_ad_pd"
    assert ctx.permission_at(w.jd_of(T1))[0] == 0.42
    assert seen["build"] == BUILD and seen["tier"] == TIER
    assert seen["chart"] is CHART and seen["rows"] is doc["_dasha_periods"]
    assert ctx.factors_record()["permission_contract"] == w.PERMISSION_CONTRACT
    assert ctx.av_donor_keys == frozenset()

    def raising(*a, **k):
        raise RuntimeError("factory invoked")

    with pytest.raises(RuntimeError, match="factory invoked"):
        w.build_projection_class_context(
            None, CHART["chart_id"], "marriage", ctx_dict, doc,
            weights=[0.9], weight_by_target_ref={"Venus": 0.9},
            context_source="test", permission_factory=raising)
    # the default factory IS the real one
    monkeypatch.setattr(w, "make_per_instant_permission_fn", raising)
    with pytest.raises(RuntimeError, match="factory invoked"):
        w.build_projection_class_context(
            None, CHART["chart_id"], "marriage", ctx_dict, doc,
            weights=[0.9], weight_by_target_ref={"Venus": 0.9},
            context_source="test")
    # main() constructs every ClassContext through the builder — no other
    # ClassContext( call sites remain in main()
    tree = ast.parse(inspect.getsource(w.main))
    calls = [n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "build_projection_class_context" in calls
    assert "ClassContext" not in calls


def test_document_with_periods_but_no_chart_is_refused():
    doc = {"_dasha_periods": _l1_rows()}
    with pytest.raises(ValueError, match="_chart"):
        w.build_projection_class_context(
            None, CHART["chart_id"], "marriage",
            {"permission_systems": {"vimshottari": True}}, doc,
            weights=[0.9], weight_by_target_ref={"Venus": 0.9},
            context_source="test", permission_factory=lambda *a, **k: None)


def test_old_document_without_periods_keeps_static_fallback():
    ctx = w.build_projection_class_context(
        None, CHART["chart_id"], "marriage",
        {"permission_systems": {"vimshottari": True}}, {"marriage": {}},
        weights=[0.9], weight_by_target_ref={"Venus": 0.9},
        context_source="test", permission_factory=lambda *a, **k: 1 / 0)
    assert ctx.permission_mode == "static_systems_active"
    assert isinstance(ctx.permission, float)


def test_factory_none_means_targets_unresolved_class_skipped():
    doc = {"_dasha_periods": _l1_rows(), "_chart": CHART}
    assert w.build_projection_class_context(
        None, CHART["chart_id"], "marriage",
        {"permission_systems": {"vimshottari": True}}, doc,
        weights=[0.9], weight_by_target_ref={"Venus": 0.9},
        context_source="test", permission_factory=lambda *a, **k: None) is None


# ── step06a: chart operands + read-contract selection ────────────────────────


def _load_step06a():
    spec = importlib.util.spec_from_file_location(
        "step06a_class_context_t06b",
        WRITER_PATH.parent / "step06a_class_context.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _Rows:
    autocommit = True

    def __init__(self, rows):
        self._rows = rows

    def execute(self, _sql, _params=None):
        rows = self._rows

        class _C:
            def fetchall(self_inner):
                return rows
        return _C()


def test_step06a_chart_operands_are_title_cased_from_l1_codes():
    mod = _load_step06a()
    rows = [("graha_position", code, "longitude_sidereal", None, lon) for code, lon in (
        ("SUN", 291.96), ("MOON", 327.06), ("MAR", 198.52), ("MER", 270.84),
        ("JUP", 249.79), ("VEN", 259.19), ("SAT", 202.43), ("RAH_MEAN", 49.03),
        ("KET_MEAN", 229.03), ("LAGNA", 12.43))]
    rows += [("panchanga_tithi", "TITHI_BIRTH", "paksha", "shukla", None),
             ("saham_position", "SAHAM", "day_birth", "true", None)]
    ch = mod.fetch_chart_operands(_Rows(rows), CHART["chart_id"])
    assert ch["natal"] == NATAL and ch["lagna_deg"] == LAGNA_DEG
    assert ch["paksha"] == "Shukla" and ch["day_birth"] is True
    assert ch["operands_missing"] == []
    # missing operands are NAMED, never defaulted
    ch2 = mod.fetch_chart_operands(_Rows(rows[:3]), CHART["chart_id"])
    assert "graha_position:LAGNA" in ch2["operands_missing"]
    assert "panchanga_tithi:paksha" in ch2["operands_missing"]
    assert ch2["day_birth"] is None
    # a duplicate position with a different value is a conflict, not a pick
    ch3 = mod.fetch_chart_operands(
        _Rows(rows + [("graha_position", "SUN", "longitude_sidereal", None, 1.0)]),
        CHART["chart_id"])
    assert "graha_position:SUN:conflict" in ch3["operands_missing"]
    assert "Sun" not in ch3["natal"]


def test_step06a_read_contract_pins_the_frozen_build_or_refuses():
    mod = _load_step06a()
    rows = _l1_rows() + _l1_rows(build="other-build")
    c = mod.select_dasha_read_contract(CHART["chart_id"], rows)
    assert c["build_id"] == BUILD and "pinned" in c["basis"]
    c1 = mod.select_dasha_read_contract("some-other-chart", _l1_rows(build="b1"))
    assert c1["build_id"] == "b1"
    with pytest.raises(DD.DashaReadConflict):
        mod.select_dasha_read_contract("some-other-chart", rows)
    assert mod.select_dasha_read_contract("x", [])["build_id"] is None


# ── ASTRA v1.1 P1-2: the frozen daśā read contract and C5 identity ───────────

MD_ID = "58afa482-4bce-42df-9c0d-0b5a2e02305e"


def _l1row(rid, level, parent, lord, start, end, *, build=BUILD, tier=TIER,
           system="vimshottari"):
    return {"dasha_row_id": rid, "system_id": system, "level_n": level,
            "parent_row_id": parent, "lord_graha": lord, "start_iso": start,
            "end_iso": end, "build_id": build, "verification_pass_status": tier}


def test_canonical_chart_refuses_a_wrong_sole_build_and_null_builds():
    mod = _load_step06a()
    with pytest.raises(DD.DashaReadConflict, match="pins build"):
        mod.select_dasha_read_contract(CHART["chart_id"], _l1_rows(build="wrong-build"))
    with pytest.raises(DD.DashaReadConflict, match="pins build"):
        mod.select_dasha_read_contract(CHART["chart_id"], [])
    # a non-canonical chart with a single build is accepted; NULL builds refused
    assert mod.select_dasha_read_contract("other", _l1_rows(build="b1"))["build_id"] == "b1"
    with pytest.raises(DD.DashaReadConflict, match="NULL build_id"):
        mod.select_dasha_read_contract("other", _l1_rows(build=None))


def test_null_build_or_tier_rows_are_rejected_under_explicit_pins():
    """A row escaping the pin with a NULL build_id / tier is excluded (never
    accepted as 'unpinned'); the reviewer's probe accepted NULLs."""
    null_build_md = _l1row("md-null", 1, None, "Venus", "2000-01-01T00:00:00Z",
                         "2030-01-01T00:00:00Z", build=None)
    sel = w.select_period_rows([null_build_md] + _l1_rows(), w.jd_of(T1),
                               pinned_build_id=BUILD, tier=TIER)
    assert sel["md"]["lord_graha"] == "Mercury"
    assert sel["rows_excluded"]["missing_build_id"] == 1
    null_tier_md = _l1row("md-nt", 1, None, "Venus", "2000-01-01T00:00:00Z",
                        "2030-01-01T00:00:00Z", tier=None)
    sel = w.select_period_rows([null_tier_md] + _l1_rows(), w.jd_of(T1),
                               pinned_build_id=BUILD, tier=TIER)
    assert sel["md"]["lord_graha"] == "Mercury"
    assert sel["rows_excluded"]["missing_tier"] == 1
    # without an explicit pin the NULL-build row is a genuine competitor —
    # and two MD rows overlapping at t is a (level, parent, index) conflict
    with pytest.raises(DD.DashaReadConflict):
        w.select_period_rows([null_build_md] + _l1_rows(), w.jd_of(T1),
                             pinned_build_id=None, tier=None)


def test_conflicting_level_parent_index_rows_raise_even_when_t_is_elsewhere():
    """Two surviving siblings under one parent whose intervals overlap
    compete for one (level, parent, index): rejected over the WHOLE pinned
    set, not only at rows covering t. The reviewer's probe retained them."""
    bogus = _l1row("ad-bogus", 2, MD_ID, "Jupiter", "2019-06-01T00:00:00Z",
                 "2019-09-01T00:00:00Z")  # overlaps the Mars AD
    with pytest.raises(DD.DashaReadConflict, match="index"):
        _c5(_l1_rows(extra=[bogus]), T2)  # t₂ is inside the Rahu AD, not the overlap
    # non-overlapping extra siblings are fine and get their own index
    fine = _l1row("ad-fine", 2, MD_ID, "Jupiter", "2022-09-02T21:05:23Z",
                "2024-01-01T00:00:00Z")
    ctx = _c5(_l1_rows(extra=[fine]), T2)["period_context"]
    assert ctx["ad"]["lord"] == "Rahu" and ctx["ad"]["index"] == 3


def test_duplicate_parent_collapse_canonicalizes_children_never_orphans():
    """Two identical MD rows (different ids) collapse; an AD parented to the
    dropped duplicate is re-pointed to the keeper and still selected."""
    rows = _l1_rows()
    dup_md = _l1row("md-dup", 1, None, "Mercury", "2010-08-18T15:50:23Z",
                  "2027-08-18T21:50:23Z")
    for r in rows:
        if r["dasha_row_id"] == "b1e4d515-6a94-4054-89ff-1ed2487f66ae":  # Mars AD
            r["parent_row_id"] = "md-dup"
    ctx = _c5(rows + [dup_md], T1)["period_context"]
    assert ctx["md"]["lord"] == "Mercury"
    assert set(ctx["md"]["merged_row_ids"]) == {MD_ID, "md-dup"}
    assert ctx["ad"]["lord"] == "Mars" and ctx["ad"]["licence"] == "scored"
    assert ctx["orphans_ignored"] == []
    # the alias is disclosed
    assert ctx["ad"]["parent_row_id"] == MD_ID


def test_exact_instants_are_never_advanced_by_rounding():
    rows = _l1_rows()
    one_ms_before = BOUNDARY - timedelta(milliseconds=1)
    assert w.utc_iso_of_jd(w.jd_of(one_ms_before)) < "2020-02-14T11:47:23"
    assert _c5(rows, one_ms_before)["period_context"]["ad"]["lord"] == "Mars"
    # the exact boundary via the exact instant (half-open ⇒ Rahu)
    at = w.frozen_c5_permission_context(
        rows, w.jd_of(BOUNDARY), "marriage", CHART, pinned_build_id=BUILD,
        tier=TIER, t_iso="2020-02-14T11:47:23+00:00")
    assert at["period_context"]["ad"]["lord"] == "Rahu"
    assert at["period_context"]["t_utc"] == "2020-02-14T11:47:23+00:00"
    before = w.frozen_c5_permission_context(
        rows, w.jd_of(BOUNDARY), "marriage", CHART, pinned_build_id=BUILD,
        tier=TIER, t_iso="2020-02-14T11:47:22.999999+00:00")
    assert before["period_context"]["ad"]["lord"] == "Mars"


def test_relation_identity_and_sibling_index_on_every_level():
    rows = _l1_rows()
    p1 = _c5(rows, T1)["period_context"]
    p2 = _c5(rows, T2)["period_context"]
    for lvl in ("md", "ad", "pd"):
        assert isinstance(p1[lvl]["index"], int)
        assert p1[lvl]["relation_record_id"].startswith("sha256:")
    # AD siblings under the MD sorted by start: Ketu, Moon, Mars, Rahu
    assert (p1["ad"]["index"], p2["ad"]["index"]) == (2, 3)
    # distinct relations ⇒ distinct record ids; same relation ⇒ same id
    assert p1["ad"]["relation_record_id"] != p1["pd"]["relation_record_id"]
    assert p1["pd"]["relation_record_id"] == p2["pd"]["relation_record_id"]
    assert p1["md"]["relation_record_id"] == p2["md"]["relation_record_id"]
    # the record id is the B5.1 deterministic natural-key hash
    from services.gochara_rules.records import RelationshipRecord
    from services.gochara_rules.registry import RULE_VERSION
    rec = RelationshipRecord(
        chart_id=CHART["chart_id"], generation="4.0", event_class="marriage",
        affected_person="native", frame="lagna", agent="Mars",
        relation="occupancy", object_id="obj:sign:Libra", object_kind="sign_span",
        object_role="occupant", contact_id=None, path_id="P1",
        rule_version=RULE_VERSION, prerequisites=[], provenance="verse_cited",
        operator_role="scored", source_text="Phaladīpikā",
        source_page="PG249-250 (XX.34-38)")
    assert p1["ad"]["relation_record_id"] == rec.record_id
    # a level with no relation carries no identity
    assert w.c5_relation_record_id("Mars", "none", "marriage", CHART, "none") is None


# ── dasha_data.canonicalize_multilevel_rows (the shared pass) ───────────────


def test_canonicalize_collapses_identical_rows_and_aliases_parents():
    rows = [_l1row("md-a", 1, None, "Mercury", "2010-01-01T00:00:00Z", "2027-01-01T00:00:00Z"),
            _l1row("md-b", 1, None, "Mercury", "2010-01-01T00:00:00Z", "2027-01-01T00:00:00Z"),
            _l1row("ad-1", 2, "md-b", "Ketu", "2013-01-14T00:00:00Z", "2014-01-11T00:00:00Z"),
            _l1row("ad-2", 2, "md-a", "Venus", "2014-01-11T00:00:00Z", "2017-01-01T00:00:00Z")]
    out = DD.canonicalize_multilevel_rows(rows)
    by_id = {r["dasha_row_id"]: r for r in out}
    assert set(by_id) == {"md-a", "ad-1", "ad-2"}
    assert by_id["md-a"]["merged_row_ids"] == ["md-a", "md-b"]
    assert by_id["ad-1"]["parent_row_id"] == "md-a"
    assert by_id["ad-1"]["parent_row_id_original"] == "md-b"
    assert (by_id["ad-1"]["index"], by_id["ad-2"]["index"]) == (0, 1)


def test_canonicalize_rejects_overlapping_siblings_and_is_order_independent():
    a = _l1row("ad-1", 2, "md", "Ketu", "2013-01-14T00:00:00Z", "2014-01-11T00:00:00Z")
    b = _l1row("ad-2", 2, "md", "Venus", "2013-06-01T00:00:00Z", "2015-01-01T00:00:00Z")
    with pytest.raises(DD.DashaReadConflict, match="index"):
        DD.canonicalize_multilevel_rows([a, b])
    with pytest.raises(DD.DashaReadConflict, match="index"):
        DD.canonicalize_multilevel_rows([b, a])
    # touching intervals (half-open) are NOT a conflict
    c = _l1row("ad-3", 2, "md", "Venus", "2014-01-11T00:00:00Z", "2015-01-01T00:00:00Z")
    out = {r["dasha_row_id"]: r["index"] for r in DD.canonicalize_multilevel_rows([c, a])}
    assert out == {"ad-1": 0, "ad-3": 1}


def test_multilevel_fetch_pins_build_in_the_query_and_drops_null_tier_rows():
    seen = {}

    class _C:
        def execute(self, sql, params):
            seen["sql"], seen["params"] = sql, params
            rows = [["r1", "vimshottari", 1, None, "Jupiter", "2020-01-01", "2030-01-01", "b1", "two_pass_verified"],
                    ["r2", "vimshottari", 2, "r1", "Saturn", "2020-01-01", "2021-01-01", "b1", None]]

            class _X:
                def fetchall(self_inner):
                    return rows
            return _X()
    out = DD.fetch_dasha_periods_multilevel(_C(), "chart-x", build_id="b1")
    assert "AND build_id = %s" in seen["sql"] and seen["params"][-1] == "b1"
    assert seen["params"][4] == DD.READ_CONTRACT_TIER  # tier pinned before duplicates
    assert [r["dasha_row_id"] for r in out] == ["r1"]  # NULL-tier row rejected


# ── ASTRA v1.2 P1-1: pin BEFORE canonicalization on main()'s path; recursive trees ──


class _DashaConn:
    """Stub chart_dashas: answers the RAW tier-pinned read (no build
    predicate) with rows of every build, and the build-PINNED read with the
    pinned build's rows only — the two reads main() now performs."""

    def __init__(self, rows_by_build: dict):
        self._rows = rows_by_build
        self.queries: list[tuple[str, list]] = []

    def execute(self, sql, params):
        self.queries.append((sql, params))
        systems = params[2]
        pinned = params[-1] if "AND build_id = %s" in sql else None
        out = []
        for build, rows in self._rows.items():
            if pinned is not None and build != pinned:
                continue
            for r in rows:
                if r["system_id"] in systems:
                    out.append([r["dasha_row_id"], r["system_id"], r["level_n"],
                                r["parent_row_id"], r["lord_graha"], r["start_iso"],
                                r["end_iso"], build, r["verification_pass_status"]])

        class _X:
            def fetchall(self_inner):
                return out
        return _X()


def test_actual_main_path_pins_the_build_before_canonicalization():
    """The reviewer's mixed-build reproduction: an UNRELATED build whose MD
    row overlaps the pinned build's MD would be rejected as a (level,
    parent, index) conflict if all builds were canonicalized first. main()'s
    load_pinned_dasha_periods selects the pin from a RAW read and
    canonicalizes only the pinned rows — the foreign build never enters the
    conflict pass."""
    mod = _load_step06a()
    foreign = [_l1row("md-foreign", 1, None, "Venus", "2005-01-01T00:00:00Z",
                      "2025-01-01T00:00:00Z", build="other-build")]
    conn = _DashaConn({BUILD: _l1_rows(), "other-build": foreign})
    periods, contract = mod.load_pinned_dasha_periods(
        conn, CHART["chart_id"], ["vimshottari", "yogini"])
    assert contract["build_id"] == BUILD and contract["basis"].endswith("pinned build")
    assert contract["raw_vimshottari_rows"] == len(_l1_rows()) + 1
    assert contract["rows_excluded_by_build_pin"] == 1
    assert {str(p["build_id"]) for p in periods if p["system_id"] == "vimshottari"} == {BUILD}
    assert not any(p["dasha_row_id"] == "md-foreign" for p in periods)
    # the raw read carried no build predicate; the pinned read did
    raw_sql, raw_params = conn.queries[0]
    pinned_sql, pinned_params = conn.queries[1]
    assert "AND build_id = %s" not in raw_sql and raw_params[2] == ["vimshottari"]
    assert "AND build_id = %s" in pinned_sql and pinned_params[-1] == BUILD
    # and the C5 licence evaluates on the pinned set at t₁ (Mars AD scored)
    ctx = w.frozen_c5_permission_context(periods, w.jd_of(T1), "marriage", CHART,
                                         pinned_build_id=contract["build_id"],
                                         tier=contract["tier"])
    assert ctx["period_context"]["ad"]["lord"] == "Mars"
    # mutation: canonicalizing every build first raises on the foreign overlap
    with pytest.raises(DD.DashaReadConflict):
        DD.canonicalize_multilevel_rows(_l1_rows() + foreign)


def test_main_calls_the_pinned_loader_and_never_the_unpinned_fetch():
    import ast, inspect
    mod = _load_step06a()
    src = inspect.getsource(mod.main)
    calls = {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None)
             for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)}
    assert "load_pinned_dasha_periods" in calls
    assert "fetch_dasha_periods_multilevel" not in calls


def test_complete_duplicated_md_ad_pd_tree_collapses_recursively():
    """A whole duplicated tree (two MD rows, two AD rows under each, two PD
    rows under each AD — identical fields, distinct ids): the reviewer's
    probe failed after the parents converged because the identical children
    were then rejected as overlapping siblings. Descendants are normalised
    after their parents and collapsed after normalisation."""
    def tree(suffix):
        md = _l1row(f"md-{suffix}", 1, None, "Mercury", "2010-08-18T15:50:23Z", "2027-08-18T21:50:23Z")
        ad1 = _l1row(f"ad1-{suffix}", 2, f"md-{suffix}", "Mars", "2019-02-17T06:50:23Z", "2020-02-14T11:47:23Z")
        ad2 = _l1row(f"ad2-{suffix}", 2, f"md-{suffix}", "Rahu", "2020-02-14T11:47:23Z", "2022-09-02T21:05:23Z")
        pd1 = _l1row(f"pd1-{suffix}", 3, f"ad1-{suffix}", "Saturn", "2019-06-21T00:55:52Z", "2019-08-17T09:18:53Z")
        pd2 = _l1row(f"pd2-{suffix}", 3, f"ad2-{suffix}", "Saturn", "2020-11-04T09:13:29Z", "2021-03-31T20:29:50Z")
        return [md, ad1, ad2, pd1, pd2]
    rows = tree("a") + tree("b")
    out = DD.canonicalize_multilevel_rows(rows)
    by_id = {r["dasha_row_id"]: r for r in out}
    assert set(by_id) == {"md-a", "ad1-a", "ad2-a", "pd1-a", "pd2-a"}
    assert by_id["md-a"]["merged_row_ids"] == ["md-a", "md-b"]
    assert by_id["ad1-a"]["merged_row_ids"] == ["ad1-a", "ad1-b"]
    assert by_id["pd1-a"]["merged_row_ids"] == ["pd1-a", "pd1-b"]
    assert by_id["pd2-a"]["parent_row_id"] == "ad2-a"
    assert (by_id["ad1-a"]["index"], by_id["ad2-a"]["index"]) == (0, 1)
    # order-independent
    out2 = DD.canonicalize_multilevel_rows(list(reversed(rows)))
    assert {r["dasha_row_id"] for r in out2} == {"md-b", "ad1-b", "ad2-b", "pd1-b", "pd2-b"}
    # the licence evaluates on the collapsed tree (Mars AD scored at t₁)
    sel = w.select_period_rows(rows, w.jd_of(T1), pinned_build_id=BUILD, tier=TIER)
    assert sel["ad"]["lord_graha"] == "Mars" and sel["pd"]["lord_graha"] == "Saturn"
    assert sel["orphans_ignored"] == []
