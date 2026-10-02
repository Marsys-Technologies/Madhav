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
calibration): the cited binary factor is applied to the favourable-residence record's CONTRIBUTION
(active obstruction -> 0.0; established inactivity -> 1.0; nothing graded), and THEN that contribution
is assigned to the event class's channel. Active obstruction never changes admission or admitted
support: the window stays admitted and the record stays stored with qualification `vedha_active`
(the spec's "zeroes" means "excludes").

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
  * COVERAGE (Codex round 7 [6a]): an obstructor's residence must be ESTABLISHED over the primary span
    before its absence from the vedha house counts. An empty or gapped residence list is NOT "inactive":
    where no known cited obstruction already settles the value (known obstruction -> 0.0 wins), a coverage
    gap yields `unqualified` (`obstructor_residence_unknown`) — never 1.0;
  * applicability: favourable-house residence records only. A record whose
    (graha, house) is not a cited pair carries NO vedha factor (declared not-applicable).

This module is also the INDEPENDENT re-derivation the verifier uses (no builder code).
"""
from __future__ import annotations

import hashlib
import json
import re
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
_COLUMNS = ("graha", "primary_house", "vedha_house", "classical_citation", "rule_type")

# Supported citation provenance: the served Phaladīpikā chunks read verbatim (design/P2_VEDHA_ANSWER_v1_0.md):
# Adhyāya XXVI, ślokas 3–8 at phaladeepika:PG322:C1 / PG323:C1. A citation anywhere else is refused.
_CITATION = re.compile(r"^Phaladipika Adh\. XXVI, Sloka ([3-8]) — (phaladeepika:PG32[23]:C1)\b")
_UNSOURCED = "UNSOURCED"

# The load CENSUS (counts, not the mapping — the mapping stays in L0 and is never copied here): 36 cited classical
# pairs by graha + 6 L0-flagged UNSOURCED node rows, read-only from production bg_transit_rules 2026-10-02.
# A load that does not match is an INCOMPLETE or CHANGED authority and is refused — a missing pair must never
# turn into a declared non-applicability.
EXPECTED_CLASSICAL_CENSUS = {"Sun": 4, "Moon": 6, "Mars": 3, "Mercury": 6, "Jupiter": 5, "Venus": 9, "Saturn": 3}
EXPECTED_NODE_ROWS = {"Rahu": 3, "Ketu": 3}


class VedhaPairs(dict):
    """(graha, primary_house) -> vedha_house for a VALIDATED, COMPLETE load of the L0 pairs, carrying the content
    identity of the rows it consumed. Only `pairs_from_rows` / `load_pairs` construct it; `derive_vedha` refuses
    any other mapping, so an absent key here is a genuine "no cited pair for this house", never missing data."""
    content_digest: str = ""
    census: dict = {}


def pairs_content_digest(rows) -> str:
    """sha256 of the canonical JSON of every consumed row (all 42, node rows included) in a total order — the `l0`
    binding of the AM-16 input vector."""
    norm = sorted([str(r["graha"]).strip().lower(), int(r["primary_house"]), int(r["vedha_house"]),
                   r.get("classical_citation") or "", r.get("rule_type") or ""] for r in rows)
    return hashlib.sha256(json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def pairs_from_rows(rows) -> VedhaPairs:
    """Validate and load the pairs from bg_transit_rules rows (dicts or tuples in the _PAIRS_SQL column order).

    Refuses: an unknown graha; a classical row without a supported Phaladīpikā XXVI.3–8 citation (uncited,
    UNSOURCED-flagged or fabricated); a node row that is not L0-flagged UNSOURCED (a newly cited node doctrine is
    ND-NODE-VEDHA's decision, not a silent change); rule_type other than 'favourable'; house numbers outside
    1..12 or a vedha house equal to its primary; a duplicate (graha, primary_house) key; and a load whose census
    differs from the expected 36 + 6 (an incomplete authority)."""
    norm = []
    for r in rows:
        if not isinstance(r, dict):
            r = dict(zip(_COLUMNS, r))
        norm.append(r)
    out = VedhaPairs()
    seen: set[tuple[str, int]] = set()
    classical_n: dict[str, int] = {}
    node_n: dict[str, int] = {}
    for r in norm:
        graha = str(r["graha"]).strip().capitalize()
        cite = (r.get("classical_citation") or "").strip()
        ph, vh = r["primary_house"], r["vedha_house"]
        if r.get("rule_type") != "favourable":
            raise VedhaPairsError(f"vedha rows apply to rule_type 'favourable' only, got {r.get('rule_type')!r}")
        if not all(isinstance(h, int) and not isinstance(h, bool) and 1 <= h <= 12 for h in (ph, vh)) or ph == vh:
            raise VedhaPairsError(f"house domain violated for {graha}: primary {ph!r}, vedha {vh!r}")
        key = (graha, int(ph))
        if key in seen:                                     # unique keys over ALL rows — node rows included (round 8 R8-7)
            raise VedhaPairsError(f"duplicate vedha row for {key}")
        seen.add(key)
        if graha in NODES:
            if not cite.upper().startswith(_UNSOURCED):
                raise VedhaPairsError(f"{graha} {ph}: a node vedha row is cited — ND-NODE-VEDHA must be ruled first")
            node_n[graha] = node_n.get(graha, 0) + 1
            continue                                        # L0-flagged UNSOURCED node rows are counted, never usable
        if graha not in CLASSICAL:
            raise VedhaPairsError(f"unknown graha {r['graha']!r} in a vedha row")
        if not _CITATION.match(cite):
            raise VedhaPairsError(f"unsupported or missing citation for {graha} {ph}: {cite[:70]!r} (Phaladīpikā XXVI.3–8 only)")
        out[key] = int(vh)
        classical_n[graha] = classical_n.get(graha, 0) + 1
    if classical_n != EXPECTED_CLASSICAL_CENSUS or node_n != EXPECTED_NODE_ROWS:
        raise VedhaPairsError(f"incomplete or changed vedha authority: classical {classical_n} vs {EXPECTED_CLASSICAL_CENSUS}; "
                              f"node rows {node_n} vs {EXPECTED_NODE_ROWS}")
    out.content_digest = pairs_content_digest(norm)
    out.census = {"classical": dict(classical_n), "node_rows": dict(node_n), "total": sum(classical_n.values()) + sum(node_n.values())}
    return out


def load_pairs(cursor) -> VedhaPairs:
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


def _validated_spans(graha: str, spans) -> list:
    """Residence spans of one graha, validated: a sign 1..12, t_in < t_out, no overlap (a graha is in one sign at a time)."""
    out = []
    for sp in spans:
        sign, t_in, t_out = sp
        if not (isinstance(sign, int) and not isinstance(sign, bool) and 1 <= sign <= 12) or not _t(t_in) < _t(t_out):
            raise VedhaPairsError(f"malformed residence span for {graha}: {sp!r}")
        out.append((sign, t_in, t_out))
    out.sort(key=lambda x: _t(x[1]))
    for prev, cur in zip(out, out[1:]):
        if _t(cur[1]) < _t(prev[2]):
            raise VedhaPairsError(f"overlapping residence spans for {graha}: {prev!r} / {cur!r}")
    return out


def _coverage_gaps(spans, within) -> list:
    """The parts of `within` NOT covered by any residence span of this graha (any sign): a graha is always in some sign, so an
    uncovered instant is MISSING DATA, never 'not in the vedha house'."""
    clipped = [x for x in (_intersect(within, (s[1], s[2])) for s in spans) if x]
    return _subtract([within], _union(clipped))


def derive_vedha(primary: str, primary_house: int, primary_span, *, moon_sign: int,
                 residence: dict[str, list], pairs: "VedhaPairs") -> dict:
    """Vedha state over ONE primary residence span.

    residence: graha -> [(sign 1..12, t_in, t_out), …] stored residence spans, nodes included. An obstructor with no
    spans, or spans that do not cover the primary span, has a COVERAGE GAP over the uncovered part (Codex round 7 [6a]).
    pairs: a validated `VedhaPairs` load — a plain mapping is refused (an absent key must mean "no cited pair", not "missing data").
    Returns {"applicable", "state", "segments": [{t_in, t_out, state, value, reason, reasons, scope, obstructors,
    unknown_obstructors}]} partitioning primary_span; `applicable: False` (state `not_applicable`, no segments) when
    the (primary, house) is not a cited pair.

    Precedence per segment: known cited obstruction -> 0.0 (settles it whatever else is unknown); otherwise any coverage
    gap of a necessary obstructor, or an undecided node obstruction / node coverage gap -> NULL (`unqualified`); only
    ESTABLISHED inactivity -> 1.0 (with the Moon scope unless the primary is Mercury).
    """
    if not isinstance(pairs, VedhaPairs):
        raise VedhaPairsError("pairs must be a validated VedhaPairs load (pairs_from_rows / load_pairs)")
    if not (isinstance(moon_sign, int) and not isinstance(moon_sign, bool) and 1 <= moon_sign <= 12):
        raise VedhaPairsError(f"moon_sign must be 1..12, got {moon_sign!r}")
    key = (primary, primary_house)
    if key not in pairs:
        return {"applicable": False, "state": "not_applicable", "reason": "no_cited_vedha_pair_for_this_house", "segments": []}
    if not _t(primary_span[0]) < _t(primary_span[1]):
        raise VedhaPairsError(f"empty or inverted primary span {primary_span!r}")
    v_house = pairs[key]
    necessary = [g for g in STORED_OBSTRUCTORS if g != primary and exception_for(primary, g) == "none"]   # M-8 exceptions never obstruct
    cited: dict[str, list] = {}
    gaps: dict[str, list] = {}
    for g in necessary:
        spans = _validated_spans(g, residence.get(g, []))
        gap = _coverage_gaps(spans, primary_span)
        if gap:
            gaps[g] = gap
        hit = [x for x in (_intersect(primary_span, s) for s in _house_spans(spans, moon_sign, v_house)) if x]
        if hit:
            cited[g] = hit
    node_hits, node_gaps = [], []
    for n in sorted(NODES):
        spans = _validated_spans(n, residence.get(n, []))
        node_gaps += _coverage_gaps(spans, primary_span)
        node_hits += [x for x in (_intersect(primary_span, s) for s in _house_spans(spans, moon_sign, v_house)) if x]
    active = _union([x for hs in cited.values() for x in hs])
    node_only = _subtract(_union(node_hits), active)
    node_gaps = _union(node_gaps)
    all_gaps = [x for gs in gaps.values() for x in gs]
    cuts = sorted({primary_span[0], primary_span[1]}
                  | {t for sp in active + node_only + node_gaps + all_gaps + [h for hs in cited.values() for h in hs] for t in sp}, key=_t)
    moon_excepted = exception_for(primary, "Moon") != "none"      # Mercury primary: the Moon never obstructs
    inside = lambda spans, a, b: any(_t(lo) <= _t(a) and _t(b) <= _t(hi) for lo, hi in spans)
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        if inside(active, a, b):
            names = sorted(g for g, hs in cited.items() if any(_t(lo) <= _t(a) < _t(hi) for lo, hi in hs))
            segs.append({"t_in": a, "t_out": b, "state": STATE_ACTIVE, "value": 0.0, "reason": None, "reasons": [],
                         "scope": None, "obstructors": names, "unknown_obstructors": []})
            continue
        unknown = sorted(g for g, gs in gaps.items() if inside(gs, a, b))
        reasons = []
        if unknown:
            reasons.append("obstructor_residence_unknown")
        if inside(node_only, a, b):
            reasons.append("node_obstruction_undecided")
        if inside(node_gaps, a, b):
            reasons.append("node_residence_unknown")
        if reasons:
            segs.append({"t_in": a, "t_out": b, "state": STATE_UNQUALIFIED, "value": None, "reason": reasons[0], "reasons": reasons,
                         "scope": None, "obstructors": [], "unknown_obstructors": unknown})
        else:
            segs.append({"t_in": a, "t_out": b, "state": STATE_INACTIVE, "value": 1.0, "reason": None, "reasons": [],
                         "scope": None if moon_excepted else MOON_SCOPE, "obstructors": [], "unknown_obstructors": []})
    return {"applicable": True, "state": "derived", "vedha_house": v_house, "segments": segs}


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


def vedha_factor_value(segment: dict, *, factor_ref: tuple[str, str]) -> dict:
    """The STRUCTURED factor result the score algebra and the writer carry for one derived segment, labelled with the
    factor ref of the membership that CALLED it (Codex round 7 [6c]): `state` (active / inactive / unqualified),
    `value` (0.0 | 1.0 | None — a NULL channel under R1, never 0), `reason` / `reasons`, `qualification`
    ('vedha_active' only when active), `scope` (the machine-readable Moon scope on every 1.0 except Mercury's), the
    obstructors that settled it, and the unknown obstructors that blocked it."""
    _check_ref(factor_ref)
    return {"state": segment["state"], "value": segment["value"], "null_state": "unqualified",
            "reason": segment["reason"], "reasons": list(segment.get("reasons", [])),
            "qualification": "vedha_active" if segment["state"] == STATE_ACTIVE else None,
            "scope": segment["scope"], "obstructors": list(segment["obstructors"]),
            "unknown_obstructors": list(segment.get("unknown_obstructors", [])), "factor": factor_ref}


def vedha_not_applicable(factor_ref: tuple[str, str]) -> dict:
    """A DECLARED non-applicability (adverse residence / a (graha, house) the validated COMPLETE pairs load does not cite):
    `score.factor_product` skips it — it is neither a missing operand nor a silent 1."""
    _check_ref(factor_ref)
    return {"state": "not_applicable", "not_applicable": True, "factor": factor_ref, "value": None,
            "reason": "no_cited_vedha_pair_for_this_house", "reasons": [], "qualification": None, "scope": None,
            "obstructors": [], "unknown_obstructors": []}


def vedha_factor_results(derived: dict, *, factor_ref: tuple[str, str]) -> list[dict]:
    """derive_vedha output -> the ordered list of structured factor results the writer carries: one per segment, or the single
    declared non-applicability. Each carries its `t_in`/`t_out` (a segment) so the writer can attach it to the right support."""
    if not derived["applicable"]:
        return [vedha_not_applicable(factor_ref)]
    return [{**vedha_factor_value(seg, factor_ref=factor_ref), "t_in": seg["t_in"], "t_out": seg["t_out"]} for seg in derived["segments"]]


def vedha_callback_result(derived: dict, *, factor_ref: tuple[str, str]) -> dict:
    """THE structured, version-bound result a vedha callback returns to the sweep / writer (Codex round 8 R8-7):
      factor      the exact factor reference the caller ASKED for (validated here against the registry row) — echoed back so the
                  caller can verify the reference it receives is the one it requested;
      applicable  False ⇒ one declared not-applicable result, no segments;
      results     one structured factor result per segment (state, value, reason(s), qualification, scope, obstructors,
                  unknown_obstructors, t_in/t_out), partitioning the primary span;
      boundaries  every segment boundary instant (the sweep's `state_boundaries`: a short interior vedha island is only
                  found when these are supplied);
      scopes      the machine-readable scopes present (`excluding_on_demand_moon_obstruction`) — to be persisted and served.
    A float-only callback cannot carry any of this."""
    _check_ref(factor_ref)
    results = vedha_factor_results(derived, factor_ref=factor_ref)
    stamps = {r[k] for r in results for k in ("t_in", "t_out") if k in r}
    return {"factor": factor_ref, "applicable": derived["applicable"], "results": results,
            "boundaries": sorted(stamps, key=_t), "scopes": sorted({r["scope"] for r in results if r.get("scope")})}


def check_callback_result(result: dict, requested_ref: tuple[str, str]) -> dict:
    """The caller's side of the contract: the returned reference (top level AND on every result) must equal the one requested,
    segments must be ordered and abutting, and every non-applicable result must be the single declared one. Returns `result`."""
    if tuple(result.get("factor", ())) != tuple(requested_ref):
        raise ValueError(f"vedha callback returned factor {result.get('factor')!r}, asked for {requested_ref!r}")
    res = result["results"]
    for r in res:
        if tuple(r["factor"]) != tuple(requested_ref):
            raise ValueError(f"a vedha result carries factor {r['factor']!r}, asked for {requested_ref!r}")
    if not result["applicable"]:
        if len(res) != 1 or res[0].get("state") != "not_applicable":
            raise ValueError("a not-applicable vedha result must be exactly one declared not_applicable entry")
        return result
    for a, b in zip(res, res[1:]):
        if a["t_out"] != b["t_in"]:
            raise ValueError(f"vedha segments do not abut: {a['t_out']} != {b['t_in']}")
    return result


def _check_ref(factor_ref) -> None:
    from .registry import FACTORS
    row = FACTORS.get(factor_ref)
    if row is None or row["factor_id"] != "vedha_attenuation" or "applicability" not in row:
        raise ValueError(f"{factor_ref!r} is not a vedha_attenuation row that declares applicability")
