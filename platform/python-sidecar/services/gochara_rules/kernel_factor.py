"""activity_kernel v1.1.0 evaluator (draft AM-13, RULED steward M20261002T001617-8321).

A pure function of the record's object kind and operands. The factor row
(`registry.FACTORS[("activity_kernel", "1.1.0")]`) is the single source of the
applicability declaration and the orb; nothing is copied here (CLAUDE.md §N.7 item 3).

  span objects (sign_span, house_span)  -> membership step: 1.0 inside, 0.0 outside.
  point/star objects (degree_point, star, derived_point, saham, house_lord)
                                        -> angular `1 − |Δλ|/orb`, but ONLY once the
     orb is a recorded decision: the row carries orb_deg=None (ND-ORB is open) and
     the supplied orb is NOT accepted as a substitute — the unratified 5.0° is not
     carried forward. Until then the result is `unqualified`, reason orb_not_ratified.
  any other object kind (varga_position, unknown) -> `unqualified`, never 1.

Output is the factor result the score algebra consumes: {"value", "null_state"}
(+ "reason"); value ∈ [0,1] or None. A span has no |Δλ| to be "missing", so a span
record is NOT unqualified — that is the defect AM-13 repairs.
"""
from __future__ import annotations

import math

from .registry import FACTORS, KERNEL_VERSION, composite_ref

FACTOR_REF = composite_ref("activity_kernel", KERNEL_VERSION)


def _row() -> dict:
    return FACTORS[FACTOR_REF]


def _result(value, reason, branch):
    return {"value": value, "null_state": _row()["null_state"], "reason": reason,
            "factor": FACTOR_REF, "branch": branch}


def activity_kernel(object_kind: str, *, inside: bool | None = None,
                    delta_lambda_deg: float | None = None) -> dict:
    ap = _row()["applicability"]
    if object_kind in ap["span"]["object_kinds"]:
        if not isinstance(inside, bool):
            return _result(None, "span_membership_operand_missing", "span")
        step = ap["span"]
        return _result(step["inside"] if inside else step["outside"], None, "span")
    if object_kind in ap["angular"]["object_kinds"]:
        orb = ap["angular"]["orb_deg"]          # the ROW's orb — never a caller-supplied number
        if orb is None:
            return _result(None, "orb_not_ratified", "angular")
        if (isinstance(delta_lambda_deg, bool) or not isinstance(delta_lambda_deg, (int, float))
                or not math.isfinite(delta_lambda_deg)):
            return _result(None, "delta_lambda_operand_missing", "angular")
        return _result(max(0.0, 1.0 - abs(float(delta_lambda_deg)) / orb), None, "angular")
    return _result(None, "object_kind_not_covered_by_applicability", None)
