"""Flat, lossless encoding of a factor's applicability declaration into the EXISTING typed field
`ka_gochara_factor.operand_selector` (Codex round 6 R5; migration 1154:221–240, no DDL).

1154's `ka_gochara_named_operands_ok(j)` admits ONLY a non-empty FLAT object whose keys match
`^[a-z][a-z0-9_]*$` and whose values are (a) a selector token string
`^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$`, (b) a JSON number, or (c) a non-empty array of such tokens.
No nested objects, no booleans, no JSON null. So the nested in-memory declaration is encoded here,
an unavailable numeric orb is OMITTED (never null), and `decode` reads it back so the binder can
compare what it persisted with what it meant (read-back equality).

`is_flat_selector` mirrors the SQL; a test extracts the two regexes from the migration text itself so
drift between this module and 1154 fails CI.
"""
from __future__ import annotations

import math
import re

TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$")
KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def flat_problems(obj) -> list[str]:
    """Empty list ⇔ `ka_gochara_named_operands_ok(obj)` would be true."""
    if not isinstance(obj, dict) or not obj:
        return ["not a non-empty object"]
    out = []
    for k, v in obj.items():
        if not isinstance(k, str) or not KEY_RE.match(k):
            out.append(f"key {k!r} violates ^[a-z][a-z0-9_]*$")
        if isinstance(v, bool) or v is None:
            out.append(f"{k}: booleans and null are not admitted")
        elif isinstance(v, str):
            if not TOKEN_RE.match(v):
                out.append(f"{k}: {v!r} is not a selector token")
        elif isinstance(v, (int, float)):
            if isinstance(v, float) and not math.isfinite(v):
                out.append(f"{k}: non-finite number")
        elif isinstance(v, (list, tuple)):
            if not v or not all(isinstance(x, str) and TOKEN_RE.match(x) for x in v):
                out.append(f"{k}: array must be non-empty tokens")
        else:
            out.append(f"{k}: nested/unsupported value ({type(v).__name__})")
    return out


# ── activity_kernel applicability ─────────────────────────────────────────────
ORB_UNRATIFIED = "unratified_nd_orb_open"
ORB_RATIFIED = "ratified"


def encode_kernel(nested: dict) -> dict:
    """nested = {"span": {object_kinds, inside, outside}, "angular": {object_kinds, orb_deg|None, orb_status,
    orb_decision_ref?}, "aspect_geometry": str}  →  flat selector."""
    sp, an = nested["span"], nested["angular"]
    flat = {
        "operand": "geometry:object_kind_dispatch",
        "span_kinds": list(sp["object_kinds"]), "span_form": "membership_step",
        "span_inside": sp["inside"], "span_outside": sp["outside"],
        "point_kinds": list(an["object_kinds"]), "point_form": "one_minus_abs_delta_lambda_over_orb",
        "orb_state": an["orb_status"],
        "aspect_geometry": nested["aspect_geometry"],
        "uncovered_state": "unqualified",
    }
    if an["orb_deg"] is not None:                      # ratified ⇒ both present; unratified ⇒ OMITTED, never null
        flat["orb_deg"] = an["orb_deg"]
        if an.get("orb_decision_ref") is not None:
            flat["orb_decision_ref"] = an["orb_decision_ref"]
    problems = kernel_flat_problems(flat)              # a number without ratified status + decision ref never encodes
    if problems:
        raise ValueError("activity_kernel selector refused: " + "; ".join(problems))
    return flat


KERNEL_FLAT_KEYS = ("operand", "span_kinds", "span_form", "span_inside", "span_outside", "point_kinds", "point_form",
                    "orb_state", "aspect_geometry", "uncovered_state")            # + orb_deg and orb_decision_ref ONLY when ratified


def kernel_flat_problems(flat: dict) -> list[str]:
    """The orb-ratification invariant of a flat activity_kernel selector (steward M20261002T020529-6f18 (b); Codex R5):
    a numeric orb is admissible ONLY together with `orb_state = ratified` and an `orb_decision_ref` token, and an unratified
    row carries neither. Presence of a number never implies ratification."""
    out = flat_problems(flat)
    if out:
        return out
    missing = [k for k in KERNEL_FLAT_KEYS if k not in flat]
    if missing:
        out.append(f"missing keys {missing}")
    extra = sorted(set(flat) - set(KERNEL_FLAT_KEYS) - {"orb_deg", "orb_decision_ref"})
    if extra:
        out.append(f"unknown keys {extra}")
    state = flat.get("orb_state")
    if state == ORB_UNRATIFIED:
        for k in ("orb_deg", "orb_decision_ref"):
            if k in flat:
                out.append(f"{k} present while orb_state is {ORB_UNRATIFIED}")
    elif state == ORB_RATIFIED:
        orb = flat.get("orb_deg")
        if isinstance(orb, bool) or not isinstance(orb, (int, float)) or not math.isfinite(orb) or orb <= 0:
            out.append("ratified requires a finite, strictly positive orb_deg")
        if not isinstance(flat.get("orb_decision_ref"), str):
            out.append("ratified requires an orb_decision_ref token")
    else:
        out.append(f"orb_state {state!r} is neither {ORB_UNRATIFIED} nor {ORB_RATIFIED}")
    return out


def decode_kernel(flat: dict) -> dict:
    problems = kernel_flat_problems(flat)
    if problems:
        raise ValueError("activity_kernel selector refused: " + "; ".join(problems))
    nested = {
        "span": {"object_kinds": list(flat["span_kinds"]), "function": "step",
                 "inside": float(flat["span_inside"]), "outside": float(flat["span_outside"])},
        "angular": {"object_kinds": list(flat["point_kinds"]), "function": "linear",
                    "orb_deg": flat.get("orb_deg"), "orb_status": flat["orb_state"]},
        "aspect_geometry": flat["aspect_geometry"],
    }
    if "orb_decision_ref" in flat:
        nested["angular"]["orb_decision_ref"] = flat["orb_decision_ref"]
    if nested["angular"]["orb_deg"] is not None:
        nested["angular"]["orb_deg"] = float(nested["angular"]["orb_deg"])
    return nested


# ── graduated_drishti applicability ───────────────────────────────────────────
def encode_drishti(nested: dict) -> dict:
    return {"operand": "geometry:aspect_house_offset", "applicable_relations": list(nested["relations"]),
            "not_applicable_state": "declared_omit", "node_cast_aspects": "none"}


def decode_drishti(flat: dict) -> dict:
    return {"relations": list(flat["applicable_relations"])}


# ── vedha_attenuation applicability (AM-18) ────────────────────────────────────
def encode_vedha(nested: dict) -> dict:
    return {"operand": "state:vedha_interval_derived_from_residence",
            "applicable_records": "favourable_residence_cited_pairs_only",
            "map_active": nested["mapping"]["active"], "map_inactive": nested["mapping"]["inactive"],
            "active_qualification": nested["qualification_on_active"],
            "unqualified_reasons": list(nested["unqualified_reasons"]),
            "inactive_scope": nested["scope_on_inactive"],
            "scope_exempt_primaries": [g.lower() for g in nested["scope_not_needed_for"]],
            "vipareeta_state": "not_produced_no_served_citation"}


def decode_vedha(flat: dict) -> dict:
    return {"mapping": {"active": float(flat["map_active"]), "inactive": float(flat["map_inactive"])},
            "qualification_on_active": flat["active_qualification"],
            "unqualified_reasons": list(flat["unqualified_reasons"]),
            "scope_on_inactive": flat["inactive_scope"],
            "scope_not_needed_for": [g.capitalize() for g in flat["scope_exempt_primaries"]]}
