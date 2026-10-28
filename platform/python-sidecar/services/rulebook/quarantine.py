"""Rule Book engine (packet E1) — typed quarantine reasons and the census.

A QUARANTINED_NOT_EVALUABLE card is stored, never counted (ENGINE_PLAN v0.2
§2.1). Each reason names what the panel must amend through the change
register; a card is withdrawn only if its verse itself gives no comparator.
"""

from __future__ import annotations

import enum
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional


class Reason(str, enum.Enum):
    # structure
    SCHEMA_INVALID = "SCHEMA_INVALID"
    DANGLING_OPERAND_REF = "DANGLING_OPERAND_REF"
    OPERAND_SOURCE_UNMAPPED = "OPERAND_SOURCE_UNMAPPED"
    ROLE_RELATION_MISMATCH = "ROLE_RELATION_MISMATCH"
    UNBOUND_OPERAND = "UNBOUND_OPERAND"
    TARGET_UNBOUND = "TARGET_UNBOUND"
    OR_NOT_VERSE_STATED = "OR_NOT_VERSE_STATED"
    TAUTOLOGICAL_DISJUNCTION = "TAUTOLOGICAL_DISJUNCTION"
    # comparators / aṣṭakavarga
    MISSING_COMPARATOR = "MISSING_COMPARATOR"
    AMBIGUOUS_COMPARATOR_BINDING = "AMBIGUOUS_COMPARATOR_BINDING"
    BINDU_TARGET_UNLINKED = "BINDU_TARGET_UNLINKED"
    BINDU_CONVENTION_UNDECLARED = "BINDU_CONVENTION_UNDECLARED"
    # frames / planes
    FRAME_MISSING = "FRAME_MISSING"
    FRAME_UNSUPPORTED_V1 = "FRAME_UNSUPPORTED_V1"
    FRAME_ROLE_UNBOUND = "FRAME_ROLE_UNBOUND"
    FRAME_PLANE_CONTRADICTION = "FRAME_PLANE_CONTRADICTION"
    PLANE_ROLE_CONTRADICTION = "PLANE_ROLE_CONTRADICTION"
    # operand variants the sources cannot honour
    MEAN_OPERAND = "MEAN_OPERAND"
    NODE_MODEL_MISMATCH = "NODE_MODEL_MISMATCH"
    NON_UNIQUE_LOOKUP = "NON_UNIQUE_LOOKUP"
    # doctrine defects routed by the cockpit
    GRAHA_CLASS_CONDITION_MISSING = "GRAHA_CLASS_CONDITION_MISSING"  # DF-01
    GRAHA_CLASS_SENSE_UNPINNED = "GRAHA_CLASS_SENSE_UNPINNED"
    BHAVA_GROUP_DF02_OPEN = "BHAVA_GROUP_DF02_OPEN"  # DF-02
    # vedha
    VEDHA_EXEMPTION_NOT_ENCODABLE = "VEDHA_EXEMPTION_NOT_ENCODABLE"
    UNDECLARED_OBSTRUCTOR_SET = "UNDECLARED_OBSTRUCTOR_SET"
    # exceptions
    SCHOOL_SCOPE_TEXTS_UNDECLARED = "SCHOOL_SCOPE_TEXTS_UNDECLARED"
    # build-failing semantics
    P4_DOUBLE_TRANSIT = "P4_DOUBLE_TRANSIT"
    # schema v1.2 (validated only; CR-006)
    V12_FIELD_NOT_EVALUATED = "V12_FIELD_NOT_EVALUATED"


