"""Pure source-bound checks for the registered Saṅgam window-composition facade."""
from __future__ import annotations

import ast
import copy
import math
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[4]
SIDECAR = ROOT / "platform/python-sidecar"
WRITER = SIDECAR / "pipeline/orchestrator/writers/ka_sangam.py"
OWNER = SIDECAR / "services/ka_sangam/window_generation.py"
FIELDS = {
    "mode_a_search", "mode_b_sweep", "mode_c_subsystem_period", "mode_d_av_bindhu",
    "_date_to_jd", "_mode_d_carrier_index", "_resolved_target_longitude",
    "_target_blank_note", "apply_trigger_suppression", "_SIGN_NAME_TO_IDX",
    "SIGNAL_UNRESOLVED", "TARGET_UNRESOLVED", "logger",
}
ARGS = ["self", "pred_dicts", "horizon_start", "horizon_end", "dasha_kala_service",
        "gochara_service", "chart_id", "native_ctx", "keepalive", "enrichment_context",
        "muhurta_service", "mode_d"]


def _method(tree):
    legacy = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                  and node.name == "_LegacyKaSangamWriter")
    return next(node for node in legacy.body if isinstance(node, ast.FunctionDef)
                and node.name == "_generate_windows")


def _boundary(writer_text=None, owner_text=None):
    writer = ast.parse(WRITER.read_text() if writer_text is None else writer_text)
    owner = ast.parse(OWNER.read_text() if owner_text is None else owner_text)
    imports = [node for node in writer.body if isinstance(node, ast.ImportFrom)
               and node.module == "services.ka_sangam.window_generation"]
    assert len(imports) == 1
    assert [(name.name, name.asname) for name in imports[0].names] == [
        ("WindowBindings", None), ("generate_windows", None)]
    method = _method(writer)
    assert [arg.arg for arg in method.args.args] == ARGS
    assert [ast.literal_eval(value) for value in method.args.defaults] == [None, None, None, True]
    assert len(method.body) == 3
    publish = method.body[1]
    assert isinstance(publish, ast.FunctionDef) and publish.name == "publish_target_blanks"
    assert [arg.arg for arg in publish.args.args] == ["blanks"]
    assert len(publish.body) == 1 and isinstance(publish.body[0], ast.Assign)
    assert ast.unparse(publish.body[0]) == "self._target_blanks = blanks"
    result = method.body[2]
    assert isinstance(result, ast.Return) and isinstance(result.value, ast.Call)
    assert isinstance(result.value.func, ast.Name) and result.value.func.id == "generate_windows"
    assert result.value.args == []
    keywords = {keyword.arg: keyword.value for keyword in result.value.keywords}
    assert set(keywords) == set(ARGS[1:]) | {"bindings", "publish_target_blanks"}
    for name in ARGS[1:]:
        assert isinstance(keywords[name], ast.Name) and keywords[name].id == name
    assert ast.unparse(keywords["bindings"]) == "_SangamWindowBindings()"
    assert ast.unparse(keywords["publish_target_blanks"]) == "publish_target_blanks"
    adapter = next(node for node in writer.body if isinstance(node, ast.ClassDef)
                   and node.name == "_SangamWindowBindings")
    methods = [node for node in adapter.body if isinstance(node, ast.FunctionDef)]
    assert {node.name for node in methods} == FIELDS and len(methods) == len(FIELDS)
    assert all(isinstance(node, (ast.FunctionDef, ast.Expr)) for node in adapter.body)
    for node in methods:
        assert [ast.unparse(value) for value in node.decorator_list] == ["property"]
        assert len(node.body) == 1 and isinstance(node.body[0], ast.Return)
        assert isinstance(node.body[0].value, ast.Name) and node.body[0].value.id == node.name
    assert {node.module for node in owner.body if isinstance(node, ast.ImportFrom)} == {
        "__future__", "collections.abc", "datetime", "typing"}
    assert [name.name for node in owner.body if isinstance(node, ast.Import) for name in node.names] == ["logging"]
    for node in ast.walk(owner):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"cursor", "execute", "executemany", "commit", "rollback", "close"}
        if isinstance(node, ast.Name):
            assert node.id not in {"__import__", "eval", "exec", "globals", "locals", "getattr", "setattr"}
    generate = next(node for node in owner.body if isinstance(node, ast.FunctionDef)
                    and node.name == "generate_windows")
    assert [arg.arg for arg in generate.args.args] == ARGS[1:]
    assert [arg.arg for arg in generate.args.kwonlyargs] == ["bindings", "publish_target_blanks"]
    calls = [node for node in ast.walk(generate) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
             and node.func.value.id == "bindings" and node.func.attr in {"mode_a_search", "mode_b_sweep"}]
    assert len(calls) == 2 and {node.func.attr for node in calls} == {"mode_a_search", "mode_b_sweep"}
    for call in calls:
        values = [value.value for value in call.keywords if value.arg == "enrichment_context"]
        assert len(values) == 1 and isinstance(values[0], ast.Name) and values[0].id == "enrichment_context"
    return writer, owner


