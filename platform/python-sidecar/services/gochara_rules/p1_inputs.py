"""P1 strict input wrappers over L1's pure rule functions (Codex round 7 [12]; design/P1_INPUTS_ANSWER_v1_0.md).

CLAUDE.md §N.5: L1 is the authority — a transit rule never carries a second convention. Combustion, maitrī and dignity are
therefore computed by CALLING L1's pure functions (`ga_writers.ga_condition_writer`: `check_combustion`,
`compute_combustion_arc`, `compute_tatkalika_relation`, `compute_panchadha_maitri`, `dignity_d1_from_sign`) over L0 table
rows (`bg_combustion_orbs`, `bg_graha_naisargika_friendship`, `bg_dignity_reference`).

Those L1 functions and their loaders carry SILENT DEFAULTS that must not be reachable from governed transit scoring:
  * `check_combustion` returns (False, False) for a graha with no orb row and reads missing numeric fields as 0
    (ga_condition_writer.py:389–394);
  * `compute_panchadha_maitri` returns "neutral" for an unrecognised combination (:452);
  * `_load_combustion_orbs` falls back to literal orbs when the table read fails (:669–680) and
    `_load_naisargika_friendships` to `{}`; the call site then defaults a missing pair to "neutral";
  * `dignity_d1_from_sign` classifies the mūlatrikoṇa range from a MODULE CONSTANT (`_MOOLATRIKONA_RANGE`) even when handed
    the L0 row, so a boundary schedule read from L0 `moolatrikona_from/to` could diverge from the classification.

This module validates COMPLETE, TYPED operands BEFORE the L1 call, so none of those paths can be taken, and a missing /
invalid / divergent input yields a NAMED qualification failure (`StrictInputError.reason`) — never a default. It reads rows
handed to it (the caller owns the connection) and has NO fallback loader. Dignity boundaries (the instants at which a
graha's dignity changes inside its own mūlatrikoṇa sign) are returned only when L0 and L1's effective range AGREE; a
divergence is REFUSED until the L0/L1 owner repairs it, so natal (L1) and transit never classify differently.

Vocabulary: L1 returns `great_friend` / `great_enemy`; the registry's maitrī categories are `extreme_friend` / `extreme_enemy`;
this module maps them (`maitri_category`).
"""
from __future__ import annotations

import math
from decimal import Decimal
from typing import Iterable

GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
COMBUSTIBLE = ("Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")        # a documented orb is required for these
NEVER_COMBUST = ("Sun", "Rahu", "Ketu")                                         # L1 M-19: declared, not defaulted
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_RELATIONS = ("friend", "neutral", "enemy")
_REGISTRY_LABEL = {"great_friend": "extreme_friend", "friend": "friend", "neutral": "neutral", "enemy": "enemy", "great_enemy": "extreme_enemy"}


class StrictInputError(ValueError):
    """A required operand is missing, malformed or divergent: the factor is UNQUALIFIED with this named `reason`."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def _l1():
    """L1's pure rule module (lazy: it pulls psycopg and the engine adapter; this module must stay importable without them)."""
    import ga_writers.ga_condition_writer as l1
    return l1


def _row(r) -> dict:
    if isinstance(r, dict):
        return r
    if hasattr(r, "_asdict"):
        return dict(r._asdict())
    raise StrictInputError("row_not_a_mapping", repr(r)[:80])


def _num(v, name: str, *, lo=None, hi=None, lo_open=False, hi_open=False, positive=False) -> float:
    """A finite real: int / float / Decimal only (psycopg returns NUMERIC as Decimal). No bool, no None, no string."""
    if isinstance(v, bool) or not isinstance(v, (int, float, Decimal)):
        raise StrictInputError(f"{name}_missing_or_not_numeric", repr(v))
    x = float(v)
    if not math.isfinite(x):
        raise StrictInputError(f"{name}_not_finite", repr(v))
    if positive and not x > 0:
        raise StrictInputError(f"{name}_not_positive", repr(v))
    if lo is not None and (x <= lo if lo_open else x < lo):
        raise StrictInputError(f"{name}_out_of_range", repr(v))
    if hi is not None and (x >= hi if hi_open else x > hi):
        raise StrictInputError(f"{name}_out_of_range", repr(v))
    return x


def _graha(g, name="graha") -> str:
    if g not in GRAHAS:
        raise StrictInputError(f"{name}_unknown", repr(g))
    return g


