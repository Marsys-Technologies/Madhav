"""Recognize governed independent tables while rejecting changed doctrine."""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
CHECKER = ROOT / "platform/scripts/governance/check_no_local_aspect_dict.py"
SPEC = importlib.util.spec_from_file_location("governed_aspect_checker", CHECKER)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def table_source(path: str) -> tuple[str, ast.Assign | ast.AnnAssign]:
    text = (ROOT / path).read_text()
    name = checker.GOVERNED_DECLARATIONS[path]
    declaration = next(
        node for node in ast.parse(text).body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(isinstance(target, ast.Name) and target.id == name for target in (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        ))
    )
    return text, declaration


@pytest.mark.parametrize("path", checker.GOVERNED_DECLARATIONS)
def test_exact_governed_declaration_is_recognized_without_importing_an_oracle(path):
    text, _ = table_source(path)
    assert checker.scan_python_file(text, path) == []
    assert checker.scan_python_file(text, "platform/python-sidecar/unrelated.py")


@pytest.mark.parametrize("path", checker.GOVERNED_DECLARATIONS)
@pytest.mark.parametrize("mutation", ["wrong_angle", "node_aspect", "extra_body"])
def test_changed_runtime_or_independent_oracle_table_is_a_new_violation(path, mutation):
    text, declaration = table_source(path)
    values = ast.literal_eval(declaration.value)
    keys = {name.lower(): name for name in values}
    if mutation == "wrong_angle":
        values[keys["mars"]] = [91.0, 180.0, 210.0]
    elif mutation == "node_aspect":
        values[keys["rahu"]] = [180.0]
    else:
        values["synthetic_body"] = [180.0]
    original = ast.get_source_segment(text, declaration.value)
    assert original
    changed = text.replace(original, repr(values), 1)
    assert checker.scan_python_file(changed, path)


@pytest.mark.parametrize("path", checker.GOVERNED_DECLARATIONS)
def test_role_does_not_exempt_another_table_or_a_nested_copy(path):
    text, declaration = table_source(path)
    table = ast.get_source_segment(text, declaration.value)
    name = checker.GOVERNED_DECLARATIONS[path]
    assert table
    assert checker.scan_python_file(text + "\nEXTRA_ASPECTS = " + table, path)
    nested = "\ndef unrelated():\n    " + name + " = " + repr(ast.literal_eval(table))
    assert checker.scan_python_file(text + nested, path)


def test_duplicate_or_rebound_declaration_is_not_a_governed_role():
    path = next(iter(checker.GOVERNED_DECLARATIONS))
    text, declaration = table_source(path)
    name = checker.GOVERNED_DECLARATIONS[path]
    assert checker.scan_python_file(text + "\n" + name + " = {}", path)
    original = ast.get_source_segment(text, declaration.value)
    assert original
    values = ast.literal_eval(original)
    duplicate = repr(values)[:-1] + ", 'Mars': [90.0, 180.0, 210.0]}"
    assert checker.scan_python_file(text.replace(original, duplicate, 1), path)


def test_legacy_convention_remains_visible():
    path = "platform/python-sidecar/services/gochara_grammar/primitives.py"
    assert checker.scan_python_file((ROOT / path).read_text(), path)

