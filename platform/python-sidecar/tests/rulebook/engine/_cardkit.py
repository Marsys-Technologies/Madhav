"""Builders for invented Rule Cards used by the engine tests (synthetic prose only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.rulebook.compiler import compile_card, sha256_hex
from services.rulebook.engine.irtree import operand_table
from services.rulebook.engine.units import ATTESTED_SCHEMA

PID = "synthtext_pg0001_c01:en:p001"


def mk_card(
    card_id: str,
    category: str,
    expr: dict,
    operands: List[dict],
    *,
    frame: str = "janma_lagna",
    polarity: str = "promotive",
    quote: str = "When the named planet stands thus or so the native fares in this manner as the test text says.",
    provenance: str = "verse_cited",
    class_group: str = "cross_cutting",
    frame_role: Optional[str] = None,
    exceptions: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    f3: Dict[str, Any] = {"frame": frame}
    if frame_role:
        f3["frame_role"] = frame_role
    if frame != "janma_lagna":
        f3["frame_terms"] = ["named planet"]
    return {
        "card_id": card_id,
        "schema_version": "rule-card-v1.1",
        "field1_citation": {
            "text_id": "synthtext",
            "chunk_id": "synthtext_pg0001_c01",
            "work": "Synthetic Test Text",
            "locus": "T.1",
            "quote": quote,
            "quote_language": "en",
            "passage_ids": [PID],
        },
        "field2_target_scope": {"class_group": class_group, "category": category},
        "field3_reference_frame": f3,
        "field4_necessary_gate": {"expr": expr, "gate_term": "when"},
        "field5_typed_operands": operands,
        "field6_exceptions": exceptions or [],
        "field7_discrete_arithmetic": [],
        "polarity": polarity,
        "provenance": provenance,
        "confidence_notes": "synthetic",
    }


def op(oid: str, role: str, relation: str, graha: Optional[str] = None, **kw: Any) -> dict:
    o: Dict[str, Any] = {"id": oid, "role": role, "relation": relation, "quote_terms": ["named planet"]}
    if graha:
        o["doctrinal_graha"] = graha
    o.update(kw)
    return o


def saturn_transit(card_id="SYN-SAT", houses=(3, 6, 11), polarity="promotive", graha="shani") -> dict:
    return mk_card(
        card_id,
        "transit",
        {"operand": "t"},
        [op("t", "transiting_graha", "transits", graha, target_bhavas=list(houses))],
        frame="chandra_lagna",
        polarity=polarity,
    )


def attested(card: dict, class_groups: Optional[List[str]] = None) -> dict:
    """The owner-session record the manifest builder consumes (clear synthetic card; no bank needed)."""
    res = compile_card(card)
    rec: Dict[str, Any] = {
        "card_id": card["card_id"],
        "card_sha256": sha256_hex(card),
        "ratification_sha256": sha256_hex(card),
        "class_groups": class_groups or [card["field2_target_scope"]["class_group"]],
        "operands": operand_table(card),
    }
    if res.status == "active":
        rec.update(status="active", quarantine_reason=None, ir=res.ir, ir_sha256=res.ir_sha256)
    else:
        rec.update(status="quarantined_not_evaluable", quarantine_reason="; ".join(res.reasons), ir=res.ir, ir_sha256=res.ir_sha256)
    return rec


def attested_rules(rules: Dict[str, List[dict]]) -> dict:
    return {
        "attested_schema": ATTESTED_SCHEMA,
        "rules": [{"rulebook_id": rid, "cards": [attested(c) for c in cards]} for rid, cards in sorted(rules.items())],
    }


def final_cards(rows: Dict[str, dict], clusters: Optional[Dict[str, List[str]]] = None) -> dict:
    """rows: rulebook_id -> {category, polarity, provenance?, frame?}"""
    inc = {m for ms in (clusters or {}).values() for m in ms}
    return {
        "cards": [
            {
                "rulebook_id": rid,
                "category": r["category"],
                "polarity": r["polarity"],
                "provenance": r.get("provenance", "verse_cited"),
                "frame": r.get("frame", "janma_lagna"),
                "variant_conflict": rid in inc,
            }
            for rid, r in sorted(rows.items())
        ],
        "variant_conflict_clusters": [{"cluster_id": cid, "variants": ms} for cid, ms in sorted((clusters or {}).items())],
    }
