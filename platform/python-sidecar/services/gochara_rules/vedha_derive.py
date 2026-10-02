"""Vedha derivation, value mapping and pairs accessor (draft AM-18, RULED steward
M20261002T004621-2b84; design/P2_VEDHA_ANSWER_v1_0.md).

Vedha is an INTERVAL INTERSECTION over stored residence spans, half-open, at the
spans' own instant precision:

    (primary graha resident in house h from the janma-rāśi)
        ∩ (an obstructor resident in the vedha house v)

Pairs (primary house -> vedha house) are READ from the L0 table
`bg_transit_rules` — never copied here — and ONLY the rows that carry a classical
citation (Phaladīpikā XXVI śl.3–8: phaladeepika:PG322:C1, PG323:C1). The six
Rāhu/Ketu rows L0 itself flags 'UNSOURCED' are refused.

Cited doctrine (served corpus, read verbatim): an occupied vedha place NULLIFIES
the good result of a favourable-house transit. Value mapping (a cited step, not a
calibration): active obstruction -> 0.0 on the FOR-channel of the record; no active
obstruction -> 1.0; nothing graded. The window stays admitted and the record stays
stored with qualification `vedha_active` (the spec's "zeroes" means "excludes").

Rulings applied here:
  * exceptions Sun<->Saturn and Moon<->Mercury (M-8) never obstruct each other;
  * `cancelled_vipareeta` is NOT produced — no served citation (ND-VIPAREETA);
  * Rāhu/Ketu as obstructors are UNDECIDED (ND-NODE-VEDHA): while a node resides in the
    vedha house and no cited obstructor does, the state is `unqualified`
    (`node_obstruction_undecided`) — neither 0 nor 1;
  * the Moon is not a stored agent, so a stored state can prove `active` but never fully
    `inactive`: every 1.0 carries the machine-readable scope
    `excluding_on_demand_moon_obstruction` — except for a Mercury primary, whose cited
    exception already removes the Moon from the obstructor set;
  * applicability: favourable-house residence records only. A record whose
    (graha, house) is not a cited pair carries NO vedha factor (declared not-applicable).

This module is also the INDEPENDENT re-derivation the verifier uses (no builder code).
"""
from __future__ import annotations

from datetime import datetime, timezone

from .vedha import exception_for

MOON_SCOPE = "excluding_on_demand_moon_obstruction"
NODES = frozenset({"Rahu", "Ketu"})
CLASSICAL = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
# the Moon is never a STORED agent (M-3 / AM-14), so it is never in the stored obstructor set
STORED_OBSTRUCTORS = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

STATE_ACTIVE, STATE_INACTIVE, STATE_UNQUALIFIED = "active", "inactive", "unqualified"


class VedhaPairsError(ValueError):
    pass


# ── pairs accessor over bg_transit_rules ─────────────────────────────────────
_PAIRS_SQL = ("SELECT graha, primary_house, vedha_house, classical_citation, rule_type "
              "FROM bg_transit_rules WHERE vedha_house IS NOT NULL")


def pairs_from_rows(rows) -> dict[tuple[str, int], int]:
    """(graha, primary_house) -> vedha_house from bg_transit_rules rows (dicts or
    tuples in the _PAIRS_SQL column order). Refuses uncited and node rows; refuses a
    row that contradicts another."""
    out: dict[tuple[str, int], int] = {}
    for r in rows:
        if not isinstance(r, dict):
            r = dict(zip(("graha", "primary_house", "vedha_house", "classical_citation", "rule_type"), r))
        graha = str(r["graha"]).strip().capitalize()
        cite = (r.get("classical_citation") or "").strip()
        if graha not in CLASSICAL:
            continue                                        # Rāhu/Ketu rows: L0-flagged UNSOURCED, not usable
        if not cite or cite.upper().startswith("UNSOURCED"):
            raise VedhaPairsError(f"uncited vedha row for {graha} {r['primary_house']}: refused")
        if r.get("rule_type") not in (None, "favourable"):
            raise VedhaPairsError("vedha pairs apply to favourable-house rows only")
        key = (graha, int(r["primary_house"]))
        if key in out and out[key] != int(r["vedha_house"]):
            raise VedhaPairsError(f"conflicting vedha houses for {key}")
        out[key] = int(r["vedha_house"])
    return out


def load_pairs(cursor) -> dict[tuple[str, int], int]:
    """Read the pairs through a DB-API cursor (the caller owns the connection)."""
    cursor.execute(_PAIRS_SQL)
    return pairs_from_rows(cursor.fetchall())


