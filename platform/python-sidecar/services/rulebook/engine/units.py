"""Rule Book engine (E1/E3) — the UNIT_MANIFEST and the rule bundle.

Inputs are ATTESTED RULES: for each of the 229 rules, its member cards' compile
outcome as made in the owner's session against the text bank (hash form, see
``brahmagyan.l0_rule_book.attest_text_compile``), plus each card's structural
operand table. No quote and no quote term appears in any input or output here.

Outputs
- the RULE BUNDLE: for every evaluable rule, each member card's attested IR and
  operand table (word-free); the evaluator reads only this.
- the UNIT_MANIFEST (YARDSTICK §0, §2.6): 123 units = the conflict-free rules plus the
  variant-conflict clusters; per unit the members, compile status, plane, polarity,
  area tags and a hash. A unit is evaluable when at least one member is.

Statuses (mutually exclusive, computed here by the same planner the evaluator uses):
  evaluable          every member card attested active; the planner accepts it; no node read
  excluded_node      attested active, but a predicate reads a Rāhu/Ketu position or state (DF-03)
  quarantined_compile  a member card is quarantined by the compiler/lints, or has no attestation
  quarantined_engine   attested active, but the engine does not evaluate it (reason code recorded)
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from ..compiler import _alpha_rename, sha256_hex
from . import constants as K
from .plan import CardPlan, Unsupported, plan_card

ATTESTED_SCHEMA = "rulebook-attested-rules-v1"
EVALUABLE = "evaluable"
EXCLUDED_NODE = "excluded_node"
Q_COMPILE = "quarantined_compile"
Q_ENGINE = "quarantined_engine"

_CODE_RE = re.compile(r"(?:PANEL_RETURN:)?([A-Z][A-Z0-9_]{3,})")


def canonical_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reason_codes(card: Mapping[str, Any]) -> List[str]:
    """Stable reason codes from an attested card record (compiler findings and lint codes)."""
    codes = set()
    ir = card.get("ir") or {}
    for f in ir.get("quarantine") or []:
        codes.add(f["reason"])
    why = card.get("quarantine_reason") or ""
    for seg in why.split(" | "):
        m = _CODE_RE.match(seg.strip())
        if m:
            codes.add(m.group(1))
    if card.get("hash_error"):
        codes.add("HASH_FORM_UNCONVERTIBLE")
    if not codes and card.get("status") != "active":
        codes.add("NOT_ATTESTED_ACTIVE")
    return sorted(codes)


def area_tags(class_groups: Iterable[str]) -> List[str]:
    return sorted({("GENERAL" if g == "cross_cutting" else g) for g in class_groups})


def _logic_sha(ir: Mapping[str, Any]) -> str:
    names: Dict[str, str] = {}
    logic = _alpha_rename({"gate": ir["gate"], "exceptions": ir["exceptions"]}, names)
    logic.update({k: ir[k] for k in ("category", "polarity", "provenance")})
    logic["frame"] = ir["frame"]["declared"]
    return sha256_hex(logic)


def classify_rule(rule: Mapping[str, Any]) -> Dict[str, Any]:
    """One rule's engine status from its member cards. Pure."""
    cards = rule["cards"]
    out: Dict[str, Any] = {
        "status": None,
        "reasons": [],
        "node_named": [],
        "lord_generic": False,
        "transit_bodies": [],
        "plans": [],
        "logic_agree": None,
    }
    bad = [c for c in cards if c.get("status") != "active" or c.get("hash_error") or not c.get("ir")]
    if bad:
        out["status"] = Q_COMPILE
        out["reasons"] = sorted({r for c in bad for r in reason_codes(c)})
        return out
    plans: List[CardPlan] = []
    for c in cards:
        try:
            plans.append(plan_card(c["ir"], c["operands"]))
        except Unsupported as exc:
            out["status"] = Q_ENGINE
            out["reasons"] = [exc.code]
            return out
    out["logic_agree"] = len({_logic_sha(c["ir"]) for c in cards}) == 1
    out["node_named"] = sorted({n for p in plans for n in p.node_named})
    out["lord_generic"] = any(p.lord_generic for p in plans)
    out["transit_bodies"] = sorted({b for p in plans for b in p.transit_bodies})
    out["plans"] = plans
    if out["node_named"]:
        out["status"] = EXCLUDED_NODE
        out["reasons"] = ["NODE_POSITION_READ"]
    else:
        out["status"] = EVALUABLE
    return out


