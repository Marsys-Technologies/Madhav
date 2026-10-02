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
        flat["orb_decision_ref"] = an["orb_decision_ref"]
    return flat


def decode_kernel(flat: dict) -> dict:
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
