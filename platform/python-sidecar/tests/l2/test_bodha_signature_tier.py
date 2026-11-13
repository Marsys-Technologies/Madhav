"""Pure contract for the absolute Bodha tier owner and its five writer bindings."""
from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from bodha_writers.signature_tier import _signature_tier

WRITERS = (
    "bo_arudha",
    "bo_nakshatra_semantic",
    "bo_special_lagna",
    "bo_sudarshana",
    "bo_vargottama_dhana",
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-math.inf, "background"),
        (0, "background"),
        (math.nextafter(0.3, -math.inf), "background"),
        (0.3, "supporting"),
        (math.nextafter(0.3, math.inf), "supporting"),
        (math.nextafter(0.8, -math.inf), "supporting"),
        (0.8, "major"),
        (math.nextafter(0.8, math.inf), "major"),
        (math.nextafter(2.0, -math.inf), "major"),
        (2.0, "chart_defining"),
        (math.nextafter(2.0, math.inf), "chart_defining"),
        (math.inf, "chart_defining"),
        (math.nan, "background"),
    ],
)
def test_absolute_tier_boundaries(value: float, expected: str) -> None:
    assert _signature_tier(value) == expected


@pytest.mark.parametrize("asset", WRITERS)
def test_registered_writer_uses_bodha_tier_owner(asset: str) -> None:
    sidecar = Path(__file__).resolve().parents[2]
    path = sidecar / "pipeline" / "orchestrator" / "writers" / f"{asset}.py"
    module = ast.parse(path.read_bytes())
    imports = [
        item
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module == "bodha_writers.signature_tier"
        for item in node.names
    ]
    assert any(item.name == item.asname == "_signature_tier" for item in imports)
    assert not any(isinstance(node, ast.FunctionDef) and node.name == "_signature_tier" for node in module.body)
    registered = [
        node for node in module.body if isinstance(node, ast.ClassDef)
        and any(isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "register" and decorator.args
                and isinstance(decorator.args[0], ast.Constant) and decorator.args[0].value == asset
                for decorator in node.decorator_list)
    ]
    assert len(registered) == 1
    assert sum(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_signature_tier"
        for node in ast.walk(registered[0])
    ) == 1
