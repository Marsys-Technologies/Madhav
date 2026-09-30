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
    null_state: 'omit'|'unqualified'}. Omit drops; unqualified propagates."""
    product = 1.0
    for fr in factor_results:
        value = fr.get("value")
        if value is None:
            if fr.get("null_state") == "omit":
                continue
            return UNQUALIFIED
        if not (0.0 <= value <= 1.0):
            raise ValueError("every scored factor's range ⊆ [0,1] (§2.1)")
        product *= value
    return product


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
    testimony rows contribute exactly zero to any score (O-RR-7)."""
    out = {c: 0.0 for c in CHANNELS}
    if record.operator_role == "testimony":
        return out
    value = factor_product(factor_results)
    if value == UNQUALIFIED:
        out["unqualified"] = True
        return out
    out[channel_for(direction, event_class)] = value
    return out


def path_channel_scores(records: list[RelationshipRecord], event_class: str,
                        record_evals: dict[str, dict]) -> dict:
    """Per-channel root reduction within one path (amendment 2):
    contribution(path, root, c) = max over records sharing root_id;
    path.c = Σ over roots. Order-independent, channel-preserving."""
    roots: dict[str, list[dict]] = {}
    for r in records:
        ev = record_evals.get(r.record_id)
        if ev is None or ev.get("unqualified"):
            continue
        roots.setdefault(r.root_id, []).append(ev)
    totals = {c: 0.0 for c in CHANNELS}
    for root_records in roots.values():
        for c in CHANNELS:
            totals[c] += max(ev[c] for ev in root_records)
    return totals


def aggregate_paths(path_scores: list[float | str]) -> float | str:
    """Cross-path aggregation = max over admitted paths (union semantics:
    one strong path suffices; paths never multiply each other)."""
    numeric = [s for s in path_scores if isinstance(s, (int, float))]
    if not numeric:
        return UNQUALIFIED if path_scores else 0.0
    return max(numeric)


def promise(strength: float | None, condition: bool) -> float:
    """§2.3 inv 8 — promise = strength × condition; a constant-presence
    implementation (promise independent of condition) fails O-RP-6."""
    if strength is None:
        raise ValueError("missing strength operand takes its factor's "
                         "null_state upstream — never a default (§2.1)")
    return strength * (1.0 if condition else 0.0)
