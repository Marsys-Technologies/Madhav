#!/usr/bin/env python3
"""Validate the bounded L1 Gaṇita producer-ready contract without a database."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys


SIDECAR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SIDECAR_ROOT.parents[1]
if str(SIDECAR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIDECAR_ROOT))

from ga_writers.data_plane_resource_config_slice import build_default_slice  # noqa: E402
from ga_writers.data_plane_runtime import CONTRACTED_L1_ASSETS  # noqa: E402


EXPECTED_WRITERS = (
    "ga_positions", "ga_vargas", "ga_dashas", "ga_nakshatra",
    "ga_panchanga", "ga_sensitive", "ga_sensitive_degree", "ga_strength",
    "ga_structural", "ga_condition", "ga_yoga", "ga_vichara",
    "ga_sade_sati", "ga_transit_anchors", "ga_tajaka", "ga_ayurdaya",
    "ga_medical", "ga_vastu", "ga_prashna",
)

EXPECTED_SLICE_DIGEST = "25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279"

STABLE_FACT_WRITERS = (
    "ga_positions_writer.py", "ga_vargas_writer.py", "ga_panchanga_writer.py",
    "ga_sensitive_writer.py", "ga_sensitive_degree_writer.py",
    "ga_strength_writer.py", "ga_structural_writer.py",
    "ga_sade_sati_writer.py", "ga_ayurdaya_writer.py",
)

PRODUCER_SOURCE_EXCEPTIONS = {
    "ga_nakshatra": (
        "platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py",
        "platform/python-sidecar/ga_writers/ga_nakshatra_compute.py",
        "platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py",
        "platform/python-sidecar/ga_writers/ga_kp_significators.py",
    ),
    "ga_prashna": ("platform/python-sidecar/ga_writers/ga_prashna_writer.py",),
}


def _function_source(path: Path, function_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"{path}: missing {function_name}")


def validate() -> dict[str, object]:
    findings: list[str] = []
    wrappers_dir = SIDECAR_ROOT / "pipeline" / "orchestrator" / "writers"
    actual = tuple(sorted(path.stem for path in wrappers_dir.glob("ga_*.py")))
    if actual != tuple(sorted(EXPECTED_WRITERS)):
        findings.append(f"writer denominator mismatch: actual={actual!r}")

    wrapper_sources: dict[str, tuple[str, ...]] = {}
    for writer in EXPECTED_WRITERS:
        path = wrappers_dir / f"{writer}.py"
        source = path.read_text(encoding="utf-8")
        if not re.search(rf"@register\(['\"]{re.escape(writer)}['\"]\)", source):
            findings.append(f"{writer}: missing exact @register")
        if "@l1_producer_contract" not in source:
            findings.append(f"{writer}: runtime L1 producer boundary absent")
        match = re.search(r"source_paths\s*=\s*\[([^\]]+)\]", source)
        paths = tuple(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))) if match else ()
        if not paths:
            paths = PRODUCER_SOURCE_EXCEPTIONS.get(writer, ())
        wrapper_sources[writer] = paths
        if not paths:
            findings.append(f"{writer}: no producer source_paths")

    ga_dir = SIDECAR_ROOT / "ga_writers"
    for filename in STABLE_FACT_WRITERS:
        function_source = _function_source(ga_dir / filename, "_fact_id")
        assignment_lines = [line for line in function_source.splitlines() if "raw =" in line]
        if any("build_id" in line for line in assignment_lines):
            findings.append(f"{filename}: semantic fact ID still contains build_id")
    nakshatra_source = _function_source(wrappers_dir / "ga_nakshatra.py", "_fact_id")
    if any("build_id" in line for line in nakshatra_source.splitlines() if "raw =" in line):
        findings.append("ga_nakshatra.py: semantic fact ID still contains build_id")

    condition_source = (ga_dir / "ga_condition_writer.py").read_text(encoding="utf-8")
    if re.search(r"['\"]fact_id['\"]\s*:\s*str\(uuid\.uuid4\(\)\)", condition_source):
        findings.append("ga_condition_writer.py: random fact identity remains")
    dashas_source = (ga_dir / "ga_dashas_writer.py").read_text(encoding="utf-8")
    if "stabilize_hierarchical_uuids(" not in dashas_source:
        findings.append("ga_dashas_writer.py: stable hierarchy post-pass absent")
    if re.search(r"['\"]level_n['\"]\s*:\s*5", dashas_source):
        findings.append("ga_dashas_writer.py: invalid level-5 interval sentinel remains")
    tajaka_source = (ga_dir / "ga_tajaka_writer.py").read_text(encoding="utf-8")
    if '"varsha_id": str(uuid.uuid4())' in tajaka_source:
        findings.append("ga_tajaka_writer.py: random varsha identity remains")

    slice_payload = build_default_slice()
    if slice_payload["content_sha256"] != EXPECTED_SLICE_DIGEST:
        findings.append(
            "first-slice golden digest mismatch: "
            f"{slice_payload['content_sha256']} != {EXPECTED_SLICE_DIGEST}"
        )
    states = set(slice_payload["missingness_states_proved"])
    expected_states = {
        "present", "zero", "unavailable", "floored", "inapplicable",
        "unqualified_source", "failed", "unexplored",
    }
    if states != expected_states:
        findings.append(f"missingness distinction mismatch: {sorted(states)!r}")
    if slice_payload["configuration"]["positive_doctrinal_arm"] != "NOT_REACHABLE":
        findings.append("unqualified Bhāvat positive arm became reachable")
    if slice_payload["bhavat_bhavam"]["applied"] is not False:
        findings.append("Bhāvat operator was applied in L1")
    if not str(slice_payload["context"]["chart_id"]).startswith("synthetic:"):
        findings.append("first slice is not a non-person synthetic fixture")
    resolved_dependency_ids = {
        item["dependency_id"] for item in slice_payload["resolved_l0_dependencies"]
    }
    for fact in slice_payload["facts"]:
        for dependency in fact["source_dependencies"]:
            if dependency not in resolved_dependency_ids and not dependency.startswith("l1fact:"):
                # Emitted fixture dependencies are stable fact hashes, not named
                # strings, so only named external identities reach this branch.
                if dependency.startswith(("l0:", "external:")):
                    findings.append(f"unresolved external dependency: {dependency}")
    for sensitivity in slice_payload["sensitivity"]:
        if sensitivity["target_varga_formula"] != "parasara_standard_v1":
            findings.append("first-slice D9 sensitivity did not use admitted formula")

    if set(EXPECTED_WRITERS) != CONTRACTED_L1_ASSETS:
        findings.append("runtime contract denominator differs from the fixed 19 writers")
    migration = (
        REPO_ROOT
        / "platform"
        / "supabase"
        / "migrations"
        / "1035_data_plane_l1_producer_history.sql"
    )
    migration_source = migration.read_text(encoding="utf-8") if migration.exists() else ""
    for required in (
        "open_l1_data_plane_generation",
        "complete_l1_data_plane_partition",
        "select_l1_data_plane_generation",
        "rollback_l1_data_plane_generation",
        "l1_data_plane_current_rows",
        "l1_data_plane_current_dashas",
        "l1_data_plane_current_facts",
        "l1_data_plane_current_configurations",
        "l1_data_plane_fact_snapshots",
        "l1_data_plane_dasha_snapshots",
        "l1_data_plane_configuration_snapshots",
        "l1_data_plane_jsonb_has_nonfinite",
        "l1_data_plane_reject_immutable_change",
    ):
        if required not in migration_source:
            findings.append(f"producer history migration missing {required}")
    capture_triggers = re.findall(
        r"CREATE TRIGGER l1_data_plane_capture AFTER INSERT(?: OR UPDATE)?",
        migration_source,
    )
    if len(capture_triggers) != 11 or "capture_l1_data_plane_dasha_partition" not in migration_source:
        findings.append(
            "producer history migration does not cover 11 row-trigger tables plus set-based chart_dashas"
        )

    result = {
        "schema_version": "1.0",
        "writer_denominator": len(actual),
        "expected_writer_denominator": len(EXPECTED_WRITERS),
        "writers": list(EXPECTED_WRITERS),
        "wrapper_sources": wrapper_sources,
        "slice_id": slice_payload["slice_id"],
        "slice_generation_id": slice_payload["slice_generation_id"],
        "slice_content_sha256": slice_payload["content_sha256"],
        "fixture_id": slice_payload["fixture_id"],
        "bhavat_state": slice_payload["bhavat_bhavam"]["qualification_state"],
        "positive_doctrinal_arm": slice_payload["configuration"]["positive_doctrinal_arm"],
        "findings": findings,
        "verdict": "PASS" if not findings else "FAIL",
    }
    return result


def main() -> int:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
