"""Validated producer adapter for ``L0-SLICE-RESOURCE-CONFIG-01``.

This is global/reference data only.  It cannot accept chart, subject, birth or
observation payloads and cannot emit an occurrence or interpretation.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from brahmagyan.l0_semantic_release import (
    SEMANTIC_RELEASE,
    SEMANTIC_RELEASE_DIGEST,
    SEMANTIC_RELEASE_ID,
)


SLICE_PATH = Path(__file__).with_name("l0_resource_config_slice_v1.json")
QUALIFICATION_STATES = frozenset(
    {
        "READABLE_NOT_EXECUTABLE",
        "QUALIFIED_EXECUTABLE",
        "UNQUALIFIED_SOURCE",
        "UNSUPPORTED_SCOPE",
        "METHOD_INAPPLICABLE",
    }
)
FORBIDDEN_PAYLOAD_FIELDS = frozenset(
    {"subject_id", "chart_id", "birth_data", "personal_observations"}
)


class ResourceConfigSliceError(ValueError):
    """Raised when a producer package or request violates the frozen contract."""


def package_digest_for_validation(package: dict[str, Any]) -> str:
    """Compute a candidate package digest for validation and negative tests."""
    payload = deepcopy(package)
    payload["content_sha256"] = ""
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def validate_package(package: dict[str, Any]) -> None:
    if package.get("schema_version") != "madhav-l0-resource-config-slice/v1":
        raise ResourceConfigSliceError("unsupported resource-config slice schema")
    if package.get("slice_id") != "L0-SLICE-RESOURCE-CONFIG-01":
        raise ResourceConfigSliceError("wrong resource-config slice identity")
    if package.get("semantic_release_id") != SEMANTIC_RELEASE_ID:
        raise ResourceConfigSliceError("semantic release ID mismatch")
    if package.get("semantic_release_digest") != SEMANTIC_RELEASE_DIGEST:
        raise ResourceConfigSliceError("semantic release digest mismatch")
    if package.get("content_sha256") != package_digest_for_validation(package):
        raise ResourceConfigSliceError("resource-config content digest mismatch")
    if set(package.get("qualification_states", [])) != QUALIFICATION_STATES:
        raise ResourceConfigSliceError("qualification state vocabulary mismatch")
    if package.get("grain") != [
        "semantic_release_id",
        "method_id",
        "rule_clause_id",
        "source_passage_id",
        "operator_scope_id",
    ]:
        raise ResourceConfigSliceError("composite grain mismatch")
    if package.get("scope", {}).get("kind") != "global_reference":
        raise ResourceConfigSliceError("slice must remain global/reference scoped")
    leaked = FORBIDDEN_PAYLOAD_FIELDS.intersection(_walk_keys(package))
    if leaked:
        raise ResourceConfigSliceError(f"forbidden personal-scope fields: {sorted(leaked)}")

    mapping = package.get("map", {})
    if set(mapping) != {str(i) for i in range(1, 13)}:
        raise ResourceConfigSliceError("Bhavat Bhavam map must contain all 12 houses")
    expected = {
        "1": [1, 7], "2": [], "3": [2, 8], "4": [], "5": [3, 9],
        "6": [], "7": [4, 10], "8": [], "9": [5, 11], "10": [],
        "11": [6, 12], "12": [],
    }
    if mapping != expected:
        raise ResourceConfigSliceError("frozen odd/even map changed")
    restraints = package.get("method", {}).get("restraints", {})
    if restraints != {
        "never_generator": True,
        "no_chaining": True,
        "never_outranks_primary": True,
    }:
        raise ResourceConfigSliceError("frozen restraints changed")

    state = package.get("method", {}).get("qualification_state")
    if state == "UNQUALIFIED_SOURCE":
        if package.get("epistemic_class") is not None:
            raise ResourceConfigSliceError(
                "unqualified source cannot declare a qualified epistemic class"
            )
        if package.get("target_epistemic_class") != "QUALIFIED_RULE":
            raise ResourceConfigSliceError("unqualified source target class mismatch")
        if package.get("evidence_maturity") != "present":
            raise ResourceConfigSliceError("unqualified source maturity must be present")
    elif state == "QUALIFIED_EXECUTABLE":
        if package.get("epistemic_class") != "QUALIFIED_RULE":
            raise ResourceConfigSliceError("qualified rule epistemic class mismatch")
        if package.get("evidence_maturity") != "qualified":
            raise ResourceConfigSliceError("qualified rule maturity mismatch")

    catalogue_specs = {
        "concepts": "concept_id",
        "roles": "role_id",
        "domains": "domain_id",
        "outcomes": "outcome_id",
        "methods": "method_id",
        "operator_scopes": "operator_scope_id",
    }
    released_ids = {
        name: {row[id_field] for row in SEMANTIC_RELEASE["catalogues"][name]}
        for name, id_field in catalogue_specs.items()
    }
    refs = {
        "concepts": set(package.get("rule_clause", {}).get("concept_ids", [])),
        "roles": set(package.get("rule_clause", {}).get("role_ids", [])),
        "domains": {
            package.get("consumer_question", {}).get("domain_id"),
            *package.get("rule_clause", {}).get("domain_ids", []),
        },
        "outcomes": {
            *package.get("consumer_question", {}).get("outcome_ids", []),
            *package.get("rule_clause", {}).get("outcome_ids", []),
        },
        "methods": {package.get("method", {}).get("method_id")},
        "operator_scopes": {package.get("method", {}).get("operator_scope_id")},
    }
    for catalogue, referenced in refs.items():
        missing = {value for value in referenced if value} - released_ids[catalogue]
        if missing:
            raise ResourceConfigSliceError(
                f"unreleased {catalogue} references: {sorted(missing)}"
            )

    witness = package.get("source_witness", {})
    if package.get("rule_clause", {}).get("source_passage_id") != witness.get(
        "source_passage_id"
    ):
        raise ResourceConfigSliceError("rule/source passage identity mismatch")
    if state == "QUALIFIED_EXECUTABLE":
        required = (
            "work_id", "edition_id", "translation_id", "passage_locator",
            "ancestry_root_id", "rights_use_status",
        )
        if any(not witness.get(field) for field in required):
            raise ResourceConfigSliceError("executable clause lacks exact source/rights fields")
        if witness.get("rights_use_status") not in {"PUBLIC_DOMAIN_VERIFIED", "LICENSED_FOR_USE"}:
            raise ResourceConfigSliceError("executable clause lacks admitted rights/use status")
    elif state != "UNQUALIFIED_SOURCE":
        raise ResourceConfigSliceError("current Bhavat package must remain unqualified")

    fixture_ids = {fixture.get("fixture_id") for fixture in package.get("fixtures", [])}
    required_fixtures = {
        "qualified-positive", "readable-candidate-not-executable", "missing-witness",
        "even-house-inapplicable", "recursive-prohibited", "alias-parity",
        "changed-generation-rollback",
    }
    if fixture_ids != required_fixtures:
        raise ResourceConfigSliceError("frozen fixture set mismatch")
    positive = next(f for f in package["fixtures"] if f["fixture_id"] == "qualified-positive")
    if positive.get("expected_state") != "NOT_REACHABLE":
        raise ResourceConfigSliceError("qualified positive must remain NOT_REACHABLE")


def _load() -> dict[str, Any]:
    package = json.loads(SLICE_PATH.read_text(encoding="utf-8"))
    validate_package(package)
    return package


RESOURCE_CONFIG_SLICE: dict[str, Any] = _load()
SLICE_ID: str = RESOURCE_CONFIG_SLICE["slice_id"]
SLICE_DIGEST: str = RESOURCE_CONFIG_SLICE["content_sha256"]


def classify_bhavat_bhavam(
    primary_house: int,
    *,
    recursive: bool = False,
    as_generator: bool = False,
    outrank_primary: bool = False,
) -> dict[str, Any]:
    """Return the frozen reference result and its honest qualification state."""
    if isinstance(primary_house, bool) or not isinstance(primary_house, int):
        raise ResourceConfigSliceError("primary house must be an integer")
    if primary_house < 1 or primary_house > 12:
        raise ResourceConfigSliceError("primary house must be between 1 and 12")
    if recursive or as_generator or outrank_primary:
        state = "UNSUPPORTED_SCOPE"
        derived: list[int] = []
    elif primary_house % 2 == 0:
        state = "METHOD_INAPPLICABLE"
        derived = []
    else:
        state = "UNQUALIFIED_SOURCE"
        derived = list(RESOURCE_CONFIG_SLICE["map"][str(primary_house)])
    return {
        "slice_id": SLICE_ID,
        "semantic_release_id": SEMANTIC_RELEASE_ID,
        "generation_id": RESOURCE_CONFIG_SLICE["generation_id"],
        "method_id": RESOURCE_CONFIG_SLICE["method"]["method_id"],
        "rule_clause_id": RESOURCE_CONFIG_SLICE["rule_clause"]["rule_clause_id"],
        "source_passage_id": RESOURCE_CONFIG_SLICE["source_witness"]["source_passage_id"],
        "operator_scope_id": RESOURCE_CONFIG_SLICE["method"]["operator_scope_id"],
        "primary_house": primary_house,
        "derived_houses": derived,
        "qualification_state": state,
        "restraints": deepcopy(RESOURCE_CONFIG_SLICE["method"]["restraints"]),
    }


def validate_request_payload(payload: dict[str, Any]) -> None:
    """Reject personal/chart payload fields at the producer boundary."""
    leaked = FORBIDDEN_PAYLOAD_FIELDS.intersection(_walk_keys(payload))
    if leaked:
        raise ResourceConfigSliceError(f"forbidden personal-scope fields: {sorted(leaked)}")


def slice_digest_for_test() -> str:
    return package_digest_for_validation(RESOURCE_CONFIG_SLICE)
