"""A5.3 — scope is NOT completeness (Codex round 8, R8-5).

`coverage_response` used to make a manifest's `stored_scope` sufficient for `complete_within_scope`. The scope says what
the stored tier HOLDS; completeness says the REQUESTED class and horizon were searched, finalised and verified. Both are
carried; `complete_within_scope` needs the second, derived from the class/horizon's own coverage, inventory and
verification state. Cases: the review's manifest-only fake, an unpublished manifest, a missing class, an incomplete
horizon, a stale binding, a search with missing inputs, an unverified inventory, an unverified window, and the one
complete case — plus before/after on-demand answers, which never move either.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory_verifier as ver
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import scope_response as sr

from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN
from .test_a53_window_verification_gate import CLS, _boot_p3, _consistent_sky, _windows, world  # noqa: F401

UTC = timezone.utc


def _resp(w, **kw):
    kw.setdefault("horizon", (H0, H1))
    return sr.coverage_response(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, windows=[], **kw)


def _complete_world(w):
    """Every precondition of `complete_within_scope`: published manifest bound to the snapshot, a finalised inventory
    covering the horizon, no missing inputs, an independent inventory verification, a completed coverage partition and a
    VERIFIED window result for every included grain."""
    _boot_p3(w)
    _windows(w)
    digest = w.conn.execute("SELECT inventory_digest FROM public.ka_gochara_search_inventory"
                            " WHERE event_class = %s", (CLS,)).fetchone()[0]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SELECT public.ka_gochara_lock_global_shared()")
        ver.write_verification(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, rederived_digest=digest)
        # without 1232 the Moon-resolved period portions stay honest `missing_inputs` (the schema is read, never assumed),
        # so a class is never complete on such a schema; this stand-in for 1232's accounting lets the ONE complete
        # case exist (the interval ledger digest is not what this constructor re-derives)
        w.conn.execute("ALTER TABLE public.ka_gochara_search_interval DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_search_interval SET state = 'searched_complete'"
                       " WHERE state = 'missing_inputs'")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_interval ENABLE TRIGGER USER")
        gk_ledger.publish(w.conn, CHART_ID, GEN)


def _states(w):
    r = _resp(w)
    return r["completeness"], [x["code"] for x in r["completeness_reasons"]]


# ── the review's counterexample: scope alone is not completeness ─────────────────────────────────────────

class _ManifestOnlyConn:
    """The review's fake connection: ONLY a manifest carrying `stored_scope` (published), nothing searched."""
    def execute(self, sql, params=()):
        s = " ".join(sql.split())

        class R:
            def __init__(self, rows):
                self.rows = rows

            def fetchone(self):
                return self.rows[0] if self.rows else None

            def fetchall(self):
                return self.rows
        if "FROM public.kala_gochara_publication" in s:
            return R([({"stored_scope": "stored_non_moon"}, "published", None)])
        if "partition_kind = 'moon_on_demand'" in s:
            return R([])
        if "ka_gochara_search_input_snapshot" in s:
            return R([])
        raise AssertionError(f"unexpected query: {s[:80]}")


def test_a_manifest_with_the_scope_and_nothing_else_is_never_complete():
    r = sr.coverage_response(_ManifestOnlyConn(), chart_id=CHART_ID, generation=GEN, event_class=CLS, windows=[])
    assert r["stored_scope"] == "stored_non_moon" and "Moon" in r["scope_statement"]      # the scope IS carried ...
    assert r["completeness"] == "stale_binding" != sr.COMPLETE                            # ... completeness is not claimed
    assert [x["code"] for x in r["completeness_reasons"]] == ["no_search_snapshot"]
    assert r["window_count"] == 0


# ── on the real schema ──────────────────────────────────────────────────────────────────────────────────

def test_the_complete_case_is_complete_only_when_every_precondition_holds(world):
    w = world
    _complete_world(w)
    r = _resp(w)
    assert r["completeness"] == sr.COMPLETE and r["completeness_reasons"] == [], r["completeness_reasons"]
    assert r["stored_scope"] == "stored_non_moon" and r["completeness_basis"]["window_verification"] == "VERIFIED"
    assert r["completeness_basis"]["inventory_digest"]
    # a narrower request inside the searched horizon is complete too; the default horizon is the stored one
    assert _resp(w, horizon=(datetime(2025, 1, 10, tzinfo=UTC), datetime(2025, 1, 20, tzinfo=UTC)))["completeness"] \
        == sr.COMPLETE
    assert _resp(w, horizon=None)["completeness"] == sr.COMPLETE


def test_an_unpublished_manifest_is_not_published_not_complete(world):
    w = world
    _boot_p3(w)
    _windows(w)
    r = _resp(w)
    assert r["completeness"] == "not_published" and r["stored_scope"] == "stored_non_moon"


