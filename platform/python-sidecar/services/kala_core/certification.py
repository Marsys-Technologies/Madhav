"""Offline certification evidence readers; never execute the census or award PASS."""
from __future__ import annotations

import ast
from pathlib import Path

REGISTRY_PATH = Path('platform/scripts/governance/asset_census.py')


def read_detector_registry(path: Path) -> tuple[int, dict]:
    """Read the literal revision/detector bindings used by the K7-4 verifier."""
    tree = ast.parse(path.read_text())
    revision = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'REGISTRY_REVISION' for t in n.targets))
    registry = next(n.value for n in tree.body if isinstance(n, ast.AnnAssign)
                    and isinstance(n.target, ast.Name) and n.target.id == 'CRITERION_REGISTRY')
    criteria = {ast.literal_eval(k): {x.arg: ast.literal_eval(x.value) for x in v.keywords
                if x.arg in {'revision', 'detector'}} for k, v in zip(registry.keys, registry.values)}
    return revision, criteria


def test_reference_exists(sidecar: Path, reference: str) -> bool:
    """Resolve a pytest function/class node from source without importing DB tests."""
    parts = reference.split('::')
    path = (sidecar / parts[0]).resolve()
    if len(parts) < 2 or not path.is_relative_to((sidecar / 'tests').resolve()):
        return False
    if not path.name.startswith('test_') or path.suffix != '.py':
        return False
    node = ast.parse(path.read_text())
    for name in parts[1:]:
        node = next((n for n in getattr(node, 'body', [])
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     and n.name == name), None)
        if node is None:
            return False
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')
