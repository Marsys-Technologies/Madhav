from __future__ import annotations

import ast
from pathlib import Path

from bodha_writers.data_plane_contracts import CURRENT_WRITERS


WRITER_DIR = Path(__file__).parents[2] / "pipeline" / "orchestrator" / "writers"


def test_all_23_registered_writers_adopt_common_l2_contract():
    registered = set()
    adopted = set()
    for path in WRITER_DIR.glob("bo_*.py"):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not decorator.args:
                    continue
                name = getattr(decorator.func, "id", None)
                value = ast.literal_eval(decorator.args[0])
                if name == "register" and value.startswith("bo_"):
                    registered.add(value)
                if name == "l2_producer":
                    adopted.add(value)
    assert registered == set(CURRENT_WRITERS)
    assert adopted == registered


def test_no_l2_writer_imports_l3_service_or_resolves_activation_windows():
    for path in WRITER_DIR.glob("bo_*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("services.ka_")

    karanajala = (WRITER_DIR / "bo_karanajala.py").read_text()
    assert "resolve_activation_windows(" not in karanajala
    assert "load_dasha_timeline(" not in karanajala
    assert '"active_dasha_periods_jsonb":      json.dumps' not in karanajala


def test_upaya_runtime_preserves_legacy_windows_without_new_emission():
    tree = ast.parse((WRITER_DIR / "bo_upaya.py").read_text())
    writer = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "BoUpayaWriter")
    run = next(n for n in writer.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    calls = {
        getattr(n.func, "id", None)
        for n in ast.walk(run)
        if isinstance(n, ast.Call)
    }
    assert "_build_remedy_leverage_windows" not in calls
    assert "replace_prior_rm_dasha_windowed" not in calls
