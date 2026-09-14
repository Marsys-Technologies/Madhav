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


EXPECTED_WRITERS = (
    "ga_positions", "ga_vargas", "ga_dashas", "ga_nakshatra",
    "ga_panchanga", "ga_sensitive", "ga_sensitive_degree", "ga_strength",
    "ga_structural", "ga_condition", "ga_yoga", "ga_vichara",
    "ga_sade_sati", "ga_transit_anchors", "ga_tajaka", "ga_ayurdaya",
    "ga_medical", "ga_vastu", "ga_prashna",
)

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
    tajaka_source = (ga_dir / "ga_tajaka_writer.py").read_text(encoding="utf-8")
    if '"varsha_id": str(uuid.uuid4())' in tajaka_source:
        findings.append("ga_tajaka_writer.py: random varsha identity remains")

    slice_payload = build_default_slice()
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
