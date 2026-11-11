"""Check the reviewed CGM identity edge and its historical exports."""

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest


SIDECAR = Path(__file__).resolve().parents[3] / "python-sidecar"
WRITERS = "pipeline.orchestrator.writers"
BIMBA = WRITERS + ".bo_bimba"
KARANAJALA = WRITERS + ".bo_karanajala"
IDENTITY = "bodha_writers.cgm_identity"
BIMBA_EXPORTS = {
    "_SUBJECT_TO_GRAHA": "SUBJECT_TO_GRAHA",
    "_YOGA_NODE_CLASSES": "YOGA_NODE_CLASSES",
    "_yoga_config_name": "_yoga_config_name",
    "yoga_node_subject": "yoga_node_subject",
}
KARANAJALA_IMPORTS = {
    "_GRAHA_SUBJECT_MAP": "SUBJECT_TO_GRAHA",
    "_YOGA_NODE_CLASSES": "YOGA_NODE_CLASSES",
    "_yoga_node_subject": "yoga_node_subject",
}


def _import_targets(tree, package, *, include_from_modules=True):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            target = resolve_name("." * node.level + (node.module or ""), package)
            if include_from_modules:
                yield target
            yield from (f"{target}.{alias.name}" for alias in node.names)


def _check_writer_imports(tree, expected):
    bindings = [
        (alias.asname or alias.name.split(".", 1)[0], getattr(node, "module", None), getattr(node, "level", 0), alias.name)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
        if (alias.asname or alias.name.split(".", 1)[0]) in expected
    ]
    assert sorted(bindings, key=lambda binding: binding[0]) == sorted(
        (name, IDENTITY, 0, original) for name, original in expected.items()
    ), "CGM identity bindings changed"
    assert not any(
        isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in expected
        or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in expected
        for node in ast.walk(tree)
    ), "CGM identity binding was reassigned"


def _check_karanajala(tree):
    imports = tuple(_import_targets(tree, WRITERS))
    assert not any(target == BIMBA or target.startswith(BIMBA + ".") for target in imports), (
        "Karanajala imports the Bimba implementation"
    )
    imported_values = set(_import_targets(tree, WRITERS, include_from_modules=False))
    assert not {WRITERS, WRITERS + ".*"} & imported_values, "Karanajala imports a writer namespace"
    assert not any(target == "importlib" or target.startswith("importlib.") for target in imports)
    assert not any(isinstance(node, ast.Name) and node.id == "__import__" for node in ast.walk(tree)), (
        "unreviewed dynamic import in Karanajala"
    )
    _check_writer_imports(tree, KARANAJALA_IMPORTS)


def _check_identity(tree):
    assert sorted(_import_targets(tree, "bodha_writers")) == sorted((
        "__future__", "__future__.annotations", "re",
        "brahmagyan.graha_vocabulary", "brahmagyan.graha_vocabulary.to_title",
    )), "CGM identity must depend only on vocabulary and local transformations"
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [ast.unparse(target) for target in node.targets]
            assert names == ["YOGA_NODE_CLASSES"], "unexpected CGM module binding"
        elif isinstance(node, ast.AnnAssign):
            assert ast.unparse(node.target) == "SUBJECT_TO_GRAHA", "unexpected CGM module binding"
        elif isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant) and isinstance(node.value.value, str), "unexpected CGM module expression"
        else:
            assert isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)), "unexpected CGM module statement"
    allowed_calls = {"to_title", "_yoga_config_name", "cfg.get", "isinstance", "v.strip", "re.sub", "name.lower"}
    for node in ast.walk(tree):
        assert not isinstance(node, ast.AsyncFunctionDef), "unexpected asynchronous CGM helper"
        if isinstance(node, ast.FunctionDef):
            assert not node.decorator_list, "CGM identity helper cannot register at import"
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute) and target.attr == "strip" and isinstance(target.value, ast.Call):
                assert ast.unparse(target.value.func) == "re.sub", "unexpected CGM identity call"
            else:
                assert ast.unparse(target) in allowed_calls, "unexpected CGM identity call"


def _source(module):
    return (SIDECAR / (module.replace(".", "/") + ".py")).read_text(encoding="utf-8")


def test_cgm_identity_is_owned_below_both_writers():
    _check_writer_imports(ast.parse(_source(BIMBA)), BIMBA_EXPORTS)
    _check_karanajala(ast.parse(_source(KARANAJALA)))
    _check_identity(ast.parse(_source(IDENTITY)))


@pytest.mark.parametrize("import_line", [
    "from .bo_bimba import yoga_node_subject as legacy_key",
    "from pipeline.orchestrator.writers import bo_bimba as writer",
    "import pipeline.orchestrator.writers.bo_bimba as writer",
])
def test_cgm_rejects_a_sibling_writer_import(import_line):
    with pytest.raises(AssertionError, match="imports the Bimba implementation"):
        _check_karanajala(ast.parse(_source(KARANAJALA) + "\n" + import_line))


@pytest.mark.parametrize(("body", "diagnostic"), [
    ("register('bo_identity')", "unexpected CGM module expression"),
    ("to_title('fixture')", "unexpected CGM module expression"),
    ("import psycopg as database", "only on vocabulary"),
    ("@register('bo_identity')\ndef f(): pass", "cannot register"),
    ("@register\nasync def f(): pass", "unexpected CGM module statement"),
])
def test_cgm_rejects_effects_in_the_identity_module(body, diagnostic):
    with pytest.raises(AssertionError, match=diagnostic):
        _check_identity(ast.parse(_source(IDENTITY) + "\n" + body))


def test_cgm_rejects_a_writer_package_namespace():
    candidate = _source(KARANAJALA) + "\nfrom pipeline.orchestrator import writers as holder\nlocal_writer = holder.bo_bimba"
    with pytest.raises(AssertionError, match="imports a writer namespace"):
        _check_karanajala(ast.parse(candidate))


@pytest.mark.parametrize(("module", "body", "diagnostic"), [
    (KARANAJALA, "from math import sqrt as _yoga_node_subject", "identity bindings changed"),
    (BIMBA, "def yoga_node_subject(*args): return None", "identity binding was reassigned"),
])
def test_cgm_rejects_rebound_compatibility_symbols(module, body, diagnostic):
    expected = KARANAJALA_IMPORTS if module == KARANAJALA else BIMBA_EXPORTS
    with pytest.raises(AssertionError, match=diagnostic):
        _check_writer_imports(ast.parse(_source(module) + "\n" + body), expected)