# ── combustion ───────────────────────────────────────────────────────────────────────────────────────────────
def validated_combustion_orbs(rows: Iterable) -> dict[str, dict]:
    """bg_combustion_orbs rows -> L1's `{graha: {'orb', 'deep'}}`, only if EVERY combustible graha has exactly one complete,
    finite, positive row with deep ≤ orb. No literal fallback exists in this module."""
    out: dict[str, dict] = {}
    for r in rows:
        r = _row(r)
        g = r.get("graha")
        if g not in GRAHAS:
            raise StrictInputError("combustion_row_graha_unknown", repr(g))
        if g in out:
            raise StrictInputError("combustion_row_duplicate", g)
        orb = _num(r.get("orb_degrees"), f"{g}_orb_degrees", positive=True)
        deep = _num(r.get("deep_orb_degrees"), f"{g}_deep_orb_degrees", positive=True)
        if deep > orb:
            raise StrictInputError("combustion_deep_exceeds_orb", f"{g}: deep {deep} > orb {orb}")
        out[g] = {"orb": orb, "deep": deep}
    missing = [g for g in COMBUSTIBLE if g not in out]
    if missing:
        raise StrictInputError("combustion_orbs_incomplete", f"no row for {missing}")
    return out


def combustion_state(graha: str, planet_longitude_deg, sun_longitude_deg, is_retrograde, orb_rows: Iterable) -> dict:
    """{'applicable', 'is_combust', 'is_deeply_combust', 'arc_deg', 'limit_deg'}; the arc and the rule are L1's.

    Sun / Rāhu / Ketu: a DECLARED non-applicability (L1 M-19: never combust) — not a missing row. Every other graha needs a
    validated orb row, finite longitudes in [0, 360) and a real boolean motion state (a missing station/speed is not `False`)."""
    _graha(graha)
    if graha in NEVER_COMBUST:
        return {"applicable": False, "reason": "never_combust_by_declaration", "is_combust": False, "is_deeply_combust": False}
    if not isinstance(is_retrograde, bool):
        raise StrictInputError("motion_state_missing_or_not_boolean", repr(is_retrograde))
    lon = _num(planet_longitude_deg, "planet_longitude", lo=0.0, hi=360.0, hi_open=True)
    sun = _num(sun_longitude_deg, "sun_longitude", lo=0.0, hi=360.0, hi_open=True)
    orbs = validated_combustion_orbs(orb_rows)
    l1 = _l1()
    arc = l1.compute_combustion_arc(lon, sun)
    is_combust, is_deep = l1.check_combustion(graha, arc, orbs, is_retrograde)
    row = orbs[graha]
    limit = row["deep"] if (is_retrograde and graha in l1._RETROGRADE_COMBUSTION_GRAHAS) else row["orb"]
    return {"applicable": True, "is_combust": is_combust, "is_deeply_combust": is_deep, "arc_deg": arc, "limit_deg": limit}


# ── maitrī ────────────────────────────────────────────────────────────────────────────────────────────────────
def validated_naisargika(rows: Iterable) -> dict[tuple[str, str], str]:
    """bg_graha_naisargika_friendship rows -> {(graha, other): relation}, only if the table is COMPLETE: every ordered pair of
    distinct grahas (9 × 8 = 72) exactly once with relation ∈ {friend, neutral, enemy}. A missing pair is never 'neutral'."""
    out: dict[tuple[str, str], str] = {}
    for r in rows:
        r = _row(r)
        g, o, rel = r.get("graha"), r.get("other_graha"), r.get("relation")
        if g not in GRAHAS or o not in GRAHAS or g == o:
            raise StrictInputError("naisargika_row_graha_invalid", f"{g!r}->{o!r}")
        if rel not in _RELATIONS:
            raise StrictInputError("naisargika_relation_invalid", f"{g}->{o}: {rel!r}")
        if (g, o) in out:
            raise StrictInputError("naisargika_row_duplicate", f"{g}->{o}")
        out[(g, o)] = rel
    missing = [(g, o) for g in GRAHAS for o in GRAHAS if g != o and (g, o) not in out]
    if missing:
        raise StrictInputError("naisargika_table_incomplete", f"{len(missing)} ordered pair(s) missing, first {missing[0]}")
    return out


def maitri_category(graha: str, graha_sign: str, sign_lord_sign: str, naisargika_rows: Iterable) -> dict:
    """Panchadha maitrī of `graha` (in `graha_sign`) towards the lord of that sign (placed in `sign_lord_sign`), by L1's rules:
    naisargika from L0, tatkālika from the two signs' mutual offset (`compute_tatkalika_relation`, offsets 2,3,4,10,11,12 = friend),
    combined by `compute_panchadha_maitri`. In its own sign there is no maitrī (declared `own_sign`). Result uses the registry labels."""
    _graha(graha)
    if graha_sign not in SIGNS or sign_lord_sign not in SIGNS:
        raise StrictInputError("sign_unknown", f"{graha_sign!r}, {sign_lord_sign!r}")
    l1 = _l1()
    lord = l1.SIGN_LORDS[graha_sign]
    if lord == graha:
        return {"applicable": False, "reason": "own_sign", "category": None}
    nais = validated_naisargika(naisargika_rows)[(graha, lord)]
    tat = l1.compute_tatkalika_relation(SIGNS.index(sign_lord_sign) + 1, SIGNS.index(graha_sign) + 1)
    if tat not in ("friend", "enemy"):
        raise StrictInputError("tatkalika_unrecognised", repr(tat))
    pan = l1.compute_panchadha_maitri(nais, tat)
    if pan not in _REGISTRY_LABEL:
        raise StrictInputError("panchadha_unrecognised", repr(pan))
    return {"applicable": True, "sign_lord": lord, "naisargika": nais, "tatkalika": tat, "panchadha": pan,
            "category": _REGISTRY_LABEL[pan]}


