"""Rule Book scorer - Holm, the outcome rule (v1.1 Part E) and the minimum detectable effect (v1.1 F4, A8)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import config as C

STRONG = "STRONG"
MIDDLE = "MIDDLE"
CHANCE = "CHANCE-LEVEL"

LABEL_NOT_DIRECTION = "timing association, not direction-specific"
LABEL_CHOSEN_DATES = "could reflect chosen dates"
LABEL_INCLUDES_CHOSEN = "includes dates that could have been chosen"
LABEL_CONFLICT_DRIVEN = "driven by variant-conflict readings"


def holm_adjust(p: Mapping[str, float]) -> Dict[str, float]:
    """Holm step-down adjusted p-values for the given families (m = len(p))."""
    items = sorted(p.items(), key=lambda kv: (kv[1], kv[0]))
    m = len(items)
    out: Dict[str, float] = {}
    running = 0.0
    for i, (k, v) in enumerate(items):
        running = max(running, min(1.0, (m - i) * v))
        out[k] = running
    return out


def _le(x: Optional[float], a: float) -> bool:
    return x is not None and x <= a


def decide(
    results: Mapping[str, Mapping[str, Any]],
    testable: Mapping[str, bool],
    fallback_primary_set: bool = False,
) -> Dict[str, Any]:
    """Read the outcome of a run by v1.1 Part E. ``results`` = family -> ``score_family`` output.

    Only testable families enter Holm (their number is m, at most 2). A family with no p1 is not testable.
    """
    fams = [f for f, r in results.items() if testable.get(f, False) and r.get("p1") is not None]
    holm = holm_adjust({f: results[f]["p1"] for f in fams}) if fams else {}
    per: Dict[str, Dict[str, Any]] = {}
    for f in fams:
        r = results[f]
        adj = holm[f]
        core5 = _le(adj, C.ALPHA_STRONG) and _le(r.get("p2"), C.ALPHA_STRONG) and _le(r.get("p3"), C.ALPHA_STRONG)
        dir_ok = _le(r.get("p_dir"), C.ALPHA_STRONG)
        cons_ok = (not fallback_primary_set) or bool(r.get("nonschedulable_above_null_mean"))
        core10 = _le(adj, C.ALPHA_MIDDLE) and _le(r.get("p2"), C.ALPHA_MIDDLE) and _le(r.get("p3"), C.ALPHA_MIDDLE)
        per[f] = {
            "p1": r["p1"], "p1_holm": adj, "p2": r.get("p2"), "p3": r.get("p3"), "p_dir": r.get("p_dir"),
            "strong": bool(core5 and dir_ok and cons_ok),
            "strong_core": bool(core5),
            "middle_core": bool(core10),
            "fails_only_direction": bool(core5 and not dir_ok and cons_ok),
            "fails_only_consistency": bool(core5 and dir_ok and not cons_ok),
        }
    labels: List[str] = []
    if any(v["strong"] for v in per.values()):
        outcome = STRONG
    elif any(v["middle_core"] for v in per.values()):
        outcome = MIDDLE
        if any(v["strong_core"] and not v["strong"] for v in per.values()):
            if any(v["fails_only_direction"] for v in per.values()):
                labels.append(LABEL_NOT_DIRECTION)
            if any(v["fails_only_consistency"] for v in per.values()):
                labels.append(LABEL_CHOSEN_DATES)
            if not labels:  # strong core but failing both extras
                labels.append(LABEL_NOT_DIRECTION)
                if fallback_primary_set:
                    labels.append(LABEL_CHOSEN_DATES)
    else:
        outcome = CHANCE
    if fallback_primary_set:
        labels.append(LABEL_INCLUDES_CHOSEN)
    return {"outcome": outcome, "labels": labels, "m": len(fams), "families": per, "testable": dict(testable)}


def mde_from_power(qs: Sequence[float], power: Sequence[float], target: float = C.GATE_SANITY_POWER) -> Optional[float]:
    """Smallest effect q at which the STRONG rate first reaches ``target`` (linear interpolation between the
    simulated points); None when the curve never reaches it."""
    pts = sorted(zip(qs, power))
    for (q0, p0), (q1, p1) in zip(pts, pts[1:]):
        if p0 >= target:
            return q0
        if p1 >= target:
            return q0 + (target - p0) * (q1 - q0) / (p1 - p0) if p1 > p0 else q1
    if pts and pts[0][1] >= target:
        return pts[0][0]
    return None


def mde_report(qs: Sequence[float], power: Sequence[float]) -> Dict[str, Any]:
    """The MDE as simulated and divided by the extraction-noise level 0.67 (v1.1 A8)."""
    q = mde_from_power(qs, power)
    return {
        "target_power": C.GATE_SANITY_POWER,
        "mde_as_is": q,
        "mde_divided_by_0_67": None if q is None else q / C.EXTRACTION_NOISE,
        "note": "q = share of events tied to a typical rule's window beyond chance; none reached" if q is None else "q = share of events tied to a typical rule's window beyond chance",
    }
