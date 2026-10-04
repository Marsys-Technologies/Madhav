"""INDEPENDENT oracle for the vedha derivation (Codex round 7 [6c]) — a different ALGORITHM, shared with `vedha_derive` only
by the cited exception table (`vedha.exception_for`) and the validated pairs object.

`vedha_derive.derive_vedha` computes interval algebra (intersect / union / subtract over spans). This oracle never builds an
interval: it evaluates the vedha state POINTWISE at an instant (which sign is each graha in at t? a half-open lookup), takes
the instants at which anything could change (every span endpoint) and evaluates once inside each elementary interval, then
merges equal neighbours. A verifier compares the two; a defect in either algebra shows up as a disagreement."""
from __future__ import annotations

from datetime import datetime, timezone

from .vedha import exception_for

_NODES = ("Rahu", "Ketu")
_STORED = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
MOON_SCOPE = "excluding_on_demand_moon_obstruction"


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _sign_at(spans, t: datetime):
    """The sign of the (unique) span with t_in <= t < t_out, else None (no coverage)."""
    for sign, a, b in spans:
        if _t(a) <= t < _t(b):
            return sign
    return None


def state_at(t: str, primary: str, primary_house: int, *, moon_sign: int, residence: dict, pairs) -> dict:
    """The vedha state of a record on `primary` in `primary_house` at the single instant `t`."""
    key = (primary, primary_house)
    if key not in pairs:
        return {"state": "not_applicable"}
    v_house = pairs[key]
    when = _t(t)
    house_of = lambda sign: (sign - moon_sign) % 12 + 1
    active, unknown = [], []
    for g in _STORED:
        if g == primary or exception_for(primary, g) != "none":
            continue
        sign = _sign_at(residence.get(g, []), when)
        if sign is None:
            unknown.append(g)
        elif house_of(sign) == v_house:
            active.append(g)
    node_in, node_missing = False, False
    for n in _NODES:
        sign = _sign_at(residence.get(n, []), when)
        if sign is None:
            node_missing = True
        elif house_of(sign) == v_house:
            node_in = True
    if active:
        return {"state": "active", "value": 0.0, "reason": None, "scope": None, "obstructors": sorted(active), "unknown_obstructors": []}
    reasons = (["obstructor_residence_unknown"] if unknown else []) + (["node_obstruction_undecided"] if node_in else []) \
        + (["node_residence_unknown"] if node_missing else [])
    if reasons:
        return {"state": "unqualified", "value": None, "reason": reasons[0], "scope": None, "obstructors": [], "unknown_obstructors": sorted(unknown)}
    return {"state": "inactive", "value": 1.0, "reason": None,
            "scope": None if exception_for(primary, "Moon") != "none" else MOON_SCOPE, "obstructors": [], "unknown_obstructors": []}


def oracle_segments(primary: str, primary_house: int, primary_span, *, moon_sign: int, residence: dict, pairs) -> list[dict]:
    """Maximal runs of identical state over `primary_span`, found by pointwise evaluation inside each elementary interval."""
    lo, hi = _t(primary_span[0]), _t(primary_span[1])
    cuts = {lo, hi}
    for spans in residence.values():
        for _, a, b in spans:
            for x in (_t(a), _t(b)):
                if lo < x < hi:
                    cuts.add(x)
    points = sorted(cuts)
    runs: list[dict] = []
    for a, b in zip(points, points[1:]):
        st = state_at(a.isoformat(), primary, primary_house, moon_sign=moon_sign, residence=residence, pairs=pairs)
        if st["state"] == "not_applicable":
            return []
        sig = tuple(sorted((k, repr(v)) for k, v in st.items()))
        if runs and runs[-1]["_sig"] == sig:
            runs[-1]["t_out"] = b
        else:
            runs.append({**st, "t_in": a, "t_out": b, "_sig": sig})
    for r in runs:
        r.pop("_sig")
    return runs


def normalise(segments: list[dict]) -> list[tuple]:
    """Canonical comparison form for EITHER side: merged runs of (state, value, reason, scope, obstructors, unknown) with UTC
    instants — so an algebra that splits at more cut points than the oracle still compares equal when the states agree."""
    runs: list[list] = []
    for s in segments:
        a = _t(s["t_in"]) if isinstance(s["t_in"], str) else s["t_in"]
        b = _t(s["t_out"]) if isinstance(s["t_out"], str) else s["t_out"]
        sig = (s["state"], s["value"], s["reason"], s["scope"], tuple(s["obstructors"]), tuple(s.get("unknown_obstructors", [])))
        if runs and runs[-1][2] == sig and runs[-1][1] == a:
            runs[-1][1] = b
        else:
            runs.append([a, b, sig])
    return [(a.isoformat(), b.isoformat(), sig) for a, b, sig in runs]


def agrees(derived: dict, primary: str, primary_house: int, primary_span, *, moon_sign: int, residence: dict, pairs) -> bool:
    """True iff the interval-algebra result equals the pointwise oracle (the verifier's independent check)."""
    oracle = oracle_segments(primary, primary_house, primary_span, moon_sign=moon_sign, residence=residence, pairs=pairs)
    if not derived["applicable"]:
        return oracle == []
    return normalise(derived["segments"]) == normalise(oracle)
