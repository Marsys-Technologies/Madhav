"""Rule Card schema validation (v1, v1.1, v1.2) — no third-party dependency.

``RULE_CARD_SCHEMA_v1_2.json`` (data/) is the machine-readable schema. This
module executes it with a small JSON Schema 2020-12 subset interpreter (the
keywords the schema uses, nothing else; an unknown keyword is an error, so the
schema cannot silently grow past what is checked), then applies the
cross-field rules JSON Schema cannot state (proposal v0.2 §3).

Validation only: nothing here evaluates a v1.2 field (the compiler quarantines
any card that uses one with V12_FIELD_NOT_EVALUATED until the panel ratifies
v1.2 and the evaluator is built).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from . import constants as C

SCHEMA_FILE = "RULE_CARD_SCHEMA_v1_2.json"
V12 = "rule-card-v1.2"
GRAHA_BEARING_ROLES = frozenset(
    {"transiting_graha", "natal_graha", "dasha_lord", "antardasha_lord", "bhava_lord", "karaka"}
)
DIGNITY_RELATIONS = frozenset({"exalted", "debilitated", "own_sign", "moolatrikona"})
_EXEMPTION_WORDS = re.compile(C.VEDHA_EXEMPTION_RE, re.IGNORECASE)

_SUPPORTED = {
    "$schema",
    "$id",
    "$ref",
    "$defs",
    "title",
    "description",
    "type",
    "enum",
    "const",
    "pattern",
    "minLength",
    "maxLength",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "minItems",
    "maxItems",
    "uniqueItems",
    "minimum",
    "maximum",
    "oneOf",
    "anyOf",
    "allOf",
    "not",
    "if",
    "then",
    "else",
    "contains",
}


@lru_cache(maxsize=None)
def load_schema() -> Mapping[str, Any]:
    with (C.DATA_DIR / SCHEMA_FILE).open(encoding="utf-8") as fh:
        return json.load(fh)


# ── JSON Schema subset interpreter ─────────────────────────────────────────
def _type_ok(value: Any, t: str) -> bool:
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    raise ValueError(f"unsupported type {t!r}")


def _eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    return a == b


def _errors(value: Any, sch: Any, root: Mapping[str, Any], path: str) -> List[str]:
    if sch is True or sch == {}:
        return []
    if sch is False:
        return [f"{path}: not allowed"]
    unknown = set(sch) - _SUPPORTED
    if unknown:
        raise ValueError(f"schema keyword(s) not supported by the interpreter: {sorted(unknown)}")
    errs: List[str] = []
    if "$ref" in sch:
        ref = sch["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"only local $defs refs are supported: {ref}")
        errs += _errors(value, root["$defs"][ref.split("/")[-1]], root, path)
    if "type" in sch and not _type_ok(value, sch["type"]):
        return errs + [f"{path}: expected {sch['type']}"]
    if "enum" in sch and not any(_eq(value, e) for e in sch["enum"]):
        errs.append(f"{path}: {value!r} not in enum")
    if "const" in sch and not _eq(value, sch["const"]):
        errs.append(f"{path}: must be {sch['const']!r}")
    if isinstance(value, str):
        if "pattern" in sch and not re.search(sch["pattern"], value):
            errs.append(f"{path}: does not match {sch['pattern']}")
        if "minLength" in sch and len(value) < sch["minLength"]:
            errs.append(f"{path}: shorter than {sch['minLength']}")
        if "maxLength" in sch and len(value) > sch["maxLength"]:
            errs.append(f"{path}: longer than {sch['maxLength']}")
    if _type_ok(value, "number"):
        if "minimum" in sch and value < sch["minimum"]:
            errs.append(f"{path}: below {sch['minimum']}")
        if "maximum" in sch and value > sch["maximum"]:
            errs.append(f"{path}: above {sch['maximum']}")
    if isinstance(value, dict):
        for k in sch.get("required", []):
            if k not in value:
                errs.append(f"{path}: missing {k}")
        props = sch.get("properties", {})
        for k, v in value.items():
            if k in props:
                errs += _errors(v, props[k], root, f"{path}.{k}")
            elif sch.get("additionalProperties") is False:
                errs.append(f"{path}: unexpected key {k}")
    if isinstance(value, list):
        if "minItems" in sch and len(value) < sch["minItems"]:
            errs.append(f"{path}: fewer than {sch['minItems']} items")
        if "maxItems" in sch and len(value) > sch["maxItems"]:
            errs.append(f"{path}: more than {sch['maxItems']} items")
        if sch.get("uniqueItems"):
            seen = [json.dumps(v, sort_keys=True) for v in value]
            if len(seen) != len(set(seen)):
                errs.append(f"{path}: items not unique")
        if "items" in sch:
            for i, v in enumerate(value):
                errs += _errors(v, sch["items"], root, f"{path}[{i}]")
        if "contains" in sch and not any(not _errors(v, sch["contains"], root, path) for v in value):
            errs.append(f"{path}: contains no matching item")
    for sub in sch.get("allOf", []):
        errs += _errors(value, sub, root, path)
    if "anyOf" in sch and not any(not _errors(value, s, root, path) for s in sch["anyOf"]):
        errs.append(f"{path}: matches none of anyOf")
    if "oneOf" in sch and sum(1 for s in sch["oneOf"] if not _errors(value, s, root, path)) != 1:
        errs.append(f"{path}: must match exactly one of oneOf")
    if "not" in sch and not _errors(value, sch["not"], root, path):
        errs.append(f"{path}: matches a forbidden form")
    if "if" in sch:
        branch = sch.get("then") if not _errors(value, sch["if"], root, path) else sch.get("else")
        if branch is not None:
            errs += _errors(value, branch, root, path)
    return errs


def schema_errors(card: Any, root: Optional[Mapping[str, Any]] = None) -> List[str]:
    """Errors of one card against RULE_CARD_SCHEMA_v1_2.json (which admits v1 and v1.1 cards unchanged).

    ``root`` may name another Rule Card schema document (e.g. v1.1, for parity tests)."""
    root = root if root is not None else load_schema()
    return _errors(card, root["$defs"]["card"], root, "card")


# ── cross-field rules (proposal v0.2 §3) ───────────────────────────────────
def _operands(card: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    ops = list(card.get("field5_typed_operands") or [])
    for exc in card.get("field6_exceptions") or []:
        ops += list(exc.get("operands") or [])
    return ops


def _walk_terms(obj: Any) -> Iterable[Any]:
    """Every quote-term item on the card: operand quote_terms and every v1.2 *terms / clause_span list."""
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if (k.endswith("_terms") or k == "clause_span") and isinstance(v, list):
                yield from v
            else:
                yield from _walk_terms(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_terms(v)


def _cited_ids(card: Mapping[str, Any]) -> Set[str]:
    ids = set((card.get("field1_citation") or {}).get("passage_ids") or [])
    ids |= set(((card.get("field3_reference_frame") or {}).get("frame_citation") or {}).get("passage_ids") or [])
    for exc in card.get("field6_exceptions") or []:
        ids |= set((exc.get("citation") or {}).get("passage_ids") or [])
    return ids


def _witnesses(card: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    out = [t for t in _walk_terms(card) if isinstance(t, Mapping)]
    for cit in _citations(card):
        out += list(cit.get("witnesses") or [])
    return out


def _citations(card: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    cits = [card.get("field1_citation") or {}]
    fc = (card.get("field3_reference_frame") or {}).get("frame_citation")
    if fc:
        cits.append(fc)
    cits += [exc["citation"] for exc in card.get("field6_exceptions") or [] if exc.get("citation")]
    return cits


def semantic_errors(card: Mapping[str, Any]) -> List[str]:
    errs: List[str] = []
    ops = _operands(card)
    by_id: Dict[str, Mapping[str, Any]] = {o.get("id"): o for o in ops}
    frame = (card.get("field3_reference_frame") or {}).get("frame")

    # witnesses: well-formed ranges inside the card's own cited passages
    cited = _cited_ids(card)
    for w in _witnesses(card):
        if w["token_end"] <= w["token_start"]:
            errs.append(f"witness {w['passage_id']}: token_end must exceed token_start")
        if w["passage_id"] not in cited:
            errs.append(f"witness {w['passage_id']}: not a passage this card cites")
    # hash form: no clear text anywhere on the card
    if any(c.get("quote_form") == "sha256" for c in _citations(card)):
        if any(c.get("quote_form") != "sha256" for c in _citations(card)):
            errs.append("quote_form sha256 must apply to every citation on the card")
        if any(isinstance(t, str) for t in _walk_terms(card)):
            errs.append("quote_form sha256: every quote term must be a witness, not clear text")

    for o in ops:
        oid = o.get("id")
        v = o.get("vedha")
        if v:
            prim = o.get("doctrinal_graha")
            grahas = [x["graha"] for x in v["obstructors"]]
            if len(grahas) != len(set(grahas)):
                errs.append(f"{oid}.vedha: a graha is listed twice")
            if prim in grahas:
                errs.append(f"{oid}.vedha: the primary graha cannot obstruct itself")
            exempt = [x for x in v["obstructors"] if x["status"] == "exempt"]
            if v["exemption"]["stated"] and not exempt:
                errs.append(f"{oid}.vedha: exemption.stated true needs an exempt obstructor entry")
            if not v["exemption"]["stated"] and exempt:
                errs.append(f"{oid}.vedha: exemption.stated false contradicts an exempt entry")
            if not v["exemption"]["stated"]:
                clear = " ".join(t for t in v["exemption"]["clause_span"] if isinstance(t, str))
                if _EXEMPTION_WORDS.search(clear):
                    errs.append(f"{oid}.vedha: clause_span carries exemption words but stated is false")
            tb = [p["transit_bhava"] for p in v["vedha_pairs"]]
            if len(tb) != len(set(tb)):
                errs.append(f"{oid}.vedha: a transit_bhava is paired twice")
            if any(p["transit_bhava"] == p["vedha_bhava"] for p in v["vedha_pairs"]):
                errs.append(f"{oid}.vedha: a vedha pair cannot map a house to itself")
            for t in ops:
                if (
                    t is not o
                    and t.get("role") == "transiting_graha"
                    and t.get("doctrinal_graha") == prim
                    and t.get("relation") == "transits"
                ):
                    hs = ([t["bhava"]] if t.get("bhava") else []) + list(t.get("target_bhavas") or [])
                    if hs and not set(hs) <= set(tb):
                        errs.append(f"{oid}.vedha: transit houses {sorted(hs)} of {t.get('id')} have no vedha pair")
        b = o.get("bindu_gate")
        if b:
            tgt = by_id.get(b["reads_sign_of"])
            if tgt is None or tgt is o:
                errs.append(f"{oid}.bindu_gate: reads_sign_of must name another declared operand")
            elif not (tgt.get("role") == "transiting_graha" or tgt.get("bhava") or tgt.get("target_bhavas")):
                errs.append(f"{oid}.bindu_gate: reads_sign_of must name a positional operand")
            owner = b["varga_owner"]
            if owner == "sav" and o.get("role") != "ashtakavarga_sav":
                errs.append(f"{oid}.bindu_gate: varga_owner sav needs role ashtakavarga_sav")
            if owner in C.GRAHAS:
                if o.get("role") != "ashtakavarga_bav":
                    errs.append(f"{oid}.bindu_gate: a graha varga_owner needs role ashtakavarga_bav")
                if o.get("doctrinal_graha") and o["doctrinal_graha"] != owner:
                    errs.append(f"{oid}.bindu_gate: varga_owner differs from doctrinal_graha")
            if owner == "undeclared" and b.get("value", 0) > 8:
                errs.append(f"{oid}.bindu_gate: a value above 8 needs varga_owner sav")
        ts = o.get("target_sign")
        if ts:
            if frame != "sign_intrinsic":
                errs.append(f"{oid}.target_sign: needs frame sign_intrinsic")
            ref = by_id.get(ts["of_role"])
            if ref is None or ref is o:
                errs.append(f"{oid}.target_sign: of_role must name another declared operand")
            elif not (ref.get("doctrinal_graha") or ref.get("role") in GRAHA_BEARING_ROLES):
                errs.append(f"{oid}.target_sign: of_role must resolve to a graha-bearing operand")
            want = {
                "transiting_graha": {"transit"},
                "natal_graha": {"natal"},
                "dasha_lord": {"natal", "dasha_period"},
                "antardasha_lord": {"natal", "dasha_period"},
            }
            if o.get("role") in want and ts["locus"] not in want[o["role"]]:
                errs.append(f"{oid}.target_sign: locus {ts['locus']} contradicts role {o.get('role')}")
    if frame == "sign_intrinsic":
        if not any(o.get("target_sign") for o in ops):
            errs.append("frame sign_intrinsic needs an operand with target_sign")
        if not (card.get("field3_reference_frame") or {}).get("frame_terms"):
            errs.append("frame sign_intrinsic needs frame_terms (checked against the cited passage)")
    if any(o.get("bindu_gate") for o in ops) and any(
        a.get("kind") == "bindus_of_8" for a in card.get("field7_discrete_arithmetic") or []
    ):
        errs.append("bindu_gate and field7 bindus_of_8 are mutually exclusive")
    return errs


def validate_card(card: Any) -> List[str]:
    """All schema and cross-field errors; empty means valid. Never fills a value."""
    if not isinstance(card, Mapping):
        return ["card: expected object"]
    errs = schema_errors(card)
    if errs:
        return errs
    return semantic_errors(card)


def v12_features(card: Mapping[str, Any]) -> List[str]:
    """Names of the v1.2 fields a card uses (the compiler does not evaluate them yet)."""
    feats: Set[str] = set()
    for o in _operands(card):
        for k in ("vedha", "bindu_gate", "target_sign"):
            if k in o:
                feats.add(k)
        if o.get("relation") == "moolatrikona":
            feats.add("relation:moolatrikona")
    if (card.get("field3_reference_frame") or {}).get("frame") == "sign_intrinsic":
        feats.add("frame:sign_intrinsic")
    if any(c.get("quote_form") == "sha256" for c in _citations(card)):
        feats.add("quote_form:sha256")
    if any(isinstance(t, Mapping) for t in _walk_terms(card)):
        feats.add("witness_terms")
    return sorted(feats)


def class_groups(card: Mapping[str, Any]) -> Optional[List[str]]:
    scope = card.get("field2_target_scope") or {}
    if "class_groups" in scope:
        return list(scope["class_groups"])
    if "class_group" in scope:
        return [scope["class_group"]]
    return None
