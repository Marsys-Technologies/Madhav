"""sad_bala_sufficient v1.0 evaluator (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-6
Option C; Phaladīpikā IV.22-23, corpus locator phaladeepika:PG79:C1).

A pure function over ONE L1 operand: the graha's total ṣaḍbala in rūpas
(`graha_shadbala_total` / `rupa`). It never recomputes strength and never reads
the database. The thresholds are read from the registry's factor row — there is
no second copy in this module (CLAUDE.md §N.7 item 3).

Output = the factor result the score algebra consumes
(`{"value", "null_state"}` — `score.factor_product`) PLUS the raw rūpa magnitude
as typed OPERAND EVIDENCE, kept in a separate field and never part of the
score:

  value  1.0   total >= threshold (equality IS sufficient)
         0.0   total <  threshold
         None  the operand cannot be classified: node (no cited threshold),
               missing, non-finite, negative, boolean/non-numeric, or a unit
               other than 'rupa' → the FACTOR is unqualified (`null_state`
               from the factor row). A missing/unsupported operand is NEVER an
               invented 0 or 1, and it NEVER touches admission (1155:822-832 —
               admission derives from the path's necessary predicates only; the
               soft factor orders admitted windows, it does not admit or revoke).
"""
from __future__ import annotations

import math
from decimal import Decimal

from .registry import FACTORS, RULE_VERSION, composite_ref

FACTOR_REF = composite_ref("sad_bala_sufficient", RULE_VERSION)

# L1 subject code → registry graha name (inverse of the factor row's
# operand_evidence.l1_subjects, so the mapping has ONE source).
_GRAHA_NAMES = frozenset({"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                          "Saturn", "Rahu", "Ketu"})


def _factor_row() -> dict:
    return FACTORS[FACTOR_REF]


def graha_name(subject: str) -> str | None:
    """Accepts a registry name ('Sun') or an L1 fact_subject ('SUN', 'RAH_MEAN')."""
    if subject in _GRAHA_NAMES:
        return subject
    for name, code in _factor_row()["operand_evidence"]["l1_subjects"].items():
        if subject == code:
            return name
    return None


def _evidence(operand: dict | None, graha: str | None) -> dict:
    """Typed operand evidence: value, unit and the L1 row's own provenance,
    carried verbatim. `scored` is always False — raw rūpas are never a score."""
    op = operand or {}
    spec = _factor_row()["operand_evidence"]
    ev = {
        "scored": False,
        "kind": "typed_operand_evidence",
        "graha": graha,
        "fact_category": spec["fact_category"],
        "fact_key": spec["fact_key"],
        "unit": op.get("unit"),
        "value": op.get("value"),
    }
    for field in ("fact_id", "fact_subject", "build_id", "ayanamsha_id",
                  "verification_pass_status"):
        ev[field] = op.get(field)
    return ev


def _unqualified(reason: str, operand: dict | None, graha: str | None) -> dict:
    row = _factor_row()
    return {"value": None, "null_state": row["null_state"], "reason": reason,
            "factor": FACTOR_REF, "evidence": _evidence(operand, graha)}


def sad_bala_sufficient(operand: dict | None) -> dict:
    """Classify one ṣaḍbala operand.

    operand = {"fact_subject": 'SUN'|…|'Sun'|…, "value": rūpas, "unit": 'rupa',
               "fact_id", "build_id", "ayanamsha_id", "verification_pass_status"}
    — a plain read of one L1 `graha_shadbala_total/rupa` row; fields other than
    subject/value/unit are provenance and are copied through unchanged.
    """
    if not isinstance(operand, dict):
        return _unqualified("operand_missing", None, None)
    subject = operand.get("fact_subject", operand.get("graha"))
    graha = graha_name(subject) if isinstance(subject, str) else None
    if graha is None:
        return _unqualified("graha_unrecognised", operand, None)
    row = _factor_row()
    if graha in row["unsupported_agents"]:
        return _unqualified("no_cited_threshold_for_node", operand, graha)
    if operand.get("unit") != row["operand_evidence"]["unit"]:
        return _unqualified("incompatible_unit", operand, graha)
    value = operand.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return _unqualified("operand_missing_or_not_numeric", operand, graha)
    if not math.isfinite(float(value)) or value < 0:
        return _unqualified("operand_not_a_finite_non_negative_total", operand, graha)
    threshold = row["thresholds_rupa"][graha]
    sufficient = Decimal(str(value)) >= Decimal(str(threshold))   # exact: equality IS sufficient
    return {"value": 1.0 if sufficient else 0.0, "null_state": row["null_state"],
            "threshold_rupa": threshold, "reason": None, "factor": FACTOR_REF,
            "evidence": _evidence(operand, graha)}