REASON_HELP: Mapping[Reason, str] = {
    Reason.SCHEMA_INVALID: "card does not match Rule Card v1.1 in a field the compiler reads",
    Reason.DANGLING_OPERAND_REF: "gate/exception/frame_role/target_role names an operand id the card does not declare",
    Reason.OPERAND_SOURCE_UNMAPPED: "role x relation has no source in the E0 operand matrix",
    Reason.ROLE_RELATION_MISMATCH: "relation is not admissible for the role (e.g. bhava + bindus)",
    Reason.UNBOUND_OPERAND: "role needs one graha but the card binds none (no doctrinal_graha)",
    Reason.TARGET_UNBOUND: "positional predicate has no bhava, group or linked sign to test",
    Reason.OR_NOT_VERSE_STATED: "OR used but the cited quote states no disjunction (or / vā / athavā)",
    Reason.TAUTOLOGICAL_DISJUNCTION: "OR branches jointly cover every graha, so the OR constrains nothing",
    Reason.MISSING_COMPARATOR: "bindus operand without a field-7 bindus_of_8 comparator; no threshold is supplied",
    Reason.AMBIGUOUS_COMPARATOR_BINDING: "several bindus operands or comparators; binding is not unique",
    Reason.BINDU_TARGET_UNLINKED: "bindus operand has no target_role naming the transit whose sign it reads",
    Reason.BINDU_CONVENTION_UNDECLARED: "rekha/bindu count term not declared for this text in the convention map",
    Reason.FRAME_MISSING: "no frame; the compiler never defaults one",
    Reason.FRAME_UNSUPPORTED_V1: "frame is deferred in v1 (surya_lagna, navamsa_lagna, antardasha_lord_natal_position)",
    Reason.FRAME_ROLE_UNBOUND: "*_of_role frame without a frame_role naming a declared operand",
    Reason.FRAME_PLANE_CONTRADICTION: "frame contradicts the card's plane (e.g. dasha card on sign_of_transit_only)",
    Reason.PLANE_ROLE_CONTRADICTION: "no operand of the card's plane, or a natal card with time-varying operands",
    Reason.MEAN_OPERAND: "operand names a madhya/mean position; v1 has no mean-motion source",
    Reason.NODE_MODEL_MISMATCH: "verse states a node model other than the source's (L1 natal mean, L0 transit true)",
    Reason.NON_UNIQUE_LOOKUP: "E0 found the fact lookup non-unique (e.g. karaka 7/8 school)",
    Reason.GRAHA_CLASS_CONDITION_MISSING: "Moon/Mercury class needs a verse condition v1.1 cannot state (DF-01)",
    Reason.GRAHA_CLASS_SENSE_UNPINNED: "benefic/malefic without natural_: natural vs functional not pinned",
    Reason.BHAVA_GROUP_DF02_OPEN: "panaphara/apoklima while cockpit DF-02 (incomplete L0 groups) is open",
    Reason.VEDHA_EXEMPTION_NOT_ENCODABLE: "cited verse exempts an obstructor; v1.1 has no field to encode it",
    Reason.UNDECLARED_OBSTRUCTOR_SET: "vedha obstructor set is a class or unbound; the set cannot be formed",
    Reason.SCHOOL_SCOPE_TEXTS_UNDECLARED: "exception scope has no explicit text list yet (Q10)",
    Reason.V12_FIELD_NOT_EVALUATED: "card uses a v1.2 field; it validates but the evaluator does not read v1.2 yet",
    Reason.P4_DOUBLE_TRANSIT: "requires Jupiter and Saturn in transit on a shared target (D4: P4 is not evaluated)",
}


@dataclass(frozen=True)
class Finding:
    reason: Reason
    operand_id: Optional[str]
    detail: str

    def to_json(self) -> dict:
        return {"reason": self.reason.value, "operand_id": self.operand_id, "detail": self.detail}


def census(results: Iterable[Mapping[str, Any]], *, expected: Optional[Mapping[str, str]] = None) -> dict:
    """Summarise compile results for a consolidated card set.

    ``results`` items: {"consolidated_id", "members": [CompileResult.to_json(), ...]}.
    A consolidated card is active only when every member compiles active.
    ``expected`` optionally maps consolidated_id -> "evaluable" | "quarantine"
    (E0's census) for reconciliation.
    """
    rows = []
    reason_counter: Counter = Counter()
    for item in results:
        members = item["members"]
        statuses = {m["status"] for m in members}
        status = "active" if statuses == {"active"} else "quarantined_not_evaluable"
        reasons = sorted({f["reason"] for m in members for f in m["findings"]})
        for r in reasons:
            reason_counter[r] += 1
        logic = sorted({m.get("logic_sha256") for m in members if m.get("logic_sha256")})
        row = {
            "consolidated_id": item["consolidated_id"],
            "category": item.get("category"),
            "status": status,
            "reasons": reasons,
            "members": [
                {
                    "card_id": m["card_id"],
                    "status": m["status"],
                    "ir_sha256": m.get("ir_sha256"),
                    "logic_sha256": m.get("logic_sha256"),
                    "convention_pending": m.get("convention_pending", []),
                }
                for m in members
            ],
            "members_logic_agree": len(logic) <= 1,
        }
        if expected is not None:
            exp = expected.get(item["consolidated_id"])
            got = "evaluable" if status == "active" else "quarantine"
            row["e0_expected"] = exp
            row["reconciles_with_e0"] = exp == got
        rows.append(row)
    active = sum(1 for r in rows if r["status"] == "active")
    out = {
        "cards": len(rows),
        "active": active,
        "quarantined_not_evaluable": len(rows) - active,
        "reason_card_counts": dict(sorted(reason_counter.items())),
        "rows": rows,
    }
    if expected is not None:
        out["e0_reconciliation"] = {
            "e0_evaluable": sum(1 for v in expected.values() if v == "evaluable"),
            "e0_quarantine": sum(1 for v in expected.values() if v == "quarantine"),
            "mismatches": [r["consolidated_id"] for r in rows if not r.get("reconciles_with_e0")],
        }
    return out
