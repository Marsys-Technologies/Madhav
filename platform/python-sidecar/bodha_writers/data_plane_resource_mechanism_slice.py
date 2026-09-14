"""Deterministic non-person L2-SLICE-RESOURCE-MECHANISM-01."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from bodha_writers.data_plane_contracts import (
    ACCEPTED_L0_RELEASE,
    ACCEPTED_L1_SLICE_DIGEST,
    ACCEPTED_L1_TERMINAL,
    CONTRACT_VERSION,
    content_digest,
    stable_structural_id,
)


SLICE_ID = "L2-SLICE-RESOURCE-MECHANISM-01"
SLICE_VERSION = "1.0"
_DOMAIN_ALIASES = {
    "financial": "resources",
    "finance": "resources",
    "income": "receipts",
    "savings": "retention",
    "debt_relief": "relief",
}


def _domains(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for item in items:
        name = _DOMAIN_ALIASES.get(str(item["domain"]).lower(), str(item["domain"]).lower())
        role = str(item["role"]).lower()
        normalized[f"{name}:{role}"] = {"domain": name, "role": role}
    return [normalized[key] for key in sorted(normalized)]


def _assert_fixture(fixture: Mapping[str, Any]) -> None:
    if fixture.get("fixture_class") != "ENGINEERING_ONLY":
        raise ValueError("slice fixture must be ENGINEERING_ONLY")
    if fixture.get("promotable") is not False:
        raise ValueError("engineering fixture must be non-promotable")
    if fixture.get("person_data") is not False:
        raise ValueError("slice must contain no person data")
    if fixture.get("accepted_l1_slice_digest") != ACCEPTED_L1_SLICE_DIGEST:
        raise ValueError("wrong accepted L1 slice digest")
    if fixture.get("accepted_l0_release") != ACCEPTED_L0_RELEASE:
        raise ValueError("wrong accepted L0 release")
    if fixture.get("accepted_l1_terminal") != ACCEPTED_L1_TERMINAL:
        raise ValueError("wrong accepted L1 terminal")
    expected = fixture.get("expected_context") or {}
    selected = fixture.get("selected_configuration") or {}
    for key in ("chart_id", "calculation_context_id", "generation_id", "ayanamsha_id"):
        if selected.get(key) != expected.get(key):
            raise ValueError(f"wrong slice {key}")
    if selected.get("qualification_state") != "UNQUALIFIED_SOURCE":
        raise ValueError("Bhavat source must remain unqualified")


def build_resource_mechanism_slice(fixture: Mapping[str, Any]) -> dict[str, Any]:
    _assert_fixture(fixture)
    selected = deepcopy(fixture["selected_configuration"])
    participants = sorted(
        deepcopy(selected["participants"]), key=lambda x: (x["role"], x["subject"]),
    )
    domains = _domains(deepcopy(selected["domains"]))
    roots = {r["root_id"]: r for r in selected["evidence_roots"]}
    paths = []
    independent_groups: set[str] = set()
    for path in selected["paths"]:
        root_id = path["root_id"]
        if root_id not in roots:
            raise ValueError(f"unreachable evidence root: {root_id}")
        polarity = int(path["polarity"])
        if polarity not in (-1, 1):
            raise ValueError("path polarity must be signed")
        root_group = str(roots[root_id].get("shared_root_group") or root_id)
        supplied_group = path.get("shared_root_group")
        if supplied_group is not None and str(supplied_group) != root_group:
            raise ValueError("path shared-root label disagrees with root ancestry")
        independent_groups.add(root_group)
        paths.append({
            **deepcopy(path),
            "polarity": polarity,
            "shared_root_group": root_group,
        })
    paths.sort(key=lambda x: (x["relation"], x["actor"], x["target"], x["root_id"]))

    occurrence = deepcopy(selected["occurrence_ledger"])
    condition = deepcopy(selected["condition_ledger"])
    if occurrence.get("unit") != "probability_like_structural_score":
        raise ValueError("occurrence ledger has the wrong unit")
    if occurrence.get("polarity") != "higher_is_more_formed":
        raise ValueError("occurrence ledger has the wrong polarity")
    if condition.get("unit") != "affliction_0_10":
        raise ValueError("condition ledger has the wrong unit")
    if condition.get("polarity") != "higher_is_more_afflicted":
        raise ValueError("condition ledger has the wrong polarity")
    if not 0.0 <= float(occurrence["value"]) <= 1.0:
        raise ValueError("occurrence must use [0,1]")
    if not 0.0 <= float(condition["affliction_value"]) <= 10.0:
        raise ValueError("condition affliction must use [0,10]")
    for component in condition.get("components", []):
        if int(component.get("polarity", 0)) not in (-1, 1):
            raise ValueError("condition component polarity must be exactly -1 or +1")
    cancellation = deepcopy(selected["cancellation"])
    target = next((p for p in paths if p["path_id"] == cancellation["target_path_id"]), None)
    if target is None or target["polarity"] != cancellation["target_original_polarity"]:
        raise ValueError("cancellation target/polarity mismatch")
    cancellation["resulting_role"] = (
        "attenuated_opposition" if target["polarity"] == -1 else "attenuated_support"
    )

    identity_payload = {
        "rule_id": selected["rule_id"],
        "participants": participants,
        "domains": domains,
        "configuration_roles": selected["configuration_roles"],
    }
    configuration_id = stable_structural_id("configuration", identity_payload)
    proposition_id = stable_structural_id("proposition", {
        "configuration_id": configuration_id,
        "claim_class": selected["claim_class"],
        "qualification_state": selected["qualification_state"],
    })
    relationships = [{
        **p,
        "relationship_id": stable_structural_id("relationship", {
            "configuration_id": configuration_id,
            "actor": p["actor"], "relation": p["relation"], "target": p["target"],
            "polarity": p["polarity"], "basis": p["basis"],
        }),
    } for p in paths]
    mechanism_id = stable_structural_id("mechanism", {
        "configuration_id": configuration_id,
        "relationship_ids": sorted(p["relationship_id"] for p in relationships),
        "condition_ids": sorted(x["condition_id"] for x in condition["components"]),
    })

    bundle = {
        "slice_id": SLICE_ID,
        "slice_version": SLICE_VERSION,
        "contract_version": CONTRACT_VERSION,
        "fixture_class": "ENGINEERING_ONLY",
        "promotable": False,
        "upstream": {
            "accepted_l0_release": ACCEPTED_L0_RELEASE,
            "accepted_l1_terminal": ACCEPTED_L1_TERMINAL,
            "accepted_l1_slice_digest": ACCEPTED_L1_SLICE_DIGEST,
            **deepcopy(fixture["expected_context"]),
        },
        "configuration_id": configuration_id,
        "proposition_id": proposition_id,
        "mechanism_id": mechanism_id,
        "participants": participants,
        "configuration_roles": deepcopy(selected["configuration_roles"]),
        "domains": domains,
        "occurrence_ledger": occurrence,
        "condition_ledger": condition,
        "relationships": relationships,
        "independent_support_count": len(independent_groups),
        "shared_root_groups": sorted(independent_groups),
        "cancellation": cancellation,
        "contradictions": deepcopy(selected["contradictions"]),
        "rivals": deepcopy(selected["rivals"]),
        "grounding": {
            "qualification_state": "UNQUALIFIED_SOURCE",
            "rule_id": selected["rule_id"],
            "citation_granularity": "rule",
            "positive_doctrinal_arm": "NOT_REACHABLE",
            "engineering_fixture_authority": "NON_DOCTRINAL_NON_PROMOTABLE",
        },
        "missingness": deepcopy(selected["missingness"]),
        "discovery_pointers": deepcopy(selected["discovery_pointers"]),
        "hydration_required": True,
        "temporal_semantics_status": "UNAVAILABLE_AT_L2",
        "activation_windows": None,
    }
    bundle["content_digest"] = content_digest(bundle)
    return bundle
