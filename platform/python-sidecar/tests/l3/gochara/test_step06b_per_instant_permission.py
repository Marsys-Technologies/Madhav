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
