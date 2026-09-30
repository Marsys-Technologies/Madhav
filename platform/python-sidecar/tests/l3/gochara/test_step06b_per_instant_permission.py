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
from datetime import datetime, timezone
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