def test_a_class_that_was_never_searched_is_named_not_complete(world):
    w = world
    _complete_world(w)
    r = sr.coverage_response(w.conn, chart_id=CHART_ID, generation=GEN, event_class="career_entry", windows=[],
                             horizon=(H0, H1))
    assert r["completeness"] == "class_not_searched" and r["completeness_reasons"][0]["code"] == "no_inventory_for_class"
    assert r["stored_scope"] == "stored_non_moon"


@pytest.mark.parametrize("horizon", [
    (datetime(2024, 12, 1, tzinfo=UTC), datetime(2025, 2, 1, tzinfo=UTC)),       # starts before the searched horizon
    (datetime(2025, 2, 1, tzinfo=UTC), datetime(2025, 4, 1, tzinfo=UTC)),        # ends after it
    (datetime(2020, 1, 1, tzinfo=UTC), datetime(2030, 1, 1, tzinfo=UTC))])       # far wider
def test_a_requested_horizon_beyond_the_searched_one_is_incomplete_not_complete(world, horizon):
    w = world
    _complete_world(w)
    r = _resp(w, horizon=horizon)
    assert r["completeness"] == "incomplete_horizon" and r["completeness_reasons"][0]["code"] == \
        "requested_horizon_not_covered"


def test_a_coverage_partition_that_did_not_complete_the_horizon_is_incomplete(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.kala_gochara_coverage DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.kala_gochara_coverage SET completed_horizon ="
                       " tstzrange(lower(completed_horizon), lower(completed_horizon) + interval '1 day')"
                       " WHERE partition_kind = 'event_class'")
        w.conn.execute("ALTER TABLE public.kala_gochara_coverage ENABLE TRIGGER USER")
    r = _resp(w)
    assert r["completeness"] == "incomplete_horizon" and \
        r["completeness_reasons"][0]["code"] == "coverage_partition_does_not_cover_the_horizon"


def test_a_stale_binding_is_named_when_the_manifest_vector_moved_after_the_snapshot(world):
    w = world
    _complete_world(w)
    assert _resp(w)["completeness"] == sr.COMPLETE
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.kala_gochara_publication DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                       " input_generation_vector || '{\"stored_scope\": \"stored_non_moon\", \"x\": 1}'::jsonb")
        w.conn.execute("ALTER TABLE public.kala_gochara_publication ENABLE TRIGGER USER")
    r = _resp(w)
    assert r["completeness"] == "stale_binding" and \
        r["completeness_reasons"][0]["code"] == "manifest_vector_differs_from_snapshot"
    assert r["stored_scope"] == "stored_non_moon"                      # the scope is still stated; completeness is not


def test_missing_inputs_leave_the_search_incomplete(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.ka_gochara_search_interval DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_search_interval SET state = 'missing_inputs'"
                       " WHERE ctid = (SELECT ctid FROM public.ka_gochara_search_interval LIMIT 1)")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_interval ENABLE TRIGGER USER")
    r = _resp(w)
    assert r["completeness"] == "incomplete_inventory" and r["completeness_reasons"][0]["code"] == \
        "missing_inputs_present"