# ── interval helpers (half-open, UTC instants; ISO strings in, same strings out) ──
def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def house_from_moon(sign: int, moon_sign: int) -> int:
    """Inclusive count from the janma-rāśi (1st = the Moon's own sign)."""
    return (sign - moon_sign) % 12 + 1


def _house_spans(spans, moon_sign, house):
    return [(s[1], s[2]) for s in spans if house_from_moon(s[0], moon_sign) == house]


def _intersect(a, b):
    lo, hi = max(_t(a[0]), _t(b[0])), min(_t(a[1]), _t(b[1]))
    if lo >= hi:
        return None
    return (max((a[0], b[0]), key=_t), min((a[1], b[1]), key=_t))


def _union(spans):
    """Merge overlapping AND abutting half-open spans."""
    out = []
    for lo, hi in sorted(spans, key=lambda s: _t(s[0])):
        if out and _t(lo) <= _t(out[-1][1]):
            if _t(hi) > _t(out[-1][1]):
                out[-1] = (out[-1][0], hi)
        else:
            out.append((lo, hi))
    return out


def derive_vedha(primary: str, primary_house: int, primary_span, *, moon_sign: int,
                 residence: dict[str, list], pairs: dict[tuple[str, int], int]) -> dict:
    """Vedha state over ONE primary residence span.

    residence: graha -> [(sign 1..12, t_in, t_out), …] stored residence spans, nodes included.
    Returns {"applicable": bool, "segments": [{t_in, t_out, state, value, reason, scope,
    obstructors}]} partitioning primary_span; `applicable: False` (no segments) when the
    (primary, house) is not a cited pair.
    """
    key = (primary, primary_house)
    if key not in pairs:
        return {"applicable": False, "reason": "no_cited_vedha_pair_for_this_house", "segments": []}
    v_house = pairs[key]
    cited: dict[str, list] = {}
    for g in STORED_OBSTRUCTORS:
        if g == primary or exception_for(primary, g) != "none":
            continue                                        # M-8 exception pairs never obstruct
        if g not in residence:
            raise VedhaPairsError(f"stored residence spans missing for obstructor {g}")
        hit = [x for x in (_intersect(primary_span, s) for s in _house_spans(residence[g], moon_sign, v_house)) if x]
        if hit:
            cited[g] = hit
    node_hits = []
    for n in sorted(NODES):
        if n not in residence:
            raise VedhaPairsError(f"stored residence spans missing for {n}")
        node_hits += [x for x in (_intersect(primary_span, s) for s in _house_spans(residence[n], moon_sign, v_house)) if x]
    active = _union([x for hs in cited.values() for x in hs])
    node_only = _subtract(_union(node_hits), active)
    cuts = sorted({primary_span[0], primary_span[1]}
                  | {t for sp in active + node_only + [h for hs in cited.values() for h in hs] for t in sp}, key=_t)
    moon_excepted = exception_for(primary, "Moon") != "none"      # Mercury primary: the Moon never obstructs
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        if any(_t(lo) <= _t(a) and _t(b) <= _t(hi) for lo, hi in active):
            names = sorted(g for g, hs in cited.items() if any(_t(lo) <= _t(a) < _t(hi) for lo, hi in hs))
            segs.append({"t_in": a, "t_out": b, "state": STATE_ACTIVE, "value": 0.0, "reason": None,
                         "scope": None, "obstructors": names})
        elif any(_t(lo) <= _t(a) and _t(b) <= _t(hi) for lo, hi in node_only):
            segs.append({"t_in": a, "t_out": b, "state": STATE_UNQUALIFIED, "value": None,
                         "reason": "node_obstruction_undecided", "scope": None, "obstructors": []})
        else:
            segs.append({"t_in": a, "t_out": b, "state": STATE_INACTIVE, "value": 1.0, "reason": None,
                         "scope": None if moon_excepted else MOON_SCOPE, "obstructors": []})
    return {"applicable": True, "vedha_house": v_house, "segments": segs}


def _subtract(spans, minus):
    out = []
    for lo, hi in spans:
        cur = [(lo, hi)]
        for mlo, mhi in minus:
            nxt = []
            for a, b in cur:
                if _t(mhi) <= _t(a) or _t(b) <= _t(mlo):
                    nxt.append((a, b)); continue
                if _t(a) < _t(mlo):
                    nxt.append((a, mlo))
                if _t(mhi) < _t(b):
                    nxt.append((mhi, b))
            cur = nxt
        out += cur
    return out


def vedha_factor_value(segment: dict) -> dict:
    """The factor result the score algebra consumes for one derived segment."""
    return {"value": segment["value"], "null_state": "unqualified", "reason": segment["reason"],
            "qualification": "vedha_active" if segment["state"] == STATE_ACTIVE else None,
            "scope": segment["scope"]}