def _rule_sha(rule: Mapping[str, Any]) -> str:
    return sha256_hex(
        {
            "rulebook_id": rule["rulebook_id"],
            "cards": [{"card_id": c["card_id"], "card_sha256": c["card_sha256"], "ir_sha256": c.get("ir_sha256")} for c in rule["cards"]],
        }
    )


def build_units(
    final_cards: Mapping[str, Any], attested: Mapping[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """Return (units, rule_records_by_id, counts). Raises on any inconsistency (fail closed)."""
    if attested.get("attested_schema") != ATTESTED_SCHEMA:
        raise ValueError(f"attested file schema must be {ATTESTED_SCHEMA!r}")
    rules_in = {r["rulebook_id"]: r for r in attested["rules"]}
    final_rules = final_cards["cards"]
    if set(rules_in) != {r["rulebook_id"] for r in final_rules}:
        raise ValueError("attested rules and the final cards file are not the same 229-rule set")
    cluster_of: Dict[str, str] = {}
    clusters = final_cards["variant_conflict_clusters"]
    for cl in clusters:
        for v in cl["variants"]:
            if v in cluster_of:
                raise ValueError(f"{v} is in two clusters")
            cluster_of[v] = cl["cluster_id"]
    flagged = {r["rulebook_id"] for r in final_rules if r.get("variant_conflict")}
    if flagged != set(cluster_of):
        raise ValueError("variant_conflict flags and the cluster list disagree")

    recs: Dict[str, Dict[str, Any]] = {}
    for fr in final_rules:
        rid = fr["rulebook_id"]
        rule = rules_in[rid]
        cls = classify_rule(rule)
        groups = sorted({g for c in rule["cards"] for g in (c.get("class_groups") or [])})
        recs[rid] = {
            "rulebook_id": rid,
            "cluster_id": cluster_of.get(rid),
            "plane": fr["category"],
            "polarity": fr["polarity"],
            "provenance": fr["provenance"],
            "area_tags": area_tags(groups),
            "class_groups": groups,
            "status": cls["status"],
            "reasons": cls["reasons"],
            "node_named": cls["node_named"],
            "lord_generic": cls["lord_generic"],
            "transit_bodies": cls["transit_bodies"],
            "logic_agree": cls["logic_agree"],
            "frame": fr.get("frame"),
            "member_cards": [
                {
                    "card_id": c["card_id"],
                    "card_sha256": c.get("card_sha256"),
                    "ir_sha256": c.get("ir_sha256"),
                    "attested_status": c.get("status") if not c.get("hash_error") else "hash_form_unconvertible",
                }
                for c in rule["cards"]
            ],
            "rule_sha256": _rule_sha(rule),
        }
    # compile_status is the compiler/lints/attestation verdict only; engine statuses are separate
    for r in recs.values():
        r["compile_status"] = "active" if all(m["attested_status"] == "active" for m in r["member_cards"]) else "quarantined"

    units: List[Dict[str, Any]] = []
    cluster_members: Dict[str, List[str]] = OrderedDict()
    for cl in clusters:
        cluster_members[cl["cluster_id"]] = list(cl["variants"])
    for rid in sorted(recs):
        if recs[rid]["cluster_id"] is None:
            units.append(_unit(rid, "conflict_free", None, [recs[rid]]))
    for cid, members in cluster_members.items():
        units.append(_unit(cid, "cluster", cid, [recs[m] for m in members]))
    units.sort(key=lambda u: u["unit_id"])

    counts = _counts(units, recs)
    return units, recs, counts


def _unit(unit_id: str, kind: str, cluster_id: Optional[str], members: List[Dict[str, Any]]) -> Dict[str, Any]:
    planes = sorted({m["plane"] for m in members})
    pols = sorted({m["polarity"] for m in members})
    provs = sorted({m["provenance"] for m in members})
    ev = [m["rulebook_id"] for m in members if m["status"] == EVALUABLE]
    ex = [m["rulebook_id"] for m in members if m["status"] == EXCLUDED_NODE]
    if ev:
        status = EVALUABLE
    elif ex:
        status = EXCLUDED_NODE
    else:
        status = "quarantined"
    body = {
        "unit_id": unit_id,
        "kind": kind,
        "cluster_id": cluster_id,
        "plane": planes[0] if len(planes) == 1 else "mixed:" + "+".join(planes),
        "polarity": pols[0] if len(pols) == 1 else "mixed:" + "+".join(pols),
        "provenance": provs[0] if len(provs) == 1 else "mixed:" + "+".join(provs),
        "area_tags": sorted({t for m in members for t in m["area_tags"]}),
        "status": status,
        "evaluable_members": ev,
        "members": [
            {
                "rulebook_id": m["rulebook_id"],
                "status": m["status"],
                "compile_status": m["compile_status"],
                "reasons": m["reasons"],
                "node_named": m["node_named"],
                "lord_generic": m["lord_generic"],
                "transit_bodies": m["transit_bodies"],
                "plane": m["plane"],
                "polarity": m["polarity"],
                "area_tags": m["area_tags"],
                "frame": m["frame"],
                "logic_agree": m["logic_agree"],
                "member_cards": m["member_cards"],
                "rule_sha256": m["rule_sha256"],
            }
            for m in members
        ],
    }
    body["unit_sha256"] = sha256_hex(body)
    return body


def _counts(units: Sequence[Mapping[str, Any]], recs: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    u = Counter(x["status"] for x in units)
    by_kind = Counter((x["kind"], x["status"]) for x in units)
    by_plane = Counter((x["plane"], x["status"]) for x in units)
    r = Counter(x["status"] for x in recs.values())
    r_plane = Counter((x["plane"], x["status"]) for x in recs.values())
    reasons: Counter = Counter()
    for x in recs.values():
        for c in x["reasons"]:
            reasons[(x["status"], c)] += 1
    return {
        "units": len(units),
        "unit_status": dict(sorted(u.items())),
        "unit_status_by_kind": {f"{k}/{s}": n for (k, s), n in sorted(by_kind.items())},
        "unit_status_by_plane": {f"{p}/{s}": n for (p, s), n in sorted(by_plane.items())},
        "rules": len(recs),
        "rule_status": dict(sorted(r.items())),
        "rule_status_by_plane": {f"{p}/{s}": n for (p, s), n in sorted(r_plane.items())},
        "rule_reasons": {f"{s}/{c}": n for (s, c), n in sorted(reasons.items())},
        "evaluable_rules_lord_generic": sum(1 for x in recs.values() if x["status"] == EVALUABLE and x["lord_generic"]),
        "evaluable_rules_logic_disagree": sum(1 for x in recs.values() if x["status"] == EVALUABLE and x["logic_agree"] is False),
        "conflict_free_units": sum(1 for x in units if x["kind"] == "conflict_free"),
        "cluster_units": sum(1 for x in units if x["kind"] == "cluster"),
    }


def build_bundle(attested: Mapping[str, Any], recs: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """Word-free evaluation inputs for every evaluable rule."""
    by_id = {r["rulebook_id"]: r for r in attested["rules"]}
    rules = {}
    for rid in sorted(recs):
        if recs[rid]["status"] != EVALUABLE:
            continue
        cards = []
        for c in by_id[rid]["cards"]:
            cards.append({"card_id": c["card_id"], "card_sha256": c["card_sha256"], "ir_sha256": c["ir_sha256"], "ir": c["ir"], "operands": c["operands"]})
        rules[rid] = {"rulebook_id": rid, "cards": cards, "rule_sha256": recs[rid]["rule_sha256"]}
    doc = {"bundle_schema": K.BUNDLE_SCHEMA, "rules": rules}
    assert not _has_key(doc, "quote") and not _has_key(doc, "witnesses") and not _has_key(doc, "quote_terms"), "bundle must be word-free"
    return doc


def _has_key(obj: Any, key: str) -> bool:
    if isinstance(obj, Mapping):
        return key in obj or any(_has_key(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_key(v, key) for v in obj)
    return False


def source_tree_hashes(root: Path, rel_paths: Sequence[str]) -> Dict[str, str]:
    return {p: sha256_file(root / p) for p in sorted(rel_paths)}
