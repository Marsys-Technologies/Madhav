"""Read-only rule registry and admission boundary for Kāla consumers.

This module deliberately owns no catalogue constants.  Catalogue persistence and
its codec remain in :mod:`services.gochara_kernel.rule_registry`; callers pass
the rows they have read and receive a typed, ordered view suitable for an
evaluator.  In particular, an incomplete Aṣṭakavarga qualification is an
honest non-admission, never a default activity score.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from services.gochara_kernel import rule_registry as _kernel_registry
from services.gochara_kernel.convention import drishti_angles as _canonical_drishti_angles


@dataclass(frozen=True)
class RuleLocator:
    """A source locator carried through a read model without inventing one."""

    source: str
    locator: str


@dataclass(frozen=True)
class RuleFactor:
    factor_id: str
    version: str
    soft: bool
    provenance: str | None
    operator_role: str | None
    source_locators: tuple[RuleLocator, ...]


@dataclass(frozen=True)
class RulePrerequisite:
    predicate_id: str
    version: str
    evaluation_order: int


@dataclass(frozen=True)
class RulePath:
    path_id: str
    version: str
    prerequisites: tuple[RulePrerequisite, ...]
    soft_factors: tuple[RuleFactor, ...]
    provenance: str | None
    operator_role: str | None
    source_locators: tuple[RuleLocator, ...]


@dataclass(frozen=True)
class Admission:
    admitted: bool
    reason: str | None = None
    completeness_state: str = "qualified"


def _locators(value: Any) -> tuple[RuleLocator, ...]:
    if not value:
        return ()
    if isinstance(value, Mapping):
        value = (value,)
    return tuple(
        RuleLocator(str(row["source"]), str(row["locator"]))
        for row in value
    )


def _prerequisite(row: Mapping[str, Any], index: int) -> RulePrerequisite:
    return RulePrerequisite(
        predicate_id=str(row["predicate_id"]),
        version=str(row["rule_version"]),
        evaluation_order=int(row.get("evaluation_order", index)),
    )


def _factor(row: Mapping[str, Any]) -> RuleFactor:
    return RuleFactor(
        factor_id=str(row["factor_id"]),
        version=str(row["rule_version"]),
        soft=bool(row.get("soft", True)),
        provenance=row.get("provenance"),
        operator_role=row.get("operator_role"),
        source_locators=_locators(row.get("source_locators")),
    )


def read_path(row: Mapping[str, Any]) -> RulePath:
    """Return one typed rule path, with prerequisites in declared order.

    The data is intentionally supplied by the caller's registry read.  That
    keeps this package read-only and makes a missing declaration observable.
    """
    prerequisites = tuple(
        sorted(
            (_prerequisite(item, index) for index, item in enumerate(row.get("prerequisites", ()))),
            key=lambda item: item.evaluation_order,
        )
    )
    factors = tuple(_factor(item) for item in row.get("soft_factors", ()))
    return RulePath(
        path_id=str(row["path_id"]),
        version=str(row["rule_version"]),
        prerequisites=prerequisites,
        soft_factors=factors,
        provenance=row.get("provenance"),
        operator_role=row.get("operator_role"),
        source_locators=_locators(row.get("source_locators")),
    )


def read_paths(rows: Iterable[Mapping[str, Any]]) -> tuple[RulePath, ...]:
    """Read paths deterministically by id/version after preserving each order."""
    return tuple(sorted((read_path(row) for row in rows), key=lambda path: (path.path_id, path.version)))


def registry_predicates() -> tuple[Mapping[str, Any], ...]:
    """Expose the kernel's declared predicates as a read-side convenience."""
    return tuple(_kernel_registry.predicate_rows())


def read_ashtakavarga_bindu(
    rows: Iterable[Mapping[str, Any]], *, graha: str, sign: str
) -> int | None:
    """Read the one sign-level BAV operand for an admission decision.

    ``None`` means the L1 fact was not resolvable.  The function does not
    manufacture a value from a SAV total or a legacy table; a caller shares
    this one read among its judge, jury, and forecaster decisions.
    """
    matches = [
        row for row in rows
        if row.get("graha") == graha and row.get("sign") == sign
    ]
    if len(matches) != 1:
        return None
    value = matches[0].get("bindu")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def admit(
    *,
    prerequisites_satisfied: bool,
    av_bindu: int | None = None,
    is_kakshya_crossing: bool = False,
) -> Admission:
    """Apply the shared admission floor.

    N-13: an Aṣṭakavarga-dependent kakṣyā crossing without a resolvable bindu
    is unqualified and contributes no activity.  A resolved zero is qualified;
    it is not confused with a missing fact.
    """
    if not prerequisites_satisfied:
        return Admission(False, "prerequisite_unsatisfied", "qualified")
    if is_kakshya_crossing and av_bindu is None:
        return Admission(False, "av_bindu_missing", "unqualified")
    return Admission(True)


def drishti_angles(body: str) -> tuple[float, ...]:
    """The canonical convention: Rāhu and Ketu cast no dṛṣṭi (N-14)."""
    canonical_body = body[:1].upper() + body[1:].lower()
    return _canonical_drishti_angles(canonical_body)
