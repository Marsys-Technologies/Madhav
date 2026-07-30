"""
test_mi_bhara_weights_acyclicity — ṢAḌ-DARŚANA W2 Lane E · weights versioning and THE
WEIGHTS-VERSION ACYCLICITY MECHANISM (§7.5).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.5 (all six sub-rules); brief §2.5.4.

THE TWO THINGS THIS FILE PROVES, both of which are cheap to get wrong and expensive to
discover later:

  A. **RESOLVE ONCE (sub-rule 5).** A long `ka_kshetra` build that straddles an `mi_bhara`
     release must NOT write some segments under the old weights version and the rest under
     the new one. The detector below is a connection whose answer genuinely CHANGES between
     calls — a fake that returns `v1` the first time and `v2` thereafter. If the pin were
     re-resolved per substep, every substep after the first would carry `v2` and the assertion
     would fail. With `pin_once`, all of them carry `v1`. That is a real failure mode with a
     real detector, not a restated intention (§N.8).

  B. **NO CYCLE (sub-rule 6), asserted POSITIVELY.** Not "we did not find `mi_bhara` in
     `ka_kshetra.depends_on`" — a topo-sort that either produces an order or raises. The
     negative form would pass by not-noticing if the edge arrived under a different name or
     through a longer path; the positive form cannot.

`platform/tests/unit/build/w2_weights_acyclicity.test.ts` is the sibling half, asserting the
REAL `resolveBuildPlan` against the REAL `asset_registry_seed.ts`. Neither half alone is the
proof: this one covers the Python writer side, that one covers the resolver that actually
runs in production.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mi_bhara.weights import (  # noqa: E402
    V0_CLASSICAL,
    WeightsPin,
    WeightsPinnedPlan,
    WeightsResolutionError,
    assert_no_weights_cycle,
    assert_single_weights_version,
    next_version_id,
    resolve_weights_version,
    topo_sort,
)

CHART = "482012f1-710e-4a25-994a-93821f5871aa"


# ── a connection double whose answer CHANGES between calls ─────────────────────────────

class _MutatingCursor:
    def __init__(self, owner):
        self._owner = owner

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._owner.calls += 1

    def fetchone(self):
        # First call sees v1; every call after sees v2 — i.e. an `mi_bhara` release landed
        # mid-build. A per-substep resolver would silently follow it.
        if self._owner.calls <= 1:
            return {
                "version_id": "v1_2026-08-14_abhisek",
                "scope": "per_chart",
                "fitted_from_chart_id": CHART,
                "x_schema_version": "x_schema/1",
                "activated_at": "2026-08-14T00:00:00Z",
            }
        return {
            "version_id": "v2_2026-08-15_abhisek",
            "scope": "per_chart",
            "fitted_from_chart_id": CHART,
            "x_schema_version": "x_schema/1",
            "activated_at": "2026-08-15T00:00:00Z",
        }


class MutatingConn:
    """Simulates a weights release landing mid-build."""

    def __init__(self):
        self.calls = 0

    def cursor(self, *a, **kw):
        return _MutatingCursor(self)


class EmptyConn:
    class _Cur:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return None

    def cursor(self, *a, **kw):
        return EmptyConn._Cur()


class TupleRowConn:
    """A connection using the default tuple row factory rather than `dict_row`."""

    class _Cur:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return (V0_CLASSICAL, "global", None, "x_schema/1", "2026-07-30T00:00:00Z")

    def cursor(self, *a, **kw):
        return TupleRowConn._Cur()


# ── A — RESOLVE ONCE ───────────────────────────────────────────────────────────────────

def test_pin_is_resolved_once_even_when_a_new_version_lands_mid_build():
    """SUB-RULE 5's detector. The connection would report a NEW version on every call after
    the first; the plan must never ask it again."""
    conn = MutatingConn()
    plan = WeightsPinnedPlan.pin_once(conn, CHART)

    keys = [plan.substep_key("stage4", f"career_change:{decade}") for decade in range(10)]
    keys += [plan.substep_key("stage5", f"career_change:{block}") for block in range(8)]
    keys += [plan.substep_key("stage8", view) for view in ("now", "ahead", "elect")]

    versions = {WeightsPinnedPlan.version_from_substep_key(k) for k in keys}
    assert versions == {"v1_2026-08-14_abhisek"}, (
        "every substep of one build must carry the SAME pinned weights version; a build that "
        "re-resolved per substep would mix two models into one snapshot (§7.5 sub-rule 5)"
    )
    assert conn.calls == 1, f"the table was queried {conn.calls} times; sub-rule 5 allows one"
    plan.assert_resolved_once()
    assert plan.resolutions() == 1


def test_the_detector_would_genuinely_fail_if_the_version_were_re_resolved_per_substep():
    """The VACUITY HALF of the test above (§N.7 item 4). If `MutatingConn` did not actually
    change its answer, the assertion `versions == {one thing}` would pass for a broken
    implementation too. This proves the double is live."""
    conn = MutatingConn()
    naive = [resolve_weights_version(conn, CHART).version_id for _ in range(3)]
    assert naive == [
        "v1_2026-08-14_abhisek",
        "v2_2026-08-15_abhisek",
        "v2_2026-08-15_abhisek",
    ], "the fake must genuinely change its answer, or the resolve-once test is vacuous"
    assert conn.calls == 3


def test_a_substep_key_with_no_pin_is_rejected_rather_than_silently_defaulted():
    with pytest.raises(ValueError, match="carries no weights pin"):
        WeightsPinnedPlan.version_from_substep_key("stage4:career_change:3")


def test_the_pin_survives_serialisation_so_a_resumed_build_reads_the_ORIGINAL_version():
    """`build_substep_progress` persists substep keys across process restarts. A resumed build
    must continue under the version it started with, not under today's newest."""
    pin = WeightsPin(
        version_id="v1_2026-08-14_abhisek",
        scope="per_chart",
        x_schema_version="x_schema/1",
        fitted_from_chart_id=CHART,
    )
    assert WeightsPin.from_payload(pin.to_payload()) == pin
    # order-independent: the payload is the field-hash input, so it must be canonical
    assert pin.to_payload() == WeightsPin(
        fitted_from_chart_id=CHART,
        x_schema_version="x_schema/1",
        scope="per_chart",
        version_id="v1_2026-08-14_abhisek",
    ).to_payload()


