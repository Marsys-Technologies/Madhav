"""Score algebra (GOCHARA_DESIGN_SPECS_v1_4 §2.1, pinned NK-4 / R2-S03 /
amendment 2 R4-S01).

Within-path score = PRODUCT of factor scores over the admitted base; a
missing operand takes its declared null_state — `omit` drops the factor,
`unqualified` propagates (never 0 or 1 by default). Per-channel root
reduction: contribution(path, root, c) = max over records sharing root_id;
path.c = Σ over roots. Cross-path aggregation = MAX (union semantics; paths
never multiply each other). Testimony rows contribute exactly zero to any
score, weight, or gate (§1.2 inv 2, O-RR-7). Channel is assigned by
class-relative polarity (§3.1): a factor value is never negative — direction
carries the sign (O-RP-7).
"""
from __future__ import annotations

from .records import RelationshipRecord
from .registry import CLASS_BY_NAME

UNQUALIFIED = "unqualified"
CHANNELS = ("evidence_for_occurrence", "evidence_against_occurrence")


def factor_product(factor_results: list[dict]) -> float | str:
    """The within-path product. Each item: {value: float|None,
    null_state: 'omit'|'unqualified'} or a DECLARED non-applicability
    {not_applicable: True, factor: <ref>}. Omit drops; a declared
    non-applicability is skipped (the registry row says the factor does not
    apply to this record — its operand was never missing); unqualified
    propagates."""
    product = 1.0
    for fr in factor_results:
        if fr.get("not_applicable") is True and fr.get("factor"):
            continue            # declared applicability, not a missing operand and never a silent 1 elsewhere
        value = fr.get("value")
        if value is None:
            if fr.get("null_state") == "omit":
                continue
            return UNQUALIFIED
        if not (0.0 <= value <= 1.0):
            raise ValueError("every scored factor's range ⊆ [0,1] (§2.1)")
        product *= value
    return product


def unqualified_reasons(factor_results: list[dict]) -> list[str]:
    """Why factor_product returned UNQUALIFIED: the unresolved (non-omit, non-declared-N/A) factors."""
    return [str(fr.get("reason") or fr.get("factor") or "unresolved_factor") for fr in factor_results
            if fr.get("value") is None and fr.get("null_state") != "omit"
            and not (fr.get("not_applicable") is True and fr.get("factor"))]


def channel_for(direction: str, event_class: str) -> str:
    """Class-relative polarity (§3.1): adverse-direction evidence is evidence
    FOR adverse classes and AGAINST gain classes; favourable-direction evidence
    is FOR gain classes and AGAINST adverse classes."""
    polarity = CLASS_BY_NAME[event_class]["polarity"]
    if direction == "adverse":
        return ("evidence_for_occurrence" if polarity == "adverse"
                else "evidence_against_occurrence")
    if direction == "favourable":
        return ("evidence_against_occurrence" if polarity == "adverse"
                else "evidence_for_occurrence")
    raise ValueError(f"unknown direction {direction!r}")


def record_channel_value(record: RelationshipRecord, event_class: str,
                         direction: str, factor_results: list[dict]) -> dict:
    """A record's value in its assigned channel; its other channel is 0;
    testimony rows contribute exactly zero to any score (O-RR-7).

    An UNRESOLVED applicable factor makes the record `unqualified` (S §2.1): it
    names the channel it would have fed (`unqualified_channel`) and why — it is
    never a numeric 0 in that channel."""
    out = {c: 0.0 for c in CHANNELS}
    if record.operator_role == "testimony":
        return out
    value = factor_product(factor_results)
    if value == UNQUALIFIED:
        out["unqualified"] = True
        out["unqualified_channel"] = channel_for(direction, event_class)
        out["unqualified_reasons"] = unqualified_reasons(factor_results)
        return out
    out[channel_for(direction, event_class)] = value
    return out


