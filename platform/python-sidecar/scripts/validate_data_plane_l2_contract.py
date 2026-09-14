#!/usr/bin/env python3
"""Static and deterministic validator for DP-SD-015 L2 producer readiness."""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "python-sidecar"
sys.path.insert(0, str(PYTHON))

from bodha_writers.data_plane_contracts import CURRENT_WRITERS  # noqa: E402
from bodha_writers.data_plane_resource_mechanism_slice import (  # noqa: E402
    build_resource_mechanism_slice,
)


def _call_name(node: ast.Call) -> str:
    target: ast.expr = node.func
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def _function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise ValueError(f"function {name} absent")


def _string_constants(tree: ast.AST) -> list[tuple[int, str]]:
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def main() -> int:
    violations: list[str] = []
    writer_dir = PYTHON / "pipeline" / "orchestrator" / "writers"
    registered: set[str] = set()
    adopted: set[str] = set()
    writer_trees: dict[str, ast.Module] = {}
    for path in writer_dir.glob("bo_*.py"):
        tree = ast.parse(path.read_text())
        writer_trees[path.name] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("services.ka_"):
                violations.append(f"l3_import:{path.name}:{node.lineno}")
            if isinstance(node, ast.Call) and _call_name(node) in {"uuid.uuid4", "uuid4"}:
                violations.append(f"volatile_live_id:{path.name}:{node.lineno}")
        for lineno, value in _string_constants(tree):
            if "%" in value and re.search(
                r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(?:bodha_|synthesis_)",
                value,
                re.IGNORECASE,
            ):
                violations.append(f"unqualified_l2_mutation:{path.name}:{lineno}")
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

    amplifier = ast.parse(
        (PYTHON / "bodha_writers" / "bhavat_bhavam_amplifier.py").read_text()
    )
    for node in ast.walk(amplifier):
        if isinstance(node, ast.Call) and _call_name(node) in {"uuid.uuid4", "uuid4"}:
            violations.append(f"volatile_live_id:bhavat_bhavam_amplifier.py:{node.lineno}")

    laksana_tree = writer_trees["bo_laksana.py"]
    if any(
        isinstance(node, ast.Call)
        and _call_name(node).endswith("compute_bhavat_bhavam_amplifiers")
        for node in ast.walk(laksana_tree)
    ):
        violations.append("bhavat_positive_emission_call")

    upaya_tree = writer_trees["bo_upaya.py"]
    upaya_run = _function(upaya_tree, "run")
    forbidden_temporal_calls = {
        "_legacy_l3_dasha_proximity_unavailable",
        "_fetch_dasha_runway_fresh",
        "_fetch_sadhana_milestones",
        "_build_remedy_leverage_windows",
    }
    for node in ast.walk(upaya_run):
        if isinstance(node, ast.Call) and _call_name(node).split(".")[-1] in forbidden_temporal_calls:
            violations.append(f"l2_temporal_call:bo_upaya.py:{node.lineno}")

    formulas_tree = ast.parse((PYTHON / "bodha_writers" / "formulas.py").read_text())
    resonance = _function(formulas_tree, "resonance_score_v1")
    if any(
        isinstance(node, ast.Attribute)
        and node.attr == "dasha_proximity_activation_score"
        for node in ast.walk(resonance)
    ):
        violations.append("l2_resonance_consumes_dasha")

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
    if first["occurrence_ledger"].get("unit") != "probability_like_structural_score":
        violations.append("slice_occurrence_unit")
    if first["condition_ledger"].get("unit") != "affliction_0_10":
        violations.append("slice_condition_unit")
    if first["occurrence_ledger"].get("polarity") != "higher_is_more_formed":
        violations.append("slice_occurrence_polarity")
    if first["condition_ledger"].get("polarity") != "higher_is_more_afflicted":
        violations.append("slice_condition_polarity")

    migration = (ROOT / "migrations" / "1034_data_plane_l2_producer_generations.sql").read_text()
    for token in (
        "UNAVAILABLE_AT_L2",
        "completed L2 producer generation is immutable",
        "l2_data_plane_row_snapshots",
        "l2_data_plane_partition_contexts",
        "semantic_output_digest",
        "select_l2_data_plane_generation",
        "rollback_l2_data_plane_generation",
        "bind_l2_exact_inputs",
        "l2_data_plane_asset_outputs",
        "source_digest",
        "BEFORE UPDATE OR DELETE",
    ):
        if token not in migration:
            violations.append(f"migration_contract_missing:{token}")
    if re.search(r"\binvalidated\b", migration, re.IGNORECASE):
        violations.append("mutable_invalidation_state")

    contract = (PYTHON / "bodha_writers" / "data_plane_contracts.py").read_text()
    for token in (
        "get_writer_source_hash",
        "_resolve_upstream_context",
        "bind_l2_exact_inputs",
        "generation_context_id",
        "stable_semantic_uuid",
    ):
        if token not in contract:
            violations.append(f"runtime_contract_missing:{token}")

    idempotency = ast.parse((PYTHON / "bodha_writers" / "_idempotency.py").read_text())
    for lineno, value in _string_constants(idempotency):
        if re.search(
            r"\bDELETE\s+FROM\s+(?:bodha_|synthesis_)", value, re.IGNORECASE
        ):
            violations.append(f"unqualified_l2_mutation:_idempotency.py:{lineno}")

    karanajala = (writer_dir / "bo_karanajala.py").read_text()
    for token in ("%(cancelled_by_jsonb)s::jsonb", "cancelling_roots", "original_polarity"):
        if token not in karanajala:
            violations.append(f"cancellation_contract_missing:{token}")

    sangati = (writer_dir / "bo_sangati.py").read_text()
    for token in (
        "contradicts_signals_array",
        "shared_root_groups",
        "_is_qualified_contradiction",
        "constituent_facts_array",
    ):
        if token not in sangati:
            violations.append(f"sangati_contract_missing:{token}")

    pramana = (writer_dir / "bo_pramana_mapa.py").read_text()
    for token in (
        "detect_l2_contract_integrity",
        '"context_generation"',
        '"signed_relation_and_cancellation"',
        '"ledger_independence_and_duplicate_root"',
        "no_pre_answer_pass",
    ):
        if token not in pramana:
            violations.append(f"quality_detector_missing:{token}")

    for violation in violations:
        print(f"VIOLATION {violation}")
    print(
        f"data_plane_l2_validator: writers={len(registered)} adopted={len(adopted)} "
        f"slice_digest={first['content_digest']} violations={len(violations)}"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