def test_no_active_weights_version_halts_rather_than_inventing_one():
    """Migration 476 seeds `v0_classical` exactly so this cannot happen. If it does, a
    fabricated default would produce a `field_snapshot_id` that means nothing."""
    with pytest.raises(WeightsResolutionError, match="migration 476"):
        resolve_weights_version(EmptyConn(), CHART)


def test_resolution_works_under_the_default_tuple_row_factory_too():
    """Writers in this repo variously use `dict_row` and the default tuple factory; a resolver
    that only handled one would fail at exactly the wrong moment."""
    pin = resolve_weights_version(TupleRowConn(), CHART)
    assert pin.version_id == V0_CLASSICAL
    assert pin.scope == "global"
    assert pin.fitted_from_chart_id is None


def test_a_snapshot_carrying_two_weights_versions_is_rejected():
    """The CI-side half of sub-rule 5, run over a snapshot's `kala_field` rows."""
    assert assert_single_weights_version([{"weights_version": "v1"}] * 5) == "v1"
    with pytest.raises(AssertionError, match="straddled a weights release"):
        assert_single_weights_version(
            [{"weights_version": "v1"}, {"weights_version": "v1"}, {"weights_version": "v2"}]
        )
    with pytest.raises(ValueError, match="empty snapshot proves nothing"):
        assert_single_weights_version([])


# ── B — NO CYCLE, asserted positively ──────────────────────────────────────────────────

# The eight edges §9.1 declares for `ka_kshetra` at W2. `bg_sky_calendar` is deliberately
# ABSENT: it is a W3 asset and §9.1's EDGE-STAGING RULE says W2 must not pre-declare it.
KA_KSHETRA_W2_EDGES = [
    "ka_dasha_kala",
    "ka_gochara_sweep",
    "ka_gochara_resonance",
    "ga_panchanga",
    "bo_pratijna",
    "bo_sangati",
    "bo_upaya",
    "bg_cohort",
]

W2_DAG = {
    "ka_kshetra": KA_KSHETRA_W2_EDGES,
    "mi_bhara": ["ka_kshetra"],
    "mi_sankalpa": ["ka_kshetra"],
}


def test_the_three_asset_plan_topo_sorts_without_error_and_orders_ka_kshetra_first():
    order = assert_no_weights_cycle(W2_DAG)
    assert set(order) == {"ka_kshetra", "mi_bhara", "mi_sankalpa"}
    assert order.index("ka_kshetra") < order.index("mi_bhara")
    assert order.index("ka_kshetra") < order.index("mi_sankalpa")


def test_adding_the_forbidden_edge_is_caught_by_BOTH_halves_of_the_guard():
    """The one that matters. Half (a) names the specific edge; half (b) — the topo-sort —
    catches the same cycle arriving by any other route."""
    poisoned = dict(W2_DAG)
    poisoned["ka_kshetra"] = KA_KSHETRA_W2_EDGES + ["mi_bhara"]
    with pytest.raises(AssertionError, match="forms the cycle"):
        assert_no_weights_cycle(poisoned)
    with pytest.raises(ValueError, match="Cycle detected"):
        topo_sort(["ka_kshetra", "mi_bhara"], poisoned)


def test_a_longer_cycle_that_evades_the_named_edge_check_is_still_caught():
    """`ka_kshetra → mi_sankalpa → mi_bhara → ka_kshetra` never puts `mi_bhara` directly in
    `ka_kshetra.depends_on`, so half (a) alone would pass it. Half (b) does not."""
    sneaky = {
        "ka_kshetra": KA_KSHETRA_W2_EDGES + ["mi_sankalpa"],
        "mi_sankalpa": ["mi_bhara"],
        "mi_bhara": ["ka_kshetra"],
    }
    with pytest.raises(ValueError, match="Cycle detected"):
        assert_no_weights_cycle(sneaky)


def test_w2_must_not_pre_declare_the_w3_bg_sky_calendar_edge():
    """§9.1's EDGE-STAGING RULE. `resolveBuildPlan` cannot resolve an edge to an id with no
    seed row, so a "helpful" early declaration would 500 every chart build."""
    assert "bg_sky_calendar" not in KA_KSHETRA_W2_EDGES


def test_topo_sort_mirrors_plan_ts_by_skipping_out_of_scope_dependencies():
    """`plan.ts`'s `topoSort` only recurses into deps that are IN SCOPE. A mirror that
    recursed into everything would raise on a perfectly valid partial plan."""
    order = topo_sort(["mi_bhara"], W2_DAG)
    assert order == ["mi_bhara"]


# ── version identity ───────────────────────────────────────────────────────────────────

def test_next_version_id_increments_past_the_highest_existing_and_never_collides_same_day():
    assert next_version_id("abhisek", "2026-08-14", [V0_CLASSICAL]) == "v1_2026-08-14_abhisek"
    assert (
        next_version_id("abhisek", "2026-08-14", [V0_CLASSICAL, "v1_2026-08-14_abhisek"])
        == "v2_2026-08-14_abhisek"
    )
    assert next_version_id("abhisek", "2026-08-14", []) == "v1_2026-08-14_abhisek"
