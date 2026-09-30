"""Exaltation / debility / mūlatrikoṇa sign data and the dignity category
helper (PROMISE_NATURE_YOGA_MAP_v1_1 §4.2; BPHS ch.3 śl.49–54,
PG37:C1–PG38:C2 [D]).

Moon's mūlatrikoṇa DEGREE-SPAN is OCR-degraded in the chunk — the sign
(Taurus) is unambiguous; the span is flagged 'unverified_ocr', not used.
Dignity categories follow the doctrine's stated order (exaltation >
mūlatrikoṇa > own > extreme friend's > friend's > neutral's > enemy's >
debility, §1.1); the virūpa ordering anchor lives on the
`dignity_of_transit_sign` factor row.
"""
from __future__ import annotations

from .frames import SIGN_LORDS
from .nature import naisargika_relation

# śl.49-50 (PG37:C1–C2): signs of exaltation with deepest-exaltation degrees;
# debilitation in the 7th sign from the exaltation sign, same degrees.
EXALTATION: dict[str, dict] = {
    "Sun": {"sign": "Aries", "deep_deg": 10.0},
    "Moon": {"sign": "Taurus", "deep_deg": 3.0},
    "Mars": {"sign": "Capricorn", "deep_deg": 28.0},
    "Mercury": {"sign": "Virgo", "deep_deg": 15.0},
    "Jupiter": {"sign": "Cancer", "deep_deg": 5.0},
    "Venus": {"sign": "Pisces", "deep_deg": 27.0},
    "Saturn": {"sign": "Libra", "deep_deg": 20.0},
}
DEBILITY: dict[str, dict] = {  # 7th sign from the exaltation sign
    "Sun": {"sign": "Libra", "deep_deg": 10.0},
    "Moon": {"sign": "Scorpio", "deep_deg": 3.0},
    "Mars": {"sign": "Cancer", "deep_deg": 28.0},
    "Mercury": {"sign": "Pisces", "deep_deg": 15.0},
    "Jupiter": {"sign": "Capricorn", "deep_deg": 5.0},
    "Venus": {"sign": "Virgo", "deep_deg": 27.0},
    "Saturn": {"sign": "Aries", "deep_deg": 20.0},
}

# Mūlatrikoṇa (śl.51-54, PG38:C1–C2). Spans are (sign, from_deg, to_deg)
# within the sign; Mercury: first 15° exaltation zone, next 5° mūlatrikoṇa,
# last 10° own.
MULATRIKONA: dict[str, dict] = {
    "Sun": {"sign": "Leo", "span": (0.0, 20.0)},
    # Moon: sign Taurus unambiguous; degree-span OCR-degraded in PG38:C1–C2
    "Moon": {"sign": "Taurus", "span": None, "span_state": "unverified_ocr"},
    "Mars": {"sign": "Aries", "span": (0.0, 12.0)},
    "Mercury": {"sign": "Virgo", "span": (15.0, 20.0)},
    "Jupiter": {"sign": "Sagittarius", "span": (0.0, 10.0)},  # first third
    "Venus": {"sign": "Libra", "span": (0.0, 15.0)},          # first half
    "Saturn": {"sign": "Aquarius", "span": (0.0, 20.0)},  # "same as the Sun"
}
DIGNITY_SOURCE = "BPHS ch.3 śl.49-54, PG37:C1-PG38:C2 [D]"

DIGNITY_ORDER = ("exaltation", "mulatrikona", "own", "extreme_friend",
                 "friend", "neutral", "enemy", "extreme_enemy", "debility")


def dignity_of(graha: str, sign: str, deg_in_sign: float | None = None,
               compound_relation: str | None = None) -> str:
    """The doctrine-ordered dignity category of `graha` in `sign`.

    `compound_relation` (pañcādha maitrī of the graha with the sign's lord)
    supplies the extreme_friend/friend/enemy/extreme_enemy distinction; when
    absent the NAISARGIKA relation alone is used (friend/enemy/neutral) —
    the extreme tiers are not derivable without the tatkālika operand.
    Moon's mūlatrikoṇa span is unverified_ocr: a degree-dependent MT query on
    the Moon returns 'unqualified', never a guessed span.
    """
    exalted = EXALTATION.get(graha, {}).get("sign") == sign
    debilitated = DEBILITY.get(graha, {}).get("sign") == sign
    mt = MULATRIKONA.get(graha)
    in_mt_sign = bool(mt and mt["sign"] == sign)
    if exalted and in_mt_sign:
        # exaltation sign coincides with the mūlatrikoṇa sign (Moon/Taurus,
        # Mercury/Virgo): the split is degree-dependent. Mercury's zones are
        # cited (first 15° exaltation, next 5° MT, last 10° own); Moon's MT
        # span is flagged unverified_ocr — unqualified, never a guessed span.
        if deg_in_sign is None:
            return "unqualified"
        if mt["span"] is None:
            return "unqualified"
        deep = EXALTATION[graha]["deep_deg"]
        lo, hi = mt["span"]
        if deg_in_sign < deep or (graha == "Mercury" and deg_in_sign < lo):
            return "exaltation"
        if lo <= deg_in_sign < hi:
            return "mulatrikona"
        return "own"
    if exalted:
        return "exaltation"
    if debilitated:
        return "debility"
    if in_mt_sign:
        if deg_in_sign is None:
            return "mulatrikona"  # sign-level query; span not consulted
        if mt["span"] is None:
            return "unqualified"  # Moon: span flagged unverified_ocr
        lo, hi = mt["span"]
        if lo <= deg_in_sign < hi:
            return "mulatrikona"
    if SIGN_LORDS.get(sign) == graha:
        return "own"
    if compound_relation is not None:
        if compound_relation in ("extreme_friend", "friend", "neutral",
                                 "enemy", "extreme_enemy"):
            return compound_relation
        return "unqualified"
    rel = naisargika_relation(graha, SIGN_LORDS.get(sign, ""))
    return rel if rel is not None else "unqualified"
