"""Synthetic Rule Card v1.1 fixtures for the E1 tests.

Every quote here is invented test prose. No real card, no real verse text, no
chart value and no edition quote is used (restricted editions must never
enter git).
"""

from __future__ import annotations

import copy

SYN_TEXT = "synthtext"
PID = "synthtext_pg0001_c01:en:p001"
FRAME_PID = "synthtext_pg0001_c01:en:p000"


def _cite(quote: str, text_id: str = SYN_TEXT, pid: str = PID) -> dict:
    return {
        "text_id": text_id,
        "chunk_id": pid.split(":")[0],
        "work": "Synthetic Test Text",
        "locus": "T.1",
        "quote": quote,
        "quote_language": "en",
        "passage_ids": [pid],
    }


def venus_vedha_card() -> dict:
    """Transit card shaped like the Venus vedha cards (no exemption)."""
    return {
        "card_id": "SYN-VEDHA-1",
        "schema_version": "rule-card-v1.1",
        "field1_citation": _cite(
            "If the test planet passes through the fifth sign it brings trouble "
            "when that place is struck by vedha from planets in the ninth sign."
        ),
        "field2_target_scope": {"class_group": "cross_cutting", "category": "transit"},
        "field3_reference_frame": {
            "frame": "chandra_lagna",
            "frame_terms": ["from the Moon"],
            "frame_citation": {
                "passage_ids": [FRAME_PID],
                "quote": "all houses here are counted from the natal Moon sign",
            },
        },
        "field4_necessary_gate": {
            "expr": {"op": "AND", "args": [{"operand": "ven_t"}, {"operand": "ven_v"}]},
            "gate_term": "if",
        },
        "field5_typed_operands": [
            {
                "id": "ven_t",
                "role": "transiting_graha",
                "doctrinal_graha": "shukra",
                "relation": "transits",
                "bhava": 5,
                "quote_terms": ["test planet", "fifth sign"],
            },
            {
                "id": "ven_v",
                "role": "transiting_graha",
                "doctrinal_graha": "shukra",
                "relation": "vedha_by",
                "target_bhavas": [9],
                "quote_terms": ["struck by vedha", "planets in the ninth"],
            },
        ],
        "field6_exceptions": [],
        "field7_discrete_arithmetic": [],
        "polarity": "obstructive",
        "provenance": "verse_cited",
        "confidence_notes": "synthetic",
    }


def dasha_card() -> dict:
    """Daśā card: antardaśā lord in the 6th or 8th from the daśā lord."""
    return {
        "card_id": "SYN-DASHA-1",
        "schema_version": "rule-card-v1.1",
        "field1_citation": _cite(
            "During the period when the sub lord stands sixth or eighth from the "
            "major lord the native meets obstacles of many kinds in that time."
        ),
        "field2_target_scope": {"class_group": "cross_cutting", "category": "dasha"},
        "field3_reference_frame": {"frame": "dasha_lord_natal_position", "frame_terms": ["from the major lord"]},
        "field4_necessary_gate": {
            "expr": {
                "op": "AND",
                "args": [{"operand": "md"}, {"op": "OR", "args": [{"operand": "ad6"}, {"operand": "ad8"}]}],
            },
            "gate_term": "when",
        },
        "field5_typed_operands": [
            {"id": "md", "role": "dasha_lord", "relation": "is_dasha_lord", "quote_terms": ["major lord"]},
            {
                "id": "ad6",
                "role": "antardasha_lord",
                "relation": "occupies",
                "bhava": 6,
                "target_role": "md",
                "quote_terms": ["sub lord", "sixth"],
            },
            {
                "id": "ad8",
                "role": "antardasha_lord",
                "relation": "occupies",
                "bhava": 8,
                "target_role": "md",
                "quote_terms": ["sub lord", "eighth"],
            },
        ],
        "field6_exceptions": [],
        "field7_discrete_arithmetic": [],
        "polarity": "obstructive",
        "provenance": "verse_cited",
        "confidence_notes": "synthetic",
    }


