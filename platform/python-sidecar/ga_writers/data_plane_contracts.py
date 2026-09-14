"""Typed L1 Gaṇita producer contracts for the Madhav data plane.

This module is deliberately computation-only.  It does not retrieve, rank,
interpret, persist, or activate any specialist service.  The contracts make
context, identity, epistemic class, missingness, generation, and correction
semantics explicit before an L1 value is offered to a later layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import math
import uuid
from typing import Any, Iterable, Mapping, Sequence


L0_SEMANTIC_RELEASE_ID = "l0.semantic.2026-09-13.1"
L0_SEMANTIC_RELEASE_DIGEST = (
    "665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1"
)
L0_RESOURCE_CONFIG_GENERATION_ID = "l0-resource-config-g1"
L0_RESOURCE_CONFIG_DIGEST = (
    "d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a"
)
L1_CONTRACT_VERSION = "l1.data-plane.contract.1.0"
_L1_UUID_NAMESPACE = uuid.UUID("66f328d8-98a9-4f8d-aa1c-93ce43712c8d")


class ContractError(ValueError):
    """Raised when producer data would blur a governed L1 distinction."""


class MissingnessState(str, Enum):
    PRESENT = "present"
    ZERO = "zero"
    UNAVAILABLE = "unavailable"
    FLOORED = "floored"
    INAPPLICABLE = "inapplicable"
    UNQUALIFIED_SOURCE = "unqualified_source"
    FAILED = "failed"
    UNEXPLORED = "unexplored"


class EpistemicClass(str, Enum):
    ASTRONOMICAL = "astronomical"
    DETERMINISTIC_DERIVATION = "deterministic_derivation"
    RULE_DERIVED = "rule_derived"
    JUDGED = "judged"
    DOCUMENTED_APPROXIMATION = "documented_approximation"
    ENGINEERING_FIXTURE = "engineering_fixture"
    RESTRICTED_SCHOLARLY = "restricted_scholarly"


class OccurrenceState(str, Enum):
    FORMED = "formed"
    PARTIAL = "partial"
    NOT_FORMED = "not_formed"
    FAILED = "failed"
    METHOD_INAPPLICABLE = "method_inapplicable"
    UNQUALIFIED_SOURCE = "unqualified_source"


class QualificationState(str, Enum):
    QUALIFIED_EXECUTABLE = "QUALIFIED_EXECUTABLE"
    READABLE_NOT_EXECUTABLE = "READABLE_NOT_EXECUTABLE"
    UNQUALIFIED_SOURCE = "UNQUALIFIED_SOURCE"
    UNSUPPORTED = "UNSUPPORTED"
    ENGINEERING_ONLY = "ENGINEERING_ONLY"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def stable_fact_id(
    category: str,
    subject: str,
    key: str,
    chart_id: str,
    ayanamsha_id: str,
    *variant_parts: object,
    length: int = 16,
) -> str:
    """Return a semantic fact identity independent of build/generation.

    ``build_id`` is intentionally not accepted as a named input.  Rebuilds
    observe a fact; they do not redefine what the fact is about.  Legitimate
    method/formula variants belong in ``variant_parts``.
    """
    if length < 16 or length > 64:
        raise ContractError("stable fact-id length must be between 16 and 64")
    parts = (category, subject, key, chart_id, ayanamsha_id, *variant_parts)
    if any(part is None or str(part) == "" for part in parts[:5]):
        raise ContractError("stable fact-id core parts must be non-empty")
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def stable_uuid(kind: str, *identity_parts: object) -> str:
    """Return a UUID5 for a semantic row/interval identity."""
    # ``None`` is a meaningful, canonical value for an absent parent or an
    # inapplicable optional discriminator; canonical JSON preserves it as null.
    if not kind or not identity_parts:
        raise ContractError("stable UUID requires a kind and identity parts")
    name = canonical_json([kind, *identity_parts])
    return str(uuid.uuid5(_L1_UUID_NAMESPACE, name))


def parse_aware_instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f"instant must include an explicit UTC offset: {value!r}")
    return parsed


@dataclass(frozen=True)
class CalculationContext:
    subject_id: str
    chart_id: str
    build_id: str
    generation_id: str
    instant_iso: str
    latitude_deg: float
    longitude_deg: float
    timezone_name: str
    input_precision: str
    frame: str
    ayanamsha_id: str
    node_type: str
    house_convention: str
    varga: str
    varga_formula: str
    varga_domain: str
    karaka_school: str
    engine_version: str
    l0_semantic_release_id: str = L0_SEMANTIC_RELEASE_ID
    l0_semantic_release_digest: str = L0_SEMANTIC_RELEASE_DIGEST
    l0_resource_config_generation_id: str = L0_RESOURCE_CONFIG_GENERATION_ID
    l0_resource_config_digest: str = L0_RESOURCE_CONFIG_DIGEST

    def __post_init__(self) -> None:
        required = (
            self.subject_id,
            self.chart_id,
            self.build_id,
            self.generation_id,
            self.timezone_name,
            self.input_precision,
            self.ayanamsha_id,
            self.house_convention,
            self.varga,
            self.varga_formula,
            self.varga_domain,
            self.karaka_school,
            self.engine_version,
        )
        if any(not item for item in required):
            raise ContractError("calculation context fields must be non-empty")
        parse_aware_instant(self.instant_iso)
        if not math.isfinite(self.latitude_deg) or not -90 <= self.latitude_deg <= 90:
            raise ContractError("latitude must be finite and within [-90, 90]")
        if not math.isfinite(self.longitude_deg) or not -180 <= self.longitude_deg <= 180:
            raise ContractError("longitude must be finite and within [-180, 180]")
        if self.frame not in {"sidereal", "tropical"}:
            raise ContractError("frame must be sidereal or tropical")
        if self.node_type not in {"mean", "true"}:
            raise ContractError("mean and true nodes must remain explicit")
        if self.l0_semantic_release_id != L0_SEMANTIC_RELEASE_ID:
            raise ContractError("unknown L0 semantic release")
        if self.l0_semantic_release_digest != L0_SEMANTIC_RELEASE_DIGEST:
            raise ContractError("L0 semantic release digest mismatch")
        if self.l0_resource_config_generation_id != L0_RESOURCE_CONFIG_GENERATION_ID:
            raise ContractError("unknown L0 resource/config generation")
        if self.l0_resource_config_digest != L0_RESOURCE_CONFIG_DIGEST:
            raise ContractError("L0 resource/config digest mismatch")

    @property
    def context_id(self) -> str:
        """Stable calculation identity; build and generation are observations."""
        payload = asdict(self)
        payload.pop("build_id")
        payload.pop("generation_id")
        return f"l1ctx:{content_sha256(payload)[:24]}"

    @property
    def generation_key(self) -> str:
        return f"{self.context_id}@generation={self.generation_id}:build={self.build_id}"


@dataclass(frozen=True)
class FactEnvelope:
    context: CalculationContext
    category: str
    subject: str
    key: str
    grain: str
    unit: str | None
    epistemic_class: EpistemicClass
    verification_class: str
    missingness: MissingnessState = MissingnessState.PRESENT
    value_num: float | int | None = None
    value_text: str | None = None
    value_json: Any = None
    reason: str | None = None
    source_dependencies: tuple[str, ...] = field(default_factory=tuple)
    variant_identity: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not all((self.category, self.subject, self.key, self.grain, self.verification_class)):
            raise ContractError("fact identity, grain and verification must be non-empty")
        values = (self.value_num, self.value_text, self.value_json)
        populated = sum(value is not None for value in values)
        if self.missingness is MissingnessState.PRESENT and populated != 1:
            raise ContractError("present facts carry exactly one typed value")
        if self.missingness is MissingnessState.ZERO:
            if self.value_num != 0 or self.value_text is not None or self.value_json is not None:
                raise ContractError("zero is an explicit numeric zero, not missingness")
        if self.missingness not in {MissingnessState.PRESENT, MissingnessState.ZERO}:
            if populated:
                raise ContractError(f"{self.missingness.value} facts cannot carry a normal value")
            if not self.reason:
                raise ContractError(f"{self.missingness.value} facts require a reason")

    @property
    def fact_id(self) -> str:
        return stable_fact_id(
            self.category,
            self.subject,
            self.key,
            self.context.chart_id,
            self.context.ayanamsha_id,
            *self.variant_identity,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = _jsonable(self)
        payload["context_id"] = self.context.context_id
        payload["generation_key"] = self.context.generation_key
        payload["fact_id"] = self.fact_id
        return payload


@dataclass(frozen=True)
class ConfigurationOccurrence:
    context: CalculationContext
    configuration_id: str
    configuration_version: str
    source_rule_id: str
    source_rule_version: str
    qualification_state: QualificationState
    state: OccurrenceState
    participants: tuple[Mapping[str, str], ...]
    satisfied_clauses: tuple[str, ...]
    failed_clauses: tuple[str, ...]
    exceptions: tuple[str, ...] = field(default_factory=tuple)
    cancellations: tuple[str, ...] = field(default_factory=tuple)
    constituent_fact_ids: tuple[str, ...] = field(default_factory=tuple)
    epistemic_class: EpistemicClass = EpistemicClass.RULE_DERIVED
    doctrinal: bool = True

    def __post_init__(self) -> None:
        if not all((self.configuration_id, self.configuration_version, self.source_rule_id, self.source_rule_version)):
            raise ContractError("configuration and source-rule identities are required")
        if len(set(self.constituent_fact_ids)) != len(self.constituent_fact_ids):
            raise ContractError("shared-root/duplicate fact identities cannot inflate support")
        if self.qualification_state is QualificationState.UNQUALIFIED_SOURCE:
            if self.state is not OccurrenceState.UNQUALIFIED_SOURCE:
                raise ContractError("an unqualified source cannot yield a doctrinal occurrence")
        if self.state in {OccurrenceState.FORMED, OccurrenceState.PARTIAL}:
            if self.doctrinal and self.qualification_state is not QualificationState.QUALIFIED_EXECUTABLE:
                raise ContractError("positive doctrinal occurrence requires a qualified executable rule")
            if not self.doctrinal and self.qualification_state is not QualificationState.ENGINEERING_ONLY:
                raise ContractError("non-doctrinal positive occurrence must remain engineering-only")

    @property
    def occurrence_id(self) -> str:
        return stable_uuid(
            "configuration_occurrence",
            self.context.context_id,
            self.configuration_id,
            self.configuration_version,
            self.source_rule_id,
        )

    @property
    def positive_doctrinal_arm(self) -> str:
        if self.qualification_state is QualificationState.UNQUALIFIED_SOURCE:
            return "NOT_REACHABLE"
        return "REACHABLE" if self.state in {OccurrenceState.FORMED, OccurrenceState.PARTIAL} else "NOT_ASSERTED"

    def to_dict(self) -> dict[str, Any]:
        payload = _jsonable(self)
        payload["context_id"] = self.context.context_id
        payload["generation_key"] = self.context.generation_key
        payload["occurrence_id"] = self.occurrence_id
        payload["positive_doctrinal_arm"] = self.positive_doctrinal_arm
        return payload


@dataclass(frozen=True)
class TypedRelation:
    context: CalculationContext
    relation_type: str
    actor_fact_id: str
    target_fact_id: str
    method_id: str
    orb_deg: float | None
    constituent_fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all((self.relation_type, self.actor_fact_id, self.target_fact_id, self.method_id)):
            raise ContractError("typed relation requires actor, target, type and method")
        if len(set(self.constituent_fact_ids)) != len(self.constituent_fact_ids):
            raise ContractError("relation constituents must be identity-deduplicated")
        if self.orb_deg is not None and (not math.isfinite(self.orb_deg) or self.orb_deg < 0):
            raise ContractError("orb must be a finite non-negative degree value")


@dataclass(frozen=True)
class ClockInterval:
    context: CalculationContext
    system_id: str
    interval_id: str
    parent_interval_id: str | None
    level: int
    start_iso: str
    end_iso: str
    applicability: MissingnessState
    coverage: str
    uncertainty_seconds: float

    def __post_init__(self) -> None:
        start = parse_aware_instant(self.start_iso)
        end = parse_aware_instant(self.end_iso)
        if end <= start:
            raise ContractError("clock intervals are half-open and end after start")
        if self.level < 1:
            raise ContractError("clock hierarchy level must be positive")
        if self.level > 1 and not self.parent_interval_id:
            raise ContractError("non-root clock intervals require a parent identity")
        if not math.isfinite(self.uncertainty_seconds) or self.uncertainty_seconds < 0:
            raise ContractError("clock uncertainty must be finite and non-negative")


@dataclass(frozen=True)
class SensitivityResult:
    context_id: str
    fact_id: str
    perturbation_id: str
    baseline_input: float
    perturbed_input: float
    boundary_distance: float
    classification: str
    reason: str

    def __post_init__(self) -> None:
        if self.classification not in {"changed", "unchanged", "unsupported"}:
            raise ContractError("sensitivity classification must be changed, unchanged or unsupported")


def assert_join_compatible(left: CalculationContext, right: CalculationContext) -> None:
    mismatches: list[str] = []
    if left.subject_id != right.subject_id:
        mismatches.append("subject_id")
    if left.chart_id != right.chart_id:
        mismatches.append("chart_id")
    if left.context_id != right.context_id:
        mismatches.append("context_id")
    if left.build_id != right.build_id:
        mismatches.append("build_id")
    if left.generation_id != right.generation_id:
        mismatches.append("generation_id")
    if mismatches:
        raise ContractError("incompatible L1 join: " + ", ".join(mismatches))


def deduplicate_fact_ids(fact_ids: Iterable[str]) -> tuple[str, ...]:
    """Preserve first-seen order while removing shared-root aliases."""
    return tuple(dict.fromkeys(fact_ids))


def stabilize_hierarchical_uuids(
    rows: Sequence[dict[str, Any]],
    *,
    id_field: str,
    parent_field: str,
    identity_fields: Sequence[str],
    kind: str,
) -> None:
    """Rewrite random hierarchy IDs to build-independent UUID5 identities.

    Rows are mutated in place.  Parent identities are resolved level-by-level;
    a dangling parent or duplicate semantic identity fails instead of silently
    producing an ambiguous clock tree.
    """
    old_to_new: dict[str, str] = {}
    seen: set[str] = set()
    pending = list(rows)
    while pending:
        progressed = False
        next_pending: list[dict[str, Any]] = []
        for row in pending:
            old_id = str(row[id_field])
            old_parent = row.get(parent_field)
            if old_parent is not None and str(old_parent) not in old_to_new:
                next_pending.append(row)
                continue
            stable_parent = old_to_new.get(str(old_parent)) if old_parent is not None else None
            values = [row.get(field_name) for field_name in identity_fields]
            new_id = stable_uuid(kind, stable_parent, *values)
            if new_id in seen:
                raise ContractError(f"duplicate semantic {kind} identity: {values!r}")
            old_to_new[old_id] = new_id
            seen.add(new_id)
            row[id_field] = new_id
            row[parent_field] = stable_parent
            progressed = True
        if not progressed:
            dangling = [row.get(parent_field) for row in next_pending]
            raise ContractError(f"unresolved {kind} parent identities: {dangling!r}")
        pending = next_pending
