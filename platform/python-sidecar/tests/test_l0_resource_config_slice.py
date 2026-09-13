from __future__ import annotations

from copy import deepcopy

import pytest

from brahmagyan.l0_resource_config_slice import (
    QUALIFICATION_STATES,
    RESOURCE_CONFIG_SLICE,
    ResourceConfigSliceError,
    SLICE_DIGEST,
    classify_bhavat_bhavam,
    package_digest_for_validation,
    slice_digest_for_test,
    validate_package,
    validate_request_payload,
)


def test_exact_composite_grain_and_five_states_are_frozen() -> None:
    assert RESOURCE_CONFIG_SLICE["grain"] == [
        "semantic_release_id",
        "method_id",
        "rule_clause_id",
        "source_passage_id",
        "operator_scope_id",
    ]
    assert set(RESOURCE_CONFIG_SLICE["qualification_states"]) == QUALIFICATION_STATES


def test_missing_witness_is_unqualified_and_positive_is_not_reachable() -> None:
    assert RESOURCE_CONFIG_SLICE["epistemic_class"] is None
    assert RESOURCE_CONFIG_SLICE["target_epistemic_class"] == "QUALIFIED_RULE"
    assert RESOURCE_CONFIG_SLICE["evidence_maturity"] == "present"
    assert RESOURCE_CONFIG_SLICE["source_witness"]["rights_use_status"] == "UNRESOLVED"
    assert RESOURCE_CONFIG_SLICE["method"]["qualification_state"] == "UNQUALIFIED_SOURCE"
    positive = next(
        fixture for fixture in RESOURCE_CONFIG_SLICE["fixtures"]
        if fixture["fixture_id"] == "qualified-positive"
    )
    assert positive["expected_state"] == "NOT_REACHABLE"
    assert classify_bhavat_bhavam(11)["qualification_state"] == "UNQUALIFIED_SOURCE"


@pytest.mark.parametrize(
    ("house", "expected"),
    [(1, [1, 7]), (3, [2, 8]), (5, [3, 9]), (7, [4, 10]), (9, [5, 11]), (11, [6, 12])],
)
def test_odd_house_map_is_preserved_but_not_promoted(house: int, expected: list[int]) -> None:
    result = classify_bhavat_bhavam(house)
    assert result["derived_houses"] == expected
    assert result["qualification_state"] == "UNQUALIFIED_SOURCE"


@pytest.mark.parametrize("house", [2, 4, 6, 8, 10, 12])
def test_even_house_is_method_inapplicable(house: int) -> None:
    result = classify_bhavat_bhavam(house)
    assert result["derived_houses"] == []
    assert result["qualification_state"] == "METHOD_INAPPLICABLE"


@pytest.mark.parametrize("kwargs", [{"recursive": True}, {"as_generator": True}, {"outrank_primary": True}])
def test_restraint_violations_are_unsupported_scope(kwargs: dict[str, bool]) -> None:
    result = classify_bhavat_bhavam(11, **kwargs)
    assert result["derived_houses"] == []
    assert result["qualification_state"] == "UNSUPPORTED_SCOPE"


def test_invalid_boundary_fails_closed() -> None:
    for invalid in (0, 13, -1, True, 1.5, "1"):
        with pytest.raises(ResourceConfigSliceError):
            classify_bhavat_bhavam(invalid)  # type: ignore[arg-type]


def test_personal_or_chart_payload_is_forbidden_at_l0_boundary() -> None:
    validate_request_payload({"primary_house": 11})
    with pytest.raises(ResourceConfigSliceError):
        validate_request_payload({"context": {"chart_id": "forbidden"}})
    with pytest.raises(ResourceConfigSliceError):
        validate_request_payload({"subject_id": "forbidden"})


def test_rights_or_passage_cannot_be_omitted_from_executable_state() -> None:
    candidate = deepcopy(RESOURCE_CONFIG_SLICE)
    candidate["method"]["qualification_state"] = "QUALIFIED_EXECUTABLE"
    candidate["epistemic_class"] = "QUALIFIED_RULE"
    candidate["epistemic_class_reason"] = None
    candidate["evidence_maturity"] = "qualified"
    candidate["content_sha256"] = package_digest_for_validation(candidate)
    with pytest.raises(ResourceConfigSliceError, match="lacks exact"):
        validate_package(candidate)


def test_all_slice_semantic_references_resolve_to_the_pinned_release() -> None:
    candidate = deepcopy(RESOURCE_CONFIG_SLICE)
    candidate["rule_clause"]["outcome_ids"].append("unreleased_outcome")
    candidate["content_sha256"] = package_digest_for_validation(candidate)
    with pytest.raises(ResourceConfigSliceError, match="unreleased outcomes"):
        validate_package(candidate)


def test_duplicate_wrapper_cannot_inflate_source_ancestry() -> None:
    lineage = RESOURCE_CONFIG_SLICE["lineage_drill"]
    assert len(lineage) == len(set(lineage))
    assert sum(item.startswith("source:") for item in lineage) == 1


def test_generation_change_preserves_map_and_prior_replay() -> None:
    fixture = next(
        item for item in RESOURCE_CONFIG_SLICE["fixtures"]
        if item["fixture_id"] == "changed-generation-rollback"
    )
    assert fixture["expected_map_change"] is False
    assert fixture["expected_prior_replayable"] is True
    assert RESOURCE_CONFIG_SLICE["compatibility"]["rollback_generation_id"]


def test_content_digest_detects_mutation() -> None:
    assert slice_digest_for_test() == SLICE_DIGEST
    changed = deepcopy(RESOURCE_CONFIG_SLICE)
    changed["map"]["11"] = [12]
    with pytest.raises(ResourceConfigSliceError):
        validate_package(changed)
