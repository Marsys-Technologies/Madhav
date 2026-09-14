"""Deterministic non-person proof for L1-SLICE-RESOURCE-CONFIG-01."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import timedelta
import json
from pathlib import Path
from typing import Any, Mapping

from .data_plane_contracts import (
    CalculationContext,
    ClockInterval,
    ConfigurationOccurrence,
    ContractError,
    EpistemicClass,
    FactEnvelope,
    L0_RESOURCE_CONFIG_DIGEST,
    L0_RESOURCE_CONFIG_GENERATION_ID,
    L0_SEMANTIC_RELEASE_DIGEST,
    L0_SEMANTIC_RELEASE_ID,
    L1_CONTRACT_VERSION,
    MissingnessState,
    OccurrenceState,
    QualificationState,
    SensitivityResult,
    canonical_json,
    content_sha256,
    parse_aware_instant,
    stable_uuid,
)


SLICE_ID = "L1-SLICE-RESOURCE-CONFIG-01"
SLICE_GENERATION_ID = "l1-resource-config-g1"
_DEFAULT_FIXTURE = Path(__file__).parent / "__tests__" / "fixtures" / "l1_resource_config_non_person_v1.json"

_ACCEPTED_L0_DEPENDENCIES = frozenset({
    "l0:graha:SUN",
    "l0:graha:JUP",
    "l0:ayanamsha:lahiri_chitrapaksha",
    "l0:house_convention:whole_sign",
    "l0:karaka_school:jaimini_eight_karaka",
})
_ADMITTED_VARGA_TARGETS = frozenset({
    ("D9", "parasara_standard_v1", "relationship"),
})


def load_fixture(path: str | Path = _DEFAULT_FIXTURE) -> dict[str, Any]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    if not str(fixture.get("fixture_id", "")).startswith("synthetic.non_person."):
        raise ContractError("the L1 slice accepts deterministic non-person fixtures only")
    if not str(fixture.get("chart_id", "")).startswith("synthetic:"):
        raise ContractError("the L1 slice cannot consume a stored/personal chart identity")
    if not str(fixture.get("subject_id", "")).startswith("synthetic-subject:"):
        raise ContractError("the L1 slice cannot consume a personal subject identity")
    return fixture


def _context(fixture: Mapping[str, Any]) -> CalculationContext:
    return CalculationContext(
        subject_id=str(fixture["subject_id"]),
        chart_id=str(fixture["chart_id"]),
        build_id=str(fixture["build_id"]),
        generation_id=SLICE_GENERATION_ID,
        instant_iso=str(fixture["instant_iso"]),
        latitude_deg=float(fixture["latitude_deg"]),
        longitude_deg=float(fixture["longitude_deg"]),
        timezone_name=str(fixture["timezone_name"]),
        input_precision=str(fixture["input_precision"]),
        frame=str(fixture["frame"]),
        ayanamsha_id=str(fixture["ayanamsha_id"]),
        node_type=str(fixture["node_type"]),
        house_convention=str(fixture["house_convention"]),
        varga=str(fixture["varga"]),
        varga_formula=str(fixture["varga_formula"]),
        varga_domain=str(fixture["varga_domain"]),
        karaka_school=str(fixture["karaka_school"]),
        engine_version=str(fixture["engine_version"]),
    )


def _fact(context: CalculationContext, spec: Mapping[str, Any]) -> FactEnvelope:
    return FactEnvelope(
        context=context,
        category=str(spec["category"]),
        subject=str(spec["subject"]),
        key=str(spec["key"]),
        grain=str(spec["grain"]),
        unit=spec.get("unit"),
        epistemic_class=EpistemicClass(spec["epistemic_class"]),
        verification_class=str(spec["verification_class"]),
        missingness=MissingnessState(spec.get("missingness", "present")),
        value_num=spec.get("value_num"),
        value_text=spec.get("value_text"),
        value_json=spec.get("value_json"),
        reason=spec.get("reason"),
        source_dependencies=tuple(spec.get("source_dependencies", [])),
        variant_identity=tuple(spec.get("variant_identity", [])),
    )


def _d1_sign(longitude: float) -> int:
    if not 0.0 <= longitude < 360.0:
        raise ContractError("varga sensitivity longitude must be within [0, 360)")
    return int(longitude // 30.0) + 1


def _varga_sign(longitude: float, *, varga: str, formula: str, domain: str) -> int:
    target = (varga, formula, domain)
    if target not in _ADMITTED_VARGA_TARGETS:
        raise ContractError(f"unadmitted varga sensitivity target: {target!r}")
    if target == ("D9", "parasara_standard_v1", "relationship"):
        from .ga_vargas_writer import _compute_d9_navamsa

        return int(_compute_d9_navamsa(longitude)) + 1
    raise ContractError(f"no evaluator for varga sensitivity target: {target!r}")


def _sensitivity(context: CalculationContext, fact: FactEnvelope, spec: Mapping[str, Any]) -> SensitivityResult:
    baseline = float(spec["baseline_input"])
    perturbed = float(spec["perturbed_input"])
    if fact.value_num is None or float(fact.value_num) != baseline:
        raise ContractError("sensitivity baseline must equal the referenced fact value")
    target_varga = str(spec["target_varga"])
    target_formula = str(spec["target_varga_formula"])
    target_domain = str(spec["target_varga_domain"])
    baseline_d1 = _d1_sign(baseline)
    perturbed_d1 = _d1_sign(perturbed)
    baseline_output = _varga_sign(
        baseline, varga=target_varga, formula=target_formula, domain=target_domain,
    )
    perturbed_output = _varga_sign(
        perturbed, varga=target_varga, formula=target_formula, domain=target_domain,
    )
    segment_width = 30.0 / 9.0
    baseline_remainder = baseline % segment_width
    perturbed_remainder = perturbed % segment_width
    boundary_distance = min(
        baseline_remainder,
        segment_width - baseline_remainder,
        perturbed_remainder,
        segment_width - perturbed_remainder,
    )
    classification = "changed" if baseline_output != perturbed_output else "unchanged"
    return SensitivityResult(
        context_id=context.context_id,
        fact_id=fact.fact_id,
        perturbation_id=str(spec["perturbation_id"]),
        target_varga=target_varga,
        target_varga_formula=target_formula,
        target_varga_domain=target_domain,
        baseline_input=baseline,
        perturbed_input=perturbed,
        baseline_d1_output=baseline_d1,
        perturbed_d1_output=perturbed_d1,
        baseline_output=baseline_output,
        perturbed_output=perturbed_output,
        boundary_distance=boundary_distance,
        classification=classification,
        reason=(f"D1={baseline_d1}->{perturbed_d1}; {target_varga}/"
                f"{target_formula}/{target_domain}={baseline_output}->{perturbed_output}; "
                f"computed_segment_width={segment_width}"),
    )


def build_slice(fixture: Mapping[str, Any]) -> dict[str, Any]:
    if not str(fixture.get("fixture_id", "")).startswith("synthetic.non_person."):
        raise ContractError("the L1 slice accepts deterministic non-person fixtures only")
    if not str(fixture.get("chart_id", "")).startswith("synthetic:"):
        raise ContractError("the L1 slice cannot consume a stored/personal chart identity")
    if not str(fixture.get("subject_id", "")).startswith("synthetic-subject:"):
        raise ContractError("the L1 slice cannot consume a personal subject identity")
    from brahmagyan.l0_resource_config_slice import RESOURCE_CONFIG_SLICE, SLICE_DIGEST

    if SLICE_DIGEST != L0_RESOURCE_CONFIG_DIGEST:
        raise ContractError("accepted L0 resource/config package digest mismatch")
    if RESOURCE_CONFIG_SLICE["semantic_release_id"] != L0_SEMANTIC_RELEASE_ID:
        raise ContractError("accepted L0 semantic release identity mismatch")
    context = _context(fixture)
    facts = [_fact(context, spec) for spec in fixture["facts"]]
    facts_by_key = {fact.key: fact for fact in facts}
    if len(facts_by_key) != len(facts):
        raise ContractError("fixture fact keys must be unique")
    emitted_ids = {fact.fact_id for fact in facts}
    resolved_facts: list[FactEnvelope] = []
    for fact in facts:
        resolved_dependencies: list[str] = []
        for dependency in fact.source_dependencies:
            if dependency.startswith("fixture_fact:"):
                dependency_key = dependency.removeprefix("fixture_fact:")
                if dependency_key not in facts_by_key:
                    raise ContractError(f"unresolved fixture dependency: {dependency_key}")
                resolved_dependencies.append(facts_by_key[dependency_key].fact_id)
            elif dependency in _ACCEPTED_L0_DEPENDENCIES:
                resolved_dependencies.append(dependency)
            else:
                raise ContractError(
                    f"dependency is not resolved by accepted L0 release: {dependency}"
                )
        resolved_facts.append(replace(fact, source_dependencies=tuple(resolved_dependencies)))
    facts = resolved_facts
    facts_by_key = {fact.key: fact for fact in facts}
    for fact in facts:
        for dependency in fact.source_dependencies:
            if dependency not in emitted_ids and dependency not in _ACCEPTED_L0_DEPENDENCIES:
                raise ContractError(
                    f"dependency is neither emitted nor resolved in accepted L0: {dependency}"
                )

    occurrence_spec = fixture["configuration"]
    constituent_ids = tuple(facts_by_key[key].fact_id for key in occurrence_spec["constituent_fact_keys"])
    occurrence = ConfigurationOccurrence(
        context=context,
        configuration_id=str(occurrence_spec["configuration_id"]),
        configuration_version=str(occurrence_spec["configuration_version"]),
        source_rule_id=str(occurrence_spec["source_rule_id"]),
        source_rule_version=str(occurrence_spec["source_rule_version"]),
        qualification_state=QualificationState(occurrence_spec["qualification_state"]),
        state=OccurrenceState(occurrence_spec["state"]),
        participants=tuple(occurrence_spec["participants"]),
        satisfied_clauses=tuple(occurrence_spec["satisfied_clauses"]),
        failed_clauses=tuple(occurrence_spec["failed_clauses"]),
        exceptions=tuple(occurrence_spec.get("exceptions", [])),
        cancellations=tuple(occurrence_spec.get("cancellations", [])),
        constituent_fact_ids=constituent_ids,
    )
    if occurrence.source_rule_id != RESOURCE_CONFIG_SLICE["method"]["method_id"]:
        raise ContractError("configuration rule is not resolved by accepted L0 package")
    if occurrence.source_rule_version != RESOURCE_CONFIG_SLICE["generation_id"]:
        raise ContractError("configuration rule generation mismatches accepted L0 package")
    if occurrence.qualification_state.value != RESOURCE_CONFIG_SLICE["method"]["qualification_state"]:
        raise ContractError("configuration qualification mismatches accepted L0 package")

    sensitivity = [
        _sensitivity(context, facts_by_key[str(spec["fact_key"])], spec)
        for spec in fixture["sensitivity"]
    ]

    clock_start = parse_aware_instant(context.instant_iso)
    clock_end = clock_start + timedelta(seconds=int(fixture["clock"]["duration_seconds"]))
    clock_end_iso = clock_end.isoformat()
    clock_id = stable_uuid(
        "clock_interval", context.context_id, str(fixture["clock"]["system_id"]),
        None, 1, clock_start.isoformat(), clock_end_iso,
    )
    clock = ClockInterval(
        context=context,
        system_id=str(fixture["clock"]["system_id"]),
        interval_id=clock_id,
        parent_interval_id=None,
        level=1,
        start_iso=clock_start.isoformat(),
        end_iso=clock_end_iso,
        applicability=MissingnessState.PRESENT,
        coverage="synthetic_fixture_only",
        uncertainty_seconds=float(fixture["clock"]["uncertainty_seconds"]),
    )

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "contract_version": L1_CONTRACT_VERSION,
        "slice_id": SLICE_ID,
        "slice_generation_id": SLICE_GENERATION_ID,
        "fixture_id": fixture["fixture_id"],
        "fixture_class": "deterministic_non_person",
        "accepted_l0": {
            "semantic_release_id": L0_SEMANTIC_RELEASE_ID,
            "semantic_release_digest": L0_SEMANTIC_RELEASE_DIGEST,
            "resource_config_generation_id": L0_RESOURCE_CONFIG_GENERATION_ID,
            "resource_config_digest": L0_RESOURCE_CONFIG_DIGEST,
        },
        "resolved_l0_dependencies": [
            {
                "dependency_id": dependency,
                "semantic_release_id": L0_SEMANTIC_RELEASE_ID,
                "semantic_release_digest": L0_SEMANTIC_RELEASE_DIGEST,
            }
            for dependency in sorted({
                dependency
                for fact in facts
                for dependency in fact.source_dependencies
                if dependency in _ACCEPTED_L0_DEPENDENCIES
            })
        ],
        "context": {**asdict(context), "context_id": context.context_id, "generation_key": context.generation_key},
        "facts": [fact.to_dict() for fact in facts],
        "configuration": occurrence.to_dict(),
        "sensitivity": [asdict(item) for item in sensitivity],
        "clock": asdict(clock),
        "bhavat_bhavam": {
            "method_id": "bhavat_bhavam.odd_house_nonrecursive.v1",
            "qualification_state": "UNQUALIFIED_SOURCE",
            "application_owner": "L2 Bodha",
            "applied": False,
            "positive_doctrinal_arm": "NOT_REACHABLE",
            "primary_house_facts_preserved": True,
        },
        "missingness_states_proved": sorted({fact.missingness.value for fact in facts}),
        "terminal_truth": {
            "producer_fixture": "PASS",
            "doctrinal_positive": "NOT_REACHABLE",
            "integrated": False,
            "deployed": False,
            "consumer_value_demonstrated": False,
            "empirically_evaluated": False,
        },
    }
    payload["content_sha256"] = content_sha256(payload)
    return payload


def build_default_slice() -> dict[str, Any]:
    return build_slice(load_fixture())


if __name__ == "__main__":
    print(canonical_json(build_default_slice()))
