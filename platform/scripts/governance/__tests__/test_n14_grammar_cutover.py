"""Synthetic, source-bound N-14 geometry and supported-consumer cutover controls."""
from __future__ import annotations

import ast
import __future__
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[4]
SIDECAR = ROOT / "platform/python-sidecar"
PRIMITIVES = SIDECAR / "services/gochara_grammar/primitives.py"
ENGINE = SIDECAR / "services/gochara_v3/engine.py"


def _tree(path):
    return ast.parse(path.read_bytes())


def _literal(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        else:
            continue
        if isinstance(target, ast.Name) and target.id == name:
            return ast.literal_eval(node.value)
    raise AssertionError(name)


def _grammar(*, historical=False):
    tree = _tree(PRIMITIVES)
    convention = {}
    exec(compile((SIDECAR / "services/gochara_kernel/convention.py").read_bytes(), "<exact governed convention>", "exec"), convention)
    vocabulary = {}
    exec(compile((SIDECAR / "brahmagyan/graha_vocabulary.py").read_bytes(), "<exact vocabulary>", "exec"), vocabulary)
    calls = []
    def event(degree):
        return SimpleNamespace(event_jd=1.5, event_datetime_ist="fixture-time", extra={"aspect_deg": degree}, orb_at_event_deg=0.0, orb_strength=1.0, exact_longitude_deg=0.0)
    def aspects(swe, planet, target, degrees, *args):
        calls.append(("aspect", planet, tuple(degrees)))
        return [event(d) for d in degrees]
    def ingress(swe, planet, sign, *args):
        calls.append(("ingress", planet, sign))
        return [event(None)]
    context = {"ALL_GRAHAS": _literal(tree, "ALL_GRAHAS"), "_DEFAULT_DRISHTI_DEG": [180.0],
               "SPECIAL_DRISHTI_DEG": convention["SPECIAL_DRISHTI_DEG"],
               "norm_graha": vocabulary["norm_graha"], "SIGNS": [f"s{i}" for i in range(12)],
               "find_aspect_events": aspects, "find_ingress_events": ingress,
               "_shortest_arc_diff": lambda x, y: x-y, "_jd_to_ist_iso": lambda *args: "fixture-time",
               "_get_planet_pos": lambda *args: (0.0, 0.0),
               "ConfigurationSentence": lambda **kwargs: SimpleNamespace(**kwargs),
               "C": SimpleNamespace(GRAHA_DRISHTI_BPHS_26="fixture-citation", GRAHA_DRISHTI_RASI_BPHS_26="fixture-rasi"),
               "logger": SimpleNamespace(debug=lambda *args: None)}
    if historical:
        # Exact old values are an independent frozen synthetic nodal golden,
        # not the current convention or a new supported runtime mode.
        context["SPECIAL_DRISHTI_DEG"] = {"Mars": [90.0,180.0,210.0], "Jupiter": [120.0,180.0,240.0],
            "Saturn": [60.0,180.0,270.0], "Rahu": [120.0,180.0,240.0], "Ketu": [120.0,180.0,240.0]}
    names = {"_sign_index", "_signs_casting_drishti_onto", "_offset_sign", "_sign_of_longitude", "_fact_id",
             "degree_contact", "drishti_contact", "_drishti_contact_point", "_rasi_drishti_sentence", "_drishti_contact_rasi"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if historical:
        offsets = ast.parse("def _drishti_house_offsets(planet):\n return sorted({int(round(d/30.0))+1 for d in SPECIAL_DRISHTI_DEG.get(planet,_DEFAULT_DRISHTI_DEG)})").body[0]
        # Bind the exact current consumer shape to old table for independent
        # non-node parity. Real old-body replay is additionally run by the owner.
        angle = ast.parse("def _governed_drishti_degrees(planet):\n return SPECIAL_DRISHTI_DEG.get(planet,_DEFAULT_DRISHTI_DEG)").body[0]
        nodes += [offsets, angle]
    else:
        nodes += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"_drishti_house_offsets", "_governed_drishti_degrees"}]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), "<exact geometry functions>", "exec", flags=__future__.annotations.compiler_flag), context)
    return context, calls