def _fixture(owner_text=None, hook=None, fault=None):
    writer, _ = _boundary(owner_text=owner_text)
    context = {"__name__": "fixture_registered_sangam", "math": math}
    selected = []
    for node in writer.body:
        if isinstance(node, ast.Assign):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in {
                "_can_carry_mode_d", "_mode_d_carrier_index", "_resolved_target_longitude", "_target_blank_note"}:
            selected.append(node)
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<actual pure Sangam helpers>", "exec"), context)
    previous = ["previous"]
    self = SimpleNamespace(_target_blanks=previous)
    calls, returned = [], []
    enrichment = SimpleNamespace(vedha_rules=object())
    native = SimpleNamespace(moon_sign="fixture", janma_nakshatra_idx=3, location=object())
    services = [object(), object(), object()]
    class Log:
        def info(self, *args):
            pass
        def warning(self, *args):
            pass
    context["logger"] = Log()
    context["_SIGN_NAME_TO_IDX"] = {"fixture": 2}
    def convert(value):
        calls.append(("date", {"value": value, "prior_sink": self._target_blanks is previous}))
        if fault == "date":
            raise RuntimeError("FIXTURE_DATE")
        return float(value.toordinal())
    context["_date_to_jd"] = convert
    def engine(tag):
        def call(**kwargs):
            calls.append((tag, kwargs))
            if fault == tag:
                raise RuntimeError("FIXTURE_MODE")
            row = {"mode": tag}
            returned.append(row)
            return [row]
        return call
    for name, tag in [("mode_a_search", "A"), ("mode_b_sweep", "B"),
                      ("mode_c_subsystem_period", "C"), ("mode_d_av_bindhu", "D")]:
        context[name] = engine(tag)
    def suppress(rows, **kwargs):
        calls.append(("suppress", kwargs))
        return rows
    context["apply_trigger_suppression"] = suppress
    owner_context = {"__name__": "fixture_window_owner"}
    exec(compile(OWNER.read_text() if owner_text is None else owner_text,
                 "<actual Sangam domain owner>", "exec"), owner_context)
    context.update(WindowBindings=owner_context["WindowBindings"], generate_windows=owner_context["generate_windows"])
    adapter = next(node for node in writer.body if isinstance(node, ast.ClassDef)
                   and node.name == "_SangamWindowBindings")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[adapter, _method(writer)], type_ignores=[])),
                 "<actual registered facade>", "exec"), context)
    def keepalive():
        calls.append(("keepalive", {}))
        if hook:
            hook(context, self, calls, engine)
    def invoke(predicates, **kwargs):
        return context["_generate_windows"](
            self, predicates, date(2030, 1, 1), date(2030, 2, 1), services[0], services[1],
            "fixture-chart", native, keepalive, enrichment, services[2], **kwargs)
    return invoke, context, self, previous, calls, returned, enrichment, services


def _predicate(signal="fixture-signal", kind="TRANSIT", target=12):
    return {"signal_id": signal, "signature_class": kind, "primary_domain": "fixture-domain",
            "transit_trigger_jsonb": {"target_longitude_deg": target}}


def test_actual_source_boundary():
    _boundary()