def path_channel_scores(records: list[RelationshipRecord], event_class: str,
                        record_evals: dict[str, dict]) -> dict:
    """Per-channel root reduction within one path (amendment 2):
    contribution(path, root, c) = max over records sharing root_id;
    path.c = Σ over roots. Order-independent, channel-preserving.

    QUALIFICATION PROPAGATES (Codex round 6 R1; S §2.1): an unresolved applicable
    factor on any scored record in channel c makes that channel's total
    **None** — it is never reported as a complete numeric total. Known partial
    subtotals (Σ over roots of the max over their QUALIFIED aliases — a lower
    bound) are returned separately under `known_partial_subtotals`, flagged
    incomplete. A genuine numeric 0.0 stays 0.0; testimony contributes nothing
    and never qualifies or disqualifies; a record with no evaluation at all is
    unqualified in BOTH channels (reason `not_evaluated`). Admission and
    admitted support are unchanged by qualification."""
    roots: dict[str, list[dict]] = {}
    unq: dict[str, list[str]] = {c: [] for c in CHANNELS}
    reasons: dict[str, list[str]] = {}
    scored = 0
    for r in records:
        if r.operator_role == "testimony":
            continue
        scored += 1
        ev = record_evals.get(r.record_id)
        if ev is None:
            chans, why = list(CHANNELS), ["not_evaluated"]
        elif ev.get("unqualified"):
            ch = ev.get("unqualified_channel")
            chans = [ch] if ch in CHANNELS else list(CHANNELS)
            why = list(ev.get("unqualified_reasons") or ["unresolved_factor"])
        else:
            roots.setdefault(r.root_id, []).append(ev)
            continue
        for c in chans:
            unq[c].append(r.record_id)
        reasons[r.record_id] = why
    # (testimony rows carry zeros and never move a total: skipping them is the O-RR-7 rule)
    partial = {c: 0.0 for c in CHANNELS}
    for root_records in roots.values():
        for c in CHANNELS:
            partial[c] += max(ev[c] for ev in root_records)
    totals = {c: (None if unq[c] else partial[c]) for c in CHANNELS}
    qualified_records = sum(len(v) for v in roots.values())
    bad = sorted({rid for c in CHANNELS for rid in unq[c]})
    if not bad:
        qualification = "qualified"
    elif qualified_records == 0:
        qualification = "unqualified"
    else:
        qualification = "partially_unqualified"
    out = dict(totals)
    out.update({
        "qualification": qualification,
        "unqualified_channels": [c for c in CHANNELS if unq[c]],
        "unqualified_record_ids": bad,
        "unqualified_reasons": {rid: reasons[rid] for rid in bad},
        "known_partial_subtotals": {c: partial[c] for c in CHANNELS if unq[c]},   # lower bounds, NEVER complete evidence
    })
    return out


def aggregate_paths_detail(path_scores: list) -> dict:
    """Cross-path aggregation = MAX over admitted paths (union semantics), with qualification (Codex round 7 [1]).

    An unknown (UNQUALIFIED / None) competing path can hold any value in the factor range [0, 1], so the maximum
    is established only when it is PROVED independent of the unknown: the known maximum is already 1.0 (nothing in
    [0, 1] can exceed it). Otherwise the cross-path value is unqualified — never the known maximum standing in for
    the whole — and the known maximum is returned only as a labelled LOWER BOUND. A path score is a product of
    factors in [0, 1] (§2.1), so anything outside that range is a defect, not a value."""
    known, unknown = [], 0
    for item in path_scores:
        if item is None or item == UNQUALIFIED:
            unknown += 1
        elif isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"path score {item!r} is neither a number nor UNQUALIFIED")
        elif not (0.0 <= item <= 1.0) or item != item:
            raise ValueError("a path score is a product of factors in [0,1] (§2.1)")
        else:
            known.append(float(item))
    lower = max(known) if known else None
    if not path_scores:
        return {"value": 0.0, "qualification": "qualified", "unknown_paths": 0, "known_lower_bound": None, "reason": None}
    if unknown and (lower is None or lower < 1.0):
        return {"value": UNQUALIFIED, "qualification": "unqualified", "unknown_paths": unknown,
                "known_lower_bound": lower, "reason": "competing_path_unqualified"}
    return {"value": lower, "qualification": "qualified", "unknown_paths": unknown,
            "known_lower_bound": lower, "reason": None}


def aggregate_paths(path_scores: list[float | str]) -> float | str:
    """Cross-path aggregation = max over admitted paths, qualified only if proved independent of any unknown path
    (see `aggregate_paths_detail`, which also reports the known lower bound and the reason)."""
    return aggregate_paths_detail(path_scores)["value"]


def promise(strength: float | None, condition: bool) -> float:
    """§2.3 inv 8 — promise = strength × condition; a constant-presence
    implementation (promise independent of condition) fails O-RP-6."""
    if strength is None:
        raise ValueError("missing strength operand takes its factor's "
                         "null_state upstream — never a default (§2.1)")
    return strength * (1.0 if condition else 0.0)
