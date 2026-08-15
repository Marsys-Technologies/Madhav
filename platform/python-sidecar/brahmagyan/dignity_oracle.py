"""
brahmagyan/dignity_oracle.py — B-01 Dignity Oracle

Single shared dignity classifier for all consumers that need sign-level
dignity classification with degree-gated moolatrikona support.

Data source: pipeline/orchestrator/writers/bg_dignity_reference._DIGNITY_REFERENCE
(the authoritative L0 reference — reproduced here as a read-only static dict
built at import time, NOT re-imported from the writer module to avoid pulling
in writer-layer dependencies into serving-layer code).

Returns one of: "exalted" | "debilitated" | "moolatrikona" | "own" | "neutral"
All lowercase — matching the live SQL vocabulary in chart_facts.fact_value_text.

Priority order (classical BPHS):
  1. exalted          — planet in its exaltation sign
  2. debilitated      — planet in its debilitation sign
  3. nodes early-exit — Rahu/Ketu: only exalted/debilitated/neutral (§2.1)
  4. moolatrikona     — in MT sign AND degree within [moolatrikona_from, moolatrikona_to)
  5. own              — in own sign (but not in MT range)
  6. neutral          — none of the above

B-01 lane spec: exaltation and debilitation are checked BEFORE moolatrikona;
moolatrikona is checked BEFORE own; degree gate is [from, to) half-open interval.
Jupiter at 0°-10° Sag = MT; at 15° Sag = own. Sun at 0°-20° Leo = MT; at 25° = own.

Nodes (Rahu/Ketu) carry ONLY exalted/debilitated/neutral — §2.1 neutral-default.
"""
from __future__ import annotations

# ── Static dignity data ────────────────────────────────────────────────────────
# Reproduces bg_dignity_reference._DIGNITY_REFERENCE without importing the writer.
# Keyed by graha name (Title-case canonical form).
# "mt_sign": None means no moolatrikona tier for that graha.
# "mt_from" / "mt_to": the [from, to) degree range within the MT sign.
# "own": list of own sign names.

_DATA: dict[str, dict] = {
    "Sun": {
        "exaltation": "Aries",
        "debilitation": "Libra",
        "mt_sign": "Leo",
        "mt_from": 0,
        "mt_to": 20,
        "own": frozenset(["Leo"]),
    },
    "Moon": {
        "exaltation": "Taurus",
        "debilitation": "Scorpio",
        "mt_sign": "Taurus",
        "mt_from": 4,
        "mt_to": 30,
        "own": frozenset(["Cancer"]),
    },
    "Mars": {
        "exaltation": "Capricorn",
        "debilitation": "Cancer",
        "mt_sign": "Aries",
        "mt_from": 0,
        "mt_to": 12,
        "own": frozenset(["Aries", "Scorpio"]),
    },
    "Mercury": {
        "exaltation": "Virgo",
        "debilitation": "Pisces",
        "mt_sign": "Virgo",
        "mt_from": 16,
        "mt_to": 20,
        "own": frozenset(["Gemini", "Virgo"]),
    },
    "Jupiter": {
        "exaltation": "Cancer",
        "debilitation": "Capricorn",
        "mt_sign": "Sagittarius",
        "mt_from": 0,
        "mt_to": 10,
        "own": frozenset(["Sagittarius", "Pisces"]),
    },
    "Venus": {
        "exaltation": "Pisces",
        "debilitation": "Virgo",
        "mt_sign": "Libra",
        "mt_from": 0,
        "mt_to": 15,
        "own": frozenset(["Taurus", "Libra"]),
    },
    "Saturn": {
        "exaltation": "Libra",
        "debilitation": "Aries",
        "mt_sign": "Aquarius",
        "mt_from": 0,
        "mt_to": 20,
        "own": frozenset(["Capricorn", "Aquarius"]),
    },
    # Nodes: no moolatrikona or own tier (§2.1 neutral-default)
    "Rahu": {
        "exaltation": "Taurus",
        "debilitation": "Scorpio",
        "mt_sign": None,
        "mt_from": None,
        "mt_to": None,
        "own": frozenset(),
    },
    "Ketu": {
        "exaltation": "Scorpio",
        "debilitation": "Taurus",
        "mt_sign": None,
        "mt_from": None,
        "mt_to": None,
        "own": frozenset(),
    },
}

_NODES: frozenset[str] = frozenset(["Rahu", "Ketu"])


def classify_dignity(graha: str, sign_name: str, degree_in_sign: float) -> str:
    """Classify the dignity of `graha` occupying `sign_name` at `degree_in_sign`.

    Parameters
    ----------
    graha : str
        Title-case canonical graha name (e.g. "Jupiter", "Rahu").
    sign_name : str
        Title-case sign name (e.g. "Sagittarius", "Taurus").
    degree_in_sign : float
        Degree within the sign, in the range [0.0, 30.0).
        Used for the moolatrikona degree gate only.

    Returns
    -------
    str
        One of: "exalted" | "debilitated" | "moolatrikona" | "own" | "neutral"
        (all lowercase, matching the live SQL vocabulary).

    Raises
    ------
    KeyError
        If `graha` is not in the 9-planet canonical set.
    """
    r = _DATA.get(graha)
    if r is None:
        raise KeyError(
            f"dignity_oracle: unknown graha {graha!r}. "
            f"Valid names: {sorted(_DATA)}"
        )

    # 1. Exaltation (highest priority — checked before MT)
    if sign_name == r["exaltation"]:
        return "exalted"

    # 2. Debilitation
    if sign_name == r["debilitation"]:
        return "debilitated"

    # 3. Nodes early-exit — no MT or own tier
    if graha in _NODES:
        return "neutral"

    # 4. Moolatrikona — degree-gated: [mt_from, mt_to)
    if (
        r["mt_sign"] is not None
        and sign_name == r["mt_sign"]
        and r["mt_from"] <= degree_in_sign < r["mt_to"]
    ):
        return "moolatrikona"

    # 5. Own sign (after MT check — MT wins when in range)
    if sign_name in r["own"]:
        return "own"

    # 6. Neutral
    return "neutral"