# ── dignity ───────────────────────────────────────────────────────────────────────────────────────────────────
def validated_dignity_row(rows: Iterable, graha: str) -> dict:
    """The complete bg_dignity_reference row for `graha` in L1's `dignity_ref` shape. Classical grahas need exaltation,
    debilitation, own signs and a mūlatrikoṇa sign + degree range; the nodes need exaltation and debilitation signs."""
    _graha(graha)
    found = [_row(r) for r in rows if _row(r).get("graha") == graha]
    if len(found) != 1:
        raise StrictInputError("dignity_row_missing_or_duplicate", f"{graha}: {len(found)} row(s)")
    r = found[0]
    for k in ("exaltation_sign", "debilitation_sign"):
        if r.get(k) not in SIGNS:
            raise StrictInputError(f"dignity_{k}_invalid", f"{graha}: {r.get(k)!r}")
    own = r.get("own_signs")
    if not isinstance(own, (list, tuple)) or any(s not in SIGNS for s in own):
        raise StrictInputError("dignity_own_signs_invalid", f"{graha}: {own!r}")
    ref = {"exaltation_sign": r["exaltation_sign"], "debilitation_sign": r["debilitation_sign"], "own_signs": list(own)}
    if graha in ("Rahu", "Ketu"):
        ref["moolatrikona_sign"] = None
        return ref
    if not own:
        raise StrictInputError("dignity_own_signs_empty", graha)
    if r.get("moolatrikona_sign") not in SIGNS:
        raise StrictInputError("dignity_moolatrikona_sign_invalid", f"{graha}: {r.get('moolatrikona_sign')!r}")
    lo = _num(r.get("moolatrikona_from"), f"{graha}_moolatrikona_from", lo=0.0, hi=30.0)
    hi = _num(r.get("moolatrikona_to"), f"{graha}_moolatrikona_to", lo=0.0, hi=30.0)
    if not lo < hi:
        raise StrictInputError("dignity_moolatrikona_range_inverted", f"{graha}: {lo}..{hi}")
    ref.update({"moolatrikona_sign": r["moolatrikona_sign"], "moolatrikona_from": lo, "moolatrikona_to": hi})
    return ref


def dignity_boundaries(graha: str, dignity_rows: Iterable) -> dict | None:
    """The in-sign dignity boundary degrees of `graha` — (mūlatrikoṇa sign, from, to) — for Stream A's crossing schedule, returned
    ONLY when L0's `moolatrikona_from/to` EQUAL the range L1's classifier actually uses (`_MOOLATRIKONA_RANGE`). A divergence is
    refused (`dignity_boundary_authority_divergence`): the schedule and the classification must come from one effective authority.
    None for a graha with no mūlatrikoṇa range (the nodes)."""
    ref = validated_dignity_row(dignity_rows, graha)
    if ref.get("moolatrikona_sign") is None:
        return None
    l1 = _l1()
    eff = l1._MOOLATRIKONA_RANGE.get(graha)
    if eff is None or (float(eff[0]), float(eff[1])) != (ref["moolatrikona_from"], ref["moolatrikona_to"]) \
            or l1._MOOLATRIKONA.get(graha) != ref["moolatrikona_sign"]:
        raise StrictInputError("dignity_boundary_authority_divergence",
                               f"{graha}: L0 {ref['moolatrikona_sign']} {ref['moolatrikona_from']}..{ref['moolatrikona_to']} "
                               f"vs L1 classifier {l1._MOOLATRIKONA.get(graha)} {eff}")
    return {"sign": ref["moolatrikona_sign"], "from_deg": ref["moolatrikona_from"], "to_deg": ref["moolatrikona_to"]}


def dignity_category(graha: str, sign: str, degree_in_sign, dignity_rows: Iterable) -> str:
    """L1's `dignity_d1_from_sign` over a validated complete row, after the boundary-authority check (classical grahas)."""
    ref = validated_dignity_row(dignity_rows, graha)
    if sign not in SIGNS:
        raise StrictInputError("sign_unknown", repr(sign))
    deg = _num(degree_in_sign, "degree_in_sign", lo=0.0, hi=30.0, hi_open=True)
    dignity_boundaries(graha, dignity_rows)                       # raises on authority divergence; None for the nodes
    return _l1().dignity_d1_from_sign(graha, sign, deg, ref)
