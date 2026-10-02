"""A5.3 — per-class version SELECTION and supersession (Codex round 8, R8-2).

The bound CATALOGUE (every sealed `(path, version)`) is not the SELECTION (the one version of each path a class's
search runs under). 1206: at most one `included` version per class and path
(`multiple_included_versions`); a `superseded_by_version` pin asserts that ANOTHER version of the path carries the
search (`superseded_without_included_version`). The planner and the independent verifier derive the same
dispositions; a historical replay reuses the ORIGINAL selection stored with the inventory.

Cases (the review's): old-only, old+new, successor included, successor withheld, unknown-H, held P5.
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import inventory_verifier as ver
from services.gochara_kernel import rule_registry as rr
from services.gochara_rules import registry as rules_registry

from ._bound_1_1_0 import bind_successors
from .test_a53_inventory import (CHART, CHART_ID, DASHA, FULL, H0, H1, H_UNKNOWN_EXCL, P5_EXCL,  # noqa: F401
                                 _am5_dsn, _boot, _write, am5)

P3_BOTH = [("P3", "1.0.0"), ("P3", "1.1.0")]
VCHART = {"lagna": CHART["lagna_deg"], "natal": {k.lower(): v for k, v in CHART["natal"].items()}}
V_P5 = {"p5": {"reason": "tier_withheld_by_ruling", "basis": "ruling:M20261001T121451-1a8d",
               "ruling_ref": "M20261001T121451-1a8d"}}
V_H = {"reason": "inputs_unavailable", "basis": "ruling:TEST-H-UNKNOWN", "ruling_ref": "TEST-H-UNKNOWN"}
UNKNOWN_H_CLASS = "business_launch"


def _plan(sealed, selected=None, cls="marriage", **kw):
    kw.setdefault("path_exclusions", {})
    return inv.plan_class_inventory(event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=sealed,
                                    selected_versions=selected, capability=FULL, **kw)


def _pins(plan):
    return {(p.path_id, p.rule_version): p for p in plan.pins}


def _included(plan, path):
    return sorted(p.rule_version for p in plan.pins if p.path_id == path and p.disposition == "included")


def _view(pin):
    """A planner pin / a verifier pin in ONE comparable shape."""
    if isinstance(pin, dict):
        return (pin["path"], pin["version"], pin["disposition"], pin["reason"], pin["ruling"], pin["basis"],
                tuple(sorted(pin["obligations"])))
    return (pin.path_id.lower(), pin.rule_version.lower(), pin.disposition, pin.exclusion_reason or "",
            pin.ruling_ref or "", pin.basis or "", tuple(sorted(o.canonical_bytes for o in pin.obligations)))


def _both(sealed, selected, cls="marriage", planner_excl=None, verifier_excl=None, **kw):
    """The planner's pins and the independent verifier's, in the same shape — they must be equal."""
    plan = _plan(sealed, selected, cls=cls, path_exclusions=planner_excl or {}, **kw)
    vpins = ver.derive_class_pins(cls, VCHART, sealed, selected_versions=selected,
                                  path_exclusions=verifier_excl if verifier_excl is not None else {},
                                  h_unknown_exclusion=V_H)
    return plan, vpins


# ── the planner: one included version per path, every sealed version accounted ──────────────────────────

def test_old_only_catalogue_is_unchanged_one_included_pin():
    plan = _plan([("P3", "1.0.0")])
    assert _included(plan, "P3") == ["1.0.0"] and len(plan.pins) == 1
    assert plan.obligations and {o.rule_version for o in plan.obligations} == {"1.0.0"}


def test_old_plus_new_with_the_successor_selected_supersedes_the_old_version():
    plan = _plan(P3_BOTH, {"P3": "1.1.0"})
    assert _included(plan, "P3") == ["1.1.0"]                           # at most ONE included version
    old = _pins(plan)[("P3", "1.0.0")]
    assert (old.disposition, old.exclusion_reason, old.ruling_ref) == ("excluded", "superseded_by_version", None)
    assert old.basis == inv.supersession_basis("P3", "1.0.0", "1.1.0") and old.obligations == ()
    # the obligations (and their ids) are the SELECTED version's only — nothing is searched twice
    assert plan.obligations and {o.rule_version for o in plan.obligations} == {"1.1.0"}
    assert len({o.ob_id for o in plan.obligations}) == len(plan.obligations)


def test_old_plus_new_with_the_old_selected_needs_a_composite_ruling_for_the_withheld_successor():
    with pytest.raises(inv.InventoryBlocked, match="neither the selected"):
        _plan(P3_BOTH, {"P3": "1.0.0"})
    withheld = {("P3", "1.1.0"): inv.Exclusion("tier_withheld_by_ruling", "ruling:ST-P3-1-1-WITHHELD",
                                                "ST-P3-1-1-WITHHELD")}
    plan = _plan(P3_BOTH, {"P3": "1.0.0"}, path_exclusions=withheld)
    assert _included(plan, "P3") == ["1.0.0"]
    new = _pins(plan)[("P3", "1.1.0")]
    assert (new.disposition, new.exclusion_reason, new.ruling_ref) == (
        "excluded", "tier_withheld_by_ruling", "ST-P3-1-1-WITHHELD")
    # the composite key applies to THAT version only — the old version keeps its search
    assert {o.rule_version for o in plan.obligations} == {"1.0.0"}


def test_a_catalogue_with_several_versions_and_no_selection_is_refused_never_searched_twice():
    with pytest.raises(inv.InventoryBlocked, match="no selected version"):
        _plan(P3_BOTH, None)
    with pytest.raises(inv.InventoryBlocked, match="not sealed"):
        _plan(P3_BOTH, {"P3": "7.7.7"})


def test_a_supersession_needs_the_APPROVED_successor_to_be_the_selected_included_version(monkeypatch):
    approved = dict(rules_registry.SUPERSEDED_PATHS)
    approved[("P3", "1.0.0")] = dict(approved[("P3", "1.0.0")], superseded_by=("P3", "1.2.0"))
    monkeypatch.setattr(rules_registry, "SUPERSEDED_PATHS", approved)
    with pytest.raises(inv.InventoryBlocked, match="neither the selected"):
        _plan(P3_BOTH, {"P3": "1.1.0"})                                   # 1.1.0 is not 1.0.0's approved successor


def test_a_class_with_unknown_h_excludes_every_version_of_the_h_dependent_paths_with_the_ruling():
    plan = _plan(P3_BOTH, {"P3": "1.1.0"}, cls=UNKNOWN_H_CLASS, h_unknown_exclusion=H_UNKNOWN_EXCL)
    assert _included(plan, "P3") == []
    for key in P3_BOTH:
        pin = _pins(plan)[key]
        assert (pin.disposition, pin.exclusion_reason, pin.ruling_ref) == (
            "excluded", "inputs_unavailable", "TEST-H-UNKNOWN")          # never `superseded` with no superseder
    assert not plan.obligations


def test_held_p5_excludes_every_version_with_the_hold_ruling_and_nothing_is_superseded():
    sealed = [("P5", "1.0.0"), ("P5", "1.1.0")]
    for selected in ({"P5": "1.0.0"}, {"P5": "1.1.0"}):
        plan = _plan(sealed, selected, path_exclusions={"P5": P5_EXCL})
        assert _included(plan, "P5") == []
        assert {(p.disposition, p.exclusion_reason) for p in plan.pins} == {("excluded", "tier_withheld_by_ruling")}


def test_a_selected_computed_empty_successor_is_not_a_superseder(monkeypatch):
    """H known but the qualified set empty: no version is `included`, so none may be `superseded` — each is
    accounted exactly as it would be (computed_empty)."""
    monkeypatch.setattr(inv, "enumerate_edges", lambda *a, **k: [])
    plan = _plan(P3_BOTH, {"P3": "1.1.0"})
    assert {(p.rule_version, p.disposition, p.exclusion_reason) for p in plan.pins} == {
        ("1.0.0", "computed_empty", None), ("1.1.0", "computed_empty", None)}


def test_p1_and_p4_follow_the_same_selection():
    plan = _plan([("P1", "1.0.0"), ("P4", "1.0.0"), ("P4", "1.1.0")], {"P4": "1.1.0", "P1": "1.0.0"},
                 dasha_rows=DASHA)
    assert _included(plan, "P4") == ["1.1.0"] and _included(plan, "P1") == ["1.0.0"]
    assert _pins(plan)[("P4", "1.0.0")].exclusion_reason == "superseded_by_version"


# ── the independent verifier derives the SAME dispositions ───────────────────────────────────────────────

@pytest.mark.parametrize("name,sealed,selected,cls,planner_excl,verifier_excl", [
    ("old-only", [("P3", "1.0.0")], None, "marriage", {}, {}),
    ("successor included", P3_BOTH, {"P3": "1.1.0"}, "marriage", {}, {}),
    ("successor withheld", P3_BOTH, {"P3": "1.0.0"}, "marriage",
     {("P3", "1.1.0"): inv.Exclusion("tier_withheld_by_ruling", "ruling:R-W", "R-W")},
     {("p3", "1.1.0"): {"reason": "tier_withheld_by_ruling", "basis": "ruling:R-W", "ruling_ref": "R-W"}}),
    ("unknown-H", P3_BOTH, {"P3": "1.1.0"}, UNKNOWN_H_CLASS, {}, {}),
    ("held P5", [("P5", "1.0.0"), ("P5", "1.1.0")], {"P5": "1.1.0"}, "marriage", {"P5": P5_EXCL}, V_P5),
    ("P3+P4 successors", P3_BOTH + [("P4", "1.0.0"), ("P4", "1.1.0")], {"P3": "1.1.0", "P4": "1.1.0"},
     "marriage", {}, {}),
])
def test_the_verifier_derives_the_planners_dispositions_independently(name, sealed, selected, cls,
                                                                     planner_excl, verifier_excl):
    plan, vpins = _both(sealed, selected, cls, planner_excl, verifier_excl, h_unknown_exclusion=H_UNKNOWN_EXCL)
    assert sorted(map(_view, plan.pins)) == sorted(map(_view, vpins)), name


def test_the_verifier_refuses_what_it_cannot_derive_rather_than_picking_a_version():
    with pytest.raises(ver.Unverifiable, match="neither selected"):
        ver.derive_class_pins("marriage", VCHART, P3_BOTH, selected_versions={"p3": "1.0.0"},
                              path_exclusions={}, h_unknown_exclusion=V_H)
    with pytest.raises(ver.Unverifiable, match="no selection"):
        ver.derive_class_pins("marriage", VCHART, P3_BOTH, selected_versions=None,
                              path_exclusions={}, h_unknown_exclusion=V_H)
    with pytest.raises(ver.Unverifiable, match="not sealed"):
        ver.derive_class_pins("marriage", VCHART, P3_BOTH, selected_versions={"p3": "9.9.9"},
                              path_exclusions={}, h_unknown_exclusion=V_H)


def test_the_verifiers_supersession_table_is_its_own_not_the_registrys():
    import ast
    import inspect
    imported = {n.module for n in ast.walk(ast.parse(inspect.getsource(ver))) if isinstance(n, ast.ImportFrom)}
    assert not any("registry" in (m or "") or "inventory" == (m or "").split(".")[-1] for m in imported)
    assert ver._SUPERSEDED == {("p2", "1.0.0"): "1.1.0", ("p3", "1.0.0"): "1.1.0",
                               ("p4", "1.0.0"): "1.1.0", ("p5", "1.0.0"): "1.1.0"}
    # ... and it agrees with what the registry actually approves (so a new approval cannot go unmirrored)
    approved = {(p.lower(), v): tuple(row["superseded_by"])[1]
                for (p, v), row in rules_registry.SUPERSEDED_PATHS.items()}
    assert approved == ver._SUPERSEDED


# ── the selection API ────────────────────────────────────────────────────────────────────────────────

def test_the_default_selection_is_the_1_0_0_set_and_never_the_first_bound_version(monkeypatch):
    assert rr.selected_versions_for("marriage") == {p: "1.0.0" for p in ("P1", "P2", "P3", "P4", "P5")}
    bind_successors(monkeypatch)
    # binding successors into the CATALOGUE does not change what any class searches
    assert rr.selected_path_version("marriage", "P3") == "1.0.0"
    monkeypatch.setattr(rr, "SELECTED_PATH_REFS", tuple(("P3", "1.1.0") if p == "P3" else (p, v)
                                                        for p, v in rr.SELECTED_PATH_REFS))
    assert rr.selected_path_version("marriage", "P3") == "1.1.0" and rr.selected_path_version("marriage", "P4") == "1.0.0"
    # a per-class override
    monkeypatch.setitem(rr.CLASS_SELECTION_OVERRIDES, ("career", "P3"), "1.0.0")
    assert rr.selected_path_version("career", "P3") == "1.0.0" and rr.selected_path_version("marriage", "P3") == "1.1.0"
    with pytest.raises(KeyError):
        rr.selected_path_version("marriage", "P9")


def test_a_selection_outside_the_catalogue_or_twice_is_refused(monkeypatch):
    monkeypatch.setattr(rr, "SELECTED_PATH_REFS", rr.SELECTED_PATH_REFS + (("P3", "1.1.0"),))
    with pytest.raises(ValueError, match="appears twice|not in the bound catalogue"):
        rr._membership_consistent()
    monkeypatch.setattr(rr, "SELECTED_PATH_REFS", (("P3", "1.1.0"),))
    with pytest.raises(ValueError, match="not in the bound catalogue"):
        rr._membership_consistent()


# ── on the REAL 1206 schema: the detectors accept the new plan and reject the old behaviour ──────────────

def _violations(conn, generation):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        return {r[1] for r in conn.execute(
            "SELECT * FROM public.ka_gochara_search_completeness_violations(%s::uuid, %s)",
            (CHART_ID, generation)).fetchall()}


def test_1206_accepts_the_supersession_plan_and_flags_two_included_versions(am5, monkeypatch):
    bind_successors(monkeypatch)
    store, sky, _ = _boot(am5, "5.31")
    sealed = store.sealed_rule_paths()
    assert ("P3", "1.0.0") in sealed and ("P3", "1.1.0") in sealed       # the real catalogue holds both
    paths = [p for p in sealed if p[0] in ("P3", "P4")]
    good = _plan(paths, {"P3": "1.1.0", "P4": "1.1.0"})
    _write(am5, store, sky, "5.31", good)
    found = _violations(am5, "5.31")
    assert not {"multiple_included_versions", "superseded_without_included_version"} & found, found
    rows = am5.execute("SELECT path_id, rule_version, disposition, exclusion_reason, ruling_ref FROM"
                       " public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = '5.31'"
                       " ORDER BY path_id, rule_version", (CHART_ID,)).fetchall()
    assert rows == [("P3", "1.0.0", "excluded", "superseded_by_version", None),
                    ("P3", "1.1.0", "included", None, None),
                    ("P4", "1.0.0", "excluded", "superseded_by_version", None),
                    ("P4", "1.1.0", "included", None, None)]
    # the OLD behaviour (every sealed version included) is exactly what 1206 rejects
    two = inv.ClassInventory(event_class="marriage", horizon=good.horizon, pins=tuple(
        inv.PinPlan(p.path_id, p.rule_version, "included", _plan([(p.path_id, p.rule_version)]).obligations)
        for p in good.pins), intervals=())
    _write(am5, store, sky, "5.31", two)
    assert "multiple_included_versions" in _violations(am5, "5.31")


def test_the_verifier_replays_the_stored_selection_and_matches_the_stored_digest(am5, monkeypatch):
    bind_successors(monkeypatch)
    store, sky, _ = _boot(am5, "5.32")
    sealed = [p for p in store.sealed_rule_paths() if p[0] in ("P3", "P4", "P5")]
    plan = _plan(sealed, {"P3": "1.1.0", "P4": "1.1.0", "P5": "1.1.0"}, path_exclusions={"P5": P5_EXCL})
    _write(am5, store, sky, "5.32", plan)
    stored = ver.stored_selection(am5, chart_id=CHART_ID, generation="5.32", event_class="marriage")
    assert stored == {"p3": "1.1.0", "p4": "1.1.0"}                       # P5 held: nothing included
    res = ver.rederive_inventory_digest(am5, chart_id=CHART_ID, generation="5.32", event_class="marriage",
                                        sealed_paths=sealed, path_exclusions=V_P5, h_unknown_exclusion=V_H,
                                        selected_versions=stored)
    assert res["digest"] == store.finalised_class_facts(CHART_ID, "5.32", "marriage")["inventory_digest"]
    # historical replay: a later change of the CONFIGURATION never re-selects — the stored selection is reused
    monkeypatch.setattr(rr, "SELECTED_PATH_REFS", tuple(("P3", "1.0.0") if p == "P3" else (p, v)
                                                        for p, v in rr.SELECTED_PATH_REFS))
    assert rr.selected_path_version("marriage", "P3") == "1.0.0"          # today's configuration differs ...
    again = ver.rederive_inventory_digest(am5, chart_id=CHART_ID, generation="5.32", event_class="marriage",
                                          sealed_paths=sealed, path_exclusions=V_P5, h_unknown_exclusion=V_H,
                                          selected_versions=ver.stored_selection(
                                              am5, chart_id=CHART_ID, generation="5.32",
                                              event_class="marriage"))
    assert again["digest"] == res["digest"]                                # ... the replay does not follow it
    # a verifier told a selection the stored inventory did NOT use cannot vouch for it
    with pytest.raises(ver.Unverifiable, match="neither selected"):
        ver.rederive_inventory_digest(am5, chart_id=CHART_ID, generation="5.32", event_class="marriage",
                                      sealed_paths=sealed, path_exclusions=V_P5, h_unknown_exclusion=V_H,
                                      selected_versions={"p3": "1.0.0", "p4": "1.1.0", "p5": "1.1.0"})


def test_the_writers_verify_step_refuses_a_stored_selection_that_drifted_from_the_configuration():
    import inspect
    src = inspect.getsource(writer_mod.GocharaV5Writer)
    assert "stored_selection" in src and "selection drifted" in src


# ═══ R8-4: the independent P2 inventory derivation ═══════════════════════════════════════════════════════

def test_the_verifiers_p2_tables_equal_the_rule_modules_and_it_imports_neither():
    from services.gochara_rules import favourable_houses as fh
    from services.gochara_rules.registry import CLASS_BY_NAME
    assert ver._POLARITY == {k: v["polarity"] for k, v in CLASS_BY_NAME.items()}
    assert {g: tuple(sorted(h["houses"])) for g, h in {k.lower(): v for k, v in
                                                       fh.FAVOURABLE_HOUSES_FROM_MOON.items()}.items()} == ver._FAVOURABLE


@pytest.mark.parametrize("cls", sorted(ver._POLARITY))
def test_p2_obligations_the_planner_and_the_verifier_agree_for_every_class(cls):
    if cls == "birth_anchor":
        pytest.skip("excluded from enumeration entirely (O-CF-N6)")
    plan = inv.plan_class_inventory(event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=[("P2", "1.0.0")],
                                    capability=FULL, path_exclusions={})
    pin = ver.derive_path_pin(cls, VCHART, "P2", "1.0.0", path_exclusions={}, h_unknown_exclusion=V_H)
    (mine,) = plan.pins
    assert _view(mine) == _view(pin), cls
    polarity = ver._POLARITY[cls]
    assert (mine.disposition == "included") == (polarity in ("gain", "adverse"))     # anchor / non-adverse: empty


def test_a_p2_obligation_set_that_the_verifier_does_not_derive_is_caught_by_the_digest():
    plan = _plan([("P2", "1.0.0")], {"P2": "1.0.0"})
    pin = ver.derive_path_pin("marriage", VCHART, "P2", "1.0.0", path_exclusions={}, h_unknown_exclusion=V_H)
    assert len(pin["obligations"]) == len(plan.obligations) > 0
    tampered = dict(pin, obligations=pin["obligations"][:-1])
    assert _view(tampered) != _view(plan.pins[0])
