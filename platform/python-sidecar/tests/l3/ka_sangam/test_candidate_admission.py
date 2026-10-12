"""Operational conclusions require selection-safe, covered evidence (review F1/F2)."""
from dataclasses import replace
import pytest
from services.ka_sangam.jury import Node, Opinion, Use
from services.kala_core.measure import Interval
from tests.l3.ka_sangam.test_jury_writer import api, fixture_input, T, H


def unsupported(mode, event_class="career"):
    v = fixture_input(event_class)
    if mode == "selected":
        v["nodes"] = (Node("p", frozenset({"selected:contact"})),)
        v["opinions"] = (replace(v["opinions"][0], roots=frozenset({"selected:contact"})),)
    elif mode == "conditioned":
        v["uses"] += (replace(v["uses"][0], role="conditions"),)
    elif mode == "testimony":
        v["uses"] = (replace(v["uses"][0], testimony=True),)
    elif mode == "outside_coverage":
        v["groups"] = tuple(replace(g, coverage=(Interval(T+20,T+30),)) if g.group_id == "G-P" else g for g in v["groups"])
    elif mode == "selection_ancestry":
        v["uses"] += (Use("p", "G-P", H, "selects", frozenset({"jaimini_cara"})),)
        from tests.l3.ka_sangam.test_jury_qualification import complete_method
        v["jaimini"] = complete_method(v)
    return v


@pytest.mark.parametrize("mode", ["selected", "conditioned", "testimony", "outside_coverage"])
def test_no_operational_contest_without_admitted_support(mode):
    v = unsupported(mode)
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    r = api().compute(api().ClassInput.model_validate(v))
    assert r.agreement.witness_signature == ()
    assert r.contests == (), f"{mode}: {len(r.contests)} unsupported contest"


@pytest.mark.parametrize("mode", ["selected", "conditioned", "testimony", "outside_coverage", "selection_ancestry"])
def test_no_joint_turning_point_without_admitted_support(mode):
    values = [api().ClassInput.model_validate(unsupported(mode, c)) for c in ("career", "family")]
    if mode != "selection_ancestry":
        assert all(api().compute(v).agreement.witness_signature == () for v in values)
    else:
        assert all("G-J" not in api().compute(v).agreement.witness_signature for v in values)
    points = api().joint_turning_points(values)
    assert points == (), f"{mode}: {len(points)} unsupported turning point"


def test_independent_supported_control():
    v = fixture_input()
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    r = api().compute(api().ClassInput.model_validate(v))
    assert r.agreement.witness_signature == ("G-P",)
    assert len(r.contests) == 1
    values = [api().ClassInput.model_validate(fixture_input(c)) for c in ("career", "family")]
    assert len(api().joint_turning_points(values)) == 1


def test_no_operational_sequence_from_selected_root():
    v = unsupported("selected")
    v["opinions"] += (replace(v["opinions"][0], interval=Interval(T+5,T+15), conclusion="adverse"),)
    r = api().compute(api().ClassInput.model_validate(v))
    assert r.agreement.witness_signature == ()
    assert r.sequences == ()


def test_selection_ancestry_outside_anchor_roots_is_still_blocked():
    v = fixture_input()
    v["anchor"] = v["anchor"].model_copy(update={"used_for_selection": ("selected:contact", "judge:other")})
    r = api().compute(api().ClassInput.model_validate(v))
    assert r.agreement.witness_signature == (), "explicit upstream selection root gained corroboration"
    assert r.support == ()


def partial_coverage(event_class="career"):
    v = fixture_input(event_class)
    v["groups"] = tuple(replace(g, coverage=(Interval(T+5, T+8),))
                        if g.group_id == "G-P" else g for g in v["groups"])
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    return api().ClassInput.model_validate(v)


def test_contest_is_clipped_to_admitted_coverage():
    r = api().compute(partial_coverage())
    assert tuple(c.interval for c in r.contests) == (Interval(T+5, T+8),)


def test_persisted_support_is_clipped_to_admitted_coverage():
    r = api().compute(partial_coverage())
    assert tuple(s.interval for s in r.support) == (Interval(T+5, T+8),)


def test_joint_turning_point_is_clipped_to_admitted_coverage():
    values = [partial_coverage(c) for c in ("career", "family")]
    assert tuple(p.interval for p in api().joint_turning_points(values)) == (Interval(T+5, T+8),)


def test_all_opinion_roots_must_have_support_at_the_same_time():
    v = fixture_input()
    v["nodes"] += (Node("q", frozenset({"judge:q"})),)
    v["uses"] += (Use("q", "G-P", Interval(T+5, T+15), "corroborates"),)
    opinion = replace(v["opinions"][0], roots=frozenset({"judge:other", "judge:q"}))
    v["opinions"] = (opinion, replace(opinion, conclusion="adverse"))
    r = api().compute(api().ClassInput.model_validate(v))
    assert tuple(c.interval for c in r.contests) == (Interval(T+5, T+10),)


def test_explanatory_use_does_not_admit_operational_opinion():
    v = fixture_input()
    v["uses"] = (replace(v["uses"][0], role="explains"),)
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    r = api().compute(api().ClassInput.model_validate(v))
    assert r.contests == ()


def test_opinion_cannot_borrow_support_from_another_group():
    v = fixture_input()
    v["opinions"] = (replace(v["opinions"][0], groups=frozenset({"G-P", "G-T"})),)
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    r = api().compute(api().ClassInput.model_validate(v))
    assert r.contests == ()


def test_disconnected_coverage_does_not_fill_the_gap_in_a_contest():
    v = fixture_input()
    v["groups"] = tuple(replace(g, coverage=(Interval(T, T+3), Interval(T+7, T+10)))
                        if g.group_id == "G-P" else g for g in v["groups"])
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    r = api().compute(api().ClassInput.model_validate(v))
    assert tuple(c.interval for c in r.contests) == (Interval(T, T+3), Interval(T+7, T+10))


def test_operational_admission_mutant_fails_selected_root_oracle(monkeypatch):
    from services.ka_sangam.jury.contests import _canonical
    monkeypatch.setattr(api(), "_supported_opinions", lambda opinions, support: _canonical(opinions))
    with pytest.raises(AssertionError):
        test_no_operational_contest_without_admitted_support("selected")


def test_missing_upstream_selection_root_mutant_fails_oracle(monkeypatch):
    import ast
    from pathlib import Path
    module = api()
    source = Path(module.__file__).read_text()
    target = "*value.anchor.roots.fact_ids, *value.anchor.used_for_selection"
    assert source.count(target) == 1
    tree = ast.parse(source.replace(target, "*value.anchor.roots.fact_ids"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_class_evidence")
    scope = dict(module.__dict__)
    exec(compile(ast.Module(body=[function], type_ignores=[]), module.__file__, "exec"), scope)
    monkeypatch.setattr(module, "_class_evidence", scope["_class_evidence"])
    with pytest.raises(AssertionError):
        test_selection_ancestry_outside_anchor_roots_is_still_blocked()
