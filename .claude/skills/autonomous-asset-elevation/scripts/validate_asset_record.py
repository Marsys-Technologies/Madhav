#!/usr/bin/env python3
"""Validate an Asset Elevation Record, including state-dependent invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "references" / "asset-elevation-record.schema.json"

STATE_RANK = {
    "RECONCILED": 0,
    "ELIGIBLE": 1,
    "ANALYZED": 2,
    "OPTIMIZED": 3,
    "JUSTIFIED_NO_CHANGE": 3,
    "INTEGRATED": 4,
    "DEPLOYED": 5,
    "REBUILT_ONCE": 6,
    "INDEPENDENTLY_VERIFIED": 7,
    "FROZEN": 8,
}

NO_REBUILD_DISPOSITIONS = {
    "MERGED_SPLIT",
    "RETIRED_SUPERSEDED",
    "SOURCE_ONLY",
    "SERVICE_PROBE",
    "PRODUCER_COVERED",
}


def present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def schema_type_matches(value: Any, expected: str) -> bool:
    """Match the JSON types used by this schema without bool/int ambiguity."""
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return type(value) is int
    if expected == "boolean":
        return type(value) is bool
    raise ValueError(f"unsupported schema type: {expected}")


def validate_schema_node(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    """Evaluate the JSON Schema keywords used by the checked-in record schema."""
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} has invalid value {value!r}")

    declared = schema.get("type")
    if declared is not None:
        expected = [declared] if isinstance(declared, str) else declared
        if not any(schema_type_matches(value, item) for item in expected):
            errors.append(f"{path} must have type {' or '.join(expected)}")
            return

    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{path} must not be empty")
    if type(value) is int and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path} must be at least {schema['minimum']}")

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = sorted(required - value.keys())
        if missing:
            errors.append(f"{path} missing required keys: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(value.keys() - properties.keys())
            if extra:
                errors.append(f"{path} has unexpected keys: {', '.join(extra)}")
        for key in sorted(value.keys() & properties.keys()):
            validate_schema_node(value[key], properties[key], f"{path}.{key}", errors)

    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_schema_node(item, item_schema, f"{path}[{index}]", errors)
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{path} entries must be unique")


def load_schema() -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("record schema must be a JSON object")
    return schema


def require_refs(name: str, refs: Any, errors: list[str]) -> None:
    if not isinstance(refs, list) or not refs or not all(present(item) for item in refs):
        errors.append(f"{name} must contain at least one non-empty reference")


def require_ownership(record: dict[str, Any], errors: list[str]) -> None:
    ownership = record["ownership"]
    for key in ("owner", "worktree", "branch", "base_sha"):
        if not present(ownership[key]):
            errors.append(f"{record['lifecycle_state']} requires ownership.{key}")
    if ownership["lease_fence"] <= 0:
        errors.append(f"{record['lifecycle_state']} requires a positive ownership.lease_fence")


def require_deployment(record: dict[str, Any], errors: list[str]) -> None:
    release = record["release"]
    if not present(release["merge_sha"]) or not present(release["deployed_sha"]):
        errors.append(f"{record['lifecycle_state']} requires merge_sha and deployed_sha")
    elif release["merge_sha"] != release["deployed_sha"]:
        errors.append(f"{record['lifecycle_state']} requires deployed_sha to equal merge_sha")
    if release["production_verified"] is not True:
        errors.append(f"{record['lifecycle_state']} requires release.production_verified=true")


def require_run_binding(record: dict[str, Any], errors: list[str]) -> None:
    binding = record["run_binding"]
    ownership = record["ownership"]
    release = record["release"]
    for key in ("definition_digest", "code_sha", "upstream_digest"):
        if not present(binding[key]):
            errors.append(f"{record['lifecycle_state']} requires run_binding.{key}")
    if binding["definition_digest"] != record["definition_digest"]:
        errors.append("run binding definition does not match the record definition")
    if present(release["deployed_sha"]) and binding["code_sha"] != release["deployed_sha"]:
        errors.append("run binding code_sha does not match deployed_sha")
    if binding["lease_fence"] != ownership["lease_fence"]:
        errors.append("run binding lease fence does not match ownership fence")
    if binding["run_generation"] <= 0:
        errors.append("accepted run binding requires a positive run_generation")


def require_rebuild(record: dict[str, Any], allow_not_applicable: bool, errors: list[str]) -> None:
    release = record["release"]
    applicability = release["rebuild_applicability"]
    if applicability == "REQUIRED":
        if not present(release["production_rebuild_receipt"]):
            errors.append("required production rebuild lacks a receipt")
        if release["not_applicable_reason"] is not None:
            errors.append("required production rebuild cannot carry a not-applicable reason")
    elif applicability == "NOT_APPLICABLE":
        if not allow_not_applicable:
            errors.append("this state or disposition requires a production rebuild")
        if not present(release["not_applicable_reason"]):
            errors.append("NOT_APPLICABLE rebuild requires a reason")
        if release["production_rebuild_receipt"] is not None:
            errors.append("NOT_APPLICABLE rebuild cannot carry a rebuild receipt")


def validate_disposition(record: dict[str, Any], errors: list[str]) -> None:
    disposition = record["disposition"]
    asset_type = record["asset_type"]
    quality = record["quality"]
    coverage = record["producer_coverage"]
    change = quality["change_kind"]
    comparison = quality["output_comparison"]

    require_refs("quality.baseline_refs", quality["baseline_refs"], errors)
    require_refs("quality.result_refs", quality["result_refs"], errors)

    if disposition == "OPTIMIZED":
        if change != "OPTIMIZATION" or comparison != "EQUIVALENT":
            errors.append("OPTIMIZED requires OPTIMIZATION plus EQUIVALENT output")
        if not present(quality["performance_gain_ref"]):
            errors.append("OPTIMIZED requires measured performance evidence")
    elif disposition == "ENRICHED_CORRECTED":
        if change != "CORRECTNESS_ENRICHMENT" or comparison != "EXPECTED_DELTA":
            errors.append("ENRICHED_CORRECTED requires CORRECTNESS_ENRICHMENT plus EXPECTED_DELTA")
        if not present(quality["expected_delta_ref"]):
            errors.append("ENRICHED_CORRECTED requires expected-delta evidence")
    elif disposition == "EXPANDED_ADOPTION":
        if change != "ADOPTION" or comparison not in {"EQUIVALENT", "NOT_APPLICABLE"}:
            errors.append("EXPANDED_ADOPTION requires ADOPTION plus EQUIVALENT or NOT_APPLICABLE output")
    elif disposition == "JUSTIFIED_NO_CHANGE":
        if change != "NONE" or comparison not in {"EQUIVALENT", "NOT_APPLICABLE"}:
            errors.append("JUSTIFIED_NO_CHANGE requires NONE plus EQUIVALENT or NOT_APPLICABLE output")
    elif disposition == "MERGED_SPLIT":
        if change != "DISPOSITION" or comparison != "NOT_APPLICABLE":
            errors.append("MERGED_SPLIT requires DISPOSITION plus NOT_APPLICABLE output")
    elif disposition == "RETAINED_LIMITED_USE":
        if change not in {"NONE", "DISPOSITION"} or comparison not in {"EQUIVALENT", "NOT_APPLICABLE"}:
            errors.append("RETAINED_LIMITED_USE requires a bounded disposition/no-change proof")
    elif disposition == "RETIRED_SUPERSEDED":
        if change != "DISPOSITION" or comparison != "NOT_APPLICABLE":
            errors.append("RETIRED_SUPERSEDED requires DISPOSITION plus NOT_APPLICABLE output")
    elif disposition == "SOURCE_ONLY":
        if asset_type != "SOURCE" or change not in {"NONE", "DISPOSITION"} or comparison != "NOT_APPLICABLE":
            errors.append("SOURCE_ONLY requires SOURCE type and a NOT_APPLICABLE output comparison")
    elif disposition == "SERVICE_PROBE":
        if asset_type not in {"SERVICE", "PROBE"} or change not in {"NONE", "DISPOSITION"}:
            errors.append("SERVICE_PROBE requires SERVICE/PROBE type and a no-change/disposition proof")
        if comparison not in {"EQUIVALENT", "NOT_APPLICABLE"}:
            errors.append("SERVICE_PROBE requires EQUIVALENT or NOT_APPLICABLE output")
    elif disposition == "PRODUCER_COVERED":
        if asset_type != "PRODUCER_COVERED" or change != "DISPOSITION" or comparison != "NOT_APPLICABLE":
            errors.append("PRODUCER_COVERED requires its matching type and inherited-receipt disposition proof")
        producer_id = coverage["covered_by_asset_id"]
        rebuild_receipt = coverage["inherited_production_rebuild_receipt"]
        acceptance_receipt = coverage["inherited_acceptance_receipt"]
        if not present(producer_id) or producer_id == record["asset_id"]:
            errors.append("PRODUCER_COVERED requires a distinct covered_by_asset_id")
        if not present(rebuild_receipt) or rebuild_receipt not in quality["result_refs"]:
            errors.append("PRODUCER_COVERED requires the inherited producer rebuild receipt in result_refs")
        if not present(acceptance_receipt) or acceptance_receipt not in record["evidence"]["references"]:
            errors.append("PRODUCER_COVERED requires the inherited producer acceptance receipt in evidence.references")

    should_skip_rebuild = disposition in NO_REBUILD_DISPOSITIONS
    if should_skip_rebuild and record["release"]["rebuild_applicability"] != "NOT_APPLICABLE":
        errors.append(f"{disposition} must not fabricate a production rebuild")
    if asset_type == "BUILD" and not should_skip_rebuild and record["release"]["rebuild_applicability"] != "REQUIRED":
        errors.append(f"BUILD asset with {disposition} requires a production rebuild")

    coverage_values = tuple(coverage.values())
    if asset_type == "PRODUCER_COVERED" and disposition != "PRODUCER_COVERED":
        errors.append("PRODUCER_COVERED asset_type requires the matching disposition")
    if disposition != "PRODUCER_COVERED" and any(value is not None for value in coverage_values):
        errors.append("producer_coverage fields must be null for non-covered dispositions")


def validate(record: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    validate_schema_node(record, schema or load_schema(), "$", errors)
    if errors:
        return errors

    state = record["lifecycle_state"]
    disposition = record["disposition"]
    dag = record["dag"]
    quality = record["quality"]
    release = record["release"]
    evidence = record["evidence"]

    if state == "QUARANTINED":
        if not record["blockers"]:
            errors.append("QUARANTINED requires at least one blocker")
        return errors

    rank = STATE_RANK[state]
    if rank >= STATE_RANK["ANALYZED"]:
        if dag["hard_edges_verified"] is not True:
            errors.append(f"{state} requires dag.hard_edges_verified=true")
        require_refs("quality.baseline_refs", quality["baseline_refs"], errors)

    if state in {"OPTIMIZED", "JUSTIFIED_NO_CHANGE"} or rank >= STATE_RANK["INTEGRATED"]:
        if disposition is None:
            errors.append(f"{state} requires a selected disposition")
        require_refs("quality.result_refs", quality["result_refs"], errors)
        if quality["output_comparison"] in {"NOT_RUN", "FAILED"}:
            errors.append(f"{state} requires a completed, successful output comparison")

    if state == "JUSTIFIED_NO_CHANGE" and disposition != "JUSTIFIED_NO_CHANGE":
        errors.append("JUSTIFIED_NO_CHANGE lifecycle requires its matching disposition")
    if state == "OPTIMIZED" and disposition == "JUSTIFIED_NO_CHANGE":
        errors.append("OPTIMIZED lifecycle cannot carry JUSTIFIED_NO_CHANGE disposition")

    if rank >= STATE_RANK["INTEGRATED"]:
        require_ownership(record, errors)
        if not present(release["merge_sha"]):
            errors.append(f"{state} requires release.merge_sha")

    if rank >= STATE_RANK["DEPLOYED"]:
        require_deployment(record, errors)

    if state == "REBUILT_ONCE":
        require_rebuild(record, allow_not_applicable=False, errors=errors)
        require_run_binding(record, errors)

    if rank >= STATE_RANK["INDEPENDENTLY_VERIFIED"]:
        allow_not_applicable = disposition in NO_REBUILD_DISPOSITIONS or record["asset_type"] != "BUILD"
        require_rebuild(record, allow_not_applicable=allow_not_applicable, errors=errors)
        require_run_binding(record, errors)
        require_refs("evidence.references", evidence["references"], errors)
        if evidence["independent_verdict"] != "ACCEPT":
            errors.append(f"{state} requires evidence.independent_verdict='ACCEPT'")
        if disposition is not None:
            validate_disposition(record, errors)

    if state == "FROZEN":
        if evidence["protected_terminal_writer"] is not True:
            errors.append("FROZEN requires a protected terminal evidence writer")
        if not present(evidence["accepted_receipt"]):
            errors.append("FROZEN requires evidence.accepted_receipt")
        if record["blockers"]:
            errors.append("FROZEN cannot retain blockers")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()

    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        schema = load_schema()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    if not isinstance(record, dict):
        print("INVALID: top-level value must be an object", file=sys.stderr)
        return 2

    errors = validate(record, schema)
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