def av_card() -> dict:
    """Aṣṭakavarga gate with a card-stated comparator (synthetic 'without points' = eq 0)."""
    return {
        "card_id": "SYN-AV-1",
        "schema_version": "rule-card-v1.1",
        "field1_citation": _cite(
            "When the slow planet transits a sign with no benefic dots in its own "
            "chart of points the native suffers loss and much sorrow."
        ),
        "field2_target_scope": {"class_group": "cross_cutting", "category": "transit"},
        "field3_reference_frame": {"frame": "sign_of_transit_only", "frame_terms": ["transits a sign"]},
        "field4_necessary_gate": {
            "expr": {"op": "AND", "args": [{"operand": "sat_t"}, {"operand": "sat_av"}]},
            "gate_term": "when",
        },
        "field5_typed_operands": [
            {
                "id": "sat_t",
                "role": "transiting_graha",
                "doctrinal_graha": "shani",
                "relation": "transits",
                "quote_terms": ["slow planet transits a sign"],
            },
            {
                "id": "sat_av",
                "role": "ashtakavarga_bav",
                "doctrinal_graha": "shani",
                "relation": "bindus",
                "target_role": "sat_t",
                "quote_terms": ["no benefic dots", "its own chart of points"],
            },
        ],
        "field6_exceptions": [],
        "field7_discrete_arithmetic": [{"kind": "bindus_of_8", "bindus": 0, "comparator": "eq"}],
        "polarity": "obstructive",
        "provenance": "verse_cited",
        "confidence_notes": "synthetic",
    }


def natal_card() -> dict:
    return {
        "card_id": "SYN-NATAL-1",
        "schema_version": "rule-card-v1.1",
        "field1_citation": _cite(
            "The test planet in backward motion is said to be strong and gives its "
            "good results to the native all through the life."
        ),
        "field2_target_scope": {"class_group": "cross_cutting", "category": "natal_promise"},
        "field3_reference_frame": {"frame": "janma_lagna"},
        "field4_necessary_gate": {"expr": {"operand": "ven_r"}, "gate_term": "when"},
        "field5_typed_operands": [
            {
                "id": "ven_r",
                "role": "natal_graha",
                "doctrinal_graha": "shukra",
                "relation": "retrograde",
                "quote_terms": ["test planet", "backward motion"],
            }
        ],
        "field6_exceptions": [],
        "field7_discrete_arithmetic": [],
        "polarity": "promotive",
        "provenance": "verse_cited",
        "confidence_notes": "synthetic",
    }


def two_transit_card(j: dict, s: dict, op: str = "AND", frame: str = "chandra_lagna") -> dict:
    """Card with a Jupiter operand and a Saturn operand joined by op (for P4)."""
    card = venus_vedha_card()
    card["card_id"] = "SYN-P4"
    card["field1_citation"] = _cite(
        "When the great planet or the slow planet moves through the named house "
        "from the Moon the native gains much wealth and fame."
    )
    card["field3_reference_frame"] = {"frame": frame, "frame_terms": ["from the Moon"]}
    jo = {
        "id": "ju",
        "role": "transiting_graha",
        "doctrinal_graha": "guru",
        "relation": "transits",
        "quote_terms": ["great planet"],
    }
    so = {
        "id": "sa",
        "role": "transiting_graha",
        "doctrinal_graha": "shani",
        "relation": "transits",
        "quote_terms": ["slow planet"],
    }
    jo.update(j)
    so.update(s)
    card["field5_typed_operands"] = [jo, so]
    card["field4_necessary_gate"] = {
        "expr": {"op": op, "args": [{"operand": "ju"}, {"operand": "sa"}]},
        "gate_term": "when",
    }
    card["polarity"] = "promotive"
    return card


def clone(card: dict) -> dict:
    return copy.deepcopy(card)
