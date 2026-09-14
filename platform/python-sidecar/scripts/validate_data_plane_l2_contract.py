#!/usr/bin/env python3
"""Static and deterministic validator for DP-SD-015 L2 producer readiness."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "python-sidecar"
sys.path.insert(0, str(PYTHON))

from bodha_writers.data_plane_contracts import CURRENT_WRITERS  # noqa: E402
from bodha_writers.data_plane_resource_mechanism_slice import (  # noqa: E402
    build_resource_mechanism_slice,
)


def main() -> int:
    violations: list[str] = []
    writer_dir = PYTHON / "pipeline" / "orchestrator" / "writers"
    registered: set[str] = set()
    adopted: set[str] = set()
    for path in writer_dir.glob("bo_*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("services.ka_"):
                violations.append(f"l3_import:{path.name}:{node.lineno}")
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not decorator.args:
                    continue
                name = getattr(decorator.func, "id", None)
                value = ast.literal_eval(decorator.args[0])
                if name == "register" and str(value).startswith("bo_"):
                    registered.add(value)
                elif name == "l2_producer":
                    adopted.add(value)
    expected = set(CURRENT_WRITERS)
    if registered != expected:
        violations.append(f"writer_census:{sorted(registered ^ expected)}")
    if adopted != expected:
        violations.append(f"runtime_adoption:{sorted(adopted ^ expected)}")

    fixture_path = (
        PYTHON / "bodha_writers" / "__tests__" / "fixtures" /
        "l2_resource_mechanism_non_person_v1.json"
    )
    fixture = json.loads(fixture_path.read_text())
    first = build_resource_mechanism_slice(fixture)
    second = build_resource_mechanism_slice(fixture)
    if first != second or first.get("content_digest") != second.get("content_digest"):
        violations.append("slice_nondeterministic")
    if first.get("activation_windows") is not None:
        violations.append("slice_activation_window_present")
    if first["grounding"].get("positive_doctrinal_arm") != "NOT_REACHABLE":
        violations.append("bhavat_positive_arm_reachable")

    migration = (ROOT / "migrations" / "1034_data_plane_l2_producer_generations.sql").read_text()
    for token in ("UNAVAILABLE_AT_L2", "completed L2 producer generation is immutable"):
        if token not in migration:
            violations.append(f"migration_contract_missing:{token}")

    for violation in violations:
        print(f"VIOLATION {violation}")
    print(
        f"data_plane_l2_validator: writers={len(registered)} adopted={len(adopted)} "
        f"slice_digest={first['content_digest']} violations={len(violations)}"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
