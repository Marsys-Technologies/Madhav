"""Source-only ownership checks for the fact-identity implementation boundary."""
from pathlib import Path
import ast
import json

import pytest

ROOT = Path(__file__).resolve().parents[4]
SIDECAR = ROOT / "platform/python-sidecar"
LEAVES = ("parser", "check", "index")
OWNED = {
    "parser": {"IdentityMatch", "parse_fact_identity", "classify_unparsed_subject"},
    "check": {"classify_fact", "check_identity_index", "CheckItem", "CheckResult"},
    "index": {"parsed_from", "build_index_for_chart"},
}


def _alias(leaf, source):
    expected = (
        '"""compatibility"""\nimport sys as _sys\n'
        f'from ga_writers import fact_identity_{leaf} as _implementation\n'
        '_sys.modules[__name__] = _implementation\n'
    )
    tree = ast.parse(source)
    target = ast.parse(expected)
    # The documentation may change; executable facade statements are bounded.
    assert ast.dump(ast.Module(body=tree.body[1:], type_ignores=[])) == ast.dump(
        ast.Module(body=target.body[1:], type_ignores=[])
    ), "compatibility alias must share the actual owner module"
    assert isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant)


def _owner(leaf, source):
    tree = ast.parse(source)
    definitions = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    assert OWNED[leaf] <= definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("brahmagyan.fact_identity_")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"commit", "rollback", "close"}, "borrowed connection cannot end its owner transaction"
    if leaf == "index":
        assignments = {t.id: n.value for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
        sql = ast.literal_eval(assignments["INSERT_SQL"])
        columns = tuple(x.strip() for x in sql.split("(", 1)[1].split(")", 1)[0].split(","))
        assert columns == ("fact_id", "chart_id", "entity_kind", "graha_code", "graha_code_secondary", "house_num", "house_num_secondary", "varga_id", "sign_num", "parse_rule", "parsed_from", "build_id", "computed_at")
        cursors = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "cursor"]
        assert len(cursors) == 2 and all(any(k.arg == "row_factory" and isinstance(k.value, ast.Name) and k.value.id == "tuple_row" for k in n.keywords) for n in cursors)
        assert "FROM chart_facts WHERE chart_id = %s" in source


@pytest.mark.parametrize("leaf", LEAVES)
def test_owner_and_historical_facade(leaf):
    _owner(leaf, (SIDECAR / "ga_writers" / f"fact_identity_{leaf}.py").read_text())
    _alias(leaf, (SIDECAR / "brahmagyan" / f"fact_identity_{leaf}.py").read_text())


def test_registered_adapter_points_at_the_real_owner():
    source = (SIDECAR / "pipeline/orchestrator/writers/ga_fact_identity.py").read_text()
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1 and classes[0].name == "GaFactIdentityWriter"
    paths = next(ast.literal_eval(n.value) for n in classes[0].body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "source_paths" for t in n.targets))
    assert paths == ["platform/python-sidecar/pipeline/orchestrator/writers/ga_fact_identity.py"] + [f"platform/python-sidecar/ga_writers/fact_identity_{leaf}.py" for leaf in ("index", "check", "parser")]
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "register" and ast.literal_eval(n.args[0]) == "ga_fact_identity" for n in classes[0].decorator_list)
    assert "from brahmagyan.fact_identity_" not in source


def test_current_declaration_body_anchors_follow_the_owner():
    entry = json.loads((ROOT / "platform/scripts/governance/asset_declarations.json").read_text())["assets"]["ga_fact_identity"]
    pointers = [entry["carriage"]["evidence"], entry["ldgr_source"]["evidence"], entry["prose_none"]["identifier_columns"][0]["evidence"]] + [x["evidence"] for x in entry["prose_none"]["templated_columns"]]
    for pointer in pointers:
        path, line = pointer.rsplit(":", 1)
        assert path.startswith("platform/python-sidecar/ga_writers/fact_identity_")
        assert (ROOT / path).read_text().splitlines()[int(line) - 1].strip()
    assert "platform/python-sidecar/ga_writers/fact_identity_index.py:38" in entry["evidence"]["prose_fields"]


@pytest.mark.parametrize("leaf", LEAVES)
def test_duplicate_body_or_star_shim_refuses(leaf):
    with pytest.raises(AssertionError):
        _alias(leaf, '"""bad facade"""\nfrom ga_writers.fact_identity_' + leaf + ' import *\n')
    with pytest.raises(AssertionError):
        _alias(leaf, (SIDECAR / "ga_writers" / f"fact_identity_{leaf}.py").read_text())


@pytest.mark.parametrize("method", ("commit", "rollback", "close"))
def test_borrowed_transaction_ending_refuses(method):
    source = (SIDECAR / "ga_writers/fact_identity_index.py").read_text()
    with pytest.raises(AssertionError, match="borrowed connection"):
        _owner("index", source + f"\nconn.{method}()\n")


def test_old_owner_import_refuses():
    source = (SIDECAR / "ga_writers/fact_identity_index.py").read_text()
    with pytest.raises(AssertionError):
        _owner("index", source.replace("from ga_writers.fact_identity_check import", "from brahmagyan.fact_identity_check import"))


def test_cursor_and_column_changes_refuse():
    source = (SIDECAR / "ga_writers/fact_identity_index.py").read_text()
    for mutant in (source.replace("row_factory=tuple_row", "row_factory=dict", 1), source.replace("fact_id, chart_id,", "fact_id,", 1)):
        with pytest.raises(AssertionError):
            _owner("index", mutant)