def _target(point=True):
    return SimpleNamespace(target_longitude_deg=0.0 if point else None, target_sign=None if point else "s0",
                           event_class="fixture-class", target_type="fixture-type", target_ref="fixture-target")


@pytest.mark.parametrize("node", ["Rahu", "Ketu", "rahu", "ketu", "RAHU", "KETU", "RAH_MEAN", "KET_MEAN"])
def test_normalized_nodes_never_cast_point_or_rasi_drishti(node):
    new, calls = _grammar()
    assert new["_drishti_house_offsets"](node) == []
    for point in [True, False]:
        assert new["drishti_contact"](None, "fixture-chart", _target(point), 1.0, 2.0, planets=[node]) == []
    assert calls == []


@pytest.mark.parametrize("body", ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"])
def test_nonnode_point_and_rasi_golden_is_unchanged(body):
    old, _ = _grammar(historical=True)
    new, _ = _grammar()
    for point in [True, False]:
        before = old["drishti_contact"](None, "fixture-chart", _target(point), 1.0, 2.0, planets=[body])
        after = new["drishti_contact"](None, "fixture-chart", _target(point), 1.0, 2.0, planets=[body])
        assert [vars(row) for row in before] == [vars(row) for row in after]


@pytest.mark.parametrize("node", ["Rahu", "Ketu"])
def test_preserved_old_nodal_golden_is_explicit_delta_not_rewritten(node):
    old, _ = _grammar(historical=True)
    new, _ = _grammar()
    before = old["drishti_contact"](None, "fixture-chart", _target(), 1.0, 2.0, planets=[node])
    assert [row.detail["aspect_deg"] for row in before] == [120.0, 180.0, 240.0]
    assert new["drishti_contact"](None, "fixture-chart", _target(), 1.0, 2.0, planets=[node]) == []


def test_conjunction_still_supports_nodes():
    new, _ = _grammar()
    for node in ["Rahu", "Ketu"]:
        assert new["degree_contact"](None, "fixture-chart", _target(), 1.0, 2.0, planets=[node])


def test_configuration_activity_actual_dispatch_uses_governed_primitive():
    from contextlib import nullcontext
    new, _ = _grammar()
    # Keep real degree/drishti functions; unrelated scoped primitives are inert.
    for name in ["sign_ingress", "nakshatra_ingress_tara", "kakshya_cell_crossing", "station_retro_loop", "eclipse_degree", "gochara_vedha_pair"]:
        new[name] = lambda *args, **kwargs: []
    tree = _tree(SIDECAR / "services/gochara_intensity/configuration_activity.py")
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "gather_configuration_sentences")
    context = {"P": SimpleNamespace(**new), "SBC": SimpleNamespace(find_sarvatobhadra_vedha_states=lambda *args, **kw: []),
               "savepoint_scope": lambda *args: nullcontext(), "logger": SimpleNamespace(info=lambda *args: None)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), "<exact activity dispatch>", "exec", flags=__future__.annotations.compiler_flag), context)
    rows = context["gather_configuration_sentences"](None, object(), "fixture-chart", [_target()], 1.0, 2.0)
    assert not [row for row in rows if row.primitive == "drishti_contact" and row.transit_planet in {"Rahu", "Ketu"}]
    assert {row.transit_planet for row in rows if row.primitive == "degree_contact"} >= {"Rahu", "Ketu"}


def test_default_and_retired_enabled_are_explicit_at_empty_batch_and_gather():
    tree = _tree(ENGINE)
    assert _literal(tree, "_NODAL_DRISHTI_DEFAULT") == "removed"
    assert _literal(tree, "_NODAL_DRISHTI_MODES") == ("removed",)
    for name in ["evaluate_lambda_vector", "_gather_sentences_no_db"]:
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        body = fn.body[1:] if isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant) else fn.body
        guard = body[0]
        assert isinstance(guard, ast.If)
        context = {"nodal_drishti": "enabled", "_NODAL_DRISHTI_MODES": ("removed",)}
        with pytest.raises(ValueError):
            exec(compile(ast.Module(body=[guard], type_ignores=[]), "<exact retired-mode guard>", "exec"), context)
