"""activity_kernel v1.1.0 evaluator (draft AM-13, RULED; Codex round 6 R4/R5).

A pure function of the record's object kind, its physical object's canonical target and the transiting
body's longitude. The factor row addressed by `factor_ref` (the soft-factor membership the path actually
carries — NOT a global version) is the single source of the applicability declaration and the orb
(CLAUDE.md §N.7 item 3):

  1. the factor row must be an `activity_kernel` row; a row with no `applicability` (the 1.0.0 row) ⇒
     `unqualified (applicability_undeclared)` for every record — exactly what is stored today;
  2. the record's physical object is VALIDATED before any evaluation: `span:1`–`span:12` (sign_span,
     house_span) and `star:1`–`star:27` (star) are extents; `point:<longitude 0 ≤ λ < 360>` is required by the
     declared point kinds. A kind/target mismatch raises `TargetKindMismatch` — a mislabelled point can no longer
     take the membership step and bypass the unratified-orb branch. `varga_position` ⇒ unqualified;
  3. extent targets: MEMBERSHIP is computed from the validated geometry — the body's longitude (carried along
     the DIRECTED ASPECT RAY when `aspect_angle_deg` is given) inside the sign / nakṣatra — never a caller flag;
     inside ⇒ the row's `inside` value, outside ⇒ its `outside` value (0 is a computed value, not an exclusion);
  4. point targets: qualified only with a RATIFIED orb on the row — finite, strictly positive, with a decision
     reference; the row's orb is the only orb (the evaluator takes none). Unratified (`orb_deg` absent) ⇒
     `unqualified (orb_not_ratified)`; a configured-but-invalid orb (0, negative, NaN, ±Infinity, status
     not ratified, no decision ref) raises `KernelFactorConfigError` — a configuration defect fails closed,
     it never scores. Distance is seam-safe angular distance, measured along the aspect ray if any.
"""
from __future__ import annotations

import math
import re

from .registry import FACTORS

NAKSHATRA_ARC = 360.0 / 27.0


class TargetKindMismatch(ValueError):
    """The object kind and the physical object's canonical target disagree (1155 does not check this)."""


class KernelFactorConfigError(ValueError):
    """The factor row's declaration is invalid for evaluation — fail closed."""


_SPAN = re.compile(r"^span:([0-9]{1,2})$")
_STAR = re.compile(r"^star:([0-9]{1,2})$")
_POINT = re.compile(r"^point:([0-9]+(?:\.[0-9]+)?)$")


def parse_target(object_kind: str, canonical_target: str, ap: dict) -> tuple[str, float | int] | None:
    """Validate `canonical_target` against `object_kind`; returns ("span", 1..12) | ("star", 1..27) |
    ("point", λ) — or None for a kind the declaration does not classify. Raises TargetKindMismatch."""
    if object_kind in ap["span"]["object_kinds"]:
        if object_kind == "star":
            m = _STAR.match(canonical_target or "")
            if not m or not 1 <= int(m.group(1)) <= 27:
                raise TargetKindMismatch(f"star requires star:1..27, got {canonical_target!r}")
            return ("star", int(m.group(1)))
        m = _SPAN.match(canonical_target or "")
        if not m or not 1 <= int(m.group(1)) <= 12:
            raise TargetKindMismatch(f"{object_kind} requires span:1..12, got {canonical_target!r}")
        return ("span", int(m.group(1)))
    if object_kind in ap["angular"]["object_kinds"]:
        m = _POINT.match(canonical_target or "")
        lam = float(m.group(1)) if m else None
        if lam is None or not (0.0 <= lam < 360.0):
            raise TargetKindMismatch(f"{object_kind} requires point:<0 ≤ λ < 360>, got {canonical_target!r}")
        return ("point", lam)
    return None


def _result(ref, value, reason, branch):
    row = FACTORS[ref]
    return {"value": value, "null_state": row["null_state"], "reason": reason, "factor": ref, "branch": branch}


def _finite_lon(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and 0.0 <= x < 360.0


def activity_kernel(object_kind: str, canonical_target: str, *, factor_ref: tuple[str, str],
                    body_longitude_deg: float | None = None, aspect_angle_deg: float | None = None) -> dict:
    row = FACTORS.get(factor_ref)
    if row is None or row["factor_id"] != "activity_kernel":
        raise ValueError(f"{factor_ref!r} is not an activity_kernel factor row")
    ap = row.get("applicability")
    if ap is None:
        return _result(factor_ref, None, "applicability_undeclared", None)
    parsed = parse_target(object_kind, canonical_target, ap)
    if parsed is None:
        return _result(factor_ref, None, "object_kind_not_covered_by_applicability", None)
    if not _finite_lon(body_longitude_deg):
        return _result(factor_ref, None, "body_longitude_missing_or_invalid", parsed[0])
    eff = float(body_longitude_deg)
    if aspect_angle_deg is not None:                              # the directed aspect ray
        if isinstance(aspect_angle_deg, bool) or not isinstance(aspect_angle_deg, (int, float)) or not math.isfinite(aspect_angle_deg):
            return _result(factor_ref, None, "aspect_angle_invalid", parsed[0])
        eff = (eff + float(aspect_angle_deg)) % 360.0
    kind, target = parsed
    if kind in ("span", "star"):
        arc = 30.0 if kind == "span" else NAKSHATRA_ARC
        inside = int(eff // arc) + 1 == target
        step = ap["span"]
        return _result(factor_ref, step["inside"] if inside else step["outside"], None, kind)
    # point
    ang = ap["angular"]
    orb = ang["orb_deg"]
    if orb is None:
        if ang["orb_status"] != "unratified_nd_orb_open":
            raise KernelFactorConfigError(f"orb absent but orb_status is {ang['orb_status']!r}")
        return _result(factor_ref, None, "orb_not_ratified", "point")
    if ang["orb_status"] != "ratified" or not ang.get("orb_decision_ref"):
        raise KernelFactorConfigError("an orb is present without a ratified status and a decision reference")
    if isinstance(orb, bool) or not isinstance(orb, (int, float)) or not math.isfinite(orb) or orb <= 0.0:
        raise KernelFactorConfigError(f"orb must be finite and strictly positive, got {orb!r}")
    d = abs((eff - target + 180.0) % 360.0 - 180.0)               # seam-safe
    return _result(factor_ref, max(0.0, 1.0 - d / float(orb)), None, "point")