def test_an_unverified_inventory_or_window_is_not_complete(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
    r = _resp(w)
    assert r["completeness"] == "unverified" and [x["code"] for x in r["completeness_reasons"]] == \
        ["window_verification_missing"]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory_verification DISABLE TRIGGER USER")
        w.conn.execute("DELETE FROM public.ka_gochara_search_inventory_verification")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory_verification ENABLE TRIGGER USER")
    assert _resp(w)["completeness_reasons"][0]["code"] == "inventory_not_independently_verified"


def test_without_window_verification_support_completeness_is_unavailable_not_complete(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("DROP FUNCTION public.ka_gochara_candidate_gate_violations(uuid, text)")
        w.conn.execute("DROP FUNCTION public.ka_gochara_window_verification_violations(uuid, text)")
    r = _resp(w)
    assert r["completeness"] == "evidence_unavailable" and \
        r["completeness_reasons"][0]["code"] == "window_verification_not_applied"


def test_on_demand_answers_before_and_after_change_neither_scope_nor_completeness(world):
    from services.gochara_kernel.record_store import RecordStore
    w = world
    _complete_world(w)
    before = _resp(w)
    kala = w.conn.execute("SELECT convention_id FROM public.kala_gochara_coverage WHERE generation = %s"
                          " AND partition_kind = 'event_class' LIMIT 1", (GEN,)).fetchone()[0]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        RecordStore(w.conn).write_moon_coverage(
            chart_id=CHART_ID, generation=GEN, partition_key="moon:interval:2025-01-05/2025-01-06",
            convention_id=kala, horizon=(datetime(2025, 1, 5, tzinfo=UTC), datetime(2025, 1, 6, tzinfo=UTC)),
            resolution=1.0, relations_searched=["residence"], targets_requested=1, targets_resolved=1,
            state_counts={"resolved": 1, "unavailable": 0, "unqualified": 0}, unavailable_inputs={},
            unsearched_reason=None, build_id="b-od")
    after = _resp(w)
    assert before["completeness"] == after["completeness"] == sr.COMPLETE
    assert before["stored_scope"] == after["stored_scope"] == "stored_non_moon"
    assert before["on_demand_answered"] == [] and after["on_demand_answered"] == ["moon:interval:2025-01-05/2025-01-06"]


def test_a_manifest_without_the_scope_still_refuses_any_completeness_claim(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.kala_gochara_publication DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                       " input_generation_vector - 'stored_scope'")
        w.conn.execute("ALTER TABLE public.kala_gochara_publication ENABLE TRIGGER USER")
    r = _resp(w)
    assert r["completeness"] == "refused" and r["refusal"] == "stored_scope_missing" and r["stored_scope"] is None


# ── window qualification is carried with each returned window ────────────────────────────────────────────

def test_each_returned_window_carries_its_persisted_qualification_and_the_p2_vedha_scope(world):
    w = world
    _complete_world(w)
    wid, objective, qual = w.conn.execute(
        "SELECT window_id::text, objective, qualification FROM public.ka_gochara_eval_window"
        " WHERE path_id = 'P3'").fetchone()
    r = sr.coverage_response(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS,
                             windows=[{"window_id": wid}, {"interval": "no id"}], horizon=(H0, H1))
    first, second = r["window_qualification"]
    assert first["objective"] == objective and first["qualification"] == qual
    # why it is NULL, served: the milestone's policy (the manifest's) — every window carries no number
    assert first["qualification"]["unqualified_reason"] == "all_null_candidate_policy"
    assert first["qualification"]["policy"] == "all_null_candidate/1"
    assert first["qualification"]["unresolved"] == {"applicability_undeclared": 1}         # the audit trail survives
    assert second["qualification"] is None and second["objective"] is None                 # never invented
    assert first["vedha_moon_obstruction_scope"] is None                                   # P3: no vedha operand
    # a numeric P2 window carries the cited vedha scope (a stored state can prove `active`, never fully `inactive`)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
    assert sr.VEDHA_MOON_SCOPE == "excluding_on_demand_moon_obstruction"


def test_the_constructor_is_the_only_place_that_says_complete():
    import inspect
    src = inspect.getsource(sr)
    assert src.count('"complete_within_scope"') == 1 and "COMPLETE = " in src
    assert "completeness=\"complete_within_scope\"" not in src


def test_an_unfinalised_inventory_is_incomplete(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_search_inventory SET inventory_digest = NULL, ledger_digest = NULL,"
                       " finalized_at = NULL")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory ENABLE TRIGGER USER")
    r = _resp(w)
    assert r["completeness"] == "incomplete_inventory" and r["completeness_reasons"][0]["code"] == \
        "inventory_not_finalised"


def test_an_inventory_computed_under_another_snapshot_is_a_stale_binding(world):
    w = world
    _complete_world(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SET LOCAL session_replication_role = replica")                 # skip the FK for the adversary
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_search_inventory SET input_digest = repeat('f', 64)")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory ENABLE TRIGGER USER")
    r = _resp(w)
    assert r["completeness"] == "stale_binding" and r["completeness_reasons"][0]["code"] == \
        "inventory_bound_to_another_snapshot"


def test_a_numeric_p2_window_carries_the_cited_vedha_moon_obstruction_scope():
    class Conn:
        def __init__(self, path, value):
            self.row = ("evidence_for_per_root_sum", value, {"unqualified_reason": None, "unresolved": {},
                                                             "affected_channels": [], "members": 1,
                                                             "qualified_members": 1}, path)

        def execute(self, sql, params=()):
            outer = self

            class R:
                def fetchone(self_):
                    return outer.row
            return R()
    got = sr._window_qualification(Conn("P2", 0.5), CHART_ID, GEN, [{"window_id": "w"}])
    assert got[0]["vedha_moon_obstruction_scope"] == "excluding_on_demand_moon_obstruction"
    for path, value in (("P2", None), ("P3", 0.5), ("P4", 0.5)):          # unqualified P2 / other paths: none
        assert sr._window_qualification(Conn(path, value), CHART_ID, GEN, [{"window_id": "w"}])[0][
            "vedha_moon_obstruction_scope"] is None