@pytest.mark.parametrize("predicates,mode_d,expected", [
    ([], True, []),
    ([_predicate()], True, ["A", "B", "D"]),
    ([_predicate()], False, ["A", "B"]),
    ([_predicate(kind="SUBSYSTEM")], True, ["C"]),
    ([_predicate(target=None)], True, ["D"]),
    ([_predicate(None)], True, []),
    ([_predicate(), _predicate()], True, ["A", "B", "D", "A", "B"]),
])
def test_mode_sequence_rows_context_and_identity(predicates, mode_d, expected):
    invoke, _, self, previous, calls, returned, enrichment, services = _fixture()
    out = invoke(copy.deepcopy(predicates), mode_d=mode_d)
    assert [row["mode"] for row in out] == expected
    assert all(any(row is original for original in returned) for row in out)
    assert all(row["primary_domain"] == "fixture-domain" for row in out)
    assert self._target_blanks is not previous
    for tag, values in calls:
        if tag in {"A", "B", "C", "D"}:
            assert values["enrichment_context"] is enrichment
            assert values["gochara_service"] is services[1]
        if tag == "A":
            assert values["dasha_kala_service"] is services[0]


def test_date_failure_preserves_previous_blank_sink():
    invoke, _, self, previous, _, _, _, _ = _fixture(fault="date")
    with pytest.raises(RuntimeError):
        invoke([_predicate()])
    assert self._target_blanks is previous


def test_each_call_binds_a_new_blank_list_before_mode_work():
    invoke, _, self, _, calls, _, _, _ = _fixture()
    invoke([_predicate(None)])
    first = self._target_blanks
    invoke([_predicate(target=None)])
    assert self._target_blanks is not first
    assert first == [{"signal_id": None, "reason": "signal_unresolved"}]
    assert self._target_blanks == [{"signal_id": "fixture-signal", "reason": "target_unresolved"}]
    assert all(values["prior_sink"] for tag, values in calls[:2] if tag == "date")


def test_live_callable_mapping_and_blank_attribute_rebinding():
    fired = False
    def hook(context, self, calls, engine):
        nonlocal fired
        if not fired:
            fired = True
            context["mode_b_sweep"] = engine("B2")
            context["_SIGN_NAME_TO_IDX"] = {"fixture": 9}
            self._target_blanks = ["callback-owned"]
    invoke, _, self, _, calls, _, _, _ = _fixture(hook=hook)
    invoke([_predicate(), _predicate(None), _predicate(target=None)])
    assert any(tag == "B2" for tag, _ in calls)
    assert self._target_blanks == ["callback-owned"]
    invoke([_predicate()])
    assert any(values.get("moon_sign_idx") == 9 for tag, values in calls if tag == "suppress")


@pytest.mark.parametrize("fault,remaining", [("A", ["B", "D"]), ("B", ["A", "D"]),
                                              ("C", []), ("D", ["A", "B"])])
def test_mode_failures_keep_the_existing_independent_paths(fault, remaining):
    invoke, _, _, _, _, _, _, _ = _fixture(fault=fault)
    out = invoke([_predicate(kind="SUBSYSTEM" if fault == "C" else "TRANSIT")])
    assert [row["mode"] for row in out] == remaining


@pytest.mark.parametrize("change", [
    lambda text: text.replace("from services.ka_sangam.window_generation", "from services.ka_sangam.engine", 1),
    lambda text: text.replace("return mode_b_sweep", "return mode_a_search", 1),
    lambda text: text.replace("self._target_blanks = blanks", "self._target_blanks = []", 1),
    lambda text: text.replace("mode_d: bool = True", "mode_d: bool = False", 1),
])
def test_binding_facade_mutants_refuse(change):
    with pytest.raises(AssertionError):
        _boundary(writer_text=change(WRITER.read_text()))


def test_domain_database_capability_mutant_refuses():
    with pytest.raises(AssertionError):
        _boundary(owner_text=OWNER.read_text() + "\nconnection.execute('FIXTURE')\n")


def test_missing_actual_mode_enrichment_binding_refuses():
    tree = ast.parse(OWNER.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "mode_b_sweep":
            for keyword in node.keywords:
                if keyword.arg == "enrichment_context":
                    keyword.value = ast.Constant(None)
    with pytest.raises(AssertionError):
        _boundary(owner_text=ast.unparse(tree))


def test_old_empty_algorithm_return_cannot_pass_behavior_oracle():
    changed = OWNER.read_text().replace("    return all_windows", "    return []")
    invoke, _, _, _, _, _, _, _ = _fixture(owner_text=changed)
    with pytest.raises(AssertionError):
        assert [row["mode"] for row in invoke([_predicate()])] == ["A", "B", "D"]
